"""
Celery configuration for background task processing.
"""

from celery import Celery
from core.config import settings
import structlog

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "legal_intel_dashboard",
    broker=settings.redis_url,  # Use internal URL for container-to-container communication
    backend=settings.redis_url,  # Use internal URL for container-to-container communication
)

# Import tasks to register them
import workers.tasks

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'auto-process-pending-documents': {
        'task': 'workers.tasks.auto_process_pending_documents',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# Use default queue for all tasks
celery_app.conf.task_default_queue = "celery"
celery_app.conf.task_default_exchange = "celery"
celery_app.conf.task_default_routing_key = "celery"

logger.info("Celery app configured successfully") 