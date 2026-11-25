"""Celery application configuration for asynchronous background tasks."""
import os
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "offercheck_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.app.tasks.domain_intel",
        "backend.app.tasks.link_scan",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,  # 30 seconds max for network tasks
    worker_prefetch_multiplier=1,
)
