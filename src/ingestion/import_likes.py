"""
Import liked tweets from Twitter data export
Twitter provides data in like.js format
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import argparse

from src.database.connection import db
from src.utils.logger import logger
from src.config.settings import settings


def parse_twitter_export_js(file_path: str) -> List[Dict]:
    """
    Parse Twitter export like.js file
    Twitter exports data as: window.YTD.like.part0 = [...]
    """
    logger.info(f"Parsing Twitter export file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove JavaScript variable assignment
    # Format: window.YTD.like.part0 = [...]
    content = re.sub(r'^window\.YTD\.\w+\.part\d+\s*=\s*', '', content)
    content = content.strip().rstrip(';')
    
    try:
        data = json.loads(content)
        logger.info(f"Parsed {len(data)} liked tweets from export")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise


def extract_tweet_data(like_entry: Dict) -> Dict[str, Any]:
    """Extract relevant data from a like entry"""
    try:
        like_data = like_entry.get('like', {})

        # Check for newest format (2024+): has tweetId directly in like object
        if 'tweetId' in like_data:
            tweet_id = like_data.get('tweetId', '')
            full_text = like_data.get('fullText', '')
            expanded_url = like_data.get('expandedUrl', '')

            # Extract username from URL if available
            author_username = 'unknown'
            if expanded_url:
                # URL format: https://twitter.com/username/status/tweetid
                try:
                    parts = expanded_url.split('/')
                    if len(parts) >= 4:
                        author_username = parts[3]
                except:
                    pass

            return {
                'tweet_id': tweet_id,
                'author_username': author_username,
                'author_name': 'unknown',
                'author_id': '',
                'text': full_text,
                'created_at': None,
                'url': expanded_url,
                'like_count': 0,
                'retweet_count': 0,
                'reply_count': 0,
                'quote_count': 0,
                'language': 'en',
                'is_reply': False,
                'is_quote': False,
                'has_media': False,
                'media_urls': [],
                'hashtags': [],
                'mentions': [],
                'urls': [],
                'raw_json': like_entry
            }

        # Check for older format with tweetDisplayText
        tweet = like_data.get('tweetDisplayText') or like_data

        # Handle different export formats
        if isinstance(tweet, str):
            # Older format: just the text
            return {
                'tweet_id': like_data.get('id', 'unknown'),
                'text': tweet,
                'author_username': 'unknown',
                'author_name': 'unknown',
                'created_at': None,
                'url': None,
                'raw_json': like_entry
            }

        # Older structured format: has user object
        full_text = tweet.get('fullText', '')
        tweet_id = tweet.get('id_str', '') or tweet.get('id', '')
        
        # Extract author info
        user = tweet.get('user', {})
        author_username = user.get('screen_name', 'unknown')
        author_name = user.get('name', 'unknown')
        author_id = user.get('id_str', '') or user.get('id', '')
        
        # Parse created_at
        created_at_str = tweet.get('created_at')
        created_at = None
        if created_at_str:
            try:
                # Twitter format: "Wed Oct 10 20:19:24 +0000 2018"
                created_at = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
            except Exception as e:
                logger.debug(f"Could not parse date {created_at_str}: {e}")
        
        # Build tweet URL
        url = f"https://twitter.com/{author_username}/status/{tweet_id}" if tweet_id else None
        
        # Extract entities
        entities = tweet.get('entities', {})
        hashtags = [tag['text'] for tag in entities.get('hashtags', [])]
        mentions = [mention['screen_name'] for mention in entities.get('user_mentions', [])]
        urls = [url_obj.get('expanded_url', url_obj.get('url', '')) for url_obj in entities.get('urls', [])]
        
        # Media
        media = entities.get('media', [])
        has_media = len(media) > 0
        media_urls = [m.get('media_url_https', m.get('media_url', '')) for m in media]
        
        # Engagement metrics
        like_count = tweet.get('favorite_count', 0)
        retweet_count = tweet.get('retweet_count', 0)
        reply_count = tweet.get('reply_count', 0)
        quote_count = tweet.get('quote_count', 0)
        
        # Reply/quote info
        is_reply = bool(tweet.get('in_reply_to_status_id_str'))
        is_quote = bool(tweet.get('is_quote_status'))
        
        return {
            'tweet_id': tweet_id,
            'author_username': author_username,
            'author_name': author_name,
            'author_id': author_id,
            'text': full_text,
            'created_at': created_at,
            'url': url,
            'like_count': like_count,
            'retweet_count': retweet_count,
            'reply_count': reply_count,
            'quote_count': quote_count,
            'language': tweet.get('lang', 'en'),
            'is_reply': is_reply,
            'is_quote': is_quote,
            'has_media': has_media,
            'media_urls': media_urls,
            'hashtags': hashtags,
            'mentions': mentions,
            'urls': urls,
            'raw_json': like_entry
        }
    
    except Exception as e:
        logger.error(f"Error extracting tweet data: {e}")
        logger.debug(f"Problematic entry: {like_entry}")
        return None


def insert_tweet(tweet_data: Dict[str, Any]) -> bool:
    """Insert a tweet into the database"""
    if not tweet_data or not tweet_data.get('tweet_id'):
        logger.debug("Skipping tweet: missing tweet_data or tweet_id")
        return False

    try:
        query = """
            INSERT INTO tweets (
                tweet_id, author_username, author_name, author_id, text,
                created_at, url, like_count, retweet_count, reply_count, quote_count,
                language, is_reply, is_quote, has_media, media_urls,
                hashtags, mentions, raw_json
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (tweet_id) DO UPDATE SET
                like_count = EXCLUDED.like_count,
                retweet_count = EXCLUDED.retweet_count,
                reply_count = EXCLUDED.reply_count,
                quote_count = EXCLUDED.quote_count,
                updated_at_db = NOW()
        """

        result = db.execute_query(
            query,
            (
                tweet_data['tweet_id'],
                tweet_data['author_username'],
                tweet_data['author_name'],
                tweet_data.get('author_id'),
                tweet_data['text'],
                tweet_data.get('created_at'),
                tweet_data.get('url'),
                tweet_data.get('like_count', 0),
                tweet_data.get('retweet_count', 0),
                tweet_data.get('reply_count', 0),
                tweet_data.get('quote_count', 0),
                tweet_data.get('language', 'en'),
                tweet_data.get('is_reply', False),
                tweet_data.get('is_quote', False),
                tweet_data.get('has_media', False),
                tweet_data.get('media_urls', []),
                tweet_data.get('hashtags', []),
                tweet_data.get('mentions', []),
                json.dumps(tweet_data['raw_json'])
            ),
            fetch=False
        )
        if result is None:  # execute_query returns None when fetch=False
            return True
        logger.warning(f"Unexpected result from insert: {result}")
        return True

    except Exception as e:
        logger.error(f"Failed to insert tweet {tweet_data.get('tweet_id')}: {e}", exc_info=True)
        return False


def import_likes(file_path: str, batch_size: int = 100) -> Dict[str, int]:
    """
    Import liked tweets from Twitter export file
    
    Returns:
        Dict with statistics: {'total': int, 'imported': int, 'skipped': int, 'failed': int}
    """
    stats = {'total': 0, 'imported': 0, 'skipped': 0, 'failed': 0}
    
    try:
        # Parse the export file
        like_entries = parse_twitter_export_js(file_path)
        stats['total'] = len(like_entries)
        
        logger.info(f"Importing {stats['total']} liked tweets...")
        
        # Process in batches
        for i in range(0, len(like_entries), batch_size):
            batch = like_entries[i:i + batch_size]
            
            for like_entry in batch:
                tweet_data = extract_tweet_data(like_entry)
                
                if not tweet_data:
                    stats['skipped'] += 1
                    continue
                
                if insert_tweet(tweet_data):
                    stats['imported'] += 1
                else:
                    stats['failed'] += 1
            
            if (i + batch_size) % 1000 == 0:
                logger.info(f"Progress: {min(i + batch_size, stats['total'])}/{stats['total']} tweets processed")
        
        logger.info("Import complete!")
        logger.info(f"Total: {stats['total']}, Imported: {stats['imported']}, "
                   f"Skipped: {stats['skipped']}, Failed: {stats['failed']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(description="Import Twitter likes from export data")
    parser.add_argument(
        '--file', '-f',
        default='inputs/twitter/data/like.js',
        help='Path to like.js file from Twitter export (default: inputs/twitter/data/like.js)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing (default: 100)'
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info("Starting Twitter likes import...")
    logger.info(f"File: {file_path}")
    
    try:
        stats = import_likes(str(file_path), args.batch_size)
        logger.info("✓ Import completed successfully")
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")


if __name__ == "__main__":
    main()
