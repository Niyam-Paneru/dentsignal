"""
routes_sms.py - SMS & Patient Engagement API Routes

Endpoints for:
- Sending SMS messages (confirmations, reminders, follow-ups)
- Managing SMS templates
- Viewing SMS history
- Automated reminder scheduling
- Inbound SMS webhook for patient responses (No-Show Reduction)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Form, Request
from pydantic import BaseModel, Field

from twilio_service import (
    send_sms,
    send_appointment_confirmation,
    send_appointment_reminder,
    send_post_call_followup,
    send_recall_reminder,
    send_review_request,
)
from utils import mask_phone

try:
    from tasks_reminder import handle_patient_sms_response
except ImportError:
    from dental_agent.tasks_reminder import handle_patient_sms_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sms", tags=["SMS & Messaging"])


# =============================================================================
# Pydantic Models
# =============================================================================

class SMSRequest(BaseModel):
    """Generic SMS request."""
    to_number: str = Field(..., description="Phone number in E.164 format (+1XXXXXXXXXX)")
    message: str = Field(..., max_length=1600)
    
    
class AppointmentConfirmationRequest(BaseModel):
    """Appointment confirmation SMS request."""
    to_number: str
    patient_name: str
    appointment_date: str = Field(..., json_schema_extra={"example": "Monday, December 16th"})
    appointment_time: str = Field(..., json_schema_extra={"example": "2:30 PM"})
    clinic_name: str
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None


class AppointmentReminderRequest(BaseModel):
    """Appointment reminder SMS request."""
    to_number: str
    patient_name: str
    appointment_date: str
    appointment_time: str
    clinic_name: str
    hours_until: int = Field(default=24, ge=1, le=72)


class PostCallFollowupRequest(BaseModel):
    """Post-call follow-up SMS request."""
    to_number: str
    patient_name: str
    clinic_name: str
    appointment_booked: bool = False
    appointment_details: Optional[str] = None


class RecallReminderRequest(BaseModel):
    """Patient recall reminder request."""
    to_number: str
    patient_name: str
    clinic_name: str
    last_visit_months: int = 6


class ReviewRequestPayload(BaseModel):
    """Review request SMS."""
    to_number: str
    patient_name: str
    clinic_name: str
    review_link: str = Field(..., description="Google review link or similar")


class SMSResponse(BaseModel):
    """Standard SMS response."""
    success: bool
    message_sid: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Routes
# =============================================================================

@router.post("/send", response_model=SMSResponse)
async def send_generic_sms(request: SMSRequest):
    """
    Send a custom SMS message.
    
    Use this for one-off messages. For standard messages, use the 
    dedicated endpoints (confirmation, reminder, etc.)
    """
    result = send_sms(request.to_number, request.message)
    return SMSResponse(**result)


@router.post("/confirmation", response_model=SMSResponse)
async def send_confirmation_sms(request: AppointmentConfirmationRequest):
    """
    Send appointment confirmation SMS.
    
    This should be sent immediately after booking an appointment.
    Patients love instant confirmation - it reduces anxiety and no-shows.
    """
    result = send_appointment_confirmation(
        to_number=request.to_number,
        patient_name=request.patient_name,
        appointment_date=request.appointment_date,
        appointment_time=request.appointment_time,
        clinic_name=request.clinic_name,
        clinic_address=request.clinic_address,
        clinic_phone=request.clinic_phone,
    )
    return SMSResponse(**result)


@router.post("/reminder", response_model=SMSResponse)
async def send_reminder_sms(request: AppointmentReminderRequest):
    """
    Send appointment reminder SMS.
    
    Best practice:
    - Send 24 hours before appointment
    - Send 2 hours before appointment
    
    Reduces no-shows by 30-50%.
    """
    result = send_appointment_reminder(
        to_number=request.to_number,
        patient_name=request.patient_name,
        appointment_date=request.appointment_date,
        appointment_time=request.appointment_time,
        clinic_name=request.clinic_name,
        hours_until=request.hours_until,
    )
    return SMSResponse(**result)


@router.post("/followup", response_model=SMSResponse)
async def send_followup_sms(request: PostCallFollowupRequest):
    """
    Send post-call follow-up SMS.
    
    Send this after every call to:
    - Confirm appointment details (if booked)
    - Keep the door open (if not booked)
    
    Increases patient satisfaction and conversion.
    """
    result = send_post_call_followup(
        to_number=request.to_number,
        patient_name=request.patient_name,
        clinic_name=request.clinic_name,
        appointment_booked=request.appointment_booked,
        appointment_details=request.appointment_details,
    )
    return SMSResponse(**result)


@router.post("/recall", response_model=SMSResponse)
async def send_recall_sms(request: RecallReminderRequest):
    """
    Send patient recall reminder.
    
    Perfect for:
    - 6-month checkup reminders
    - Annual exam reminders
    - Patients who haven't visited in a while
    
    Drives recurring revenue - most patients forget without reminders.
    """
    result = send_recall_reminder(
        to_number=request.to_number,
        patient_name=request.patient_name,
        clinic_name=request.clinic_name,
        last_visit_months=request.last_visit_months,
    )
    return SMSResponse(**result)


@router.post("/review-request", response_model=SMSResponse)
async def send_review_sms(request: ReviewRequestPayload):
    """
    Send review request SMS.
    
    Best practice:
    - Send 1-2 hours after appointment
    - Only send to patients who had a good experience
    - Don't over-ask (max 1x per patient per 6 months)
    
    5-star reviews are marketing gold.
    """
    result = send_review_request(
        to_number=request.to_number,
        patient_name=request.patient_name,
        clinic_name=request.clinic_name,
        review_link=request.review_link,
    )
    return SMSResponse(**result)


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkRecallRequest(BaseModel):
    """Request to send recall reminders to multiple patients."""
    clinic_name: str
    patients: List[dict] = Field(
        ..., 
        description="List of {to_number, patient_name, last_visit_months}"
    )


@router.post("/bulk/recall", response_model=dict)
async def send_bulk_recall(request: BulkRecallRequest, background_tasks: BackgroundTasks):
    """
    Send recall reminders to multiple patients.
    
    This runs in the background and returns immediately.
    Check the dashboard for results.
    """
    async def send_recalls():
        results = {"sent": 0, "failed": 0, "errors": []}
        for patient in request.patients:
            result = send_recall_reminder(
                to_number=patient["to_number"],
                patient_name=patient["patient_name"],
                clinic_name=request.clinic_name,
                last_visit_months=patient.get("last_visit_months", 6),
            )
            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "patient": patient["patient_name"],
                    "error": result.get("error"),
                })
        logger.info(f"Bulk recall complete: sent={results['sent']} failed={results['failed']}")
    
    background_tasks.add_task(send_recalls)
    
    return {
        "status": "processing",
        "message": f"Sending {len(request.patients)} recall reminders in background",
    }


# =============================================================================
# SMS Templates (for future customization)
# =============================================================================

DEFAULT_TEMPLATES = {
    "confirmation": """✅ Appointment Confirmed!

Hi {patient_name}!

Your appointment at {clinic_name} is scheduled for:
📅 {appointment_date}
🕐 {appointment_time}

Reply CONFIRM to confirm or RESCHEDULE to change.""",

    "reminder_24h": """⏰ Reminder: Your dental appointment is tomorrow!

Hi {patient_name},

📅 {appointment_date} at {appointment_time}
🏥 {clinic_name}

Please arrive 10 minutes early.

Reply C to confirm or R to reschedule.""",

    "reminder_2h": """⏰ Your appointment is in 2 hours!

Hi {patient_name},

📅 Today at {appointment_time}
🏥 {clinic_name}

We'll see you soon! 😊""",

    "post_call_booked": """Thanks for calling {clinic_name}, {patient_name}! 😊

Your appointment is confirmed:
{appointment_details}

We look forward to seeing you!""",

    "post_call_not_booked": """Thanks for calling {clinic_name}, {patient_name}!

We're here whenever you're ready to schedule. 

📞 Call back anytime or reply BOOK to schedule.""",

    "recall": """Hi {patient_name}! 👋

It's been {last_visit_months} months since your last visit to {clinic_name}.

Time for your routine checkup!

📞 Reply BOOK or call us to schedule.""",

    "review_request": """Hi {patient_name}!

Thank you for visiting {clinic_name} today!

Would you take 30 seconds to leave us a review?

⭐ {review_link}

Thanks so much!""",
}


@router.get("/templates")
async def get_sms_templates():
    """
    Get all available SMS templates.
    
    These can be customized per clinic in the future.
    """
    return {
        "templates": [
            {"id": k, "content": v, "variables": _extract_variables(v)}
            for k, v in DEFAULT_TEMPLATES.items()
        ]
    }


# =============================================================================
# Inbound SMS Webhook (No-Show Reduction)
# =============================================================================

@router.post("/inbound")
async def inbound_sms_webhook(
    request: Request,
    From: str = Form(None),
    To: str = Form(None),
    Body: str = Form(None),
):
    """
    Twilio webhook for incoming SMS messages.
    
    Processes patient responses to appointment reminders:
    - YES/CONFIRM → Mark appointment confirmed
    - NO/RESCHEDULE → Flag for follow-up
    - BOOK → Provide booking info
    
    Configure this URL in Twilio Console:
    Messaging > Phone Number > Messaging Configuration > Webhook URL
    
    Set to: https://your-domain.com/api/sms/inbound (POST)
    """
    # Handle both Form data and JSON
    if From is None or Body is None:
        try:
            form_data = await request.form()
            From = form_data.get("From", "")
            To = form_data.get("To", "")
            Body = form_data.get("Body", "")
        except:
            pass
    
    if not From or not Body:
        logger.warning("Inbound SMS missing From or Body")
        return {"status": "error", "message": "Missing required fields"}
    
    logger.info("Inbound SMS received")
    
    # Process the response
    result = handle_patient_sms_response(
        from_number=From,
        message_body=Body,
    )
    
    # Send response SMS if we have one
    if result.get("response"):
        try:
            send_sms(From, result["response"])
            result["response_sent"] = True
        except Exception:
            logger.error("Failed to send response SMS")
            result["response_sent"] = False
    
    logger.info(f"Inbound SMS processed: {result.get('action', 'unknown')}")
    
    # Return TwiML response (empty is fine - we send response via API)
    return {
        "status": "success",
        "intent": result.get("intent"),
        "action": result.get("action"),
        "appointment_id": result.get("appointment_id"),
    }


class AppointmentConfirmationStatusRequest(BaseModel):
    """Request to get confirmation status."""
    appointment_id: int


@router.get("/appointments/{appointment_id}/confirmation-status")
async def get_appointment_confirmation_status(appointment_id: int):
    """
    Get the confirmation status of an appointment.
    
    Returns the current SMS sequence step and confirmation status.
    """
    try:
        from db import get_session, Appointment
    except ImportError:
        from dental_agent.db import get_session, Appointment
    
    with get_session() as session:
        appointment = session.get(Appointment, appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "appointment_id": appointment_id,
            "confirmation_status": appointment.confirmation_status,
            "sms_sequence_step": appointment.sms_sequence_step,
            "confirmation_sent": appointment.confirmation_sent,
            "reminder_24h_sent": appointment.reminder_24h_sent,
            "reminder_2h_sent": appointment.reminder_2h_sent,
            "last_sms_sent_at": appointment.last_sms_sent_at.isoformat() if appointment.last_sms_sent_at else None,
            "patient_response": appointment.patient_response,
            "escalation_needed": appointment.escalation_needed,
            "confirmed_at": appointment.confirmed_at.isoformat() if appointment.confirmed_at else None,
        }


def _extract_variables(template: str) -> List[str]:
    """Extract {variable} placeholders from template."""
    import re
    return list(set(re.findall(r'\{(\w+)\}', template)))
