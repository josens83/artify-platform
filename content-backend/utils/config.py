from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    DEBUG: bool = True
    PORT: int = 8001
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/content_db"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # Vector Database
    VECTOR_DB_URL: str = "http://localhost:6333"
    VECTOR_COLLECTION_NAME: str = "content_embeddings"

    # AI Service
    AI_SERVICE_URL: str = "http://localhost:8000"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
