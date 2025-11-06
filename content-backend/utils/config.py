from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    DEBUG: bool = True
    PORT: int = 8001
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Supabase
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_KEY: str = "your-supabase-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "your-supabase-service-role-key"

    # ChromaDB (embedded mode)
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # OpenAI
    OPENAI_API_KEY: str = "your-openai-api-key"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
