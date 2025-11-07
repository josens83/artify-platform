"""
Campaign Management API
Handles campaign CRUD, creative management, and event tracking
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import base64

from database import get_db, Campaign, Creative, Event
from storage_client import get_storage_client
from logger import get_logger

logger = get_logger("campaigns_api")
router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ==========================================
# Pydantic Models
# ==========================================

class CampaignCreate(BaseModel):
    """Campaign creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    channel: str = Field(..., description="Channel type: social, email, display, video")
    size: Optional[str] = Field(None, description="Content size, e.g., 1080x1080")
    segment_id: Optional[int] = None
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    meta_data: Optional[dict] = None


class CampaignUpdate(BaseModel):
    """Campaign update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    segment_id: Optional[int] = None
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    meta_data: Optional[dict] = None


class CampaignResponse(BaseModel):
    """Campaign response"""
    id: int
    user_id: Optional[int]
    name: str
    description: Optional[str]
    channel: str
    size: Optional[str]
    segment_id: Optional[int]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    budget: Optional[float]
    meta_data: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreativeCreate(BaseModel):
    """Creative creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="Type: text, image, video")
    content_text: Optional[str] = None
    image_base64: Optional[str] = Field(None, description="Base64 encoded image (will be uploaded to storage)")
    asset_url: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    variant: Optional[str] = None
    meta_data: Optional[dict] = None


class CreativeResponse(BaseModel):
    """Creative response"""
    id: int
    campaign_id: int
    name: str
    content_type: str
    content_text: Optional[str]
    asset_url: Optional[str]
    thumbnail_url: Optional[str]
    prompt: Optional[str]
    model: Optional[str]
    size: Optional[str]
    variant: Optional[str]
    status: str
    performance_score: Optional[float]
    meta_data: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventTrackRequest(BaseModel):
    """Event tracking request"""
    campaign_id: int
    creative_id: Optional[int] = None
    event_type: str = Field(..., description="Type: impression, click, conversion")
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    referrer: Optional[str] = None
    landing_url: Optional[str] = None
    channel: Optional[str] = None
    segment_id: Optional[int] = None
    meta_data: Optional[dict] = None


# ==========================================
# Campaign CRUD Endpoints
# ==========================================

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """
    Create a new campaign

    **Workflow:**
    1. Create campaign with minimal metadata (channel, size)
    2. Returns campaign_id
    3. Frontend redirects to editor with campaign_id
    """
    try:
        new_campaign = Campaign(
            user_id=user_id,
            name=campaign.name,
            description=campaign.description,
            channel=campaign.channel,
            size=campaign.size,
            segment_id=campaign.segment_id,
            budget=campaign.budget,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            meta_data=campaign.meta_data,
            status='draft'
        )

        db.add(new_campaign)
        db.commit()
        db.refresh(new_campaign)

        logger.info(f"Campaign created: {new_campaign.id} - {new_campaign.name}")

        return new_campaign

    except Exception as e:
        db.rollback()
        logger.error(f"Campaign creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    user_id: int = 1,  # TODO: Get from authentication
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get campaigns for user with optional filters"""
    query = db.query(Campaign).filter(Campaign.user_id == user_id)

    if status:
        query = query.filter(Campaign.status == status)
    if channel:
        query = query.filter(Campaign.channel == channel)

    campaigns = query.order_by(Campaign.created_at.desc()).limit(limit).offset(offset).all()

    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Get campaign by ID"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    updates: CampaignUpdate,
    db: Session = Depends(get_db)
):
    """Update campaign"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    campaign.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(campaign)

    logger.info(f"Campaign updated: {campaign_id}")

    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Delete campaign and all associated creatives and events"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()

    logger.info(f"Campaign deleted: {campaign_id}")

    return {"success": True, "message": f"Campaign {campaign_id} deleted"}


# ==========================================
# Creative Management Endpoints
# ==========================================

@router.post("/{campaign_id}/creatives", response_model=CreativeResponse)
async def create_creative(
    campaign_id: int,
    creative: CreativeCreate,
    db: Session = Depends(get_db)
):
    """
    Create creative for campaign

    **Features:**
    - Handles image upload (Base64 → Supabase Storage)
    - Generates thumbnail automatically
    - Returns storage URLs (not Base64)
    """
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    try:
        asset_url = creative.asset_url
        thumbnail_url = None

        # Handle image upload if Base64 provided
        if creative.image_base64 and creative.content_type == "image":
            try:
                # Decode Base64
                image_data = base64.b64decode(creative.image_base64)

                # Upload with thumbnail
                storage = get_storage_client()
                success, main_url, thumb_url, error = storage.upload_with_thumbnail(
                    image_data,
                    f"{creative.name}.jpg",
                    folder=f"campaigns/{campaign_id}"
                )

                if success:
                    asset_url = main_url
                    thumbnail_url = thumb_url
                    logger.info(f"Image uploaded for creative: {creative.name}")
                else:
                    logger.error(f"Image upload failed: {error}")
                    raise HTTPException(status_code=500, detail=f"Image upload failed: {error}")

            except Exception as e:
                logger.error(f"Base64 decode/upload error: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid image data")

        # Create creative
        new_creative = Creative(
            campaign_id=campaign_id,
            name=creative.name,
            content_type=creative.content_type,
            content_text=creative.content_text,
            asset_url=asset_url,
            thumbnail_url=thumbnail_url,
            prompt=creative.prompt,
            model=creative.model,
            size=creative.size or campaign.size,
            variant=creative.variant,
            meta_data=creative.meta_data,
            status='draft'
        )

        db.add(new_creative)
        db.commit()
        db.refresh(new_creative)

        logger.info(f"Creative created: {new_creative.id} for campaign {campaign_id}")

        return new_creative

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Creative creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/creatives", response_model=List[CreativeResponse])
async def get_campaign_creatives(
    campaign_id: int,
    status: Optional[str] = None,
    variant: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all creatives for a campaign"""
    query = db.query(Creative).filter(Creative.campaign_id == campaign_id)

    if status:
        query = query.filter(Creative.status == status)
    if variant:
        query = query.filter(Creative.variant == variant)

    creatives = query.order_by(Creative.created_at.desc()).all()

    return creatives


@router.delete("/{campaign_id}/creatives/{creative_id}")
async def delete_creative(
    campaign_id: int,
    creative_id: int,
    db: Session = Depends(get_db)
):
    """Delete creative and associated assets"""
    creative = db.query(Creative).filter(
        Creative.id == creative_id,
        Creative.campaign_id == campaign_id
    ).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # Delete from storage if URL exists
    if creative.asset_url:
        storage = get_storage_client()
        storage.delete_file(creative.asset_url)
        if creative.thumbnail_url:
            storage.delete_file(creative.thumbnail_url)

    db.delete(creative)
    db.commit()

    logger.info(f"Creative deleted: {creative_id}")

    return {"success": True, "message": f"Creative {creative_id} deleted"}
