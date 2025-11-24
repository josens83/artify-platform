"""
Seed database with pre-built creative templates
Run this script to populate the templates library with starter templates
"""
import sys
import os
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, CreativeTemplate, ChannelPreset
from logger import get_logger

logger = get_logger("seed_templates")


def seed_creative_templates(db: Session):
    """Create pre-built creative templates"""

    templates = [
        # Social Media Templates
        {
            "name": "Instagram Post - Minimal",
            "description": "미니멀한 디자인의 인스타그램 포스트 템플릿",
            "category": "minimal",
            "channel": "social",
            "size": "1080x1080",
            "font_family": "Arial",
            "font_sizes": {"heading": 48, "body": 24},
            "color_palette": {
                "primary": "#2c3e50",
                "secondary": "#ecf0f1",
                "accent": "#3498db",
                "background": "#ffffff"
            },
            "layout_config": {
                "dimensions": {"width": 1080, "height": 1080},
                "background": "#ffffff",
                "text_slots": [
                    {
                        "id": "heading",
                        "x": 100,
                        "y": 400,
                        "width": 880,
                        "height": 100,
                        "text": "Your Heading Here",
                        "align": "center"
                    },
                    {
                        "id": "body",
                        "x": 100,
                        "y": 550,
                        "width": 880,
                        "height": 60,
                        "text": "Supporting text goes here",
                        "align": "center"
                    }
                ],
                "image_slots": [
                    {
                        "id": "main_image",
                        "x": 290,
                        "y": 100,
                        "width": 500,
                        "height": 250
                    }
                ]
            }
        },
        {
            "name": "Instagram Story - Bold",
            "description": "강렬한 색상의 인스타그램 스토리 템플릿",
            "category": "bold",
            "channel": "social",
            "size": "1080x1920",
            "font_family": "Impact",
            "font_sizes": {"heading": 72, "body": 36},
            "color_palette": {
                "primary": "#ffffff",
                "secondary": "#ff6b6b",
                "accent": "#ffd93d",
                "background": "#6c5ce7"
            },
            "layout_config": {
                "dimensions": {"width": 1080, "height": 1920},
                "background": "#6c5ce7",
                "text_slots": [
                    {
                        "id": "heading",
                        "x": 80,
                        "y": 800,
                        "width": 920,
                        "height": 150,
                        "text": "AMAZING OFFER",
                        "align": "center"
                    },
                    {
                        "id": "body",
                        "x": 80,
                        "y": 1000,
                        "width": 920,
                        "height": 80,
                        "text": "Swipe up to learn more!",
                        "align": "center"
                    }
                ],
                "image_slots": [
                    {
                        "id": "product",
                        "x": 290,
                        "y": 300,
                        "width": 500,
                        "height": 500
                    }
                ]
            }
        },
        # Banner Templates
        {
            "name": "Web Banner - Product Launch",
            "description": "제품 런칭용 웹 배너",
            "category": "banner",
            "channel": "display",
            "size": "1200x630",
            "font_family": "Helvetica",
            "font_sizes": {"heading": 56, "body": 28, "cta": 32},
            "color_palette": {
                "primary": "#1a1a2e",
                "secondary": "#16213e",
                "accent": "#0f3460",
                "background": "#e94560"
            },
            "layout_config": {
                "dimensions": {"width": 1200, "height": 630},
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "text_slots": [
                    {
                        "id": "heading",
                        "x": 600,
                        "y": 150,
                        "width": 550,
                        "height": 120,
                        "text": "New Product Launch",
                        "align": "left"
                    },
                    {
                        "id": "body",
                        "x": 600,
                        "y": 280,
                        "width": 550,
                        "height": 70,
                        "text": "Get 30% off for early birds",
                        "align": "left"
                    },
                    {
                        "id": "cta",
                        "x": 600,
                        "y": 400,
                        "width": 200,
                        "height": 70,
                        "text": "Shop Now",
                        "align": "center"
                    }
                ],
                "image_slots": [
                    {
                        "id": "product_image",
                        "x": 50,
                        "y": 115,
                        "width": 450,
                        "height": 400
                    }
                ]
            }
        },
        # Poster Templates
        {
            "name": "Event Poster - Elegant",
            "description": "우아한 이벤트 포스터 템플릿",
            "category": "elegant",
            "channel": "poster",
            "size": "1080x1350",
            "font_family": "Georgia",
            "font_sizes": {"heading": 64, "subheading": 36, "body": 24},
            "color_palette": {
                "primary": "#2d3436",
                "secondary": "#636e72",
                "accent": "#fdcb6e",
                "background": "#ffeaa7"
            },
            "layout_config": {
                "dimensions": {"width": 1080, "height": 1350},
                "background": "#ffeaa7",
                "text_slots": [
                    {
                        "id": "heading",
                        "x": 100,
                        "y": 900,
                        "width": 880,
                        "height": 130,
                        "text": "ANNUAL GALA EVENT",
                        "align": "center"
                    },
                    {
                        "id": "subheading",
                        "x": 100,
                        "y": 1050,
                        "width": 880,
                        "height": 70,
                        "text": "Join us for an unforgettable evening",
                        "align": "center"
                    },
                    {
                        "id": "date",
                        "x": 100,
                        "y": 1150,
                        "width": 880,
                        "height": 50,
                        "text": "December 15, 2025 • 7:00 PM",
                        "align": "center"
                    }
                ],
                "image_slots": [
                    {
                        "id": "hero_image",
                        "x": 140,
                        "y": 100,
                        "width": 800,
                        "height": 700
                    }
                ]
            }
        },
        # Presentation Templates
        {
            "name": "Presentation Slide - Modern",
            "description": "현대적인 프레젠테이션 슬라이드",
            "category": "presentation",
            "channel": "presentation",
            "size": "1920x1080",
            "font_family": "Roboto",
            "font_sizes": {"heading": 72, "body": 32},
            "color_palette": {
                "primary": "#2c3e50",
                "secondary": "#34495e",
                "accent": "#e74c3c",
                "background": "#ecf0f1"
            },
            "layout_config": {
                "dimensions": {"width": 1920, "height": 1080},
                "background": "#ecf0f1",
                "text_slots": [
                    {
                        "id": "heading",
                        "x": 100,
                        "y": 150,
                        "width": 1200,
                        "height": 150,
                        "text": "Slide Title",
                        "align": "left"
                    },
                    {
                        "id": "bullet1",
                        "x": 100,
                        "y": 350,
                        "width": 1200,
                        "height": 80,
                        "text": "• First key point",
                        "align": "left"
                    },
                    {
                        "id": "bullet2",
                        "x": 100,
                        "y": 450,
                        "width": 1200,
                        "height": 80,
                        "text": "• Second key point",
                        "align": "left"
                    },
                    {
                        "id": "bullet3",
                        "x": 100,
                        "y": 550,
                        "width": 1200,
                        "height": 80,
                        "text": "• Third key point",
                        "align": "left"
                    }
                ],
                "image_slots": [
                    {
                        "id": "visual",
                        "x": 1350,
                        "y": 200,
                        "width": 470,
                        "height": 700
                    }
                ]
            }
        },
        # Additional Social Media Templates
        {
            "name": "Facebook Cover - Brand",
            "description": "브랜드 페이스북 커버 이미지",
            "category": "social",
            "channel": "social",
            "size": "820x312",
            "font_family": "Arial",
            "font_sizes": {"heading": 48, "tagline": 20},
            "color_palette": {
                "primary": "#ffffff",
                "secondary": "#4267B2",
                "accent": "#898f9c",
                "background": "#4267B2"
            },
            "layout_config": {
                "dimensions": {"width": 820, "height": 312},
                "background": "#4267B2",
                "text_slots": [
                    {
                        "id": "brand",
                        "x": 50,
                        "y": 80,
                        "width": 400,
                        "height": 80,
                        "text": "Your Brand",
                        "align": "left"
                    },
                    {
                        "id": "tagline",
                        "x": 50,
                        "y": 180,
                        "width": 400,
                        "height": 40,
                        "text": "Your tagline goes here",
                        "align": "left"
                    }
                ],
                "image_slots": [
                    {
                        "id": "logo",
                        "x": 550,
                        "y": 56,
                        "width": 200,
                        "height": 200
                    }
                ]
            }
        },
        {
            "name": "LinkedIn Post - Professional",
            "description": "전문적인 링크드인 포스트",
            "category": "minimal",
            "channel": "social",
            "size": "1200x627",
            "font_family": "Segoe UI",
            "font_sizes": {"heading": 42, "body": 24},
            "color_palette": {
                "primary": "#0a66c2",
                "secondary": "#313335",
                "accent": "#70b5f9",
                "background": "#ffffff"
            },
            "layout_config": {
                "dimensions": {"width": 1200, "height": 627},
                "background": "#ffffff",
                "text_slots": [
                    {
                        "id": "heading",
                        "x": 80,
                        "y": 200,
                        "width": 1040,
                        "height": 90,
                        "text": "Professional Insight",
                        "align": "left"
                    },
                    {
                        "id": "body",
                        "x": 80,
                        "y": 320,
                        "width": 1040,
                        "height": 60,
                        "text": "Share your expertise with the world",
                        "align": "left"
                    }
                ],
                "image_slots": [
                    {
                        "id": "accent_bar",
                        "x": 0,
                        "y": 0,
                        "width": 20,
                        "height": 627
                    }
                ]
            }
        }
    ]

    created_count = 0

    for template_data in templates:
        # Check if template already exists
        existing = db.query(CreativeTemplate).filter(
            CreativeTemplate.name == template_data["name"]
        ).first()

        if existing:
            logger.info(f"Template '{template_data['name']}' already exists, skipping...")
            continue

        # Create new template
        template = CreativeTemplate(**template_data)
        db.add(template)
        created_count += 1

    db.commit()
    logger.info(f"✅ Created {created_count} new creative templates")
    return created_count


def seed_channel_presets(db: Session):
    """Create channel presets for social media platforms"""

    presets = [
        # Instagram
        {
            "name": "Instagram Feed Post",
            "channel": "instagram",
            "type": "feed",
            "width": 1080,
            "height": 1080,
            "aspect_ratio": "1:1",
            "recommended_text_length": 2200,
            "recommended_hashtags": 11,
            "best_practices": [
                "Use high-quality images",
                "Include engaging captions",
                "Use 9-11 relevant hashtags",
                "Post during peak hours (11am-1pm, 7pm-9pm)"
            ]
        },
        {
            "name": "Instagram Story",
            "channel": "instagram",
            "type": "story",
            "width": 1080,
            "height": 1920,
            "aspect_ratio": "9:16",
            "recommended_text_length": 200,
            "recommended_hashtags": 3,
            "best_practices": [
                "Keep text concise and readable",
                "Use interactive stickers (polls, questions)",
                "Add location tags for visibility",
                "Use vertical video format"
            ]
        },
        {
            "name": "Instagram Reel",
            "channel": "instagram",
            "type": "reel",
            "width": 1080,
            "height": 1920,
            "aspect_ratio": "9:16",
            "recommended_text_length": 2200,
            "recommended_hashtags": 5,
            "best_practices": [
                "15-30 seconds for best engagement",
                "Use trending audio",
                "Hook viewers in first 3 seconds",
                "Add captions for accessibility"
            ]
        },
        # Facebook
        {
            "name": "Facebook Post",
            "channel": "facebook",
            "type": "post",
            "width": 1200,
            "height": 630,
            "aspect_ratio": "1.91:1",
            "recommended_text_length": 250,
            "recommended_hashtags": 3,
            "best_practices": [
                "Keep text overlay minimal",
                "Use eye-catching visuals",
                "Include clear call-to-action",
                "Optimal posting time: 1pm-3pm weekdays"
            ]
        },
        {
            "name": "Facebook Cover",
            "channel": "facebook",
            "type": "cover",
            "width": 820,
            "height": 312,
            "aspect_ratio": "2.63:1",
            "recommended_text_length": 100,
            "recommended_hashtags": 0,
            "best_practices": [
                "Keep important content in center",
                "Avoid text in bottom left (profile pic area)",
                "Use brand colors",
                "Update seasonally"
            ]
        },
        # Twitter/X
        {
            "name": "Twitter Post",
            "channel": "twitter",
            "type": "post",
            "width": 1200,
            "height": 675,
            "aspect_ratio": "16:9",
            "recommended_text_length": 280,
            "recommended_hashtags": 2,
            "best_practices": [
                "Use 1-2 relevant hashtags",
                "Engage with trending topics",
                "Include compelling visuals",
                "Post during peak hours"
            ]
        },
        # LinkedIn
        {
            "name": "LinkedIn Post",
            "channel": "linkedin",
            "type": "post",
            "width": 1200,
            "height": 627,
            "aspect_ratio": "1.91:1",
            "recommended_text_length": 1300,
            "recommended_hashtags": 5,
            "best_practices": [
                "Professional tone",
                "Share insights and expertise",
                "Use data and statistics",
                "Engage in comments"
            ]
        },
        {
            "name": "LinkedIn Banner",
            "channel": "linkedin",
            "type": "banner",
            "width": 1584,
            "height": 396,
            "aspect_ratio": "4:1",
            "recommended_text_length": 50,
            "recommended_hashtags": 0,
            "best_practices": [
                "Showcase your expertise",
                "Keep it professional",
                "Update regularly",
                "Align with personal brand"
            ]
        },
        # YouTube
        {
            "name": "YouTube Thumbnail",
            "channel": "youtube",
            "type": "thumbnail",
            "width": 1280,
            "height": 720,
            "aspect_ratio": "16:9",
            "recommended_text_length": 50,
            "recommended_hashtags": 0,
            "best_practices": [
                "Use bold, readable text",
                "Include faces with emotions",
                "High contrast colors",
                "Consistent branding"
            ]
        },
        {
            "name": "YouTube Banner",
            "channel": "youtube",
            "type": "banner",
            "width": 2560,
            "height": 1440,
            "aspect_ratio": "16:9",
            "recommended_text_length": 100,
            "recommended_hashtags": 0,
            "best_practices": [
                "Safe area: 1546x423 center",
                "Upload schedule in design",
                "Social media links",
                "Mobile-friendly design"
            ]
        }
    ]

    created_count = 0

    for preset_data in presets:
        # Check if preset already exists
        existing = db.query(ChannelPreset).filter(
            ChannelPreset.name == preset_data["name"]
        ).first()

        if existing:
            logger.info(f"Preset '{preset_data['name']}' already exists, skipping...")
            continue

        # Create new preset
        preset = ChannelPreset(**preset_data)
        db.add(preset)
        created_count += 1

    db.commit()
    logger.info(f"✅ Created {created_count} new channel presets")
    return created_count


def main():
    """Run seed script"""
    logger.info("🌱 Starting template seeding...")

    db = SessionLocal()
    try:
        template_count = seed_creative_templates(db)
        preset_count = seed_channel_presets(db)

        logger.info(f"""
✅ Seeding completed successfully!
   - Creative Templates: {template_count} created
   - Channel Presets: {preset_count} created
        """)

    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
