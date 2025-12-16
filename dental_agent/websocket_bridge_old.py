"""
websocket_bridge.py - Twilio ↔ Deepgram Voice Agent Bridge

This is the core of the voice agent system. It:
1. Receives audio from Twilio Media Streams (mulaw, 8kHz)
2. Converts audio format (mulaw → linear16)
3. Sends audio to Deepgram Voice Agent WebSocket
4. Receives AI responses (text + TTS audio) from Deepgram
5. Converts audio back (linear16 → mulaw)
6. Sends audio back to Twilio

Audio Format Conversion:
- Twilio sends: mulaw (µ-law), 8000 Hz, mono, base64-encoded
- Deepgram expects: linear16 (PCM), 8000 or 16000 Hz, mono
- We use pure Python implementation (audioop removed in Python 3.13)

WebSocket Protocol:
- Twilio: wss://your-server.com/ws/voice/{call_id}
- Deepgram: wss://agent.deepgram.com/v1/agent/converse

Environment Variables:
- DEEPGRAM_API_KEY: Deepgram API key for Voice Agent
- OPENAI_API_KEY: OpenAI API key (for GPT-4 in Voice Agent)
"""

from __future__ import annotations

import asyncio
import array
import base64
import json
import logging
import os
import struct
from datetime import datetime
from typing import Optional, Any

import websockets
from dotenv import load_dotenv

from prompt_builder import PromptBuilder

load_dotenv()

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Deepgram Voice Agent WebSocket endpoint (v1 converse API)
DEEPGRAM_AGENT_URL = "wss://agent.deepgram.com/v1/agent/converse"

# Audio format settings
# Note: Deepgram accepts 8kHz directly, no need to upsample
TWILIO_SAMPLE_RATE = 8000
DEEPGRAM_SAMPLE_RATE = 8000  # Deepgram accepts 8kHz linear16 directly


# -----------------------------------------------------------------------------
# Audio Conversion Utilities (Pure Python - no audioop)
# -----------------------------------------------------------------------------

# μ-law decoding table (ITU-T G.711)
MULAW_DECODE_TABLE = [
    -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
    -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
    -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
    -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
    -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
    -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
    -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
    -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
    -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
    -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
    -876, -844, -812, -780, -748, -716, -684, -652,
    -620, -588, -556, -524, -492, -460, -428, -396,
    -372, -356, -340, -324, -308, -292, -276, -260,
    -244, -228, -212, -196, -180, -164, -148, -132,
    -120, -112, -104, -96, -88, -80, -72, -64,
    -56, -48, -40, -32, -24, -16, -8, 0,
    32124, 31100, 30076, 29052, 28028, 27004, 25980, 24956,
    23932, 22908, 21884, 20860, 19836, 18812, 17788, 16764,
    15996, 15484, 14972, 14460, 13948, 13436, 12924, 12412,
    11900, 11388, 10876, 10364, 9852, 9340, 8828, 8316,
    7932, 7676, 7420, 7164, 6908, 6652, 6396, 6140,
    5884, 5628, 5372, 5116, 4860, 4604, 4348, 4092,
    3900, 3772, 3644, 3516, 3388, 3260, 3132, 3004,
    2876, 2748, 2620, 2492, 2364, 2236, 2108, 1980,
    1884, 1820, 1756, 1692, 1628, 1564, 1500, 1436,
    1372, 1308, 1244, 1180, 1116, 1052, 988, 924,
    876, 844, 812, 780, 748, 716, 684, 652,
    620, 588, 556, 524, 492, 460, 428, 396,
    372, 356, 340, 324, 308, 292, 276, 260,
    244, 228, 212, 196, 180, 164, 148, 132,
    120, 112, 104, 96, 88, 80, 72, 64,
    56, 48, 40, 32, 24, 16, 8, 0
]

# μ-law encoding parameters
MULAW_BIAS = 0x84
MULAW_CLIP = 32635


def mulaw_to_linear16(mulaw_bytes: bytes) -> bytes:
    """
    Convert mulaw (µ-law) audio to linear16 (PCM).
    
    Args:
        mulaw_bytes: Raw mulaw audio bytes
        
    Returns:
        Raw linear16 (PCM) audio bytes
    """
    samples = array.array('h')
    for byte in mulaw_bytes:
        samples.append(MULAW_DECODE_TABLE[byte])
    return samples.tobytes()


def _encode_mulaw_sample(sample: int) -> int:
    """Encode a single 16-bit PCM sample to mulaw."""
    # Get the sign and magnitude
    sign = (sample >> 8) & 0x80
    if sign:
        sample = -sample
    
    # Clip the sample
    if sample > MULAW_CLIP:
        sample = MULAW_CLIP
    
    sample = sample + MULAW_BIAS
    
    # Find the segment
    exp = 7
    for i in range(8):
        if sample < (1 << (i + 8)):
            exp = i
            break
    
    # Compute the mantissa
    mant = (sample >> (exp + 3)) & 0x0F
    
    # Combine sign, exponent, and mantissa
    mulaw_byte = ~(sign | (exp << 4) | mant) & 0xFF
    
    return mulaw_byte


def linear16_to_mulaw(linear16_bytes: bytes) -> bytes:
    """
    Convert linear16 (PCM) audio to mulaw (µ-law).
    
    Args:
        linear16_bytes: Raw linear16 audio bytes
        
    Returns:
        Raw mulaw audio bytes
    """
    # Parse samples as signed 16-bit integers
    samples = array.array('h')
    samples.frombytes(linear16_bytes)
    
    mulaw_bytes = bytearray()
    for sample in samples:
        mulaw_bytes.append(_encode_mulaw_sample(sample))
    
    return bytes(mulaw_bytes)


def resample_audio(audio_bytes: bytes, from_rate: int, to_rate: int, sample_width: int = 2) -> bytes:
    """
    Resample audio to a different sample rate using linear interpolation.
    
    Args:
        audio_bytes: Raw audio bytes
        from_rate: Original sample rate (e.g., 8000)
        to_rate: Target sample rate (e.g., 16000)
        sample_width: Bytes per sample (2 for 16-bit)
        
    Returns:
        Resampled audio bytes
    """
    if from_rate == to_rate:
        return audio_bytes
    
    # Parse samples
    samples = array.array('h')
    samples.frombytes(audio_bytes)
    
    if len(samples) == 0:
        return audio_bytes
    
    ratio = to_rate / from_rate
    new_length = int(len(samples) * ratio)
    
    new_samples = array.array('h')
    for i in range(new_length):
        src_idx = i / ratio
        idx = int(src_idx)
        frac = src_idx - idx
        
        if idx + 1 < len(samples):
            # Linear interpolation
            sample = int(samples[idx] * (1 - frac) + samples[idx + 1] * frac)
        else:
            sample = samples[idx] if idx < len(samples) else 0
        
        # Clamp to 16-bit range
        sample = max(-32768, min(32767, sample))
        new_samples.append(sample)
    
    return new_samples.tobytes()


# -----------------------------------------------------------------------------
# Conversation State Tracker
# -----------------------------------------------------------------------------

class ConversationTracker:
    """Tracks conversation state and transcript."""
    
    def __init__(self, call_id: int, clinic_id: int, stream_sid: str):
        self.call_id = call_id
        self.clinic_id = clinic_id
        self.stream_sid = stream_sid
        self.turns: list[dict] = []
        self.started_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
        # Extracted info
        self.caller_name: Optional[str] = None
        self.is_new_patient: Optional[bool] = None
        self.reason_for_call: Optional[str] = None
        self.booked_appointment: Optional[datetime] = None
    
    def add_user_turn(self, text: str) -> None:
        """Add a user (caller) turn to the transcript."""
        self.turns.append({
            "role": "user",
            "content": text,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_activity = datetime.utcnow()
    
    def add_agent_turn(self, text: str) -> None:
        """Add an agent turn to the transcript."""
        self.turns.append({
            "role": "agent",
            "content": text,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_activity = datetime.utcnow()
    
    def get_transcript(self) -> str:
        """Get formatted transcript."""
        lines = []
        for turn in self.turns:
            role = "Caller" if turn["role"] == "user" else "Agent"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)
    
    def get_duration_seconds(self) -> int:
        """Get conversation duration in seconds."""
        return int((datetime.utcnow() - self.started_at).total_seconds())


# -----------------------------------------------------------------------------
# Twilio ↔ Deepgram Bridge
# -----------------------------------------------------------------------------

class VoiceAgentBridge:
    """
    Bridge between Twilio Media Streams and Deepgram Voice Agent.
    
    Handles bidirectional audio streaming and format conversion.
    """
    
    def __init__(
        self,
        twilio_ws,  # FastAPI WebSocket
        clinic,  # Client model
        call_id: int,
    ):
        """
        Initialize the bridge.
        
        Args:
            twilio_ws: FastAPI WebSocket connection from Twilio
            clinic: Client/Clinic model from database
            call_id: Database ID of the InboundCall record
        """
        self.twilio_ws = twilio_ws
        self.clinic = clinic
        self.call_id = call_id
        
        self.deepgram_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.stream_sid: Optional[str] = None
        self.twilio_call_sid: Optional[str] = None
        
        self.tracker: Optional[ConversationTracker] = None
        self.is_running = False
        self.mark_counter = 0
        
        # Build agent configuration
        self.prompt_builder = PromptBuilder(clinic)
        self.agent_config = self.prompt_builder.build_agent_config()
    
    async def connect_to_deepgram(self) -> bool:
        """
        Establish WebSocket connection to Deepgram Voice Agent.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not DEEPGRAM_API_KEY:
            logger.error("DEEPGRAM_API_KEY not configured")
            return False
        
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
        }
        
        try:
            self.deepgram_ws = await websockets.connect(
                DEEPGRAM_AGENT_URL,
                additional_headers=headers,
            )
            logger.info(f"Connected to Deepgram Voice Agent for call {self.call_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            return False
    
    async def send_agent_settings(self) -> None:
        """Send initial SettingsConfiguration message to Deepgram Voice Agent."""
        if not self.deepgram_ws:
            return
        
        # Configure the agent session using SettingsConfiguration format
        # Per Deepgram Voice Agent API (December 2025)
        settings = {
            "type": "SettingsConfiguration",
            "audio": {
                "encoding": "linear16",
                "sample_rate": DEEPGRAM_SAMPLE_RATE,  # 8000 Hz
            },
            "agent": {
                "listen": {
                    "model": "nova-3"  # Latest STT model
                },
                "think": {
                    "provider": {
                        "type": "openai",
                        "model": "gpt-4o-mini"
                    },
                    "instructions": self.agent_config["system_prompt"],
                    "functions": self.agent_config["functions"],
                },
                "speak": {
                    "model": self.agent_config["voice_id"]  # e.g., "aura-2-zeus-en"
                }
            },
            "context": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": self.agent_config["greeting_message"]
                    }
                ],
                "replay": True  # Speak the greeting immediately
            }
        }
        
        await self.deepgram_ws.send(json.dumps(settings))
        logger.info(f"Sent SettingsConfiguration for call {self.call_id}")
    
    async def handle_twilio_message(self, message: dict) -> None:
        """
        Handle incoming message from Twilio Media Stream.
        
        Message types:
        - connected: WebSocket connected
        - start: Media stream started
        - media: Audio data
        - stop: Media stream stopped
        - mark: Audio playback marker
        """
        event_type = message.get("event")
        
        if event_type == "connected":
            logger.info(f"Twilio connected for call {self.call_id}")
            
        elif event_type == "start":
            # Extract stream info
            start_data = message.get("start", {})
            self.stream_sid = start_data.get("streamSid")
            self.twilio_call_sid = start_data.get("callSid")
            
            # Initialize conversation tracker
            self.tracker = ConversationTracker(
                call_id=self.call_id,
                clinic_id=self.clinic.id,
                stream_sid=self.stream_sid or ""
            )
            
            logger.info(f"Stream started: streamSid={self.stream_sid}, callSid={self.twilio_call_sid}")
            
            # Connect to Deepgram and configure
            if await self.connect_to_deepgram():
                await self.send_agent_settings()
                # Start listening for Deepgram responses
                asyncio.create_task(self._deepgram_listener())
            else:
                # Deepgram connection failed - send error audio to caller
                logger.error(f"Failed to connect to Deepgram for call {self.call_id}")
                await self._send_error_message_to_twilio(
                    "We're sorry, we're experiencing technical difficulties. "
                    "Please call back in a few minutes or leave a message after the tone."
                )
            
        elif event_type == "media":
            # Process incoming audio from caller
            await self._process_twilio_audio(message.get("media", {}))
            
        elif event_type == "stop":
            logger.info(f"Stream stopped for call {self.call_id}")
            self.is_running = False
            
        elif event_type == "mark":
            # Audio playback completed marker
            mark_name = message.get("mark", {}).get("name")
            logger.debug(f"Mark received: {mark_name}")
    
    async def _process_twilio_audio(self, media: dict) -> None:
        """Process audio chunk from Twilio and forward to Deepgram."""
        if not self.deepgram_ws:
            return
        
        # Decode base64 audio
        payload = media.get("payload", "")
        if not payload:
            return
        
        try:
            # Twilio sends mulaw, base64-encoded at 8kHz
            mulaw_audio = base64.b64decode(payload)
            
            # Convert mulaw → linear16 (still 8kHz)
            linear16_audio = mulaw_to_linear16(mulaw_audio)
            
            # Deepgram accepts 8kHz directly, no resampling needed
            # Send as AudioData JSON message per API spec
            audio_msg = {
                "type": "AudioData",
                "audio_data": base64.b64encode(linear16_audio).decode("utf-8")
            }
            await self.deepgram_ws.send(json.dumps(audio_msg))
            
        except Exception as e:
            logger.error(f"Error processing Twilio audio: {e}")
    
    async def _deepgram_listener(self) -> None:
        """Listen for messages from Deepgram Voice Agent."""
        if not self.deepgram_ws:
            return
        
        self.is_running = True
        
        try:
            async for message in self.deepgram_ws:
                if not self.is_running:
                    break
                
                # Deepgram sends JSON messages (text format)
                # Parse and handle based on message type
                try:
                    event = json.loads(message)
                    await self._handle_deepgram_event(event)
                except json.JSONDecodeError:
                    # If it's binary, it might be raw audio (fallback)
                    if isinstance(message, bytes):
                        await self._send_audio_to_twilio(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Deepgram connection closed for call {self.call_id}")
        except Exception as e:
            logger.error(f"Error in Deepgram listener: {e}")
        finally:
            self.is_running = False
    
    async def _handle_deepgram_event(self, event: dict) -> None:
        """Handle event message from Deepgram Voice Agent."""
        event_type = event.get("type")
        
        if event_type == "UserStartedSpeaking":
            logger.debug("User started speaking")
            # Could use this to interrupt agent playback
            
        elif event_type == "UtteranceEnd":
            # User finished speaking
            pass
        
        elif event_type == "ConversationAudio":
            # TTS audio from agent (base64-encoded linear16)
            audio_data = event.get("audio_data")
            if audio_data:
                audio_bytes = base64.b64decode(audio_data)
                await self._send_audio_to_twilio(audio_bytes)
            
        elif event_type == "ConversationText":
            # Transcript of what was said
            role = event.get("role")
            content = event.get("content", "")
            
            if self.tracker:
                if role == "user":
                    self.tracker.add_user_turn(content)
                    logger.info(f"Caller: {content}")
                elif role == "assistant":
                    self.tracker.add_agent_turn(content)
                    logger.info(f"Agent: {content}")
        
        elif event_type == "ConversationFunctionCall":
            # Agent wants to call a function (new format)
            await self._handle_function_call(event)
                    
        elif event_type == "FunctionCallRequest":
            # Agent wants to call a function (legacy format)
            await self._handle_function_call(event)
            
        elif event_type == "AgentAudioDone":
            # Agent finished speaking
            # Send mark to track when audio completes
            await self._send_mark_to_twilio()
            
        elif event_type == "Error":
            error_msg = event.get("message", "Unknown error")
            logger.error(f"Deepgram error: {error_msg}")
    
    async def _handle_function_call(self, event: dict) -> None:
        """Handle function call request from Deepgram agent."""
        # Support both old (FunctionCallRequest) and new (ConversationFunctionCall) formats
        function_name = event.get("function_name")
        function_id = event.get("function_call_id")
        arguments = event.get("input") or event.get("function_arguments") or {}
        
        logger.info(f"Function call: {function_name}({arguments})")
        
        result = {}
        
        if function_name == "book_appointment":
            # In production, integrate with clinic's scheduling system
            result = {
                "success": True,
                "message": f"Appointment booked for {arguments.get('patient_name')} on {arguments.get('date')} at {arguments.get('time')}"
            }
            
            # Track booking in conversation
            if self.tracker:
                self.tracker.caller_name = arguments.get("patient_name")
                self.tracker.is_new_patient = arguments.get("is_new_patient")
                self.tracker.reason_for_call = arguments.get("reason")
                
        elif function_name == "check_availability":
            # In production, query scheduling system
            result = {
                "available_slots": [
                    "9:00 AM",
                    "10:30 AM",
                    "2:00 PM",
                    "3:30 PM"
                ]
            }
            
        elif function_name == "transfer_to_human":
            result = {
                "success": True,
                "message": "Transferring to team member..."
            }
            # In production, initiate call transfer here
            
        elif function_name == "take_message":
            result = {
                "success": True,
                "message": "Message recorded. Our team will call you back."
            }
        
        # Send function result back to Deepgram
        if self.deepgram_ws:
            response = {
                "type": "FunctionCallResponse",
                "function_call_id": function_id,
                "output": json.dumps(result)
            }
            await self.deepgram_ws.send(json.dumps(response))
    
    async def _send_audio_to_twilio(self, audio_bytes: bytes) -> None:
        """Send TTS audio from Deepgram back to Twilio."""
        if not self.stream_sid:
            return
        
        try:
            # Deepgram sends linear16 at 8kHz (same as our configured sample rate)
            # No resampling needed since we're using 8kHz throughout
            
            # Convert linear16 → mulaw for Twilio
            mulaw_audio = linear16_to_mulaw(audio_bytes)
            
            # Base64 encode for Twilio
            payload = base64.b64encode(mulaw_audio).decode("utf-8")
            
            # Send media message to Twilio
            message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {
                    "payload": payload
                }
            }
            
            await self.twilio_ws.send_json(message)
            
        except Exception as e:
            logger.error(f"Error sending audio to Twilio: {e}")
    
    async def _send_mark_to_twilio(self) -> None:
        """Send a mark message to Twilio for audio synchronization."""
        if not self.stream_sid:
            return
        
        self.mark_counter += 1
        mark_name = f"mark_{self.mark_counter}"
        
        message = {
            "event": "mark",
            "streamSid": self.stream_sid,
            "mark": {
                "name": mark_name
            }
        }
        
        try:
            await self.twilio_ws.send_json(message)
        except Exception as e:
            logger.error(f"Error sending mark to Twilio: {e}")
    
    async def _send_error_message_to_twilio(self, message_text: str) -> None:
        """
        Send a spoken error message to the caller using Twilio's TTS.
        
        This is used when Deepgram fails to connect. We use Twilio's
        built-in TTS as a fallback since we can't use Deepgram.
        
        Note: This uses a simple approach of sending a "clear" event
        followed by synthesized speech. In production, you might want
        to use Deepgram's TTS API directly or pre-recorded audio.
        """
        if not self.stream_sid:
            return
        
        logger.info(f"Sending error message to caller: {message_text[:50]}...")
        
        # For now, we'll just log it - Twilio Media Streams don't support
        # direct TTS injection. The caller will hear silence and then disconnect.
        # A better approach is to handle this at the TwiML level with <Say> fallback.
        
        # Close the stream gracefully
        try:
            await self.twilio_ws.send_json({
                "event": "clear",
                "streamSid": self.stream_sid
            })
        except Exception as e:
            logger.error(f"Error sending clear to Twilio: {e}")
    
    async def run(self) -> dict:
        """
        Main loop - process messages from Twilio.
        
        Returns:
            Dict with conversation summary
        """
        try:
            # Process Twilio messages
            while True:
                try:
                    message = await self.twilio_ws.receive_json()
                    await self.handle_twilio_message(message)
                    
                    # Check for stop event
                    if message.get("event") == "stop":
                        break
                        
                except Exception as e:
                    logger.error(f"Error receiving from Twilio: {e}")
                    break
                    
        finally:
            # Cleanup
            await self.cleanup()
        
        # Return conversation summary
        return self.get_summary()
    
    async def cleanup(self) -> None:
        """Clean up connections."""
        self.is_running = False
        
        if self.deepgram_ws:
            try:
                await self.deepgram_ws.close()
            except Exception:
                pass
    
    def get_summary(self) -> dict:
        """Get conversation summary."""
        if not self.tracker:
            return {
                "call_id": self.call_id,
                "duration_seconds": 0,
                "transcript": "",
                "turns": []
            }
        
        return {
            "call_id": self.call_id,
            "stream_sid": self.stream_sid,
            "duration_seconds": self.tracker.get_duration_seconds(),
            "transcript": self.tracker.get_transcript(),
            "turns": self.tracker.turns,
            "caller_name": self.tracker.caller_name,
            "is_new_patient": self.tracker.is_new_patient,
            "reason_for_call": self.tracker.reason_for_call,
            "booked_appointment": self.tracker.booked_appointment.isoformat() if self.tracker.booked_appointment else None,
        }


# -----------------------------------------------------------------------------
# WebSocket Handler for FastAPI
# -----------------------------------------------------------------------------

async def handle_voice_websocket(websocket, clinic, call_id: int) -> dict:
    """
    Handle a voice WebSocket connection.
    
    This is called from the FastAPI route handler.
    
    Args:
        websocket: FastAPI WebSocket connection
        clinic: Client/Clinic model from database
        call_id: Database ID of the InboundCall record
        
    Returns:
        Dict with conversation summary
    """
    bridge = VoiceAgentBridge(
        twilio_ws=websocket,
        clinic=clinic,
        call_id=call_id
    )
    
    return await bridge.run()
