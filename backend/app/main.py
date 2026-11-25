import os
# Ensure pure Python fallback in constrained sandbox environments
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.middleware import PayloadSizeLimitMiddleware, IPRateLimitMiddleware
from backend.app.api.v1 import router as api_v1_router
from backend.app.api.v1.health import router as health_router
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield


def create_app() -> FastAPI:
    """FastAPI application factory configuring routes, security, and middlewares."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="OfferCheck: AI-Assisted Fake Internship Offer Detection System",
        lifespan=lifespan
    )

    # 1. Payload size limiter (200 KB cap per specification)
    app.add_middleware(PayloadSizeLimitMiddleware, max_bytes=settings.MAX_PAYLOAD_BYTES)

    # 2. Rate limiter per IP (30 req/min)
    app.add_middleware(IPRateLimitMiddleware, max_requests=settings.RATE_LIMIT_PER_MINUTE)

    # 3. CORS restricted to frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
