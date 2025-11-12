"""
X-Factor Streamlit UI
Main user interface for querying the Twitter intelligence system
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from src.retrieval.rag_pipeline import rag_pipeline
from src.processing.batch_processor import processor
from src.database.connection import db
from src.utils.logger import logger


# Page configuration
st.set_page_config(
    page_title="X-Factor - Personal Twitter Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .source-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .tweet-author {
        font-weight: bold;
        color: #1DA1F2;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None


def get_system_stats():
    """Get system statistics"""
    try:
        stats = processor.get_processing_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {}


def display_tweet_source(tweet):
    """Display a tweet source"""
    st.markdown(f"""
    <div class="source-card">
        <div class="tweet-author">@{tweet['author_username']}</div>
        <div style="margin-top: 0.5rem;">{tweet['text']}</div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #666;">
            📅 {tweet.get('created_at', 'N/A')} | 
            ❤️ {tweet.get('like_count', 0)} | 
            🔄 {tweet.get('retweet_count', 0)} |
            🎯 Similarity: {tweet.get('similarity', 0):.2%}
        </div>
        <a href="{tweet.get('url', '#')}" target="_blank" style="font-size: 0.9rem;">View on Twitter →</a>
    </div>
    """, unsafe_allow_html=True)


def display_link_source(link):
    """Display a linked article source"""
    st.markdown(f"""
    <div class="source-card">
        <div style="font-weight: bold; font-size: 1.1rem;">{link.get('title', 'Untitled')}</div>
        <div style="margin-top: 0.5rem; color: #666;">{link.get('domain', 'unknown')}</div>
        <div style="margin-top: 0.5rem;">{link.get('summary', '')}</div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #666;">
            From tweet by @{link.get('tweet_author', 'unknown')} |
            🎯 Similarity: {link.get('similarity', 0):.2%}
        </div>
        <a href="{link['url']}" target="_blank" style="font-size: 0.9rem;">Read Article →</a>
    </div>
    """, unsafe_allow_html=True)


def main_page():
    """Main query page"""
    st.markdown('<div class="main-header">🧠 X-Factor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your Personal Twitter Intelligence System</div>', unsafe_allow_html=True)
    
    # Query input
    query = st.text_input(
        "Ask anything about your liked tweets:",
        placeholder="e.g., What are the key points about AI safety from recent discussions?",
        help="Enter your question and X-Factor will search through your liked tweets and articles"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.current_result = None
        st.rerun()
    
    # Process query
    if search_button and query:
        with st.spinner("🔍 Searching through your tweets..."):
            try:
                result = rag_pipeline.query(query, return_sources=True)
                st.session_state.current_result = result
                st.session_state.query_history.append({
                    'query': query,
                    'timestamp': datetime.now(),
                    'tweets_found': result['metadata']['tweets_found'],
                    'links_found': result['metadata']['links_found']
                })
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                logger.error(f"Query error: {e}")
    
    # Display results
    if st.session_state.current_result:
        result = st.session_state.current_result
        
        st.markdown("---")
        
        # Answer section
        st.markdown("### 💡 Answer")
        st.markdown(result['answer'])
        
        # Metadata
        metadata = result['metadata']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tweets Found", metadata['tweets_found'])
        with col2:
            st.metric("Articles Found", metadata['links_found'])
        with col3:
            st.metric("Search Time", f"{metadata['search_time_ms']}ms")
        with col4:
            st.metric("Total Time", f"{metadata['total_time_ms']}ms")
        
        st.markdown("---")
        
        # Sources section
        st.markdown("### 📚 Sources")
        
        tab1, tab2 = st.tabs(["🐦 Tweets", "📰 Articles"])
        
        with tab1:
            tweets = result['sources']['tweets']
            if tweets:
                for tweet in tweets:
                    display_tweet_source(tweet)
            else:
                st.info("No relevant tweets found")
        
        with tab2:
            links = result['sources']['links']
            if links:
                for link in links:
                    display_link_source(link)
            else:
                st.info("No relevant articles found")


def stats_page():
    """Statistics and analytics page"""
    st.markdown("## 📊 System Statistics")
    
    try:
        stats = get_system_stats()
        
        if not stats:
            st.warning("No statistics available yet. Import some tweets first!")
            return
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: bold; color: #1DA1F2;">
                    {}</div>
                <div>Total Tweets</div>
            </div>
            """.format(stats.get('total_tweets', 0)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: bold; color: #17BF63;">
                    {}</div>
                <div>With Embeddings</div>
            </div>
            """.format(stats.get('tweets_with_embeddings', 0)), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: bold; color: #F91880;">
                    {}</div>
                <div>Linked Articles</div>
            </div>
            """.format(stats.get('total_links', 0)), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: bold; color: #794BC4;">
                    {}</div>
                <div>Unique Authors</div>
            </div>
            """.format(stats.get('unique_authors', 0)), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Processing status
        st.markdown("### 🔄 Processing Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            processed_pct = (stats.get('tweets_processed', 0) / stats.get('total_tweets', 1)) * 100
            st.metric("Tweets Processed", 
                     f"{stats.get('tweets_processed', 0)} / {stats.get('total_tweets', 0)}",
                     f"{processed_pct:.1f}%")
        
        with col2:
            links_scraped_pct = (stats.get('links_scraped_successfully', 0) / stats.get('total_links', 1)) * 100 if stats.get('total_links', 0) > 0 else 0
            st.metric("Links Scraped Successfully", 
                     f"{stats.get('links_scraped_successfully', 0)} / {stats.get('total_links', 0)}",
                     f"{links_scraped_pct:.1f}%")
        
        # Recent queries
        st.markdown("---")
        st.markdown("### 🔍 Recent Queries")
        
        query = """
            SELECT query_text, created_at, results_count, total_time_ms
            FROM user_queries
            ORDER BY created_at DESC
            LIMIT 10
        """
        
        recent_queries = db.execute_query(query)
        
        if recent_queries:
            df = pd.DataFrame(recent_queries)
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No queries yet")
        
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        logger.error(f"Stats page error: {e}")


def settings_page():
    """Settings and management page"""
    st.markdown("## ⚙️ Settings & Management")
    
    st.markdown("### 🔄 Data Processing")
    
    st.info("""
    Run these tasks to process your tweets:
    1. **Scrape Links**: Extract and scrape content from URLs in tweets
    2. **Generate Embeddings**: Create vector embeddings for semantic search
    3. **Run Full Pipeline**: Execute both tasks in sequence
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔗 Scrape Links", use_container_width=True):
            with st.spinner("Scraping links..."):
                try:
                    stats = processor.scrape_pending_links()
                    st.success(f"✓ Scraped {stats['links_scraped']} links from {stats['tweets_processed']} tweets")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("🧠 Generate Embeddings", use_container_width=True):
            with st.spinner("Generating embeddings..."):
                try:
                    stats = processor.generate_all_embeddings()
                    st.success(f"✓ Generated {stats['embeddings_generated']} embeddings")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("⚡ Run Full Pipeline", use_container_width=True, type="primary"):
            with st.spinner("Running full pipeline..."):
                try:
                    stats = processor.run_full_pipeline()
                    st.success(f"""
                    ✓ Pipeline complete!
                    - Tweets processed: {stats['tweets_processed']}
                    - Links scraped: {stats['links_scraped']}
                    - Embeddings generated: {stats['embeddings_generated']}
                    """)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    st.markdown("### 📊 Current Status")
    stats = get_system_stats()
    
    if stats:
        progress_data = {
            'Metric': ['Tweets Embedded', 'Links Scraped', 'Tweets Processed'],
            'Progress': [
                stats.get('tweets_with_embeddings', 0) / max(stats.get('total_tweets', 1), 1),
                stats.get('links_scraped_successfully', 0) / max(stats.get('total_links', 1), 1),
                stats.get('tweets_processed', 0) / max(stats.get('total_tweets', 1), 1)
            ]
        }
        
        df = pd.DataFrame(progress_data)
        st.bar_chart(df.set_index('Metric'))


def main():
    """Main application"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        page = st.radio(
            "Select Page:",
            ["🔍 Search", "📊 Statistics", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        st.markdown("### 📝 About")
        st.markdown("""
        **X-Factor** is your personal AI-powered intelligence system for Twitter likes.
        
        It helps you:
        - 🔍 Search through liked tweets semantically
        - 💡 Get AI-generated insights
        - 📚 Analyze linked articles
        - 🧠 Build your personal knowledge base
        """)
        
        st.markdown("---")
        
        # Quick stats
        stats = get_system_stats()
        if stats:
            st.markdown("### 📊 Quick Stats")
            st.metric("Total Tweets", stats.get('total_tweets', 0))
            st.metric("With Embeddings", stats.get('tweets_with_embeddings', 0))
            st.metric("Linked Articles", stats.get('total_links', 0))
    
    # Main content
    if "🔍 Search" in page:
        main_page()
    elif "📊 Statistics" in page:
        stats_page()
    elif "⚙️ Settings" in page:
        settings_page()


if __name__ == "__main__":
    main()
