"""
app/routes/generate.py — POST /generate endpoint.

Protected by JWT auth + rate limiting + Redis caching.
"""

import json
import time
import urllib.request
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_token
from app.cache import cache
from app.limiter import limiter
from app.models import GenerateRequest, GenerateResponse

router = APIRouter()

OLLAMA_URL = "http://localhost:11434/api/chat"


def _call_ollama(prompt: str, model: str, max_tokens: int, temperature: float) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {e}")


@router.post("/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest,
    api_key: str = Depends(verify_token),
):
    """
    Generate a response from an LLM.

    - Requires Bearer token (get from POST /token)
    - Rate limited: 10 requests per 60 seconds per API key
    - Responses cached in Redis for 1 hour
    """
    # Rate limit check
    limiter.check(api_key)

    start = time.time()

    # Check cache
    cached_response = cache.get(request.prompt, request.model, request.temperature)
    if cached_response:
        latency = round((time.time() - start) * 1000, 2)
        return GenerateResponse(
            response=cached_response,
            model=request.model,
            cached=True,
            latency_ms=latency,
            timestamp=datetime.utcnow(),
        )

    # Call Ollama
    response_text = _call_ollama(
        request.prompt,
        request.model,
        request.max_tokens,
        request.temperature,
    )

    # Store in cache
    cache.set(request.prompt, request.model, request.temperature, response_text)

    latency = round((time.time() - start) * 1000, 2)

    return GenerateResponse(
        response=response_text,
        model=request.model,
        cached=False,
        latency_ms=latency,
        timestamp=datetime.utcnow(),
    )