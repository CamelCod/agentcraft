from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "youtube_kg",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.discovery",
        "app.workers.tasks.ingestion",
        "app.workers.tasks.extraction",
        "app.workers.tasks.verification",
        "app.workers.tasks.reporting",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.ingestion.*": {"queue": "ingestion"},
        "app.workers.tasks.extraction.*": {"queue": "extraction"},
        "app.workers.tasks.verification.*": {"queue": "verification"},
        "app.workers.tasks.reporting.*": {"queue": "reporting"},
        "app.workers.tasks.discovery.*": {"queue": "discovery"},
    },
    task_default_queue="default",
    beat_schedule={
        "backup-postgres-daily": {
            "task": "app.workers.tasks.discovery.health_check",
            "schedule": 3600.0,  # every hour
        },
    },
)
