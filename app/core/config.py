from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+asyncpg://fielddata:fielddata@localhost:5432/fielddata"
    default_user_name: str = "Demo User"
    default_user_phone: str = "5491100000000"
    alert_evaluation_cron: str = "*/15 * * * *"
    seed_on_startup: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
