"""
Artify Content Backend - FastAPI
Provides AI generation, segments management, and analytics
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime
import random

from dotenv import load_dotenv
from openai import OpenAI

from database import get_db, init_db, Segment, GeneratedContent, Metric

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Artify Content API",
    description="AI-powered content generation and analytics",
    version="2.0.0"
)

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
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ==========================================
# Pydantic Models (Request/Response)
# ==========================================

class TextGenerationRequest(BaseModel):
    prompt: str
    segment_id: Optional[int] = None
    tone: Optional[str] = "전문적"
    keywords: Optional[List[str]] = []
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7


class ImageGenerationRequest(BaseModel):
    prompt: str
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
        "endpoints": [
            "/health",
            "/generate/text",
            "/generate/image",
            "/segments",
            "/metrics/simulate"
        ]
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
async def generate_text(
    request: TextGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate AI text using OpenAI GPT"""
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
            "model": "gpt-3.5-turbo"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/image")
async def generate_image(
    request: ImageGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate AI image using OpenAI DALL-E"""
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
            "model": "dall-e-3"
        }

    except Exception as e:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
