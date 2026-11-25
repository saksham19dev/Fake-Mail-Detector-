import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status
from backend.app.core.config import settings


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming request bodies exceeding the 200 KB security cap."""
    def __init__(self, app, max_bytes: int = settings.MAX_PAYLOAD_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": f"Payload size exceeds the {self.max_bytes // 1024} KB limit."}
            )
        return await call_next(request)


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter per client IP (30 req/min)."""
    def __init__(self, app, max_requests: int = settings.RATE_LIMIT_PER_MINUTE, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude health check and docs from rate limiting
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old timestamps
        timestamps = self.requests_log[client_ip]
        self.requests_log[client_ip] = [t for t in timestamps if t > window_start]

        if len(self.requests_log[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Rate limit is 30 requests per minute."},
                headers={"Retry-After": str(self.window_seconds)}
            )

        self.requests_log[client_ip].append(now)
        return await call_next(request)
