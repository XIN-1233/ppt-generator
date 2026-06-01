"""AI service layer: calls Claude API to generate structured slide content."""

import json
import re
import anthropic
from src.config import settings
from src.models import PPTRequest
from src.prompts import build_system_prompt, build_user_prompt

# Singleton client, reuse across requests
client = anthropic.Anthropic(
    api_key=settings.anthropic_api_key,
    base_url=settings.anthropic_base_url,
    timeout=settings.max_request_timeout,
)


def generate_slide_content(request: PPTRequest) -> dict:
    """Call Claude API to generate structured slide content.

    Args:
        request: Validated PPTRequest with all user parameters.

    Returns:
        dict: Parsed JSON matching the slide schema.

    Raises:
        ValueError: If Claude returns unparseable content.
        anthropic.APIError: If the API call fails.
    """
    system_prompt = build_system_prompt(
        language=request.language.value,
        tone=request.tone.value,
        audience=request.audience or "general audience",
        include_notes=request.include_speaker_notes,
        include_emojis=request.include_emojis,
        slide_count=request.slide_count,
    )

    user_prompt = build_user_prompt(
        topic=request.topic,
        slide_count=request.slide_count,
        style=request.style.value,
        language=request.language.value,
        tone=request.tone.value,
        audience=request.audience or "",
        include_notes=request.include_speaker_notes,
        include_emojis=request.include_emojis,
    )

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.7,
    )

    # Extract text from TextBlock(s), skip ThinkingBlock(s)
    text_blocks = [
        block.text for block in response.content if block.type == "text"
    ]
    if not text_blocks:
        raise ValueError("AI response contained no text content")
    raw_text = "".join(text_blocks)
    return _parse_json_response(raw_text)


def _parse_json_response(text: str) -> dict:
    """Extract and parse JSON from Claude's response.

    Handles cases where the model wraps JSON in:
    - Markdown code fences (```json ... ```)
    - Explanatory text before/after the JSON
    - Plain JSON (ideal case)

    Args:
        text: Raw text response from Claude.

    Returns:
        dict: Parsed JSON object.

    Raises:
        ValueError: If no valid JSON could be extracted.
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Fix common JSON issues and retry
    # Remove trailing commas (most common AI JSON mistake)
    fixed = re.sub(r",(\s*[}\]])", r"\1", text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Strategy 4: Find the outermost JSON object via bracket matching
    start = text.find("{")
    if start >= 0:
        # Find the matching closing brace
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break

    raise ValueError(
        f"Failed to parse JSON from AI response. "
        f"First 200 chars: {text[:200]}..."
    )


def validate_slide_structure(data: dict, expected_count: int) -> dict:
    """Validate and normalize the AI-generated slide structure.

    Ensures:
    - The top-level has 'title' and 'slides' keys.
    - First slide is a title slide.
    - Last slide is a summary slide.
    - Slide count does not exceed expected_count.
    - Each slide has its required fields.

    Args:
        data: Parsed JSON from the AI.
        expected_count: Target number of slides.

    Returns:
        dict: Validated and normalized slide data.
    """
    # Ensure top-level fields
    if "title" not in data:
        data["title"] = "Untitled Presentation"
    if "slides" not in data or not isinstance(data["slides"], list):
        raise ValueError("AI response missing 'slides' array")

    slides = data["slides"]
    if not slides:
        raise ValueError("AI returned an empty slides array")

    # Ensure first slide is a title slide
    if slides[0].get("type") != "title":
        slides.insert(
            0,
            {
                "type": "title",
                "title": data["title"],
                "subtitle": "",
            },
        )

    # Ensure last slide is a summary slide (if we have enough slides)
    if len(slides) > 2 and slides[-1].get("type") != "summary":
        slides.append(
            {
                "type": "summary",
                "title": "Thank You",
                "bullets": [
                    "Key points summarized",
                    "Questions & Discussion",
                    "Thank you for your attention",
                ],
            }
        )

    # Enforce slide count limit
    if len(slides) > expected_count + 2:
        # Keep the title slide, trim from the middle, keep the summary
        title_slide = slides[0]
        summary_slide = slides[-1] if slides[-1]["type"] == "summary" else None
        body = [s for s in slides[1:-1]] if summary_slide else slides[1:]
        trimmed = body[: expected_count - (1 if summary_slide else 0)]
        slides = [title_slide] + trimmed + ([summary_slide] if summary_slide else [])
    elif len(slides) < expected_count:
        # Pad with placeholder content slides (should be rare with good prompts)
        while len(slides) < expected_count:
            slides.insert(
                -1 if slides[-1]["type"] == "summary" else len(slides),
                {
                    "type": "content",
                    "title": "Additional Insights",
                    "bullets": ["Topic exploration", "Further considerations"],
                },
            )

    # Ensure each slide has minimum required fields based on type
    for slide in slides:
        slide_type = slide.get("type", "content")
        if "title" not in slide:
            slide["title"] = "Untitled Slide"
        # depth field: default to "medium"
        if "depth" not in slide:
            slide["depth"] = "medium"
        if slide["depth"] not in ("deep", "medium", "light"):
            slide["depth"] = "medium"
        # content_style: default based on depth
        if "content_style" not in slide:
            slide["content_style"] = "narrative" if slide["depth"] == "light" else "bullets"
        # narrative field for light slides
        if slide["content_style"] == "narrative" and "narrative" not in slide:
            # convert bullets to narrative
            bullets = slide.get("bullets", [])
            if bullets:
                texts = [b if isinstance(b, str) else b.get("text", "") for b in bullets]
                slide["narrative"] = ". ".join(texts) + "."
        if slide_type in ("content", "summary", "agenda") and "bullets" not in slide:
            slide["bullets"] = []
        if slide_type == "two_column":
            if "left_bullets" not in slide:
                slide["left_bullets"] = []
            if "right_bullets" not in slide:
                slide["right_bullets"] = slide.get("bullets", [])
        if slide_type == "quote" and "quote" not in slide:
            slide["quote"] = slide.get("title", "")
        if slide_type == "datapoint":
            if "big_number" not in slide:
                slide["big_number"] = ""
            if "description" not in slide:
                slide["description"] = slide.get("subtitle", "")
        if slide_type == "chart":
            if "chart_type" not in slide:
                slide["chart_type"] = "bar"
            valid_types = ("bar", "column", "line", "pie", "stacked_bar", "area")
            if slide["chart_type"] not in valid_types:
                slide["chart_type"] = "bar"
            if "categories" not in slide or len(slide.get("categories", [])) < 2:
                slide["categories"] = ["A", "B", "C", "D"]
            if "series" not in slide or not isinstance(slide.get("series"), list):
                slide["series"] = [{"name": "Value", "values": [10, 20, 30, 40]}]
            # Ensure each series values match categories length
            cat_len = len(slide["categories"])
            for s in slide["series"]:
                if len(s.get("values", [])) != cat_len:
                    s["values"] = s.get("values", [0] * cat_len)[:cat_len]
                    while len(s["values"]) < cat_len:
                        s["values"].append(0)
            if "insight" not in slide:
                slide["insight"] = ""

    data["slides"] = slides
    return data
