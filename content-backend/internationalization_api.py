"""
Internationalization and Social Media Integration API
Multi-language support and SNS sharing/download functionality
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

from database import get_db, Creative, Campaign
from openai_client import generate_text
from logger import get_logger

logger = get_logger("i18n_api")
router = APIRouter(prefix="/i18n", tags=["internationalization"])


# ==========================================
# Language Configuration
# ==========================================

SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "code": "en",
        "prompt_suffix": "Generate content in English.",
        "char_limit_multiplier": 1.0,
        "best_practices": [
            "Keep sentences concise and punchy",
            "Use active voice",
            "Avoid jargon unless technical audience"
        ]
    },
    "ko": {
        "name": "한국어 (Korean)",
        "code": "ko",
        "prompt_suffix": "Generate content in Korean (한국어).",
        "char_limit_multiplier": 0.7,  # Korean characters are more information-dense
        "best_practices": [
            "Use appropriate honorifics (존댓말/반말)",
            "Keep spacing consistent (띄어쓰기)",
            "Avoid excessive English words"
        ]
    },
    "ja": {
        "name": "日本語 (Japanese)",
        "code": "ja",
        "prompt_suffix": "Generate content in Japanese (日本語).",
        "char_limit_multiplier": 0.7,
        "best_practices": [
            "Use appropriate politeness levels (敬語)",
            "Mix hiragana/katakana/kanji appropriately",
            "Keep sentences natural"
        ]
    },
    "es": {
        "name": "Español (Spanish)",
        "code": "es",
        "prompt_suffix": "Generate content in Spanish (Español).",
        "char_limit_multiplier": 1.1,
        "best_practices": [
            "Use formal/informal appropriately (tú/usted)",
            "Keep accent marks correct",
            "Adapt to regional variations if specified"
        ]
    },
    "zh": {
        "name": "中文 (Chinese)",
        "code": "zh",
        "prompt_suffix": "Generate content in Simplified Chinese (简体中文).",
        "char_limit_multiplier": 0.6,
        "best_practices": [
            "Use simplified or traditional as specified",
            "Keep tone appropriate for context",
            "Avoid complex classical phrases unless formal"
        ]
    }
}


# ==========================================
# Pydantic Models
# ==========================================

class TranslateRequest(BaseModel):
    """Translate content to target language"""
    creative_id: int
    target_language: str = Field(..., pattern="^(en|ko|ja|es|zh)$")
    preserve_tone: bool = True


class TranslateResponse(BaseModel):
    """Translation response"""
    creative_id: int
    original_language: str
    target_language: str
    original_text: str
    translated_text: str


class LocalizeRequest(BaseModel):
    """Localize content for target market"""
    prompt: str
    language: str = Field(..., pattern="^(en|ko|ja|es|zh)$")
    tone: Optional[str] = None
    region: Optional[str] = None  # 'us', 'uk', 'kr', 'jp', etc.


class ShareLinkRequest(BaseModel):
    """Generate shareable link"""
    creative_id: int
    platform: str = Field(..., pattern="^(facebook|twitter|instagram|linkedin|email|sms)$")
    include_preview: bool = True


class ShareLinkResponse(BaseModel):
    """Shareable link response"""
    creative_id: int
    platform: str
    share_url: str
    share_token: str
    preview_data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class DownloadLinkRequest(BaseModel):
    """Generate download link"""
    creative_id: int
    format: str = Field(default="original", pattern="^(original|png|jpg|pdf)$")
    quality: Optional[int] = Field(default=95, ge=1, le=100)


# ==========================================
# Multi-Language Endpoints
# ==========================================

@router.get("/languages")
async def list_supported_languages():
    """List all supported languages with best practices"""
    return {
        "languages": SUPPORTED_LANGUAGES,
        "total": len(SUPPORTED_LANGUAGES)
    }


@router.get("/languages/{language_code}")
async def get_language_info(language_code: str):
    """Get language-specific information and best practices"""
    if language_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")

    return SUPPORTED_LANGUAGES[language_code]


@router.post("/translate", response_model=TranslateResponse)
async def translate_creative(
    request: TranslateRequest,
    db: Session = Depends(get_db)
):
    """
    Translate creative content to target language

    Preserves tone and style while adapting to target language conventions
    """
    # Get creative
    creative = db.query(Creative).filter(Creative.id == request.creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    if not creative.content_text:
        raise HTTPException(status_code=400, detail="Creative has no text content")

    # Check target language
    if request.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Target language not supported")

    target_lang = SUPPORTED_LANGUAGES[request.target_language]

    # Build translation prompt
    translation_prompt = f"""Translate the following marketing content to {target_lang['name']}.

Original text: {creative.content_text}

Requirements:
- Translate to {target_lang['name']}
- Preserve marketing tone and intent
- Adapt cultural references if needed
- Keep the message concise and impactful
{"- Preserve the original tone and style" if request.preserve_tone else "- Adapt tone for target audience"}

Translation:"""

    # Generate translation
    translated_text = await generate_text(translation_prompt, max_tokens=500)

    logger.info(f"Translated creative {creative.id} to {request.target_language}")

    return TranslateResponse(
        creative_id=creative.id,
        original_language="en",  # TODO: Detect original language
        target_language=request.target_language,
        original_text=creative.content_text,
        translated_text=translated_text
    )


@router.post("/localize")
async def localize_content(request: LocalizeRequest):
    """
    Generate localized content from scratch

    Takes prompt and generates content optimized for target language/region
    """
    if request.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Language not supported")

    lang_config = SUPPORTED_LANGUAGES[request.language]

    # Build localized prompt
    localized_prompt = request.prompt

    # Add language instruction
    localized_prompt += f"\n\n{lang_config['prompt_suffix']}"

    # Add tone if specified
    if request.tone:
        localized_prompt += f"\nTone: {request.tone}"

    # Add region-specific instructions
    if request.region:
        localized_prompt += f"\nTarget region: {request.region}"

    # Add best practices
    localized_prompt += f"\n\nBest practices:\n" + "\n".join(f"- {bp}" for bp in lang_config["best_practices"])

    # Calculate character limit based on language
    base_char_limit = 500
    adjusted_limit = int(base_char_limit * lang_config["char_limit_multiplier"])

    # Generate content
    content = await generate_text(localized_prompt, max_tokens=adjusted_limit)

    logger.info(f"Generated localized content in {request.language}")

    return {
        "language": request.language,
        "language_name": lang_config["name"],
        "content": content,
        "char_count": len(content),
        "char_limit": adjusted_limit,
        "best_practices": lang_config["best_practices"]
    }


# ==========================================
# Social Media Integration Endpoints
# ==========================================

# In-memory store for share tokens (use Redis in production)
share_tokens = {}


@router.post("/share", response_model=ShareLinkResponse)
async def create_share_link(
    request: ShareLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Generate shareable link for social media platforms

    Creates platform-specific share URL with preview metadata
    """
    # Get creative
    creative = db.query(Creative).filter(Creative.id == request.creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # Get campaign
    campaign = db.query(Campaign).filter(Campaign.id == creative.campaign_id).first()

    # Generate share token
    share_token = secrets.token_urlsafe(16)

    # Store token mapping
    share_tokens[share_token] = {
        "creative_id": creative.id,
        "platform": request.platform,
        "created_at": datetime.utcnow()
    }

    # Build platform-specific share URL
    base_url = f"https://artify.app/share/{share_token}"

    platform_urls = {
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={base_url}",
        "twitter": f"https://twitter.com/intent/tweet?url={base_url}&text={creative.name}",
        "instagram": base_url,  # Instagram doesn't support direct sharing
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={base_url}",
        "email": f"mailto:?subject={creative.name}&body=Check out this creative: {base_url}",
        "sms": f"sms:?body=Check out this creative: {base_url}"
    }

    share_url = platform_urls.get(request.platform, base_url)

    # Build preview data
    preview_data = None
    if request.include_preview:
        preview_data = {
            "title": creative.name,
            "description": creative.content_text[:200] if creative.content_text else campaign.description,
            "image_url": creative.thumbnail_url or creative.asset_url,
            "campaign_name": campaign.name if campaign else None
        }

    logger.info(f"Created share link for creative {creative.id} on {request.platform}")

    return ShareLinkResponse(
        creative_id=creative.id,
        platform=request.platform,
        share_url=share_url,
        share_token=share_token,
        preview_data=preview_data
    )


@router.get("/share/{share_token}")
async def resolve_share_link(share_token: str, db: Session = Depends(get_db)):
    """
    Resolve share token to creative

    Used for landing page when user clicks share link
    """
    if share_token not in share_tokens:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    token_data = share_tokens[share_token]
    creative_id = token_data["creative_id"]

    # Get creative
    creative = db.query(Creative).filter(Creative.id == creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # Get campaign
    campaign = db.query(Campaign).filter(Campaign.id == creative.campaign_id).first()

    return {
        "creative_id": creative.id,
        "name": creative.name,
        "content_text": creative.content_text,
        "asset_url": creative.asset_url,
        "thumbnail_url": creative.thumbnail_url,
        "campaign_name": campaign.name if campaign else None,
        "shared_platform": token_data["platform"],
        "created_at": token_data["created_at"]
    }


@router.post("/download")
async def create_download_link(
    request: DownloadLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Generate download link for creative asset

    Supports format conversion and quality adjustment
    """
    # Get creative
    creative = db.query(Creative).filter(Creative.id == request.creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    if not creative.asset_url:
        raise HTTPException(status_code=400, detail="Creative has no asset to download")

    # Generate download token
    download_token = secrets.token_urlsafe(16)

    # Store token mapping (use Redis in production)
    share_tokens[download_token] = {
        "creative_id": creative.id,
        "format": request.format,
        "quality": request.quality,
        "created_at": datetime.utcnow(),
        "type": "download"
    }

    download_url = f"https://artify.app/api/i18n/download/{download_token}"

    logger.info(f"Created download link for creative {creative.id}, format: {request.format}")

    return {
        "creative_id": creative.id,
        "download_url": download_url,
        "download_token": download_token,
        "format": request.format,
        "original_url": creative.asset_url,
        "expires_in": 3600  # 1 hour
    }


@router.get("/download/{download_token}")
async def download_creative(download_token: str, db: Session = Depends(get_db)):
    """
    Download creative asset

    TODO: Implement format conversion and streaming
    """
    if download_token not in share_tokens:
        raise HTTPException(status_code=404, detail="Invalid or expired download link")

    token_data = share_tokens[download_token]

    if token_data.get("type") != "download":
        raise HTTPException(status_code=400, detail="Invalid download token")

    creative_id = token_data["creative_id"]

    # Get creative
    creative = db.query(Creative).filter(Creative.id == creative_id).first()
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # TODO: Implement actual file streaming and format conversion
    # For now, return redirect to original asset URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=creative.asset_url, status_code=302)


@router.get("/platforms")
async def list_social_platforms():
    """List supported social media platforms and their capabilities"""
    platforms = {
        "facebook": {
            "name": "Facebook",
            "supports_share": True,
            "supports_scheduled_post": False,
            "recommended_sizes": ["1200x630", "1080x1080"],
            "aspect_ratios": ["1.91:1", "1:1"],
            "char_limit": 63206,
            "best_practices": [
                "Use eye-catching images",
                "Keep text concise in first 2 lines",
                "Include call-to-action"
            ]
        },
        "instagram": {
            "name": "Instagram",
            "supports_share": False,  # Manual sharing only
            "supports_scheduled_post": False,
            "recommended_sizes": ["1080x1080", "1080x1350", "1080x1920"],
            "aspect_ratios": ["1:1", "4:5", "9:16"],
            "char_limit": 2200,
            "best_practices": [
                "Use high-quality images",
                "Include relevant hashtags (5-10)",
                "Post at optimal times"
            ]
        },
        "twitter": {
            "name": "Twitter/X",
            "supports_share": True,
            "supports_scheduled_post": False,
            "recommended_sizes": ["1200x675", "1080x1080"],
            "aspect_ratios": ["16:9", "1:1"],
            "char_limit": 280,
            "best_practices": [
                "Keep under 280 characters",
                "Use 1-2 hashtags max",
                "Include media for engagement"
            ]
        },
        "linkedin": {
            "name": "LinkedIn",
            "supports_share": True,
            "supports_scheduled_post": False,
            "recommended_sizes": ["1200x627", "1080x1080"],
            "aspect_ratios": ["1.91:1", "1:1"],
            "char_limit": 3000,
            "best_practices": [
                "Professional tone",
                "Value-driven content",
                "Engage with comments"
            ]
        }
    }

    return {
        "platforms": platforms,
        "total": len(platforms)
    }
