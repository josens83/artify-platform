from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24 hours

    # API Keys
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Rate Limiting
    rate_limit_per_minute: int = 20

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
