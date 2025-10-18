"""
Configuration management for News System
Centralized configuration with validation
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "News Management System"
    DEBUG: bool = False
    
    # Server Configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    USE_HTTPS: bool = False
    
    # SSL Configuration
    SSL_CERT_PATH: str = ""
    SSL_KEY_PATH: str = ""
    
    # Secret Path for Admin Panel (randomized for security)
    SECRET_PATH: str = "admin"
    
    # Database
    DATABASE_URL: str = "sqlite:///news.db"
    
    # Security
    SECRET_KEY: str = ""
    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD_HASH: str = ""
    SESSION_EXPIRE_HOURS: int = 24
    
    # API Keys - as strings, will be parsed to lists
    WEBZ_API_KEYS: str = ""
    GEMINI_API_KEYS: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHANNEL: str = ""
    
    # Proxy
    SOCKS5_PROXY: str = ""
    
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
    
    # Property methods to get API keys as lists
    @property
    def webz_api_keys_list(self) -> List[str]:
        """Get WEBZ API keys as list"""
        if not self.WEBZ_API_KEYS or not self.WEBZ_API_KEYS.strip():
            return []
        return [k.strip() for k in self.WEBZ_API_KEYS.split(",") if k.strip()]
    
    @property
    def gemini_api_keys_list(self) -> List[str]:
        """Get Gemini API keys as list"""
        if not self.GEMINI_API_KEYS or not self.GEMINI_API_KEYS.strip():
            return []
        return [k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()]
    
    @field_validator("APP_PORT", mode='before')
    @classmethod
    def parse_port(cls, v):
        """Parse port from env"""
        if isinstance(v, str):
            return int(v)
        return v
    
    @field_validator("USE_HTTPS", mode='before')
    @classmethod
    def parse_use_https(cls, v):
        """Parse USE_HTTPS boolean"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes')
        return bool(v)
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate SECRET_KEY"""
        if not v or not v.strip():
            raise ValueError("SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    @field_validator("ADMIN_PASSWORD_HASH")
    @classmethod
    def validate_admin_hash(cls, v):
        """Validate ADMIN_PASSWORD_HASH"""
        if not v or not v.strip():
            raise ValueError("ADMIN_PASSWORD_HASH is required")
        return v
    
    @field_validator("SECRET_PATH")
    @classmethod
    def validate_secret_path(cls, v):
        """Validate SECRET_PATH"""
        if not v or not v.strip():
            raise ValueError("SECRET_PATH is required")
        # Remove leading/trailing slashes
        v = v.strip("/")
        if not v:
            raise ValueError("SECRET_PATH cannot be empty or just slashes")
        # Validate path format (alphanumeric, dash, underscore only)
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("SECRET_PATH must contain only alphanumeric characters, dashes, and underscores")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Singleton instance
settings = Settings()


def validate_environment():
    """Validate all required environment variables"""
    required_vars = {
        "SECRET_KEY": "Secret key for session encryption",
        "ADMIN_USERNAME": "Admin username",
        "ADMIN_PASSWORD_HASH": "Hashed admin password",
        "WEBZ_API_KEYS": "Webz.io API keys",
        "TELEGRAM_BOT_TOKEN": "Telegram bot token",
        "TELEGRAM_CHANNEL": "Telegram channel ID",
        "SECRET_PATH": "Secret path for admin panel"
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