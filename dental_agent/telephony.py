"""
telephony.py - Telephony Adapter Module

Supports two modes:
- SIMULATED: Mock calls for local development and testing
- TWILIO: Real PSTN calls via Twilio (requires TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER)

Set mode via environment variable: TELEPHONY_MODE=SIMULATED|TWILIO

Usage:
    from telephony import make_call, format_phone_e164
    
    result = make_call("+15551234567", call_id=123, callback_url="http://localhost:8000/api/calls/123/status")
"""

from __future__ import annotations

import os
import re
import random
import threading
import time
import logging
from typing import Optional
from datetime import datetime, timedelta

import requests

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

TELEPHONY_MODE = os.getenv("TELEPHONY_MODE", "SIMULATED").upper()
TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "")

logger = logging.getLogger(__name__)

# Simulated call results (deterministic with seeding)
SIMULATED_RESULTS = ["booked", "no-answer", "reschedule", "voicemail", "failed"]


# -----------------------------------------------------------------------------
# Phone Formatting
# -----------------------------------------------------------------------------

def format_phone_e164(phone: str, default_country: str = "US") -> str:
    """
    Format phone number to E.164 format.
    
    Simple implementation - strips non-digits, adds +1 for US if needed.
    For production, use a library like phonenumbers.
    
    Args:
        phone: Raw phone number string
        default_country: Default country code (default: US)
        
    Returns:
        E.164 formatted phone number (e.g., +15551234567)
    """
    # Strip all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle US numbers
    if default_country == "US":
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
    
    # If already has country code or unknown format, return with +
    if not digits.startswith("+"):
        return f"+{digits}"
    return digits


def validate_phone(phone: str) -> bool:
    """
    Basic phone number validation.
    
    Args:
        phone: Phone number string
        
    Returns:
        True if phone appears valid
    """
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15


# -----------------------------------------------------------------------------
# Simulated Telephony
# -----------------------------------------------------------------------------

def _simulated_call_worker(
    phone_number: str,
    call_id: int,
    callback_url: Optional[str],
    seed: Optional[int] = None,
):
    """
    Background worker for simulated calls.
    
    Sleeps for 2 seconds to simulate call duration, then POSTs result to callback_url.
    Results are deterministic when seed is provided.
    """
    # Simulate call duration
    time.sleep(2)
    
    # Generate deterministic result based on seed or call_id
    rng = random.Random(seed if seed is not None else call_id)
    result = rng.choice(SIMULATED_RESULTS)
    
    # Generate simulated transcript
    transcript = _generate_simulated_transcript(result, call_id)
    
    # Prepare payload
    payload = {
        "status": "completed",
        "result": result,
        "transcript": transcript,
        "notes": f"Simulated call completed with result: {result}",
    }
    
    # Add booked_slot if result is "booked"
    if result == "booked":
        # Schedule for tomorrow at 10am
        tomorrow = datetime.utcnow() + timedelta(days=1)
        booked_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        payload["booked_slot"] = booked_time.isoformat()
    
    # POST to callback URL if provided
    if callback_url:
        try:
            response = requests.post(callback_url, json=payload, timeout=10)
            logger.info(f"Simulated call {call_id} completed: {result}, callback status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to POST callback for call {call_id}: {e}")
    else:
        logger.info(f"Simulated call {call_id} completed: {result} (no callback URL)")
    
    return payload


def _generate_simulated_transcript(result: str, call_id: int) -> str:
    """Generate a simulated conversation transcript based on result."""
    
    transcripts = {
        "booked": f"""
Agent: Hello! This is Sarah from Sunshine Dental. Am I speaking with the patient?
Patient: Yes, this is them.
Agent: Great! I'm calling to schedule your dental checkup. We have availability tomorrow at 10 AM. Would that work for you?
Patient: Yes, that works perfectly.
Agent: Wonderful! I've booked you for tomorrow at 10 AM. You'll receive a confirmation text shortly. Is there anything else I can help you with?
Patient: No, that's all. Thank you!
Agent: Thank you for choosing Sunshine Dental. Have a great day!
[Call ended - Appointment booked: Tomorrow 10:00 AM]
""".strip(),
        
        "no-answer": f"""
[Dialing...]
[Ring 1...]
[Ring 2...]
[Ring 3...]
[Ring 4...]
[Ring 5...]
[No answer - Call went to voicemail but did not leave message]
""".strip(),
        
        "reschedule": f"""
Agent: Hello! This is Sarah from Sunshine Dental. Am I speaking with the patient?
Patient: Yes, hi.
Agent: I'm calling to schedule your dental checkup. We have availability tomorrow at 10 AM. Would that work?
Patient: Actually, I'm not available this week. Can we do next week?
Agent: Of course! Let me check our availability for next week and call you back. What days work best for you?
Patient: Monday or Tuesday afternoon would be ideal.
Agent: Perfect, I'll have our scheduling team reach out with options. Thank you!
[Call ended - Patient requested reschedule]
""".strip(),
        
        "voicemail": f"""
[Dialing...]
[Ring 1...]
[Ring 2...]
[Ring 3...]
[Voicemail activated]
Voicemail: Hi, you've reached [patient]. Please leave a message.
Agent: Hello, this is Sarah from Sunshine Dental. I'm calling to schedule your dental checkup. Please call us back at your convenience at 555-123-4567. Thank you and have a great day!
[Call ended - Left voicemail]
""".strip(),
        
        "failed": f"""
[Dialing...]
[Call failed - Number not in service or blocked]
[Call ID: {call_id}]
""".strip(),
    }
    
    return transcripts.get(result, f"[Simulated call {call_id} - Result: {result}]")


def make_simulated_call(
    phone_number: str,
    call_id: int,
    callback_url: Optional[str] = None,
    blocking: bool = False,
    seed: Optional[int] = None,
) -> dict:
    """
    Make a simulated call.
    
    Args:
        phone_number: Target phone number
        call_id: Internal call ID for tracking
        callback_url: URL to POST results to (e.g., /api/calls/{call_id}/status)
        blocking: If True, wait for call to complete. If False, run in background.
        seed: Random seed for deterministic results (useful for testing)
        
    Returns:
        Dict with call_sid and initial status
    """
    call_sid = f"SIM{call_id:08d}"
    
    if blocking:
        # Run synchronously for testing
        result = _simulated_call_worker(phone_number, call_id, callback_url, seed)
        return {"call_sid": call_sid, "status": "completed", "result": result}
    else:
        # Start background thread
        thread = threading.Thread(
            target=_simulated_call_worker,
            args=(phone_number, call_id, callback_url, seed),
            daemon=True,
        )
        thread.start()
        return {"call_sid": call_sid, "status": "initiated"}


# -----------------------------------------------------------------------------
# Twilio Telephony
# -----------------------------------------------------------------------------

def make_twilio_call(
    phone_number: str,
    call_id: int,
    callback_url: Optional[str] = None,
    twiml_url: Optional[str] = None,
) -> dict:
    """
    Make a real call via Twilio.
    
    Requires environment variables:
    - TWILIO_SID: Twilio Account SID
    - TWILIO_TOKEN: Twilio Auth Token
    - TWILIO_NUMBER: Twilio phone number to call from
    
    Args:
        phone_number: Target phone number in E.164 format
        call_id: Internal call ID for tracking
        callback_url: URL for Twilio to POST status updates
        twiml_url: URL returning TwiML for call handling
        
    Returns:
        Dict with call_sid and status
        
    Raises:
        RuntimeError: If Twilio credentials are not configured
    """
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_NUMBER:
        raise RuntimeError(
            "Twilio credentials not configured. "
            "Set TWILIO_SID, TWILIO_TOKEN, and TWILIO_NUMBER environment variables."
        )
    
    try:
        from twilio.rest import Client
    except ImportError:
        raise RuntimeError("Twilio library not installed. Run: pip install twilio")
    
    # Initialize Twilio client
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    
    # Format phone number
    to_number = format_phone_e164(phone_number)
    
    # Build call parameters
    call_params = {
        "to": to_number,
        "from_": TWILIO_NUMBER,
    }
    
    # Add TwiML URL if provided (required for handling the call)
    if twiml_url:
        call_params["url"] = twiml_url
    else:
        # Default: Use a simple TwiML that plays a message
        # In production, this would point to your voice agent webhook
        call_params["twiml"] = '<Response><Say>Hello, this is a test call from Sunshine Dental.</Say></Response>'
    
    # Add status callback if provided
    if callback_url:
        call_params["status_callback"] = callback_url
        call_params["status_callback_event"] = ["initiated", "ringing", "answered", "completed"]
    
    # Create the call
    call = client.calls.create(**call_params)
    
    logger.info(f"Twilio call initiated: SID={call.sid}, to=***{to_number[-4:]}")
    
    return {
        "call_sid": call.sid,
        "status": call.status,
    }


# -----------------------------------------------------------------------------
# Main Interface
# -----------------------------------------------------------------------------

def make_call(
    phone_number: str,
    call_id: int,
    callback_url: Optional[str] = None,
    mode: Optional[str] = None,
    **kwargs,
) -> dict:
    """
    Make an outbound call using the configured telephony mode.
    
    Args:
        phone_number: Target phone number
        call_id: Internal call ID for tracking
        callback_url: URL to POST status updates to
        mode: Override telephony mode (SIMULATED or TWILIO)
        **kwargs: Additional arguments passed to the mode-specific function
        
    Returns:
        Dict with call_sid and status
    """
    active_mode = (mode or TELEPHONY_MODE).upper()
    
    logger.info(f"Making call: phone=***{phone_number[-4:]}, call_id={call_id}, mode={active_mode}")
    
    if active_mode == "SIMULATED":
        return make_simulated_call(phone_number, call_id, callback_url, **kwargs)
    elif active_mode == "TWILIO":
        return make_twilio_call(phone_number, call_id, callback_url, **kwargs)
    else:
        raise ValueError(f"Unknown telephony mode: {active_mode}. Use SIMULATED or TWILIO.")


# -----------------------------------------------------------------------------
# Twilio Webhook Handler
# -----------------------------------------------------------------------------

def handle_inbound_twilio_event(request_data: dict) -> dict:
    """
    Convert Twilio webhook payload to internal format.
    
    Twilio sends POST requests with form data for call status updates.
    
    Args:
        request_data: Dict of Twilio webhook parameters
        
    Returns:
        Normalized dict with status, result, etc.
    """
    call_sid = request_data.get("CallSid", "")
    call_status = request_data.get("CallStatus", "").lower()
    
    # Map Twilio status to internal status
    status_map = {
        "queued": "queued",
        "initiated": "in-progress",
        "ringing": "in-progress",
        "in-progress": "in-progress",
        "completed": "completed",
        "busy": "failed",
        "failed": "failed",
        "no-answer": "failed",
        "canceled": "failed",
    }
    
    # Map Twilio status to call result
    result_map = {
        "completed": "booked",  # Default, will be overwritten by agent
        "busy": "no-answer",
        "failed": "failed",
        "no-answer": "no-answer",
        "canceled": "failed",
    }
    
    internal_status = status_map.get(call_status, "queued")
    internal_result = result_map.get(call_status)
    
    return {
        "call_sid": call_sid,
        "status": internal_status,
        "result": internal_result,
        "raw_status": call_status,
        "from_number": request_data.get("From", ""),
        "to_number": request_data.get("To", ""),
        "duration": request_data.get("CallDuration", 0),
        "direction": request_data.get("Direction", ""),
    }


# -----------------------------------------------------------------------------
# Main (Demo)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Telephony Adapter Demo")
    print(f"Mode: {TELEPHONY_MODE}")
    print()
    
    # Test phone formatting
    test_phones = [
        "5551234567",
        "(555) 123-4567",
        "+1-555-123-4567",
        "1-555-123-4567",
    ]
    
    print("Phone formatting:")
    for phone in test_phones:
        formatted = format_phone_e164(phone)
        print(f"  {phone} -> {formatted}")
    print()
    
    # Test simulated call (blocking mode for demo)
    print("Making simulated call (blocking)...")
    result = make_simulated_call(
        phone_number="+15551234567",
        call_id=1,
        callback_url=None,  # No callback for demo
        blocking=True,
        seed=42,  # Deterministic result
    )
    print(f"Result: {result}")
    print()
    
    # Test Twilio mode check
    print("Checking Twilio configuration...")
    if TWILIO_SID and TWILIO_TOKEN and TWILIO_NUMBER:
        print("  Twilio credentials configured!")
    else:
        print("  Twilio credentials NOT configured (expected for demo)")
    
    print("\nDemo complete!")
