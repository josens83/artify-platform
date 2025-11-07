"""
Database configuration and models for Content Backend
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database Models
class Segment(Base):
    """Segment model for content targeting"""
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    criteria = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedContent(Base):
    """Generated AI content history"""
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(50), nullable=False)  # 'text' or 'image'
    prompt = Column(Text, nullable=False)
    result = Column(Text, nullable=False)  # Generated content or image URL
    model = Column(String(100), nullable=True)
    cache_key = Column(String(255), nullable=True, index=True)  # Cache identifier for prompt cache
    is_cached_result = Column(Boolean, default=False)  # True if this was returned from cache
    created_at = Column(DateTime, default=datetime.utcnow)


class Metric(Base):
    """Analytics metrics"""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class GenerationJob(Base):
    """AI Generation jobs tracking for cost monitoring"""
    __tablename__ = "gen_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    job_type = Column(String(50), nullable=False)  # 'text' or 'image'
    model = Column(String(100), nullable=False)  # e.g., 'gpt-3.5-turbo', 'dall-e-3'
    prompt = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, default=0.0)  # in USD
    status = Column(String(50), default='completed')  # 'pending', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class UserQuota(Base):
    """User quota tracking for cost and usage limits"""
    __tablename__ = "user_quotas"

    user_id = Column(Integer, primary_key=True, index=True)
    daily_text_quota = Column(Integer, default=100)
    daily_image_quota = Column(Integer, default=20)
    monthly_cost_cap = Column(Float, default=50.0)  # USD
    daily_text_used = Column(Integer, default=0)
    daily_image_used = Column(Integer, default=0)
    monthly_cost_used = Column(Float, default=0.0)
    last_daily_reset = Column(DateTime, default=datetime.utcnow)
    last_monthly_reset = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
