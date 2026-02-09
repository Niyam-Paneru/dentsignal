"""
routes_recall.py - Proactive Recall Management API

Endpoints for managing patient recalls (cleanings, checkups, etc.)

Features:
- Generate recall lists for overdue patients
- Create and manage recall campaigns
- View recall status and analytics
- Process SMS replies and call outcomes
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from sqlmodel import select, Session

try:
    from dental_agent.db import (
        get_session, Client, Patient, PatientRecall, RecallCampaign,
        RecallStatus, RecallType
    )
    from dental_agent.tasks_recall import (
        generate_recall_list, create_recall_campaign, process_pending_recalls,
        send_recall_sms, schedule_recall_call, process_recall_response
    )
except ImportError:
    from db import (
        get_session, Client, Patient, PatientRecall, RecallCampaign,
        RecallStatus, RecallType
    )
    from tasks_recall import (
        generate_recall_list, create_recall_campaign, process_pending_recalls,
        send_recall_sms, schedule_recall_call, process_recall_response
    )

router = APIRouter(prefix="/api/v1/recalls", tags=["recalls"])


# =============================================================================
# Pydantic Models
# =============================================================================

class RecallCampaignCreate(BaseModel):
    """Request model for creating a recall campaign."""
    name: str
    recall_type: str  # "cleaning", "checkup", "followup", "periodontal", "custom"
    overdue_days: int = 30
    description: Optional[str] = None


class RecallUpdate(BaseModel):
    """Request model for updating a recall."""
    status: Optional[str] = None
    notes: Optional[str] = None
    next_outreach_at: Optional[datetime] = None


class RecallResponse(BaseModel):
    """Request model for processing recall response."""
    response_type: str  # "sms" or "call"
    response_text: Optional[str] = None
    outcome: Optional[str] = None  # for calls: "booked", "declined", "callback", "no_answer"
    appointment_id: Optional[int] = None


class RecallListItem(BaseModel):
    """Response model for a recall list item."""
    id: int
    patient_name: str
    patient_phone: str
    recall_type: str
    status: str
    due_date: datetime
    days_overdue: int
    sms_attempts: int
    call_attempts: int
    last_contact: Optional[datetime] = None


class RecallStats(BaseModel):
    """Response model for recall statistics."""
    total_recalls: int
    pending: int
    sms_sent: int
    calls_made: int
    booked: int
    declined: int
    no_response: int
    conversion_rate: float
    estimated_revenue: float


# =============================================================================
# Recall List Endpoints
# =============================================================================

@router.get("/candidates")
async def get_recall_candidates(
    clinic_id: int,
    recall_type: str = "cleaning",
    overdue_days: int = 30,
):
    """
    Get list of patients who are due for recalls.
    
    This endpoint identifies patients who haven't been seen
    within the recommended interval for a given recall type.
    """
    try:
        recall_type_enum = RecallType(recall_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid recall type: {recall_type}")
    
    # Run the task synchronously for API response
    result = generate_recall_list(clinic_id, recall_type_enum, overdue_days)
    
    if result.get("error"):
        logger.error(f"Operation failed: {result.get('error', 'unknown')}")
        raise HTTPException(status_code=500, detail="Operation failed")
    
    return result


@router.get("/list")
async def get_recalls(
    clinic_id: int,
    status: Optional[str] = None,
    recall_type: Optional[str] = None,
    campaign_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Get list of recalls for a clinic with optional filters."""
    try:
        with get_session() as session:
            query = select(PatientRecall).where(PatientRecall.clinic_id == clinic_id)
            
            if status:
                try:
                    status_enum = RecallStatus(status)
                    query = query.where(PatientRecall.status == status_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
            if recall_type:
                try:
                    type_enum = RecallType(recall_type)
                    query = query.where(PatientRecall.recall_type == type_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid recall type: {recall_type}")
            
            if campaign_id:
                query = query.where(PatientRecall.campaign_id == str(campaign_id))
            
            query = query.order_by(PatientRecall.due_date.desc())
            query = query.offset(offset).limit(limit)
            
            recalls = session.exec(query).all()
            
            result = []
            for recall in recalls:
                days_overdue = max(0, (datetime.utcnow() - recall.due_date).days)
                last_contact = recall.sms_sent_at or recall.call_completed_at
                
                result.append({
                    "id": recall.id,
                    "patient_name": recall.patient_name,
                    "patient_phone": recall.patient_phone,
                    "patient_email": recall.patient_email,
                    "recall_type": recall.recall_type.value,
                    "status": recall.status.value,
                    "due_date": recall.due_date.isoformat(),
                    "days_overdue": days_overdue,
                    "sms_attempts": recall.sms_attempts,
                    "call_attempts": recall.call_attempts,
                    "last_contact": last_contact.isoformat() if last_contact else None,
                    "patient_response": recall.patient_response,
                    "priority": recall.priority,
                })
            
            return {
                "recalls": result,
                "total": len(result),
                "limit": limit,
                "offset": offset,
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_recall_stats(
    clinic_id: int,
    days: int = 30,
    campaign_id: Optional[int] = None,
):
    """Get recall statistics for a clinic."""
    try:
        with get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(PatientRecall).where(
                PatientRecall.clinic_id == clinic_id,
                PatientRecall.created_at >= start_date,
            )
            
            if campaign_id:
                query = query.where(PatientRecall.campaign_id == str(campaign_id))
            
            recalls = session.exec(query).all()
            
            total = len(recalls)
            pending = sum(1 for r in recalls if r.status == RecallStatus.PENDING)
            sms_sent = sum(1 for r in recalls if r.sms_attempts > 0)
            calls_made = sum(1 for r in recalls if r.call_attempts > 0)
            booked = sum(1 for r in recalls if r.status == RecallStatus.BOOKED)
            declined = sum(1 for r in recalls if r.status == RecallStatus.DECLINED)
            no_response = sum(1 for r in recalls if r.status == RecallStatus.NO_RESPONSE)
            
            conversion_rate = (booked / total * 100) if total > 0 else 0
            estimated_revenue = booked * 200  # ~$200 per cleaning
            
            return {
                "total_recalls": total,
                "pending": pending,
                "sms_sent": sms_sent,
                "calls_made": calls_made,
                "booked": booked,
                "declined": declined,
                "no_response": no_response,
                "conversion_rate": round(conversion_rate, 1),
                "estimated_revenue": estimated_revenue,
                "period_days": days,
            }
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Campaign Endpoints
# =============================================================================

@router.post("/campaigns")
async def create_campaign(
    clinic_id: int,
    campaign: RecallCampaignCreate,
):
    """
    Create a new recall campaign.
    
    This will:
    1. Find all patients matching the recall criteria
    2. Create PatientRecall records for each
    3. Schedule the outreach sequence
    """
    try:
        recall_type_enum = RecallType(campaign.recall_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid recall type: {campaign.recall_type}")
    
    # Create the campaign (runs synchronously)
    result = create_recall_campaign(
        clinic_id=clinic_id,
        name=campaign.name,
        recall_type=recall_type_enum,
        overdue_days=campaign.overdue_days,
        description=campaign.description,
    )
    
    if result.get("error"):
        logger.error(f"Operation failed: {result.get('error', 'unknown')}")
        raise HTTPException(status_code=500, detail="Operation failed")
    
    return result


@router.get("/campaigns")
async def get_campaigns(
    clinic_id: int,
    active_only: bool = False,
    limit: int = 20,
):
    """Get list of recall campaigns for a clinic."""
    try:
        with get_session() as session:
            query = select(RecallCampaign).where(RecallCampaign.clinic_id == clinic_id)
            
            if active_only:
                query = query.where(RecallCampaign.is_active == True)
            
            query = query.order_by(RecallCampaign.created_at.desc()).limit(limit)
            campaigns = session.exec(query).all()
            
            return {
                "campaigns": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "recall_type": c.recall_type.value,
                        "description": c.description,
                        "total_recalls": c.total_recalls,
                        "appointments_booked": c.appointments_booked,
                        "conversion_rate": round(c.appointments_booked / c.total_recalls * 100, 1) if c.total_recalls > 0 else 0,
                        "estimated_revenue": c.estimated_revenue,
                        "actual_revenue": c.actual_revenue,
                        "is_active": c.is_active,
                        "started_at": c.started_at.isoformat() if c.started_at else None,
                        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                    }
                    for c in campaigns
                ]
            }
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int):
    """Get details of a specific campaign."""
    try:
        with get_session() as session:
            campaign = session.get(RecallCampaign, campaign_id)
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")
            
            # Get recall breakdown
            recalls = session.exec(
                select(PatientRecall).where(PatientRecall.campaign_id == str(campaign_id))
            ).all()
            
            status_breakdown = {}
            for recall in recalls:
                status = recall.status.value
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            return {
                "campaign": {
                    "id": campaign.id,
                    "name": campaign.name,
                    "recall_type": campaign.recall_type.value,
                    "description": campaign.description,
                    "target_overdue_days": campaign.target_overdue_days,
                    "total_recalls": campaign.total_recalls,
                    "sms_sent": campaign.sms_sent,
                    "calls_made": campaign.calls_made,
                    "appointments_booked": campaign.appointments_booked,
                    "declined": campaign.declined,
                    "no_response": campaign.no_response,
                    "estimated_revenue": campaign.estimated_revenue,
                    "actual_revenue": campaign.actual_revenue,
                    "is_active": campaign.is_active,
                    "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                },
                "status_breakdown": status_breakdown,
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Individual Recall Endpoints
# =============================================================================

@router.get("/{recall_id}")
async def get_recall(recall_id: int):
    """Get details of a specific recall."""
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                raise HTTPException(status_code=404, detail="Recall not found")
            
            return {
                "id": recall.id,
                "patient_name": recall.patient_name,
                "patient_phone": recall.patient_phone,
                "patient_email": recall.patient_email,
                "recall_type": recall.recall_type.value,
                "status": recall.status.value,
                "priority": recall.priority,
                "due_date": recall.due_date.isoformat(),
                "last_visit_date": recall.last_visit_date.isoformat() if recall.last_visit_date else None,
                "sms_attempts": recall.sms_attempts,
                "call_attempts": recall.call_attempts,
                "sms_sent_at": recall.sms_sent_at.isoformat() if recall.sms_sent_at else None,
                "call_scheduled_at": recall.call_scheduled_at.isoformat() if recall.call_scheduled_at else None,
                "call_completed_at": recall.call_completed_at.isoformat() if recall.call_completed_at else None,
                "patient_response": recall.patient_response,
                "declined_reason": recall.declined_reason,
                "notes": recall.notes,
                "created_at": recall.created_at.isoformat(),
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{recall_id}")
async def update_recall(
    recall_id: int,
    update: RecallUpdate,
):
    """Update a recall's status or notes."""
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                raise HTTPException(status_code=404, detail="Recall not found")
            
            if update.status:
                try:
                    recall.status = RecallStatus(update.status)
                    if recall.status in [RecallStatus.BOOKED, RecallStatus.DECLINED, RecallStatus.NO_RESPONSE, RecallStatus.CANCELLED]:
                        recall.completed_at = datetime.utcnow()
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")
            
            if update.notes is not None:
                recall.notes = update.notes
            
            if update.next_outreach_at:
                recall.next_outreach_at = update.next_outreach_at
            
            recall.updated_at = datetime.utcnow()
            session.commit()
            
            return {"success": True, "recall_id": recall_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{recall_id}/send-sms")
async def trigger_recall_sms(
    recall_id: int,
    is_followup: bool = False,
    is_final: bool = False,
):
    """Manually trigger SMS for a recall."""
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                raise HTTPException(status_code=404, detail="Recall not found")
        
        # Queue the SMS task
        task = send_recall_sms.delay(recall_id, is_followup=is_followup, is_final=is_final)
        
        return {
            "success": True,
            "task_id": task.id,
            "recall_id": recall_id,
            "message": "SMS task queued",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{recall_id}/call")
async def trigger_recall_call(recall_id: int):
    """Manually trigger AI call for a recall."""
    try:
        with get_session() as session:
            recall = session.get(PatientRecall, recall_id)
            if not recall:
                raise HTTPException(status_code=404, detail="Recall not found")
        
        # Queue the call task
        task = schedule_recall_call.delay(recall_id)
        
        return {
            "success": True,
            "task_id": task.id,
            "recall_id": recall_id,
            "message": "Call task queued",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{recall_id}/response")
async def record_recall_response(
    recall_id: int,
    response: RecallResponse,
):
    """Record a patient's response to a recall (SMS or call outcome)."""
    try:
        result = process_recall_response(
            recall_id,
            response.response_type,
            {
                "response_text": response.response_text,
                "outcome": response.outcome,
                "appointment_id": response.appointment_id,
            }
        )
        
        if result.get("error"):
            logger.error(f"Operation failed: {result.get('error', 'unknown')}")
            raise HTTPException(status_code=500, detail="Operation failed")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Processing Endpoints
# =============================================================================

@router.post("/process")
async def trigger_process_recalls(
    clinic_id: Optional[int] = None,
    limit: int = 50,
):
    """
    Process pending recalls.
    
    This is typically run on a schedule (e.g., hourly),
    but can be triggered manually for testing.
    """
    try:
        task = process_pending_recalls.delay(clinic_id, limit)
        
        return {
            "success": True,
            "task_id": task.id,
            "message": f"Processing up to {limit} pending recalls",
        }
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
