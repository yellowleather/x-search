"""
RAG (Retrieval-Augmented Generation) pipeline for X-Factor
Handles semantic search and AI-powered answer generation
"""

import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.config.settings import settings
from src.database.connection import db
from src.processing.embedder import embedder
from src.retrieval.vector_store import vector_store_manager
from src.utils.logger import logger


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline"""

    def __init__(self):
        self.top_k = settings.TOP_K_RESULTS
        self.min_similarity = settings.MIN_SIMILARITY_THRESHOLD

        # Initialize LLM client (prefer Anthropic, fall back to OpenAI)
        self.llm_available = False
        self.llm_provider = None
        self.llm_client = None

        if settings.ANTHROPIC_API_KEY:
            try:
                from anthropic import Anthropic
                self.llm_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self.llm_provider = "anthropic"
                self.llm_available = True
                logger.info("Claude API initialized")
            except ImportError:
                logger.warning("anthropic package not installed")
        elif settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.llm_provider = "openai"
                self.llm_available = True
                logger.info("OpenAI API initialized")
            except ImportError:
                logger.warning("openai package not installed")

        if not self.llm_available:
            logger.warning("No LLM API key found - LLM features disabled")
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """Generate embedding for search query"""
        try:
            embedding = embedder.embed_query(query)
            if embedding is not None:
                return embedding.tolist()
            return None
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return None
    
    def vector_search_tweets(self, query_embedding: List[float], limit: int = None) -> List[Dict]:
        """
        Perform vector similarity search on tweets using the local FAISS store
        """
        limit = limit or self.top_k
        
        try:
            np_query = np.asarray(query_embedding, dtype="float32")
            results = vector_store_manager.search_tweets(np_query, limit)
            filtered = [item for item in results if item.get("similarity", 0) >= self.min_similarity]
            return filtered
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def vector_search_links(self, query_embedding: List[float], limit: int = None) -> List[Dict]:
        """
        Perform vector similarity search on linked content via FAISS store
        """
        limit = limit or self.top_k
        
        try:
            np_query = np.asarray(query_embedding, dtype="float32")
            results = vector_store_manager.search_links(np_query, limit)
            filtered = [item for item in results if item.get("similarity", 0) >= self.min_similarity]
            return filtered
        except Exception as e:
            logger.error(f"Vector search on links failed: {e}")
            return []
    
    def keyword_search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Full-text keyword search as fallback or supplement
        """
        query_sql = """
            SELECT 
                tweet_id,
                author_username,
                author_name,
                text,
                created_at,
                liked_at,
                url,
                ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s)) as rank
            FROM tweets
            WHERE to_tsvector('english', text) @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        """
        
        try:
            results = db.execute_query(query_sql, (query, query, limit))
            return results or []
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Hybrid search combining vector similarity and keyword matching
        Returns: (tweet_results, link_results)
        """
        limit = limit or self.top_k
        
        # Generate query embedding
        query_embedding = self.embed_query(query)
        
        if not query_embedding:
            logger.warning("Could not generate query embedding, falling back to keyword search")
            tweet_results = self.keyword_search(query, limit)
            return tweet_results, []
        
        # Vector search on both tweets and links
        tweet_results = self.vector_search_tweets(query_embedding, limit)
        link_results = self.vector_search_links(query_embedding, limit)
        
        logger.info(f"Found {len(tweet_results)} tweets and {len(link_results)} links")
        
        return tweet_results, link_results
    
    def format_context(self, tweet_results: List[Dict], link_results: List[Dict], 
                      max_tokens: int = None) -> str:
        """
        Format search results into context for LLM
        """
        max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS
        
        context_parts = []
        
        # Add tweets
        if tweet_results:
            context_parts.append("=== RELEVANT TWEETS ===\n")
            for i, tweet in enumerate(tweet_results[:10], 1):  # Limit to top 10
                context_parts.append(
                    f"[{i}] @{tweet['author_username']} ({tweet.get('liked_at', 'N/A')})\n"
                    f"    {tweet['text']}\n"
                    f"    URL: {tweet.get('url', 'N/A')}\n"
                    f"    Similarity: {tweet.get('similarity', 0):.3f}\n"
                )
        
        # Add linked articles
        if link_results:
            context_parts.append("\n=== RELEVANT ARTICLES/CONTENT ===\n")
            for i, link in enumerate(link_results[:10], 1):  # Limit to top 10
                summary = link.get('summary', '') or link.get('content_text', '')[:500]
                context_parts.append(
                    f"[{i}] {link.get('title', 'Untitled')}\n"
                    f"    URL: {link['url']}\n"
                    f"    Domain: {link.get('domain', 'N/A')}\n"
                    f"    From tweet by: @{link.get('tweet_author', 'unknown')}\n"
                    f"    Summary: {summary}...\n"
                    f"    Similarity: {link.get('similarity', 0):.3f}\n"
                )
        
        context = "".join(context_parts)
        
        # Truncate if too long (rough token estimation: 1 token ≈ 4 chars)
        estimated_tokens = len(context) // 4
        if estimated_tokens > max_tokens:
            char_limit = max_tokens * 4
            context = context[:char_limit] + "\n\n[Context truncated due to length...]"
        
        return context
    
    def generate_answer(self, query: str, context: str) -> Dict:
        """
        Generate answer using LLM API (Anthropic Claude or OpenAI)
        """
        if not self.llm_available:
            return {
                'answer': "LLM not available. Please configure ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file.",
                'model': None,
                'tokens': 0
            }

        system_prompt = """You are an AI assistant helping analyze a personal collection of liked tweets and articles.
Your task is to answer questions based on the provided context from the user's Twitter likes.

Guidelines:
1. Base your answers ONLY on the provided context
2. Be specific and cite relevant tweets or articles when possible
3. If the context doesn't contain relevant information, say so honestly
4. Provide a balanced, nuanced view when multiple perspectives exist
5. Format your response clearly with relevant quotes or summaries
6. Include tweet authors and article titles when referencing sources"""

        user_message = f"""Query: {query}

Context from liked tweets and articles:

{context}

Please provide a comprehensive answer to the query based on the above context.
If you reference specific tweets or articles, mention the author/source."""

        try:
            start_time = time.time()
            answer = ""
            tokens = 0
            elapsed_ms = 0

            if self.llm_provider == "anthropic":
                response = self.llm_client.messages.create(  # type: ignore
                    model=settings.LLM_MODEL,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    temperature=settings.LLM_TEMPERATURE,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )
                elapsed_ms = int((time.time() - start_time) * 1000)
                answer = response.content[0].text  # type: ignore
                tokens = response.usage.input_tokens + response.usage.output_tokens

            elif self.llm_provider == "openai":
                response = self.llm_client.chat.completions.create(  # type: ignore
                    model=settings.LLM_MODEL if settings.LLM_MODEL.startswith("gpt") else "gpt-4-turbo-preview",
                    max_tokens=settings.LLM_MAX_TOKENS,
                    temperature=settings.LLM_TEMPERATURE,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                elapsed_ms = int((time.time() - start_time) * 1000)
                answer = response.choices[0].message.content or ""
                tokens = response.usage.total_tokens if response.usage else 0
            else:
                return {
                    'answer': "LLM provider not configured correctly.",
                    'model': None,
                    'tokens': 0,
                    'time_ms': 0
                }

            return {
                'answer': answer,
                'model': settings.LLM_MODEL,
                'tokens': tokens,
                'time_ms': elapsed_ms
            }

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                'answer': f"Error generating answer: {str(e)}",
                'model': settings.LLM_MODEL,
                'tokens': 0,
                'error': str(e)
            }
    
    def query(self, query_text: str, return_sources: bool = True) -> Dict:
        """
        Main query method - performs search and generates answer
        
        Returns:
            Dict with 'answer', 'sources', and metadata
        """
        logger.info(f"Processing query: {query_text}")
        
        start_time = time.time()
        
        # Step 1: Hybrid search
        search_start = time.time()
        tweet_results, link_results = self.hybrid_search(query_text)
        search_time_ms = int((time.time() - search_start) * 1000)
        
        if not tweet_results and not link_results:
            return {
                'query': query_text,
                'answer': "No relevant content found in your liked tweets. Try a different query.",
                'sources': {
                    'tweets': [],
                    'links': []
                },
                'metadata': {
                    'tweets_found': 0,
                    'links_found': 0,
                    'search_time_ms': search_time_ms,
                    'llm_time_ms': 0,
                    'total_time_ms': int((time.time() - start_time) * 1000)
                }
            }
        
        # Step 2: Format context
        context = self.format_context(tweet_results, link_results)
        
        # Step 3: Generate answer
        llm_result = self.generate_answer(query_text, context)
        
        # Step 4: Save query to database
        self._save_query(query_text, tweet_results, link_results, search_time_ms, 
                        llm_result.get('time_ms', 0))
        
        total_time_ms = int((time.time() - start_time) * 1000)
        
        result = {
            'query': query_text,
            'answer': llm_result['answer'],
            'sources': {
                'tweets': tweet_results[:settings.MAX_DISPLAY_RESULTS] if return_sources else [],
                'links': link_results[:settings.MAX_DISPLAY_RESULTS] if return_sources else []
            },
            'metadata': {
                'tweets_found': len(tweet_results),
                'links_found': len(link_results),
                'search_time_ms': search_time_ms,
                'llm_time_ms': llm_result.get('time_ms', 0),
                'total_time_ms': total_time_ms,
                'model': llm_result.get('model'),
                'tokens': llm_result.get('tokens', 0)
            }
        }
        
        logger.info(f"Query completed in {total_time_ms}ms")
        
        return result
    
    def _save_query(self, query_text: str, tweet_results: List, link_results: List,
                   search_time_ms: int, llm_time_ms: int):
        """Save query to database for analytics"""
        try:
            import json
            
            results_returned = {
                'tweets': [t['tweet_id'] for t in tweet_results[:10]],
                'links': [l['id'] for l in link_results[:10]]
            }
            
            query = """
                INSERT INTO user_queries (
                    query_text, results_count, results_returned,
                    search_time_ms, llm_time_ms, total_time_ms
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            db.execute_query(
                query,
                (
                    query_text,
                    len(tweet_results) + len(link_results),
                    json.dumps(results_returned),
                    search_time_ms,
                    llm_time_ms,
                    search_time_ms + llm_time_ms
                ),
                fetch=False
            )
        except Exception as e:
            logger.error(f"Failed to save query: {e}")


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()


if __name__ == "__main__":
    """Test the RAG pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test X-Factor RAG Pipeline")
    parser.add_argument('query', nargs='+', help='Search query')
    
    args = parser.parse_args()
    query_text = ' '.join(args.query)
    
    result = rag_pipeline.query(query_text)
    
    print("\n" + "=" * 80)
    print(f"QUERY: {result['query']}")
    print("=" * 80)
    print(f"\n{result['answer']}\n")
    print("=" * 80)
    print(f"Found {result['metadata']['tweets_found']} tweets, "
          f"{result['metadata']['links_found']} links")
    print(f"Search time: {result['metadata']['search_time_ms']}ms")
    print(f"LLM time: {result['metadata']['llm_time_ms']}ms")
    print(f"Total time: {result['metadata']['total_time_ms']}ms")
    print("=" * 80)
