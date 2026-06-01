"""PPT theme definitions: color palettes, fonts, and layout constants."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorTheme:
    """Color scheme for a presentation style."""

    name: str
    primary_color: str  # RGB hex, used for titles and accents
    secondary_color: str  # Used for subtle elements
    background_color: str  # Slide background
    text_color: str  # Body text
    title_color: str  # Slide titles
    accent_bar_color: str  # Decorative bars/lines
    title_slide_bg: str  # Title slide full background


# Four predefined themes
THEMES: Dict[str, ColorTheme] = {
    "professional": ColorTheme(
        name="Professional Blue",
        primary_color="1F4E79",
        secondary_color="5B9BD5",
        background_color="FFFFFF",
        text_color="333333",
        title_color="1F4E79",
        accent_bar_color="5B9BD5",
        title_slide_bg="1F4E79",
    ),
    "creative": ColorTheme(
        name="Creative Warm",
        primary_color="E87722",
        secondary_color="F5A623",
        background_color="FFF8F0",
        text_color="4A4A4A",
        title_color="D35400",
        accent_bar_color="F5A623",
        title_slide_bg="E87722",
    ),
    "academic": ColorTheme(
        name="Academic Green",
        primary_color="1B5E20",
        secondary_color="4CAF50",
        background_color="FFFFFF",
        text_color="333333",
        title_color="1B5E20",
        accent_bar_color="4CAF50",
        title_slide_bg="1B5E20",
    ),
    "minimal": ColorTheme(
        name="Minimal Dark",
        primary_color="2C3E50",
        secondary_color="95A5A6",
        background_color="FFFFFF",
        text_color="555555",
        title_color="2C3E50",
        accent_bar_color="2C3E50",
        title_slide_bg="2C3E50",
    ),
    "modern_dark": ColorTheme(
        name="Modern Dark",
        primary_color="0D1117",
        secondary_color="58A6FF",
        background_color="161B22",
        text_color="C9D1D9",
        title_color="58A6FF",
        accent_bar_color="58A6FF",
        title_slide_bg="0D1117",
    ),
    "warm_sunset": ColorTheme(
        name="Warm Sunset",
        primary_color="FF6B35",
        secondary_color="F7C59F",
        background_color="FFFAF5",
        text_color="4A3728",
        title_color="E55A1E",
        accent_bar_color="FF6B35",
        title_slide_bg="FF6B35",
    ),
    "ocean_teal": ColorTheme(
        name="Ocean Teal",
        primary_color="006D77",
        secondary_color="83C5BE",
        background_color="FFFFFF",
        text_color="2D4059",
        title_color="006D77",
        accent_bar_color="83C5BE",
        title_slide_bg="006D77",
    ),
    "bold_red": ColorTheme(
        name="Bold Red",
        primary_color="C62828",
        secondary_color="EF9A9A",
        background_color="FFFFFF",
        text_color="333333",
        title_color="B71C1C",
        accent_bar_color="C62828",
        title_slide_bg="C62828",
    ),
}

# Font configuration by language
FONT_FAMILIES: Dict[str, Dict[str, str]] = {
    "english": {"title": "Calibri", "body": "Calibri"},
    "chinese": {"title": "Microsoft YaHei", "body": "Microsoft YaHei"},
    "bilingual": {"title": "Microsoft YaHei", "body": "Microsoft YaHei"},
}

# Slide dimensions (16:9 widescreen, in EMU)
SLIDE_WIDTH = 13333333  # 13.333 inches
SLIDE_HEIGHT = 7500000  # 7.5 inches

# Font sizes (in Pt)
TITLE_SIZE = 32
SUBTITLE_SIZE = 24
SECTION_TITLE_SIZE = 36
BULLET_SIZE = 18
NOTES_SIZE = 10
SLIDE_NUMBER_SIZE = 8
