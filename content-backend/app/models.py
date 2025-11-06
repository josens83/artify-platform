from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="user", cascade="all, delete-orphan")
    gen_jobs = relationship("GenJob", back_populates="user", cascade="all, delete-orphan")

class Campaign(Base):
    """Campaign model"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    objective = Column(String(100))
    channel = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="campaigns")
    creatives = relationship("Creative", back_populates="campaign", cascade="all, delete-orphan")

class Segment(Base):
    """Segment model"""
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    filters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="segments")
    creatives = relationship("Creative", back_populates="segment")

class Creative(Base):
    """Creative model"""
    __tablename__ = "creatives"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id", ondelete="SET NULL"))
    copy_text = Column(Text)
    image_url = Column(Text)
    meta = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="creatives")
    segment = relationship("Segment", back_populates="creatives")
    metrics = relationship("Metric", back_populates="creative", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="creative", cascade="all, delete-orphan")

class GenJob(Base):
    """Generation job model"""
    __tablename__ = "gen_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    model = Column(String(100))
    type = Column(String(50))  # 'text', 'image', etc.
    prompt = Column(Text)
    response = Column(Text)
    tokens = Column(Integer)
    cost = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="gen_jobs")

class Metric(Base):
    """Metrics model"""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    creative_id = Column(Integer, ForeignKey("creatives.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    engagement = Column(Integer, default=0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creative = relationship("Creative", back_populates="metrics")

class Feedback(Base):
    """Feedback model"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    creative_id = Column(Integer, ForeignKey("creatives.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(100))
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creative = relationship("Creative", back_populates="feedbacks")
