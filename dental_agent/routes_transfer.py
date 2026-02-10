"""
routes_transfer.py - Call Transfer/Takeover API

Enables clinic owners to take over active calls from the AI receptionist.
When triggered, the AI announces the transfer and redirects the call to the owner's phone.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

# Import auth dependency
try:
    from dental_agent.auth import require_auth
    from dental_agent.utils import mask_phone
except ImportError:
    from auth import require_auth
    from utils import mask_phone

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transfer", tags=["Call Transfer"])

# Twilio client (initialized on first use)
_twilio_client = None


def get_twilio_client():
    """Get or create Twilio client."""
    global _twilio_client
    if _twilio_client is None:
        account_sid = os.getenv("TWILIO_SID")
        auth_token = os.getenv("TWILIO_TOKEN")
        if account_sid and auth_token and TwilioClient:
            _twilio_client = TwilioClient(account_sid, auth_token)
        else:
            logger.warning("Twilio credentials not configured")
    return _twilio_client


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TransferRequest(BaseModel):
    """Request to transfer an active call to the owner."""
    call_sid: str
    owner_phone: str
    clinic_name: Optional[str] = "the practice owner"
    timeout_seconds: int = 20


class TransferResponse(BaseModel):
    """Response after initiating a transfer."""
    success: bool
    message: str
    call_sid: str
    transfer_to: str
    status: str  # pending, ringing, answered, failed


class TransferStatusResponse(BaseModel):
    """Response for transfer status check."""
    call_sid: str
    status: str
    duration_seconds: Optional[int] = None
    answered_at: Optional[datetime] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/initiate", response_model=TransferResponse)
async def initiate_transfer(
    request: TransferRequest,
    user: dict = Depends(require_auth)
):
    """
    Transfer an active call to the clinic owner.
    
    Requires authentication via JWT Bearer token.
    
    Flow:
    1. Interrupt the current AI conversation (send signal to Deepgram)
    2. Update the Twilio call with new TwiML that:
       - Speaks an announcement: "I'm connecting you with the practice owner now"
       - Dials the owner's phone
       - If no answer, tells caller the owner is unavailable
    3. Log the transfer attempt
    
    Args:
        request: Transfer request with call_sid and owner_phone
        
    Returns:
        TransferResponse with status
    """
    client = get_twilio_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Twilio service not configured. Please check your environment variables."
        )
    
    # Validate phone number format (basic check)
    owner_phone = request.owner_phone.strip()
    if not owner_phone.startswith('+'):
        # Assume US number if no country code
        owner_phone = f"+1{owner_phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')}"
    
    # Build TwiML for the transfer
    # This TwiML will:
    # 1. Announce the transfer (using Twilio's TTS)
    # 2. Dial the owner's phone with a timeout
    # 3. If no answer, apologize and hang up
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">I'm connecting you with {request.clinic_name} now. One moment please.</Say>
    <Dial timeout="{request.timeout_seconds}" action="/api/transfer/dial-complete">
        <Number>{owner_phone}</Number>
    </Dial>
    <Say voice="Polly.Joanna">I'm sorry, the owner is currently unavailable. Please try calling back later or leave your information and we'll get back to you.</Say>
    <Hangup/>
</Response>"""
    
    try:
        # Update the active call with new TwiML
        call = client.calls(request.call_sid).update(twiml=twiml)
        
        call_sid_suffix = f"***{request.call_sid[-6:]}" if request.call_sid else "***"
        logger.info(
            "Transfer initiated: call_sid=%s, to=%s",
            call_sid_suffix,
            mask_phone(owner_phone),
        )
        
        return TransferResponse(
            success=True,
            message="Transfer initiated. The AI will announce the transfer and dial your phone.",
            call_sid=request.call_sid,
            transfer_to=owner_phone,
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate transfer"
        )


@router.post("/dial-complete")
async def dial_complete_webhook():
    """
    Webhook called by Twilio after the dial attempt completes.
    Used for logging and analytics.
    """
    # This would log the outcome (answered, no-answer, busy, etc.)
    # For now, just acknowledge
    return {"status": "ok"}


@router.get("/status/{call_sid}", response_model=TransferStatusResponse)
async def get_transfer_status(call_sid: str):
    """
    Check the status of a transfer.
    
    Returns current call status from Twilio.
    """
    client = get_twilio_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Twilio service not configured"
        )
    
    try:
        call = client.calls(call_sid).fetch()
        
        return TransferStatusResponse(
            call_sid=call_sid,
            status=call.status,
            duration_seconds=call.duration if hasattr(call, 'duration') else None
        )
        
    except Exception as e:
        logger.error(f"Failed to get transfer status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )


@router.get("/can-transfer/{call_sid}")
async def can_transfer(call_sid: str):
    """
    Check if a call can be transferred.
    
    Returns whether the call is still active and can be transferred.
    """
    client = get_twilio_client()
    
    if not client:
        return {
            "can_transfer": False,
            "reason": "Twilio not configured"
        }
    
    try:
        call = client.calls(call_sid).fetch()
        
        # Can only transfer if call is in progress
        can_transfer = call.status in ['in-progress', 'ringing', 'queued']
        
        return {
            "can_transfer": can_transfer,
            "status": call.status,
            "reason": None if can_transfer else f"Call is {call.status}"
        }
        
    except Exception as e:
        logger.error(f"Error checking transfer availability: {e}")
        return {
            "can_transfer": False,
            "reason": "Internal error checking transfer availability"
        }
