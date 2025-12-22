"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "UniversalAPI"
    app_env: str = "development"
    debug: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "auto"  # auto (based on app_env), console, or json
    logs_dir: str = "./logs"
    log_to_file: bool = True  # Always log to files
    log_file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_file_backup_count: int = 5

    # Shutdown
    shutdown_timeout_seconds: int = 30  # Kubernetes standard grace period

    # Database Health
    require_migrations_on_startup: bool = True
    """If True, application won't start if database migrations are not up to date.
    If False, only logs a warning. Default: True for maximum safety."""

    # Database
    database_url: str = "postgresql+asyncpg://universalapi:universalapi_dev@localhost:5432/universalapi"
    database_url_sync: str = "postgresql://universalapi:universalapi_dev@localhost:5432/universalapi"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    api_key_prefix: str = "uapi_"

    # AI Providers
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # Storage
    storage_type: str = "local"
    storage_local_path: str = "./storage"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_s3_region: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # Plugins
    plugins_enabled: list[str] = ["upload", "audio_transcription"]

    @field_validator("plugins_enabled", mode="before")
    @classmethod
    def parse_plugins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [p.strip() for p in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
