"""
OpenAI Client Helper
Provides utility functions for text and image generation using OpenAI API
"""
import os
from typing import Optional
from openai import OpenAI
from logger import get_logger

logger = get_logger("openai_client")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. AI generation will fail.")
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI client initialized")


async def generate_text(
    prompt: str,
    max_tokens: Optional[int] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7
) -> str:
    """
    Generate text using OpenAI Chat API

    Args:
        prompt: The prompt to generate text from
        max_tokens: Maximum tokens to generate (default: None for model default)
        model: Model to use (default: gpt-3.5-turbo)
        temperature: Sampling temperature (default: 0.7)

    Returns:
        Generated text string

    Raises:
        Exception: If OpenAI API call fails
    """
    if not client:
        raise Exception("OpenAI client not initialized. Check OPENAI_API_KEY.")

    try:
        logger.debug(f"Generating text with prompt: {prompt[:100]}...")

        # Prepare API call parameters
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful marketing content generator."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        if max_tokens:
            params["max_tokens"] = max_tokens

        # Call OpenAI API
        response = client.chat.completions.create(**params)

        # Extract generated text
        generated_text = response.choices[0].message.content

        logger.info(f"Generated {len(generated_text)} characters of text")
        return generated_text

    except Exception as e:
        logger.error(f"Text generation failed: {str(e)}")
        raise Exception(f"Failed to generate text: {str(e)}")


async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    model: str = "dall-e-3",
    quality: str = "standard"
) -> Optional[str]:
    """
    Generate image using OpenAI DALL-E API

    Args:
        prompt: The prompt to generate image from
        size: Image size (default: 1024x1024)
              Valid sizes for DALL-E 3: 1024x1024, 1024x1792, 1792x1024
        model: Model to use (default: dall-e-3)
        quality: Image quality - 'standard' or 'hd' (default: standard)

    Returns:
        URL of generated image, or None if generation fails

    Raises:
        Exception: If OpenAI API call fails
    """
    if not client:
        raise Exception("OpenAI client not initialized. Check OPENAI_API_KEY.")

    try:
        logger.debug(f"Generating image with prompt: {prompt[:100]}...")

        # Validate size for DALL-E 3
        valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
        if size not in valid_sizes:
            logger.warning(f"Invalid size {size}, using 1024x1024")
            size = "1024x1024"

        # Call OpenAI DALL-E API
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1
        )

        # Extract image URL
        image_url = response.data[0].url

        logger.info(f"Generated image: {image_url}")
        return image_url

    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise Exception(f"Failed to generate image: {str(e)}")


def get_client() -> Optional[OpenAI]:
    """
    Get the initialized OpenAI client

    Returns:
        OpenAI client instance or None if not initialized
    """
    return client
