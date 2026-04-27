"""إعدادات البوت"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """إعدادات التطبيق"""

    # Bot
    BOT_TOKEN: str
    OWNER_ID: int

    # Database
    DATABASE_URL: str = "sqlite:///library.db"

    # AI
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "google/gemini-1.5-flash"
    GEMINI_API_KEY: str = ""

    # Embeddings
    EMBEDDINGS_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # App
    DEBUG: bool = False
    WEBHOOK_URL: str = ""
    PORT: int = 8080

    # Features
    ENABLE_AI_SUMMARY: bool = True
    ENABLE_SEMANTIC_SEARCH: bool = True
    ENABLE_REFERRAL_SYSTEM: bool = True
    ENABLE_LEADERBOARD: bool = True
    ENABLE_COMMENTS: bool = True
    ENABLE_BATCH_UPLOAD: bool = True
    ENABLE_AI_INSIGHTS: bool = True
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_PACKS: bool = True

    # Rate Limiting
    RATE_LIMIT_MESSAGES: int = 30
    RATE_LIMIT_WINDOW: int = 60

    # Backup
    BACKUP_CHANNEL_ID: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """الحصول على الإعدادات (cached)"""
    return Settings()
