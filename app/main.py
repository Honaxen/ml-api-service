"""
app/main.py — FastAPI application entry point.

Endpoints:
    POST /token       — get JWT from API key (no auth needed)
    POST /generate    — generate LLM response (requires JWT)
    GET  /health      — service status (no auth needed)
    GET  /docs        — Swagger UI (auto-generated)

Run:
    uvicorn app.main:app --reload
"""

import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.auth import create_access_token, validate_api_key
from app.models import TokenRequest, TokenResponse
from app.routes import generate, health

app = FastAPI(
    title="ML API Service",
    description="Production-ready LLM API with auth, rate limiting, and caching.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(generate.router, tags=["Generation"])
app.include_router(health.router, tags=["Health"])


@app.post("/token", response_model=TokenResponse, tags=["Auth"])
def get_token(request: TokenRequest):
    """
    Exchange an API key for a JWT access token.

    Use the token in subsequent requests:
        Authorization: Bearer <token>

    Default dev keys (set in .env):
        dev-key-123
        test-key-456
    """
    if not validate_api_key(request.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    token = create_access_token(request.api_key)
    return TokenResponse(access_token=token)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "ML API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }