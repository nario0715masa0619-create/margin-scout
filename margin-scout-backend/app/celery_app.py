from celery import Celery
from celery.schedules import crontab
from app.config import settings
import ssl

broker_url = settings.CELERY_BROKER_URL
backend_url = settings.CELERY_RESULT_BACKEND

celery_app = Celery(
    "margin_scout",
    broker=broker_url,
    backend=backend_url,
    include=["app.tasks.scraper_task", "app.tasks.monitoring_tasks"]
)

# Base config
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Production Upstash Redis needs SSL without cert validation
if broker_url.startswith("rediss://"):
    celery_app.conf.update(
        broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE}
    )

celery_app.conf.beat_schedule = {
    "dispatch-due-monitoring-jobs": {
        "task": "app.tasks.monitoring_tasks.dispatch_due_monitoring_jobs",
        "schedule": crontab(minute="*/5"),  # 5分ごと
    },
}
