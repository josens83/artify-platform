from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from models.database import get_db

router = APIRouter()

# Pydantic models
class SegmentCreate(BaseModel):
    name: str
    filters: Optional[Dict[str, Any]] = None

class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class Segment(BaseModel):
    id: int
    user_id: int
    name: str
    filters: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

@router.post("/", response_model=dict)
async def create_segment(segment: SegmentCreate, db: Client = Depends(get_db)):
    """Create a new segment"""
    try:
        # TODO: Get user_id from auth token
        user_id = 1  # Placeholder

        data = {
            "user_id": user_id,
            "name": segment.name,
            "filters": segment.filters
        }

        result = db.table("segments").insert(data).execute()

        return {"success": True, "data": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=dict)
async def get_segments(db: Client = Depends(get_db)):
    """Get all segments for the current user"""
    try:
        # TODO: Get user_id from auth token
        user_id = 1  # Placeholder

        result = db.table("segments")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()

        return {"success": True, "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{segment_id}", response_model=dict)
async def get_segment(segment_id: int, db: Client = Depends(get_db)):
    """Get a specific segment"""
    try:
        result = db.table("segments")\
            .select("*")\
            .eq("id", segment_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Segment not found")

        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{segment_id}", response_model=dict)
async def update_segment(
    segment_id: int,
    segment: SegmentUpdate,
    db: Client = Depends(get_db)
):
    """Update a segment"""
    try:
        data = segment.dict(exclude_unset=True)

        result = db.table("segments")\
            .update(data)\
            .eq("id", segment_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Segment not found")

        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{segment_id}", response_model=dict)
async def delete_segment(segment_id: int, db: Client = Depends(get_db)):
    """Delete a segment"""
    try:
        result = db.table("segments")\
            .delete()\
            .eq("id", segment_id)\
            .execute()

        return {"success": True, "message": "Segment deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
