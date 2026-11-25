from typing import List, Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    PROJECT_NAME: str = "OfferCheck"
    API_V1_STR: str = "/v1"
    
    # Database URL: defaults to postgresql+asyncpg; fallback to sqlite+aiosqlite for testing/dev
    DATABASE_URL: str = "sqlite+aiosqlite:///./offercheck.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security & Limits
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    MAX_PAYLOAD_BYTES: int = 200 * 1024  # 200 KB cap per specification
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # External APIs (optional in dev)
    GOOGLE_SAFE_BROWSING_API_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Rules YAML path
    RULES_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules.yaml")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
