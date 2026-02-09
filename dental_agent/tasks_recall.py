"""
tasks_recall.py - Proactive Recall Outbound System

Automated outreach to patients overdue for cleanings, checkups, etc.

Sequence:
1. SMS Reminder (Day 1): "Hi {name}, you're due for your 6-month cleaning!"
2. Follow-up SMS (Day 3): If no response, send second SMS
3. AI Call (Day 5): If still no response, schedule AI voice call
4. Final SMS (Day 7): Last chance reminder

Revenue Impact: Each booked cleaning = ~$150-250 recovered revenue

Similar to Dentina.ai's recall system, but with AI voice capability.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from celery import shared_task
from sqlmodel import Session, select, and_

try:
    from dental_agent.celery_config import celery_app
    from dental_agent.db import (
        get_session, Patient, Appointment, Client, 
        PatientRecall, RecallCampaign, RecallStatus, RecallType,
        AppointmentType, AppointmentStatus
    )
    from dental_agent.twilio_service import send_sms, make_call
except ImportError:
    from celery_config import celery_app
    from db import (
        get_session, Patient, Appointment, Client,
        PatientRecall, RecallCampaign, RecallStatus, RecallType,
        AppointmentType, AppointmentStatus
    )
    from twilio_service import send_sms, make_call

logger = logging.getLogger(__name__)


# =============================================================================
# Default SMS Templates for Recall (used if clinic hasn't customized)
# =============================================================================

DEFAULT_RECALL_SMS_TEMPLATES = {
    "recall": """Hi {patient_name}! It's been a while since your last visit to {clinic_name}. We'd love to see you! Reply BOOK or call {phone} to schedule.""",

    "recall_followup": """{patient_name}, your smile matters to us! {clinic_name} has convenient appointment times available. Call {phone} or reply BOOK to schedule your checkup.""",

    "cleaning_initial": """Hi {patient_name}! It's time for your 6-month cleaning at {clinic_name}. Your last visit was on {last_visit}. Reply BOOK or call {phone}.""",

    "cleaning_followup": """Quick reminder, {patient_name}! We have openings this week for your cleaning. Reply BOOK or call {phone}.""",

    "checkup_initial": """Hi {patient_name}! Time for your dental checkup at {clinic_name}. Regular checkups keep your smile healthy! Reply BOOK or call {phone}.""",

    "checkup_followup": """Friendly reminder: Your dental checkup is overdue, {patient_name}. Reply BOOK or call {phone}.""",

    "followup_initial": """Hi {patient_name}! Time for your follow-up appointment at {clinic_name}. Reply BOOK or call {phone}.""",

    "final_reminder": """Last reminder, {patient_name}! Your {recall_type} is now {days_overdue} days overdue. Reply BOOK or call {phone} today.""",
}


def get_clinic_recall_template(clinic_id: int, template_key: str) -> str:
    """
    Get recall SMS template for a clinic with fallback to default.
    
    Args:
        clinic_id: The clinic ID
        template_key: One of 'recall', 'recall_followup', 'cleaning_initial', etc.
    
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
    
    return DEFAULT_RECALL_SMS_TEMPLATES.get(template_key, DEFAULT_RECALL_SMS_TEMPLATES["recall"])


def is_recall_enabled(clinic_id: int) -> bool:
    """Check if recall SMS is enabled for a clinic."""
    try:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic:
                return clinic.sms_recall_enabled
    except Exception as e:
        logger.error(f"Error checking recall enabled status: {e}")
    return True  # Default to enabled


def get_recall_template(recall_type: RecallType, is_followup: bool = False, is_final: bool = False) -> str:
    """Get the appropriate default SMS template key for a recall type."""
    if is_final:
        return "final_reminder"
    
    type_map = {
        RecallType.CLEANING: "cleaning",
        RecallType.CHECKUP: "checkup",
        RecallType.FOLLOWUP: "followup",
        RecallType.PERIODONTAL: "cleaning",  # Use cleaning template
        RecallType.CUSTOM: "checkup",  # Use checkup template
    }
    
    base = type_map.get(recall_type, "checkup")
    suffix = "_followup" if is_followup else "_initial"
    
    return f"{base}{suffix}"


# =============================================================================
# Helper Functions
# =============================================================================

def get_clinic_info(clinic_id: int) -> Dict[str, str]:
    """Get clinic info for SMS templates."""
    try:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic:
                return {
                    "name": clinic.name,
                    "phone": clinic.phone_display or clinic.twilio_number or "our office",
                }
    except Exception as e:
        logger.error(f"Error getting clinic info: {e}")
    return {"name": "our clinic", "phone": "us"}


def calculate_days_overdue(due_date: datetime) -> int:
    """Calculate how many days overdue a recall is."""
    return max(0, (datetime.utcnow() - due_date).days)


# =============================================================================
# Celery Tasks - Recall System
# =============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_recall_sms(self, recall_id: int, is_followup: bool = False, is_final: bool = False) -> Dict[str, Any]:
    """
    Send recall SMS to patient.
    
    Args:
        recall_id: ID of PatientRecall record
        is_followup: Whether this is a follow-up SMS
        is_final: Whether this is the final reminder
    """
    logger.info(f"Sending recall SMS for recall_id={recall_id} (followup={is_followup}, final={is_final})")
    
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                return {"error": "Recall not found", "recall_id": recall_id}
            
            # Check if already completed
            if recall.status in [RecallStatus.BOOKED, RecallStatus.DECLINED, RecallStatus.CANCELLED]:
                return {"skipped": True, "reason": f"Recall already {recall.status.value}"}
            
            # Check if recall SMS is enabled for this clinic
            if not is_recall_enabled(recall.clinic_id):
                return {"skipped": True, "reason": "Recall SMS disabled for this clinic"}
            
            # Check attempt limits
            if recall.sms_attempts >= recall.max_sms_attempts and not is_final:
                return {"skipped": True, "reason": "Max SMS attempts reached"}
            
            if not recall.patient_phone:
                return {"error": "No patient phone number"}
            
            # Get clinic info
            clinic_info = get_clinic_info(recall.clinic_id)
            
            # Get template key and then fetch custom or default template
            template_key = get_recall_template(recall.recall_type, is_followup, is_final)
            template = get_clinic_recall_template(recall.clinic_id, template_key)
            
            # Format message
            days_overdue = calculate_days_overdue(recall.due_date)
            last_visit = recall.last_visit_date.strftime("%B %d") if recall.last_visit_date else "a while ago"
            
            message = template.format(
                patient_name=recall.patient_name.split()[0] if recall.patient_name else "there",
                clinic_name=clinic_info["name"],
                phone=clinic_info["phone"],
                last_visit=last_visit,
                recall_type=recall.recall_type.value.replace("_", " "),
                days_overdue=days_overdue,
            )
            
            # Send SMS
            result = send_sms(recall.patient_phone, message)
            
            if result.get("success"):
                # Update recall record
                recall.sms_attempts += 1
                recall.sms_sent_at = datetime.utcnow()
                recall.sms_message_sid = result.get("message_sid")
                recall.updated_at = datetime.utcnow()
                
                if recall.status == RecallStatus.PENDING:
                    recall.status = RecallStatus.SMS_SENT
                
                # Schedule next step
                if is_final:
                    # After final SMS, mark as no response if no action in 3 days
                    recall.next_outreach_at = datetime.utcnow() + timedelta(days=3)
                elif is_followup:
                    # After followup SMS, schedule AI call in 2 days
                    recall.next_outreach_at = datetime.utcnow() + timedelta(days=2)
                    schedule_recall_call.apply_async(
                        args=[recall_id],
                        countdown=2 * 24 * 60 * 60,  # 2 days in seconds
                    )
                else:
                    # After initial SMS, schedule followup in 3 days
                    recall.next_outreach_at = datetime.utcnow() + timedelta(days=3)
                    send_recall_sms.apply_async(
                        args=[recall_id],
                        kwargs={"is_followup": True},
                        countdown=3 * 24 * 60 * 60,  # 3 days in seconds
                    )
                
                session.commit()
                
                return {
                    "success": True,
                    "recall_id": recall_id,
                    "message_sid": result.get("message_sid"),
                    "attempt": recall.sms_attempts,
                    "is_followup": is_followup,
                    "is_final": is_final,
                }
            else:
                raise Exception(result.get("error", "SMS send failed"))
                
    except Exception as exc:
        logger.error(f"Error sending recall SMS for {recall_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def schedule_recall_call(self, recall_id: int) -> Dict[str, Any]:
    """
    Schedule an AI voice call for recall follow-up.
    
    This is the AI calling feature that Dentina.ai doesn't have!
    """
    logger.info(f"Scheduling recall call for recall_id={recall_id}")
    
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                return {"error": "Recall not found", "recall_id": recall_id}
            
            # Check if already completed
            if recall.status in [RecallStatus.BOOKED, RecallStatus.DECLINED, RecallStatus.CANCELLED]:
                return {"skipped": True, "reason": f"Recall already {recall.status.value}"}
            
            # Check attempt limits
            if recall.call_attempts >= recall.max_call_attempts:
                # Send final SMS instead
                send_recall_sms.apply_async(
                    args=[recall_id],
                    kwargs={"is_final": True},
                )
                return {"skipped": True, "reason": "Max call attempts reached, sending final SMS"}
            
            if not recall.patient_phone:
                return {"error": "No patient phone number"}
            
            # Get clinic info
            clinic = session.get(Client, recall.clinic_id)
            if not clinic or not clinic.twilio_number:
                return {"error": "Clinic has no Twilio number configured"}
            
            # Update status
            recall.status = RecallStatus.CALL_SCHEDULED
            recall.call_scheduled_at = datetime.utcnow()
            recall.call_attempts += 1
            recall.updated_at = datetime.utcnow()
            session.commit()
            
            # Make the AI outbound call
            # The call will use the recall context to guide the conversation
            call_context = {
                "type": "recall",
                "recall_id": recall_id,
                "recall_type": recall.recall_type.value,
                "patient_name": recall.patient_name,
                "last_visit": recall.last_visit_date.isoformat() if recall.last_visit_date else None,
                "days_overdue": calculate_days_overdue(recall.due_date),
            }
            
            result = make_call(
                to_number=recall.patient_phone,
                from_number=clinic.twilio_number,
                call_type="recall",
                context=call_context,
            )
            
            if result.get("success"):
                recall.outbound_call_sid = result.get("call_sid")
                session.commit()
                
                return {
                    "success": True,
                    "recall_id": recall_id,
                    "call_sid": result.get("call_sid"),
                    "attempt": recall.call_attempts,
                }
            else:
                # If call fails, schedule retry or final SMS
                if recall.call_attempts >= recall.max_call_attempts:
                    send_recall_sms.apply_async(
                        args=[recall_id],
                        kwargs={"is_final": True},
                    )
                raise Exception(result.get("error", "Call failed"))
                
    except Exception as exc:
        logger.error(f"Error scheduling recall call for {recall_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True)
def process_recall_response(self, recall_id: int, response_type: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process patient response to recall (SMS reply or call outcome).
    
    Args:
        recall_id: ID of PatientRecall record
        response_type: "sms" or "call"
        response_data: Dict with response details
    """
    logger.info(f"Processing recall response for recall_id={recall_id} type={response_type}")
    
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                return {"error": "Recall not found"}
            
            recall.patient_response = response_data.get("response_text", "")
            recall.updated_at = datetime.utcnow()
            
            # Analyze response
            response_lower = recall.patient_response.lower() if recall.patient_response else ""
            
            if response_type == "sms":
                if any(word in response_lower for word in ["book", "yes", "schedule", "ok"]):
                    # Patient wants to book!
                    recall.status = RecallStatus.BOOKED
                    recall.completed_at = datetime.utcnow()
                    # TODO: Create appointment or notify staff
                    logger.info(f"Recall {recall_id}: patient wants to book")
                    
                elif any(word in response_lower for word in ["no", "stop", "cancel", "remove"]):
                    recall.status = RecallStatus.DECLINED
                    recall.declined_reason = "Patient opted out via SMS"
                    recall.completed_at = datetime.utcnow()
                    
            elif response_type == "call":
                outcome = response_data.get("outcome", "")
                
                if outcome == "booked":
                    recall.status = RecallStatus.BOOKED
                    recall.completed_at = datetime.utcnow()
                    recall.booked_appointment_id = response_data.get("appointment_id")
                    
                elif outcome == "declined":
                    recall.status = RecallStatus.DECLINED
                    recall.declined_reason = response_data.get("reason", "Declined during call")
                    recall.completed_at = datetime.utcnow()
                    
                elif outcome == "callback":
                    # Patient requested callback - schedule for later
                    recall.next_outreach_at = datetime.utcnow() + timedelta(days=1)
                    
                elif outcome == "no_answer":
                    recall.status = RecallStatus.CALL_COMPLETED
                    # Schedule final SMS if max calls reached
                    if recall.call_attempts >= recall.max_call_attempts:
                        send_recall_sms.apply_async(
                            args=[recall_id],
                            kwargs={"is_final": True},
                        )
            
            session.commit()
            
            return {
                "success": True,
                "recall_id": recall_id,
                "new_status": recall.status.value,
            }
            
    except Exception as exc:
        logger.error(f"Error processing recall response: {exc}")
        return {"error": str(exc)}


@celery_app.task
def generate_recall_list(clinic_id: int, recall_type: RecallType, overdue_days: int = 30) -> Dict[str, Any]:
    """
    Generate list of patients due for recalls.
    
    Finds patients whose last appointment of a certain type
    was more than the recommended interval ago.
    
    Args:
        clinic_id: Clinic ID
        recall_type: Type of recall (cleaning, checkup, etc.)
        overdue_days: Days overdue to include (default 30)
    
    Returns:
        Dict with list of patients and counts
    """
    logger.info(f"Generating recall list for clinic {clinic_id}, type={recall_type}, overdue_days={overdue_days}")
    
    # Recall intervals in days
    RECALL_INTERVALS = {
        RecallType.CLEANING: 180,     # 6 months
        RecallType.CHECKUP: 365,      # 1 year
        RecallType.PERIODONTAL: 120,  # 4 months
        RecallType.FOLLOWUP: 30,      # 30 days
        RecallType.CUSTOM: 180,       # Default 6 months
    }
    
    interval_days = RECALL_INTERVALS.get(recall_type, 180)
    cutoff_date = datetime.utcnow() - timedelta(days=interval_days + overdue_days)
    
    try:
        with get_session() as session:
            # Get patients with completed appointments of this type before cutoff
            # who don't have a future appointment scheduled
            
            # Map recall type to appointment type
            appointment_type_map = {
                RecallType.CLEANING: AppointmentType.CLEANING,
                RecallType.CHECKUP: AppointmentType.CHECKUP,
                RecallType.PERIODONTAL: AppointmentType.CLEANING,
                RecallType.FOLLOWUP: None,  # Any completed appointment
                RecallType.CUSTOM: None,
            }
            
            apt_type = appointment_type_map.get(recall_type)
            
            # Query patients with their last relevant appointment
            query = select(Patient).where(
                Patient.clinic_id == clinic_id,
                Patient.phone.isnot(None),
            )
            
            patients = session.exec(query).all()
            
            recall_candidates = []
            
            for patient in patients:
                # Check if patient already has a pending recall
                existing_recall = session.exec(
                    select(PatientRecall).where(
                        PatientRecall.patient_id == patient.id,
                        PatientRecall.recall_type == recall_type,
                        PatientRecall.status.in_([
                            RecallStatus.PENDING, 
                            RecallStatus.SMS_SENT, 
                            RecallStatus.CALL_SCHEDULED
                        ])
                    )
                ).first()
                
                if existing_recall:
                    continue  # Skip patients with pending recalls
                
                # Check last appointment
                apt_query = select(Appointment).where(
                    Appointment.patient_id == patient.id,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
                if apt_type:
                    apt_query = apt_query.where(Appointment.appointment_type == apt_type)
                
                apt_query = apt_query.order_by(Appointment.scheduled_time.desc()).limit(1)
                last_apt = session.exec(apt_query).first()
                
                # Check if overdue
                if last_apt:
                    days_since = (datetime.utcnow() - last_apt.scheduled_time).days
                    if days_since >= interval_days + overdue_days:
                        recall_candidates.append({
                            "patient_id": patient.id,
                            "patient_name": f"{patient.first_name} {patient.last_name}",
                            "patient_phone": patient.phone,
                            "patient_email": patient.email,
                            "last_visit": last_apt.scheduled_time,
                            "days_since": days_since,
                            "days_overdue": days_since - interval_days,
                        })
                elif patient.last_visit:
                    # Use patient's last_visit field
                    days_since = (datetime.utcnow() - patient.last_visit).days
                    if days_since >= interval_days + overdue_days:
                        recall_candidates.append({
                            "patient_id": patient.id,
                            "patient_name": f"{patient.first_name} {patient.last_name}",
                            "patient_phone": patient.phone,
                            "patient_email": patient.email,
                            "last_visit": patient.last_visit,
                            "days_since": days_since,
                            "days_overdue": days_since - interval_days,
                        })
            
            # Sort by days overdue (most overdue first)
            recall_candidates.sort(key=lambda x: x["days_overdue"], reverse=True)
            
            return {
                "success": True,
                "clinic_id": clinic_id,
                "recall_type": recall_type.value,
                "overdue_days": overdue_days,
                "total_candidates": len(recall_candidates),
                "candidates": recall_candidates,
            }
            
    except Exception as exc:
        logger.error(f"Error generating recall list: {exc}")
        return {"error": str(exc), "candidates": []}


@celery_app.task
def create_recall_campaign(
    clinic_id: int,
    name: str,
    recall_type: RecallType,
    overdue_days: int = 30,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a recall campaign and generate recalls for all matching patients.
    
    Args:
        clinic_id: Clinic ID
        name: Campaign name
        recall_type: Type of recall
        overdue_days: Days overdue to target
        description: Optional campaign description
    
    Returns:
        Campaign details and count of recalls created
    """
    logger.info(f"Creating recall campaign for clinic {clinic_id}: {name}")
    
    try:
        # First generate the recall list
        recall_list = generate_recall_list(clinic_id, recall_type, overdue_days)
        
        if recall_list.get("error"):
            return recall_list
        
        candidates = recall_list.get("candidates", [])
        
        if not candidates:
            return {
                "success": True,
                "message": "No patients match the recall criteria",
                "recalls_created": 0,
            }
        
        with get_session() as session:
            # Create campaign
            campaign = RecallCampaign(
                clinic_id=clinic_id,
                name=name,
                recall_type=recall_type,
                description=description,
                target_overdue_days=overdue_days,
                target_count=len(candidates),
                total_recalls=len(candidates),
                estimated_revenue=len(candidates) * 200,  # ~$200 per cleaning
                started_at=datetime.utcnow(),
            )
            session.add(campaign)
            session.commit()
            session.refresh(campaign)
            
            campaign_id = str(campaign.id)
            recalls_created = 0
            
            # Create recall records for each patient
            for candidate in candidates:
                due_date = datetime.utcnow() - timedelta(days=candidate["days_overdue"])
                
                recall = PatientRecall(
                    clinic_id=clinic_id,
                    patient_id=candidate["patient_id"],
                    patient_name=candidate["patient_name"],
                    patient_phone=candidate["patient_phone"],
                    patient_email=candidate.get("patient_email"),
                    recall_type=recall_type,
                    last_visit_date=candidate["last_visit"],
                    due_date=due_date,
                    status=RecallStatus.PENDING,
                    priority=min(10, candidate["days_overdue"] // 30),  # Higher priority for more overdue
                    campaign_id=campaign_id,
                    next_outreach_at=datetime.utcnow(),  # Start immediately
                )
                session.add(recall)
                recalls_created += 1
            
            session.commit()
            
            return {
                "success": True,
                "campaign_id": campaign.id,
                "campaign_name": name,
                "recalls_created": recalls_created,
                "estimated_revenue": campaign.estimated_revenue,
            }
            
    except Exception as exc:
        logger.error(f"Error creating recall campaign: {exc}")
        return {"error": str(exc)}


@celery_app.task
def process_pending_recalls(clinic_id: Optional[int] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Process pending recalls - send SMS to those ready for outreach.
    
    Run this task periodically (e.g., every hour) to process recalls.
    
    Args:
        clinic_id: Optional clinic ID to filter (None = all clinics)
        limit: Max recalls to process in one run
    """
    logger.info(f"Processing pending recalls (clinic_id={clinic_id}, limit={limit})")
    
    try:
        with get_session() as session:
            # Find recalls ready for outreach
            query = select(PatientRecall).where(
                PatientRecall.status.in_([RecallStatus.PENDING, RecallStatus.SMS_SENT]),
                PatientRecall.next_outreach_at <= datetime.utcnow(),
            )
            
            if clinic_id:
                query = query.where(PatientRecall.clinic_id == clinic_id)
            
            query = query.order_by(PatientRecall.priority).limit(limit)
            recalls = session.exec(query).all()
            
            processed = 0
            for recall in recalls:
                # Schedule SMS task
                is_followup = recall.status == RecallStatus.SMS_SENT
                send_recall_sms.delay(recall.id, is_followup=is_followup)
                processed += 1
            
            return {
                "success": True,
                "processed": processed,
                "message": f"Scheduled {processed} recall SMS tasks",
            }
            
    except Exception as exc:
        logger.error(f"Error processing pending recalls: {exc}")
        return {"error": str(exc)}


@celery_app.task
def cleanup_expired_recalls(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old recalls that never got a response.
    
    Mark recalls as NO_RESPONSE if they've been pending for too long.
    """
    logger.info(f"Cleaning up recalls older than {days_old} days")
    
    try:
        with get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days_old)
            
            query = select(PatientRecall).where(
                PatientRecall.status.in_([
                    RecallStatus.SMS_SENT, 
                    RecallStatus.CALL_SCHEDULED,
                    RecallStatus.CALL_COMPLETED
                ]),
                PatientRecall.updated_at < cutoff,
            )
            
            recalls = session.exec(query).all()
            
            cleaned = 0
            for recall in recalls:
                recall.status = RecallStatus.NO_RESPONSE
                recall.completed_at = datetime.utcnow()
                recall.notes = f"Auto-closed after {days_old} days with no response"
                cleaned += 1
            
            session.commit()
            
            return {
                "success": True,
                "cleaned": cleaned,
                "message": f"Marked {cleaned} recalls as no response",
            }
            
    except Exception as exc:
        logger.error(f"Error cleaning up recalls: {exc}")
        return {"error": str(exc)}
