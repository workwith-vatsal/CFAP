from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "cfap",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "backend.app.tasks.analysis_tasks",
        "backend.app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max for large dataset inference
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
)
