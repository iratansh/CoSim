"""Celery application bootstrap for asynchronous tasks.

This lightweight module ensures that the Docker Compose worker
(`celery -A celery_app worker`) can start successfully even if no
tasks have been implemented yet. Projects can add real tasks by
importing `celery_app.celery` and registering them via the
`@celery.task` decorator.
"""

from __future__ import annotations

from celery import Celery

from core.config import get_settings


settings = get_settings()


celery = Celery(
    "codegenius",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Basic, secure defaults; extend as needed per project requirements.
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Ensure task modules are registered when the worker starts.
celery.autodiscover_tasks(['tasks', 'backend.tasks'], force=True)


@celery.task(name="codegenius.health_check")
def health_check() -> str:
    """Simple task to verify Celery worker wiring."""
    return "ok"


__all__ = ["celery", "health_check"]
