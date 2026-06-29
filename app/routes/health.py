"""
app/routes/health.py — GET /health endpoint.

Returns status of all services: API, Ollama, Redis.
No authentication required.
"""

import json
import urllib.request

from fastapi import APIRouter
from app.cache import cache
from app.models import HealthResponse

router = APIRouter()


def _check_ollama() -> str:
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return "connected"
        return "unavailable"
    except Exception:
        return "unavailable"


@router.get("/health", response_model=HealthResponse)
def health():
    """Check status of all services."""
    return HealthResponse(
        status="ok",
        ollama=_check_ollama(),
        redis=cache.status(),
    )