"""
Database configuration and models for Content Backend
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine with slow query logging
# echo=True logs all SQL (use only in development)
# echo_pool=True logs connection pool events
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,  # Verify connections before using
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10"))
)

# Slow query monitoring
from sqlalchemy import event
from logger import get_logger
import time

logger = get_logger("database")

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop()

    # Log slow queries (> 1 second)
    if total_time > 1.0:
        logger.warning(
            f"Slow query detected ({total_time:.2f}s): {statement[:200]}"
        )

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
    # Prompt template fields for auto-injection
    tone = Column(String(100), nullable=True)  # 'professional', 'casual', 'friendly', etc.
    keywords = Column(Text, nullable=True)  # Comma-separated keywords
    reference_urls = Column(Text, nullable=True)  # JSON array of reference URLs
    prompt_template = Column(Text, nullable=True)  # Custom prompt template with {variables}
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


class Campaign(Base):
    """Marketing campaigns with channel and target metadata"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    channel = Column(String(50), nullable=False)  # 'social', 'email', 'display', 'video'
    size = Column(String(50), nullable=True)  # '1080x1080', '1920x1080', etc.
    segment_id = Column(Integer, ForeignKey('segments.id'), nullable=True)
    status = Column(String(50), default='draft')  # 'draft', 'active', 'paused', 'completed'
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)  # Campaign budget
    metadata = Column(JSON, nullable=True)  # Additional campaign settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creatives = relationship("Creative", back_populates="campaign", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="campaign", cascade="all, delete-orphan")


class Creative(Base):
    """Creative assets associated with campaigns"""
    __tablename__ = "creatives"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # 'text', 'image', 'video'
    content_text = Column(Text, nullable=True)  # Generated text content
    asset_url = Column(Text, nullable=True)  # S3/Supabase URL for images/videos
    thumbnail_url = Column(Text, nullable=True)  # Thumbnail URL
    prompt = Column(Text, nullable=True)  # Original prompt
    model = Column(String(100), nullable=True)  # Model used
    size = Column(String(50), nullable=True)  # Image/video dimensions
    variant = Column(String(50), nullable=True)  # A/B test variant (e.g., 'A', 'B')
    status = Column(String(50), default='draft')  # 'draft', 'approved', 'rejected'
    performance_score = Column(Float, nullable=True)  # Calculated performance metric
    metadata = Column(JSON, nullable=True)  # Additional creative metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="creatives")
    events = relationship("Event", back_populates="creative", cascade="all, delete-orphan")


class Event(Base):
    """Event tracking for impressions, clicks, and conversions"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    creative_id = Column(Integer, ForeignKey('creatives.id'), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # 'impression', 'click', 'conversion'
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    landing_url = Column(Text, nullable=True)
    channel = Column(String(50), nullable=True)  # Track channel at event level
    segment_id = Column(Integer, nullable=True, index=True)  # User segment
    metadata = Column(JSON, nullable=True)  # Additional event data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="events")
    creative = relationship("Creative", back_populates="events")


class PromptTemplate(Base):
    """Reusable prompt templates for content generation"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template = Column(Text, nullable=False)  # Template with {variables}
    category = Column(String(50), nullable=True)  # 'social', 'email', 'display', etc.
    language = Column(String(10), default='en')  # 'en', 'ko', etc.
    variables = Column(JSON, nullable=True)  # List of required variables
    is_public = Column(Boolean, default=True)
    user_id = Column(Integer, nullable=True, index=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreativeTemplate(Base):
    """Layout/font/palette templates for creatives"""
    __tablename__ = "creative_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    preview_url = Column(Text, nullable=True)  # Template preview image
    category = Column(String(50), nullable=True)  # 'minimal', 'bold', 'elegant', etc.
    # Layout configuration
    layout_config = Column(JSON, nullable=False)  # {text_slots: [], image_slots: [], dimensions: {}}
    # Style configuration
    font_family = Column(String(100), nullable=True)  # 'Roboto', 'Arial', etc.
    font_sizes = Column(JSON, nullable=True)  # {heading: 48, body: 16, etc.}
    color_palette = Column(JSON, nullable=False)  # {primary: '#000', secondary: '#fff', etc.}
    # Metadata
    channel = Column(String(50), nullable=True)  # Target channel
    size = Column(String(50), nullable=True)  # '1080x1080', '1920x1080', etc.
    is_public = Column(Boolean, default=True)
    user_id = Column(Integer, nullable=True, index=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BatchGenerationJob(Base):
    """Batch generation jobs for segments"""
    __tablename__ = "batch_generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey('segments.id'), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    # Job configuration
    content_type = Column(String(50), nullable=False)  # 'text', 'image', 'both'
    count = Column(Integer, nullable=False)  # Number of creatives to generate
    prompt_template_id = Column(Integer, ForeignKey('prompt_templates.id'), nullable=True)
    creative_template_id = Column(Integer, ForeignKey('creative_templates.id'), nullable=True)
    parameters = Column(JSON, nullable=True)  # Additional generation parameters
    # Job status
    status = Column(String(50), default='pending', index=True)  # 'pending', 'processing', 'completed', 'failed'
    progress = Column(Integer, default=0)  # 0-100 percentage
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    # Results
    creative_ids = Column(JSON, nullable=True)  # List of generated creative IDs
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    campaign = relationship("Campaign")


class ChannelPreset(Base):
    """Channel-specific presets for size, format, and best practices"""
    __tablename__ = "channel_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False, index=True)  # 'instagram', 'facebook', 'twitter', etc.
    type = Column(String(50), nullable=False)  # 'feed', 'story', 'reel', 'post', etc.
    # Size configuration
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    aspect_ratio = Column(String(20), nullable=False)  # '1:1', '16:9', '9:16', etc.
    # Recommendations
    recommended_text_length = Column(Integer, nullable=True)  # Max characters
    recommended_hashtags = Column(Integer, nullable=True)  # Number of hashtags
    best_practices = Column(JSON, nullable=True)  # List of tips
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
