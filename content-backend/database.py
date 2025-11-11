"""
Database configuration and models for Content Backend
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, text
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
    segment_id = Column(Integer, nullable=True)  # Track which segment was used for generation
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
    meta_data = Column(JSON, nullable=True)  # Additional campaign settings
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
    meta_data = Column(JSON, nullable=True)  # Additional creative metadata
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
    meta_data = Column(JSON, nullable=True)  # Additional event data
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

    # Add missing columns to segments table if they don't exist
    # This is a safety measure for existing databases
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)

        # Check if segments table exists
        if 'segments' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('segments')]

            # First, handle problematic columns
            with engine.connect() as conn:
                # Remove NOT NULL constraint from 'filters' if it exists (legacy column)
                if 'filters' in existing_columns:
                    try:
                        conn.execute(text('ALTER TABLE segments ALTER COLUMN filters DROP NOT NULL'))
                        conn.commit()
                        print("✓ Removed NOT NULL constraint from 'filters' column")
                    except Exception as e:
                        print(f"⚠️  Could not modify 'filters' column: {str(e)}")
                        conn.rollback()

                # Define required columns
                required_columns = {
                    'criteria': 'TEXT',
                    'description': 'TEXT',
                    'created_at': 'TIMESTAMP',
                    'updated_at': 'TIMESTAMP',
                    'tone': 'VARCHAR(100)',
                    'keywords': 'TEXT',
                    'reference_urls': 'TEXT',
                    'prompt_template': 'TEXT'
                }

                # Add missing columns
                for col_name, col_type in required_columns.items():
                    if col_name not in existing_columns:
                        try:
                            conn.execute(text(f'ALTER TABLE segments ADD COLUMN {col_name} {col_type}'))
                            conn.commit()
                            print(f"✓ Added column '{col_name}' to segments table")
                        except Exception as e:
                            print(f"⚠️  Could not add column '{col_name}': {str(e)}")
                            conn.rollback()

        # Check if gen_jobs table exists and add missing columns
        if 'gen_jobs' in inspector.get_table_names():
            gen_jobs_columns = [col['name'] for col in inspector.get_columns('gen_jobs')]
            gen_jobs_columns_info = {col['name']: col for col in inspector.get_columns('gen_jobs')}

            # Define all required columns for gen_jobs
            gen_jobs_required_columns = {
                'user_id': 'INTEGER',
                'job_type': 'VARCHAR(50)',
                'model': 'VARCHAR(100)',
                'prompt': 'TEXT',
                'prompt_tokens': 'INTEGER',
                'completion_tokens': 'INTEGER',
                'total_tokens': 'INTEGER',
                'estimated_cost': 'FLOAT DEFAULT 0.0',
                'status': "VARCHAR(50) DEFAULT 'completed'",
                'error_message': 'TEXT',
                'segment_id': 'INTEGER',
                'created_at': 'TIMESTAMP',
                'completed_at': 'TIMESTAMP'
            }

            with engine.connect() as conn:
                # First, fix prompt column if it's JSON type (should be TEXT)
                if 'prompt' in gen_jobs_columns:
                    prompt_col_info = gen_jobs_columns_info.get('prompt')
                    if prompt_col_info and str(prompt_col_info['type']).upper() in ['JSON', 'JSONB']:
                        try:
                            # Change column type from JSON to TEXT
                            conn.execute(text('ALTER TABLE gen_jobs ALTER COLUMN prompt TYPE TEXT USING prompt::text'))
                            conn.commit()
                            print("✓ Changed 'prompt' column type from JSON to TEXT in gen_jobs table")
                        except Exception as e:
                            print(f"⚠️  Could not change 'prompt' column type: {str(e)}")
                            conn.rollback()

                # Add missing columns to gen_jobs
                for col_name, col_type in gen_jobs_required_columns.items():
                    if col_name not in gen_jobs_columns:
                        try:
                            conn.execute(text(f'ALTER TABLE gen_jobs ADD COLUMN {col_name} {col_type}'))
                            conn.commit()
                            print(f"✓ Added column '{col_name}' to gen_jobs table")
                        except Exception as e:
                            print(f"⚠️  Could not add column '{col_name}' to gen_jobs: {str(e)}")
                            conn.rollback()
    except Exception as e:
        print(f"⚠️  Error checking/adding table columns: {str(e)}")
