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

    # Database
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/diet_ai"
    mongo_url: str = "mongodb://localhost:27017"

    # AI
    use_mock_ai: bool = True
    openai_api_key: str | None = None

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