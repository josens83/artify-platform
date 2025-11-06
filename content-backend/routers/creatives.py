from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from models.database import get_db
from utils.vector import get_vector_db, VectorDB

router = APIRouter()

# Pydantic models
class CreativeCreate(BaseModel):
    campaign_id: int
    segment_id: Optional[int] = None
    copy_text: Optional[str] = None
    image_url: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class CreativeUpdate(BaseModel):
    campaign_id: Optional[int] = None
    segment_id: Optional[int] = None
    copy_text: Optional[str] = None
    image_url: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class Creative(BaseModel):
    id: int
    campaign_id: int
    segment_id: Optional[int]
    copy_text: Optional[str]
    image_url: Optional[str]
    meta: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

@router.post("/", response_model=dict)
async def create_creative(
    creative: CreativeCreate,
    db: Client = Depends(get_db)
):
    """Create a new creative and add to vector DB"""
    try:
        data = creative.dict()

        # Insert into Supabase
        result = db.table("creatives").insert(data).execute()
        creative_data = result.data[0]

        # Add to vector DB if copy_text exists
        if creative.copy_text:
            vector_db = get_vector_db()
            vector_db.add_creative(
                creative_id=creative_data["id"],
                text=creative.copy_text,
                metadata={
                    "campaign_id": creative.campaign_id,
                    "segment_id": creative.segment_id
                },
                collection_name=VectorDB.COLLECTION_COPY_TEXTS
            )

        return {"success": True, "data": creative_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=dict)
async def get_creatives(
    campaign_id: Optional[int] = None,
    db: Client = Depends(get_db)
):
    """Get all creatives, optionally filtered by campaign"""
    try:
        query = db.table("creatives").select("*")

        if campaign_id:
            query = query.eq("campaign_id", campaign_id)

        result = query.order("created_at", desc=True).execute()

        return {"success": True, "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{creative_id}", response_model=dict)
async def get_creative(creative_id: int, db: Client = Depends(get_db)):
    """Get a specific creative"""
    try:
        result = db.table("creatives")\
            .select("*")\
            .eq("id", creative_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Creative not found")

        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{creative_id}", response_model=dict)
async def update_creative(
    creative_id: int,
    creative: CreativeUpdate,
    db: Client = Depends(get_db)
):
    """Update a creative"""
    try:
        data = creative.dict(exclude_unset=True)

        result = db.table("creatives")\
            .update(data)\
            .eq("id", creative_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Creative not found")

        # Update vector DB if copy_text was updated
        if "copy_text" in data and data["copy_text"]:
            vector_db = get_vector_db()
            creative_data = result.data[0]
            vector_db.add_creative(
                creative_id=creative_id,
                text=data["copy_text"],
                metadata={
                    "campaign_id": creative_data.get("campaign_id"),
                    "segment_id": creative_data.get("segment_id")
                },
                collection_name=VectorDB.COLLECTION_COPY_TEXTS
            )

        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{creative_id}", response_model=dict)
async def delete_creative(creative_id: int, db: Client = Depends(get_db)):
    """Delete a creative"""
    try:
        # Delete from vector DB first
        vector_db = get_vector_db()
        vector_db.delete_creative(creative_id, VectorDB.COLLECTION_COPY_TEXTS)

        # Delete from Supabase
        result = db.table("creatives")\
            .delete()\
            .eq("id", creative_id)\
            .execute()

        return {"success": True, "message": "Creative deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{creative_id}/similar", response_model=dict)
async def find_similar_creatives(
    creative_id: int,
    top_k: int = 5,
    db: Client = Depends(get_db)
):
    """Find similar creatives using vector search"""
    try:
        # Get the creative's copy text
        result = db.table("creatives")\
            .select("copy_text")\
            .eq("id", creative_id)\
            .execute()

        if not result.data or not result.data[0].get("copy_text"):
            raise HTTPException(status_code=404, detail="Creative not found or has no copy text")

        copy_text = result.data[0]["copy_text"]

        # Search for similar in vector DB
        vector_db = get_vector_db()
        similar = vector_db.search_similar(
            query=copy_text,
            collection_name=VectorDB.COLLECTION_COPY_TEXTS,
            top_k=top_k + 1  # +1 to exclude self
        )

        # Filter out the query creative itself
        similar = [s for s in similar if int(s["id"]) != creative_id][:top_k]

        return {"success": True, "data": similar}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
