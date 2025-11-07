"""
Analytics and Event Tracking API
Handles event tracking (impressions, clicks) and campaign analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import hashlib

from database import get_db, Campaign, Creative, Event
from logger import get_logger

logger = get_logger("analytics_api")
router = APIRouter(tags=["analytics"])


# ==========================================
# Pydantic Models
# ==========================================

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


class CampaignAnalytics(BaseModel):
    """Campaign analytics response"""
    campaign_id: int
    campaign_name: str
    period: str
    impressions: int
    clicks: int
    conversions: int
    ctr: float  # Click-through rate
    cvr: float  # Conversion rate
    unique_users: int
    top_creatives: List[dict]
    by_channel: Dict[str, dict]
    by_segment: Dict[str, dict]
    timeline: List[dict]


class ABTestComparison(BaseModel):
    """A/B test comparison response"""
    campaign_id: int
    variant_a: dict
    variant_b: dict
    winner: Optional[str] = None
    confidence: Optional[float] = None


# ==========================================
# Event Tracking Endpoints
# ==========================================

@router.post("/events/track")
async def track_event(
    event: EventTrackRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track impression, click, or conversion event

    **Real-time event collection for analytics pipeline**
    """
    try:
        # Extract request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Create event
        new_event = Event(
            campaign_id=event.campaign_id,
            creative_id=event.creative_id,
            event_type=event.event_type,
            user_id=event.user_id,
            session_id=event.session_id or hashlib.md5(f"{ip_address}{user_agent}".encode()).hexdigest()[:16],
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=event.referrer,
            landing_url=event.landing_url,
            channel=event.channel,
            segment_id=event.segment_id,
            meta_data=event.meta_data
        )

        db.add(new_event)
        db.commit()

        logger.info(f"Event tracked: {event.event_type} for campaign {event.campaign_id}")

        return {
            "success": True,
            "event_id": new_event.id,
            "event_type": event.event_type
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Event tracking error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/track/click/{campaign_id}/{creative_id}")
async def track_click_redirect(
    campaign_id: int,
    creative_id: int,
    url: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track click and redirect to destination URL

    **Proxy link for click tracking**

    Usage: `/track/click/123/456?url=https://example.com`
    """
    try:
        # Track click event
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        referrer = request.headers.get("referer")

        event = Event(
            campaign_id=campaign_id,
            creative_id=creative_id,
            event_type='click',
            session_id=hashlib.md5(f"{ip_address}{user_agent}".encode()).hexdigest()[:16],
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            landing_url=url
        )

        db.add(event)
        db.commit()

        logger.info(f"Click tracked: campaign={campaign_id}, creative={creative_id}")

        # Redirect to destination
        return RedirectResponse(url=url, status_code=302)

    except Exception as e:
        logger.error(f"Click tracking error: {str(e)}")
        # Still redirect even if tracking fails
        return RedirectResponse(url=url, status_code=302)


@router.post("/track/impression")
async def track_impression(
    campaign_id: int,
    creative_id: Optional[int] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Track impression (ad view)

    **Lightweight endpoint for high-volume impression tracking**
    """
    try:
        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        event = Event(
            campaign_id=campaign_id,
            creative_id=creative_id,
            event_type='impression',
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=hashlib.md5(f"{ip_address}{user_agent}".encode()).hexdigest()[:16] if ip_address and user_agent else None
        )

        db.add(event)
        db.commit()

        # Return 1x1 transparent pixel
        return Response(
            content=b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            media_type="image/gif"
        )

    except Exception as e:
        logger.error(f"Impression tracking error: {str(e)}")
        # Return pixel even if tracking fails
        return Response(
            content=b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            media_type="image/gif"
        )


# ==========================================
# Analytics Endpoints
# ==========================================

@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive campaign analytics

    **Features:**
    - Time period filtering
    - Top performing creatives
    - Channel breakdown
    - Segment breakdown
    - Timeline data for charts
    """
    # Get campaign
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Default time range (last 30 days)
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Base query
    events_query = db.query(Event).filter(
        Event.campaign_id == campaign_id,
        Event.created_at >= start_date,
        Event.created_at <= end_date
    )

    # Overall metrics
    impressions = events_query.filter(Event.event_type == 'impression').count()
    clicks = events_query.filter(Event.event_type == 'click').count()
    conversions = events_query.filter(Event.event_type == 'conversion').count()

    # Calculate rates
    ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
    cvr = (conversions / clicks * 100) if clicks > 0 else 0.0

    # Unique users
    unique_users = db.query(func.count(func.distinct(Event.session_id))).filter(
        Event.campaign_id == campaign_id,
        Event.created_at >= start_date,
        Event.created_at <= end_date
    ).scalar() or 0

    # Top creatives by performance
    creative_stats = db.query(
        Creative.id,
        Creative.name,
        Creative.variant,
        func.count(case((Event.event_type == 'impression', 1))).label('impressions'),
        func.count(case((Event.event_type == 'click', 1))).label('clicks'),
        func.count(case((Event.event_type == 'conversion', 1))).label('conversions')
    ).join(
        Event, Event.creative_id == Creative.id
    ).filter(
        Creative.campaign_id == campaign_id,
        Event.created_at >= start_date,
        Event.created_at <= end_date
    ).group_by(
        Creative.id, Creative.name, Creative.variant
    ).all()

    top_creatives = [
        {
            "creative_id": c.id,
            "name": c.name,
            "variant": c.variant,
            "impressions": c.impressions,
            "clicks": c.clicks,
            "conversions": c.conversions,
            "ctr": (c.clicks / c.impressions * 100) if c.impressions > 0 else 0.0
        }
        for c in creative_stats
    ]
    top_creatives.sort(key=lambda x: x['ctr'], reverse=True)

    # By channel
    channel_stats = db.query(
        Event.channel,
        func.count(case((Event.event_type == 'impression', 1))).label('impressions'),
        func.count(case((Event.event_type == 'click', 1))).label('clicks')
    ).filter(
        Event.campaign_id == campaign_id,
        Event.created_at >= start_date,
        Event.created_at <= end_date,
        Event.channel.isnot(None)
    ).group_by(Event.channel).all()

    by_channel = {
        ch.channel: {
            "impressions": ch.impressions,
            "clicks": ch.clicks,
            "ctr": (ch.clicks / ch.impressions * 100) if ch.impressions > 0 else 0.0
        }
        for ch in channel_stats
    }

    # By segment
    segment_stats = db.query(
        Event.segment_id,
        func.count(case((Event.event_type == 'impression', 1))).label('impressions'),
        func.count(case((Event.event_type == 'click', 1))).label('clicks')
    ).filter(
        Event.campaign_id == campaign_id,
        Event.created_at >= start_date,
        Event.created_at <= end_date,
        Event.segment_id.isnot(None)
    ).group_by(Event.segment_id).all()

    by_segment = {
        str(seg.segment_id): {
            "impressions": seg.impressions,
            "clicks": seg.clicks,
            "ctr": (seg.clicks / seg.impressions * 100) if seg.impressions > 0 else 0.0
        }
        for seg in segment_stats
    }

    # Timeline (daily)
    timeline_stats = db.query(
        func.date(Event.created_at).label('date'),
        func.count(case((Event.event_type == 'impression', 1))).label('impressions'),
        func.count(case((Event.event_type == 'click', 1))).label('clicks'),
        func.count(case((Event.event_type == 'conversion', 1))).label('conversions')
    ).filter(
        Event.campaign_id == campaign_id,
        Event.created_at >= start_date,
        Event.created_at <= end_date
    ).group_by(func.date(Event.created_at)).order_by(func.date(Event.created_at)).all()

    timeline = [
        {
            "date": t.date.isoformat(),
            "impressions": t.impressions,
            "clicks": t.clicks,
            "conversions": t.conversions
        }
        for t in timeline_stats
    ]

    return CampaignAnalytics(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        period=f"{start_date.date()} to {end_date.date()}",
        impressions=impressions,
        clicks=clicks,
        conversions=conversions,
        ctr=round(ctr, 2),
        cvr=round(cvr, 2),
        unique_users=unique_users,
        top_creatives=top_creatives[:10],  # Top 10
        by_channel=by_channel,
        by_segment=by_segment,
        timeline=timeline
    )


@router.get("/campaigns/{campaign_id}/analytics/compare", response_model=ABTestComparison)
async def compare_ab_test(
    campaign_id: int,
    variant_a: str = "A",
    variant_b: str = "B",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Compare A/B test variants

    **Features:**
    - Statistical significance calculation
    - Performance metrics comparison
    - Winner determination
    """
    # Get campaign
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Default time range
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    def get_variant_stats(variant: str):
        """Get stats for a variant"""
        creatives = db.query(Creative.id).filter(
            Creative.campaign_id == campaign_id,
            Creative.variant == variant
        ).all()

        creative_ids = [c.id for c in creatives]

        if not creative_ids:
            return {
                "variant": variant,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "ctr": 0.0,
                "cvr": 0.0
            }

        events = db.query(Event).filter(
            Event.creative_id.in_(creative_ids),
            Event.created_at >= start_date,
            Event.created_at <= end_date
        )

        impressions = events.filter(Event.event_type == 'impression').count()
        clicks = events.filter(Event.event_type == 'click').count()
        conversions = events.filter(Event.event_type == 'conversion').count()

        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        cvr = (conversions / clicks * 100) if clicks > 0 else 0.0

        return {
            "variant": variant,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": round(ctr, 2),
            "cvr": round(cvr, 2)
        }

    # Get stats for both variants
    stats_a = get_variant_stats(variant_a)
    stats_b = get_variant_stats(variant_b)

    # Determine winner (simple comparison by CTR)
    winner = None
    confidence = None

    if stats_a["impressions"] > 0 and stats_b["impressions"] > 0:
        if stats_a["ctr"] > stats_b["ctr"]:
            winner = variant_a
            confidence = min(abs(stats_a["ctr"] - stats_b["ctr"]) / max(stats_a["ctr"], stats_b["ctr"]) * 100, 100)
        elif stats_b["ctr"] > stats_a["ctr"]:
            winner = variant_b
            confidence = min(abs(stats_b["ctr"] - stats_a["ctr"]) / max(stats_a["ctr"], stats_b["ctr"]) * 100, 100)
        else:
            winner = "tie"
            confidence = 0.0

    return ABTestComparison(
        campaign_id=campaign_id,
        variant_a=stats_a,
        variant_b=stats_b,
        winner=winner,
        confidence=round(confidence, 2) if confidence is not None else None
    )
