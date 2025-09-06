from celery import Celery
from .config import settings

# Create Celery instance
celery_app = Celery(
    "neetimanthan",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.services.coordinator",
        "app.services.processing",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
