from celery import Celery
import os

import ssl

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if redis_url.startswith("rediss://"):
    celery_app = Celery(__name__, broker=redis_url, backend=redis_url)
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE}
    )
else:
    celery_app = Celery(__name__, broker=redis_url, backend=redis_url)
    celery_app.conf.update(
        task_serializer="json", 
        accept_content=["json"], 
        result_serializer="json"
    )
