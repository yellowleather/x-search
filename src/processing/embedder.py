"""
Embedding generation for semantic search
Uses sentence-transformers for local, free embeddings
"""

from datetime import datetime
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.config.settings import settings
from src.database.connection import db
from src.retrieval.vector_store import vector_store_manager
from src.utils.logger import logger


class EmbeddingGenerator:
    """Generate embeddings for tweets and linked content"""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.dimension = settings.EMBEDDING_DIMENSION
        
        logger.info(f"Loading embedding model: {self.model_name}")
        logger.info(f"Device: {self.device}, Batch size: {self.batch_size}")
        
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"✓ Model loaded successfully (dimension: {self.model.get_sentence_embedding_dimension()})")
            
            # Verify dimension matches
            model_dim = self.model.get_sentence_embedding_dimension()
            if model_dim != self.dimension:
                logger.warning(
                    f"Model dimension ({model_dim}) doesn't match configured dimension ({self.dimension}). "
                    f"Update EMBEDDING_DIMENSION in .env to {model_dim}"
                )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a single text"""
        try:
            if not text or len(text.strip()) == 0:
                return None
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """Generate embeddings for a batch of texts"""
        try:
            # Filter out empty texts
            valid_indices = [i for i, text in enumerate(texts) if text and len(text.strip()) > 0]
            valid_texts = [texts[i] for i in valid_indices]
            
            if not valid_texts:
                return [None] * len(texts)
            
            # Generate embeddings
            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Map back to original indices
            result = [None] * len(texts)
            for i, idx in enumerate(valid_indices):
                result[idx] = embeddings[i]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Generate embedding for a search query"""
        return self.generate_embedding(query)
    
    @staticmethod
    def _to_iso(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    def _tweet_metadata(self, tweet: dict) -> dict:
        return {
            "type": "tweet",
            "tweet_id": tweet["tweet_id"],
            "text": tweet.get("text"),
            "author_username": tweet.get("author_username"),
            "author_name": tweet.get("author_name"),
            "liked_at": self._to_iso(tweet.get("liked_at")),
            "url": tweet.get("url"),
            "like_count": tweet.get("like_count"),
            "retweet_count": tweet.get("retweet_count"),
            "hashtags": tweet.get("hashtags") or [],
        }
    
    def _link_metadata(self, link: dict) -> dict:
        summary = link.get("summary") or link.get("content_text", "")
        return {
            "type": "link",
            "link_id": link["id"],
            "tweet_id": link.get("tweet_id"),
            "tweet_author": link.get("tweet_author_username"),
            "url": link.get("url"),
            "title": link.get("title"),
            "author": link.get("author"),
            "domain": link.get("domain"),
            "summary": summary[:1000] if summary else "",
            "scraped_at": self._to_iso(link.get("scraped_at")),
        }
    
    def get_pending_tweets(self, limit: int = 1000) -> List[dict]:
        """Get tweets that need embeddings"""
        query = """
            SELECT 
                id,
                tweet_id,
                text,
                author_username,
                author_name,
                liked_at,
                url,
                like_count,
                retweet_count,
                hashtags
            FROM tweets
            WHERE (embedding_generated = FALSE OR embedding_generated IS NULL)
            AND text IS NOT NULL
            AND text != ''
            ORDER BY liked_at DESC
            LIMIT %s
        """
        
        result = db.execute_query(query, (limit,))
        return result or []
    
    def get_pending_links(self, limit: int = 1000) -> List[dict]:
        """Get linked content that needs embeddings"""
        query = """
            SELECT 
                lc.id,
                lc.tweet_id,
                lc.url,
                lc.title,
                lc.content_text,
                lc.summary,
                lc.author,
                lc.domain,
                lc.scraped_at,
                t.author_username AS tweet_author_username
            FROM linked_content lc
            JOIN tweets t ON lc.tweet_id = t.tweet_id
            WHERE (lc.embedding_generated = FALSE OR lc.embedding_generated IS NULL)
            AND lc.content_text IS NOT NULL
            AND lc.content_text != ''
            AND lc.scrape_status = 'success'
            ORDER BY lc.scraped_at DESC
            LIMIT %s
        """
        
        result = db.execute_query(query, (limit,))
        return result or []
    
    def mark_tweet_embedded(self, tweet_id: str) -> bool:
        """Flag tweet as embedded in the database (metadata only)."""
        try:
            query = """
                UPDATE tweets
                SET embedding_generated = TRUE,
                    updated_at_db = NOW()
                WHERE tweet_id = %s
            """
            db.execute_query(query, (tweet_id,), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Failed to mark tweet as embedded: {e}")
            return False
    
    def mark_link_embedded(self, link_id: int) -> bool:
        """Flag linked content as embedded in the database."""
        try:
            query = """
                UPDATE linked_content
                SET embedding_generated = TRUE,
                    updated_at = NOW()
                WHERE id = %s
            """
            db.execute_query(query, (link_id,), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Failed to mark link as embedded: {e}")
            return False
    
    def process_tweets(self, batch_size: int = None) -> dict:
        """Process all pending tweets"""
        batch_size = batch_size or self.batch_size
        
        logger.info("Processing tweet embeddings...")
        
        tweets = self.get_pending_tweets(limit=10000)  # Process up to 10k at a time
        
        if not tweets:
            logger.info("No tweets to process")
            return {'processed': 0, 'failed': 0}
        
        logger.info(f"Found {len(tweets)} tweets to process")
        
        stats = {'processed': 0, 'failed': 0}
        
        # Process in batches
        for i in tqdm(range(0, len(tweets), batch_size), desc="Generating embeddings"):
            batch = tweets[i:i + batch_size]
            
            # Prepare texts (combine tweet text with author info for better context)
            texts = [
                f"{tweet['text']} (by @{tweet['author_username']})"
                for tweet in batch
            ]
            
            # Generate embeddings
            embeddings = self.generate_embeddings_batch(texts)
            
            # Update database
            batch_store_embeddings: List[np.ndarray] = []
            batch_metadata: List[dict] = []
            for tweet, embedding in zip(batch, embeddings):
                if embedding is None:
                    stats['failed'] += 1
                    continue
                
                if self.mark_tweet_embedded(tweet['tweet_id']):
                    stats['processed'] += 1
                    batch_store_embeddings.append(embedding)
                    batch_metadata.append(self._tweet_metadata(tweet))
                else:
                    stats['failed'] += 1
            
            if batch_store_embeddings:
                vector_store_manager.add_tweet_embeddings(batch_store_embeddings, batch_metadata)
        
        logger.info(f"✓ Processed {stats['processed']} tweets, {stats['failed']} failed")
        return stats
    
    def process_links(self, batch_size: int = None) -> dict:
        """Process all pending linked content"""
        batch_size = batch_size or self.batch_size
        
        logger.info("Processing linked content embeddings...")
        
        links = self.get_pending_links(limit=10000)
        
        if not links:
            logger.info("No links to process")
            return {'processed': 0, 'failed': 0}
        
        logger.info(f"Found {len(links)} links to process")
        
        stats = {'processed': 0, 'failed': 0}
        
        # Process in batches
        for i in tqdm(range(0, len(links), batch_size), desc="Generating embeddings"):
            batch = links[i:i + batch_size]
            
            # Prepare texts (combine title and content)
            texts = []
            for link in batch:
                title = link.get('title', '')
                content = link.get('content_text', '')
                # Combine title and content, truncate to reasonable length
                combined = f"{title}. {content}"[:2000]  # Limit to 2000 chars
                texts.append(combined)
            
            # Generate embeddings
            embeddings = self.generate_embeddings_batch(texts)
            
            # Update database
            batch_store_embeddings: List[np.ndarray] = []
            batch_metadata: List[dict] = []
            for link, embedding in zip(batch, embeddings):
                if embedding is None:
                    stats['failed'] += 1
                    continue
                
                if self.mark_link_embedded(link['id']):
                    stats['processed'] += 1
                    batch_store_embeddings.append(embedding)
                    batch_metadata.append(self._link_metadata(link))
                else:
                    stats['failed'] += 1
            
            if batch_store_embeddings:
                vector_store_manager.add_link_embeddings(batch_store_embeddings, batch_metadata)
        
        logger.info(f"✓ Processed {stats['processed']} links, {stats['failed']} failed")
        return stats
    
    def process_all(self) -> dict:
        """Process all pending embeddings (tweets + links)"""
        logger.info("Starting embedding generation for all content...")
        
        tweet_stats = self.process_tweets()
        link_stats = self.process_links()
        
        total_stats = {
            'tweets_processed': tweet_stats['processed'],
            'tweets_failed': tweet_stats['failed'],
            'links_processed': link_stats['processed'],
            'links_failed': link_stats['failed'],
            'total_processed': tweet_stats['processed'] + link_stats['processed'],
            'total_failed': tweet_stats['failed'] + link_stats['failed']
        }
        
        logger.info("✓ Embedding generation complete!")
        logger.info(f"Total processed: {total_stats['total_processed']}, "
                   f"Total failed: {total_stats['total_failed']}")
        
        return total_stats


# Global embedder instance
embedder = EmbeddingGenerator()


if __name__ == "__main__":
    """Run embedding generation as standalone script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate embeddings for tweets and links")
    parser.add_argument('--type', choices=['tweets', 'links', 'all'], default='all',
                       help='What to process: tweets, links, or all')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing')
    
    args = parser.parse_args()
    
    if args.type == 'tweets':
        embedder.process_tweets(batch_size=args.batch_size)
    elif args.type == 'links':
        embedder.process_links(batch_size=args.batch_size)
    else:
        embedder.process_all()
