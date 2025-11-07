"""
Artify Content Backend - FastAPI
Provides AI generation, segments management, and analytics
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import os
from datetime import datetime, timedelta
import random

from dotenv import load_dotenv
from openai import OpenAI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import get_db, init_db, Segment, GeneratedContent, Metric, GenerationJob, UserQuota

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Artify Content API",
    description="AI-powered content generation and analytics",
    version="2.0.0"
)

# Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://artify-ruddy.vercel.app",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "":
    print("⚠️  WARNING: OPENAI_API_KEY not set. AI generation will fail.")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI API client initialized")


# Cost estimation (USD per token)
# Reference: https://openai.com/pricing
PRICING = {
    "gpt-3.5-turbo": {
        "input": 0.0005 / 1000,  # $0.0005 per 1K input tokens
        "output": 0.0015 / 1000  # $0.0015 per 1K output tokens
    },
    "gpt-4": {
        "input": 0.03 / 1000,
        "output": 0.06 / 1000
    },
    "dall-e-3": {
        "1024x1024": 0.040,  # per image
        "1024x1792": 0.080,
        "1792x1024": 0.080
    }
}


def calculate_text_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated cost for text generation"""
    if model not in PRICING:
        return 0.0

    pricing = PRICING[model]
    input_cost = prompt_tokens * pricing["input"]
    output_cost = completion_tokens * pricing["output"]
    return round(input_cost + output_cost, 6)


def calculate_image_cost(model: str, size: str) -> float:
    """Calculate estimated cost for image generation"""
    if model not in PRICING:
        return 0.0

    pricing = PRICING.get(model, {})
    return pricing.get(size, 0.04)  # Default to standard size cost


# ==========================================
# Quota Management Functions
# ==========================================

async def get_or_create_quota(user_id: int, db: Session) -> UserQuota:
    """Get or create user quota"""
    quota = db.query(UserQuota).filter_by(user_id=user_id).first()
    if not quota:
        quota = UserQuota(user_id=user_id)
        db.add(quota)
        db.commit()
        db.refresh(quota)
    return quota


async def check_quota(user_id: int, job_type: str, db: Session, estimated_cost: float = 0.0):
    """Check and update user quota before generation"""
    quota = await get_or_create_quota(user_id, db)

    # Daily reset check
    if (datetime.utcnow() - quota.last_daily_reset).days >= 1:
        quota.daily_text_used = 0
        quota.daily_image_used = 0
        quota.last_daily_reset = datetime.utcnow()

    # Monthly reset check
    if (datetime.utcnow() - quota.last_monthly_reset).days >= 30:
        quota.monthly_cost_used = 0.0
        quota.last_monthly_reset = datetime.utcnow()

    # Check daily quota limits
    if job_type == "text":
        if quota.daily_text_used >= quota.daily_text_quota:
            raise HTTPException(
                status_code=429,
                detail=f"Daily text generation quota exceeded. Limit: {quota.daily_text_quota}"
            )
        quota.daily_text_used += 1

    if job_type == "image":
        if quota.daily_image_used >= quota.daily_image_quota:
            raise HTTPException(
                status_code=429,
                detail=f"Daily image generation quota exceeded. Limit: {quota.daily_image_quota}"
            )
        quota.daily_image_used += 1

    # Check monthly cost cap
    if quota.monthly_cost_used >= quota.monthly_cost_cap:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly cost cap exceeded. Cap: ${quota.monthly_cost_cap}"
        )

    db.commit()
    return quota


async def update_quota_cost(user_id: int, cost: float, db: Session):
    """Update user quota with actual generation cost"""
    quota = await get_or_create_quota(user_id, db)
    quota.monthly_cost_used += cost
    db.commit()


# ==========================================
# Pydantic Models (Request/Response)
# ==========================================

class TextGenerationRequest(BaseModel):
    prompt: str
    user_id: int = 1  # Default to user 1 for now (should come from auth)
    segment_id: Optional[int] = None
    tone: Optional[str] = "전문적"
    keywords: Optional[List[str]] = []
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7


class ImageGenerationRequest(BaseModel):
    prompt: str
    user_id: int = 1  # Default to user 1 for now (should come from auth)
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"


class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    criteria: Optional[str] = None


class SegmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    criteria: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MetricsRequest(BaseModel):
    projectId: int


# ==========================================
# Health & Root Endpoints
# ==========================================

@app.get("/")
async def root():
    return {
        "message": "Artify Content API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "AI Text Generation (GPT-3.5-turbo)",
            "AI Image Generation (DALL-E 3)",
            "Rate Limiting (10/min text, 5/min images)",
            "User Quotas (Daily & Monthly)",
            "Cost Tracking & Dashboard"
        ],
        "endpoints": {
            "generation": [
                "/generate/text",
                "/generate/image"
            ],
            "segments": [
                "/segments",
                "/segments/{id}"
            ],
            "analytics": [
                "/metrics/simulate",
                "/metrics/history/{project_id}"
            ],
            "cost_management": [
                "/users/{user_id}/quota",
                "/users/{user_id}/costs/daily",
                "/users/{user_id}/costs/monthly",
                "/costs/summary",
                "/costs/history"
            ],
            "health": [
                "/health"
            ]
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "artify-content-api",
        "version": "2.0.0",
        "database": "connected",
        "ai": "OpenAI API"
    }


# ==========================================
# AI Generation Endpoints
# ==========================================

@app.post("/generate/text")
@limiter.limit("10/minute")
async def generate_text(
    req: Request,
    request: TextGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate AI text using OpenAI GPT"""

    # Check if OpenAI client is initialized
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    # Check user quota before generation
    await check_quota(request.user_id, "text", db)

    job = GenerationJob(
        user_id=request.user_id,
        job_type="text",
        model="gpt-3.5-turbo",
        prompt=request.prompt,
        status="pending"
    )
    db.add(job)
    db.commit()

    try:
        # Build enhanced prompt with segment, tone, and keywords
        enhanced_prompt = request.prompt

        if request.segment_id:
            segment = db.query(Segment).filter(Segment.id == request.segment_id).first()
            if segment:
                enhanced_prompt += f"\n타겟 세그먼트: {segment.name}"

        if request.tone:
            enhanced_prompt += f"\n톤: {request.tone}"

        if request.keywords and len(request.keywords) > 0:
            keywords_str = ", ".join(request.keywords)
            enhanced_prompt += f"\n필수 키워드: {keywords_str}"

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful content creation assistant for marketing campaigns. Create engaging, persuasive content in Korean."},
                {"role": "user", "content": enhanced_prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        generated_text = response.choices[0].message.content

        # Extract token usage
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        # Calculate cost
        estimated_cost = calculate_text_cost("gpt-3.5-turbo", prompt_tokens, completion_tokens)

        # Update job with success
        job.status = "completed"
        job.prompt_tokens = prompt_tokens
        job.completion_tokens = completion_tokens
        job.total_tokens = total_tokens
        job.estimated_cost = estimated_cost
        job.completed_at = datetime.utcnow()
        db.commit()

        # Update user quota with actual cost
        await update_quota_cost(request.user_id, estimated_cost, db)

        # Save to database
        content_record = GeneratedContent(
            content_type="text",
            prompt=request.prompt,
            result=generated_text,
            model="gpt-3.5-turbo"
        )
        db.add(content_record)
        db.commit()

        return {
            "success": True,
            "text": generated_text,
            "prompt": request.prompt,
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": estimated_cost
            }
        }

    except Exception as e:
        # Update job with error
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/image")
@limiter.limit("5/minute")
async def generate_image(
    req: Request,
    request: ImageGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate AI image using OpenAI DALL-E"""

    # Check if OpenAI client is initialized
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    # Calculate cost upfront for images
    estimated_cost = calculate_image_cost("dall-e-3", request.size)

    # Check user quota before generation
    await check_quota(request.user_id, "image", db, estimated_cost)

    job = GenerationJob(
        user_id=request.user_id,
        job_type="image",
        model="dall-e-3",
        prompt=request.prompt,
        status="pending",
        estimated_cost=estimated_cost
    )
    db.add(job)
    db.commit()

    try:
        # Call OpenAI DALL-E API
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            n=1
        )

        image_url = response.data[0].url

        # Update job with success
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        # Update user quota with actual cost
        await update_quota_cost(request.user_id, estimated_cost, db)

        # Save to database
        content_record = GeneratedContent(
            content_type="image",
            prompt=request.prompt,
            result=image_url,
            model="dall-e-3"
        )
        db.add(content_record)
        db.commit()

        return {
            "success": True,
            "imageUrl": image_url,
            "prompt": request.prompt,
            "model": "dall-e-3",
            "usage": {
                "estimated_cost_usd": estimated_cost
            }
        }

    except Exception as e:
        # Update job with error
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Segments Management Endpoints
# ==========================================

@app.get("/segments", response_model=List[SegmentResponse])
async def get_segments(db: Session = Depends(get_db)):
    """Get all segments"""
    segments = db.query(Segment).all()
    return segments


@app.post("/segments", response_model=SegmentResponse)
async def create_segment(
    segment: SegmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new segment"""
    try:
        new_segment = Segment(
            name=segment.name,
            description=segment.description,
            criteria=segment.criteria
        )
        db.add(new_segment)
        db.commit()
        db.refresh(new_segment)
        return new_segment

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/segments/{segment_id}", response_model=SegmentResponse)
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    """Get a specific segment"""
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment


@app.delete("/segments/{segment_id}")
async def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    """Delete a segment"""
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    db.delete(segment)
    db.commit()
    return {"success": True, "message": "Segment deleted successfully"}


# ==========================================
# Metrics & Analytics Endpoints
# ==========================================

@app.post("/metrics/simulate")
async def simulate_metrics(
    request: MetricsRequest,
    db: Session = Depends(get_db)
):
    """Simulate analytics metrics for a project"""
    try:
        # Generate simulated metrics
        metrics_data = {
            "projectId": request.projectId,
            "views": random.randint(1000, 10000),
            "engagement": round(random.uniform(0.1, 0.8), 2),
            "conversions": random.randint(10, 500),
            "revenue": round(random.uniform(100, 5000), 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Save metrics to database
        for metric_name, metric_value in [
            ("views", metrics_data["views"]),
            ("engagement", metrics_data["engagement"]),
            ("conversions", metrics_data["conversions"]),
            ("revenue", metrics_data["revenue"])
        ]:
            metric = Metric(
                project_id=request.projectId,
                metric_name=metric_name,
                metric_value=float(metric_value)
            )
            db.add(metric)

        db.commit()

        return {
            "success": True,
            "metrics": metrics_data
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/history/{project_id}")
async def get_metrics_history(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get historical metrics for a project"""
    metrics = db.query(Metric).filter(Metric.project_id == project_id).all()

    # Group by metric name
    grouped_metrics = {}
    for metric in metrics:
        if metric.metric_name not in grouped_metrics:
            grouped_metrics[metric.metric_name] = []
        grouped_metrics[metric.metric_name].append({
            "value": metric.metric_value,
            "timestamp": metric.timestamp.isoformat()
        })

    return {
        "projectId": project_id,
        "metrics": grouped_metrics
    }


# ==========================================
# Startup Event
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("=" * 50)
    print("🚀 Artify Content API Starting...")
    print("=" * 50)
    print("Initializing database...")
    init_db()
    print("✓ Database initialized")
    print("✓ OpenAI API configured")
    print("=" * 50)
    print("Ready to serve requests!")
    print("=" * 50)


# ==========================================
# Cost Tracking & Statistics Endpoints
# ==========================================

@app.get("/users/{user_id}/quota")
async def get_user_quota(user_id: int, db: Session = Depends(get_db)):
    """Get user quota information"""
    quota = await get_or_create_quota(user_id, db)

    return {
        "user_id": user_id,
        "daily_limits": {
            "text_quota": quota.daily_text_quota,
            "text_used": quota.daily_text_used,
            "text_remaining": quota.daily_text_quota - quota.daily_text_used,
            "image_quota": quota.daily_image_quota,
            "image_used": quota.daily_image_used,
            "image_remaining": quota.daily_image_quota - quota.daily_image_used,
            "last_reset": quota.last_daily_reset.isoformat()
        },
        "monthly_limits": {
            "cost_cap_usd": quota.monthly_cost_cap,
            "cost_used_usd": round(quota.monthly_cost_used, 4),
            "cost_remaining_usd": round(quota.monthly_cost_cap - quota.monthly_cost_used, 4),
            "usage_percentage": round((quota.monthly_cost_used / quota.monthly_cost_cap) * 100, 2),
            "last_reset": quota.last_monthly_reset.isoformat()
        }
    }


@app.get("/users/{user_id}/costs/daily")
async def get_daily_costs(user_id: int, db: Session = Depends(get_db)):
    """Get daily cost breakdown for a user"""
    # Get today's date range
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Query jobs from today
    jobs = db.query(GenerationJob).filter(
        GenerationJob.user_id == user_id,
        GenerationJob.created_at >= today_start,
        GenerationJob.status == "completed"
    ).all()

    text_jobs = [j for j in jobs if j.job_type == "text"]
    image_jobs = [j for j in jobs if j.job_type == "image"]

    total_cost = sum(j.estimated_cost or 0 for j in jobs)
    text_cost = sum(j.estimated_cost or 0 for j in text_jobs)
    image_cost = sum(j.estimated_cost or 0 for j in image_jobs)
    total_tokens = sum(j.total_tokens or 0 for j in text_jobs)

    return {
        "user_id": user_id,
        "date": today_start.date().isoformat(),
        "total_cost_usd": round(total_cost, 4),
        "total_jobs": len(jobs),
        "breakdown": {
            "text": {
                "jobs": len(text_jobs),
                "cost_usd": round(text_cost, 4),
                "total_tokens": total_tokens
            },
            "image": {
                "jobs": len(image_jobs),
                "cost_usd": round(image_cost, 4)
            }
        }
    }


@app.get("/users/{user_id}/costs/monthly")
async def get_monthly_costs(user_id: int, db: Session = Depends(get_db)):
    """Get monthly cost breakdown for a user"""
    # Get this month's date range
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Query jobs from this month
    jobs = db.query(GenerationJob).filter(
        GenerationJob.user_id == user_id,
        GenerationJob.created_at >= month_start,
        GenerationJob.status == "completed"
    ).all()

    # Group by day
    daily_costs = {}
    for job in jobs:
        day = job.created_at.date().isoformat()
        if day not in daily_costs:
            daily_costs[day] = {"cost": 0, "jobs": 0}
        daily_costs[day]["cost"] += job.estimated_cost or 0
        daily_costs[day]["jobs"] += 1

    text_jobs = [j for j in jobs if j.job_type == "text"]
    image_jobs = [j for j in jobs if j.job_type == "image"]

    total_cost = sum(j.estimated_cost or 0 for j in jobs)
    text_cost = sum(j.estimated_cost or 0 for j in text_jobs)
    image_cost = sum(j.estimated_cost or 0 for j in image_jobs)
    total_tokens = sum(j.total_tokens or 0 for j in text_jobs)

    # Get quota for cost cap
    quota = await get_or_create_quota(user_id, db)

    return {
        "user_id": user_id,
        "month": month_start.strftime("%Y-%m"),
        "total_cost_usd": round(total_cost, 4),
        "cost_cap_usd": quota.monthly_cost_cap,
        "remaining_budget_usd": round(quota.monthly_cost_cap - total_cost, 4),
        "total_jobs": len(jobs),
        "daily_breakdown": {
            day: {
                "cost_usd": round(data["cost"], 4),
                "jobs": data["jobs"]
            }
            for day, data in sorted(daily_costs.items())
        },
        "type_breakdown": {
            "text": {
                "jobs": len(text_jobs),
                "cost_usd": round(text_cost, 4),
                "total_tokens": total_tokens
            },
            "image": {
                "jobs": len(image_jobs),
                "cost_usd": round(image_cost, 4)
            }
        }
    }


@app.get("/costs/summary")
async def get_cost_summary(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get cost summary for all generation jobs"""
    query = db.query(GenerationJob)

    if user_id:
        query = query.filter(GenerationJob.user_id == user_id)

    jobs = query.all()

    total_cost = sum(job.estimated_cost or 0 for job in jobs)
    total_jobs = len(jobs)
    completed_jobs = len([j for j in jobs if j.status == "completed"])
    failed_jobs = len([j for j in jobs if j.status == "failed"])

    text_jobs = [j for j in jobs if j.job_type == "text"]
    image_jobs = [j for j in jobs if j.job_type == "image"]

    text_cost = sum(j.estimated_cost or 0 for j in text_jobs)
    image_cost = sum(j.estimated_cost or 0 for j in image_jobs)

    total_tokens = sum(j.total_tokens or 0 for j in text_jobs)

    return {
        "total_cost_usd": round(total_cost, 4),
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "breakdown": {
            "text": {
                "jobs": len(text_jobs),
                "cost_usd": round(text_cost, 4),
                "total_tokens": total_tokens
            },
            "image": {
                "jobs": len(image_jobs),
                "cost_usd": round(image_cost, 4)
            }
        }
    }


@app.get("/costs/history")
async def get_cost_history(
    limit: int = 50,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get recent generation job history with costs"""
    query = db.query(GenerationJob)

    if user_id:
        query = query.filter(GenerationJob.user_id == user_id)

    jobs = query.order_by(GenerationJob.created_at.desc()).limit(limit).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "model": job.model,
                "status": job.status,
                "prompt": job.prompt[:100] + "..." if len(job.prompt) > 100 else job.prompt,
                "tokens": job.total_tokens,
                "cost_usd": round(job.estimated_cost or 0, 6),
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error": job.error_message
            }
            for job in jobs
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
