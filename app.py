"""FastAPI application: AI-powered PPT Generator.

Serves the web UI and exposes a /api/generate endpoint that:
1. Accepts presentation parameters (topic, style, language, etc.)
2. Calls Claude API to generate structured slide content
3. Builds a formatted .pptx file in memory
4. Streams the file back to the browser as a download
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import traceback
import re

from src.config import settings
from src.models import PPTRequest
from src.ai_service import generate_slide_content, validate_slide_structure
from src.ppt_generator import create_pptx

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PPT Generator API",
    description="AI-powered presentation generation",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse(
        request=request, name="index.html"
    )


@app.post("/api/generate")
async def generate_ppt(request: PPTRequest):
    """Generate a PPTX file from the provided topic and parameters.

    The entire pipeline runs in memory:
    AI generation → JSON validation → PPTX creation → streaming download.
    No temporary files are written to disk.

    Returns:
        StreamingResponse: The .pptx file as a download.
    """
    try:
        # Step 1: AI content generation
        slide_data = await generate_slide_content_async(request)

        # Step 2: Validate and normalize
        slide_data = validate_slide_structure(slide_data, request.slide_count)

        # Step 3: Build PPTX in memory
        pptx_buffer = create_pptx(slide_data, request)

        # Step 4: Generate ASCII-safe filename
        # Only keep ASCII alphanumeric, spaces, hyphens, and underscores.
        # Chinese/Unicode chars must be stripped because HTTP Content-Disposition
        # headers only support Latin-1 encoding.
        safe_topic = "".join(
            c
            for c in request.topic[:30]
            if c.isascii() and (c.isalnum() or c in (" ", "-", "_"))
        ).strip()
        safe_topic = safe_topic.replace(" ", "_")
        if safe_topic:
            filename = f"{safe_topic}.pptx"
        else:
            # Fallback: use a timestamp-based name for non-ASCII topics
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"presentation_{timestamp}.pptx"

        # Step 5: Return as streaming download
        return StreamingResponse(
            pptx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(pptx_buffer.getbuffer().nbytes),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"Error generating PPT: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presentation: {str(e)}",
        )


async def generate_slide_content_async(request: PPTRequest) -> dict:
    """Async wrapper around the synchronous generate_slide_content().

    In a production environment with concurrent users, we'd offload this
    to a thread pool. For single-user usage, a simple wrapper suffices.
    """
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, generate_slide_content, request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": settings.anthropic_model,
    }
