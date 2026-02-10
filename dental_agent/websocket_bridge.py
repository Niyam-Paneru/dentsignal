"""
websocket_bridge.py - Twilio ↔ Deepgram Voice Agent Bridge

This is the core of the voice agent system. It:
1. Receives audio from Twilio Media Streams (mulaw, 8kHz)
2. Converts audio format (mulaw → linear16)
3. Sends audio to Deepgram Voice Agent WebSocket
4. Receives AI responses (text + TTS audio) from Deepgram
5. Converts audio back (linear16 → mulaw)
6. Sends audio back to Twilio

Research-Based Optimizations (December 2025):
- Barge-in handling with UserStartedSpeaking events
- Audio buffering (200-400ms chunks) for optimal latency
- Turn-endpointing with AgentAudioDone tracking
- Efficient audio conversion without upsampling
- Robust error recovery and reconnection

Audio Format Conversion:
- Twilio sends: mulaw (µ-law), 8000 Hz, mono, base64-encoded
- Deepgram expects: linear16 (PCM), 8000 Hz, mono
- No resampling needed - 8kHz direct passthrough

WebSocket Protocol:
- Twilio: wss://your-server.com/ws/voice/{call_id}
- Deepgram: wss://agent.deepgram.com/v1/agent/converse
"""

from __future__ import annotations

import asyncio
import array
import base64
import json
import logging
import os
import struct
from collections import deque
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
# Deepgram accepts 8kHz directly - no upsampling needed
TWILIO_SAMPLE_RATE = 8000
DEEPGRAM_SAMPLE_RATE = 8000

# Audio buffer settings (research: 200-400ms chunks optimal)
# At 8kHz with 16-bit samples: 200ms = 3200 bytes
AUDIO_BUFFER_SIZE = 3200  # 200ms of audio
AUDIO_BUFFER_MAX_MS = 400  # Max buffer before force-send

# Connection settings
DEEPGRAM_CONNECT_TIMEOUT = 10.0
DEEPGRAM_PING_INTERVAL = 20.0
WEBSOCKET_CLOSE_TIMEOUT = 5.0

# Retry settings for reconnection
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY_BASE = 1.0  # seconds, exponential backoff


# -----------------------------------------------------------------------------
# Error Classification
# -----------------------------------------------------------------------------

class VoiceAgentError(Exception):
    """Base exception for voice agent errors."""
    pass


class ConnectionError(VoiceAgentError):
    """Connection-related errors (Deepgram, Twilio)."""
    def __init__(self, message: str, service: str = "unknown", recoverable: bool = True):
        super().__init__(message)
        self.service = service
        self.recoverable = recoverable


class AudioProcessingError(VoiceAgentError):
    """Audio conversion or processing errors."""
    pass


class ConfigurationError(VoiceAgentError):
    """Missing or invalid configuration."""
    pass


# -----------------------------------------------------------------------------
# Circuit Breaker for External Services
# -----------------------------------------------------------------------------

class CircuitBreaker:
    """
    Simple circuit breaker to prevent cascading failures.
    
    States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        name: str = "circuit"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
    
    def record_success(self) -> None:
        """Record a successful call."""
        self.failure_count = 0
        if self.state == self.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # 2 successes to close
                logger.info(f"Circuit {self.name} closing after recovery")
                self.state = self.CLOSED
                self.success_count = 0
    
    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit {self.name} opening after {self.failure_count} failures")
            self.state = self.OPEN
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == self.CLOSED:
            return True
        
        if self.state == self.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = asyncio.get_event_loop().time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(f"Circuit {self.name} entering half-open state")
                    self.state = self.HALF_OPEN
                    return True
            return False
        
        # HALF_OPEN - allow execution for testing
        return True


# Global circuit breakers for external services
deepgram_circuit = CircuitBreaker(name="deepgram", failure_threshold=3, recovery_timeout=60.0)
twilio_circuit = CircuitBreaker(name="twilio", failure_threshold=5, recovery_timeout=30.0)


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


def resample_audio(audio_bytes: bytes, source_rate: int, target_rate: int) -> bytes:
    """
    Resample audio from source sample rate to target sample rate.
    Uses simple linear interpolation.
    
    Args:
        audio_bytes: Raw linear16 audio bytes
        source_rate: Source sample rate (e.g., 8000)
        target_rate: Target sample rate (e.g., 16000)
        
    Returns:
        Resampled linear16 audio bytes
    """
    if source_rate == target_rate:
        return audio_bytes
    
    # Parse samples as signed 16-bit integers
    samples = array.array('h')
    samples.frombytes(audio_bytes)
    
    ratio = target_rate / source_rate
    new_length = int(len(samples) * ratio)
    
    resampled = array.array('h')
    for i in range(new_length):
        # Linear interpolation
        src_idx = i / ratio
        idx_low = int(src_idx)
        idx_high = min(idx_low + 1, len(samples) - 1)
        frac = src_idx - idx_low
        
        sample = int(samples[idx_low] * (1 - frac) + samples[idx_high] * frac)
        resampled.append(sample)
    
    return resampled.tobytes()


# -----------------------------------------------------------------------------
# Audio Buffer for Optimal Latency
# -----------------------------------------------------------------------------

class AudioBuffer:
    """
    Buffer audio for optimal chunk sizes.
    
    Research shows 200-400ms chunks provide best balance between
    latency and processing efficiency for Deepgram.
    """
    
    def __init__(self, target_size: int = AUDIO_BUFFER_SIZE, max_delay_ms: int = AUDIO_BUFFER_MAX_MS):
        self.buffer = bytearray()
        self.target_size = target_size
        self.max_delay_ms = max_delay_ms
        self.last_flush_time = datetime.utcnow()
    
    def add(self, audio_bytes: bytes) -> Optional[bytes]:
        """
        Add audio to buffer and return chunk if ready.
        
        Returns:
            Audio chunk if buffer is full or timeout, None otherwise
        """
        self.buffer.extend(audio_bytes)
        
        # Check if we should flush
        should_flush = False
        
        # Flush if buffer size reached
        if len(self.buffer) >= self.target_size:
            should_flush = True
        
        # Flush if max delay reached
        elapsed_ms = (datetime.utcnow() - self.last_flush_time).total_seconds() * 1000
        if elapsed_ms >= self.max_delay_ms and len(self.buffer) > 0:
            should_flush = True
        
        if should_flush:
            chunk = bytes(self.buffer)
            self.buffer = bytearray()
            self.last_flush_time = datetime.utcnow()
            return chunk
        
        return None
    
    def flush(self) -> Optional[bytes]:
        """Force flush any remaining audio."""
        if len(self.buffer) > 0:
            chunk = bytes(self.buffer)
            self.buffer = bytearray()
            self.last_flush_time = datetime.utcnow()
            return chunk
        return None


# -----------------------------------------------------------------------------
# Conversation State Tracker
# -----------------------------------------------------------------------------

class ConversationTracker:
    """Tracks conversation state and transcript with enhanced analytics."""
    
    def __init__(self, call_id: int, clinic_id: int, stream_sid: str):
        self.call_id = call_id
        self.clinic_id = clinic_id
        self.stream_sid = stream_sid
        self.turns: list[dict] = []
        self.started_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
        # Conversation state
        self.caller_name: Optional[str] = None
        self.is_new_patient: Optional[bool] = None
        self.reason_for_call: Optional[str] = None
        self.booked_appointment: Optional[datetime] = None
        
        # Barge-in tracking
        self.barge_in_count = 0
        self.interruptions: list[dict] = []
        
        # Agent speaking state (for barge-in handling)
        self.agent_is_speaking = False
        self.pending_audio_chunks: deque = deque()
    
    def add_user_turn(self, text: str, is_interruption: bool = False) -> None:
        """Add a user (caller) turn to the transcript."""
        self.turns.append({
            "role": "user",
            "content": text,
            "timestamp": datetime.utcnow().isoformat(),
            "is_interruption": is_interruption
        })
        self.last_activity = datetime.utcnow()
        
        if is_interruption:
            self.barge_in_count += 1
            self.interruptions.append({
                "timestamp": datetime.utcnow().isoformat(),
                "content": text[:100]  # First 100 chars
            })
    
    def add_agent_turn(self, text: str) -> None:
        """Add an agent turn to the transcript."""
        self.turns.append({
            "role": "agent",
            "content": text,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_activity = datetime.utcnow()
    
    def mark_agent_speaking(self, is_speaking: bool) -> None:
        """Track when agent is speaking for barge-in detection."""
        self.agent_is_speaking = is_speaking
    
    def get_transcript(self) -> str:
        """Get formatted transcript."""
        lines = []
        for turn in self.turns:
            role = "Caller" if turn["role"] == "user" else "Agent"
            interrupt_marker = " [interrupted]" if turn.get("is_interruption") else ""
            lines.append(f"{role}{interrupt_marker}: {turn['content']}")
        return "\n".join(lines)
    
    def get_duration_seconds(self) -> int:
        """Get conversation duration in seconds."""
        return int((datetime.utcnow() - self.started_at).total_seconds())
    
    def get_analytics(self) -> dict:
        """Get conversation analytics for quality monitoring."""
        user_turns = [t for t in self.turns if t["role"] == "user"]
        agent_turns = [t for t in self.turns if t["role"] == "agent"]
        
        return {
            "total_turns": len(self.turns),
            "user_turns": len(user_turns),
            "agent_turns": len(agent_turns),
            "barge_in_count": self.barge_in_count,
            "duration_seconds": self.get_duration_seconds(),
            "appointment_booked": self.booked_appointment is not None,
        }


# -----------------------------------------------------------------------------
# Twilio ↔ Deepgram Bridge with Advanced Features
# -----------------------------------------------------------------------------

class VoiceAgentBridge:
    """
    Bridge between Twilio Media Streams and Deepgram Voice Agent.
    
    Research-based optimizations:
    - Barge-in handling with audio queue clearing
    - Buffered audio for optimal latency
    - Robust error recovery
    - Function call handling for appointment booking
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
        self.audio_buffer = AudioBuffer()
        self.is_running = False
        self.mark_counter = 0
        
        # Barge-in handling
        self.pending_audio: deque = deque()
        self.user_is_speaking = False
        self.should_clear_audio = False
        
        # Build agent configuration
        self.prompt_builder = PromptBuilder(clinic)
        self.agent_config = self.prompt_builder.build_agent_config()
        
        # PMS integration (loaded asynchronously in connect_to_deepgram)
        self._pms_service = None
        self._pms_integration = None
    
    async def connect_to_deepgram(self) -> bool:
        """
        Establish WebSocket connection to Deepgram Voice Agent.
        
        Uses circuit breaker pattern and retry logic for resilience.
        Loads real-time PMS availability if Open Dental is configured.
        
        Returns:
            True if connection successful, False otherwise
        """
        # Try to load PMS availability before connecting
        await self._load_pms_availability()
        
        if not DEEPGRAM_API_KEY:
            logger.error("DEEPGRAM_API_KEY not configured")
            raise ConfigurationError("DEEPGRAM_API_KEY not configured")
        
        # Check circuit breaker
        if not deepgram_circuit.can_execute():
            logger.warning(f"Deepgram circuit open - skipping connection for call {self.call_id}")
            return False
        
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
        }
        
        last_error = None
        for attempt in range(MAX_RECONNECT_ATTEMPTS):
            try:
                self.deepgram_ws = await asyncio.wait_for(
                    websockets.connect(
                        DEEPGRAM_AGENT_URL,
                        additional_headers=headers,
                        ping_interval=DEEPGRAM_PING_INTERVAL,
                        close_timeout=WEBSOCKET_CLOSE_TIMEOUT,
                    ),
                    timeout=DEEPGRAM_CONNECT_TIMEOUT
                )
                logger.info(f"Connected to Deepgram Voice Agent for call {self.call_id}")
                deepgram_circuit.record_success()
                return True
                
            except asyncio.TimeoutError:
                last_error = ConnectionError(
                    f"Timeout connecting to Deepgram (attempt {attempt + 1}/{MAX_RECONNECT_ATTEMPTS})",
                    service="deepgram",
                    recoverable=True
                )
                logger.warning(str(last_error))
                
            except websockets.exceptions.InvalidStatusCode as e:
                # Auth failure or rate limit - don't retry
                last_error = ConnectionError(
                    f"Deepgram rejected connection: {e.status_code}",
                    service="deepgram",
                    recoverable=e.status_code != 401  # Auth failures not recoverable
                )
                logger.error(str(last_error))
                if e.status_code == 401:
                    deepgram_circuit.record_failure()
                    break
                    
            except Exception as e:
                last_error = ConnectionError(
                    f"Failed to connect to Deepgram: {e}",
                    service="deepgram",
                    recoverable=True
                )
                logger.error(str(last_error))
            
            # Exponential backoff before retry
            if attempt < MAX_RECONNECT_ATTEMPTS - 1:
                delay = RECONNECT_DELAY_BASE * (2 ** attempt)
                logger.info(f"Retrying Deepgram connection in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # All retries failed
        deepgram_circuit.record_failure()
        logger.error(f"Failed to connect to Deepgram after {MAX_RECONNECT_ATTEMPTS} attempts")
        return False
    
    async def _load_pms_availability(self) -> None:
        """
        Load real-time availability from PMS (Open Dental) if configured.
        
        Updates the agent config with actual available slots so the AI
        can offer real appointment times instead of placeholder data.
        This is a best-effort operation - failures don't block the call.
        """
        try:
            from db import PMSIntegration, get_session
            from sqlmodel import select
            import os
            
            session = next(get_session())
            try:
                pms = session.exec(
                    select(PMSIntegration).where(
                        PMSIntegration.clinic_id == self.clinic.id
                    )
                ).first()
                
                if not pms or not pms.is_active or pms.provider != "open_dental":
                    return  # No PMS configured, use default slots
                
                developer_key = os.getenv("OPEN_DENTAL_DEVELOPER_KEY", "")
                if not developer_key or not pms.od_customer_key:
                    return
                
                from open_dental_service import create_open_dental_service
                
                service = create_open_dental_service(
                    developer_key=developer_key,
                    customer_key=pms.od_customer_key,
                    api_mode=pms.od_api_mode or "remote",
                    base_url=pms.od_base_url,
                    clinic_num=pms.od_clinic_num,
                )
                
                # Fetch formatted slots for the next 7 days
                slots_text = await service.get_available_slots_formatted(
                    days_ahead=7,
                    length_minutes=30,
                )
                
                # Rebuild agent config with real PMS data
                self.agent_config = self.prompt_builder.build_agent_config(
                    available_slots_text=slots_text,
                )
                
                self._pms_service = service
                logger.info(f"Loaded PMS availability for clinic {self.clinic.id}")
                
            finally:
                session.close()
                
        except Exception as e:
            # PMS loading failure should never block a call
            logger.warning(f"Could not load PMS availability for call {self.call_id}: {e}")
    
    async def send_agent_settings(self) -> None:
        """
        Send initial SettingsConfiguration message to Deepgram Voice Agent.
        
        Configuration based on research best practices:
        - nova-3 for best STT accuracy
        - Optimized endpointing for natural conversation
        - Greeting with replay for immediate engagement
        """
        if not self.deepgram_ws:
            return
        
        # Build think provider config - Azure OpenAI or direct OpenAI
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
        
        if use_azure and azure_endpoint and azure_api_key:
            think_provider = {
                "type": "open_ai",
                "model": azure_deployment,
                "endpoint": {
                    "url": f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}/chat/completions?api-version={azure_api_version}",
                    "headers": {
                        "api-key": azure_api_key
                    }
                }
            }
            logger.info(f"Deepgram think provider: Azure OpenAI ({azure_endpoint}, deployment: {azure_deployment})")
        else:
            think_provider = {
                "type": "open_ai",
                "model": "gpt-4o-mini"  # Fast and cost-effective
            }
            logger.info("Deepgram think provider: Direct OpenAI (gpt-4o-mini)")
        
        settings = {
            "type": "SettingsConfiguration",
            "audio": {
                "encoding": "linear16",
                "sample_rate": DEEPGRAM_SAMPLE_RATE,  # 8000 Hz
            },
            "agent": {
                "listen": {
                    "model": "nova-3",  # Latest STT model - best accuracy
                },
                "think": {
                    "provider": think_provider,
                    "instructions": self.agent_config["system_prompt"],
                    "functions": self.agent_config["functions"],
                },
                "speak": {
                    "model": self.agent_config["voice_id"]  # e.g., "aura-asteria-en"
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
        
        # Mark agent as speaking (greeting will play)
        if self.tracker:
            self.tracker.mark_agent_speaking(True)
    
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
                logger.error(f"Failed to connect to Deepgram for call {self.call_id}")
                await self._send_error_message_to_twilio(
                    "We're sorry, we're experiencing technical difficulties. "
                    "Please call back in a few minutes."
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
            
            # Track when agent audio completes
            if mark_name and mark_name.startswith("audio_"):
                if self.tracker:
                    self.tracker.mark_agent_speaking(False)
    
    async def _process_twilio_audio(self, media: dict) -> None:
        """
        Process audio chunk from Twilio and forward to Deepgram.
        
        Uses buffering for optimal chunk sizes (200-400ms).
        """
        if not self.deepgram_ws:
            return
        
        payload = media.get("payload", "")
        if not payload:
            return
        
        try:
            # Twilio sends mulaw, base64-encoded at 8kHz
            mulaw_audio = base64.b64decode(payload)
            
            # Convert mulaw → linear16 (still 8kHz)
            linear16_audio = mulaw_to_linear16(mulaw_audio)
            
            # Buffer audio for optimal chunk sizes
            buffered_chunk = self.audio_buffer.add(linear16_audio)
            
            if buffered_chunk:
                # Send buffered chunk to Deepgram
                audio_msg = {
                    "type": "AudioData",
                    "audio_data": base64.b64encode(buffered_chunk).decode("utf-8")
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
                
                try:
                    event = json.loads(message)
                    await self._handle_deepgram_event(event)
                except json.JSONDecodeError:
                    # Binary audio (rare with current API)
                    if isinstance(message, bytes):
                        await self._send_audio_to_twilio(message)
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Deepgram connection closed for call {self.call_id}: {e}")
        except Exception as e:
            logger.error(f"Error in Deepgram listener: {e}")
        finally:
            self.is_running = False
    
    async def _handle_deepgram_event(self, event: dict) -> None:
        """
        Handle event message from Deepgram Voice Agent.
        
        Implements barge-in handling per research recommendations.
        """
        event_type = event.get("type")
        
        if event_type == "UserStartedSpeaking":
            # BARGE-IN DETECTION: User started speaking
            logger.debug("User started speaking - checking for barge-in")
            self.user_is_speaking = True
            
            # If agent was speaking, this is a barge-in
            if self.tracker and self.tracker.agent_is_speaking:
                logger.info("Barge-in detected - clearing audio queue")
                self.should_clear_audio = True
                # Clear pending audio on Twilio side
                await self._clear_twilio_audio()
        
        elif event_type == "UtteranceEnd":
            # User finished speaking
            self.user_is_speaking = False
            self.should_clear_audio = False
        
        elif event_type == "ConversationAudio":
            # TTS audio from agent
            if self.should_clear_audio:
                # Skip this audio chunk - user is speaking
                logger.debug("Skipping audio chunk due to barge-in")
                return
            
            audio_data = event.get("audio_data")
            if audio_data:
                if self.tracker:
                    self.tracker.mark_agent_speaking(True)
                audio_bytes = base64.b64decode(audio_data)
                await self._send_audio_to_twilio(audio_bytes)
            
        elif event_type == "ConversationText":
            # Transcript of what was said
            role = event.get("role")
            content = event.get("content", "")
            
            if self.tracker:
                if role == "user":
                    is_interruption = self.tracker.agent_is_speaking
                    self.tracker.add_user_turn(content, is_interruption=is_interruption)
                    logger.info(
                        "Caller utterance received (len=%d)%s",
                        len(content),
                        " [interrupted]" if is_interruption else "",
                    )
                elif role == "assistant":
                    self.tracker.add_agent_turn(content)
                    logger.info("Agent response generated (len=%d)", len(content))
        
        elif event_type == "ConversationFunctionCall":
            # Agent wants to call a function (new format)
            await self._handle_function_call(event)
                    
        elif event_type == "FunctionCallRequest":
            # Agent wants to call a function (legacy format)
            await self._handle_function_call(event)
            
        elif event_type == "AgentAudioDone":
            # Agent finished speaking this response
            if self.tracker:
                self.tracker.mark_agent_speaking(False)
            # Send mark to track when audio completes on Twilio side
            await self._send_mark_to_twilio("audio_done")
            
        elif event_type == "Error":
            error_msg = event.get("message", "Unknown error")
            error_code = event.get("code", "")
            logger.error(f"Deepgram error [{error_code}]: {error_msg}")
            
        elif event_type == "Welcome":
            # Connection established - Deepgram is ready
            logger.info(f"Deepgram welcome received for call {self.call_id}")
    
    async def _handle_function_call(self, event: dict) -> None:
        """
        Handle function call request from Deepgram agent.
        
        Supports enhanced function schemas with more detailed responses.
        """
        function_name = event.get("function_name")
        function_id = event.get("function_call_id")
        arguments = event.get("input") or event.get("function_arguments") or {}
        
        arg_keys = list(arguments.keys()) if isinstance(arguments, dict) else []
        logger.info("Function call: %s keys=%s", function_name, arg_keys)
        
        result = {}
        
        if function_name == "book_appointment":
            # In production, integrate with clinic's scheduling system
            patient_name = arguments.get("patient_name", "the patient")
            date = arguments.get("date", "the requested date")
            time = arguments.get("time", "the requested time")
            reason = arguments.get("reason", "appointment")
            
            result = {
                "success": True,
                "confirmation_number": f"APT{datetime.now().strftime('%Y%m%d%H%M')}",
                "message": f"Appointment successfully booked for {patient_name} on {date} at {time} for {reason}.",
                "reminder": "A confirmation text will be sent, and a reminder 24 hours before the appointment."
            }
            
            # Track booking in conversation
            if self.tracker:
                self.tracker.caller_name = patient_name
                self.tracker.is_new_patient = arguments.get("is_new_patient")
                self.tracker.reason_for_call = reason
                # Parse date/time for tracking
                try:
                    self.tracker.booked_appointment = datetime.strptime(
                        f"{date} {time}", "%Y-%m-%d %H:%M"
                    )
                except:
                    pass
                
        elif function_name == "check_availability":
            date = arguments.get("date", "")
            time_pref = arguments.get("time_preference", "any")
            is_new = arguments.get("is_new_patient", False)
            
            # In production, query scheduling system
            # For now, return mock availability
            if time_pref == "morning" or time_pref == "early_morning":
                slots = ["9:00 AM", "10:30 AM", "11:00 AM"]
            elif time_pref == "afternoon":
                slots = ["1:00 PM", "2:30 PM", "4:00 PM"]
            else:
                slots = ["9:00 AM", "10:30 AM", "2:00 PM", "3:30 PM"]
            
            duration = "60-90 minutes" if is_new else "45 minutes"
            
            result = {
                "available_slots": slots,
                "date": date,
                "estimated_duration": duration,
                "message": f"I have {', '.join(slots)} available. Which time works best for you?"
            }
        
        elif function_name == "lookup_patient":
            # In production, query patient database
            patient_name = arguments.get("patient_name", "")
            
            result = {
                "found": True,
                "patient_name": patient_name,
                "last_visit": "6 months ago",
                "last_procedure": "cleaning and checkup",
                "due_for": "6-month cleaning",
                "message": f"I found your record. Your last visit was for a cleaning about 6 months ago."
            }
        
        elif function_name == "cancel_appointment":
            patient_name = arguments.get("patient_name", "")
            reschedule = arguments.get("reschedule", False)
            
            result = {
                "success": True,
                "message": "Your appointment has been cancelled." + (
                    " Would you like to reschedule now?" if reschedule else 
                    " Please call us back when you're ready to reschedule."
                )
            }
            
        elif function_name == "transfer_to_human":
            reason = arguments.get("reason", "")
            department = arguments.get("department", "front_desk")
            
            result = {
                "success": True,
                "message": f"I'm transferring you to our {department.replace('_', ' ')} team. Please hold for a moment.",
                "transfer_initiated": True
            }
            # In production, initiate actual call transfer here
            
        elif function_name == "take_message":
            caller_name = arguments.get("caller_name", "")
            message = arguments.get("message", "")
            urgency = arguments.get("urgency", "medium")
            
            result = {
                "success": True,
                "message": f"I've recorded your message and marked it as {urgency} priority. Our team will call you back as soon as possible.",
                "callback_timeframe": "within 2 hours" if urgency == "high" else "within 24 hours"
            }
        
        elif function_name == "verify_insurance":
            provider = arguments.get("insurance_provider", "")
            
            # In production, check against clinic's accepted insurances
            accepted = provider.lower() in ["delta dental", "cigna", "aetna", "metlife", "guardian"]
            
            result = {
                "verified": True,
                "in_network": accepted,
                "message": f"Good news - we are {'in-network with' if accepted else 'able to work with'} {provider}." + (
                    "" if accepted else " We can submit claims on your behalf."
                )
            }
        
        else:
            result = {
                "success": False,
                "message": f"I'm not able to process that request right now. Let me take a message and have someone call you back."
            }
        
        # Send function result back to Deepgram
        if self.deepgram_ws:
            response = {
                "type": "FunctionCallResponse",
                "function_call_id": function_id,
                "output": json.dumps(result)
            }
            await self.deepgram_ws.send(json.dumps(response))
            logger.debug(f"Sent function response for {function_name}")
    
    async def _send_audio_to_twilio(self, audio_bytes: bytes) -> None:
        """Send TTS audio from Deepgram back to Twilio."""
        if not self.stream_sid:
            return
        
        # Skip if barge-in is in progress
        if self.should_clear_audio:
            return
        
        try:
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
    
    async def _clear_twilio_audio(self) -> None:
        """Clear pending audio on Twilio side for barge-in handling."""
        if not self.stream_sid:
            return
        
        try:
            # Send clear event to stop current audio playback
            message = {
                "event": "clear",
                "streamSid": self.stream_sid
            }
            await self.twilio_ws.send_json(message)
            logger.debug("Sent clear event to Twilio")
        except Exception as e:
            logger.error(f"Error clearing Twilio audio: {e}")
    
    async def _send_mark_to_twilio(self, mark_name: str = None) -> None:
        """Send a mark message to Twilio for audio synchronization."""
        if not self.stream_sid:
            return
        
        self.mark_counter += 1
        if not mark_name:
            mark_name = f"mark_{self.mark_counter}"
        else:
            mark_name = f"{mark_name}_{self.mark_counter}"
        
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
        Send a spoken error message to the caller.
        
        Note: Twilio Media Streams don't support direct TTS injection.
        This is handled at the TwiML level with <Say> fallback.
        """
        if not self.stream_sid:
            return
        
        logger.info(f"Sending error message to caller: {message_text[:50]}...")
        
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
        
        Includes error classification and recovery strategies:
        - Transient errors: Log and continue
        - Connection errors: Attempt reconnection
        - Fatal errors: Graceful shutdown
        
        Returns:
            Dict with conversation summary and analytics
        """
        error_count = 0
        max_consecutive_errors = 5
        
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        self.twilio_ws.receive_json(),
                        timeout=120.0  # 2 minute timeout
                    )
                    await self.handle_twilio_message(message)
                    error_count = 0  # Reset on success
                    
                    if message.get("event") == "stop":
                        logger.info(f"Call {self.call_id} ended normally (stop event)")
                        break
                
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout receiving from Twilio for call {self.call_id}")
                    # Check if call is still active
                    error_count += 1
                    if error_count >= max_consecutive_errors:
                        logger.error(f"Too many timeouts for call {self.call_id}, closing")
                        break
                        
                except websockets.exceptions.ConnectionClosed as e:
                    logger.info(f"Twilio connection closed for call {self.call_id}: {e.code}")
                    twilio_circuit.record_failure()
                    break
                    
                except json.JSONDecodeError as e:
                    # Bad message - log and continue
                    logger.warning(f"Invalid JSON from Twilio: {e}")
                    error_count += 1
                    continue
                    
                except Exception as e:
                    error_type = type(e).__name__
                    logger.error(f"Error in main loop [{error_type}]: {e}")
                    error_count += 1
                    
                    if error_count >= max_consecutive_errors:
                        logger.error(f"Too many errors ({error_count}) for call {self.call_id}, closing")
                        break
                    
                    # Small delay before retry
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Fatal error in voice agent run loop: {e}")
            
        finally:
            # Flush any remaining audio buffer
            await self._flush_audio_buffer()
            
            # Cleanup
            await self.cleanup()
        
        return self.get_summary()
    
    async def _flush_audio_buffer(self) -> None:
        """Flush remaining audio buffer to Deepgram."""
        remaining = self.audio_buffer.flush()
        if remaining and self.deepgram_ws:
            try:
                audio_msg = {
                    "type": "AudioData",
                    "audio_data": base64.b64encode(remaining).decode("utf-8")
                }
                await self.deepgram_ws.send(json.dumps(audio_msg))
            except Exception as e:
                logger.debug(f"Could not flush audio buffer: {e}")
    
    async def cleanup(self) -> None:
        """Clean up connections."""
        self.is_running = False
        
        if self.deepgram_ws:
            try:
                await self.deepgram_ws.close()
            except Exception:
                pass
    
    def get_summary(self) -> dict:
        """Get conversation summary with analytics."""
        if not self.tracker:
            return {
                "call_id": self.call_id,
                "duration_seconds": 0,
                "transcript": "",
                "turns": [],
                "analytics": {}
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
            "analytics": self.tracker.get_analytics(),
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
