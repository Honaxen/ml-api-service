"""
tests/test_api.py — Unit tests for auth, cache key generation, and rate limiter.

Tests the deterministic parts without needing Ollama or Redis.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("API_KEYS", "test-key-1,test-key-2")


# ─────────────────────────────────────────────
# Auth tests
# ─────────────────────────────────────────────

class TestAuth:
    def test_validate_valid_key(self):
        from app.auth import validate_api_key
        assert validate_api_key("test-key-1") is True

    def test_validate_invalid_key(self):
        from app.auth import validate_api_key
        assert validate_api_key("fake-key") is False

    def test_create_and_verify_token(self):
        from app.auth import create_access_token
        from jose import jwt
        token = create_access_token("test-key-1")
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == "test-key-1"

    def test_token_is_string(self):
        from app.auth import create_access_token
        token = create_access_token("test-key-1")
        assert isinstance(token, str)
        assert len(token) > 0


# ─────────────────────────────────────────────
# Cache key tests
# ─────────────────────────────────────────────

class TestCacheKey:
    def test_same_inputs_same_key(self):
        from app.cache import _make_key
        k1 = _make_key("hello", "gemma3:12b", 0.7)
        k2 = _make_key("hello", "gemma3:12b", 0.7)
        assert k1 == k2

    def test_different_prompt_different_key(self):
        from app.cache import _make_key
        k1 = _make_key("hello", "gemma3:12b", 0.7)
        k2 = _make_key("world", "gemma3:12b", 0.7)
        assert k1 != k2

    def test_different_model_different_key(self):
        from app.cache import _make_key
        k1 = _make_key("hello", "gemma3:12b", 0.7)
        k2 = _make_key("hello", "llama3.2", 0.7)
        assert k1 != k2

    def test_different_temperature_different_key(self):
        from app.cache import _make_key
        k1 = _make_key("hello", "gemma3:12b", 0.7)
        k2 = _make_key("hello", "gemma3:12b", 0.9)
        assert k1 != k2

    def test_key_has_prefix(self):
        from app.cache import _make_key
        k = _make_key("hello", "gemma3:12b", 0.7)
        assert k.startswith("ml_api:")


# ─────────────────────────────────────────────
# Rate limiter tests
# ─────────────────────────────────────────────

class TestRateLimiter:
    def test_allows_requests_under_limit(self):
        from app.limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(max_requests=5, window=60)
        for _ in range(5):
            limiter.check("test-key")  # should not raise

    def test_blocks_requests_over_limit(self):
        from app.limiter import InMemoryRateLimiter
        from fastapi import HTTPException
        limiter = InMemoryRateLimiter(max_requests=3, window=60)
        for _ in range(3):
            limiter.check("test-key-x")
        try:
            limiter.check("test-key-x")
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 429

    def test_different_keys_independent(self):
        from app.limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(max_requests=2, window=60)
        limiter.check("key-a")
        limiter.check("key-a")
        # key-b should still work
        limiter.check("key-b")

    def test_remaining_decreases(self):
        from app.limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(max_requests=5, window=60)
        assert limiter.remaining("new-key") == 5
        limiter.check("new-key")
        assert limiter.remaining("new-key") == 4

    def test_models_request_schema(self):
        from app.models import GenerateRequest
        req = GenerateRequest(prompt="Hello", model="gemma3:12b")
        assert req.prompt == "Hello"
        assert req.temperature == 0.7
        assert req.max_tokens == 500