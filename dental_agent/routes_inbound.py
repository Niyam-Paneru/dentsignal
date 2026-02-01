"""
routes_inbound.py - Inbound Call Handling Routes

Handles:
- /inbound/voice - Twilio webhook for incoming calls (returns TwiML)
- /inbound/ws/{call_id} - WebSocket endpoint for Twilio Media Streams
- /inbound/status/{call_id} - Call status callbacks from Twilio

Flow:
1. Patient calls Twilio number → Twilio calls /inbound/voice
2. We lookup clinic by phone number, create InboundCall record
3. Return TwiML with <Connect><Stream> pointing to our WebSocket
4. Twilio connects to /inbound/ws/{call_id}
5. WebSocket bridge handles audio bidirectionally with Deepgram
6. When call ends, Twilio calls /inbound/status/{call_id}
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlmodel import select
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

from db import (
    get_session, Client, InboundCall, InboundCallStatus, InboundCallOutcome, 
    record_usage, UsageType, get_clinic_by_twilio_number, is_using_postgres
)
from websocket_bridge import handle_voice_websocket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbound", tags=["Inbound Calls"])

# Base URL for WebSocket connections (derived from API_BASE_URL)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
# Convert http(s) to ws(s) for WebSocket URL
WS_BASE_URL = API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://")


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def get_clinic_by_phone(to_number: str):
    """
    Look up clinic by Twilio phone number.
    Works with both SQLite (Client) and Supabase (dental_clinics).
    
    Args:
        to_number: The Twilio number that was called (E.164 format)
        
    Returns:
        Clinic record if found, None otherwise
    """
    with get_session() as session:
        return get_clinic_by_twilio_number(session, to_number)


def create_inbound_call(
    clinic_id: int,
    from_number: str,
    to_number: str,
    twilio_call_sid: str
) -> InboundCall:
    """
    Create a new InboundCall record.
    
    Args:
        clinic_id: ID of the clinic being called
        from_number: Caller's phone number
        to_number: Twilio number that was called
        twilio_call_sid: Twilio's Call SID
        
    Returns:
        Created InboundCall record
    """
    with get_session() as session:
        call = InboundCall(
            clinic_id=clinic_id,
            from_number=from_number,
            to_number=to_number,
            twilio_call_sid=twilio_call_sid,
            status=InboundCallStatus.RINGING,
        )
        session.add(call)
        session.commit()
        session.refresh(call)
        return call


def update_inbound_call(
    call_id: int,
    **updates
) -> Optional[InboundCall]:
    """
    Update an InboundCall record.
    
    Args:
        call_id: ID of the call to update
        **updates: Fields to update
        
    Returns:
        Updated InboundCall record
    """
    with get_session() as session:
        call = session.get(InboundCall, call_id)
        if call:
            for key, value in updates.items():
                if hasattr(call, key):
                    setattr(call, key, value)
            session.commit()
            session.refresh(call)
        return call


def get_inbound_call(call_id: int) -> Optional[InboundCall]:
    """Get an InboundCall by ID."""
    with get_session() as session:
        return session.get(InboundCall, call_id)


def get_clinic(clinic_id):
    """Get a Client/Clinic by ID. Works with both SQLite and Supabase."""
    from db import get_clinic_by_id
    with get_session() as session:
        return get_clinic_by_id(session, clinic_id)


# -----------------------------------------------------------------------------
# Twilio Voice Webhook
# -----------------------------------------------------------------------------

@router.post("/voice", response_class=HTMLResponse)
async def incoming_voice_webhook(
    request: Request,
    # Twilio sends these as form data
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(None),
    Direction: str = Form(None),
    # Optional: clinic_id can be passed as query param for explicit routing
    # Use this when you want to configure webhook URL per clinic:
    # e.g., /inbound/voice?clinic_id=clinic_abc123
    clinic_id: Optional[str] = Query(None, description="Optional clinic ID for explicit routing"),
):
    """
    Handle incoming voice call from Twilio.
    
    This endpoint receives the initial webhook when someone calls
    the clinic's Twilio number. We:
    1. Look up which clinic owns this number (or use clinic_id param)
    2. Create an InboundCall record
    3. Return TwiML that connects to our WebSocket
    
    Per-Clinic Routing:
    - Each clinic gets a unique Twilio number
    - Configure each number's webhook with clinic_id param:
      https://your-api.com/inbound/voice?clinic_id=CLIENT_ABC
    - This ensures correct clinic routing even if phone lookup fails
    
    Returns:
        TwiML response with <Connect><Stream>
    """
    logger.info(f"Incoming call: From={From}, To={To}, CallSid={CallSid}, clinic_id={clinic_id}")
    
    # Try to get clinic from explicit clinic_id parameter first (most reliable)
    clinic = None
    if clinic_id:
        with get_session() as session:
            # clinic_id could be the actual ID or a slug/name
            statement = select(Client).where(
                (Client.id == clinic_id) | (Client.name == clinic_id)
            )
            clinic = session.exec(statement).first()
            if clinic:
                logger.info(f"Found clinic via clinic_id param: {clinic.name}")
    
    # Fall back to phone number lookup
    if not clinic:
        clinic = get_clinic_by_phone(To)
    
    if not clinic:
        logger.warning(f"No clinic found for number {To}")
        # Return a polite error message
        response = VoiceResponse()
        response.say(
            "We're sorry, but this number is not currently in service. Please try again later.",
            voice="alice"
        )
        response.hangup()
        return HTMLResponse(content=str(response), media_type="application/xml")
    
    if not clinic.is_active:
        logger.warning(f"Clinic {clinic.id} is not active")
        response = VoiceResponse()
        response.say(
            f"Thank you for calling {clinic.name}. We are currently closed. Please call back during business hours.",
            voice="alice"
        )
        response.hangup()
        return HTMLResponse(content=str(response), media_type="application/xml")
    
    # Create InboundCall record
    inbound_call = create_inbound_call(
        clinic_id=clinic.id,
        from_number=From,
        to_number=To,
        twilio_call_sid=CallSid,
    )
    
    logger.info(f"Created InboundCall id={inbound_call.id} for clinic={clinic.name}")
    
    # Build WebSocket URL
    ws_url = f"{WS_BASE_URL}/inbound/ws/{inbound_call.id}"
    
    # Build TwiML response with fallback for WebSocket failures
    response = VoiceResponse()
    
    # Add initial greeting (plays while WebSocket connects)
    # This ensures the caller hears something immediately
    response.say(
        f"Thank you for calling {clinic.name}. Please hold while I connect you to our assistant.",
        voice="Polly.Joanna"
    )
    response.pause(length=1)
    
    # Connect to bidirectional WebSocket stream
    # action URL is called when stream ends/fails
    action_url = f"{API_BASE_URL}/inbound/stream-failed/{inbound_call.id}"
    connect = Connect(action=action_url)
    
    stream = Stream(url=ws_url)
    stream.parameter(name="clinic_id", value=str(clinic.id))
    stream.parameter(name="call_id", value=str(inbound_call.id))
    connect.append(stream)
    response.append(connect)
    
    # Fallback after stream ends (normal call completion)
    response.say(
        "Thank you for calling. Goodbye!",
        voice="Polly.Joanna"
    )
    response.hangup()
    
    logger.info(f"Returning TwiML with stream URL: {ws_url}")
    
    return HTMLResponse(content=str(response), media_type="application/xml")


# -----------------------------------------------------------------------------
# WebSocket for Twilio Media Streams
# -----------------------------------------------------------------------------

@router.websocket("/ws/{call_id}")
async def voice_websocket(
    websocket: WebSocket,
    call_id: int,
):
    """
    WebSocket endpoint for Twilio Media Streams.
    
    This handles the bidirectional audio stream between Twilio and
    our Deepgram Voice Agent integration.
    """
    await websocket.accept()
    
    logger.info(f"WebSocket connected for call {call_id}")
    
    # Get the call and clinic
    inbound_call = get_inbound_call(call_id)
    if not inbound_call:
        logger.error(f"InboundCall {call_id} not found")
        await websocket.close(code=4000, reason="Call not found")
        return
    
    clinic = get_clinic(inbound_call.clinic_id)
    if not clinic:
        logger.error(f"Clinic {inbound_call.clinic_id} not found")
        await websocket.close(code=4001, reason="Clinic not found")
        return
    
    # Update call status
    update_inbound_call(call_id, status=InboundCallStatus.IN_PROGRESS)
    
    try:
        # Run the voice agent bridge
        summary = await handle_voice_websocket(
            websocket=websocket,
            clinic=clinic,
            call_id=call_id,
        )
        
        # Save conversation data
        update_inbound_call(
            call_id,
            transcript=summary.get("transcript"),
            caller_name=summary.get("caller_name"),
            is_new_patient=summary.get("is_new_patient"),
            reason_for_call=summary.get("reason_for_call"),
            duration_seconds=summary.get("duration_seconds"),
        )
        
        logger.info(f"Call {call_id} completed. Duration: {summary.get('duration_seconds')}s")
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call {call_id}")
    except Exception as e:
        logger.error(f"Error in voice WebSocket for call {call_id}: {e}")
    finally:
        # Ensure call is marked as completed
        call = get_inbound_call(call_id)
        if call and call.status == InboundCallStatus.IN_PROGRESS:
            update_inbound_call(
                call_id,
                status=InboundCallStatus.COMPLETED,
                ended_at=datetime.utcnow(),
            )


# -----------------------------------------------------------------------------
# Stream Failed Fallback (called when WebSocket stream fails)
# -----------------------------------------------------------------------------

@router.post("/stream-failed/{call_id}", response_class=HTMLResponse)
async def stream_failed_webhook(
    call_id: int,
    request: Request,
):
    """
    Handle stream failure - provides fallback TwiML.
    
    This is called by Twilio when the WebSocket stream ends or fails.
    We return TwiML that plays a nice error message and offers alternatives.
    """
    logger.warning(f"Stream failed/ended for call {call_id}")
    
    # Get the call and clinic for context
    inbound_call = get_inbound_call(call_id)
    clinic_name = "our office"
    
    if inbound_call:
        clinic = get_clinic(inbound_call.clinic_id)
        if clinic:
            clinic_name = clinic.name
        
        # Mark as failed if still in progress
        if inbound_call.status == InboundCallStatus.IN_PROGRESS:
            update_inbound_call(
                call_id,
                status=InboundCallStatus.FAILED,
                outcome=InboundCallOutcome.NO_RESOLUTION,
                ended_at=datetime.utcnow(),
            )
    
    # Build fallback TwiML
    response = VoiceResponse()
    
    response.say(
        f"We apologize, but we're experiencing technical difficulties at {clinic_name}. "
        "Please try calling back in a few minutes, or leave a message after the tone "
        "and we'll return your call as soon as possible.",
        voice="Polly.Joanna"
    )
    
    # Optionally record a voicemail
    response.record(
        action=f"{API_BASE_URL}/inbound/voicemail/{call_id}",
        max_length=120,  # 2 minutes max
        play_beep=True,
        timeout=5,
        transcribe=True,
    )
    
    response.say("We didn't receive your message. Goodbye!", voice="Polly.Joanna")
    response.hangup()
    
    return HTMLResponse(content=str(response), media_type="application/xml")


# -----------------------------------------------------------------------------
# Voicemail Handler
# -----------------------------------------------------------------------------

@router.post("/voicemail/{call_id}")
async def voicemail_webhook(
    call_id: int,
    RecordingUrl: str = Form(None),
    RecordingSid: str = Form(None),
    RecordingDuration: int = Form(None),
    TranscriptionText: str = Form(None),
):
    """
    Handle voicemail recording from Twilio.
    """
    logger.info(f"Voicemail received for call {call_id}: {RecordingUrl}")
    
    if RecordingUrl:
        update_inbound_call(
            call_id,
            outcome=InboundCallOutcome.VOICEMAIL,
            extra_data={
                "voicemail_url": RecordingUrl,
                "voicemail_sid": RecordingSid,
                "voicemail_duration": RecordingDuration,
                "voicemail_transcript": TranscriptionText,
            }
        )
    
    # Return empty TwiML
    response = VoiceResponse()
    response.say("Thank you for your message. Goodbye!", voice="Polly.Joanna")
    response.hangup()
    
    return HTMLResponse(content=str(response), media_type="application/xml")


# -----------------------------------------------------------------------------
# Twilio Status Callback
# -----------------------------------------------------------------------------

@router.post("/status/{call_id}", response_class=PlainTextResponse)
async def call_status_webhook(
    call_id: int,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[int] = Form(None),
    AnsweredBy: Optional[str] = Form(None),
):
    """
    Handle call status updates from Twilio.
    
    Twilio sends these at various stages: initiated, ringing, answered, completed.
    """
    logger.info(f"Status update for call {call_id}: {CallStatus}")
    
    inbound_call = get_inbound_call(call_id)
    if not inbound_call:
        logger.warning(f"Call {call_id} not found for status update")
        return "OK"
    
    # Map Twilio status to our status
    status_mapping = {
        "queued": InboundCallStatus.RINGING,
        "ringing": InboundCallStatus.RINGING,
        "in-progress": InboundCallStatus.IN_PROGRESS,
        "completed": InboundCallStatus.COMPLETED,
        "busy": InboundCallStatus.FAILED,
        "failed": InboundCallStatus.FAILED,
        "no-answer": InboundCallStatus.NO_ANSWER,
        "canceled": InboundCallStatus.FAILED,
    }
    
    new_status = status_mapping.get(CallStatus.lower(), InboundCallStatus.IN_PROGRESS)
    
    updates = {
        "status": new_status,
    }
    
    if CallDuration:
        updates["duration_seconds"] = CallDuration
    
    if new_status in [InboundCallStatus.COMPLETED, InboundCallStatus.FAILED, InboundCallStatus.NO_ANSWER]:
        updates["ended_at"] = datetime.utcnow()
        
        # Determine outcome based on conversation data
        if inbound_call.booked_appointment:
            updates["outcome"] = InboundCallOutcome.BOOKED
        elif new_status == InboundCallStatus.NO_ANSWER:
            updates["outcome"] = InboundCallOutcome.HANGUP
        else:
            updates["outcome"] = InboundCallOutcome.INQUIRY
        
        # Record usage for billing
        if CallDuration and CallDuration > 0:
            try:
                with get_session() as session:
                    record_usage(
                        session,
                        clinic_id=inbound_call.clinic_id,
                        usage_type=UsageType.INBOUND_CALL,
                        quantity=float(CallDuration),
                        reference_id=str(call_id),
                        reference_type="inbound_call",
                    )
                logger.info(f"Recorded {CallDuration}s usage for clinic {inbound_call.clinic_id}")
            except Exception as e:
                logger.error(f"Failed to record usage: {e}")
    
    update_inbound_call(call_id, **updates)
    
    return "OK"


# -----------------------------------------------------------------------------
# API Endpoints for Call Data
# -----------------------------------------------------------------------------

@router.get("/calls/{call_id}")
async def get_call_details(call_id: int):
    """Get details of a specific inbound call."""
    call = get_inbound_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return {
        "id": call.id,
        "clinic_id": call.clinic_id,
        "from_number": call.from_number,
        "to_number": call.to_number,
        "status": call.status.value if call.status else None,
        "outcome": call.outcome.value if call.outcome else None,
        "duration_seconds": call.duration_seconds,
        "transcript": call.transcript,
        "summary": call.summary,
        "caller_name": call.caller_name,
        "is_new_patient": call.is_new_patient,
        "reason_for_call": call.reason_for_call,
        "booked_appointment": call.booked_appointment.isoformat() if call.booked_appointment else None,
        "started_at": call.started_at.isoformat() if call.started_at else None,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
    }


@router.get("/calls")
async def list_inbound_calls(
    clinic_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List inbound calls with optional filtering."""
    with get_session() as session:
        statement = select(InboundCall).order_by(InboundCall.started_at.desc())
        
        if clinic_id:
            statement = statement.where(InboundCall.clinic_id == clinic_id)
        
        if status:
            try:
                status_enum = InboundCallStatus(status)
                statement = statement.where(InboundCall.status == status_enum)
            except ValueError:
                pass
        
        statement = statement.offset(offset).limit(limit)
        calls = session.exec(statement).all()
        
        return {
            "calls": [
                {
                    "id": call.id,
                    "clinic_id": call.clinic_id,
                    "from_number": call.from_number,
                    "status": call.status.value if call.status else None,
                    "outcome": call.outcome.value if call.outcome else None,
                    "duration_seconds": call.duration_seconds,
                    "caller_name": call.caller_name,
                    "started_at": call.started_at.isoformat() if call.started_at else None,
                }
                for call in calls
            ],
            "count": len(calls),
            "offset": offset,
            "limit": limit,
        }
