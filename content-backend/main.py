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
from vector_client import get_vector_client
from cache import get_cache, TTL_SEGMENTS, TTL_BRAND_GUIDELINES, TTL_VECTOR_STATS, make_cache_key

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


class BrandGuidelineRequest(BaseModel):
    guideline_text: str
    category: Optional[str] = "general"
    metadata: Optional[dict] = {}


class BrandTextRequest(BaseModel):
    brand_id: int
    prompt: str
    user_id: int = 1
    category: Optional[str] = None  # Filter guidelines by category
    n_guidelines: int = 3  # Number of guidelines to use as context
    segment_id: Optional[int] = None
    tone: Optional[str] = "전문적"
    keywords: Optional[List[str]] = []
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7


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
            "Cost Tracking & Dashboard",
            "Vector DB Semantic Search (ChromaDB)",
            "Brand Guidelines RAG (Retrieval Augmented Generation)",
            "High-Performance Content Recommendations",
            "Prompt Caching System (95% similarity threshold)",
            "Cost Savings Analytics Dashboard",
            "Redis Cache Layer (Segments, Brand Guidelines, Vector Stats)"
        ],
        "endpoints": {
            "generation": [
                "/generate/text",
                "/generate/image",
                "/generate/text/with-brand"
            ],
            "segments": [
                "/segments",
                "/segments/{id}"
            ],
            "vector_search": [
                "/vector/stats",
                "/creatives/similar/text?query={query}&n_results=5",
                "/creatives/similar/image?query={query}&n_results=5",
                "/creatives/recommend?query={query}&min_performance=0.05"
            ],
            "brand_guidelines": [
                "/brands/{brand_id}/guidelines",
                "/brands/{brand_id}/guidelines?category={category}"
            ],
            "analytics": [
                "/metrics/simulate",
                "/metrics/history/{project_id}",
                "/creatives/{content_id}/update-performance"
            ],
            "cost_management": [
                "/users/{user_id}/quota",
                "/users/{user_id}/costs/daily",
                "/users/{user_id}/costs/monthly",
                "/costs/summary",
                "/costs/history",
                "/analytics/cache-savings"
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

    # Check cache first
    try:
        vector_client = get_vector_client()
        cache_hit = vector_client.search_prompt_cache(
            query=request.prompt,
            job_type="text",
            model="gpt-3.5-turbo",
            similarity_threshold=0.95  # 95% similarity
        )

        if cache_hit:
            # Cache hit! Return cached result without calling OpenAI
            cached_text = cache_hit["cached_result"]

            # Save to database with cache flag
            content_record = GeneratedContent(
                content_type="text",
                prompt=request.prompt,
                result=cached_text,
                model="gpt-3.5-turbo",
                cache_key=cache_hit["cache_id"],
                is_cached_result=True
            )
            db.add(content_record)
            db.commit()
            db.refresh(content_record)

            return {
                "success": True,
                "text": cached_text,
                "prompt": request.prompt,
                "model": "gpt-3.5-turbo",
                "cached": True,
                "cache_info": {
                    "cache_id": cache_hit["cache_id"],
                    "similarity": cache_hit["similarity"],
                    "hit_count": cache_hit["hit_count"],
                    "cached_at": cache_hit["cached_at"]
                },
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "cost_saved": True
                }
            }
    except Exception as e:
        # Cache check failed, continue with normal generation
        print(f"⚠️  Warning: Cache check failed: {e}")

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
        db.refresh(content_record)

        # Save to Vector DB for semantic search
        try:
            vector_client = get_vector_client()
            vector_client.add_text_content(
                content_id=content_record.id,
                text=generated_text,
                prompt=request.prompt,
                model="gpt-3.5-turbo",
                metadata={
                    "user_id": request.user_id,
                    "segment_id": request.segment_id,
                    "tone": request.tone,
                    "keywords": ",".join(request.keywords) if request.keywords else None
                }
            )

            # Also add to prompt cache for future reuse
            try:
                cache_id = vector_client.add_prompt_cache(
                    prompt=request.prompt,
                    result=generated_text,
                    model="gpt-3.5-turbo",
                    job_type="text",
                    metadata={
                        "user_id": request.user_id,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "cost_usd": estimated_cost
                    }
                )
                print(f"✅ Added to prompt cache: {cache_id}")
            except Exception as cache_error:
                print(f"⚠️  Warning: Failed to add to prompt cache: {cache_error}")

        except Exception as e:
            # Vector DB 저장 실패해도 메인 플로우는 계속 진행
            print(f"⚠️  Warning: Failed to save to Vector DB: {e}")

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

    # Check cache first
    try:
        vector_client = get_vector_client()
        cache_hit = vector_client.search_prompt_cache(
            query=request.prompt,
            job_type="image",
            model="dall-e-3",
            similarity_threshold=0.95  # 95% similarity
        )

        if cache_hit:
            # Cache hit! Return cached result without calling OpenAI
            cached_url = cache_hit["cached_result"]

            # Save to database with cache flag
            content_record = GeneratedContent(
                content_type="image",
                prompt=request.prompt,
                result=cached_url,
                model="dall-e-3",
                cache_key=cache_hit["cache_id"],
                is_cached_result=True
            )
            db.add(content_record)
            db.commit()
            db.refresh(content_record)

            return {
                "success": True,
                "imageUrl": cached_url,
                "prompt": request.prompt,
                "model": "dall-e-3",
                "cached": True,
                "cache_info": {
                    "cache_id": cache_hit["cache_id"],
                    "similarity": cache_hit["similarity"],
                    "hit_count": cache_hit["hit_count"],
                    "cached_at": cache_hit["cached_at"]
                },
                "usage": {
                    "estimated_cost_usd": 0.0,
                    "cost_saved": estimated_cost
                }
            }
    except Exception as e:
        # Cache check failed, continue with normal generation
        print(f"⚠️  Warning: Cache check failed: {e}")

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
        db.refresh(content_record)

        # Save to Vector DB for semantic search
        try:
            vector_client = get_vector_client()
            vector_client.add_image_metadata(
                content_id=content_record.id,
                prompt=request.prompt,
                image_url=image_url,
                model="dall-e-3",
                metadata={
                    "user_id": request.user_id,
                    "size": request.size,
                    "quality": request.quality
                }
            )

            # Also add to prompt cache for future reuse
            try:
                cache_id = vector_client.add_prompt_cache(
                    prompt=request.prompt,
                    result=image_url,
                    model="dall-e-3",
                    job_type="image",
                    metadata={
                        "user_id": request.user_id,
                        "size": request.size,
                        "quality": request.quality,
                        "cost_usd": estimated_cost
                    }
                )
                print(f"✅ Added to prompt cache: {cache_id}")
            except Exception as cache_error:
                print(f"⚠️  Warning: Failed to add to prompt cache: {cache_error}")

        except Exception as e:
            # Vector DB 저장 실패해도 메인 플로우는 계속 진행
            print(f"⚠️  Warning: Failed to save to Vector DB: {e}")

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
    """Get all segments with Redis caching"""
    cache = get_cache()
    cache_key = "segments:all"

    # 캐시 확인
    cached = cache.get(cache_key)
    if cached:
        logger.info("Cache HIT: segments")
        return cached

    # DB 조회
    segments = db.query(Segment).all()

    # 캐시 저장 (1시간)
    segments_dict = [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "criteria": s.criteria,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat()
        }
        for s in segments
    ]
    cache.set(cache_key, segments_dict, TTL_SEGMENTS)

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

        # 캐시 무효화
        cache = get_cache()
        cache.delete("segments:all")
        logger.info("Cache invalidated: segments:all")

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

    # 캐시 무효화
    cache = get_cache()
    cache.delete("segments:all")
    logger.info("Cache invalidated: segments:all")

    return {"success": True, "message": "Segment deleted successfully"}


# ==========================================
# Vector DB & Semantic Search Endpoints
# ==========================================

@app.get("/vector/stats")
async def get_vector_stats():
    """Get Vector DB statistics with caching"""
    cache = get_cache()
    cache_key = "vector:stats"

    # 캐시 확인 (5분)
    cached = cache.get(cache_key)
    if cached:
        logger.info("Cache HIT: vector stats")
        return cached

    try:
        vector_client = get_vector_client()
        stats = vector_client.get_collection_stats()

        response = {
            "success": True,
            "stats": stats
        }

        # 캐시 저장 (5분)
        cache.set(cache_key, response, TTL_VECTOR_STATS)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/creatives/similar/text")
async def search_similar_texts(
    query: str,
    n_results: int = 5,
    model: Optional[str] = None,
    user_id: Optional[int] = None
):
    """
    Search for similar text content using semantic search

    Query Parameters:
    - query: Search query text
    - n_results: Number of results to return (default: 5)
    - model: Filter by model (e.g., 'gpt-3.5-turbo')
    - user_id: Filter by user ID
    """
    try:
        vector_client = get_vector_client()

        # 메타데이터 필터 구성
        where = {}
        if model:
            where["model"] = model
        if user_id:
            where["user_id"] = user_id

        # 유사도 검색
        results = vector_client.search_similar_texts(
            query=query,
            n_results=n_results,
            where=where if where else None
        )

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/creatives/similar/image")
async def search_similar_images(
    query: str,
    n_results: int = 5,
    model: Optional[str] = None,
    user_id: Optional[int] = None
):
    """
    Search for similar image prompts using semantic search

    Query Parameters:
    - query: Search query text
    - n_results: Number of results to return (default: 5)
    - model: Filter by model (e.g., 'dall-e-3')
    - user_id: Filter by user ID
    """
    try:
        vector_client = get_vector_client()

        # 메타데이터 필터 구성
        where = {}
        if model:
            where["model"] = model
        if user_id:
            where["user_id"] = user_id

        # 유사도 검색
        results = vector_client.search_similar_images(
            query=query,
            n_results=n_results,
            where=where if where else None
        )

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/creatives/recommend")
async def recommend_high_performing(
    query: str,
    min_performance: float = 0.05,
    n_results: int = 5
):
    """
    Recommend high-performing similar content

    Query Parameters:
    - query: Search query
    - min_performance: Minimum performance score (0-1, default: 0.05 = 5%)
    - n_results: Number of results (default: 5)
    """
    try:
        vector_client = get_vector_client()

        # 고성과 콘텐츠 검색
        results = vector_client.search_high_performing_texts(
            query=query,
            min_score=min_performance,
            n_results=n_results
        )

        return {
            "success": True,
            "query": query,
            "min_performance_score": min_performance,
            "count": len(results),
            "recommendations": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/creatives/{content_id}/update-performance")
async def update_content_performance(
    content_id: int,
    content_type: str,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Update content performance based on simulated metrics

    Path Parameters:
    - content_id: Content ID

    Query Parameters:
    - content_type: 'text' or 'image'
    - project_id: Project ID for metrics lookup (optional)
    """
    try:
        # Validate content_type
        if content_type not in ["text", "image"]:
            raise HTTPException(400, "content_type must be 'text' or 'image'")

        # 메트릭 시뮬레이션 (실제로는 metrics 테이블에서 조회)
        if project_id:
            metrics = db.query(Metric).filter(Metric.project_id == project_id).all()

            impressions = sum(m.metric_value for m in metrics if m.metric_name == "views")
            clicks = sum(m.metric_value for m in metrics if m.metric_name == "engagement") * impressions if impressions > 0 else 0
            conversions = sum(m.metric_value for m in metrics if m.metric_name == "conversions")
        else:
            # 시뮬레이션 데이터
            impressions = random.randint(1000, 10000)
            clicks = int(impressions * random.uniform(0.01, 0.15))  # 1-15% CTR
            conversions = int(clicks * random.uniform(0.01, 0.10))  # 1-10% CVR

        # 성과 점수 계산
        ctr = clicks / impressions if impressions > 0 else 0
        cvr = conversions / clicks if clicks > 0 else 0
        performance_score = (ctr * 0.6) + (cvr * 0.4)  # CTR 60%, CVR 40% 가중치

        metrics_data = {
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": round(ctr, 4),
            "cvr": round(cvr, 4)
        }

        # Vector DB 업데이트
        vector_client = get_vector_client()
        success = vector_client.update_content_performance(
            content_id=content_id,
            content_type=content_type,
            performance_score=performance_score,
            metrics=metrics_data
        )

        if not success:
            raise HTTPException(404, f"Content {content_id} not found in Vector DB")

        return {
            "success": True,
            "content_id": content_id,
            "content_type": content_type,
            "performance_score": round(performance_score, 4),
            "metrics": metrics_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Brand Guidelines Management Endpoints
# ==========================================

@app.post("/brands/{brand_id}/guidelines")
async def add_brand_guideline(
    brand_id: int,
    request: BrandGuidelineRequest
):
    """
    Add a brand guideline to Vector DB

    Path Parameters:
    - brand_id: Brand identifier

    Body:
    - guideline_text: The brand guideline text
    - category: Category (e.g., 'tone', 'voice', 'style', 'values')
    - metadata: Additional metadata (optional)
    """
    try:
        vector_client = get_vector_client()

        doc_id = vector_client.add_brand_guideline(
            brand_id=brand_id,
            guideline_text=request.guideline_text,
            category=request.category,
            metadata=request.metadata
        )

        # 캐시 무효화 (해당 브랜드의 모든 가이드라인 캐시)
        cache = get_cache()
        cache.delete_pattern(f"brand:{brand_id}:guidelines:*")
        logger.info(f"Cache invalidated: brand:{brand_id}:guidelines:*")

        return {
            "success": True,
            "brand_id": brand_id,
            "guideline_id": doc_id,
            "category": request.category,
            "message": "Brand guideline added successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/brands/{brand_id}/guidelines")
async def get_brand_guidelines(
    brand_id: int,
    category: Optional[str] = None
):
    """
    Get brand guidelines for a brand with caching

    Path Parameters:
    - brand_id: Brand identifier

    Query Parameters:
    - category: Filter by category (optional)
    """
    cache = get_cache()
    cache_key = make_cache_key("brand", brand_id, "guidelines", category or "all")

    # 캐시 확인 (1시간)
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Cache HIT: brand guidelines {brand_id}")
        return cached

    try:
        vector_client = get_vector_client()

        results = vector_client.search_brand_guidelines(
            brand_id=brand_id,
            query=None,
            category=category,
            n_results=50  # Get all guidelines
        )

        response = {
            "success": True,
            "brand_id": brand_id,
            "category": category,
            "count": len(results),
            "guidelines": results
        }

        # 캐시 저장 (1시간)
        cache.set(cache_key, response, TTL_BRAND_GUIDELINES)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/text/with-brand")
@limiter.limit("10/minute")
async def generate_text_with_brand(
    req: Request,
    request: BrandTextRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI text using brand guidelines as context (RAG)

    This endpoint:
    1. Retrieves relevant brand guidelines from Vector DB
    2. Injects them as context into the prompt
    3. Generates text using OpenAI GPT with brand context

    Body:
    - brand_id: Brand identifier
    - prompt: User's generation prompt
    - user_id: User ID (default: 1)
    - category: Filter guidelines by category (optional)
    - n_guidelines: Number of guidelines to use (default: 3)
    - segment_id, tone, keywords, max_tokens, temperature: Same as /generate/text
    """

    # Check if OpenAI client is initialized
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    # Check user quota before generation
    await check_quota(request.user_id, "text", db)

    try:
        # 1. Retrieve brand context from Vector DB
        vector_client = get_vector_client()
        brand_context = vector_client.get_brand_context(
            brand_id=request.brand_id,
            query=request.prompt,
            category=request.category,
            n_results=request.n_guidelines
        )

        if not brand_context:
            raise HTTPException(
                status_code=404,
                detail=f"No brand guidelines found for brand_id={request.brand_id}"
            )

        # 2. Create generation job
        job = GenerationJob(
            user_id=request.user_id,
            job_type="text",
            model="gpt-3.5-turbo",
            prompt=request.prompt,
            status="pending"
        )
        db.add(job)
        db.commit()

        # 3. Build enhanced prompt with brand context
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

        # 4. Inject brand context into system message
        system_message = f"""You are a helpful content creation assistant for marketing campaigns.
Create engaging, persuasive content in Korean.

IMPORTANT: Follow these brand guidelines strictly:

{brand_context}

Ensure the generated content aligns with the brand's voice, tone, style, and values as described above."""

        # 5. Call OpenAI API with brand context
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": enhanced_prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        generated_text = response.choices[0].message.content

        # 6. Extract token usage and calculate cost
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        estimated_cost = calculate_text_cost("gpt-3.5-turbo", prompt_tokens, completion_tokens)

        # 7. Update job with success
        job.status = "completed"
        job.prompt_tokens = prompt_tokens
        job.completion_tokens = completion_tokens
        job.total_tokens = total_tokens
        job.estimated_cost = estimated_cost
        job.completed_at = datetime.utcnow()
        db.commit()

        # 8. Update user quota with actual cost
        await update_quota_cost(request.user_id, estimated_cost, db)

        # 9. Save to PostgreSQL
        content_record = GeneratedContent(
            content_type="text",
            prompt=request.prompt,
            result=generated_text,
            model="gpt-3.5-turbo"
        )
        db.add(content_record)
        db.commit()
        db.refresh(content_record)

        # 10. Save to Vector DB for semantic search
        try:
            vector_client.add_text_content(
                content_id=content_record.id,
                text=generated_text,
                prompt=request.prompt,
                model="gpt-3.5-turbo",
                metadata={
                    "user_id": request.user_id,
                    "brand_id": request.brand_id,
                    "segment_id": request.segment_id,
                    "tone": request.tone,
                    "keywords": ",".join(request.keywords) if request.keywords else None
                }
            )
        except Exception as e:
            print(f"⚠️  Warning: Failed to save to Vector DB: {e}")

        return {
            "success": True,
            "text": generated_text,
            "prompt": request.prompt,
            "model": "gpt-3.5-turbo",
            "brand_id": request.brand_id,
            "brand_context_used": True,
            "guidelines_applied": request.n_guidelines,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": estimated_cost
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        # Update job with error
        if 'job' in locals():
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    cache = get_cache()
    stats = cache.get_stats()
    return {
        "success": True,
        "cache": stats
    }


@app.post("/cache/flush")
async def flush_cache():
    """Flush all Redis cache (admin only - use with caution)"""
    cache = get_cache()
    result = cache.flush_all()
    return {
        "success": result,
        "message": "All cache flushed" if result else "Cache flush failed"
    }


@app.get("/analytics/cache-savings")
async def get_cache_savings(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get cache performance and cost savings analytics

    Query Parameters:
    - user_id: Filter by user (optional)

    Returns statistics on cache hits, misses, and total cost saved
    """
    try:
        # Get all generated content
        query = db.query(GeneratedContent)
        if user_id:
            # Note: GeneratedContent doesn't have user_id, would need to add it
            pass

        all_content = query.all()

        # Separate cached vs non-cached
        cached_content = [c for c in all_content if c.is_cached_result]
        generated_content = [c for c in all_content if not c.is_cached_result]

        # Count by type
        cached_text = [c for c in cached_content if c.content_type == "text"]
        cached_image = [c for c in cached_content if c.content_type == "image"]
        generated_text = [c for c in generated_content if c.content_type == "text"]
        generated_image = [c for c in generated_content if c.content_type == "image"]

        # Calculate costs saved
        # For text: avg tokens * pricing
        # For image: fixed pricing per image
        avg_text_tokens = 500  # Estimate
        text_cost_per_generation = calculate_text_cost("gpt-3.5-turbo", avg_text_tokens // 2, avg_text_tokens // 2)
        image_cost_per_generation = calculate_image_cost("dall-e-3", "1024x1024")

        text_cost_saved = len(cached_text) * text_cost_per_generation
        image_cost_saved = len(cached_image) * image_cost_per_generation
        total_cost_saved = text_cost_saved + image_cost_saved

        # Calculate hit rates
        total_text = len(cached_text) + len(generated_text)
        total_image = len(cached_image) + len(generated_image)
        total_requests = len(all_content)

        text_hit_rate = (len(cached_text) / total_text * 100) if total_text > 0 else 0
        image_hit_rate = (len(cached_image) / total_image * 100) if total_image > 0 else 0
        overall_hit_rate = (len(cached_content) / total_requests * 100) if total_requests > 0 else 0

        # Get Vector DB cache stats
        try:
            vector_client = get_vector_client()
            stats = vector_client.get_collection_stats()
            cache_collection_size = stats.get("prompt_cache", {}).get("count", 0)
        except Exception as e:
            print(f"⚠️  Warning: Failed to get Vector DB stats: {e}")
            cache_collection_size = 0

        return {
            "success": True,
            "cache_performance": {
                "overall_hit_rate_percent": round(overall_hit_rate, 2),
                "text_hit_rate_percent": round(text_hit_rate, 2),
                "image_hit_rate_percent": round(image_hit_rate, 2),
                "total_cache_hits": len(cached_content),
                "total_cache_misses": len(generated_content),
                "total_requests": total_requests
            },
            "cost_savings": {
                "total_saved_usd": round(total_cost_saved, 4),
                "text_saved_usd": round(text_cost_saved, 4),
                "image_saved_usd": round(image_cost_saved, 4),
                "text_cache_hits": len(cached_text),
                "image_cache_hits": len(cached_image)
            },
            "breakdown": {
                "text": {
                    "cache_hits": len(cached_text),
                    "cache_misses": len(generated_text),
                    "total": total_text,
                    "hit_rate_percent": round(text_hit_rate, 2)
                },
                "image": {
                    "cache_hits": len(cached_image),
                    "cache_misses": len(generated_image),
                    "total": total_image,
                    "hit_rate_percent": round(image_hit_rate, 2)
                }
            },
            "cache_collection": {
                "size": cache_collection_size,
                "description": "Total unique prompts cached in Vector DB"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
