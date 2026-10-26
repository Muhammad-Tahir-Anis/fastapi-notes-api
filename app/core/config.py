from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: PostgresDsn
    secret_key: str
    access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
