from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings and environment variables"""

    # Application
    APP_NAME: str = "Content Management API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8001
    HOST: str = "0.0.0.0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/content_db"

    # Supabase (alternative to direct PostgreSQL)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ChromaDB (Vector Database)
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "https://artify-ruddy.vercel.app"
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
