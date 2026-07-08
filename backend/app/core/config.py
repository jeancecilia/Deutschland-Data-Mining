from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KDP Deutschland Opportunity Engine"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://kdp:kdp@postgres:5432/kdp_pipeline"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: str = "http://localhost:3000"
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.1
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    ai_enabled: bool = True
    ai_model: str = "gpt-5.5"
    ai_embedding_model: str = "text-embedding-3-small"
    ai_embedding_dimensions: int | None = 256
    ai_request_timeout_seconds: float = 30.0
    ai_max_text_chars: int = 6000
    ai_semantic_similarity_threshold: float = 0.86
    amazon_fetch_mode: str = "playwright"
    amazon_chrome_bridge_enabled: bool = True
    amazon_chrome_bridge_url: str = "http://host.docker.internal:9223"
    amazon_chrome_bridge_timeout_seconds: float = 75.0
    amazon_fetch_min_interval_seconds: float = 3.0
    amazon_browser_enabled: bool = True
    amazon_browser_headless: bool = True
    amazon_browser_timeout_seconds: float = 30.0
    amazon_browser_wait_after_load_ms: int = 1200
    amazon_browser_locale: str = "de-DE"
    amazon_browser_timezone_id: str = "Europe/Berlin"
    amazon_browser_storage_state_path: str = "/app/generated_reports/amazon-storage-state.json"
    discovery_auto_promote_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def ai_runtime_enabled(self) -> bool:
        return self.ai_enabled and bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
