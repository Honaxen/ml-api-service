"""
app/cache.py — Redis-based response caching.

Caches LLM responses by prompt hash.
Same prompt = same response, returned instantly without hitting Ollama.

TTL: configurable via CACHE_TTL_SECONDS env var (default: 1 hour)
"""

import hashlib
import json
import os
from typing import Optional

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def _make_key(prompt: str, model: str, temperature: float) -> str:
    """Create a cache key from prompt + model + temperature."""
    raw = f"{prompt}:{model}:{temperature}"
    return "ml_api:" + hashlib.sha256(raw.encode()).hexdigest()


class Cache:
    """Redis cache wrapper with graceful fallback when Redis is unavailable."""

    def __init__(self):
        self._redis = None
        self._available = False
        self._connect()

    def _connect(self):
        try:
            import redis
            self._redis = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2)
            self._redis.ping()
            self._available = True
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get(self, prompt: str, model: str, temperature: float) -> Optional[str]:
        """Return cached response or None."""
        if not self._available:
            return None
        try:
            key = _make_key(prompt, model, temperature)
            value = self._redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    def set(self, prompt: str, model: str, temperature: float, response: str) -> None:
        """Cache a response."""
        if not self._available:
            return
        try:
            key = _make_key(prompt, model, temperature)
            self._redis.setex(key, CACHE_TTL, json.dumps(response))
        except Exception:
            pass

    def status(self) -> str:
        if not self._available:
            return "unavailable"
        try:
            self._redis.ping()
            return "connected"
        except Exception:
            return "unavailable"


# Singleton instance
cache = Cache()