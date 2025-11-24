"""
AI Router - Intelligent Model Selection
Automatically selects the best AI model based on prompt characteristics
"""
from typing import Optional, Dict
import re
from logger import get_logger

logger = get_logger("ai_router")


class AIRouter:
    """
    Smart router that analyzes prompts and selects optimal AI model

    Selection Criteria:
    - Short copy (< 100 chars) → GPT-3.5 Turbo (fast & cheap)
    - Brand/Professional content → Gemini Pro (rich context)
    - Long content (> 500 chars) → GPT-4 Turbo (complex understanding)
    - Creative/Marketing → GPT-3.5 Turbo (balanced)
    - Technical/Analysis → Gemini Pro (analytical)
    """

    # Model costs (per 1K tokens) - for reference
    MODEL_COSTS = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
    }

    # Keywords for different content types
    BRAND_KEYWORDS = ["브랜드", "공식", "전문", "기업", "회사", "비전", "미션", "가치"]
    CREATIVE_KEYWORDS = ["광고", "카피", "홍보", "마케팅", "캠페인", "슬로건"]
    TECHNICAL_KEYWORDS = ["분석", "데이터", "통계", "보고서", "연구", "기술"]
    CASUAL_KEYWORDS = ["짧게", "간단", "빠르게", "요약", "한줄"]

    @staticmethod
    def select_model(
        prompt: str,
        task_type: str = "text",
        user_preference: Optional[str] = None,
        tone: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Select the best AI model based on prompt analysis

        Args:
            prompt: User's input prompt
            task_type: "text" or "image"
            user_preference: User's preferred model (if specified)
            tone: Content tone (formal, casual, etc.)
            max_tokens: Expected output length

        Returns:
            Dict with selected model and reasoning
        """
        # If user specified a model, respect it
        if user_preference:
            logger.info(f"Using user-specified model: {user_preference}")
            return {
                "model": user_preference,
                "reason": "user_preference",
                "estimated_cost": "user_specified"
            }

        # Image generation uses different models
        if task_type == "image":
            return AIRouter._select_image_model(prompt)

        # Analyze prompt for text generation
        prompt_lower = prompt.lower()
        prompt_length = len(prompt)

        # Rule 1: Very short requests → GPT-3.5 (fast)
        if prompt_length < 100 or any(kw in prompt_lower for kw in AIRouter.CASUAL_KEYWORDS):
            logger.info(f"Selected GPT-3.5 Turbo (short prompt: {prompt_length} chars)")
            return {
                "model": "gpt-3.5-turbo",
                "reason": "short_prompt",
                "estimated_cost": "low"
            }

        # Rule 2: Brand/Professional content → Gemini Pro
        if any(kw in prompt_lower for kw in AIRouter.BRAND_KEYWORDS):
            logger.info("Selected Gemini Pro (brand content)")
            return {
                "model": "gemini-pro",
                "reason": "brand_content",
                "estimated_cost": "very_low"
            }

        # Rule 3: Technical/Analytical → Gemini Pro
        if any(kw in prompt_lower for kw in AIRouter.TECHNICAL_KEYWORDS):
            logger.info("Selected Gemini Pro (technical content)")
            return {
                "model": "gemini-pro",
                "reason": "technical_content",
                "estimated_cost": "very_low"
            }

        # Rule 4: Long complex prompts → GPT-4 Turbo
        if prompt_length > 500 or (max_tokens and max_tokens > 1000):
            logger.info(f"Selected GPT-4 Turbo (long prompt: {prompt_length} chars)")
            return {
                "model": "gpt-4-turbo",
                "reason": "complex_content",
                "estimated_cost": "high"
            }

        # Rule 5: Formal tone → Gemini Pro
        if tone and tone in ["formal", "professional"]:
            logger.info("Selected Gemini Pro (formal tone)")
            return {
                "model": "gemini-pro",
                "reason": "formal_tone",
                "estimated_cost": "very_low"
            }

        # Default: GPT-3.5 Turbo (balanced performance and cost)
        logger.info("Selected GPT-3.5 Turbo (default)")
        return {
            "model": "gpt-3.5-turbo",
            "reason": "default_balanced",
            "estimated_cost": "low"
        }

    @staticmethod
    def _select_image_model(prompt: str) -> Dict[str, any]:
        """
        Select best image generation model

        DALL-E 3: High quality, realistic
        Stable Diffusion XL: Artistic, stylized
        """
        prompt_lower = prompt.lower()

        # Artistic/Stylized → SDXL
        artistic_keywords = ["예술", "그림", "일러스트", "스타일", "추상", "artistic", "illustration"]
        if any(kw in prompt_lower for kw in artistic_keywords):
            logger.info("Selected Stable Diffusion XL (artistic)")
            return {
                "model": "stability-ai/sdxl",
                "reason": "artistic_style",
                "estimated_cost": "medium"
            }

        # Realistic/Photo → DALL-E 3
        realistic_keywords = ["사진", "실사", "현실", "realistic", "photo", "photograph"]
        if any(kw in prompt_lower for kw in realistic_keywords):
            logger.info("Selected DALL-E 3 (realistic)")
            return {
                "model": "dall-e-3",
                "reason": "realistic_photo",
                "estimated_cost": "high"
            }

        # Default: DALL-E 3 (higher quality)
        return {
            "model": "dall-e-3",
            "reason": "default_quality",
            "estimated_cost": "high"
        }

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate API cost based on token usage

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        if model not in AIRouter.MODEL_COSTS:
            return 0.0

        costs = AIRouter.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        total_cost = input_cost + output_cost
        logger.debug(f"Cost estimate for {model}: ${total_cost:.6f} (in: {input_tokens}, out: {output_tokens})")

        return total_cost

    @staticmethod
    def get_model_recommendations(prompt: str) -> Dict[str, any]:
        """
        Get multiple model recommendations with reasoning

        Returns:
            Dict with primary, alternative, and budget options
        """
        primary = AIRouter.select_model(prompt)

        # Budget option: always suggest GPT-3.5
        budget = {
            "model": "gpt-3.5-turbo",
            "reason": "budget_option",
            "estimated_cost": "low"
        }

        # Alternative: Gemini Pro (if primary isn't Gemini)
        if primary["model"] != "gemini-pro":
            alternative = {
                "model": "gemini-pro",
                "reason": "alternative_option",
                "estimated_cost": "very_low"
            }
        else:
            alternative = {
                "model": "gpt-4-turbo",
                "reason": "premium_option",
                "estimated_cost": "high"
            }

        return {
            "primary": primary,
            "alternative": alternative,
            "budget": budget,
            "analysis": {
                "prompt_length": len(prompt),
                "complexity": "high" if len(prompt) > 500 else "medium" if len(prompt) > 100 else "low"
            }
        }
