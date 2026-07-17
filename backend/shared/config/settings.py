from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Diet AI"
    app_env: str = "dev"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **data):
        super().__init__(**data)
        if os.getenv("TESTING") or self.app_env == "test":
            self.app_debug = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()