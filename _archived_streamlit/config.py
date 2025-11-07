from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Backend API
    BACKEND_URL: str = "http://localhost:8001/api"

    # Vector Database
    VECTOR_DB_URL: str = "http://localhost:6333"

    # UI Settings
    PAGE_TITLE: str = "Content Management"
    PAGE_ICON: str = "📝"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
