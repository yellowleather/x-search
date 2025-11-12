"""
Link scraper for extracting content from URLs in tweets
Handles various types of websites and content
"""

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urljoin
import time
from typing import Optional, Dict, List
import re

from src.database.connection import db
from src.utils.logger import logger
from src.config.settings import settings


class LinkScraper:
    """Scrape and extract content from URLs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.timeout = settings.REQUEST_TIMEOUT
    
    def should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped"""
        skip_domains = [
            'twitter.com', 'x.com', 't.co',
            'instagram.com', 'facebook.com',
            'youtube.com', 'youtu.be',  # Handle separately if needed
        ]
        
        domain = urlparse(url).netloc.lower()
        return any(skip in domain for skip in skip_domains)
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL (expand t.co, etc.)"""
        try:
            # Follow redirects to get final URL
            response = self.session.head(url, allow_redirects=True, timeout=5)
            return response.url
        except:
            return url
    
    def scrape_with_newspaper(self, url: str) -> Optional[Dict]:
        """Scrape using newspaper3k (best for articles)"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Try to get publish date
            publish_date = None
            if article.publish_date:
                publish_date = article.publish_date
            
            return {
                'method': 'newspaper',
                'title': article.title,
                'description': article.meta_description,
                'content_text': article.text,
                'summary': article.text[:500] if article.text else '',
                'author': ', '.join(article.authors) if article.authors else None,
                'publish_date': publish_date,
                'image_url': article.top_image,
                'html': article.html
            }
        except Exception as e:
            logger.debug(f"Newspaper scraping failed for {url}: {e}")
            return None
    
    def scrape_with_beautifulsoup(self, url: str) -> Optional[Dict]:
        """Scrape using simple HTTP request + BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.string
            elif soup.find('h1'):
                title = soup.find('h1').get_text(strip=True)
            
            # Extract description
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                       soup.find('meta', attrs={'property': 'og:description'})
            if meta_desc:
                description = meta_desc.get('content')
            
            # Extract main content
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.body
            
            if main_content:
                # Get text content
                text = main_content.get_text(separator=' ', strip=True)
                # Clean up excessive whitespace
                text = re.sub(r'\s+', ' ', text)
            else:
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
            
            # Extract image
            image_url = None
            og_image = soup.find('meta', attrs={'property': 'og:image'})
            if og_image:
                image_url = og_image.get('content')
            elif soup.find('img'):
                first_img = soup.find('img')
                image_url = first_img.get('src')
                # Make absolute URL
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(url, image_url)
            
            return {
                'method': 'beautifulsoup',
                'title': title,
                'description': description,
                'content_text': text[:10000],  # Limit size
                'summary': text[:500] if text else '',
                'author': None,
                'publish_date': None,
                'image_url': image_url,
                'html': str(soup)[:50000]  # Limit HTML size
            }
            
        except Exception as e:
            logger.debug(f"BeautifulSoup scraping failed for {url}: {e}")
            return None
    
    def scrape_with_playwright(self, url: str) -> Optional[Dict]:
        """Scrape JavaScript-heavy sites using Playwright"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Navigate and wait for content
                page.goto(url, wait_until='networkidle', timeout=settings.PLAYWRIGHT_TIMEOUT)
                
                # Wait a bit for dynamic content
                page.wait_for_timeout(2000)
                
                # Get content
                content = page.content()
                title = page.title()
                
                browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                    element.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
                
                return {
                    'method': 'playwright',
                    'title': title,
                    'description': None,
                    'content_text': text[:10000],
                    'summary': text[:500] if text else '',
                    'author': None,
                    'publish_date': None,
                    'image_url': None,
                    'html': content[:50000]
                }
                
        except Exception as e:
            logger.debug(f"Playwright scraping failed for {url}: {e}")
            return None
    
    def scrape_url(self, url: str) -> Dict:
        """
        Main scraping method - tries multiple strategies
        
        Returns:
            Dict with status, content, and metadata
        """
        result = {
            'url': url,
            'final_url': url,
            'domain': urlparse(url).netloc,
            'status': 'failed',
            'error': None,
            'content': None
        }
        
        # Skip certain domains
        if self.should_skip_url(url):
            result['status'] = 'skipped'
            result['error'] = 'Domain in skip list'
            return result
        
        # Normalize URL (follow redirects)
        try:
            result['final_url'] = self.normalize_url(url)
        except:
            pass
        
        # Try newspaper3k first (best for articles)
        content = self.scrape_with_newspaper(result['final_url'])
        if content and content.get('content_text') and len(content['content_text']) > 200:
            result['status'] = 'success'
            result['content'] = content
            return result
        
        # Try BeautifulSoup
        content = self.scrape_with_beautifulsoup(result['final_url'])
        if content and content.get('content_text') and len(content['content_text']) > 100:
            result['status'] = 'success'
            result['content'] = content
            return result
        
        # Last resort: Playwright for JS-heavy sites
        content = self.scrape_with_playwright(result['final_url'])
        if content and content.get('content_text'):
            result['status'] = 'success'
            result['content'] = content
            return result
        
        # If we got here, all methods failed
        result['status'] = 'failed'
        result['error'] = 'All scraping methods failed'
        
        return result
    
    def extract_urls_from_tweet(self, tweet_id: str) -> List[str]:
        """Extract URLs from a tweet in the database"""
        query = """
            SELECT raw_json->>'urls' as urls
            FROM tweets
            WHERE tweet_id = %s
        """
        
        result = db.execute_query(query, (tweet_id,))
        
        if not result or not result[0].get('urls'):
            return []
        
        # Parse URLs from JSON array
        import json
        try:
            urls_data = json.loads(result[0]['urls'])
            return urls_data if isinstance(urls_data, list) else []
        except:
            return []
    
    def save_scraped_content(self, tweet_id: str, url: str, scrape_result: Dict) -> bool:
        """Save scraped content to database"""
        try:
            content = scrape_result.get('content', {})
            
            # Insert into database
            query = """
                INSERT INTO linked_content (
                    tweet_id, url, final_url, domain,
                    title, description, content_text, summary,
                    author, publish_date, image_url,
                    scrape_status, scrape_error, scraped_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                ON CONFLICT (tweet_id, url) DO UPDATE SET
                    final_url = EXCLUDED.final_url,
                    title = EXCLUDED.title,
                    content_text = EXCLUDED.content_text,
                    scrape_status = EXCLUDED.scrape_status,
                    scrape_error = EXCLUDED.scrape_error,
                    scraped_at = NOW(),
                    updated_at = NOW()
            """
            
            db.execute_query(
                query,
                (
                    tweet_id,
                    url,
                    scrape_result['final_url'],
                    scrape_result['domain'],
                    content.get('title'),
                    content.get('description'),
                    content.get('content_text'),
                    content.get('summary'),
                    content.get('author'),
                    content.get('publish_date'),
                    content.get('image_url'),
                    scrape_result['status'],
                    scrape_result.get('error'),
                ),
                fetch=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save scraped content: {e}")
            return False
    
    def scrape_tweet_links(self, tweet_id: str) -> int:
        """Scrape all links from a tweet"""
        urls = self.extract_urls_from_tweet(tweet_id)
        
        if not urls:
            return 0
        
        scraped_count = 0
        
        for url in urls:
            logger.info(f"Scraping: {url}")
            
            try:
                result = self.scrape_url(url)
                
                if self.save_scraped_content(tweet_id, url, result):
                    scraped_count += 1
                    logger.info(f"✓ Scraped: {url} ({result['status']})")
                else:
                    logger.warning(f"✗ Failed to save: {url}")
                
                # Respect rate limits
                time.sleep(settings.SCRAPING_DELAY)
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
        
        return scraped_count


# Global scraper instance
scraper = LinkScraper()
