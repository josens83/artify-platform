from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Qdrant Configuration
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_TIMEOUT: int = 30

    # Collection Settings
    COLLECTION_NAME: str = "content_embeddings"
    VECTOR_SIZE: int = 1536  # OpenAI embedding size

    # Embedding Model
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
