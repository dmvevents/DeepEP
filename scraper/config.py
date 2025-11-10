"""
Configuration settings for scraper service
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Scraper configuration"""

    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # openai, anthropic, litellm
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4000

    # Web Search Configuration
    WEB_SEARCH_PROVIDER: str = "serpapi"  # serpapi, brave
    SERP_API_KEY: Optional[str] = None
    BRAVE_SEARCH_API_KEY: Optional[str] = None
    MAX_SEARCH_RESULTS: int = 10

    # Database Configuration
    DATABASE_URL: str = "postgresql://admin:password@localhost:5432/mortgage_calc"

    # Scraper Behavior
    SCRAPER_TIMEOUT: int = 300  # seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    MAX_REASONING_LOOPS: int = 5
    MIN_CONFIDENCE_SCORE: int = 70
    MIN_COMPLETENESS_SCORE: int = 80

    # Caching
    CACHE_EXPIRY_DAYS: int = 30
    USE_CACHED_RESULTS: bool = True

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 20
    MAX_CONCURRENT_SCRAPES: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Browser/HTTP Configuration
    USER_AGENT: str = "Mozilla/5.0 (Mortgage Calculator Scraper Bot)"
    REQUEST_TIMEOUT: int = 30
    FOLLOW_REDIRECTS: bool = True
    MAX_REDIRECTS: int = 5

    # Validation
    REQUIRE_OFFICIAL_SOURCES: bool = True
    OFFICIAL_SOURCE_PATTERNS: list = [".gov", ".us", "treasurer", "tax-rates"]
    BLACKLIST_PATTERNS: list = ["realtor.com", "zillow.com", "trulia.com"]

    # Performance
    ENABLE_ASYNC: bool = True
    WORKER_THREADS: int = 4

    # Testing
    TEST_MODE: bool = False
    MOCK_LLM_RESPONSES: bool = False

    class Config:
        env_file = ".env.scraper"
        case_sensitive = True


# Create settings instance
settings = Settings()
