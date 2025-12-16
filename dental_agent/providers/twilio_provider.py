"""
providers/twilio_provider.py - Twilio Telephony Provider Implementation

Implements TelephonyProvider for Twilio:
- Outbound calls
- SMS messaging
- TwiML generation
"""

import os
import logging
from typing import Optional
from datetime import datetime

from providers.base import TelephonyProvider, CallInfo

logger = logging.getLogger(__name__)


class TwilioProvider(TelephonyProvider):
    """
    Twilio telephony provider implementation.
    
    Uses Twilio for:
    - Voice calls (inbound/outbound)
    - SMS messaging
    - Call control via TwiML
    """
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        default_from_number: Optional[str] = None,
    ):
        self._account_sid = account_sid or os.getenv("TWILIO_SID")
        self._auth_token = auth_token or os.getenv("TWILIO_TOKEN")
        self._default_from = default_from_number or os.getenv("TWILIO_NUMBER")
        
        if not self._account_sid or not self._auth_token:
            raise ValueError("Twilio credentials required (TWILIO_SID, TWILIO_TOKEN)")
        
        # Lazy-load Twilio client
        self._client = None
        
        # Usage tracking
        self._total_calls = 0
        self._total_sms = 0
        self._total_minutes = 0.0
    
    @property
    def name(self) -> str:
        return "twilio"
    
    def _get_client(self):
        """Get or create Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self._account_sid, self._auth_token)
            except ImportError:
                raise ImportError("twilio package required: pip install twilio")
        return self._client
    
    async def make_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs
    ) -> CallInfo:
        """
        Initiate an outbound call via Twilio.
        
        Args:
            to_number: Number to call (E.164)
            from_number: Caller ID (E.164), or uses default
            webhook_url: URL for TwiML instructions
            
        Returns:
            CallInfo with call details
        """
        client = self._get_client()
        
        from_num = from_number or self._default_from
        if not from_num:
            raise ValueError("from_number required (no default configured)")
        
        # Additional parameters
        status_callback = kwargs.get("status_callback")
        timeout = kwargs.get("timeout", 30)
        record = kwargs.get("record", False)
        
        try:
            call = client.calls.create(
                to=to_number,
                from_=from_num,
                url=webhook_url,
                status_callback=status_callback,
                timeout=timeout,
                record=record,
            )
            
            self._total_calls += 1
            
            logger.info(f"Twilio call initiated: {call.sid} to {to_number}")
            
            return CallInfo(
                call_sid=call.sid,
                from_number=from_num,
                to_number=to_number,
                direction="outbound",
                status=call.status,
            )
            
        except Exception as e:
            logger.error(f"Twilio call failed: {e}")
            raise
    
    async def end_call(self, call_sid: str) -> bool:
        """End an active call."""
        client = self._get_client()
        
        try:
            call = client.calls(call_sid).update(status="completed")
            logger.info(f"Ended call {call_sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_sid}: {e}")
            return False
    
    async def get_call(self, call_sid: str) -> Optional[CallInfo]:
        """Get call details from Twilio."""
        client = self._get_client()
        
        try:
            call = client.calls(call_sid).fetch()
            
            return CallInfo(
                call_sid=call.sid,
                from_number=call.from_,
                to_number=call.to,
                direction=call.direction,
                status=call.status,
                duration_seconds=int(call.duration) if call.duration else None,
            )
        except Exception as e:
            logger.error(f"Failed to fetch call {call_sid}: {e}")
            return None
    
    async def send_sms(
        self,
        to_number: str,
        from_number: str,
        body: str,
    ) -> dict:
        """
        Send an SMS message via Twilio.
        
        Returns:
            Message details including SID
        """
        client = self._get_client()
        
        from_num = from_number or self._default_from
        if not from_num:
            raise ValueError("from_number required (no default configured)")
        
        try:
            message = client.messages.create(
                to=to_number,
                from_=from_num,
                body=body,
            )
            
            self._total_sms += 1
            
            logger.info(f"SMS sent: {message.sid} to {to_number}")
            
            return {
                "sid": message.sid,
                "status": message.status,
                "to": to_number,
                "from": from_num,
                "body_length": len(body),
            }
            
        except Exception as e:
            logger.error(f"SMS failed to {to_number}: {e}")
            raise
    
    def generate_twiml(self, instructions: dict) -> str:
        """
        Generate TwiML from instruction dictionary.
        
        Args:
            instructions: Dict with keys like:
                - say: {"text": "Hello", "voice": "alice"}
                - stream: {"url": "wss://...", "parameters": {...}}
                - record: {"max_length": 60}
                - dial: {"number": "+1234567890"}
                
        Returns:
            TwiML XML string
        """
        from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
        
        response = VoiceResponse()
        
        for key, value in instructions.items():
            if key == "say":
                response.say(
                    value.get("text", ""),
                    voice=value.get("voice", "alice"),
                )
            
            elif key == "pause":
                response.pause(length=value.get("length", 1))
            
            elif key == "stream":
                connect = Connect(action=value.get("action"))
                stream = Stream(url=value.get("url"))
                for param_name, param_value in value.get("parameters", {}).items():
                    stream.parameter(name=param_name, value=str(param_value))
                connect.append(stream)
                response.append(connect)
            
            elif key == "record":
                response.record(
                    action=value.get("action"),
                    max_length=value.get("max_length", 60),
                    play_beep=value.get("play_beep", True),
                    transcribe=value.get("transcribe", False),
                )
            
            elif key == "dial":
                response.dial(value.get("number"))
            
            elif key == "hangup":
                response.hangup()
        
        return str(response)
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "provider": self.name,
            "total_calls": self._total_calls,
            "total_sms": self._total_sms,
            "total_minutes": round(self._total_minutes, 2),
            "note": "For accurate billing, check Twilio console",
        }


# Register with global registry
def register():
    """Register Twilio provider with the global registry."""
    from providers.base import get_registry
    get_registry().register_telephony("twilio", TwilioProvider)
