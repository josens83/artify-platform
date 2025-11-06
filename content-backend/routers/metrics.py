from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
from app.database import get_db
from app.models import User, Metric, Creative
from utils.jwt_handler import get_current_user

router = APIRouter()

# Pydantic schemas
class MetricCreate(BaseModel):
    creative_id: int
    date: date
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    engagement: int = 0

class MetricUpdate(BaseModel):
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: Optional[float] = None
    engagement: Optional[int] = None

class MetricResponse(BaseModel):
    id: int
    creative_id: int
    date: date
    impressions: int
    clicks: int
    ctr: float
    engagement: int
    recorded_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=MetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
    metric: MetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record metrics for a creative"""

    # Verify creative belongs to user
    creative = db.query(Creative).join(Creative.campaign).filter(
        Creative.id == metric.creative_id,
        Creative.campaign.has(user_id=current_user.id)
    ).first()

    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found or access denied"
        )

    # Auto-calculate CTR if not provided
    if metric.clicks > 0 and metric.impressions > 0:
        metric.ctr = (metric.clicks / metric.impressions) * 100

    db_metric = Metric(**metric.dict())

    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)

    return db_metric

@router.get("/creative/{creative_id}", response_model=List[MetricResponse])
async def get_metrics_for_creative(
    creative_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all metrics for a specific creative"""

    # Verify creative belongs to user
    creative = db.query(Creative).join(Creative.campaign).filter(
        Creative.id == creative_id,
        Creative.campaign.has(user_id=current_user.id)
    ).first()

    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found or access denied"
        )

    query = db.query(Metric).filter(Metric.creative_id == creative_id)

    if start_date:
        query = query.filter(Metric.date >= start_date)
    if end_date:
        query = query.filter(Metric.date <= end_date)

    metrics = query.order_by(Metric.date.desc()).all()

    return metrics

@router.get("/campaign/{campaign_id}/summary")
async def get_campaign_metrics_summary(
    campaign_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated metrics for a campaign"""

    from sqlalchemy import func

    # Get all creatives for the campaign
    creatives = db.query(Creative.id).filter(
        Creative.campaign_id == campaign_id,
        Creative.campaign.has(user_id=current_user.id)
    ).all()

    if not creatives:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found or no creatives"
        )

    creative_ids = [c.id for c in creatives]

    # Build query
    query = db.query(
        func.sum(Metric.impressions).label("total_impressions"),
        func.sum(Metric.clicks).label("total_clicks"),
        func.avg(Metric.ctr).label("avg_ctr"),
        func.sum(Metric.engagement).label("total_engagement")
    ).filter(Metric.creative_id.in_(creative_ids))

    if start_date:
        query = query.filter(Metric.date >= start_date)
    if end_date:
        query = query.filter(Metric.date <= end_date)

    summary = query.first()

    return {
        "campaign_id": campaign_id,
        "total_impressions": summary.total_impressions or 0,
        "total_clicks": summary.total_clicks or 0,
        "average_ctr": float(summary.avg_ctr or 0),
        "total_engagement": summary.total_engagement or 0,
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        }
    }

@router.get("/dashboard")
async def get_dashboard_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard metrics for the user"""

    from sqlalchemy import func
    from datetime import timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get all creatives for user's campaigns
    creatives_query = db.query(Creative.id).join(Creative.campaign).filter(
        Creative.campaign.has(user_id=current_user.id)
    )

    creative_ids = [c.id for c in creatives_query.all()]

    if not creative_ids:
        return {
            "period_days": days,
            "total_creatives": 0,
            "total_impressions": 0,
            "total_clicks": 0,
            "average_ctr": 0,
            "total_engagement": 0
        }

    # Aggregate metrics
    summary = db.query(
        func.sum(Metric.impressions).label("total_impressions"),
        func.sum(Metric.clicks).label("total_clicks"),
        func.avg(Metric.ctr).label("avg_ctr"),
        func.sum(Metric.engagement).label("total_engagement")
    ).filter(
        Metric.creative_id.in_(creative_ids),
        Metric.date >= start_date,
        Metric.date <= end_date
    ).first()

    return {
        "period_days": days,
        "total_creatives": len(creative_ids),
        "total_impressions": summary.total_impressions or 0,
        "total_clicks": summary.total_clicks or 0,
        "average_ctr": float(summary.avg_ctr or 0),
        "total_engagement": summary.total_engagement or 0
    }

@router.put("/{metric_id}", response_model=MetricResponse)
async def update_metric(
    metric_id: int,
    metric_update: MetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a metric record"""

    metric = db.query(Metric).join(Metric.creative).join(Creative.campaign).filter(
        Metric.id == metric_id,
        Creative.campaign.has(user_id=current_user.id)
    ).first()

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found or access denied"
        )

    # Update fields
    for field, value in metric_update.dict(exclude_unset=True).items():
        setattr(metric, field, value)

    # Recalculate CTR if impressions or clicks changed
    if metric.impressions > 0:
        metric.ctr = (metric.clicks / metric.impressions) * 100

    db.commit()
    db.refresh(metric)

    return metric

@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a metric record"""

    metric = db.query(Metric).join(Metric.creative).join(Creative.campaign).filter(
        Metric.id == metric_id,
        Creative.campaign.has(user_id=current_user.id)
    ).first()

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found or access denied"
        )

    db.delete(metric)
    db.commit()

    return None
