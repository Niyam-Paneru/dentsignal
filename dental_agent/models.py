"""
models.py - Pydantic Models for API Requests/Responses

Separate from SQLModel ORM models in db.py.
These are used for:
- API request/response validation
- WebSocket message schemas
- Deepgram Voice Agent integration
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class InboundCallStatus(str, enum.Enum):
    """Status of an inbound call."""
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no-answer"


class InboundCallOutcome(str, enum.Enum):
    """Outcome of a completed inbound call."""
    BOOKED = "booked"
    INQUIRY = "inquiry"
    CALLBACK_REQUESTED = "callback"
    TRANSFERRED = "transferred"
    HANGUP = "hangup"
    VOICEMAIL = "voicemail"


# -----------------------------------------------------------------------------
# Clinic/Client Models
# -----------------------------------------------------------------------------

class ClinicCreate(BaseModel):
    """Request model for creating a new clinic."""
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    timezone: str = "America/New_York"
    
    # Voice Agent Configuration
    agent_name: str = Field(default="Sarah", max_length=50)
    agent_voice: str = Field(default="aura-asteria-en")
    custom_instructions: Optional[str] = None
    
    # Clinic Details
    address: Optional[str] = None
    phone_display: Optional[str] = None
    hours: Optional[str] = Field(default="Mon-Fri 9am-5pm")
    services: Optional[str] = Field(default="cleanings, exams, fillings, crowns")
    insurance_accepted: Optional[str] = None
    
    # Billing
    owner_email: Optional[EmailStr] = None
    monthly_price: float = 99.0


class ClinicUpdate(BaseModel):
    """Request model for updating a clinic."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    agent_name: Optional[str] = None
    agent_voice: Optional[str] = None
    custom_instructions: Optional[str] = None
    address: Optional[str] = None
    phone_display: Optional[str] = None
    hours: Optional[str] = None
    services: Optional[str] = None
    insurance_accepted: Optional[str] = None
    is_active: Optional[bool] = None
    # SMS Templates
    sms_templates: Optional[str] = None  # JSON string of custom templates
    sms_confirmation_enabled: Optional[bool] = None
    sms_reminder_24h_enabled: Optional[bool] = None
    sms_reminder_2h_enabled: Optional[bool] = None
    sms_recall_enabled: Optional[bool] = None


class ClinicResponse(BaseModel):
    """Response model for clinic data."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    email: str
    timezone: str
    twilio_number: Optional[str]
    agent_name: str
    agent_voice: str
    address: Optional[str]
    hours: Optional[str]
    services: Optional[str]
    is_active: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# Inbound Call Models
# -----------------------------------------------------------------------------

class InboundCallCreate(BaseModel):
    """Created when Twilio receives an inbound call."""
    clinic_id: int
    from_number: str
    to_number: str
    twilio_call_sid: str
    stream_sid: Optional[str] = None


class InboundCallResponse(BaseModel):
    """Response model for inbound call data."""
    model_config = {"from_attributes": True}
    
    id: int
    clinic_id: int
    from_number: str
    to_number: str
    status: str
    outcome: Optional[str]
    duration_seconds: Optional[int]
    transcript: Optional[str]
    summary: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]


# -----------------------------------------------------------------------------
# WebSocket Message Models (Twilio Media Streams)
# -----------------------------------------------------------------------------

class TwilioMediaMessage(BaseModel):
    """Base model for Twilio Media Stream messages."""
    event: str
    streamSid: Optional[str] = None
    sequenceNumber: Optional[str] = None


class TwilioConnectedMessage(TwilioMediaMessage):
    """Sent when WebSocket connection is established."""
    protocol: Optional[str] = None
    version: Optional[str] = None


class TwilioStartMessage(TwilioMediaMessage):
    """Sent when media stream starts."""
    start: Optional[dict] = None
    # start contains: streamSid, accountSid, callSid, tracks, customParameters, mediaFormat


class TwilioMediaPayload(BaseModel):
    """Media payload from Twilio."""
    track: str = "inbound"  # inbound or outbound
    chunk: str  # sequence number
    timestamp: str
    payload: str  # base64-encoded audio


class TwilioMediaEventMessage(TwilioMediaMessage):
    """Media event with audio payload."""
    media: Optional[TwilioMediaPayload] = None


class TwilioStopMessage(TwilioMediaMessage):
    """Sent when media stream stops."""
    stop: Optional[dict] = None


class TwilioMarkMessage(TwilioMediaMessage):
    """Mark event for audio synchronization."""
    mark: Optional[dict] = None


# -----------------------------------------------------------------------------
# Deepgram Voice Agent Models
# -----------------------------------------------------------------------------

class DeepgramAgentConfig(BaseModel):
    """Configuration for Deepgram Voice Agent session."""
    # Audio settings
    input_sample_rate: int = 8000
    output_sample_rate: int = 8000
    input_encoding: str = "linear16"
    output_encoding: str = "linear16"
    
    # LLM settings
    llm_provider: str = "openai"  # or "anthropic", "deepgram"
    llm_model: str = "gpt-4o-mini"
    
    # Voice settings
    tts_model: str = "aura-asteria-en"
    
    # Agent settings
    system_prompt: str = ""
    greeting_message: Optional[str] = None
    
    # Features
    vad_enabled: bool = True
    interim_results: bool = True
    endpointing: int = 500  # ms of silence before turn end


class DeepgramAgentMessage(BaseModel):
    """Base model for Deepgram Voice Agent messages."""
    type: str
    

class DeepgramTranscriptMessage(BaseModel):
    """Transcript message from Deepgram."""
    type: str = "transcript"
    channel_index: list[int] = [0, 1]
    duration: float = 0.0
    start: float = 0.0
    is_final: bool = False
    speech_final: bool = False
    transcript: str = ""
    confidence: float = 0.0


class DeepgramAgentResponse(BaseModel):
    """Agent response message from Deepgram."""
    type: str = "agent_response"
    text: str = ""


class DeepgramAudioMessage(BaseModel):
    """TTS audio message from Deepgram."""
    type: str = "audio"
    data: str = ""  # base64-encoded audio


# -----------------------------------------------------------------------------
# Conversation State
# -----------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    role: str  # "user" or "agent"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """State tracking for an active conversation."""
    call_id: int
    clinic_id: int
    stream_sid: str
    twilio_call_sid: str
    
    # Conversation tracking
    turns: list[ConversationTurn] = []
    
    # Extracted info
    caller_name: Optional[str] = None
    is_new_patient: Optional[bool] = None
    reason_for_call: Optional[str] = None
    preferred_time: Optional[str] = None
    booked_appointment: Optional[datetime] = None
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# API Response Wrappers
# -----------------------------------------------------------------------------

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
