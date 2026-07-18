from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Diet AI"
    app_env: str = "dev"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    testing: bool = False

    # CORS — comma-separated origins allowed to call the API (the frontend's
    # dev server by default). A plain comma-separated string rather than a
    # list field: pydantic-settings would otherwise expect JSON syntax in a
    # .env value, which is awkward to hand-edit.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # Database
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/diet_ai"
    mongo_url: str = "mongodb://localhost:27017"

    # AI — provider selection: "mock" | "claude" | "ollama"
    ai_provider: str = "mock"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-4-8"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"

    # Email — provider selection: "mock" | "smtp"
    email_provider: str = "mock"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from_address: str = "noreply@dietai.local"

    # Failed-email retry: a background timer retries FAILED email_logs rows
    email_retry_interval_seconds: int = 180
    email_retry_max_attempts: int = 10
    email_retry_batch_limit: int = 50

    # SFTP — provider selection: "mock" | "sftp". Diet-plan CSV exports are
    # archived here so a user can re-download a previously generated export.
    sftp_provider: str = "mock"
    sftp_host: str = "localhost"
    sftp_port: int = 2222
    sftp_username: str = "dietai"
    sftp_password: str = "dietai"
    sftp_remote_dir: str = "/upload"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _disable_debug_when_testing(self) -> "Settings":
        if self.testing or self.app_env == "test":
            self.app_debug = False
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()