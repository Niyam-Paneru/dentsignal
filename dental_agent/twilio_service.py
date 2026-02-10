"""
twilio_service.py - Twilio Voice Call Service

Handles:
- Making outbound calls
- Generating TwiML for call flow
- Processing call status webhooks
- Managing call recordings

Uses Deepgram for speech-to-text and text-to-speech.
"""

import os
import logging
from typing import Optional
from datetime import datetime

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from dotenv import load_dotenv

try:
    from utils import mask_phone
except ImportError:
    # Fallback if utils not available
    def mask_phone(phone: str) -> str:
        if len(phone) > 4:
            return f"***{phone[-4:]}"
        return "****"

load_dotenv()

logger = logging.getLogger(__name__)

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Validate configuration
if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER]):
    logger.warning("Twilio credentials not fully configured. Set TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER in .env")
    _client = None
else:
    _client = Client(TWILIO_SID, TWILIO_TOKEN)


def get_twilio_client() -> Optional[Client]:
    """Get Twilio client instance."""
    global _client
    if _client is None and all([TWILIO_SID, TWILIO_TOKEN]):
        _client = Client(TWILIO_SID, TWILIO_TOKEN)
    return _client


def make_call(
    to_number: str,
    lead_id: int,
    call_id: int,
    webhook_base_url: Optional[str] = None,
) -> dict:
    """
    Initiate an outbound call via Twilio.
    
    Args:
        to_number: Phone number to call (E.164 format: +1XXXXXXXXXX)
        lead_id: Database ID of the lead
        call_id: Database ID of the call record
        webhook_base_url: Base URL for webhooks (defaults to API_BASE_URL)
        
    Returns:
        dict with call_sid, status, and other details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not configured. Check TWILIO_SID and TWILIO_TOKEN.")
    
    base_url = webhook_base_url or API_BASE_URL
    
    # URL that returns TwiML for the call flow
    twiml_url = f"{base_url}/twilio/voice/{call_id}"
    
    # URL for status callbacks
    status_callback = f"{base_url}/twilio/status/{call_id}"
    
    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_NUMBER,
            url=twiml_url,
            status_callback=status_callback,
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST",
            record=True,  # Record the call
            recording_status_callback=f"{base_url}/twilio/recording/{call_id}",
            machine_detection="Enable",  # Detect voicemail
            machine_detection_timeout=5,
        )
        
        call_sid_suffix = f"***{call.sid[-6:]}" if call.sid else "***"
        logger.info(f"Call initiated: SID={call_sid_suffix}, To={mask_phone(to_number)}, Status={call.status}")
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "to": mask_phone(to_number),
            "from": mask_phone(TWILIO_NUMBER) if TWILIO_NUMBER else "N/A",
            "lead_id": lead_id,
            "call_id": call_id,
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate call to {mask_phone(to_number)}: {e}")
        return {
            "success": False,
            "error": "Failed to initiate call",
            "to": mask_phone(to_number),
            "lead_id": lead_id,
            "call_id": call_id,
        }


def generate_greeting_twiml(
    lead_name: str,
    clinic_name: str = "Sunshine Dental",
    call_id: int = 0,
    webhook_base_url: Optional[str] = None,
) -> str:
    """
    Generate TwiML for the initial greeting.
    
    Uses Twilio's <Gather> to collect speech input and send to our webhook.
    """
    base_url = webhook_base_url or API_BASE_URL
    response = VoiceResponse()
    
    # Greeting with Gather for speech input
    gather = Gather(
        input="speech",
        action=f"{base_url}/twilio/gather/{call_id}",
        method="POST",
        timeout=5,
        speech_timeout="auto",
        language="en-US",
    )
    
    gather.say(
        f"Hi, am I speaking with {lead_name}? "
        f"This is Sarah calling from {clinic_name}. "
        "We noticed you were interested in scheduling an appointment. "
        "Is this a good time to talk?",
        voice="Polly.Joanna",  # Natural-sounding voice
        language="en-US",
    )
    
    response.append(gather)
    
    # If no input, try again
    response.say(
        "I'm sorry, I didn't catch that. Let me try again.",
        voice="Polly.Joanna",
    )
    response.redirect(f"{base_url}/twilio/voice/{call_id}")
    
    return str(response)


def generate_qualify_twiml(
    call_id: int,
    webhook_base_url: Optional[str] = None,
) -> str:
    """Generate TwiML for qualification question."""
    base_url = webhook_base_url or API_BASE_URL
    response = VoiceResponse()
    
    gather = Gather(
        input="speech",
        action=f"{base_url}/twilio/gather/{call_id}?state=qualify",
        method="POST",
        timeout=5,
        speech_timeout="auto",
        language="en-US",
    )
    
    gather.say(
        "Great! Are you a new patient with us, or have you visited before?",
        voice="Polly.Joanna",
    )
    
    response.append(gather)
    response.redirect(f"{base_url}/twilio/voice/{call_id}?state=qualify")
    
    return str(response)


def generate_offer_slot_twiml(
    call_id: int,
    available_slot: str = "tomorrow at 2 PM",
    webhook_base_url: Optional[str] = None,
) -> str:
    """Generate TwiML for offering appointment slot."""
    base_url = webhook_base_url or API_BASE_URL
    response = VoiceResponse()
    
    gather = Gather(
        input="speech",
        action=f"{base_url}/twilio/gather/{call_id}?state=offer",
        method="POST",
        timeout=5,
        speech_timeout="auto",
        language="en-US",
    )
    
    gather.say(
        f"I have an opening {available_slot}. Would that work for you?",
        voice="Polly.Joanna",
    )
    
    response.append(gather)
    response.redirect(f"{base_url}/twilio/voice/{call_id}?state=offer")
    
    return str(response)


def generate_confirm_twiml(
    call_id: int,
    booked_slot: str,
    clinic_name: str = "Sunshine Dental",
    webhook_base_url: Optional[str] = None,
) -> str:
    """Generate TwiML for confirming the appointment."""
    base_url = webhook_base_url or API_BASE_URL
    response = VoiceResponse()
    
    response.say(
        f"Perfect! I've booked your appointment for {booked_slot}. "
        f"You'll receive a confirmation text shortly. "
        f"Thank you for choosing {clinic_name}. Have a great day!",
        voice="Polly.Joanna",
    )
    
    response.hangup()
    
    return str(response)


def generate_end_twiml(
    reason: str = "no_appointment",
    clinic_name: str = "Sunshine Dental",
) -> str:
    """Generate TwiML for ending the call without booking."""
    response = VoiceResponse()
    
    if reason == "wrong_person":
        response.say(
            "I apologize for the confusion. Have a great day!",
            voice="Polly.Joanna",
        )
    elif reason == "not_interested":
        response.say(
            f"No problem at all. If you ever need dental care, feel free to call {clinic_name}. "
            "Have a wonderful day!",
            voice="Polly.Joanna",
        )
    elif reason == "callback_requested":
        response.say(
            "Absolutely, we'll call you back at a better time. Have a great day!",
            voice="Polly.Joanna",
        )
    else:
        response.say(
            f"Thank you for your time. Have a great day!",
            voice="Polly.Joanna",
        )
    
    response.hangup()
    
    return str(response)


def generate_voicemail_twiml(
    lead_name: str,
    clinic_name: str = "Sunshine Dental",
    callback_number: Optional[str] = None,
) -> str:
    """Generate TwiML for leaving a voicemail."""
    response = VoiceResponse()
    
    callback = callback_number or TWILIO_NUMBER
    
    response.say(
        f"Hi {lead_name}, this is Sarah from {clinic_name}. "
        "I'm calling about scheduling your dental appointment. "
        f"Please call us back at {callback}. "
        "We look forward to hearing from you. Have a great day!",
        voice="Polly.Joanna",
    )
    
    response.hangup()
    
    return str(response)


def verify_twilio_credentials() -> dict:
    """
    Verify Twilio credentials are working.
    
    Returns:
        dict with status and account info
    """
    client = get_twilio_client()
    if not client:
        return {
            "success": False,
            "error": "Twilio client not configured",
        }
    
    try:
        account = client.api.accounts(TWILIO_SID).fetch()
        
        return {
            "success": True,
            "account_sid": f"***{account.sid[-6:]}" if account.sid else "N/A",
            "friendly_name": account.friendly_name,
            "status": account.status,
            "type": account.type,
            "twilio_number": mask_phone(TWILIO_NUMBER) if TWILIO_NUMBER else "N/A",
        }
        
    except Exception as e:
        logger.error(f"Twilio credential verification failed: {e}")
        return {
            "success": False,
            "error": "Failed to verify Twilio credentials",
        }


def get_call_status(call_sid: str) -> dict:
    """Get the current status of a call."""
    client = get_twilio_client()
    if not client:
        return {"error": "Twilio client not configured"}
    
    try:
        call = client.calls(call_sid).fetch()
        return {
            "call_sid": call.sid,
            "status": call.status,
            "direction": call.direction,
            "duration": call.duration,
            "start_time": str(call.start_time) if call.start_time else None,
            "end_time": str(call.end_time) if call.end_time else None,
        }
    except Exception as e:
        logger.error(f"Failed to get call status for {call_sid}: {e}")
        return {"error": "Failed to retrieve call status"}


# =============================================================================
# SMS MESSAGING - Essential for patient engagement
# =============================================================================

def send_sms(
    to_number: str,
    message: str,
    from_number: Optional[str] = None,
) -> dict:
    """
    Send an SMS message via Twilio.
    
    Args:
        to_number: Phone number to send to (E.164 format: +1XXXXXXXXXX)
        message: Text message content (max 1600 chars)
        from_number: Optional sender number (defaults to TWILIO_NUMBER)
    
    Returns:
        dict with message SID and status
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not configured"}
    
    try:
        sms = client.messages.create(
            body=message,
            from_=from_number or TWILIO_NUMBER,
            to=to_number,
        )
        
        logger.info(f"SMS sent to {mask_phone(to_number)}: {sms.sid}")
        
        return {
            "success": True,
            "message_sid": sms.sid,
            "status": sms.status,
            "to": mask_phone(to_number),
        }
        
    except Exception as e:
        logger.error(f"Failed to send SMS to {mask_phone(to_number)}: {e}")
        return {"success": False, "error": "SMS delivery failed"}


def send_appointment_confirmation(
    to_number: str,
    patient_name: str,
    appointment_date: str,
    appointment_time: str,
    clinic_name: str,
    clinic_address: Optional[str] = None,
    clinic_phone: Optional[str] = None,
) -> dict:
    """
    Send appointment confirmation SMS.
    
    This is the #1 feature patients love - immediate confirmation.
    """
    message = f"""✅ Appointment Confirmed!

Hi {patient_name}!

Your appointment at {clinic_name} is scheduled for:
📅 {appointment_date}
🕐 {appointment_time}
"""
    
    if clinic_address:
        message += f"📍 {clinic_address}\n"
    
    message += f"""
Reply CONFIRM to confirm or RESCHEDULE to change.

Questions? """
    
    if clinic_phone:
        message += f"Call us at {clinic_phone}"
    else:
        message += "Reply to this message."
    
    return send_sms(to_number, message)


def send_appointment_reminder(
    to_number: str,
    patient_name: str,
    appointment_date: str,
    appointment_time: str,
    clinic_name: str,
    hours_until: int = 24,
) -> dict:
    """
    Send appointment reminder SMS (24h or 2h before).
    
    Reduces no-shows by 30-50%.
    """
    if hours_until <= 2:
        urgency = "in 2 hours"
    elif hours_until <= 24:
        urgency = "tomorrow"
    else:
        urgency = f"on {appointment_date}"
    
    message = f"""⏰ Reminder: Your dental appointment is {urgency}!

Hi {patient_name},

📅 {appointment_date} at {appointment_time}
🏥 {clinic_name}

Please arrive 10 minutes early.

Reply C to confirm or R to reschedule."""
    
    return send_sms(to_number, message)


def send_post_call_followup(
    to_number: str,
    patient_name: str,
    clinic_name: str,
    appointment_booked: bool = False,
    appointment_details: Optional[str] = None,
) -> dict:
    """
    Send follow-up SMS after a call.
    
    Increases patient satisfaction and conversion.
    """
    if appointment_booked:
        message = f"""Thanks for calling {clinic_name}, {patient_name}! 😊

Your appointment is confirmed:
{appointment_details or "Check your email for details."}

We look forward to seeing you!

- The {clinic_name} Team"""
    else:
        message = f"""Thanks for calling {clinic_name}, {patient_name}!

We're here whenever you're ready to schedule. 

📞 Call back anytime or reply BOOK to schedule.

- The {clinic_name} Team"""
    
    return send_sms(to_number, message)


def send_recall_reminder(
    to_number: str,
    patient_name: str,
    clinic_name: str,
    last_visit_months: int = 6,
) -> dict:
    """
    Send recall reminder for routine checkups.
    
    Drives recurring revenue - most patients forget without reminders.
    """
    message = f"""Hi {patient_name}! 👋

It's been {last_visit_months} months since your last visit to {clinic_name}.

Time for your routine checkup! Regular visits help catch issues early and keep your smile healthy.

📞 Reply BOOK or call us to schedule.

- Your {clinic_name} Team"""
    
    return send_sms(to_number, message)


def send_review_request(
    to_number: str,
    patient_name: str,
    clinic_name: str,
    review_link: str,
) -> dict:
    """
    Send review request after appointment.
    
    Should be sent 1-2 hours after appointment when experience is fresh.
    """
    message = f"""Hi {patient_name}!

Thank you for visiting {clinic_name} today! We hope you had a great experience.

Would you take 30 seconds to leave us a review? It really helps other patients find us!

⭐ {review_link}

Thanks so much!
- The {clinic_name} Team"""
    
    return send_sms(to_number, message)


# =============================================================================
# PHONE NUMBER PROVISIONING (Auto-configure webhooks for new clinics)
# =============================================================================
# 
# IMPORTANT: When you buy a Twilio number for a new clinic, webhooks must be set:
#   - Voice Webhook: {API_BASE_URL}/inbound/voice (POST)
#   - SMS Webhook: {API_BASE_URL}/api/sms/inbound (POST)
#
# Use provision_clinic_number() to automate this!
# =============================================================================

def list_available_numbers(
    area_code: Optional[str] = None,
    country: str = "US",
    limit: int = 10,
) -> list:
    """
    List available phone numbers to purchase.
    
    Args:
        area_code: Specific area code (e.g., "415" for San Francisco)
        country: Country code (default: US)
        limit: Max numbers to return
        
    Returns:
        List of available numbers with details
    """
    client = get_twilio_client()
    if not client:
        return {"error": "Twilio client not configured"}
    
    try:
        if area_code:
            numbers = client.available_phone_numbers(country).local.list(
                area_code=area_code,
                voice_enabled=True,
                sms_enabled=True,
                limit=limit,
            )
        else:
            numbers = client.available_phone_numbers(country).local.list(
                voice_enabled=True,
                sms_enabled=True,
                limit=limit,
            )
        
        return [
            {
                "phone_number": n.phone_number,
                "friendly_name": n.friendly_name,
                "locality": n.locality,
                "region": n.region,
                "capabilities": {
                    "voice": n.capabilities.get("voice", False),
                    "sms": n.capabilities.get("sms", False),
                }
            }
            for n in numbers
        ]
    except Exception as e:
        logger.error(f"Error listing available numbers: {e}")
        return {"error": "Failed to list available numbers"}


def provision_clinic_number(
    clinic_id: int,
    area_code: Optional[str] = None,
    phone_number: Optional[str] = None,
    friendly_name: Optional[str] = None,
) -> dict:
    """
    Purchase a Twilio number and auto-configure webhooks for a clinic.
    
    THIS IS THE KEY FUNCTION - it automatically sets up:
    - Voice webhook → /inbound/voice (for AI calls)
    - SMS webhook → /api/sms/inbound (for patient replies)
    
    Args:
        clinic_id: Database ID of the clinic
        area_code: Preferred area code (e.g., "415")
        phone_number: Specific number to buy (if known)
        friendly_name: Display name (e.g., "Smile Dental Main Line")
        
    Returns:
        dict with phone_number, sid, and status
        
    Example:
        >>> result = provision_clinic_number(
        ...     clinic_id=123,
        ...     area_code="512",
        ...     friendly_name="Austin Dental Clinic"
        ... )
        >>> print(result)
        {'success': True, 'phone_number': '+15125551234', 'sid': 'PN...'}
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not configured"}
    
    # Build webhook URLs
    voice_webhook = f"{API_BASE_URL}/inbound/voice"
    sms_webhook = f"{API_BASE_URL}/api/sms/inbound"
    status_callback = f"{API_BASE_URL}/twilio/status"
    
    try:
        # Option 1: Buy specific number
        if phone_number:
            number = client.incoming_phone_numbers.create(
                phone_number=phone_number,
                friendly_name=friendly_name or f"Clinic {clinic_id}",
                voice_url=voice_webhook,
                voice_method="POST",
                sms_url=sms_webhook,
                sms_method="POST",
                status_callback=status_callback,
                status_callback_method="POST",
            )
        # Option 2: Buy by area code
        elif area_code:
            number = client.incoming_phone_numbers.create(
                area_code=area_code,
                friendly_name=friendly_name or f"Clinic {clinic_id}",
                voice_url=voice_webhook,
                voice_method="POST",
                sms_url=sms_webhook,
                sms_method="POST",
                status_callback=status_callback,
                status_callback_method="POST",
            )
        else:
            return {"success": False, "error": "Must provide area_code or phone_number"}
        
        logger.info(f"Provisioned {mask_phone(number.phone_number)} for clinic {clinic_id}")
        
        return {
            "success": True,
            "phone_number": mask_phone(number.phone_number),
            "sid": number.sid,
            "friendly_name": number.friendly_name,
            "webhooks": {
                "voice": voice_webhook,
                "sms": sms_webhook,
            },
            "message": "Number purchased and webhooks configured automatically!",
        }
        
    except Exception as e:
        logger.error(f"Error provisioning number for clinic {clinic_id}: {e}")
        return {"success": False, "error": "Failed to provision number"}


def update_number_webhooks(phone_sid: str) -> dict:
    """
    Update webhooks for an existing Twilio number.
    
    Use this to fix numbers that were set up manually or need updating.
    
    Args:
        phone_sid: Twilio Phone Number SID (starts with "PN")
        
    Returns:
        dict with success status
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not configured"}
    
    voice_webhook = f"{API_BASE_URL}/inbound/voice"
    sms_webhook = f"{API_BASE_URL}/api/sms/inbound"
    
    try:
        number = client.incoming_phone_numbers(phone_sid).update(
            voice_url=voice_webhook,
            voice_method="POST",
            sms_url=sms_webhook,
            sms_method="POST",
        )
        
        logger.info(f"Updated webhooks for {mask_phone(number.phone_number)}")
        
        return {
            "success": True,
            "phone_number": mask_phone(number.phone_number),
            "webhooks": {
                "voice": voice_webhook,
                "sms": sms_webhook,
            },
        }
    except Exception as e:
        logger.error(f"Error updating number: {type(e).__name__}")
        return {"success": False, "error": "Failed to update number webhooks"}


def release_number(phone_sid: str) -> dict:
    """
    Release (delete) a Twilio phone number.
    
    Use when a clinic cancels their subscription.
    
    Args:
        phone_sid: Twilio Phone Number SID
        
    Returns:
        dict with success status
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not configured"}
    
    try:
        client.incoming_phone_numbers(phone_sid).delete()
        logger.info(f"Released phone number (SID: ***{phone_sid[-6:]})")
        return {"success": True, "message": f"Number {phone_sid} released"}
    except Exception as e:
        logger.error(f"Error releasing number (SID: ***{phone_sid[-6:]}): {e}")
        return {"success": False, "error": "Failed to release number"}


def list_clinic_numbers() -> list:
    """
    List all phone numbers in your Twilio account.
    
    Useful for auditing and checking webhook configurations.
    """
    client = get_twilio_client()
    if not client:
        return {"error": "Twilio client not configured"}
    
    try:
        numbers = client.incoming_phone_numbers.list()
        return [
            {
                "sid": n.sid,
                "phone_number": mask_phone(n.phone_number),
                "friendly_name": n.friendly_name,
                "voice_url": n.voice_url,
                "sms_url": n.sms_url,
                "date_created": str(n.date_created),
            }
            for n in numbers
        ]
    except Exception as e:
        logger.error(f"Error listing numbers: {e}")
        return {"error": "Failed to list numbers"}
