from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Segment
from utils.jwt_handler import get_current_user

router = APIRouter(prefix="/segments", tags=["Segments"])

# Pydantic schemas
class SegmentCreate(BaseModel):
    name: str
    filters: Optional[Dict[str, Any]] = None

class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class SegmentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    filters: Optional[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    segment: SegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new segment"""

    db_segment = Segment(
        user_id=current_user.id,
        name=segment.name,
        filters=segment.filters
    )

    db.add(db_segment)
    db.commit()
    db.refresh(db_segment)

    return db_segment

@router.get("/", response_model=List[SegmentResponse])
async def get_segments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all segments for the current user"""

    segments = db.query(Segment)\
        .filter(Segment.user_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()

    return segments

@router.get("/{segment_id}", response_model=SegmentResponse)
async def get_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific segment"""

    segment = db.query(Segment)\
        .filter(Segment.id == segment_id, Segment.user_id == current_user.id)\
        .first()

    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found"
        )

    return segment

@router.put("/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: int,
    segment_update: SegmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a segment"""

    segment = db.query(Segment)\
        .filter(Segment.id == segment_id, Segment.user_id == current_user.id)\
        .first()

    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found"
        )

    # Update fields
    if segment_update.name is not None:
        segment.name = segment_update.name
    if segment_update.filters is not None:
        segment.filters = segment_update.filters

    db.commit()
    db.refresh(segment)

    return segment

@router.delete("/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a segment"""

    segment = db.query(Segment)\
        .filter(Segment.id == segment_id, Segment.user_id == current_user.id)\
        .first()

    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found"
        )

    db.delete(segment)
    db.commit()

    return None
