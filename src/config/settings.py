"""
X-Search Configuration Module
Loads and validates environment variables
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)


class Settings:
    """Application settings loaded from environment variables"""
    
    # ==========================================
    # Database Configuration
    # ==========================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://xsearch_user@localhost:5432/xsearch")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "xsearch")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "xsearch_user")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    
    # Embedding/vector configuration
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", str(VECTOR_STORE_DIR))
    
    # ==========================================
    # AI Services
    # ==========================================
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # ==========================================
    # Twitter Configuration
    # ==========================================
    TWITTER_API_KEY: Optional[str] = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET: Optional[str] = os.getenv("TWITTER_API_SECRET")
    TWITTER_BEARER_TOKEN: Optional[str] = os.getenv("TWITTER_BEARER_TOKEN")
    TWITTER_ACCESS_TOKEN: Optional[str] = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    TWITTER_USERNAME: Optional[str] = os.getenv("TWITTER_USERNAME")
    
    # ==========================================
    # Embedding Model
    # ==========================================
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")  # 'cpu' or 'cuda'
    
    # ==========================================
    # Application Settings
    # ==========================================
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(LOGS_DIR / "xsearch.log"))
    
    # Processing
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "50"))
    SCRAPING_DELAY: int = int(os.getenv("SCRAPING_DELAY", "1"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))
    
    # ==========================================
    # API Configuration
    # ==========================================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # ==========================================
    # UI Configuration
    # ==========================================
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    # ==========================================
    # Scheduling
    # ==========================================
    DAILY_SYNC_HOUR: int = int(os.getenv("DAILY_SYNC_HOUR", "2"))
    DAILY_SYNC_MINUTE: int = int(os.getenv("DAILY_SYNC_MINUTE", "0"))
    
    # ==========================================
    # Feature Flags
    # ==========================================
    ENABLE_TWITTER_API: bool = os.getenv("ENABLE_TWITTER_API", "false").lower() == "true"
    ENABLE_LINK_SCRAPING: bool = os.getenv("ENABLE_LINK_SCRAPING", "false").lower() == "true"
    ENABLE_CONTEXT_FETCHING: bool = os.getenv("ENABLE_CONTEXT_FETCHING", "false").lower() == "true"
    ENABLE_EMBEDDING_GENERATION: bool = os.getenv("ENABLE_EMBEDDING_GENERATION", "true").lower() == "true"
    
    # ==========================================
    # Rate Limiting
    # ==========================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "100"))
    
    # ==========================================
    # Cache Configuration
    # ==========================================
    ENABLE_QUERY_CACHE: bool = os.getenv("ENABLE_QUERY_CACHE", "true").lower() == "true"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # ==========================================
    # Search Configuration
    # ==========================================
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "20"))
    MAX_DISPLAY_RESULTS: int = int(os.getenv("MAX_DISPLAY_RESULTS", "5"))
    MIN_SIMILARITY_THRESHOLD: float = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.5"))
    
    # ==========================================
    # LLM Configuration
    # ==========================================
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
    
    # ==========================================
    # Development Settings
    # ==========================================
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"
    
    # Playwright
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    PLAYWRIGHT_TIMEOUT: int = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []
        
        # LLM key is optional - warn but don't fail
        if not cls.ANTHROPIC_API_KEY and not cls.OPENAI_API_KEY:
            print("Warning: No LLM API key found. AI-powered answers will be disabled.")
        
        if cls.ENABLE_TWITTER_API:
            if not cls.TWITTER_BEARER_TOKEN:
                errors.append("TWITTER_BEARER_TOKEN required when ENABLE_TWITTER_API=true")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.APP_ENV == "production"
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get formatted database URL"""
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return f"postgresql://{cls.DATABASE_USER}:{cls.DATABASE_PASSWORD}@{cls.DATABASE_HOST}:{cls.DATABASE_PORT}/{cls.DATABASE_NAME}"


# Create global settings instance
settings = Settings()

# Validate settings on import (optional, comment out if you want lazy validation)
try:
    settings.validate()
except ValueError as e:
    print(f"Warning: {e}")
    print("Some features may not work properly. Check your .env file.")
