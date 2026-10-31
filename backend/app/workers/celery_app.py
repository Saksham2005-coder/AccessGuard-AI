"""Celery application configuration with Redis broker and JSON serialization."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "accessguard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=settings.SCAN_TOTAL_TIMEOUT_SECONDS + 30,
    task_soft_time_limit=settings.SCAN_TOTAL_TIMEOUT_SECONDS,
)
