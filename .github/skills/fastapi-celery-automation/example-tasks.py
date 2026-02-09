"""
example-tasks.py - Celery Task Patterns for DentSignal

Copy these patterns when creating new background tasks.
All tasks use exponential backoff retry with max 3 attempts.
"""

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERN 1: Simple Task with Retry
# =============================================================================

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_sms_reminder(self, patient_id: int, appointment_id: int, message_type: str):
    """
    Send SMS reminder to patient.
    
    Args:
        patient_id: Database ID of patient
        appointment_id: Appointment to remind about
        message_type: "confirmation", "24h", "2h", "followup"
    """
    logger.info(f"Sending {message_type} SMS for appointment {appointment_id}")
    
    try:
        patient = get_patient(patient_id)
        appointment = get_appointment(appointment_id)
        
        message = build_reminder_message(message_type, patient, appointment)
        result = twilio_client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=patient.phone  # lgtm[py/clear-text-logging-sensitive-data]
        )
        
        # Log success
        log_sms_sent(patient_id, appointment_id, result.sid)
        return {"success": True, "sid": result.sid}
        
    except TwilioRestException as e:
        logger.error(f"Twilio error: {e}")
        raise self.retry(exc=e)


# =============================================================================
# PATTERN 2: Task with Custom Retry Delays
# =============================================================================

CUSTOM_RETRY_DELAYS = {
    1: 15 * 60,      # 15 minutes
    2: 2 * 60 * 60,  # 2 hours
    3: 24 * 60 * 60, # 24 hours
}

@celery_app.task(bind=True, max_retries=3)
def make_outbound_call(self, lead_id: int):
    """
    Initiate outbound call with custom retry schedule.
    """
    try:
        lead = get_lead(lead_id)
        result = initiate_call(lead)
        return result
        
    except Exception as e:
        attempt = self.request.retries + 1
        delay = CUSTOM_RETRY_DELAYS.get(attempt, 60)
        
        if attempt >= 3:
            escalate_to_human(lead_id, reason="max_retries_exceeded")
            return {"error": "Escalated to human", "lead_id": lead_id}
            
        raise self.retry(exc=e, countdown=delay)


# =============================================================================
# PATTERN 3: Chained Tasks (Sequential Processing)
# =============================================================================

from celery import chain

def process_completed_call(call_id: int):
    """
    Chain of tasks that run after a call completes.
    Each task passes its result to the next.
    """
    workflow = chain(
        transcribe_call.s(call_id),
        analyze_sentiment.s(),
        generate_summary.s(),
        update_crm.s(),
        send_followup_sms.s()
    )
    return workflow.apply_async()


@celery_app.task
def transcribe_call(call_id: int) -> dict:
    """Step 1: Transcribe the recording."""
    recording_url = get_recording_url(call_id)
    transcript = deepgram_transcribe(recording_url)
    return {"call_id": call_id, "transcript": transcript}


@celery_app.task  
def analyze_sentiment(data: dict) -> dict:
    """Step 2: Analyze sentiment (receives output from step 1)."""
    sentiment = gemini_analyze(data["transcript"])
    data["sentiment"] = sentiment
    return data


@celery_app.task
def generate_summary(data: dict) -> dict:
    """Step 3: Generate call summary."""
    summary = gemini_summarize(data["transcript"])
    data["summary"] = summary
    return data


# =============================================================================
# PATTERN 4: Parallel Tasks (Fan-out)
# =============================================================================

from celery import group

def send_batch_reminders(appointment_ids: list):
    """
    Send reminders to multiple patients in parallel.
    """
    tasks = group([
        send_sms_reminder.s(get_patient_id(apt_id), apt_id, "24h")
        for apt_id in appointment_ids
    ])
    return tasks.apply_async()


# =============================================================================
# PATTERN 5: Scheduled/Periodic Task
# =============================================================================

# In celery_config.py:
# celery_app.conf.beat_schedule = {
#     "morning-reminders": {
#         "task": "tasks.send_morning_reminders",
#         "schedule": crontab(hour=9, minute=0),
#     },
# }

@celery_app.task
def send_morning_reminders():
    """
    Runs daily at 9 AM via Celery Beat.
    Sends 24-hour reminders for tomorrow's appointments.
    """
    tomorrow = datetime.now().date() + timedelta(days=1)
    appointments = get_appointments_for_date(tomorrow)
    
    for apt in appointments:
        send_sms_reminder.delay(apt.patient_id, apt.id, "24h")
    
    logger.info(f"Queued {len(appointments)} reminder SMSes")
    return {"queued": len(appointments)}


# =============================================================================
# PATTERN 6: Task with Rate Limiting
# =============================================================================

@celery_app.task(
    bind=True,
    rate_limit="10/m",  # Max 10 per minute
    max_retries=3,
)
def sync_to_crm(self, patient_id: int, data: dict):
    """
    Sync data to external CRM with rate limiting.
    Prevents overwhelming external API.
    """
    try:
        response = external_crm.update_patient(patient_id, data)
        return {"success": True, "crm_id": response.id}
    except RateLimitError as e:
        raise self.retry(exc=e, countdown=60)


# =============================================================================
# PATTERN 7: Webhook-Triggered Task
# =============================================================================

# In FastAPI route:
# @router.post("/webhook/twilio/status")
# async def twilio_status_webhook(request: Request):
#     data = await request.form()
#     if data.get("CallStatus") == "completed":
#         process_completed_call.delay(data.get("CallSid"))
#     return {"received": True}

@celery_app.task
def process_call_status(call_sid: str, status: str):
    """
    Process Twilio call status webhook.
    Triggered by FastAPI route when status changes.
    """
    call = get_call_by_sid(call_sid)
    
    if status == "completed":
        mark_call_completed(call.id)
        # Trigger post-call workflow
        process_completed_call(call.id)
        
    elif status == "failed":
        handle_failed_call(call.id)
        
    elif status == "no-answer":
        schedule_retry(call.lead_id)
