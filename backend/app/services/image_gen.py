import os
import re
import base64
import requests
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
_THIS_FILE = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parents[2]
_ENV_DIR_FILE = _BACKEND_DIR / "env" / ".env"
_ROOT_ENV_FILE = _BACKEND_DIR / ".env"

for candidate in (_ENV_DIR_FILE, _ROOT_ENV_FILE):
    if candidate.exists():
        load_dotenv(dotenv_path=candidate, override=False)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
POLLINATIONS_API = "https://image.pollinations.ai/prompt/{prompt}"


def detect_image_generation_request(text: str) -> Optional[str]:
    """
    Detect if the user is requesting image generation.
    Returns the image description if detected, None otherwise.
    """
    patterns = [
        # With "of/for/from/based on" (strict)
        r"generate\s+(?:an?\s+|the\s+|some\s+)?(?:new\s+)?(?:image|idea|design|concept)s?\s+(?:of|for|based on|from)\s+(.+)",
        r"create\s+(?:an?\s+|the\s+|some\s+)?(?:new\s+)?(?:image|idea|design|concept)s?\s+(?:of|for|based on|from)\s+(.+)",
        r"draw\s+(?:an?\s+|the\s+|some\s+)?(?:new\s+)?(?:image|idea|design|concept)s?\s+(?:of|for|based on|from)\s+(.+)",
        r"make\s+(?:an?\s+|the\s+|some\s+)?(?:new\s+)?(?:image|idea|design|concept)s?\s+(?:of|for|based on|from)\s+(.+)",
        r"show\s+me\s+(?:an?\s+|the\s+|some\s+)?(?:new\s+)?(?:image|idea|design|concept)s?\s+(?:of|for|based on|from)\s+(.+)",
        
        # Without "of/for" - more flexible (catches "generate image lord rama")
        r"generate\s+(?:an?\s+|the\s+)?image\s+(.+)",
        r"create\s+(?:an?\s+|the\s+)?image\s+(.+)",
        r"draw\s+(?:an?\s+|the\s+)?image\s+(.+)",
        r"make\s+(?:an?\s+|the\s+)?image\s+(.+)",
        
        # Other patterns
        r"redesign\s+(?:this|the)\s+(.+)",
        r"modify\s+(?:this|the)\s+(.+)",
        r"reimagine\s+(?:this|the)\s+(.+)",
        r"generate:\s*(.+)",
        r"image:\s*(.+)",
        r"paint\s+(?:an?\s+|the\s+)?image\s+(?:of\s+)?(.+)",
        r"design\s+(?:an?\s+|the\s+)?image\s+(?:of\s+)?(.+)",
    ]
    
    text_lower = text.lower().strip()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            description = match.group(1).strip()
            # Clean up the description
            description = re.sub(r'\s+', ' ', description)
            return description
    
    return None


async def generate_image_pollinations(prompt: str) -> Tuple[str, str]:
    """
    Generate image using Pollinations.ai (free, no API key needed).
    Returns (image_url, base64_data).
    """
    try:
        # Clean and encode the prompt
        clean_prompt = prompt.replace(' ', '%20')
        image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true"
        
        # Fetch the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Convert to base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        
        return image_url, image_data
    except Exception as e:
        raise Exception(f"Failed to generate image: {str(e)}")


async def generate_image_google(prompt: str) -> Tuple[str, str]:
    """
    Generate image using Google's Imagen via Gemini API.
    Requires GEMINI_API_KEY in environment.
    Returns (placeholder_url, base64_data).
    
    Note: As of now, Gemini primarily focuses on text and vision understanding.
    For image generation, we'll use Pollinations as the primary service.
    This function is kept for future Google Imagen integration.
    """
    if not GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY not configured")
    
    # Google's Imagen API is not yet publicly available via the standard Gemini API
    # For now, we'll fall back to Pollinations
    raise Exception("Google Imagen not yet available. Using Pollinations instead.")


async def generate_image(prompt: str) -> Tuple[str, str]:
    """
    Main function to generate an image.
    Uses Pollinations.ai (free, no API key needed).
    Returns (image_url, base64_data).
    
    Note: Google's Imagen API is not yet publicly available.
    Your GEMINI_API_KEY is used for text chat, but image generation
    uses the free Pollinations.ai service which provides high-quality results.
    """
    try:
        # Use Pollinations (free, no API key needed, high quality)
        return await generate_image_pollinations(prompt)
    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")
