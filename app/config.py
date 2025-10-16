"""
Configuration management for News System
Centralized configuration with validation
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "News Management System"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///news.db"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    SESSION_EXPIRE_HOURS: int = 24
    
    # API Keys
    WEBZ_API_KEYS: List[str] = []
    GEMINI_API_KEYS: List[str] = []
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL: str = os.getenv("TELEGRAM_CHANNEL", "")
    
    # Proxy
    SOCKS5_PROXY: str = os.getenv("SOCKS5_PROXY", "")
    
    # Crawler Settings
    CRAWLER_DEFAULT_LANGUAGE: str = "english"
    CRAWLER_MAX_PAGES: int = 5
    CRAWLER_MAX_RESULTS: int = 100
    CRAWLER_TIMEOUT: int = 30
    
    # Translation
    MAX_TRANSLATION_LENGTH: int = 15000
    TRANSLATION_TIMEOUT: int = 30
    
    # Scheduler
    CRAWLER_INTERVAL_HOURS: int = 1
    PUBLISHER_INTERVAL_MINUTES: int = 30
    
    # Logging
    LOG_FILE: str = "webz.log"
    LOG_LEVEL: str = "INFO"
    
    @validator("WEBZ_API_KEYS", pre=True)
    def parse_webz_keys(cls, v):
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v
    
    @validator("GEMINI_API_KEYS", pre=True)
    def parse_gemini_keys(cls, v):
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    @validator("ADMIN_PASSWORD_HASH")
    def validate_admin_hash(cls, v):
        if not v:
            raise ValueError("ADMIN_PASSWORD_HASH is required")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings(
    WEBZ_API_KEYS=os.getenv("WEBZ_API_KEYS", ""),
    GEMINI_API_KEYS=os.getenv("GEMINI_API_KEYS", "")
)


def validate_environment():
    """Validate all required environment variables"""
    required_vars = {
        "SECRET_KEY": "Secret key for session encryption",
        "ADMIN_USERNAME": "Admin username",
        "ADMIN_PASSWORD_HASH": "Hashed admin password",
        "WEBZ_API_KEYS": "Webz.io API keys",
        "TELEGRAM_BOT_TOKEN": "Telegram bot token",
        "TELEGRAM_CHANNEL": "Telegram channel ID",
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or not value.strip():
            missing.append(f"{var} ({description})")
    
    if missing:
        raise ValueError(
            f"Missing required environment variables:\n" + 
            "\n".join(f"  - {var}" for var in missing)
        )


# Validate on import
validate_environment()
