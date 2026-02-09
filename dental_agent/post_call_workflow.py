"""
post_call_workflow.py - Automated Post-Call Actions

This is where the magic happens. After every call:
1. Analyze the call (sentiment, quality, outcome)
2. Send appropriate follow-up SMS
3. Update analytics
4. Trigger reminders if appointment was booked
5. Alert staff if intervention needed

This automation is what makes AI receptionists 10x more valuable
than just answering calls.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from call_analytics import (
    analyze_call_transcript,
    CallAnalysis,
    CallOutcome,
    Sentiment,
)
from twilio_service import (
    send_post_call_followup,
    send_appointment_confirmation,
    send_appointment_reminder,
    send_review_request,
)

logger = logging.getLogger(__name__)


class FollowUpAction(str, Enum):
    """Possible follow-up actions after a call."""
    SEND_CONFIRMATION = "send_confirmation"
    SEND_FOLLOWUP = "send_followup"
    SCHEDULE_REMINDER = "schedule_reminder"
    REQUEST_REVIEW = "request_review"
    ALERT_STAFF = "alert_staff"
    CALL_BACK = "call_back"
    NO_ACTION = "no_action"


@dataclass
class PostCallResult:
    """Result of post-call workflow."""
    call_id: str
    analysis: CallAnalysis
    actions_taken: list
    errors: list
    next_scheduled_action: Optional[Dict[str, Any]] = None


async def run_post_call_workflow(
    call_id: str,
    transcript: str,
    duration_seconds: int,
    caller_phone: str,
    caller_name: Optional[str] = None,
    clinic_name: str = "the clinic",
    clinic_phone: Optional[str] = None,
    review_link: Optional[str] = None,
) -> PostCallResult:
    """
    Run the complete post-call automation workflow.
    
    This is called automatically when a call ends.
    
    Args:
        call_id: Unique call identifier
        transcript: Full conversation transcript
        duration_seconds: Call duration
        caller_phone: Caller's phone number
        caller_name: Caller's name (if captured)
        clinic_name: Name of the dental clinic
        clinic_phone: Clinic's phone number for callbacks
        review_link: Google review link (optional)
    
    Returns:
        PostCallResult with analysis and actions taken
    """
    actions_taken = []
    errors = []
    next_action = None
    
    # Step 1: Analyze the call
    logger.info(f"Analyzing call {call_id}...")
    analysis = analyze_call_transcript(
        transcript=transcript,
        call_id=call_id,
        duration_seconds=duration_seconds,
        clinic_name=clinic_name,
    )
    actions_taken.append({
        "action": "analyze_call",
        "success": True,
        "quality_score": analysis.quality_score,
        "sentiment": analysis.overall_sentiment.value,
        "outcome": analysis.outcome.value,
    })
    
    # Step 2: Determine follow-up actions based on outcome
    patient_name = caller_name or "valued patient"
    
    if analysis.outcome == CallOutcome.APPOINTMENT_BOOKED:
        # Send confirmation immediately
        try:
            appointment = analysis.appointment_details or {}
            confirmation_result = send_appointment_confirmation(
                to_number=caller_phone,
                patient_name=patient_name,
                appointment_date=appointment.get("date", "to be confirmed"),
                appointment_time=appointment.get("time", "to be confirmed"),
                clinic_name=clinic_name,
                clinic_phone=clinic_phone,
            )
            
            actions_taken.append({
                "action": "send_confirmation",
                "success": confirmation_result.get("success", False),
                "message_sid": confirmation_result.get("message_sid"),
            })
            
            # Schedule reminders (would integrate with task scheduler in production)
            next_action = {
                "action": "send_reminder",
                "scheduled_for": "24 hours before appointment",
                "patient_name": patient_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to send confirmation: {e}")
            errors.append({"action": "send_confirmation", "error": "SMS delivery failed"})
            
    elif analysis.outcome in [CallOutcome.QUESTION_ANSWERED, CallOutcome.UNKNOWN]:
        # Send thank-you follow-up
        try:
            followup_result = send_post_call_followup(
                to_number=caller_phone,
                patient_name=patient_name,
                clinic_name=clinic_name,
                appointment_booked=False,
            )
            
            actions_taken.append({
                "action": "send_followup",
                "success": followup_result.get("success", False),
                "message_sid": followup_result.get("message_sid"),
            })
            
        except Exception as e:
            logger.error(f"Failed to send followup: {e}")
            errors.append({"action": "send_followup", "error": "SMS delivery failed"})
    
    # Step 3: Handle sentiment-based actions
    if analysis.overall_sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE, Sentiment.FRUSTRATED]:
        # Alert staff for potential issue
        actions_taken.append({
            "action": "alert_staff",
            "reason": "Negative caller sentiment detected",
            "sentiment": analysis.overall_sentiment.value,
            "quality_issues": analysis.quality_issues,
        })
        logger.warning(f"Call {call_id}: Negative sentiment detected - staff alert triggered")
    
    # Step 4: Request review for positive calls (but not immediately)
    if (
        analysis.overall_sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE] and
        analysis.outcome == CallOutcome.APPOINTMENT_BOOKED and
        review_link
    ):
        # Schedule review request for after the appointment
        next_action = next_action or {}
        next_action["review_request"] = {
            "action": "request_review",
            "scheduled_for": "2 hours after appointment",
            "phone": caller_phone,
            "review_link": review_link,
        }
    
    # Step 5: Handle quality issues
    if analysis.quality_score < 60:
        actions_taken.append({
            "action": "quality_alert",
            "reason": f"Low quality score: {analysis.quality_score}",
            "issues": analysis.quality_issues,
            "recommendation": "Review call recording and adjust AI prompts",
        })
    
    # Step 6: Log action items for human follow-up
    if analysis.action_items:
        actions_taken.append({
            "action": "log_action_items",
            "items": analysis.action_items,
        })
    
    return PostCallResult(
        call_id=call_id,
        analysis=analysis,
        actions_taken=actions_taken,
        errors=errors,
        next_scheduled_action=next_action,
    )


def determine_sms_timing(outcome: CallOutcome, sentiment: Sentiment) -> Dict[str, Any]:
    """
    Determine optimal timing for follow-up SMS based on call outcome.
    
    Best practices from research:
    - Confirmation: Immediately
    - Reminder: 24h and 2h before
    - Review request: 1-2h after appointment
    - Recall: 6 months after last visit
    """
    timing = {
        "confirmation": "immediate",
        "reminder_24h": True,
        "reminder_2h": True,
        "review_request": "2_hours_after_appointment",
    }
    
    # Adjust based on sentiment
    if sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
        # Don't ask for review if experience was bad
        timing["review_request"] = None
    
    return timing


def get_automated_workflow_stats() -> Dict[str, Any]:
    """
    Get statistics about automated workflow performance.
    
    Track:
    - How many confirmations sent
    - How many reminders reduced no-shows
    - How many reviews generated
    """
    # In production, query database
    return {
        "today": {
            "confirmations_sent": 0,
            "reminders_sent": 0,
            "followups_sent": 0,
            "reviews_requested": 0,
            "staff_alerts": 0,
        },
        "this_week": {
            "confirmations_sent": 0,
            "reminders_sent": 0,
            "followups_sent": 0,
            "reviews_requested": 0,
            "staff_alerts": 0,
        },
        "conversion_impact": {
            "no_show_reduction": "0%",
            "reviews_generated": 0,
            "patients_retained": 0,
        }
    }


# =============================================================================
# Reminder Scheduler (would use Celery/Redis in production)
# =============================================================================

async def schedule_appointment_reminder(
    phone: str,
    patient_name: str,
    appointment_datetime: datetime,
    clinic_name: str,
    reminder_hours: list = [24, 2],
) -> Dict[str, Any]:
    """
    Schedule appointment reminders.
    
    In production, this would:
    1. Calculate reminder times
    2. Create Celery tasks
    3. Store in database for tracking
    """
    scheduled = []
    
    for hours in reminder_hours:
        reminder_time = appointment_datetime - timedelta(hours=hours)
        
        scheduled.append({
            "reminder_type": f"{hours}h_before",
            "scheduled_for": reminder_time.isoformat(),
            "phone": phone,
            "patient_name": patient_name,
            "clinic_name": clinic_name,
        })
        
        logger.info(f"Scheduled {hours}h reminder for {patient_name} at {reminder_time}")
    
    return {
        "success": True,
        "reminders_scheduled": len(scheduled),
        "schedule": scheduled,
    }


async def process_scheduled_reminders():
    """
    Process due reminders.
    
    Called periodically (every minute) by task scheduler.
    Finds reminders that are due and sends them.
    """
    # In production, query database for due reminders
    # and send SMS via send_appointment_reminder()
    pass
