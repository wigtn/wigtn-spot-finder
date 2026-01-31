"""
Application settings using Pydantic Settings.
Loads configuration from environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "spotfinder"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # vLLM / LLM (legacy - used when use_upstage=False)
    vllm_base_url: str = Field(default="http://localhost:8000/v1")
    vllm_model_name: str = Field(default="Qwen/Qwen2.5-7B-Instruct")
    vllm_api_key: str = Field(default="EMPTY")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, ge=1)

    # Upstage API
    upstage_api_key: str | None = Field(default=None)
    upstage_base_url: str = Field(default="https://api.upstage.ai/v1/solar")
    upstage_chat_model: str = Field(default="solar-pro")
    upstage_embedding_model: str = Field(default="solar-embedding-1-large")
    upstage_embedding_url: str = Field(default="https://api.upstage.ai/v1/solar/embeddings")
    upstage_document_url: str = Field(default="https://api.upstage.ai/v1/document-digitization")
    upstage_document_model: str = Field(default="document-parse-260128")
    upstage_embedding_dimension: int = Field(default=4096)
    use_upstage: bool = Field(default=True)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/spotfinder_db"
    )
    db_pool_size: int = Field(default=10, ge=1)
    db_max_overflow: int = Field(default=20, ge=0)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_pool_size: int = Field(default=10, ge=1)

    # Vector DB (Qdrant)
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection_name: str = Field(default="spotfinder_memories")

    # Embedding Model
    embedding_model_name: str = Field(default="BAAI/bge-m3")
    embedding_dimension: int = Field(default=1024)

    # Naver Map API
    naver_map_client_id: str = Field(default="")
    naver_map_client_secret: str = Field(default="")
    naver_map_api_url: str = Field(default="https://openapi.naver.com/v1")

    # Papago Translation API
    papago_client_id: str = Field(default="")
    papago_client_secret: str = Field(default="")

    # Observability - Sentry
    sentry_dsn: str | None = Field(default=None)
    sentry_environment: str = Field(default="development")
    sentry_traces_sample_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    sentry_profiles_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # Observability - Better Stack (Logtail)
    logtail_token: str | None = Field(default=None)

    # Observability - Slack
    slack_webhook_url: str | None = Field(default=None)

    # Rate Limiting
    rate_limit_requests: int = Field(default=60, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)  # seconds
    rate_limit_chat: int = Field(default=20, ge=1)
    rate_limit_chat_stream: int = Field(default=10, ge=1)
    rate_limit_requests_per_minute: int = Field(default=30, ge=1)
    rate_limit_requests_per_hour: int = Field(default=500, ge=1)

    # OpenAI (fallback for embeddings)
    openai_api_key: str | None = Field(default=None)

    # Embedding Model
    embedding_model: str = Field(default="text-embedding-3-small")

    # Context Engineering
    context_soft_limit_tokens: int = Field(default=6000, ge=1000)
    context_hard_limit_tokens: int = Field(default=8000, ge=1000)
    recent_messages_count: int = Field(default=20, ge=5)
    memory_retrieval_top_k: int = Field(default=3, ge=1)
    memory_similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # Travel Features
    enable_place_caching: bool = Field(default=True)
    place_cache_ttl_hours: int = Field(default=1, ge=1)
    default_language: str = Field(default="ja")  # Default to Japanese for Seongsu popup finder
    supported_languages: list[str] = Field(default=["ja", "en", "ko", "zh"])
    krw_to_usd_rate: float = Field(default=1400.0, ge=1.0)  # KRW to USD exchange rate

    # Instagram Scraping
    instagram_username: str | None = Field(default=None)
    instagram_password: str | None = Field(default=None)
    instagram_target_account: str = Field(default="seongsu_bible")
    scrape_interval_hours: int = Field(default=6, ge=1)
    scrape_delay_seconds: float = Field(default=1.0, ge=0.0)
    min_confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # SQLite Database
    sqlite_db_path: str = Field(default="data/popups.db")

    # Supabase Auth
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")  # anon/public key

    # Feature Flags
    observer_agent_enabled: bool = Field(default=True)
    anomaly_detection_enabled: bool = Field(default=True)

    @field_validator("supported_languages", mode="before")
    @classmethod
    def parse_supported_languages(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience exports
settings = get_settings()
