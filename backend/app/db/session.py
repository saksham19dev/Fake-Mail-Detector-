import os
# Ensure pure Python fallback in constrained sandbox environments
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.config import settings
from backend.app.db.base import Base
# Import all models to ensure they are registered with Base metadata
from backend.app.models import Report, Finding, Feedback, Domain


# Determine connect args (e.g. for sqlite)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Async SQLAlchemy engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize tables if they do not exist (useful for quickstart & tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
