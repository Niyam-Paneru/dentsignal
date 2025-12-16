"""
celery_config.py - Celery Application Setup

Uses Redis as broker and result backend.
Configures exponential backoff retries with max 3 attempts.

Redis FREE options:
- Local: docker run -d -p 6379:6379 redis
- Upstash: https://upstash.com (10K commands/day free)
- Railway: https://railway.app ($5 free credit)
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis configuration - defaults to local Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "dental_agent",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["dental_agent.tasks"],  # Auto-discover tasks
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completes (safer)
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # One task at a time per worker
    
    # Result expiration (24 hours)
    result_expires=86400,
    
    # Default retry policy (exponential backoff)
    task_default_retry_delay=60,  # 1 minute initial
    task_max_retries=3,
    
    # Rate limiting (prevent overwhelming Twilio)
    task_annotations={
        "dental_agent.tasks.start_call": {
            "rate_limit": "10/m"  # Max 10 calls per minute
        },
        "dental_agent.tasks.retry_call": {
            "rate_limit": "5/m"  # Max 5 retries per minute
        },
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "daily-billing-summary": {
            "task": "dental_agent.tasks.daily_billing_summary",
            "schedule": 86400.0,  # Every 24 hours (in seconds)
            # Or use crontab: schedule=crontab(hour=0, minute=0)
        },
    },
)

# Optional: Configure task routes for different queues
celery_app.conf.task_routes = {
    "dental_agent.tasks.start_call": {"queue": "calls"},
    "dental_agent.tasks.retry_call": {"queue": "calls"},
    "dental_agent.tasks.daily_billing_summary": {"queue": "billing"},
}


if __name__ == "__main__":
    celery_app.start()
