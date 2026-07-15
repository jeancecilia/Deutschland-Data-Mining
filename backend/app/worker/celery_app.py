from celery import Celery

from app.core.config import get_settings
from app.core.monitoring import configure_monitoring


settings = get_settings()

configure_monitoring()

celery_app = Celery(
    "kdp_deutschland",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_default_queue="default",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "health-heartbeat": {
            "task": "app.worker.tasks.heartbeat",
            "schedule": 300.0,
        },
        "refresh-recent-search-runs": {
            "task": "app.worker.tasks.refresh_recent_search_runs",
            "schedule": 43200.0,
        },
        "refresh-recent-bsr-snapshots": {
            "task": "app.worker.tasks.refresh_recent_bsr_snapshots",
            "schedule": 21600.0,
        },
        "run-discovery-cycle": {
            "task": "app.worker.tasks.run_discovery_cycle",
            "schedule": 86400.0,
        },
        # ── Initial Discovery Pipeline schedules ─────────────────────
        "discovery-import-seeds": {
            "task": "app.worker.tasks.discovery_import_seeds",
            "schedule": 86400.0,  # Daily
        },
        "discovery-full-pipeline": {
            "task": "app.worker.tasks.discovery_full_pipeline",
            "schedule": 43200.0,  # Every 12 hours
        },
    },
)
