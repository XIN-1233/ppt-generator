"""Image download service — zero config, free image sources.

Uses Lorem Picsum (picsum.photos) for stock photos and Pollinations.ai
for AI-generated images. No API key required.
"""

import requests
from io import BytesIO
from urllib.parse import quote


def download_image(url: str, timeout: int = 15) -> BytesIO | None:
    """Download an image from URL into a BytesIO buffer.

    Args:
        url: Image URL.
        timeout: Request timeout in seconds.

    Returns:
        BytesIO buffer ready for python-pptx, or None on failure.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return BytesIO(resp.content)
    except Exception:
        return None


def get_picsum_url(seed: str, width: int = 800, height: int = 600) -> str:
    """Build a Lorem Picsum URL. Same seed = same image (consistent).

    Args:
        seed: Text seed for reproducible images.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        URL string.
    """
    safe_seed = quote(seed.replace(" ", "-")[:60], safe="")
    return f"https://picsum.photos/seed/{safe_seed}/{width}/{height}"


def get_picsum_bg(seed: str, blur: int = 0) -> BytesIO | None:
    """Download a full-HD background image from Picsum.

    Args:
        seed: Text seed for reproducible images.
        blur: Blur amount 0-10 (0 = no blur).

    Returns:
        BytesIO buffer or None.
    """
    url = get_picsum_url(seed, 1920, 1080)
    if blur:
        url += f"?blur={blur}"
    return download_image(url)


def get_picsum_square(seed: str, size: int = 600) -> BytesIO | None:
    """Download a square image from Picsum (good for content slides)."""
    url = get_picsum_url(seed, size, size)
    return download_image(url)


def get_ai_image(prompt: str, width: int = 1024, height: int = 768) -> BytesIO | None:
    """Generate an AI image via Pollinations.ai (free, no API key).

    Args:
        prompt: Description of the image to generate.
        width: Image width.
        height: Image height.

    Returns:
        BytesIO buffer or None.
    """
    safe_prompt = quote(prompt[:200], safe="")
    url = (
        f"https://image.pollinations.ai/prompt/{safe_prompt}"
        f"?width={width}&height={height}&model=flux&nologo=true"
    )
    return download_image(url, timeout=30)
