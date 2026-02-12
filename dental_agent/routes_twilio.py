"""
routes_twilio.py - Twilio Webhook Handlers

Handles:
- /twilio/voice/{call_id} - Initial TwiML for call
- /twilio/gather/{call_id} - Process speech input
- /twilio/status/{call_id} - Call status callbacks
- /twilio/recording/{call_id} - Recording callbacks

These webhooks are called by Twilio during the call lifecycle.
All endpoints validate Twilio request signatures to prevent spoofing.
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from functools import wraps

from fastapi import APIRouter, Form, Query, Request, Response, HTTPException, status, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# Import Twilio request validator
try:
    from twilio.request_validator import RequestValidator
except ImportError:
    RequestValidator = None

try:
    from dental_agent.twilio_service import (
        generate_greeting_twiml,
        generate_qualify_twiml,
        generate_offer_slot_twiml,
        generate_confirm_twiml,
        generate_end_twiml,
        generate_voicemail_twiml,
        verify_twilio_credentials,
    )
    from dental_agent.deepgram_service import detect_intent, process_caller_response
    from dental_agent.db import get_session, Call, Lead, CallResult, CallStatus, CallResultType, record_usage, UsageType
    from dental_agent.tasks import retry_call, mark_call_completed
    from dental_agent.auth import require_auth
except ImportError:
    from twilio_service import (
        generate_greeting_twiml,
        generate_qualify_twiml,
        generate_offer_slot_twiml,
        generate_confirm_twiml,
        generate_end_twiml,
        generate_voicemail_twiml,
        verify_twilio_credentials,
    )
    from deepgram_service import detect_intent, process_caller_response
    from db import get_session, Call, Lead, CallResult, CallStatus, CallResultType, record_usage, UsageType
    from tasks import retry_call, mark_call_completed
    from auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["Twilio Webhooks"])

# =============================================================================
# Twilio Request Validation
# =============================================================================

_twilio_validator = None  # Type: Optional[RequestValidator]


def get_twilio_validator():
    """Get or create Twilio request validator."""
    global _twilio_validator
    if _twilio_validator is None and RequestValidator is not None:
        auth_token = os.getenv("TWILIO_TOKEN")
        if auth_token:
            _twilio_validator = RequestValidator(auth_token)
    return _twilio_validator


async def validate_twilio_request(request: Request) -> bool:
    """
    Validate that a request comes from Twilio.
    
    Checks the X-Twilio-Signature header against the request URL and parameters.
    In development mode (TELEPHONY_MODE=SIMULATED), validation is skipped.
    
    Returns:
        True if valid or in dev mode, False otherwise
    """
    # Skip validation in simulated mode
    if os.getenv("TELEPHONY_MODE", "SIMULATED").upper() == "SIMULATED":
        return True
    
    validator = get_twilio_validator()
    if not validator:
        logger.error("Twilio validator not configured - cannot validate webhook")
        return False
    
    # Get the signature from headers
    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        logger.warning("Missing X-Twilio-Signature header")
        return False
    
    # Build the full URL
    url = str(request.url)
    
    # Get form parameters
    try:
        params = await request.form()
        params_dict = dict(params)
    except Exception:
        params_dict = {}
    
    # Validate the signature
    is_valid = validator.validate(url, params_dict, signature)
    
    if not is_valid:
        logger.warning(f"Invalid Twilio signature for {url}")
    
    return is_valid


async def require_twilio_auth(request: Request):
    """
    Dependency to require valid Twilio webhook authentication.
    
    Raises HTTPException 403 if validation fails.
    """
    if not await validate_twilio_request(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature"
        )

# Store conversation state (in production, use Redis)
# Format: {call_id: {"state": "greeting", "patient_type": None, "booked_slot": None}}
CALL_STATES = {}


def get_call_state(call_id: int) -> dict:
    """Get current conversation state for a call."""
    if call_id not in CALL_STATES:
        CALL_STATES[call_id] = {
            "state": "greeting",
            "patient_type": None,
            "booked_slot": None,
            "transcript": [],
        }
    return CALL_STATES[call_id]


def update_call_state(call_id: int, **kwargs) -> None:
    """Update conversation state for a call."""
    state = get_call_state(call_id)
    state.update(kwargs)


def get_lead_for_call(call_id: int) -> Optional[dict]:
    """Get lead info for a call."""
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                lead = session.get(Lead, call.lead_id)
                if lead:
                    return {
                        "name": lead.name,
                        "phone": lead.phone,
                        "email": lead.email,
                    }
    except Exception as e:
        logger.error(f"Error getting lead for call {call_id}: {e}")
    return {"name": "there", "phone": "", "email": ""}  # Fallback


@router.post("/voice/{call_id}", response_class=PlainTextResponse)
async def voice_webhook(
    request: Request,
    call_id: int,
    state: Optional[str] = Query(None),
    AnsweredBy: Optional[str] = Form(None),
    _: None = Depends(require_twilio_auth),
):
    """
    Initial voice webhook - returns TwiML for the call.
    
    Twilio calls this URL when the call is answered.
    Returns TwiML instructions for what to say/gather.
    """
    logger.info(f"Voice webhook for call {call_id}, state={state}, AnsweredBy={AnsweredBy}")
    
    # Check if voicemail/machine detected
    if AnsweredBy and AnsweredBy in ["machine_start", "machine_end_beep", "machine_end_silence"]:
        logger.info(f"Voicemail detected for call {call_id}")
        lead = get_lead_for_call(call_id)
        return generate_voicemail_twiml(lead["name"])
    
    # Get current state
    call_state = get_call_state(call_id)
    current_state = state or call_state["state"]
    lead = get_lead_for_call(call_id)
    
    if current_state == "greeting":
        return generate_greeting_twiml(lead["name"], call_id=call_id)
    
    elif current_state == "qualify":
        return generate_qualify_twiml(call_id)
    
    elif current_state == "offer":
        # Generate a slot for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        slot = tomorrow.replace(hour=14, minute=0).strftime("%B %d at %I:%M %p")
        call_state["offered_slot"] = slot
        return generate_offer_slot_twiml(call_id, available_slot=slot)
    
    elif current_state == "confirm":
        booked_slot = call_state.get("booked_slot", "your scheduled time")
        return generate_confirm_twiml(call_id, booked_slot=booked_slot)
    
    elif current_state == "end":
        reason = call_state.get("end_reason", "complete")
        return generate_end_twiml(reason)
    
    else:
        # Default to greeting
        return generate_greeting_twiml(lead["name"], call_id=call_id)


@router.post("/gather/{call_id}", response_class=PlainTextResponse)
async def gather_webhook(
    request: Request,
    call_id: int,
    state: Optional[str] = Query(None),
    SpeechResult: Optional[str] = Form(None),
    Confidence: Optional[float] = Form(None),
    _: None = Depends(require_twilio_auth),
):
    """
    Process gathered speech input from the caller.
    
    Twilio calls this after the caller speaks during a <Gather>.
    We process their response and return next TwiML.
    """
    logger.info(f"Gather webhook for call {call_id}: '{SpeechResult}' (confidence: {Confidence})")
    
    call_state = get_call_state(call_id)
    current_state = state or call_state["state"]
    
    # Add to transcript
    if SpeechResult:
        call_state["transcript"].append({
            "speaker": "caller",
            "text": SpeechResult,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    # Process the response
    result = process_caller_response(SpeechResult or "", current_state)
    
    logger.info(f"Intent: {result['intent']}, Next state: {result['next_state']}")
    
    # Update state
    new_state = result["next_state"]
    update_call_state(call_id, state=new_state)
    
    # Handle state transitions
    if new_state == "qualify":
        return generate_qualify_twiml(call_id)
    
    elif new_state == "offer_slot":
        if "patient_type" in result:
            update_call_state(call_id, patient_type=result["patient_type"])
        
        # Generate slot offer
        tomorrow = datetime.now() + timedelta(days=1)
        slot = tomorrow.replace(hour=14, minute=0).strftime("%B %d at %I:%M %p")
        update_call_state(call_id, offered_slot=slot)
        return generate_offer_slot_twiml(call_id, available_slot=slot)
    
    elif new_state == "confirm":
        # They accepted the slot!
        slot = call_state.get("offered_slot", "tomorrow at 2 PM")
        update_call_state(call_id, booked_slot=slot)
        
        # Save booking to database
        save_booking(call_id, slot, call_state.get("patient_type"))
        
        return generate_confirm_twiml(call_id, booked_slot=slot)
    
    elif new_state == "end":
        reason = result.get("end_reason", "complete")
        update_call_state(call_id, end_reason=reason)
        
        # Save call result
        save_call_result(call_id, reason, call_state)
        
        return generate_end_twiml(reason)
    
    else:
        # Retry current state
        lead = get_lead_for_call(call_id)
        if current_state == "greeting":
            return generate_greeting_twiml(lead["name"], call_id=call_id)
        elif current_state == "qualify":
            return generate_qualify_twiml(call_id)
        elif current_state == "offer":
            slot = call_state.get("offered_slot", "tomorrow at 2 PM")
            return generate_offer_slot_twiml(call_id, available_slot=slot)
        else:
            return generate_end_twiml("complete")


@router.post("/status/{call_id}")
async def status_webhook(
    call_id: int,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    _twilio_auth=Depends(require_twilio_auth),
):
    """
    Handle Twilio call status callbacks.
    
    Called when call status changes: initiated, ringing, answered, completed.
    """
    logger.info(f"Status webhook for call {call_id}: {CallStatus}, duration={CallDuration}")
    
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                call.twilio_sid = CallSid
                
                if CallStatus == "completed":
                    call.status = CallStatus.COMPLETED
                    if CallDuration:
                        duration = int(CallDuration)
                        call.duration = duration
                        
                        # Record usage for billing
                        try:
                            record_usage(
                                session,
                                clinic_id=call.client_id,
                                usage_type=UsageType.OUTBOUND_CALL,
                                quantity=float(duration),
                                reference_id=str(call_id),
                                reference_type="outbound_call",
                            )
                            logger.info(f"Recorded {duration}s outbound usage for clinic {call.client_id}")
                        except Exception as e:
                            logger.error(f"Failed to record outbound usage: {e}")
                
                elif CallStatus == "busy":
                    call.status = CallStatus.FAILED
                    # Schedule retry
                    retry_call.delay(call.lead_id, call.attempt + 1)
                
                elif CallStatus == "no-answer":
                    call.status = CallStatus.FAILED
                    # Schedule retry
                    retry_call.delay(call.lead_id, call.attempt + 1)
                
                elif CallStatus == "failed":
                    call.status = CallStatus.FAILED
                    retry_call.delay(call.lead_id, call.attempt + 1)
                
                elif CallStatus == "in-progress":
                    call.status = CallStatus.IN_PROGRESS
                
                call.updated_at = datetime.utcnow()
                session.commit()
                
    except Exception as e:
        logger.error(f"Error updating call status: {e}")
    
    return {"received": True}


@router.post("/recording/{call_id}")
async def recording_webhook(
    call_id: int,
    RecordingSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingDuration: Optional[str] = Form(None),
    _twilio_auth=Depends(require_twilio_auth),
):
    """
    Handle recording completion callback.
    
    Twilio calls this when a call recording is ready.
    """
    logger.info(f"Recording for call {call_id}: {RecordingUrl}")
    
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                call.recording_url = RecordingUrl
                call.recording_sid = RecordingSid
                session.commit()
    except Exception as e:
        logger.error(f"Error saving recording: {e}")
    
    return {"received": True}


@router.get("/verify")
async def verify_credentials(user: dict = Depends(require_auth)):
    """Verify Twilio credentials are working."""
    return verify_twilio_credentials()


def save_booking(call_id: int, slot: str, patient_type: Optional[str]) -> None:
    """Save a booking to the database."""
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                call.status = CallStatus.COMPLETED
                
                # Create or update result
                result = CallResult(
                    call_id=call_id,
                    result=CallResultType.BOOKED,
                    booked_slot=datetime.now() + timedelta(days=1),  # Parse from slot string
                    notes=f"Patient type: {patient_type or 'unknown'}",
                )
                session.add(result)
                session.commit()
                
                logger.info(f"Saved booking for call {call_id}")
    except Exception as e:
        logger.error(f"Error saving booking: {e}")


def save_call_result(call_id: int, reason: str, call_state: dict) -> None:
    """Save call result to database."""
    try:
        with get_session() as session:
            call = session.get(Call, call_id)
            if call:
                call.status = CallStatus.COMPLETED
                
                # Map reason to result type
                result_map = {
                    "booked": CallResultType.BOOKED,
                    "not_interested": CallResultType.NOT_INTERESTED,
                    "wrong_person": CallResultType.WRONG_NUMBER,
                    "callback_requested": CallResultType.CALLBACK,
                }
                result_type = result_map.get(reason, CallResultType.NOT_INTERESTED)
                
                # Build transcript string
                transcript = "\n".join([
                    f"{t['speaker']}: {t['text']}"
                    for t in call_state.get("transcript", [])
                ])
                
                result = CallResult(
                    call_id=call_id,
                    result=result_type,
                    transcript=transcript,
                    notes=f"End reason: {reason}",
                )
                session.add(result)
                session.commit()
                
                logger.info(f"Saved result for call {call_id}: {result_type}")
    except Exception as e:
        logger.error(f"Error saving call result: {e}")
