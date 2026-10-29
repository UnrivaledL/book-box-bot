from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    google_books_api_key: str
    database_url: str = "sqlite+aiosqlite:///./book_box.db"
    log_level: str = "INFO"

    proxy_url: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()