from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from models.database import get_db

router = APIRouter()

# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    objective: Optional[str] = None
    channel: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    objective: Optional[str] = None
    channel: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class Campaign(BaseModel):
    id: int
    user_id: int
    name: str
    objective: Optional[str]
    channel: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: str
    updated_at: str

@router.post("/", response_model=dict)
async def create_campaign(campaign: CampaignCreate, db: Client = Depends(get_db)):
    """Create a new campaign"""
    try:
        # TODO: Get user_id from auth token
        user_id = 1  # Placeholder

        data = {
            "user_id": user_id,
            "name": campaign.name,
            "objective": campaign.objective,
            "channel": campaign.channel,
            "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
            "end_date": campaign.end_date.isoformat() if campaign.end_date else None
        }

        result = db.table("campaigns").insert(data).execute()

        return {"success": True, "data": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=dict)
async def get_campaigns(db: Client = Depends(get_db)):
    """Get all campaigns for the current user"""
    try:
        # TODO: Get user_id from auth token
        user_id = 1  # Placeholder

        result = db.table("campaigns")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()

        return {"success": True, "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_id}", response_model=dict)
async def get_campaign(campaign_id: int, db: Client = Depends(get_db)):
    """Get a specific campaign"""
    try:
        result = db.table("campaigns")\
            .select("*")\
            .eq("id", campaign_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{campaign_id}", response_model=dict)
async def update_campaign(
    campaign_id: int,
    campaign: CampaignUpdate,
    db: Client = Depends(get_db)
):
    """Update a campaign"""
    try:
        data = campaign.dict(exclude_unset=True)

        # Convert dates to ISO format
        if "start_date" in data and data["start_date"]:
            data["start_date"] = data["start_date"].isoformat()
        if "end_date" in data and data["end_date"]:
            data["end_date"] = data["end_date"].isoformat()

        result = db.table("campaigns")\
            .update(data)\
            .eq("id", campaign_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{campaign_id}", response_model=dict)
async def delete_campaign(campaign_id: int, db: Client = Depends(get_db)):
    """Delete a campaign"""
    try:
        result = db.table("campaigns")\
            .delete()\
            .eq("id", campaign_id)\
            .execute()

        return {"success": True, "message": "Campaign deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
