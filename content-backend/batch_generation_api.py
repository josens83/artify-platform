"""
Batch Generation API
Handles batch generation jobs for segments with queue system
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import json

from database import (
    get_db,
    BatchGenerationJob,
    Campaign,
    Creative,
    Segment,
    PromptTemplate,
    CreativeTemplate
)
from openai_client import generate_text, generate_image
from storage_client import get_storage_client
from logger import get_logger

logger = get_logger("batch_generation_api")
router = APIRouter(prefix="/batch", tags=["batch-generation"])


# ==========================================
# Pydantic Models
# ==========================================

class BatchGenerationCreate(BaseModel):
    """Create batch generation job"""
    campaign_id: int
    segment_id: Optional[int] = None
    content_type: str = Field(..., pattern="^(text|image|both)$")
    count: int = Field(..., ge=1, le=50, description="Number of creatives to generate")
    prompt_template_id: Optional[int] = None
    creative_template_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None


class BatchGenerationResponse(BaseModel):
    """Batch generation job response"""
    id: int
    campaign_id: int
    segment_id: Optional[int]
    content_type: str
    count: int
    status: str
    progress: int
    total_items: int
    completed_items: int
    failed_items: int
    error_message: Optional[str]
    creative_ids: Optional[List[int]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class BatchGenerationStatus(BaseModel):
    """Batch generation status"""
    job_id: int
    status: str
    progress: int
    completed_items: int
    total_items: int
    estimated_time_remaining: Optional[int] = None  # seconds


# ==========================================
# Background Task: Process Batch Job
# ==========================================

async def process_batch_job(job_id: int, db_session_factory):
    """
    Background task to process batch generation job

    Args:
        job_id: Job ID
        db_session_factory: Database session factory (SessionLocal)
    """
    db = db_session_factory()
    storage = get_storage_client()

    try:
        # Get job
        job = db.query(BatchGenerationJob).filter(BatchGenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update job status
        job.status = 'processing'
        job.started_at = datetime.utcnow()
        job.total_items = job.count
        db.commit()

        logger.info(f"Starting batch job {job_id}: {job.count} items")

        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == job.campaign_id).first()
        if not campaign:
            raise Exception("Campaign not found")

        # Get segment data (if provided)
        segment_data = {}
        if job.segment_id:
            segment = db.query(Segment).filter(Segment.id == job.segment_id).first()
            if segment:
                segment_data = {
                    "tone": segment.tone,
                    "keywords": segment.keywords,
                    "prompt_template": segment.prompt_template
                }

        # Get prompt template (if provided)
        base_prompt = None
        if job.prompt_template_id:
            prompt_template = db.query(PromptTemplate).filter(
                PromptTemplate.id == job.prompt_template_id
            ).first()
            if prompt_template:
                base_prompt = prompt_template.template

                # Inject segment data into prompt
                if segment_data:
                    if segment_data.get("tone"):
                        base_prompt = base_prompt.replace("{tone}", segment_data["tone"])
                    if segment_data.get("keywords"):
                        base_prompt = base_prompt.replace("{keywords}", segment_data["keywords"])

        # Get creative template (if provided)
        creative_template = None
        if job.creative_template_id:
            creative_template = db.query(CreativeTemplate).filter(
                CreativeTemplate.id == job.creative_template_id
            ).first()

        # Generate creatives
        creative_ids = []

        for i in range(job.count):
            try:
                # Build prompt
                if base_prompt:
                    prompt = base_prompt.replace("{index}", str(i + 1))
                else:
                    # Default prompt
                    prompt = f"Create engaging marketing content for {campaign.channel}"
                    if segment_data.get("tone"):
                        prompt += f" with {segment_data['tone']} tone"
                    if segment_data.get("keywords"):
                        prompt += f" focusing on: {segment_data['keywords']}"

                # Generate content based on type
                creative_name = f"Batch_{job_id}_Item_{i + 1}"
                asset_url = None
                thumbnail_url = None
                content_text = None

                if job.content_type in ['text', 'both']:
                    # Generate text
                    content_text = await generate_text(prompt)
                    logger.debug(f"Generated text for {creative_name}: {content_text[:50]}...")

                if job.content_type in ['image', 'both']:
                    # Generate image
                    image_prompt = prompt if job.content_type == 'image' else f"Create an image for: {content_text}"
                    image_url = await generate_image(image_prompt, size=campaign.size or "1024x1024")

                    if image_url:
                        # Download and upload to storage
                        import requests
                        response = requests.get(image_url)
                        if response.status_code == 200:
                            image_data = response.content
                            success, main_url, thumb_url, error = storage.upload_with_thumbnail(
                                image_data,
                                f"{creative_name}.jpg",
                                folder=f"campaigns/{campaign.id}/batch_{job_id}"
                            )
                            if success:
                                asset_url = main_url
                                thumbnail_url = thumb_url
                            else:
                                logger.error(f"Failed to upload image: {error}")

                # Create creative record
                creative = Creative(
                    campaign_id=campaign.id,
                    name=creative_name,
                    content_type='text' if job.content_type == 'text' else 'image',
                    content_text=content_text,
                    asset_url=asset_url,
                    thumbnail_url=thumbnail_url,
                    prompt=prompt,
                    status='draft',
                    metadata={
                        "batch_job_id": job_id,
                        "segment_id": job.segment_id,
                        "template_id": job.creative_template_id,
                        "index": i + 1
                    }
                )

                db.add(creative)
                db.commit()
                db.refresh(creative)

                creative_ids.append(creative.id)
                job.completed_items += 1
                job.progress = int((job.completed_items / job.total_items) * 100)
                db.commit()

                logger.info(f"Job {job_id}: Generated creative {creative.id} ({job.completed_items}/{job.total_items})")

                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Job {job_id}: Failed to generate item {i + 1}: {str(e)}")
                job.failed_items += 1
                db.commit()

        # Update job as completed
        job.status = 'completed'
        job.progress = 100
        job.creative_ids = creative_ids
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Batch job {job_id} completed: {job.completed_items} items, {job.failed_items} failed")

    except Exception as e:
        logger.error(f"Batch job {job_id} failed: {str(e)}", exc_info=True)

        # Update job as failed
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

    finally:
        db.close()


# ==========================================
# Batch Generation Endpoints
# ==========================================

@router.post("/", response_model=BatchGenerationResponse)
async def create_batch_job(
    request: BatchGenerationCreate,
    background_tasks: BackgroundTasks,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Create batch generation job

    Generates N creatives for a campaign with optional segment/template

    **Process:**
    1. Creates job with 'pending' status
    2. Returns job_id immediately
    3. Processes in background
    4. Poll `/batch/{job_id}` for status updates
    """
    # Validate campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == request.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Validate segment (if provided)
    if request.segment_id:
        segment = db.query(Segment).filter(Segment.id == request.segment_id).first()
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

    # Create job
    job = BatchGenerationJob(
        campaign_id=request.campaign_id,
        segment_id=request.segment_id,
        user_id=user_id,
        content_type=request.content_type,
        count=request.count,
        prompt_template_id=request.prompt_template_id,
        creative_template_id=request.creative_template_id,
        parameters=request.parameters,
        status='pending',
        total_items=request.count
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Batch job created: {job.id} - Campaign {campaign.id}, {request.count} items")

    # Start background processing
    from database import SessionLocal
    background_tasks.add_task(process_batch_job, job.id, SessionLocal)

    return job


@router.get("/{job_id}", response_model=BatchGenerationResponse)
async def get_batch_job(job_id: int, db: Session = Depends(get_db)):
    """Get batch job status"""
    job = db.query(BatchGenerationJob).filter(BatchGenerationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/{job_id}/status", response_model=BatchGenerationStatus)
async def get_batch_status(job_id: int, db: Session = Depends(get_db)):
    """Get batch job status (lightweight)"""
    job = db.query(BatchGenerationJob).filter(BatchGenerationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Estimate time remaining
    estimated_time = None
    if job.status == 'processing' and job.completed_items > 0:
        elapsed = (datetime.utcnow() - job.started_at).total_seconds()
        avg_time_per_item = elapsed / job.completed_items
        remaining_items = job.total_items - job.completed_items
        estimated_time = int(avg_time_per_item * remaining_items)

    return BatchGenerationStatus(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        completed_items=job.completed_items,
        total_items=job.total_items,
        estimated_time_remaining=estimated_time
    )


@router.get("/", response_model=List[BatchGenerationResponse])
async def list_batch_jobs(
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List batch jobs with filters"""
    query = db.query(BatchGenerationJob)

    if campaign_id:
        query = query.filter(BatchGenerationJob.campaign_id == campaign_id)
    if status:
        query = query.filter(BatchGenerationJob.status == status)

    jobs = query.order_by(BatchGenerationJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.delete("/{job_id}")
async def cancel_batch_job(job_id: int, db: Session = Depends(get_db)):
    """
    Cancel batch job (if pending or processing)

    Note: Already generated creatives are NOT deleted
    """
    job = db.query(BatchGenerationJob).filter(BatchGenerationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ['completed', 'failed']:
        raise HTTPException(status_code=400, detail=f"Cannot cancel {job.status} job")

    # Mark as failed with cancellation message
    job.status = 'failed'
    job.error_message = 'Job cancelled by user'
    job.completed_at = datetime.utcnow()
    db.commit()

    logger.info(f"Batch job {job_id} cancelled")

    return {
        "success": True,
        "message": "Job cancelled",
        "completed_items": job.completed_items,
        "creative_ids": job.creative_ids
    }


@router.get("/campaigns/{campaign_id}/batch-stats")
async def get_campaign_batch_stats(campaign_id: int, db: Session = Depends(get_db)):
    """Get batch generation statistics for campaign"""
    jobs = db.query(BatchGenerationJob).filter(
        BatchGenerationJob.campaign_id == campaign_id
    ).all()

    total_jobs = len(jobs)
    completed_jobs = sum(1 for j in jobs if j.status == 'completed')
    failed_jobs = sum(1 for j in jobs if j.status == 'failed')
    processing_jobs = sum(1 for j in jobs if j.status == 'processing')
    pending_jobs = sum(1 for j in jobs if j.status == 'pending')

    total_creatives = sum(j.completed_items for j in jobs)
    total_failed = sum(j.failed_items for j in jobs)

    return {
        "campaign_id": campaign_id,
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "processing_jobs": processing_jobs,
        "pending_jobs": pending_jobs,
        "total_creatives_generated": total_creatives,
        "total_failed_items": total_failed,
        "success_rate": (total_creatives / (total_creatives + total_failed) * 100) if (total_creatives + total_failed) > 0 else 0
    }
