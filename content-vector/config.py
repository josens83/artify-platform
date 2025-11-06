from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # OpenAI Configuration
    OPENAI_API_KEY: str = "your-openai-api-key-here"

    # Embedding Model
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Collection Names (정의된 컬렉션)
    COLLECTION_COPY_TEXTS: str = "copy_texts"
    COLLECTION_IMAGES: str = "images"
    COLLECTION_TEMPLATES: str = "templates"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
