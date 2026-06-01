"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Centralized settings for the PPT Generator application."""

    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_AUTH_TOKEN", "")
    )
    anthropic_base_url: str = field(
        default_factory=lambda: os.getenv(
            "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
        )
    )
    anthropic_model: str = field(
        default_factory=lambda: os.getenv(
            "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"
        )
    )
    max_slides: int = 20
    min_slides: int = 3
    default_slides: int = 10
    output_dir: str = "output"
    max_request_timeout: int = 120  # seconds


settings = Settings()
