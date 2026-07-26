"""
LUIN Rate Limiting Middleware
Token bucket algorithm for API rate limiting across auth and public endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.types import ASGIApp, Receive, Scope, Send


class RateLimiter:
    """In-memory token bucket rate limiter."""

    def __init__(self, max_tokens: int = 100, refill_rate: float = 1.0):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def _refill(self, key: str) -> None:
        now = time.time()
        if key not in self.buckets:
            self.buckets[key] = (self.max_tokens, now)
            return
        tokens, last_refill = self.buckets[key]
        elapsed = now - last_refill
        new_tokens = min(self.max_tokens, tokens + elapsed * self.refill_rate)
        self.buckets[key] = (new_tokens, now)

    def consume(self, key: str, tokens: int = 1) -> bool:
        self._refill(key)
        current, _ = self.buckets[key]
        if current >= tokens:
            self.buckets[key] = (current - tokens, time.time())
            return True
        return False

    def get_remaining(self, key: str) -> int:
        self._refill(key)
        return int(self.buckets.get(key, (self.max_tokens, 0))[0])


# Global rate limiter instance
rate_limiter = RateLimiter(max_tokens=100, refill_rate=1.0)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware for rate limiting."""

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if path in ("/health", "/api/v1/health"):
            response = await call_next(request)
            return response

        if not rate_limiter.consume(client_ip):
            remaining = rate_limiter.get_remaining(client_ip)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Try again later.",
                    "retry_after": 60,
                    "remaining_tokens": remaining,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        remaining = rate_limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
