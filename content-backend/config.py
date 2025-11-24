"""
Configuration management for Artify Platform
Supports multiple environments: development, staging, production
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment-specific defaults"""

    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")

    # Redis Cache
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_TIMEOUT: int = Field(default=30, env="OPENAI_TIMEOUT")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    ENABLE_JSON_LOGS: bool = Field(default=False, env="ENABLE_JSON_LOGS")
    ENABLE_FILE_LOGS: bool = Field(default=True, env="ENABLE_FILE_LOGS")
    ENABLE_CONSOLE_LOGS: bool = Field(default=True, env="ENABLE_CONSOLE_LOGS")

    # Rate Limiting
    RATE_LIMIT_TEXT: str = Field(default="10/minute", env="RATE_LIMIT_TEXT")
    RATE_LIMIT_IMAGE: str = Field(default="5/minute", env="RATE_LIMIT_IMAGE")

    # User Quotas (defaults)
    DEFAULT_DAILY_TEXT_QUOTA: int = Field(default=100, env="DEFAULT_DAILY_TEXT_QUOTA")
    DEFAULT_DAILY_IMAGE_QUOTA: int = Field(default=20, env="DEFAULT_DAILY_IMAGE_QUOTA")
    DEFAULT_MONTHLY_COST_CAP: float = Field(default=50.0, env="DEFAULT_MONTHLY_COST_CAP")

    # Cache TTLs (seconds)
    TTL_TEMPLATES: int = Field(default=86400, env="TTL_TEMPLATES")  # 24 hours
    TTL_SEGMENTS: int = Field(default=3600, env="TTL_SEGMENTS")  # 1 hour
    TTL_BRAND_GUIDELINES: int = Field(default=3600, env="TTL_BRAND_GUIDELINES")  # 1 hour
    TTL_VECTOR_STATS: int = Field(default=300, env="TTL_VECTOR_STATS")  # 5 minutes

    # CORS
    CORS_ORIGINS: list = Field(
        default=[
            "https://artify-ruddy.vercel.app",
            "http://localhost:3001",
            "http://localhost:5173"
        ],
        env="CORS_ORIGINS"
    )

    # Backup
    BACKUP_DIR: str = Field(default="./backups", env="BACKUP_DIR")
    BACKUP_RETENTION_DAYS: int = Field(default=7, env="BACKUP_RETENTION_DAYS")

    # ChromaDB
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")

    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    ALLOWED_HOSTS: list = Field(default=["*"], env="ALLOWED_HOSTS")

    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """Development environment settings"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_CONSOLE_LOGS: bool = True
    ENABLE_FILE_LOGS: bool = False
    WORKERS: int = 1


class StagingSettings(Settings):
    """Staging environment settings"""
    ENVIRONMENT: str = "staging"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_JSON_LOGS: bool = True
    WORKERS: int = 2


class ProductionSettings(Settings):
    """Production environment settings"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    ENABLE_JSON_LOGS: bool = True
    ENABLE_CONSOLE_LOGS: bool = False
    WORKERS: int = 4

    # Production-specific security
    ALLOWED_HOSTS: list = Field(..., env="ALLOWED_HOSTS")

    # Higher connection pools
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    # Shorter TTLs for production
    TTL_VECTOR_STATS: int = 180  # 3 minutes


def get_settings() -> Settings:
    """
    Get settings based on ENVIRONMENT variable

    Returns:
        Settings instance for current environment
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    settings_map = {
        "development": DevelopmentSettings,
        "dev": DevelopmentSettings,
        "staging": StagingSettings,
        "stage": StagingSettings,
        "production": ProductionSettings,
        "prod": ProductionSettings,
    }

    settings_class = settings_map.get(env, DevelopmentSettings)

    return settings_class()


# Global settings instance
settings = get_settings()


if __name__ == "__main__":
    # Test settings
    print("Current Settings:")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug: {settings.DEBUG}")
    print(f"  Log Level: {settings.LOG_LEVEL}")
    print(f"  Workers: {settings.WORKERS}")
    print(f"  Database: {settings.DATABASE_URL[:30]}...")
    print(f"  Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"  Cache TTL (Segments): {settings.TTL_SEGMENTS}s")
