from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import openai
from app.database import get_db
from app.models import User, GenJob
from app.config import get_settings
from utils.jwt_handler import get_current_user
from utils.rate_limiter import rate_limit
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Set OpenAI API key
openai.api_key = get_settings().openai_api_key

# Pydantic schemas
class TextGenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7
    model: Optional[str] = None

class ImageGenerateRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    n: Optional[int] = 1

class GenerateResponse(BaseModel):
    id: int
    type: str
    prompt: str
    response: str
    tokens: Optional[int]
    cost: Optional[float]

    class Config:
        from_attributes = True

@router.post("/text", response_model=GenerateResponse)
@rate_limit(max_requests=20, window=60)  # 20 requests per minute
async def generate_text(
    request: TextGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate text using OpenAI GPT"""

    model = request.model or "gpt-4"

    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for content generation."},
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        generated_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        # Rough cost estimation (GPT-4: $0.03/1K tokens, GPT-3.5: $0.002/1K tokens)
        cost_per_1k = 0.03 if "gpt-4" in model else 0.002
        cost = (tokens_used / 1000) * cost_per_1k

        # Save to database
        gen_job = GenJob(
            user_id=current_user.id,
            model=model,
            type="text",
            prompt=request.prompt,
            response=generated_text,
            tokens=tokens_used,
            cost=cost
        )

        db.add(gen_job)
        db.commit()
        db.refresh(gen_job)

        logger.info(f"Text generation completed for user {current_user.id}, tokens: {tokens_used}")

        return gen_job

    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/image")
@rate_limit(max_requests=10, window=60)  # 10 requests per minute
async def generate_image(
    request: ImageGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate image using OpenAI DALL-E"""

    try:
        # Call OpenAI DALL-E API
        response = openai.Image.create(
            prompt=request.prompt,
            n=request.n,
            size=request.size
        )

        image_url = response.data[0].url

        # Rough cost estimation for DALL-E (varies by size)
        cost = 0.02 if request.size == "1024x1024" else 0.018 if request.size == "512x512" else 0.016

        # Save to database
        gen_job = GenJob(
            user_id=current_user.id,
            model="dall-e",
            type="image",
            prompt=request.prompt,
            response=image_url,
            tokens=None,  # DALL-E doesn't use tokens
            cost=cost * request.n
        )

        db.add(gen_job)
        db.commit()
        db.refresh(gen_job)

        logger.info(f"Image generation completed for user {current_user.id}")

        return {
            "id": gen_job.id,
            "type": "image",
            "prompt": request.prompt,
            "image_url": image_url,
            "cost": cost * request.n
        }

    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/history")
async def get_generation_history(
    skip: int = 0,
    limit: int = 50,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get generation history for the current user"""

    query = db.query(GenJob).filter(GenJob.user_id == current_user.id)

    if type:
        query = query.filter(GenJob.type == type)

    jobs = query.order_by(GenJob.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    return {
        "total": len(jobs),
        "jobs": jobs
    }

@router.get("/stats")
async def get_generation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get generation statistics for the current user"""

    from sqlalchemy import func

    stats = db.query(
        func.count(GenJob.id).label("total_jobs"),
        func.sum(GenJob.tokens).label("total_tokens"),
        func.sum(GenJob.cost).label("total_cost")
    ).filter(GenJob.user_id == current_user.id).first()

    return {
        "total_generations": stats.total_jobs or 0,
        "total_tokens": stats.total_tokens or 0,
        "total_cost": float(stats.total_cost or 0)
    }
