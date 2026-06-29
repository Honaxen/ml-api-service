"""
app/models.py — Pydantic request and response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4096, description="The prompt to send to the LLM")
    model: str = Field(default="gemma3:12b", description="Ollama model to use")
    max_tokens: int = Field(default=500, ge=1, le=2048, description="Max tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")


class GenerateResponse(BaseModel):
    response: str
    model: str
    cached: bool = False
    latency_ms: float
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    ollama: str
    redis: str
    version: str = "1.0.0"


class TokenRequest(BaseModel):
    api_key: str = Field(..., description="Your API key")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600