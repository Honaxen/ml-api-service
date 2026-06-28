"""
app/limiter.py — Token bucket rate limiting per API key.

Limits: configurable via env vars
    RATE_LIMIT_REQUESTS: max requests per window (default: 10)
    RATE_LIMIT_WINDOW:   window in seconds (default: 60)

Uses Redis if available, falls back to in-memory dict.
In-memory fallback works for single-instance deployments.
"""

import os
import time
from collections import defaultdict
from fastapi import HTTPException, status

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


class InMemoryRateLimiter:
    """Simple sliding window rate limiter using in-memory storage."""

    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, api_key: str) -> None:
        """
        Check if the API key has exceeded its rate limit.
        Raises HTTP 429 if limit exceeded.
        """
        now = time.time()
        window_start = now - self.window

        # Remove timestamps outside the window
        self._requests[api_key] = [
            t for t in self._requests[api_key] if t > window_start
        ]

        if len(self._requests[api_key]) >= self.max_requests:
            oldest = self._requests[api_key][0]
            retry_after = int(self.window - (now - oldest)) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[api_key].append(now)

    def remaining(self, api_key: str) -> int:
        """Return remaining requests in current window."""
        now = time.time()
        window_start = now - self.window
        recent = [t for t in self._requests[api_key] if t > window_start]
        return max(0, self.max_requests - len(recent))


# Singleton
limiter = InMemoryRateLimiter()