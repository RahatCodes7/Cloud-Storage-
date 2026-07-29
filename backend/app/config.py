"""Environment variable loading and validation."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_string: str = ""
    telegram_storage_chat_id: int = 0

    # Auth
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # Registration
    allow_public_registration: bool = True

    # Upload limits
    max_upload_mb: int = 2000  # 2GB default

    # Database
    database_url: str = "sqlite+aiosqlite:///./televault.db"

    # CORS
    cors_origins: str = "http://localhost:5173,https://trove-delta.vercel.app"

    # Trash auto-purge days
    trash_purge_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
