"""
Template Management API
Prompt templates, creative templates, and channel presets
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from database import (
    get_db,
    PromptTemplate,
    CreativeTemplate,
    ChannelPreset,
    Segment
)
from logger import get_logger

logger = get_logger("templates_api")
router = APIRouter(prefix="/templates", tags=["templates"])


# ==========================================
# Pydantic Models - Prompt Templates
# ==========================================

class PromptTemplateCreate(BaseModel):
    """Create prompt template"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    template: str = Field(..., description="Template with {variables}")
    category: Optional[str] = None
    language: str = Field(default="en", max_length=10)
    variables: Optional[List[str]] = None
    is_public: bool = True


class PromptTemplateResponse(BaseModel):
    """Prompt template response"""
    id: int
    name: str
    description: Optional[str]
    template: str
    category: Optional[str]
    language: str
    variables: Optional[List[str]]
    is_public: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptTemplateApply(BaseModel):
    """Apply prompt template with variables"""
    template_id: int
    variables: Dict[str, str]
    segment_id: Optional[int] = None  # Auto-inject segment data


# ==========================================
# Pydantic Models - Creative Templates
# ==========================================

class CreativeTemplateCreate(BaseModel):
    """Create creative template"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    layout_config: Dict[str, Any] = Field(..., description="Layout configuration")
    font_family: Optional[str] = None
    font_sizes: Optional[Dict[str, int]] = None
    color_palette: Dict[str, str] = Field(..., description="Color palette")
    channel: Optional[str] = None
    size: Optional[str] = None
    is_public: bool = True


class CreativeTemplateResponse(BaseModel):
    """Creative template response"""
    id: int
    name: str
    description: Optional[str]
    preview_url: Optional[str]
    category: Optional[str]
    layout_config: Dict[str, Any]
    font_family: Optional[str]
    font_sizes: Optional[Dict[str, int]]
    color_palette: Dict[str, str]
    channel: Optional[str]
    size: Optional[str]
    is_public: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Pydantic Models - Channel Presets
# ==========================================

class ChannelPresetCreate(BaseModel):
    """Create channel preset"""
    name: str = Field(..., max_length=255)
    channel: str = Field(..., max_length=50)
    type: str = Field(..., max_length=50)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    aspect_ratio: str = Field(..., max_length=20)
    recommended_text_length: Optional[int] = None
    recommended_hashtags: Optional[int] = None
    best_practices: Optional[List[str]] = None


class ChannelPresetResponse(BaseModel):
    """Channel preset response"""
    id: int
    name: str
    channel: str
    type: str
    width: int
    height: int
    aspect_ratio: str
    recommended_text_length: Optional[int]
    recommended_hashtags: Optional[int]
    best_practices: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Prompt Template Endpoints
# ==========================================

@router.post("/prompts", response_model=PromptTemplateResponse)
async def create_prompt_template(
    template: PromptTemplateCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Create prompt template with {variables}

    Example template: "Create a {tone} social media post about {topic} for {audience}"
    """
    new_template = PromptTemplate(
        name=template.name,
        description=template.description,
        template=template.template,
        category=template.category,
        language=template.language,
        variables=template.variables,
        is_public=template.is_public,
        user_id=user_id
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    logger.info(f"Prompt template created: {new_template.id} - {new_template.name}")
    return new_template


@router.get("/prompts", response_model=List[PromptTemplateResponse])
async def list_prompt_templates(
    category: Optional[str] = None,
    language: Optional[str] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List prompt templates with filters"""
    query = db.query(PromptTemplate)

    if category:
        query = query.filter(PromptTemplate.category == category)
    if language:
        query = query.filter(PromptTemplate.language == language)
    if is_public is not None:
        query = query.filter(PromptTemplate.is_public == is_public)

    templates = query.order_by(PromptTemplate.usage_count.desc()).offset(skip).limit(limit).all()
    return templates


@router.get("/prompts/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(template_id: int, db: Session = Depends(get_db)):
    """Get prompt template by ID"""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.post("/prompts/apply")
async def apply_prompt_template(
    request: PromptTemplateApply,
    db: Session = Depends(get_db)
):
    """
    Apply prompt template with variable substitution

    Optionally inject segment data (tone, keywords) automatically
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == request.template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Start with template
    result = template.template

    # If segment_id provided, inject segment data
    if request.segment_id:
        segment = db.query(Segment).filter(Segment.id == request.segment_id).first()
        if segment:
            # Auto-inject segment variables
            if segment.tone and "{tone}" in result:
                result = result.replace("{tone}", segment.tone)
            if segment.keywords and "{keywords}" in result:
                result = result.replace("{keywords}", segment.keywords)

            logger.info(f"Injected segment {segment.id} data into template {template.id}")

    # Apply user-provided variables
    for key, value in request.variables.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, value)

    # Increment usage count
    template.usage_count += 1
    db.commit()

    return {
        "template_id": template.id,
        "original_template": template.template,
        "applied_prompt": result,
        "variables_used": request.variables
    }


# ==========================================
# Creative Template Endpoints
# ==========================================

@router.post("/creatives", response_model=CreativeTemplateResponse)
async def create_creative_template(
    template: CreativeTemplateCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Create creative template (layout/font/palette)

    Layout config example:
    {
        "text_slots": [
            {"id": "heading", "x": 50, "y": 50, "width": 400, "height": 100},
            {"id": "body", "x": 50, "y": 200, "width": 400, "height": 200}
        ],
        "image_slots": [
            {"id": "main_image", "x": 500, "y": 50, "width": 500, "height": 500}
        ],
        "dimensions": {"width": 1080, "height": 1080}
    }
    """
    new_template = CreativeTemplate(
        name=template.name,
        description=template.description,
        category=template.category,
        layout_config=template.layout_config,
        font_family=template.font_family,
        font_sizes=template.font_sizes,
        color_palette=template.color_palette,
        channel=template.channel,
        size=template.size,
        is_public=template.is_public,
        user_id=user_id
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    logger.info(f"Creative template created: {new_template.id} - {new_template.name}")
    return new_template


@router.get("/creatives", response_model=List[CreativeTemplateResponse])
async def list_creative_templates(
    category: Optional[str] = None,
    channel: Optional[str] = None,
    size: Optional[str] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List creative templates (gallery view)"""
    query = db.query(CreativeTemplate)

    if category:
        query = query.filter(CreativeTemplate.category == category)
    if channel:
        query = query.filter(CreativeTemplate.channel == channel)
    if size:
        query = query.filter(CreativeTemplate.size == size)
    if is_public is not None:
        query = query.filter(CreativeTemplate.is_public == is_public)

    templates = query.order_by(CreativeTemplate.usage_count.desc()).offset(skip).limit(limit).all()
    return templates


@router.get("/creatives/{template_id}", response_model=CreativeTemplateResponse)
async def get_creative_template(template_id: int, db: Session = Depends(get_db)):
    """Get creative template by ID"""
    template = db.query(CreativeTemplate).filter(CreativeTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


# ==========================================
# Channel Preset Endpoints
# ==========================================

@router.post("/presets", response_model=ChannelPresetResponse)
async def create_channel_preset(
    preset: ChannelPresetCreate,
    db: Session = Depends(get_db)
):
    """Create channel preset with size and best practices"""
    new_preset = ChannelPreset(
        name=preset.name,
        channel=preset.channel,
        type=preset.type,
        width=preset.width,
        height=preset.height,
        aspect_ratio=preset.aspect_ratio,
        recommended_text_length=preset.recommended_text_length,
        recommended_hashtags=preset.recommended_hashtags,
        best_practices=preset.best_practices
    )

    db.add(new_preset)
    db.commit()
    db.refresh(new_preset)

    logger.info(f"Channel preset created: {new_preset.id} - {new_preset.name}")
    return new_preset


@router.get("/presets", response_model=List[ChannelPresetResponse])
async def list_channel_presets(
    channel: Optional[str] = None,
    type: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """List channel presets with filters"""
    query = db.query(ChannelPreset)

    if channel:
        query = query.filter(ChannelPreset.channel == channel)
    if type:
        query = query.filter(ChannelPreset.type == type)
    if aspect_ratio:
        query = query.filter(ChannelPreset.aspect_ratio == aspect_ratio)
    if is_active is not None:
        query = query.filter(ChannelPreset.is_active == is_active)

    presets = query.order_by(ChannelPreset.channel, ChannelPreset.type).all()
    return presets


@router.get("/presets/{preset_id}", response_model=ChannelPresetResponse)
async def get_channel_preset(preset_id: int, db: Session = Depends(get_db)):
    """Get channel preset by ID"""
    preset = db.query(ChannelPreset).filter(ChannelPreset.id == preset_id).first()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    return preset


@router.get("/presets/recommend/{channel}")
async def recommend_preset(
    channel: str,
    content_type: str = Query("feed", description="feed, story, reel, post, etc."),
    db: Session = Depends(get_db)
):
    """Get recommended preset for channel and content type"""
    preset = db.query(ChannelPreset).filter(
        ChannelPreset.channel == channel,
        ChannelPreset.type == content_type,
        ChannelPreset.is_active == True
    ).first()

    if not preset:
        # Return default preset
        return {
            "channel": channel,
            "type": content_type,
            "width": 1080,
            "height": 1080,
            "aspect_ratio": "1:1",
            "recommended_text_length": 2200,
            "best_practices": ["Use high-quality images", "Keep text concise", "Include call-to-action"]
        }

    return preset
