"""
celery-config-reference.py - Celery Configuration for DentSignal

This is the reference configuration for the dental voice agent.
Copy/adapt settings as needed for your deployment.
"""

import os
from celery import Celery
from celery.schedules import crontab

# =============================================================================
# REDIS CONNECTION
# =============================================================================

# Options:
# - Local Docker: redis://localhost:6379/0
# - Upstash (free tier): redis://default:xxx@xxx.upstash.io:6379
# - Railway: redis://default:xxx@xxx.railway.app:6379
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# =============================================================================
# CELERY APP INITIALIZATION
# =============================================================================

celery_app = Celery(
    "dental_agent",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "dental_agent.tasks",
        "dental_agent.post_call_workflow",
    ],
)


# =============================================================================
# SERIALIZATION & CONTENT
# =============================================================================

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# =============================================================================
# TASK EXECUTION SETTINGS
# =============================================================================

celery_app.conf.update(
    # Acknowledge after task completes (prevents loss on crash)
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # One task at a time per worker (fair distribution)
    worker_prefetch_multiplier=1,
    
    # Task result expiration (24 hours)
    result_expires=86400,
    
    # Default retry policy
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Timeouts
    task_time_limit=300,        # 5 min hard limit
    task_soft_time_limit=240,   # 4 min soft limit
)


# =============================================================================
# RATE LIMITING
# =============================================================================

celery_app.conf.task_annotations = {
    # Outbound calls: max 10 per minute (prevent Twilio rate limits)
    "dental_agent.tasks.start_call": {
        "rate_limit": "10/m"
    },
    "dental_agent.tasks.retry_call": {
        "rate_limit": "5/m"
    },
    
    # SMS: max 60 per minute
    "dental_agent.tasks.send_sms_reminder": {
        "rate_limit": "60/m"
    },
    
    # External API sync: max 30 per minute
    "dental_agent.tasks.sync_to_crm": {
        "rate_limit": "30/m"
    },
}


# =============================================================================
# TASK ROUTING (Separate Queues)
# =============================================================================

celery_app.conf.task_routes = {
    # High priority: voice calls
    "dental_agent.tasks.start_call": {"queue": "calls"},
    "dental_agent.tasks.retry_call": {"queue": "calls"},
    
    # Medium priority: SMS
    "dental_agent.tasks.send_sms_*": {"queue": "sms"},
    
    # Low priority: analytics/billing
    "dental_agent.tasks.daily_billing_summary": {"queue": "billing"},
    "dental_agent.post_call_workflow.*": {"queue": "analytics"},
}

# Run workers for specific queues:
# celery -A celery_config worker -Q calls --concurrency=2
# celery -A celery_config worker -Q sms --concurrency=4
# celery -A celery_config worker -Q analytics --concurrency=1


# =============================================================================
# SCHEDULED TASKS (Celery Beat)
# =============================================================================

celery_app.conf.beat_schedule = {
    # Daily billing summary at midnight UTC
    "daily-billing-summary": {
        "task": "dental_agent.tasks.daily_billing_summary",
        "schedule": crontab(hour=0, minute=0),
    },
    
    # Morning appointment reminders (9 AM local)
    "morning-reminders": {
        "task": "dental_agent.tasks.send_morning_reminders",
        "schedule": crontab(hour=14, minute=0),  # 9 AM EST = 14:00 UTC
    },
    
    # 2-hour reminders (check every 30 min)
    "two-hour-reminders": {
        "task": "dental_agent.tasks.send_two_hour_reminders",
        "schedule": crontab(minute="0,30"),
    },
    
    # Nightly analytics processing (2 AM)
    "nightly-analytics": {
        "task": "dental_agent.post_call_workflow.process_daily_analytics",
        "schedule": crontab(hour=7, minute=0),  # 2 AM EST = 7:00 UTC
    },
}


# =============================================================================
# WORKER CONFIGURATION
# =============================================================================

celery_app.conf.update(
    # Worker pool settings
    worker_pool="prefork",  # Use "solo" on Windows for dev
    worker_concurrency=4,   # Number of worker processes
    
    # Max tasks before worker restarts (prevent memory leaks)
    worker_max_tasks_per_child=1000,
    
    # Logging
    worker_hijack_root_logger=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)


# =============================================================================
# COMMANDS REFERENCE
# =============================================================================

"""
# Start Redis (Docker)
docker run -d -p 6379:6379 --name redis redis:alpine

# Start Celery Worker (Development - Windows)
celery -A celery_config worker --loglevel=info --pool=solo

# Start Celery Worker (Production - Linux)
celery -A celery_config worker --loglevel=info --concurrency=4

# Start Celery Beat (Scheduler)
celery -A celery_config beat --loglevel=info

# Start Both Worker + Beat (Combined)
celery -A celery_config worker --beat --loglevel=info

# Monitor Tasks
celery -A celery_config events
celery -A celery_config flower  # Web UI (requires flower package)

# Inspect Workers
celery -A celery_config inspect ping
celery -A celery_config inspect active
celery -A celery_config inspect registered
celery -A celery_config inspect scheduled

# Purge Queues (careful!)
celery -A celery_config purge
"""
