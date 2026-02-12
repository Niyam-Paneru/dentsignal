"""
tasks_reminder.py - No-Show Reduction SMS Sequence Tasks

4-touch SMS sequence to reduce no-shows:
1. Confirmation (immediate after booking)
2. 24-hour reminder (day before)
3. 2-hour reminder (same day)
4. Escalation (if no confirmation received)

Target: Reduce no-shows from 28% to 15%
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task
from sqlmodel import Session, select

try:
    from dental_agent.celery_config import celery_app
    from dental_agent.db import get_session, Appointment, Client, AppointmentStatus
    from dental_agent.twilio_service import send_sms
    from dental_agent.utils import mask_phone
    from dental_agent.encryption import phi_hash
except ImportError:
    from celery_config import celery_app
    from db import get_session, Appointment, Client, AppointmentStatus
    from twilio_service import send_sms
    from utils import mask_phone
    from encryption import phi_hash

logger = logging.getLogger(__name__)


# =============================================================================
# Default SMS Templates (used if clinic hasn't customized)
# =============================================================================

DEFAULT_SMS_TEMPLATES = {
    "confirmation": """Hi {patient_name}! Your appointment at {clinic_name} is confirmed for {date} at {time}. Reply YES to confirm or call {phone} to reschedule.""",

    "reminder_24h": """Reminder: {patient_name}, you have an appointment tomorrow at {clinic_name} at {time}. Please reply C to confirm or R to reschedule.""",

    "reminder_2h": """Hi {patient_name}! Just a quick reminder - your appointment at {clinic_name} is in 2 hours at {time}. See you soon!""",

    "escalation": """⚠️ {patient_name}, we haven't heard from you about your {date} at {time} appointment at {clinic_name}. Please reply YES to confirm or call {phone}.""",

    "recall": """Hi {patient_name}! It's been a while since your last visit to {clinic_name}. We'd love to see you! Reply BOOK or call {phone} to schedule.""",

    "recall_followup": """{patient_name}, your smile matters to us! {clinic_name} has convenient appointment times available. Call {phone} or reply BOOK to schedule your checkup.""",
}


def get_clinic_sms_template(clinic_id: int, template_key: str) -> str:
    """
    Get SMS template for a clinic with fallback to default.
    
    Args:
        clinic_id: The clinic ID
        template_key: One of 'confirmation', 'reminder_24h', 'reminder_2h', 'escalation', 'recall', 'recall_followup'
    
    Returns:
        The template string
    """
    try:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic and clinic.sms_templates:
                try:
                    custom_templates = json.loads(clinic.sms_templates)
                    if template_key in custom_templates and custom_templates[template_key]:
                        return custom_templates[template_key]
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in sms_templates for clinic {clinic_id}")
    except Exception as e:
        logger.error(f"Error loading clinic SMS template: {e}")
    
    return DEFAULT_SMS_TEMPLATES.get(template_key, DEFAULT_SMS_TEMPLATES["confirmation"])


def is_sms_enabled(clinic_id: int, sms_type: str) -> bool:
    """
    Check if a specific SMS type is enabled for a clinic.
    
    Args:
        clinic_id: The clinic ID
        sms_type: One of 'confirmation', 'reminder_24h', 'reminder_2h', 'recall'
    
    Returns:
        True if enabled, False otherwise
    """
    try:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic:
                if sms_type == "confirmation":
                    return clinic.sms_confirmation_enabled
                elif sms_type == "reminder_24h":
                    return clinic.sms_reminder_24h_enabled
                elif sms_type == "reminder_2h":
                    return clinic.sms_reminder_2h_enabled
                elif sms_type == "recall":
                    return clinic.sms_recall_enabled
    except Exception as e:
        logger.error(f"Error checking SMS enabled status: {e}")
    
    return True  # Default to enabled


def format_appointment_datetime(scheduled_time: datetime) -> tuple:
    """Format datetime into readable date and time strings."""
    date_str = scheduled_time.strftime("%A, %B %d")  # Monday, March 15
    time_str = scheduled_time.strftime("%I:%M %p").lstrip("0")  # 2:00 PM
    return date_str, time_str


def get_clinic_phone(clinic_id: int) -> str:
    """Get clinic phone number for SMS messages."""
    try:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic and clinic.phone_display:
                return clinic.phone_display
            if clinic and clinic.twilio_number:
                return clinic.twilio_number
    except Exception:
        logger.error("Error getting clinic phone")
    return os.getenv("TWILIO_NUMBER", "your clinic")


def get_clinic_name(clinic_id: int) -> str:
    """Get clinic name for SMS messages."""
    try:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic:
                return clinic.name
    except Exception:
        logger.error("Error getting clinic name")
    return "our dental clinic"


# =============================================================================
# CELERY TASKS - No-Show Reduction Sequence
# =============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation(self, appointment_id: int) -> dict:
    """
    Step 1: Send immediate confirmation after booking.
    
    Called right after appointment is created.
    """
    logger.info("Sending booking confirmation")
    
    try:
        with get_session() as session:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return {"error": "Appointment not found", "appointment_id": appointment_id}
            
            if appointment.confirmation_sent:
                return {"skipped": True, "reason": "Confirmation already sent"}
            
            if not appointment.patient_phone:
                return {"error": "No patient phone number", "appointment_id": appointment_id}
            
            # Check if confirmation SMS is enabled for this clinic
            if not is_sms_enabled(appointment.clinic_id, "confirmation"):
                return {"skipped": True, "reason": "Confirmation SMS disabled for this clinic"}
            
            # Format message using clinic's custom template or default
            date_str, time_str = format_appointment_datetime(appointment.scheduled_time)
            clinic_name = get_clinic_name(appointment.clinic_id)
            clinic_phone = get_clinic_phone(appointment.clinic_id)
            
            template = get_clinic_sms_template(appointment.clinic_id, "confirmation")
            message = template.format(
                patient_name=appointment.patient_name or "there",
                clinic_name=clinic_name,
                date=date_str,
                time=time_str,
                phone=clinic_phone,
            )
            
            # Send SMS
            result = send_sms(appointment.patient_phone, message)
            
            if result.get("success"):
                # Update appointment tracking
                appointment.confirmation_sent = True
                appointment.sms_sequence_step = 1
                appointment.last_sms_sent_at = datetime.utcnow()
                session.commit()
                
                # Schedule 24h reminder
                hours_until = (appointment.scheduled_time - datetime.utcnow()).total_seconds() / 3600
                if hours_until > 26:  # Only schedule if more than 26 hours away
                    reminder_time = appointment.scheduled_time - timedelta(hours=24)
                    delay_seconds = max(0, (reminder_time - datetime.utcnow()).total_seconds())
                    send_24h_reminder.apply_async(
                        args=[appointment_id],
                        countdown=delay_seconds,
                    )
                    logger.info("Scheduled 24h reminder in %.1f hours", delay_seconds / 3600)
                
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "message_sid": result.get("message_sid"),
                    "step": 1,
                }
            else:
                raise Exception(result.get("error", "SMS send failed"))
                
    except Exception as exc:
        logger.error("Error sending confirmation")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_24h_reminder(self, appointment_id: int) -> dict:
    """
    Step 2: Send 24-hour reminder (day before appointment).
    """
    logger.info("Sending 24h reminder")
    
    try:
        with get_session() as session:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return {"error": "Appointment not found", "appointment_id": appointment_id}
            
            # Skip if already sent or appointment cancelled
            if appointment.reminder_24h_sent:
                return {"skipped": True, "reason": "24h reminder already sent"}
            
            if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]:
                return {"skipped": True, "reason": f"Appointment {appointment.status.value}"}
            
            if not appointment.patient_phone:
                return {"error": "No patient phone number"}
            
            # Check if 24h reminder SMS is enabled for this clinic
            if not is_sms_enabled(appointment.clinic_id, "reminder_24h"):
                return {"skipped": True, "reason": "24h reminder SMS disabled for this clinic"}
            
            # Check if appointment is still ~24h away
            hours_until = (appointment.scheduled_time - datetime.utcnow()).total_seconds() / 3600
            if hours_until < 2:
                return {"skipped": True, "reason": "Appointment too soon for 24h reminder"}
            
            # Format message using clinic's custom template or default
            date_str, time_str = format_appointment_datetime(appointment.scheduled_time)
            clinic_name = get_clinic_name(appointment.clinic_id)
            
            template = get_clinic_sms_template(appointment.clinic_id, "reminder_24h")
            message = template.format(
                patient_name=appointment.patient_name or "there",
                clinic_name=clinic_name,
                date=date_str,
                time=time_str,
            )
            
            # Send SMS
            result = send_sms(appointment.patient_phone, message)
            
            if result.get("success"):
                appointment.reminder_24h_sent = True
                appointment.sms_sequence_step = 2
                appointment.last_sms_sent_at = datetime.utcnow()
                session.commit()
                
                # Schedule 2h reminder
                if hours_until > 3:
                    reminder_time = appointment.scheduled_time - timedelta(hours=2)
                    delay_seconds = max(0, (reminder_time - datetime.utcnow()).total_seconds())
                    send_2h_reminder.apply_async(
                        args=[appointment_id],
                        countdown=delay_seconds,
                    )
                    logger.info("Scheduled 2h reminder")
                
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "message_sid": result.get("message_sid"),
                    "step": 2,
                }
            else:
                raise Exception(result.get("error", "SMS send failed"))
                
    except Exception as exc:
        logger.error("Error sending 24h reminder")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_2h_reminder(self, appointment_id: int) -> dict:
    """
    Step 3: Send 2-hour reminder (same day, final reminder).
    """
    logger.info("Sending 2h reminder")
    
    try:
        with get_session() as session:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return {"error": "Appointment not found", "appointment_id": appointment_id}
            
            if appointment.reminder_2h_sent:
                return {"skipped": True, "reason": "2h reminder already sent"}
            
            if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]:
                return {"skipped": True, "reason": f"Appointment {appointment.status.value}"}
            
            if not appointment.patient_phone:
                return {"error": "No patient phone number"}
            
            # Check if 2h reminder SMS is enabled for this clinic
            if not is_sms_enabled(appointment.clinic_id, "reminder_2h"):
                return {"skipped": True, "reason": "2h reminder SMS disabled for this clinic"}
            
            # Format message using clinic's custom template or default
            _, time_str = format_appointment_datetime(appointment.scheduled_time)
            clinic_name = get_clinic_name(appointment.clinic_id)
            clinic_phone = get_clinic_phone(appointment.clinic_id)
            
            template = get_clinic_sms_template(appointment.clinic_id, "reminder_2h")
            message = template.format(
                patient_name=appointment.patient_name or "there",
                clinic_name=clinic_name,
                time=time_str,
                phone=clinic_phone,
            )
            
            # Send SMS
            result = send_sms(appointment.patient_phone, message)
            
            if result.get("success"):
                appointment.reminder_2h_sent = True
                appointment.sms_sequence_step = 3
                appointment.last_sms_sent_at = datetime.utcnow()
                
                # Check if escalation needed (no confirmation yet)
                if appointment.confirmation_status == "pending":
                    appointment.escalation_needed = True
                    # Schedule escalation check 30 minutes before appointment
                    delay_seconds = max(0, (appointment.scheduled_time - timedelta(minutes=30) - datetime.utcnow()).total_seconds())
                    if delay_seconds > 0:
                        escalation_check.apply_async(
                            args=[appointment_id],
                            countdown=delay_seconds,
                        )
                
                session.commit()
                
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "message_sid": result.get("message_sid"),
                    "step": 3,
                }
            else:
                raise Exception(result.get("error", "SMS send failed"))
                
    except Exception as exc:
        logger.error("Error sending 2h reminder")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def escalation_check(self, appointment_id: int) -> dict:
    """
    Step 4: Escalation - final SMS or trigger outbound call.
    
    Runs if patient hasn't confirmed after all reminders.
    """
    logger.info("Running escalation check")
    
    try:
        with get_session() as session:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return {"error": "Appointment not found"}
            
            # Skip if already confirmed or completed
            if appointment.confirmation_status == "confirmed":
                return {"skipped": True, "reason": "Already confirmed"}
            
            if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED, AppointmentStatus.CONFIRMED]:
                return {"skipped": True, "reason": f"Appointment {appointment.status.value}"}
            
            if not appointment.patient_phone:
                return {"error": "No patient phone number"}
            
            # Format escalation message using clinic's custom template or default
            date_str, time_str = format_appointment_datetime(appointment.scheduled_time)
            clinic_name = get_clinic_name(appointment.clinic_id)
            clinic_phone = get_clinic_phone(appointment.clinic_id)
            
            template = get_clinic_sms_template(appointment.clinic_id, "escalation")
            message = template.format(
                patient_name=appointment.patient_name or "there",
                clinic_name=clinic_name,
                date=date_str,
                time=time_str,
                phone=clinic_phone,
            )
            
            # Send escalation SMS
            result = send_sms(appointment.patient_phone, message)
            
            if result.get("success"):
                appointment.sms_sequence_step = 4
                appointment.last_sms_sent_at = datetime.utcnow()
                appointment.confirmation_status = "no_response"
                session.commit()
                
                logger.warning("Escalation sent - patient unconfirmed")
                
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "message_sid": result.get("message_sid"),
                    "step": 4,
                    "action": "escalation_sms_sent",
                }
            else:
                raise Exception(result.get("error", "SMS send failed"))
                
    except Exception as exc:
        logger.error("Error in escalation check")
        raise self.retry(exc=exc)


@celery_app.task
def process_appointment_reminders() -> dict:
    """
    Periodic task: Scan for appointments needing reminders.
    
    Run every 15 minutes via Celery Beat to catch any missed reminders.
    """
    logger.info("Running periodic appointment reminder check")
    
    now = datetime.utcnow()
    reminders_sent = {"24h": 0, "2h": 0, "escalation": 0, "errors": 0}
    
    try:
        with get_session() as session:
            # Find appointments in next 26 hours that haven't received 24h reminder
            window_24h_start = now + timedelta(hours=22)
            window_24h_end = now + timedelta(hours=26)
            
            appointments_24h = session.exec(
                select(Appointment).where(
                    Appointment.scheduled_time >= window_24h_start,
                    Appointment.scheduled_time <= window_24h_end,
                    Appointment.reminder_24h_sent == False,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.patient_phone != None,
                )
            ).all()
            
            for apt in appointments_24h:
                try:
                    send_24h_reminder.delay(apt.id)
                    reminders_sent["24h"] += 1
                except Exception:
                    logger.error("Error queuing 24h reminder")
                    reminders_sent["errors"] += 1
            
            # Find appointments in next 3 hours that haven't received 2h reminder
            window_2h_start = now + timedelta(hours=1, minutes=30)
            window_2h_end = now + timedelta(hours=2, minutes=30)
            
            appointments_2h = session.exec(
                select(Appointment).where(
                    Appointment.scheduled_time >= window_2h_start,
                    Appointment.scheduled_time <= window_2h_end,
                    Appointment.reminder_2h_sent == False,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.patient_phone != None,
                )
            ).all()
            
            for apt in appointments_2h:
                try:
                    send_2h_reminder.delay(apt.id)
                    reminders_sent["2h"] += 1
                except Exception:
                    logger.error("Error queuing 2h reminder")
                    reminders_sent["errors"] += 1
            
            # Find unconfirmed appointments starting in next 45 minutes
            window_escalation = now + timedelta(minutes=45)
            
            appointments_escalation = session.exec(
                select(Appointment).where(
                    Appointment.scheduled_time <= window_escalation,
                    Appointment.scheduled_time > now,
                    Appointment.confirmation_status == "pending",
                    Appointment.sms_sequence_step < 4,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.patient_phone != None,
                )
            ).all()
            
            for apt in appointments_escalation:
                try:
                    escalation_check.delay(apt.id)
                    reminders_sent["escalation"] += 1
                except Exception:
                    logger.error("Error queuing escalation")
                    reminders_sent["errors"] += 1
    
    except Exception:
        logger.error("Error in periodic reminder check")
        reminders_sent["errors"] += 1
    
    logger.info("Reminder check complete: sent=%d errors=%d", reminders_sent.get('24h', 0) + reminders_sent.get('2h', 0), reminders_sent.get('errors', 0))
    return reminders_sent


def handle_patient_sms_response(
    from_number: str,
    message_body: str,
) -> dict:
    """
    Process inbound SMS response from patient.
    
    Called by the /sms/inbound webhook.
    
    Returns action taken and response to send.
    """
    logger.info("Processing inbound SMS response")
    
    body_lower = message_body.strip().lower()
    
    # Determine intent
    if body_lower in ["yes", "y", "confirm", "confirmed", "c", "ok", "yep", "yeah"]:
        intent = "confirm"
    elif body_lower in ["no", "n", "cancel", "reschedule", "r", "change"]:
        intent = "reschedule"
    elif "book" in body_lower:
        intent = "book"
    else:
        intent = "unknown"
    
    try:
        with get_session() as session:
            # Find the most recent appointment for this phone number
            appointment = session.exec(
                select(Appointment).where(
                    Appointment.patient_phone_hash == phi_hash(from_number),
                    Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
                    Appointment.scheduled_time > datetime.utcnow(),
                ).order_by(Appointment.scheduled_time)
            ).first()
            
            if not appointment:
                return {
                    "found": False,
                    "intent": intent,
                    "response": "We couldn't find an upcoming appointment for this number. Please call us to schedule.",
                }
            
            clinic_name = get_clinic_name(appointment.clinic_id)
            clinic_phone = get_clinic_phone(appointment.clinic_id)
            date_str, time_str = format_appointment_datetime(appointment.scheduled_time)
            
            if intent == "confirm":
                appointment.confirmation_status = "confirmed"
                appointment.status = AppointmentStatus.CONFIRMED
                appointment.confirmed_at = datetime.utcnow()
                appointment.patient_response = message_body
                appointment.escalation_needed = False
                session.commit()
                
                response_msg = f"✅ Confirmed! See you {date_str} at {time_str}. - {clinic_name}"
                
                return {
                    "found": True,
                    "appointment_id": appointment.id,
                    "intent": intent,
                    "action": "confirmed",
                    "response": response_msg,
                }
            
            elif intent == "reschedule":
                appointment.confirmation_status = "declined"
                appointment.patient_response = message_body
                session.commit()
                
                response_msg = f"No problem! Please call {clinic_phone} to reschedule. We look forward to seeing you!"
                
                return {
                    "found": True,
                    "appointment_id": appointment.id,
                    "intent": intent,
                    "action": "reschedule_requested",
                    "response": response_msg,
                }
            
            else:
                # Unknown response - acknowledge and ask to confirm
                appointment.patient_response = message_body
                session.commit()
                
                response_msg = f"Thanks for your message! Your appointment is {date_str} at {time_str}. Reply YES to confirm or call {clinic_phone}."
                
                return {
                    "found": True,
                    "appointment_id": appointment.id,
                    "intent": intent,
                    "action": "clarification_sent",
                    "response": response_msg,
                }
                
    except Exception:
        logger.error("Error processing SMS response")
        return {
            "error": "SMS processing failed",
            "response": "Sorry, we had trouble processing your message. Please call us directly.",
        }
