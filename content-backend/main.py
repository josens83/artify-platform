"""
Artify Content Backend - FastAPI
Provides AI generation, segments management, and analytics
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional, List
import os
from datetime import datetime, timedelta
import random
import psutil
import shutil
import time

from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai
import requests
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import get_db, init_db, Segment, GeneratedContent, Metric, GenerationJob, UserQuota, Campaign, Creative, Event
from vector_client import get_vector_client
from cache import get_cache, TTL_SEGMENTS, TTL_BRAND_GUIDELINES, TTL_VECTOR_STATS, make_cache_key
from logger import get_logger, RequestLogger
from exceptions import register_exception_handlers, ArtifyException, QuotaExceededError
from campaigns_api import router as campaigns_router
from analytics_api import router as analytics_router
from auth_api import router as auth_router
from templates_api import router as templates_router
from batch_generation_api import router as batch_router
from internationalization_api import router as i18n_router

load_dotenv()

# Initialize logger
logger = get_logger("main")
api_logger = get_logger("api")

# Initialize FastAPI app with enhanced documentation
app = FastAPI(
    title="Artify Content API",
    description="""
# Artify Content Generation Platform API

AI-powered content generation and analytics platform with advanced features.

## Key Features

* 🤖 **AI Text Generation** - GPT-3.5-turbo powered content creation
* 🎨 **AI Image Generation** - DALL-E 3 image generation
* 🔒 **Rate Limiting** - 10/min for text, 5/min for images
* 📊 **User Quotas** - Daily and monthly usage limits
* 💰 **Cost Tracking** - Real-time cost estimation and analytics
* 🔍 **Vector Search** - Semantic search with ChromaDB
* 📚 **Brand Guidelines** - RAG-powered brand consistency
* ⚡ **Redis Caching** - High-performance caching layer
* 📈 **Analytics Dashboard** - Comprehensive metrics and monitoring
* 🔄 **Prompt Caching** - Duplicate detection and cost savings

## Authentication

Currently, this API does not require authentication. Rate limiting is applied per IP address.

## Rate Limits

- Text Generation: 10 requests/minute
- Image Generation: 5 requests/minute

## Support

For issues and feature requests, please contact the development team.
    """,
    version="2.0.0",
    terms_of_service="https://artify-ruddy.vercel.app/terms",
    contact={
        "name": "Artify Support",
        "url": "https://artify-ruddy.vercel.app",
        "email": "support@artify.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "authentication",
            "description": "JWT authentication and authorization endpoints"
        },
        {
            "name": "ai-generation",
            "description": "AI content generation endpoints (text and images)"
        },
        {
            "name": "campaigns",
            "description": "Campaign and creative management"
        },
        {
            "name": "segments",
            "description": "User segment management"
        },
        {
            "name": "templates",
            "description": "Prompt templates, creative templates, and channel presets"
        },
        {
            "name": "batch-generation",
            "description": "Batch generation jobs with queue system"
        },
        {
            "name": "internationalization",
            "description": "Multi-language support and social media integration"
        },
        {
            "name": "analytics",
            "description": "Usage analytics, event tracking, and cost tracking"
        },
        {
            "name": "vector-db",
            "description": "Vector database operations for semantic search"
        },
        {
            "name": "brand-guidelines",
            "description": "Brand guidelines management and RAG"
        },
        {
            "name": "cache",
            "description": "Cache management and statistics"
        },
        {
            "name": "monitoring",
            "description": "System monitoring and operational metrics"
        }
    ]
)

# Register exception handlers
register_exception_handlers(app)

# Include routers for campaigns, analytics, authentication, templates, batch generation, and i18n
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(analytics_router)
app.include_router(templates_router)
app.include_router(batch_router)
app.include_router(i18n_router)

# Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    RequestLogger.log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )

    # Add custom headers
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

    return response


# CORS Configuration
# CORS Configuration - Production whitelist
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "https://artify-ruddy.vercel.app",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Include OPTIONS for preflight
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to the client
    max_age=600,  # Cache preflight requests for 10 minutes
)

logger.info(f"CORS middleware configured with {len(CORS_ORIGINS)} origins")
logger.info(f"Allowed origins: {CORS_ORIGINS}")

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "":
    logger.warning("OPENAI_API_KEY not set. OpenAI generation will fail.")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI API client initialized")

# Google Gemini client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "":
    logger.warning("GOOGLE_API_KEY not set. Gemini generation will be unavailable.")
    gemini_client = None
else:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_client = genai.GenerativeModel('gemini-pro')
    logger.info("Google Gemini API client initialized")

# Stability AI configuration
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
if not STABILITY_API_KEY or STABILITY_API_KEY == "":
    logger.warning("STABILITY_API_KEY not set. Stability AI generation will be unavailable.")
    stability_enabled = False
else:
    stability_enabled = True
    logger.info("Stability AI API configured")


# Cost estimation (USD per token)
# References:
# - OpenAI: https://openai.com/pricing
# - Google AI: https://ai.google.dev/pricing
# - Stability AI: https://platform.stability.ai/pricing
PRICING = {
    "gpt-3.5-turbo": {
        "input": 0.0005 / 1000,  # $0.0005 per 1K input tokens
        "output": 0.0015 / 1000  # $0.0015 per 1K output tokens
    },
    "gpt-4": {
        "input": 0.03 / 1000,
        "output": 0.06 / 1000
    },
    "gemini-pro": {
        "input": 0.00025 / 1000,  # $0.00025 per 1K input tokens (cheaper than GPT-3.5)
        "output": 0.0005 / 1000   # $0.0005 per 1K output tokens
    },
    "dall-e-3": {
        "1024x1024": 0.040,  # per image
        "1024x1792": 0.080,
        "1792x1024": 0.080
    },
    "stable-diffusion-xl": {
        "1024x1024": 0.030,  # per image (cheaper than DALL-E)
        "1536x640": 0.030,
        "640x1536": 0.030
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
    model: Optional[str] = "auto"  # "gpt-3.5-turbo", "gemini-pro", "gpt-4-turbo", or "auto" for smart selection
    segment_id: Optional[int] = None
    tone: Optional[str] = "전문적"
    keywords: Optional[List[str]] = []
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7


class ImageGenerationRequest(BaseModel):
    prompt: str
    user_id: int = 1  # Default to user 1 for now (should come from auth)
    model: Optional[str] = "dall-e-3"  # "dall-e-3" or "stable-diffusion-xl"
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"  # Only for DALL-E


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

@app.get("/", tags=["health"])
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


@app.get("/models", tags=["ai-generation"])
async def get_available_models():
    """
    Get list of available AI models for text and image generation

    Returns:
    - Available models with their capabilities, pricing, and availability status
    """
    models = {
        "text_models": [
            {
                "id": "gpt-3.5-turbo",
                "name": "OpenAI GPT-3.5 Turbo",
                "provider": "OpenAI",
                "type": "text",
                "available": openai_client is not None,
                "pricing": {
                    "input_per_1k_tokens": "$0.0005",
                    "output_per_1k_tokens": "$0.0015"
                },
                "features": ["Fast", "Reliable", "Korean support"],
                "max_tokens": 4096
            },
            {
                "id": "gemini-pro",
                "name": "Google Gemini Pro",
                "provider": "Google",
                "type": "text",
                "available": gemini_client is not None,
                "pricing": {
                    "input_per_1k_tokens": "$0.00025",
                    "output_per_1k_tokens": "$0.0005"
                },
                "features": ["Cost-effective", "Fast", "Korean support"],
                "max_tokens": 30720
            }
        ],
        "image_models": [
            {
                "id": "dall-e-3",
                "name": "DALL-E 3",
                "provider": "OpenAI",
                "type": "image",
                "available": openai_client is not None,
                "pricing": {
                    "1024x1024": "$0.040",
                    "1024x1792": "$0.080",
                    "1792x1024": "$0.080"
                },
                "features": ["High quality", "Precise prompts", "HD option"],
                "supported_sizes": ["1024x1024", "1024x1792", "1792x1024"]
            },
            {
                "id": "stable-diffusion-xl",
                "name": "Stable Diffusion XL",
                "provider": "Stability AI",
                "type": "image",
                "available": stability_enabled,
                "pricing": {
                    "1024x1024": "$0.030",
                    "1536x640": "$0.030",
                    "640x1536": "$0.030"
                },
                "features": ["Cost-effective", "Fast", "Customizable"],
                "supported_sizes": ["1024x1024", "1536x640", "640x1536"]
            }
        ]
    }

    return {
        "success": True,
        "models": models,
        "summary": {
            "total_text_models": len(models["text_models"]),
            "total_image_models": len(models["image_models"]),
            "available_text_models": sum(1 for m in models["text_models"] if m["available"]),
            "available_image_models": sum(1 for m in models["image_models"] if m["available"])
        }
    }


@app.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Enhanced health check endpoint with detailed system status"""

    health_status = {
        "status": "healthy",
        "service": "artify-content-api",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    all_healthy = True

    # 1. Database Check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "PostgreSQL connected"
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 2. Redis Cache Check
    try:
        cache = get_cache()
        if cache.enabled:
            cache.client.ping()
            stats = cache.get_stats()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connected",
                "keys": stats.get("keys", 0),
                "memory": stats.get("used_memory_human", "unknown")
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "message": "Redis not available, cache disabled"
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 3. Vector Database Check (ChromaDB)
    try:
        vector_client = get_vector_client()
        collections = vector_client.get_collection_stats()
        health_status["checks"]["vector_db"] = {
            "status": "healthy",
            "message": "ChromaDB connected",
            "collections": len(collections)
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["vector_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 4. OpenAI API Check
    if openai_client:
        health_status["checks"]["openai"] = {
            "status": "healthy",
            "message": "OpenAI client initialized"
        }
    else:
        all_healthy = False
        health_status["checks"]["openai"] = {
            "status": "unhealthy",
            "message": "OpenAI API key not configured"
        }

    # 5. Disk Space Check
    try:
        disk = shutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)  # Convert to GB

        disk_status = "healthy"
        if disk_percent > 90:
            disk_status = "critical"
            all_healthy = False
        elif disk_percent > 80:
            disk_status = "warning"

        health_status["checks"]["disk_space"] = {
            "status": disk_status,
            "used_percent": round(disk_percent, 2),
            "free_gb": round(disk_free_gb, 2),
            "total_gb": round(disk.total / (1024**3), 2)
        }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "error": str(e)
        }

    # 6. Memory Check
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        memory_status = "healthy"
        if memory_percent > 90:
            memory_status = "critical"
            all_healthy = False
        elif memory_percent > 80:
            memory_status = "warning"

        health_status["checks"]["memory"] = {
            "status": memory_status,
            "used_percent": memory_percent,
            "available_gb": round(memory.available / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2)
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": str(e)
        }

    # Overall status
    if not all_healthy:
        health_status["status"] = "degraded"

    return health_status


# ==========================================
# AI Generation Endpoints
# ==========================================

@app.post("/generate/text", tags=["ai-generation"])
@limiter.limit("10/minute")
async def generate_text(
    req: Request,
    request: TextGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI text using GPT-3.5-turbo, Gemini Pro, or GPT-4 Turbo

    **Supported Models:**
    - gpt-3.5-turbo (OpenAI) - Fast & economical
    - gemini-pro (Google) - Rich context & analytical
    - gpt-4-turbo (OpenAI) - Complex understanding
    - auto - Smart model selection based on prompt

    **Rate Limit:** 10 requests per minute

    **Features:**
    - 🤖 AI Router: Intelligent model selection
    - 💰 Real-time cost estimation
    - 📊 Token usage tracking
    - 👤 User quota enforcement
    - 💾 Automatic caching for duplicate prompts
    - 🎯 Multi-model support
    """

    # Import AI Router
    from ai_router import AIRouter

    # Smart Model Selection
    selected_model = request.model
    router_info = None

    if request.model == "auto" or request.model is None:
        # Use AI Router to select best model
        router_result = AIRouter.select_model(
            prompt=request.prompt,
            task_type="text",
            tone=request.tone,
            max_tokens=request.max_tokens
        )
        selected_model = router_result["model"]
        router_info = router_result

        print(f"🤖 AI Router selected: {selected_model} (reason: {router_result['reason']})")

    # Validate selected model
    supported_models = ["gpt-3.5-turbo", "gemini-pro", "gpt-4-turbo"]
    if selected_model not in supported_models:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {selected_model}. Supported models: {', '.join(supported_models)} or 'auto'"
        )

    # Check if selected model's client is initialized
    if selected_model in ["gpt-3.5-turbo", "gpt-4-turbo"] and not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    if selected_model == "gemini-pro" and not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Google API key not configured. Please set GOOGLE_API_KEY environment variable."
        )

    # Check user quota before generation
    await check_quota(request.user_id, "text", db)

    # Check cache first
    try:
        vector_client = get_vector_client()
        cache_hit = vector_client.search_prompt_cache(
            query=request.prompt,
            job_type="text",
            model=selected_model,
            similarity_threshold=0.95  # 95% similarity
        )

        if cache_hit:
            # Cache hit! Return cached result without calling AI API
            cached_text = cache_hit["cached_result"]

            # Save to database with cache flag
            content_record = GeneratedContent(
                content_type="text",
                prompt=request.prompt,
                result=cached_text,
                model=selected_model,
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
                "model": selected_model,
                "requested_model": request.model,
                "router_info": router_info,
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
        model=selected_model,
        prompt=request.prompt,
        status="pending",
        segment_id=request.segment_id
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

        # 🧠 RAG: Retrieve brand guidelines and high-performing examples
        rag_context = ""
        rag_info = {
            "brand_guidelines_used": False,
            "examples_found": 0,
            "rag_enabled": False
        }

        try:
            vector_client = get_vector_client()
            rag_context_parts = []

            # 1. Retrieve brand guidelines if segment exists
            # Note: Brand guidelines feature ready, but requires brand_id in Segment model
            # This will be enabled when Segment table has brand_id column
            if request.segment_id:
                segment = db.query(Segment).filter(Segment.id == request.segment_id).first()
                if segment and hasattr(segment, 'brand_id') and segment.brand_id:
                    brand_context = vector_client.get_brand_context(
                        brand_id=segment.brand_id,
                        query=request.prompt,
                        n_results=2
                    )
                    if brand_context:
                        rag_context_parts.append(f"=== 브랜드 가이드라인 ===\n{brand_context}")
                        rag_info["brand_guidelines_used"] = True

            # 2. Retrieve high-performing similar content as examples
            similar_high_performers = vector_client.search_high_performing_texts(
                query=request.prompt,
                min_score=0.05,  # Performance score threshold
                n_results=3
            )

            if similar_high_performers:
                examples_text = "=== 고성과 콘텐츠 예시 ===\n"
                for i, example in enumerate(similar_high_performers, 1):
                    ctr = example.get('ctr', 0)
                    score = example.get('performance_score', 0)
                    content = example.get('content', '')[:200]  # Limit length
                    examples_text += f"\n[예시 {i}] (CTR: {ctr:.2%}, 성과점수: {score:.3f})\n{content}...\n"

                rag_context_parts.append(examples_text)
                rag_info["examples_found"] = len(similar_high_performers)

            # Combine RAG context
            if rag_context_parts:
                rag_context = "\n\n".join(rag_context_parts)
                rag_info["rag_enabled"] = True
                print(f"🧠 RAG enabled: brand_guidelines={rag_info['brand_guidelines_used']}, examples={rag_info['examples_found']}")

        except Exception as e:
            print(f"⚠️  Warning: RAG context retrieval failed: {e}")
            # Continue without RAG context

        # Build enhanced system message with RAG context
        system_message = "You are a helpful content creation assistant for marketing campaigns. Create engaging, persuasive content in Korean."

        if rag_context:
            system_message += f"\n\n{rag_context}\n\n위의 브랜드 가이드라인과 고성과 콘텐츠 예시를 참고하여, 사용자의 요청에 맞는 콘텐츠를 생성하세요."

        # Call AI API based on selected model
        generated_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if selected_model in ["gpt-3.5-turbo", "gpt-4-turbo"]:
            # OpenAI GPT (3.5 or 4) with RAG-enhanced system message
            response = openai_client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            generated_text = response.choices[0].message.content
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

        elif selected_model == "gemini-pro":
            # Google Gemini Pro with RAG-enhanced prompt
            # Gemini doesn't have separate system message, so prepend to prompt
            gemini_prompt = f"{system_message}\n\n{enhanced_prompt}"
            response = gemini_client.generate_content(
                gemini_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            )

            generated_text = response.text

            # Gemini doesn't provide exact token counts in the same way
            # Estimate tokens (rough approximation: ~4 characters per token)
            prompt_tokens = len(enhanced_prompt) // 4
            completion_tokens = len(generated_text) // 4
            total_tokens = prompt_tokens + completion_tokens

        # Calculate cost (use AI Router's estimation if available)
        from ai_router import AIRouter
        estimated_cost = AIRouter.estimate_cost(selected_model, prompt_tokens, completion_tokens)
        if estimated_cost == 0.0:
            # Fallback to old calculation
            estimated_cost = calculate_text_cost(selected_model, prompt_tokens, completion_tokens)

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
            model=selected_model
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
                model=selected_model,
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
                    model=selected_model,
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
            "model": selected_model,
            "requested_model": request.model,
            "router_info": router_info,
            "rag_info": rag_info,
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
    """
    Generate AI image using DALL-E 3 or Stable Diffusion XL

    **Supported Models:**
    - dall-e-3 (OpenAI)
    - stable-diffusion-xl (Stability AI)

    **Rate Limit:** 5 requests per minute
    """

    # Validate model parameter
    supported_models = ["dall-e-3", "stable-diffusion-xl"]
    if request.model not in supported_models:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {request.model}. Supported models: {', '.join(supported_models)}"
        )

    # Check if requested model's client is initialized
    if request.model == "dall-e-3" and not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    if request.model == "stable-diffusion-xl" and not stability_enabled:
        raise HTTPException(
            status_code=503,
            detail="Stability AI API key not configured. Please set STABILITY_API_KEY environment variable."
        )

    # Calculate cost upfront for images
    estimated_cost = calculate_image_cost(request.model, request.size)

    # Check user quota before generation
    await check_quota(request.user_id, "image", db, estimated_cost)

    # Check cache first
    try:
        vector_client = get_vector_client()
        cache_hit = vector_client.search_prompt_cache(
            query=request.prompt,
            job_type="image",
            model=request.model,
            similarity_threshold=0.95  # 95% similarity
        )

        if cache_hit:
            # Cache hit! Return cached result without calling AI API
            cached_url = cache_hit["cached_result"]

            # Save to database with cache flag
            content_record = GeneratedContent(
                content_type="image",
                prompt=request.prompt,
                result=cached_url,
                model=request.model,
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
                "model": request.model,
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
        model=request.model,
        prompt=request.prompt,
        status="pending",
        estimated_cost=estimated_cost
    )
    db.add(job)
    db.commit()

    try:
        # Call AI API based on selected model
        image_url = ""

        if request.model == "dall-e-3":
            # OpenAI DALL-E 3
            response = openai_client.images.generate(
                model="dall-e-3",
                prompt=request.prompt,
                size=request.size,
                quality=request.quality,
                n=1
            )
            image_url = response.data[0].url

        elif request.model == "stable-diffusion-xl":
            # Stability AI - Stable Diffusion XL
            # Validate size for Stability AI
            valid_sizes = ["1024x1024", "1536x640", "640x1536"]
            size = request.size if request.size in valid_sizes else "1024x1024"

            # Parse size
            width, height = map(int, size.split("x"))

            # Call Stability AI API
            api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

            headers = {
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = {
                "text_prompts": [
                    {
                        "text": request.prompt,
                        "weight": 1
                    }
                ],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 30
            }

            response = requests.post(api_url, headers=headers, json=payload)

            if response.status_code != 200:
                raise Exception(f"Stability AI API error: {response.text}")

            response_data = response.json()

            # Stability AI returns base64 encoded images
            # In production, you'd upload this to a storage service and return the URL
            # For now, we'll use a placeholder
            image_base64 = response_data["artifacts"][0]["base64"]
            image_url = f"data:image/png;base64,{image_base64}"

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
            model=request.model
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
                model=request.model,
                metadata={
                    "user_id": request.user_id,
                    "size": request.size,
                    "quality": request.quality if request.model == "dall-e-3" else None
                }
            )

            # Also add to prompt cache for future reuse
            try:
                cache_id = vector_client.add_prompt_cache(
                    prompt=request.prompt,
                    result=image_url,
                    model=request.model,
                    job_type="image",
                    metadata={
                        "user_id": request.user_id,
                        "size": request.size,
                        "quality": request.quality if request.model == "dall-e-3" else None,
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
            "model": request.model,
            "size": request.size,
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

@app.get("/segments", response_model=List[SegmentResponse], tags=["segments"])
async def get_segments(db: Session = Depends(get_db)):
    """
    Get all user segments

    **Caching:** Results are cached for 1 hour in Redis
    """
    try:
        cache = get_cache()
        cache_key = "segments:all"

        # 캐시 확인
        cached = cache.get(cache_key)
        if cached:
            logger.info("Cache HIT: segments")
            return cached

        # DB 조회
        segments = db.query(Segment).all()
        logger.info(f"Loaded {len(segments)} segments from database")

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

        return segments_dict
    except Exception as e:
        logger.error(f"Error loading segments: {str(e)}", exc_info=True)
        # Return empty list instead of crashing
        return []


@app.post("/segments", response_model=SegmentResponse)
async def create_segment(
    segment: SegmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new segment"""
    try:
        logger.info(f"Creating segment: name={segment.name}, criteria={segment.criteria}")

        new_segment = Segment(
            name=segment.name,
            description=segment.description,
            criteria=segment.criteria
        )
        db.add(new_segment)
        db.commit()
        db.refresh(new_segment)

        logger.info(f"Segment created successfully: id={new_segment.id}")

        # 캐시 무효화 (에러 발생해도 무시)
        try:
            cache = get_cache()
            cache.delete("segments:all")
            logger.info("Cache invalidated: segments:all")
        except Exception as cache_err:
            logger.warning(f"Failed to invalidate cache: {cache_err}")

        return new_segment

    except Exception as e:
        logger.error(f"Error creating segment: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create segment: {str(e)}")


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

    # Run Alembic migrations automatically
    print("🔄 Running database migrations...")
    try:
        import subprocess
        import sys

        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Check current migration status
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=current_dir,
            capture_output=True,
            text=True
        )

        if "head" in result.stdout:
            print("✓ Database is already at head revision")
        elif result.returncode != 0 or "No alembic" in result.stdout or "no alembic_version" in result.stderr.lower():
            # No version table, stamp at 004 first
            print("⚠️  No alembic version found, stamping at revision 004...")
            subprocess.run(
                [sys.executable, "-m", "alembic", "stamp", "004"],
                cwd=current_dir,
                check=False  # Don't fail if stamp fails
            )
            print("🔄 Upgrading to head...")
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=current_dir,
                check=True
            )
            print("✓ Migrations applied successfully")
        else:
            # Has a version, just upgrade
            print("📌 Upgrading to head...")
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=current_dir,
                check=True
            )
            print("✓ Migrations applied successfully")
    except Exception as e:
        print(f"⚠️  Migration warning: {str(e)}")
        print("Continuing without migrations...")

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


@app.get("/cache/stats", tags=["cache"])
async def get_cache_stats():
    """Get Redis cache statistics and performance metrics"""
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


@app.get("/monitoring/dashboard", tags=["monitoring"])
async def monitoring_dashboard(db: Session = Depends(get_db)):
    """
    Comprehensive monitoring dashboard with system metrics and operational statistics

    Returns:
    - System health summary
    - Database statistics
    - Cache performance metrics
    - API usage statistics
    - Cost tracking
    - Recent activity
    """

    dashboard = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "system": {},
        "database": {},
        "cache": {},
        "usage": {},
        "costs": {},
        "activity": {}
    }

    # 1. System Health Metrics
    try:
        memory = psutil.virtual_memory()
        disk = shutil.disk_usage("/")

        dashboard["system"] = {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 2)
            },
            "uptime": "N/A"  # Could be enhanced with process start time tracking
        }
    except Exception as e:
        dashboard["system"]["error"] = str(e)

    # 2. Database Statistics
    try:
        # Count records in each table
        segments_count = db.query(func.count(Segment.id)).scalar()
        content_count = db.query(func.count(GeneratedContent.id)).scalar()
        metrics_count = db.query(func.count(Metric.id)).scalar()
        jobs_count = db.query(func.count(GenerationJob.id)).scalar()
        quotas_count = db.query(func.count(UserQuota.user_id)).scalar()

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_content = db.query(func.count(GeneratedContent.id)).filter(
            GeneratedContent.created_at >= yesterday
        ).scalar()
        recent_jobs = db.query(func.count(GenerationJob.id)).filter(
            GenerationJob.created_at >= yesterday
        ).scalar()

        dashboard["database"] = {
            "tables": {
                "segments": segments_count,
                "generated_content": content_count,
                "metrics": metrics_count,
                "generation_jobs": jobs_count,
                "user_quotas": quotas_count
            },
            "recent_24h": {
                "content_generated": recent_content,
                "jobs_completed": recent_jobs
            },
            "status": "connected"
        }
    except Exception as e:
        dashboard["database"]["error"] = str(e)
        dashboard["status"] = "degraded"

    # 3. Cache Performance Metrics
    try:
        cache = get_cache()
        if cache.enabled:
            cache_stats = cache.get_stats()
            dashboard["cache"] = {
                "status": "connected",
                "redis_version": cache_stats.get("redis_version", "unknown"),
                "keys": cache_stats.get("keys", 0),
                "memory": cache_stats.get("used_memory_human", "unknown"),
                "hits": cache_stats.get("keyspace_hits", 0),
                "misses": cache_stats.get("keyspace_misses", 0),
                "hit_rate": cache_stats.get("hit_rate", 0.0)
            }
        else:
            dashboard["cache"] = {
                "status": "disabled",
                "message": "Redis not available, running without cache"
            }
    except Exception as e:
        dashboard["cache"] = {
            "status": "error",
            "error": str(e)
        }

    # 4. API Usage Statistics (last 24 hours)
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)

        # Text generation usage
        text_jobs = db.query(GenerationJob).filter(
            GenerationJob.job_type == "text",
            GenerationJob.created_at >= yesterday
        ).all()

        # Image generation usage
        image_jobs = db.query(GenerationJob).filter(
            GenerationJob.job_type == "image",
            GenerationJob.created_at >= yesterday
        ).all()

        # Success/failure rates
        text_successful = sum(1 for job in text_jobs if job.status == "completed")
        image_successful = sum(1 for job in image_jobs if job.status == "completed")

        dashboard["usage"] = {
            "last_24h": {
                "text_generations": {
                    "total": len(text_jobs),
                    "successful": text_successful,
                    "failed": len(text_jobs) - text_successful,
                    "success_rate": round((text_successful / len(text_jobs) * 100) if text_jobs else 0, 2)
                },
                "image_generations": {
                    "total": len(image_jobs),
                    "successful": image_successful,
                    "failed": len(image_jobs) - image_successful,
                    "success_rate": round((image_successful / len(image_jobs) * 100) if image_jobs else 0, 2)
                }
            }
        }
    except Exception as e:
        dashboard["usage"]["error"] = str(e)

    # 5. Cost Tracking (last 24 hours)
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)

        recent_jobs = db.query(GenerationJob).filter(
            GenerationJob.created_at >= yesterday
        ).all()

        total_cost_24h = sum(job.estimated_cost or 0.0 for job in recent_jobs)
        total_tokens_24h = sum(job.total_tokens or 0 for job in recent_jobs)

        # This month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_jobs = db.query(GenerationJob).filter(
            GenerationJob.created_at >= month_start
        ).all()

        total_cost_month = sum(job.estimated_cost or 0.0 for job in month_jobs)

        dashboard["costs"] = {
            "last_24h": {
                "total_cost_usd": round(total_cost_24h, 4),
                "total_tokens": total_tokens_24h,
                "avg_cost_per_request": round(total_cost_24h / len(recent_jobs), 6) if recent_jobs else 0.0
            },
            "this_month": {
                "total_cost_usd": round(total_cost_month, 4),
                "requests": len(month_jobs)
            }
        }
    except Exception as e:
        dashboard["costs"]["error"] = str(e)

    # 6. Recent Activity (last 10 jobs)
    try:
        recent_activity = db.query(GenerationJob).order_by(
            GenerationJob.created_at.desc()
        ).limit(10).all()

        dashboard["activity"] = {
            "recent_jobs": [
                {
                    "id": job.id,
                    "type": job.job_type,
                    "status": job.status,
                    "cost_usd": round(job.estimated_cost or 0.0, 6),
                    "tokens": job.total_tokens,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                }
                for job in recent_activity
            ]
        }
    except Exception as e:
        dashboard["activity"]["error"] = str(e)

    # 7. Vector Database Statistics
    try:
        vector_client = get_vector_client()
        collections = vector_client.get_collection_stats()

        dashboard["vector_db"] = {
            "status": "connected",
            "collections": collections
        }
    except Exception as e:
        dashboard["vector_db"] = {
            "status": "error",
            "error": str(e)
        }

    return dashboard


@app.get("/analytics/cache-savings", tags=["analytics"])
async def get_cache_savings(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get cache performance and cost savings analytics

    **Features:**
    - Prompt cache hit/miss rates
    - Estimated cost savings from caching
    - Duplicate prompt detection statistics

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
