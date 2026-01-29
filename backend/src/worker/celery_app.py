import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "markpdfdown_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Be careful with prefetch in long running tasks
    worker_prefetch_multiplier=1
)

celery_app.autodiscover_tasks(["src.worker.tasks"])
