"""
routes_calls.py - FastAPI Routes for Calls, Batches, and Webhooks

Provides REST endpoints for:
- POST /batches - Create batch and enqueue calls
- POST /calls/{call_id}/result - Process call results
- POST /twilio/webhook - Handle Twilio status callbacks

Integrates with Celery tasks for background processing.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Form, Request
from pydantic import BaseModel, Field

try:
    from dental_agent.tasks import (
        start_call,
        retry_call,
        process_call_result,
        get_lead_id_from_call_sid,
        get_call_attempt,
    )
except ImportError:
    from tasks import (
        start_call,
        retry_call,
        process_call_result,
        get_lead_id_from_call_sid,
        get_call_attempt,
    )

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class LeadInput(BaseModel):
    """Lead data for batch upload."""
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None
    consent: bool = True


class BatchCreateRequest(BaseModel):
    """Request to create a batch of leads."""
    leads: List[LeadInput] = Field(..., min_length=1, max_length=1000)
    client_id: int = 1


class BatchCreateResponse(BaseModel):
    """Response after creating a batch."""
    batch_id: int
    leads_created: int
    calls_queued: int
    message: str


class CallResultRequest(BaseModel):
    """Request to update call result."""
    status: str = Field(..., description="completed, no-answer, failed, busy")
    lead_id: int
    attempt: int = 1
    transcript: Optional[str] = None
    booked_slot: Optional[datetime] = None
    notes: Optional[str] = None


class CallResultResponse(BaseModel):
    """Response after processing call result."""
    success: bool
    action: str
    call_id: int
    next_attempt: Optional[int] = None


class TwilioWebhookResponse(BaseModel):
    """Response for Twilio webhook."""
    success: bool
    action: str
    message: str


# =============================================================================
# PLACEHOLDER FUNCTIONS - Implement with actual DB logic
# =============================================================================

def save_batch(leads: List[LeadInput], client_id: int) -> tuple:
    """
    Save a batch of leads to the database.
    
    TODO: Replace with actual SQLModel implementation:
        batch = UploadBatch(client_id=client_id, source="api")
        session.add(batch)
        session.commit()
        
        for lead_data in leads:
            lead = Lead(batch_id=batch.id, **lead_data.dict())
            session.add(lead)
        session.commit()
        
        return batch.id, [lead.id for lead in leads]
    """
    logger.info(f"[PLACEHOLDER] Saving batch of {len(leads)} leads for client {client_id}")
    
    # Mock: Return fake batch_id and lead_ids
    batch_id = 1
    lead_ids = list(range(1, len(leads) + 1))
    return batch_id, lead_ids


# =============================================================================
# ROUTES
# =============================================================================

@router.post("/batches", response_model=BatchCreateResponse)
async def create_batch(request: BatchCreateRequest):
    """
    Create a batch of leads and enqueue calls for each.
    
    Accepts a list of leads, saves them to DB, and schedules
    Celery tasks to initiate calls to each lead.
    
    Returns:
        BatchCreateResponse with batch_id and counts
    """
    logger.info(f"Creating batch with {len(request.leads)} leads")
    
    try:
        # Save leads to database
        batch_id, lead_ids = save_batch(request.leads, request.client_id)
        
        # Enqueue calls for each lead
        for lead_id in lead_ids:
            start_call.delay(lead_id)
            logger.debug(f"Enqueued call for lead {lead_id}")
        
        return BatchCreateResponse(
            batch_id=batch_id,
            leads_created=len(lead_ids),
            calls_queued=len(lead_ids),
            message=f"Successfully created batch {batch_id} with {len(lead_ids)} leads",
        )
    
    except Exception as e:
        logger.error(f"Failed to create batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calls/{call_id}/result", response_model=CallResultResponse)
async def update_call_result(call_id: int, request: CallResultRequest):
    """
    Process a call result and take appropriate action.
    
    - If completed: Mark call as done
    - If no-answer/failed and attempt < 3: Schedule retry
    - If no-answer/failed and attempt >= 3: Escalate to human
    
    Args:
        call_id: Database ID of the call
        request: Call result data
        
    Returns:
        CallResultResponse with action taken
    """
    logger.info(f"Processing result for call {call_id}: {request.status}")
    
    # Process via Celery task (runs synchronously for immediate response)
    result = process_call_result(
        call_id=call_id,
        lead_id=request.lead_id,
        status=request.status,
        attempt=request.attempt,
    )
    
    return CallResultResponse(
        success=result.get("success", False),
        action=result.get("action", "unknown"),
        call_id=call_id,
        next_attempt=result.get("next_attempt"),
    )


@router.post("/twilio/webhook", response_model=TwilioWebhookResponse)
async def twilio_status_webhook(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: str = Form(None),
    To: str = Form(None),
    Direction: str = Form(None),
    CallDuration: str = Form(None),
):
    """
    Handle Twilio call status webhooks.
    
    Twilio sends POST requests with form-encoded data when call
    status changes. This endpoint processes those updates.
    
    Status values:
    - queued, ringing, in-progress: Call is active
    - completed: Call finished successfully
    - busy, no-answer, failed, canceled: Call failed
    
    Args:
        CallSid: Twilio's unique call identifier
        CallStatus: Current status of the call
        From: Caller phone number
        To: Recipient phone number
        Direction: inbound or outbound
        CallDuration: Duration in seconds (if completed)
        
    Returns:
        TwilioWebhookResponse confirming action taken
    """
    logger.info(f"Twilio webhook: CallSid={CallSid}, Status={CallStatus}")
    
    # Map Twilio statuses to our internal statuses
    FAILED_STATUSES = {"no-answer", "failed", "busy", "canceled"}
    COMPLETED_STATUSES = {"completed"}
    
    if CallStatus in FAILED_STATUSES:
        # Lookup lead from CallSid
        lead_id = get_lead_id_from_call_sid(CallSid)
        
        if not lead_id:
            logger.warning(f"Could not find lead for CallSid {CallSid}")
            return TwilioWebhookResponse(
                success=False,
                action="lead_not_found",
                message=f"No lead found for CallSid {CallSid}",
            )
        
        # Get current attempt count
        attempt = get_call_attempt(CallSid)
        
        # Schedule retry
        retry_call.delay(lead_id, attempt + 1)
        
        return TwilioWebhookResponse(
            success=True,
            action="retry_scheduled",
            message=f"Retry scheduled for lead {lead_id}, attempt {attempt + 1}",
        )
    
    elif CallStatus in COMPLETED_STATUSES:
        lead_id = get_lead_id_from_call_sid(CallSid)
        
        if lead_id:
            logger.info(f"Call completed for lead {lead_id}")
        
        return TwilioWebhookResponse(
            success=True,
            action="completed",
            message=f"Call {CallSid} completed successfully",
        )
    
    else:
        # In-progress statuses - just acknowledge
        return TwilioWebhookResponse(
            success=True,
            action="acknowledged",
            message=f"Status {CallStatus} acknowledged",
        )


@router.get("/health/celery")
async def check_celery_health():
    """
    Health check for Celery workers.
    
    Returns:
        dict with Celery status
    """
    try:
        from dental_agent.celery_config import celery_app
        
        # Ping Celery
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            return {
                "status": "healthy",
                "workers": list(stats.keys()),
                "worker_count": len(stats),
            }
        else:
            return {
                "status": "no_workers",
                "message": "No Celery workers are running",
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
