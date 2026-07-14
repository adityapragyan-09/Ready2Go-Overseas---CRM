import time
from collections import deque, defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import status
from fastapi.responses import JSONResponse

from app.core.config import settings


class SimpleRateLimiterMiddleware(BaseHTTPMiddleware):
    """Very small in-memory IP rate limiter.

    Not suitable for multi-process production deployments behind a load
    balancer — prefer a centralized store (Redis) or API gateway in real setups.
    """

    def __init__(self, app, requests_per_minute: int = 600):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.store = defaultdict(deque)

    async def dispatch(self, request, call_next):
        # Do not rate limit internal health checks or docs when in debug
        if request.url.path in ("/health",) or settings.DEBUG:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.time()
        q = self.store[client]
        # purge old timestamps
        while q and q[0] < now - self.window_seconds:
            q.popleft()

        if len(q) >= self.requests_per_minute:
            retry_after = int(self.window_seconds - (now - q[0]))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "Too many requests. Please slow down.",
                    "data": None,
                    "error": "RATE_LIMITED",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        q.append(now)
        return await call_next(request)


def setup_rate_limiter(app, requests_per_minute: int = 600):
    app.add_middleware(SimpleRateLimiterMiddleware, requests_per_minute=requests_per_minute)
