"""Pydantic models for request validation and response serialization."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class SlideStyle(str, Enum):
    """Visual theme options for the presentation."""

    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    ACADEMIC = "academic"
    MINIMAL = "minimal"
    MODERN_DARK = "modern_dark"
    WARM_SUNSET = "warm_sunset"
    OCEAN_TEAL = "ocean_teal"
    BOLD_RED = "bold_red"


class Language(str, Enum):
    """Content language options."""

    ENGLISH = "english"
    CHINESE = "chinese"
    BILINGUAL = "bilingual"


class Tone(str, Enum):
    """Writing tone for slide content."""

    FORMAL = "formal"
    SEMI_FORMAL = "semi-formal"
    CASUAL = "casual"


class PPTRequest(BaseModel):
    """Request schema for generating a presentation."""

    topic: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="The presentation topic / 课题要求",
    )
    slide_count: int = Field(
        default=10,
        ge=3,
        le=20,
        description="Number of slides to generate",
    )
    style: SlideStyle = Field(
        default=SlideStyle.PROFESSIONAL,
        description="Visual style / color theme",
    )
    language: Language = Field(
        default=Language.ENGLISH,
        description="Content language",
    )
    tone: Tone = Field(
        default=Tone.SEMI_FORMAL,
        description="Writing tone for slide text",
    )
    include_speaker_notes: bool = Field(
        default=False,
        description="Generate speaker notes for each slide",
    )
    include_emojis: bool = Field(
        default=True,
        description="Add emoji icons to slide titles",
    )
    audience: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Target audience description (e.g., 'high school students')",
    )

    @field_validator("topic")
    @classmethod
    def topic_must_be_meaningful(cls, v: str) -> str:
        """Strip whitespace and ensure minimum length."""
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Topic must be at least 2 characters")
        return stripped


class PPTResponse(BaseModel):
    """Response schema returned after successful generation."""

    filename: str
    slide_count: int
    message: str
