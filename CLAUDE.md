# PPT Generator — AI-Powered Presentation Creation

FastAPI web app that calls Claude API to generate structured slide content,
then builds a formatted .pptx file with professional layouts, charts, and
typography.

## Quick Start

```bash
cd C:/Users/34208/ppt-generator
cp .env.example .env          # add your ANTHROPIC_AUTH_TOKEN
pip install -r requirements.txt
python app.py                  # → http://localhost:8000
```

API base URL defaults to `https://api.anthropic.com`. Override via
`ANTHROPIC_BASE_URL` in `.env` if using a proxy (e.g., DeepSeek).

## Project Structure

```
ppt-generator/
├── app.py                  # FastAPI app, routes, entry point
├── src/
│   ├── __init__.py
│   ├── config.py           # Settings from env vars (dataclass)
│   ├── models.py           # Pydantic request/response schemas
│   ├── prompts.py          # System & user prompt templates
│   ├── ai_service.py       # Claude API client + JSON parsing
│   ├── ppt_generator.py    # PPTX creation engine (~700 lines)
│   └── templates.py        # 8 color themes, fonts, dimensions
├── templates/
│   └── index.html          # Jinja2 web UI
├── static/
│   ├── css/style.css       # Responsive form styling
│   └── js/main.js          # Form submit + download logic
├── output/                 # Generated .pptx files (gitignored)
└── .env.example            # Env template
```

## Data Flow

```
Browser form → POST /api/generate → PPTRequest (Pydantic validation)
  → build_system_prompt() + build_user_prompt()
  → generate_slide_content() → Claude API (anthropic SDK)
  → _parse_json_response() (4 fallback strategies)
  → validate_slide_structure() (normalize, trim, pad)
  → create_pptx() → BytesIO buffer
  → StreamingResponse (in-memory download)
```

## Key Design Decisions

- **In-memory pipeline**: Entire flow runs in memory. No temp files. PPTX
  returned as a streaming download.
- **4-layer JSON parsing**: Direct parse → code fence extraction → trailing
  comma fix → bracket matching. Claude often wraps JSON in markdown or adds
  trailing commas.
- **McKinsey-style prompts**: System prompt instructs Claude to roleplay a
  strategy consultant. Varies depth (deep/medium/light) across slides for
  rhythm. Titles must state the key message, not just labels.
- **8 color themes**: Professional, Creative, Academic, Minimal, Modern Dark,
  Warm Sunset, Ocean Teal, Bold Red. Defined in `src/templates.py`.
- **10 slide types**: title, agenda, content (deep/medium/light), chart,
  two_column, quote, datapoint, section, summary. Dispatch via `create_pptx()`.

## Running Locally

```bash
# Install
pip install fastapi uvicorn python-pptx anthropic python-dotenv jinja2 python-multipart

# Run
python app.py
# or: uvicorn app:app --reload --port 8000

# Test
curl http://localhost:8000/health
```

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `ANTHROPIC_AUTH_TOKEN` | (required) | Claude API key |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | Use DeepSeek proxy if needed |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Model to use |

## Common Operations

- **Add a new theme**: Add entry to `THEMES` dict in `src/templates.py`
- **Change slide layout**: Edit layout functions in `src/ppt_generator.py`
- **Tweak AI output style**: Edit `SYSTEM_PROMPT` in `src/prompts.py`
- **Add new slide type**: Add layout function + dispatch in `create_pptx()`
- **Add request param**: Add field to `PPTRequest` in `src/models.py`,
  pass through `build_system_prompt()` / `build_user_prompt()`

## Git

- Initialized 2026-06-01, main branch
- `.env` is gitignored (contains API key)
- `output/*.pptx` is gitignored (generated files)
