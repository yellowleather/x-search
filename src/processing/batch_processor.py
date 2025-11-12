"""
Batch processor for X-Search
Orchestrates the full pipeline: scraping → processing → embedding
"""

from datetime import datetime
from typing import Dict, Optional
import time

from src.database.connection import db
from src.processing.embedder import embedder
from src.utils.logger import logger
from src.config.settings import settings

# Optional import for link scraping
scraper = None
if settings.ENABLE_LINK_SCRAPING:
    try:
        from src.ingestion.link_scraper import scraper
    except ImportError as e:
        logger.warning(f"Link scraping disabled - missing dependencies: {e}")
        logger.warning("Install with: pip install lxml[html_clean] or disable ENABLE_LINK_SCRAPING")


class BatchProcessor:
    """Orchestrate the full processing pipeline"""
    
    def __init__(self):
        self.batch_size = settings.BATCH_SIZE
        self.max_workers = settings.MAX_WORKERS
    
    def log_job_start(self, job_type: str) -> int:
        """Log the start of a batch job"""
        query = """
            INSERT INTO processing_log (job_type, batch_date, status, started_at)
            VALUES (%s, %s, 'running', NOW())
            RETURNING id
        """
        
        result = db.execute_query(
            query,
            (job_type, datetime.now().date())
        )
        
        job_id = result[0]['id'] if result else None
        logger.info(f"Started job: {job_type} (ID: {job_id})")
        return job_id
    
    def log_job_complete(self, job_id: int, stats: Dict, status: str = 'completed'):
        """Log job completion"""
        query = """
            UPDATE processing_log
            SET status = %s,
                tweets_processed = %s,
                links_scraped = %s,
                embeddings_generated = %s,
                errors_count = %s,
                metadata = %s,
                completed_at = NOW()
            WHERE id = %s
        """
        
        db.execute_query(
            query,
            (
                status,
                stats.get('tweets_processed', 0),
                stats.get('links_scraped', 0),
                stats.get('embeddings_generated', 0),
                stats.get('errors', 0),
                str(stats),
                job_id
            ),
            fetch=False
        )
        
        logger.info(f"Job {job_id} completed with status: {status}")
    
    def get_tweets_without_links(self, limit: int = 1000) -> list:
        """Get tweets that haven't had their links scraped yet"""
        query = """
            SELECT DISTINCT t.tweet_id, t.raw_json->>'urls' as urls_json
            FROM tweets t
            WHERE t.links_scraped = FALSE
            AND t.raw_json->>'urls' IS NOT NULL
            AND t.raw_json->>'urls' != '[]'
            ORDER BY t.liked_at DESC
            LIMIT %s
        """
        
        result = db.execute_query(query, (limit,))
        return result or []
    
    def mark_tweet_links_scraped(self, tweet_id: str):
        """Mark tweet as having links scraped"""
        query = """
            UPDATE tweets
            SET links_scraped = TRUE,
                updated_at_db = NOW()
            WHERE tweet_id = %s
        """
        db.execute_query(query, (tweet_id,), fetch=False)
    
    def scrape_pending_links(self) -> Dict:
        """Scrape all pending links from tweets"""
        if not settings.ENABLE_LINK_SCRAPING or scraper is None:
            logger.info("Link scraping is disabled or dependencies not installed")
            return {'tweets_processed': 0, 'links_scraped': 0, 'errors': 0}

        logger.info("Starting link scraping...")
        
        tweets = self.get_tweets_without_links(limit=5000)
        
        if not tweets:
            logger.info("No tweets with pending links")
            return {'tweets_processed': 0, 'links_scraped': 0, 'errors': 0}
        
        logger.info(f"Found {len(tweets)} tweets with links to scrape")
        
        stats = {
            'tweets_processed': 0,
            'links_scraped': 0,
            'errors': 0
        }
        
        for tweet in tweets:
            try:
                tweet_id = tweet['tweet_id']
                
                # Parse URLs from JSON
                import json
                urls_json = tweet.get('urls_json', '[]')
                try:
                    urls = json.loads(urls_json) if urls_json else []
                except:
                    urls = []
                
                if not urls:
                    self.mark_tweet_links_scraped(tweet_id)
                    continue
                
                # Scrape each URL
                for url in urls:
                    try:
                        logger.info(f"Scraping {url} from tweet {tweet_id}")
                        result = scraper.scrape_url(url)
                        scraper.save_scraped_content(tweet_id, url, result)
                        
                        if result['status'] == 'success':
                            stats['links_scraped'] += 1
                        
                        # Respect rate limits
                        time.sleep(settings.SCRAPING_DELAY)
                        
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
                        stats['errors'] += 1
                
                self.mark_tweet_links_scraped(tweet_id)
                stats['tweets_processed'] += 1
                
                # Log progress
                if stats['tweets_processed'] % 100 == 0:
                    logger.info(f"Progress: {stats['tweets_processed']}/{len(tweets)} tweets, "
                               f"{stats['links_scraped']} links scraped")
                
            except Exception as e:
                logger.error(f"Error processing tweet {tweet.get('tweet_id')}: {e}")
                stats['errors'] += 1
        
        logger.info(f"✓ Link scraping complete: {stats['links_scraped']} links from "
                   f"{stats['tweets_processed']} tweets")
        
        return stats
    
    def generate_all_embeddings(self) -> Dict:
        """Generate embeddings for all content"""
        if not settings.ENABLE_EMBEDDING_GENERATION:
            logger.info("Embedding generation is disabled")
            return {'embeddings_generated': 0, 'errors': 0}
        
        logger.info("Starting embedding generation...")
        
        stats = embedder.process_all()
        
        return {
            'embeddings_generated': stats['total_processed'],
            'errors': stats['total_failed']
        }
    
    def mark_tweets_processed(self, limit: int = 10000):
        """Mark tweets as processed"""
        query = """
            UPDATE tweets
            SET processed = TRUE
            WHERE embedding_generated = TRUE
            AND processed = FALSE
            LIMIT %s
        """

        result = db.execute_query(query, (limit,), fetch=False)
        logger.info(f"Marked tweets as processed")
    
    def run_full_pipeline(self) -> Dict:
        """Run the complete processing pipeline"""
        logger.info("=" * 60)
        logger.info("Starting full processing pipeline")
        logger.info("=" * 60)
        
        job_id = self.log_job_start('full_pipeline')
        start_time = time.time()
        
        total_stats = {
            'tweets_processed': 0,
            'links_scraped': 0,
            'embeddings_generated': 0,
            'errors': 0
        }
        
        try:
            # Step 1: Scrape links
            logger.info("\n[1/3] Scraping links from tweets...")
            scraping_stats = self.scrape_pending_links()
            total_stats['tweets_processed'] = scraping_stats['tweets_processed']
            total_stats['links_scraped'] = scraping_stats['links_scraped']
            total_stats['errors'] += scraping_stats['errors']
            
            # Step 2: Generate embeddings
            logger.info("\n[2/3] Generating embeddings...")
            embedding_stats = self.generate_all_embeddings()
            total_stats['embeddings_generated'] = embedding_stats['embeddings_generated']
            total_stats['errors'] += embedding_stats['errors']
            
            # Step 3: Mark as processed
            logger.info("\n[3/3] Marking tweets as processed...")
            self.mark_tweets_processed()
            
            # Log completion
            elapsed = time.time() - start_time
            total_stats['elapsed_seconds'] = elapsed
            
            logger.info("\n" + "=" * 60)
            logger.info("✓ Pipeline complete!")
            logger.info(f"  Tweets processed: {total_stats['tweets_processed']}")
            logger.info(f"  Links scraped: {total_stats['links_scraped']}")
            logger.info(f"  Embeddings generated: {total_stats['embeddings_generated']}")
            logger.info(f"  Errors: {total_stats['errors']}")
            logger.info(f"  Time elapsed: {elapsed:.2f}s")
            logger.info("=" * 60)
            
            self.log_job_complete(job_id, total_stats, 'completed')
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            total_stats['errors'] += 1
            total_stats['error_message'] = str(e)
            self.log_job_complete(job_id, total_stats, 'failed')
            raise
        
        return total_stats
    
    def get_processing_stats(self) -> Dict:
        """Get current processing statistics"""
        query = """
            SELECT
                COUNT(*) as total_tweets,
                COUNT(*) FILTER (WHERE embedding_generated = TRUE) as tweets_with_embeddings,
                COUNT(*) FILTER (WHERE processed = TRUE) as tweets_processed,
                COUNT(*) FILTER (WHERE links_scraped = TRUE) as tweets_links_scraped,
                (SELECT COUNT(*) FROM linked_content) as total_links,
                (SELECT COUNT(*) FROM linked_content WHERE embedding_generated = TRUE) as links_with_embeddings,
                (SELECT COUNT(*) FROM linked_content WHERE scrape_status = 'success') as links_scraped_successfully,
                COUNT(DISTINCT author_username) as unique_authors
            FROM tweets
        """
        
        result = db.execute_query(query)
        
        if result:
            return dict(result[0])
        return {}


# Global processor instance
processor = BatchProcessor()


if __name__ == "__main__":
    """Run batch processor as standalone script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="X-Factor Batch Processor")
    parser.add_argument(
        '--task',
        choices=['full', 'links', 'embeddings', 'stats'],
        default='full',
        help='Task to run: full pipeline, links only, embeddings only, or show stats'
    )
    
    args = parser.parse_args()
    
    if args.task == 'full':
        processor.run_full_pipeline()
    elif args.task == 'links':
        stats = processor.scrape_pending_links()
        logger.info(f"Scraping complete: {stats}")
    elif args.task == 'embeddings':
        stats = processor.generate_all_embeddings()
        logger.info(f"Embedding generation complete: {stats}")
    elif args.task == 'stats':
        stats = processor.get_processing_stats()
        logger.info("\nProcessing Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
