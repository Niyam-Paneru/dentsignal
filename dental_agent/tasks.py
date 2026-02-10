"""
tasks.py - Celery Background Tasks

Handles:
- start_call: Initiate calls to leads via Twilio
- retry_call: Retry failed calls with exponential backoff
- daily_billing_summary: Daily billing report generation

Now with REAL Twilio integration!
"""

import csv
import io
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from sqlmodel import Session, select
from dotenv import load_dotenv

load_dotenv()

try:
    from dental_agent.celery_config import celery_app
    from dental_agent.db import get_session, Lead, Call, CallResult, CallStatus, CallResultType
    from dental_agent.twilio_service import make_call, verify_twilio_credentials
    from dental_agent.utils import mask_phone
except ImportError:
    from celery_config import celery_app
    from db import get_session, Lead, Call, CallResult, CallStatus, CallResultType
    from twilio_service import make_call, verify_twilio_credentials
    from utils import mask_phone

logger = logging.getLogger(__name__)

# Get API base URL for webhooks
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")  # DevSkim: ignore DS137138 - localhost fallback for dev only

# =============================================================================
# RETRY DELAYS (exponential backoff)
# =============================================================================
RETRY_DELAYS = {
    1: 15 * 60,       # Attempt 1 failed → wait 15 minutes
    2: 2 * 60 * 60,   # Attempt 2 failed → wait 2 hours
    3: 24 * 60 * 60,  # Attempt 3 failed → wait 24 hours (then escalate)
}


# =============================================================================
# DATABASE FUNCTIONS - Real implementations
# =============================================================================

def get_lead_by_id(lead_id: int) -> Optional[dict]:
    """Fetch lead from database."""
    try:
        with get_session() as session:
            lead = session.get(Lead, lead_id)
            if lead:
                return {
                    "id": lead.id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "email": lead.email,
                    "batch_id": lead.batch_id,
                    "consent": lead.consent,  # Include consent field
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        return None


def get_call_by_id(call_id: int) -> Optional[dict]:
    """Fetch call from database."""
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                return {
                    "id": call.id,
                    "lead_id": call.lead_id,
                    "status": call.status,
                    "attempt": call.attempt,
                    "twilio_sid": call.twilio_sid if hasattr(call, 'twilio_sid') else None,
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching call {call_id}: {e}")
        return None


def initiate_call(lead: dict, call_id: int) -> dict:
    """Trigger a call via Twilio."""
    logger.info(f"Initiating Twilio call to {mask_phone(lead['phone'])} for lead {lead['id']}")
    
    result = make_call(
        to_number=lead["phone"],
        lead_id=lead["id"],
        call_id=call_id,
        webhook_base_url=API_BASE_URL,
    )
    
    if result.get("success"):
        # Update call record with Twilio SID
        try:
            with get_session() as session:
                call = session.get(Call, call_id)
                if call:
                    call.twilio_sid = result.get("call_sid")
                    call.status = CallStatus.IN_PROGRESS
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating call with Twilio SID: {e}")
    
    return result


def escalate_lead(lead_id: int) -> None:
    """Mark lead as requiring human follow-up."""
    logger.warning(f"Escalating lead {lead_id} to human follow-up")
    try:
        with get_session() as session:
            lead = session.get(Lead, lead_id)
            if lead:
                lead.notes = (lead.notes or "") + "\n[ESCALATED] Max retries reached - needs human follow-up"
                session.commit()
    except Exception as e:
        logger.error(f"Error escalating lead: {e}")


def get_calls_for_billing(since: datetime) -> list:
    """Get all calls from the last 24 hours for billing."""
    try:
        with get_session() as session:
            calls = session.exec(
                select(Call).where(Call.created_at >= since)
            ).all()
            return [
                {
                    "id": c.id,
                    "duration": 0,  # TODO: Get from Twilio
                    "status": c.status.value if c.status else "unknown",
                    "cost": 0.02,  # Estimated cost per call
                }
                for c in calls
            ]
    except Exception as e:
        logger.error(f"Error fetching calls for billing: {e}")
        return []


def mark_call_completed(call_id: int) -> None:
    """Mark a call as completed in the database."""
    logger.info(f"Marking call {call_id} as completed")
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                call.status = CallStatus.COMPLETED
                call.updated_at = datetime.utcnow()
                session.commit()
    except Exception as e:
        logger.error(f"Error marking call completed: {e}")


def get_lead_id_from_call_sid(call_sid: str) -> Optional[int]:
    """Lookup lead_id from Twilio CallSid."""
    logger.info(f"Looking up lead for CallSid {call_sid}")
    try:
        with get_session() as session:
            call = session.exec(
                select(Call).where(Call.twilio_sid == call_sid)
            ).first()
            if call:
                return call.lead_id
            return None
    except Exception as e:
        logger.error(f"Error looking up call by SID: {e}")
        return None


def get_call_attempt(call_sid: str) -> int:
    """Get current attempt number for a call."""
    try:
        with get_session() as session:
            call = session.exec(
                select(Call).where(Call.twilio_sid == call_sid)
            ).first()
            if call:
                return call.attempt or 1
            return 1
    except Exception as e:
        logger.error(f"Error getting call attempt: {e}")
        return 1


def get_or_create_call_for_lead(lead_id: int, batch_id: Optional[int] = None) -> Optional[int]:
    """Get existing queued call or create new one for lead."""
    try:
        with get_session() as session:
            # Check for existing queued call
            existing = session.exec(
                select(Call).where(
                    Call.lead_id == lead_id,
                    Call.status == CallStatus.QUEUED
                )
            ).first()
            
            if existing:
                return existing.id
            
            # Create new call
            lead = session.get(Lead, lead_id)
            if not lead:
                return None
            
            call = Call(
                lead_id=lead_id,
                batch_id=batch_id or lead.batch_id,
                client_id=1,  # TODO: Get from lead's batch
                status=CallStatus.QUEUED,
                attempt=1,
            )
            session.add(call)
            session.commit()
            session.refresh(call)
            return call.id
    except Exception as e:
        logger.error(f"Error creating call for lead: {e}")
        return None


# =============================================================================
# CELERY TASKS
# =============================================================================

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def start_call(self, lead_id: int, call_id: Optional[int] = None) -> dict:
    """
    Start a call to a lead via Twilio.
    
    Fetches lead from DB, initiates call via Twilio.
    Automatically retries on failure with exponential backoff.
    
    For PSTN calls (TELEPHONY_MODE=TWILIO), consent is REQUIRED.
    
    Args:
        lead_id: Database ID of the lead to call
        call_id: Optional existing call ID (creates new if not provided)
        
    Returns:
        dict with call_sid and status
    """
    logger.info(f"Task start_call: Processing lead {lead_id}")
    
    # Fetch lead from database
    lead = get_lead_by_id(lead_id)
    if not lead:
        logger.error(f"Lead {lead_id} not found")
        return {"error": "Lead not found", "lead_id": lead_id}
    
    # TCPA COMPLIANCE: Check consent for PSTN mode
    telephony_mode = os.getenv("TELEPHONY_MODE", "SIMULATED")
    if telephony_mode == "TWILIO" and not lead.get("consent", False):
        logger.error(f"TCPA BLOCK: Lead {lead_id} does not have consent for PSTN call")
        return {
            "error": "TCPA compliance: consent required for PSTN calls",
            "lead_id": lead_id,
            "consent": False,
        }
    
    # Get or create call record
    if not call_id:
        call_id = get_or_create_call_for_lead(lead_id)
        if not call_id:
            return {"error": "Could not create call record", "lead_id": lead_id}
    
    try:
        # Initiate the call via Twilio
        result = initiate_call(lead, call_id)
        
        if result.get("success"):
            logger.info(f"Call initiated for lead {lead_id}: SID={result.get('call_sid')}")
            return {
                "success": True,
                "lead_id": lead_id,
                "call_id": call_id,
                "call_sid": result.get("call_sid"),
                "status": result.get("status"),
            }
        else:
            logger.error(f"Twilio call failed: {result.get('error')}")
            raise Exception(result.get("error", "Unknown Twilio error"))
            
    except Exception as exc:
        logger.error(f"Failed to initiate call for lead {lead_id}: {exc}")
        # Celery will auto-retry due to autoretry_for=(Exception,)
        raise


@celery_app.task(bind=True)
def retry_call(self, lead_id: int, attempt: int) -> dict:
    """
    Retry a failed call with exponential backoff.
    
    Delay schedule:
    - Attempt 1 failed → wait 15 minutes
    - Attempt 2 failed → wait 2 hours  
    - Attempt 3 failed → wait 24 hours, then escalate
    
    Args:
        lead_id: Database ID of the lead
        attempt: Current attempt number (1, 2, or 3)
        
    Returns:
        dict with retry status
    """
    logger.info(f"Task retry_call: Lead {lead_id}, attempt {attempt}")
    
    if attempt > 3:
        # Max retries exceeded - escalate to human
        logger.warning(f"Max retries exceeded for lead {lead_id}, escalating")
        escalate_lead(lead_id)
        return {
            "success": False,
            "lead_id": lead_id,
            "action": "escalated_to_human",
            "attempts": attempt,
        }
    
    # Get retry delay for this attempt
    delay_seconds = RETRY_DELAYS.get(attempt, 15 * 60)
    
    # Schedule the actual call
    logger.info(f"Scheduling retry for lead {lead_id} in {delay_seconds}s (attempt {attempt})")
    
    # Use countdown to delay the next attempt
    start_call.apply_async(
        args=[lead_id],
        countdown=delay_seconds,
        kwargs={"attempt": attempt},
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "action": "retry_scheduled",
        "attempt": attempt,
        "delay_seconds": delay_seconds,
    }


@celery_app.task
def daily_billing_summary() -> dict:
    """
    Generate daily billing summary.
    
    Runs once per day (configured in celery_config.py beat_schedule).
    Aggregates call data and generates CSV report.
    
    Returns:
        dict with summary statistics
    """
    logger.info("Task daily_billing_summary: Starting daily billing run")
    
    # Get calls from last 24 hours
    since = datetime.utcnow() - timedelta(hours=24)
    calls = get_calls_for_billing(since)
    
    if not calls:
        logger.info("No calls to bill for the last 24 hours")
        return {"success": True, "total_calls": 0, "total_cost": 0}
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "duration", "status", "cost"])
    writer.writeheader()
    writer.writerows(calls)
    csv_content = output.getvalue()
    
    # Calculate totals
    total_calls = len(calls)
    total_duration = sum(c.get("duration", 0) for c in calls)
    total_cost = sum(c.get("cost", 0) for c in calls)
    
    # Log summary (in production, send to billing system)
    logger.info(f"Daily Billing Summary:")
    logger.info(f"  Total Calls: {total_calls}")
    logger.info(f"  Total Duration: {total_duration} seconds")
    logger.info(f"  Total Cost: ${total_cost:.2f}")
    logger.info(f"  CSV Report:\n{csv_content}")
    
    return {
        "success": True,
        "total_calls": total_calls,
        "total_duration": total_duration,
        "total_cost": total_cost,
        "csv_preview": csv_content[:500],  # First 500 chars
    }


@celery_app.task
def process_call_result(call_id: int, lead_id: int, status: str, attempt: int) -> dict:
    """
    Process a call result and decide next action.
    
    Called by the /calls/{call_id}/result endpoint.
    
    Args:
        call_id: Database ID of the call
        lead_id: Database ID of the lead
        status: Call result status (completed, no-answer, failed)
        attempt: Current attempt number
        
    Returns:
        dict with action taken
    """
    logger.info(f"Processing call result: call={call_id}, status={status}, attempt={attempt}")
    
    if status == "completed":
        mark_call_completed(call_id)
        return {
            "success": True,
            "action": "completed",
            "call_id": call_id,
        }
    
    elif status in ("no-answer", "failed", "busy"):
        if attempt < 3:
            # Schedule retry
            retry_call.delay(lead_id, attempt + 1)
            return {
                "success": True,
                "action": "retry_scheduled",
                "call_id": call_id,
                "next_attempt": attempt + 1,
            }
        else:
            # Escalate after 3 attempts
            escalate_lead(lead_id)
            return {
                "success": True,
                "action": "escalated",
                "call_id": call_id,
            }
    
    else:
        logger.warning(f"Unknown call status: {status}")
        return {
            "success": False,
            "action": "unknown_status",
            "status": status,
        }
