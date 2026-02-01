"""
db.py - Database Layer using SQLModel

A database module with models for the AI Voice Agent system.
Uses SQLModel (Pydantic + SQLAlchemy) for ORM.
Supports SQLite (development) and PostgreSQL/Supabase (production).

Models: User, Client, UploadBatch, Lead, Call, CallResult, etc.
"""

import enum
import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Generator, Union

from sqlmodel import Field, SQLModel, Session, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String

# Password hashing with bcrypt
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
        
except ImportError:
    # Fallback if passlib not installed - but this should not happen in production
    import hashlib
    import secrets
    
    def hash_password(password: str) -> str:
        """Fallback: Hash password with PBKDF2."""
        salt = secrets.token_hex(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"pbkdf2_sha256${salt}${pwdhash.hex()}"
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Fallback: Verify password against PBKDF2 hash."""
        if not hashed_password.startswith("pbkdf2_sha256$"):
            # Legacy plain text comparison for migration
            return plain_password == hashed_password
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        pwdhash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
        return pwdhash.hex() == parts[2]


# -----------------------------------------------------------------------------
# Helper for UUID/String clinic IDs (Supabase compatibility)
# -----------------------------------------------------------------------------
def generate_uuid() -> str:
    """Generate a UUID string for Supabase compatibility."""
    return str(uuid.uuid4())


# Type alias for clinic ID (can be int for SQLite or str/UUID for Supabase)
ClinicIdType = Union[int, str]


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class CallStatus(str, enum.Enum):
    """Status of a call."""
    QUEUED = "queued"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CallResultType(str, enum.Enum):
    """Result type of a completed call."""
    BOOKED = "booked"
    NO_ANSWER = "no-answer"
    FAILED = "failed"
    RESCHEDULE = "reschedule"
    VOICEMAIL = "voicemail"


# -----------------------------------------------------------------------------
# Models (No relationships for simplicity - use queries instead)
# -----------------------------------------------------------------------------

class User(SQLModel, table=True):
    """User model for authentication with bcrypt password hashing."""
    __tablename__ = "backend_users"  # Use backend_users for Supabase compatibility
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str  # bcrypt hashed password
    is_admin: bool = Field(default=False)
    
    def set_password(self, password: str) -> None:
        """Hash and set the user password."""
        self.password_hash = hash_password(password)
    
    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return verify_password(password, self.password_hash)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} is_admin={self.is_admin}>"


class Client(SQLModel, table=True):
    """Client (dental clinic) model with voice agent configuration."""
    __tablename__ = "clients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # Clinic name, e.g. "Smile Dental Care"
    email: str  # Primary contact email
    timezone: str = Field(default="America/New_York")
    
    # Voice Agent Configuration
    agent_name: str = Field(default="Sarah")  # AI assistant's name
    agent_voice: str = Field(default="aura-asteria-en")  # Deepgram Aura-2 voice
    custom_instructions: Optional[str] = None  # Additional prompt instructions
    
    # Twilio Configuration
    twilio_number: Optional[str] = None  # Dedicated Twilio number for this clinic
    
    # Clinic Details (for AI context)
    address: Optional[str] = None  # Physical address
    phone_display: Optional[str] = None  # Human-readable phone for AI to mention
    hours: Optional[str] = None  # e.g. "Mon-Fri 9am-5pm, Sat 9am-1pm"
    services: Optional[str] = None  # Comma-separated: "cleanings, fillings, crowns"
    insurance_accepted: Optional[str] = None  # Comma-separated insurance providers
    
    # SMS Templates (JSON)
    # Structure: {"confirmation": "...", "reminder_24h": "...", "reminder_2h": "...", "recall": "...", "recall_followup": "..."}
    sms_templates: Optional[str] = None  # JSON string of custom templates
    sms_confirmation_enabled: bool = Field(default=True)
    sms_reminder_24h_enabled: bool = Field(default=True)
    sms_reminder_2h_enabled: bool = Field(default=True)
    sms_recall_enabled: bool = Field(default=True)
    
    # Billing & Status
    owner_email: Optional[str] = None  # Clinic owner for billing
    monthly_price: float = Field(default=0.0)  # Monthly subscription
    is_active: bool = Field(default=True)  # Active subscription
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name} agent={self.agent_name}>"


class UploadBatch(SQLModel, table=True):
    """Batch of uploaded leads."""
    __tablename__ = "upload_batches"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="csv")  # csv, json, api, n8n

    def __repr__(self) -> str:
        return f"<UploadBatch id={self.id} client_id={self.client_id} source={self.source}>"


class Lead(SQLModel, table=True):
    """Lead (potential patient) model."""
    __tablename__ = "leads"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    batch_id: int = Field(foreign_key="upload_batches.id", index=True)
    name: str
    phone: str = Field(index=True)
    email: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None
    consent: bool = Field(default=False)  # TCPA consent for PSTN calls
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Lead id={self.id} name={self.name} phone={self.phone}>"


class Call(SQLModel, table=True):
    """Call record linking lead to call attempt."""
    __tablename__ = "calls"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id", index=True)
    batch_id: int = Field(foreign_key="upload_batches.id", index=True)
    client_id: int = Field(foreign_key="clients.id", index=True)
    status: CallStatus = Field(default=CallStatus.QUEUED)
    attempt: int = Field(default=1)
    twilio_sid: Optional[str] = Field(default=None, index=True)  # Twilio Call SID
    recording_url: Optional[str] = None  # URL to call recording
    recording_sid: Optional[str] = None  # Twilio Recording SID
    duration: Optional[int] = None  # Call duration in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Call id={self.id} lead_id={self.lead_id} status={self.status}>"


class CallResult(SQLModel, table=True):
    """Result of a completed call."""
    __tablename__ = "call_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: int = Field(foreign_key="calls.id", unique=True, index=True)
    result: CallResultType
    transcript: Optional[str] = None  # Full conversation transcript
    booked_slot: Optional[datetime] = None  # If booked, the appointment time
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CallResult id={self.id} call_id={self.call_id} result={self.result}>"


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
    NO_RESOLUTION = "no_resolution"  # Stream failed, technical issue


class UsageType(str, enum.Enum):
    """Type of usage being tracked."""
    INBOUND_CALL = "inbound_call"
    OUTBOUND_CALL = "outbound_call"
    SMS_SENT = "sms_sent"
    SMS_RECEIVED = "sms_received"
    AI_TOKENS = "ai_tokens"
    TTS_CHARACTERS = "tts_characters"
    STT_SECONDS = "stt_seconds"


class UsageRecord(SQLModel, table=True):
    """
    Usage record for tracking billable usage per clinic.
    
    This tracks all billable events - calls, SMS, AI tokens, etc.
    Used for overage billing (>2000 min/mo = additional charges).
    """
    __tablename__ = "usage_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    usage_type: UsageType
    
    # Quantity (interpretation depends on usage_type)
    # - INBOUND_CALL/OUTBOUND_CALL: seconds
    # - SMS_*: count of messages
    # - AI_TOKENS: token count
    # - TTS_CHARACTERS: character count
    # - STT_SECONDS: seconds
    quantity: float = Field(default=0.0)
    
    # Optional reference (e.g., call_id, twilio_sid)
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None  # "inbound_call", "outbound_call", "sms"
    
    # Billing period (for aggregation)
    billing_month: str  # Format: "2024-12"
    
    # Cost tracking (calculated at time of recording)
    unit_cost: float = Field(default=0.0)  # Cost per unit
    total_cost: float = Field(default=0.0)  # quantity * unit_cost
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<UsageRecord clinic={self.clinic_id} type={self.usage_type} qty={self.quantity}>"


class MonthlyUsageSummary(SQLModel, table=True):
    """
    Monthly usage summary per clinic.
    
    This is a denormalized table for quick billing lookups.
    Updated incrementally as usage is recorded.
    """
    __tablename__ = "monthly_usage_summaries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    billing_month: str = Field(index=True)  # Format: "2024-12"
    
    # Voice minutes (inbound + outbound)
    total_voice_seconds: int = Field(default=0)
    inbound_seconds: int = Field(default=0)
    outbound_seconds: int = Field(default=0)
    
    # SMS counts
    sms_sent_count: int = Field(default=0)
    sms_received_count: int = Field(default=0)
    
    # AI usage
    ai_tokens_used: int = Field(default=0)
    tts_characters: int = Field(default=0)
    stt_seconds: int = Field(default=0)
    
    # Billing thresholds
    included_minutes: int = Field(default=2000)  # Minutes included in plan
    overage_minutes: int = Field(default=0)  # Minutes over limit
    overage_rate: float = Field(default=0.05)  # Per-minute overage rate
    
    # Costs
    base_cost: float = Field(default=0.0)  # Monthly subscription
    overage_cost: float = Field(default=0.0)  # Overage charges
    total_cost: float = Field(default=0.0)  # Total for month
    
    # Status
    is_finalized: bool = Field(default=False)  # Month closed for billing
    finalized_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        mins = self.total_voice_seconds // 60
        return f"<MonthlySummary clinic={self.clinic_id} month={self.billing_month} mins={mins}>"


class InboundCall(SQLModel, table=True):
    """
    Inbound call record for calls received via Twilio.
    
    This is different from Call (outbound) - these are calls
    initiated by patients calling the clinic's Twilio number.
    """
    __tablename__ = "inbound_calls"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    
    # Call identifiers
    from_number: str = Field(index=True)  # Caller's phone number
    to_number: str  # Twilio number that was called
    twilio_call_sid: str = Field(unique=True, index=True)
    stream_sid: Optional[str] = None  # Twilio Media Stream SID
    
    # Status tracking
    status: InboundCallStatus = Field(default=InboundCallStatus.RINGING)
    outcome: Optional[InboundCallOutcome] = None
    
    # Call details
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None  # Full conversation transcript
    summary: Optional[str] = None  # AI-generated summary
    
    # Extracted info from conversation
    caller_name: Optional[str] = None
    is_new_patient: Optional[bool] = None
    reason_for_call: Optional[str] = None
    booked_appointment: Optional[datetime] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # Extra data
    extra_data: Optional[str] = None  # JSON string for additional data

    def __repr__(self) -> str:
        return f"<InboundCall id={self.id} clinic_id={self.clinic_id} from={self.from_number} status={self.status}>"


# -----------------------------------------------------------------------------
# Appointment and Calendar Models
# -----------------------------------------------------------------------------

class AppointmentStatus(str, enum.Enum):
    """Status of an appointment."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, enum.Enum):
    """Types of dental appointments."""
    CLEANING = "cleaning"
    CHECKUP = "checkup"
    EMERGENCY = "emergency"
    CONSULTATION = "consultation"
    FILLING = "filling"
    CROWN = "crown"
    ROOT_CANAL = "root_canal"
    EXTRACTION = "extraction"
    WHITENING = "whitening"
    INVISALIGN = "invisalign"
    OTHER = "other"


class Patient(SQLModel, table=True):
    """Patient model for tracking patient information."""
    __tablename__ = "patients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    
    # Personal info
    first_name: str
    last_name: str
    phone: str = Field(index=True)
    email: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    
    # Dental info
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    is_new_patient: bool = Field(default=True)
    
    # History
    notes: Optional[str] = None
    no_show_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_visit: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.first_name} {self.last_name}>"


class Appointment(SQLModel, table=True):
    """Appointment model for scheduling."""
    __tablename__ = "appointments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    patient_id: Optional[int] = Field(default=None, foreign_key="patients.id", index=True)
    
    # Scheduling
    scheduled_time: datetime = Field(index=True)
    duration_minutes: int = Field(default=60)
    appointment_type: AppointmentType = Field(default=AppointmentType.CHECKUP)
    
    # Status
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    
    # Provider (dentist)
    provider_name: Optional[str] = None
    
    # Calendar integration
    calendar_provider: Optional[str] = None  # "google", "calendly", "manual"
    calendar_event_id: Optional[str] = None  # External calendar event ID
    
    # Source tracking
    source: str = Field(default="phone")  # "phone", "website", "walk-in", "ai"
    inbound_call_id: Optional[int] = Field(default=None, foreign_key="inbound_calls.id")
    
    # Patient info (for quick access without join)
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    is_new_patient: bool = Field(default=False)
    
    # Notes
    notes: Optional[str] = None
    reason: Optional[str] = None  # Reason for visit
    
    # Reminders
    reminder_24h_sent: bool = Field(default=False)
    reminder_2h_sent: bool = Field(default=False)
    confirmation_sent: bool = Field(default=False)
    
    # No-Show Reduction SMS Sequence (4-touch)
    confirmation_status: str = Field(default="pending")  # pending, confirmed, declined, no_response
    sms_sequence_step: int = Field(default=0)  # 0=none, 1=confirmation, 2=24h, 3=2h, 4=escalation
    last_sms_sent_at: Optional[datetime] = None
    patient_response: Optional[str] = None  # Raw response text from patient
    escalation_needed: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"<Appointment id={self.id} patient={self.patient_name} time={self.scheduled_time} status={self.status}>"


class NoShowRecord(SQLModel, table=True):
    """Record of no-show appointments for tracking and follow-up."""
    __tablename__ = "no_show_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    appointment_id: int = Field(foreign_key="appointments.id", index=True)
    patient_id: Optional[int] = Field(default=None, foreign_key="patients.id", index=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    
    # Original appointment info
    scheduled_time: datetime
    appointment_type: Optional[AppointmentType] = None
    
    # Follow-up tracking
    followed_up: bool = Field(default=False)
    followup_call_made: bool = Field(default=False)
    followup_sms_sent: bool = Field(default=False)
    followup_notes: Optional[str] = None
    rescheduled_appointment_id: Optional[int] = None  # If patient rescheduled
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    followed_up_at: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"<NoShowRecord id={self.id} appointment_id={self.appointment_id}>"


class CalendarIntegration(SQLModel, table=True):
    """Calendar integration settings per clinic."""
    __tablename__ = "calendar_integrations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", unique=True, index=True)
    
    # Provider
    provider: str = Field(default="manual")  # "google", "calendly", "manual"
    is_active: bool = Field(default=True)
    
    # Google Calendar settings
    google_calendar_id: Optional[str] = None
    google_credentials_json: Optional[str] = None  # Encrypted in production
    
    # Calendly settings
    calendly_api_key: Optional[str] = None
    calendly_user_uri: Optional[str] = None
    calendly_event_type_uri: Optional[str] = None
    
    # General settings
    slot_duration_minutes: int = Field(default=60)
    buffer_minutes: int = Field(default=15)
    business_hours_json: Optional[str] = None  # JSON string
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"<CalendarIntegration clinic_id={self.clinic_id} provider={self.provider}>"


# -----------------------------------------------------------------------------
# Proactive Recall System Models
# -----------------------------------------------------------------------------

class RecallStatus(str, enum.Enum):
    """Status of a recall outreach."""
    PENDING = "pending"           # Scheduled but not sent
    SMS_SENT = "sms_sent"         # First SMS sent
    CALL_SCHEDULED = "call_scheduled"  # AI call scheduled
    CALL_COMPLETED = "call_completed"  # AI call made
    BOOKED = "booked"             # Patient booked appointment
    DECLINED = "declined"         # Patient declined
    NO_RESPONSE = "no_response"   # No response after all attempts
    CANCELLED = "cancelled"       # Recall cancelled (e.g., patient already visited)


class RecallType(str, enum.Enum):
    """Types of recall reminders."""
    CLEANING = "cleaning"         # 6-month cleaning
    CHECKUP = "checkup"           # Annual checkup
    FOLLOWUP = "followup"         # Follow-up from previous treatment
    PERIODONTAL = "periodontal"   # Periodontal maintenance (3-4 month)
    CUSTOM = "custom"             # Custom recall set by clinic


class PatientRecall(SQLModel, table=True):
    """
    Patient recall tracking for proactive outbound campaigns.
    
    Tracks which patients are due for recalls (cleanings, checkups, etc.)
    and manages the outreach sequence: SMS → AI Call → Follow-up
    """
    __tablename__ = "patient_recalls"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    patient_id: Optional[int] = Field(default=None, foreign_key="patients.id", index=True)
    
    # Patient info (cached for quick access)
    patient_name: str
    patient_phone: str = Field(index=True)
    patient_email: Optional[str] = None
    
    # Recall details
    recall_type: RecallType = Field(default=RecallType.CLEANING)
    last_visit_date: Optional[datetime] = None
    due_date: datetime = Field(index=True)  # When patient is due for recall
    
    # Outreach status
    status: RecallStatus = Field(default=RecallStatus.PENDING)
    priority: int = Field(default=5)  # 1=highest, 10=lowest
    
    # Outreach sequence tracking
    sms_sent_at: Optional[datetime] = None
    sms_message_sid: Optional[str] = None  # Twilio message SID
    call_scheduled_at: Optional[datetime] = None
    call_completed_at: Optional[datetime] = None
    call_id: Optional[int] = Field(default=None, foreign_key="calls.id")
    outbound_call_sid: Optional[str] = None  # Twilio call SID
    
    # Response tracking
    patient_response: Optional[str] = None  # SMS response or call outcome
    booked_appointment_id: Optional[int] = Field(default=None, foreign_key="appointments.id")
    declined_reason: Optional[str] = None
    
    # Outreach attempts
    sms_attempts: int = Field(default=0)
    call_attempts: int = Field(default=0)
    max_sms_attempts: int = Field(default=2)
    max_call_attempts: int = Field(default=2)
    
    # Campaign tracking (for batch campaigns)
    campaign_id: Optional[str] = None  # For batch recall campaigns
    batch_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    next_outreach_at: Optional[datetime] = None  # When to attempt next contact
    completed_at: Optional[datetime] = None  # When recall was resolved
    
    # Notes
    notes: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"<PatientRecall id={self.id} patient={self.patient_name} type={self.recall_type} status={self.status}>"


class RecallCampaign(SQLModel, table=True):
    """
    Recall campaign for batch processing recalls.
    
    A clinic can create a campaign to reach all patients overdue
    for cleanings, for example.
    """
    __tablename__ = "recall_campaigns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clients.id", index=True)
    
    # Campaign details
    name: str
    recall_type: RecallType
    description: Optional[str] = None
    
    # Targeting
    target_overdue_days: int = Field(default=30)  # Patients overdue by X days
    target_count: int = Field(default=0)  # Number of patients targeted
    
    # Progress
    total_recalls: int = Field(default=0)
    sms_sent: int = Field(default=0)
    calls_made: int = Field(default=0)
    appointments_booked: int = Field(default=0)
    declined: int = Field(default=0)
    no_response: int = Field(default=0)
    
    # Revenue tracking
    estimated_revenue: float = Field(default=0.0)  # Projected if all book
    actual_revenue: float = Field(default=0.0)  # From booked appointments
    
    # Status
    is_active: bool = Field(default=True)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<RecallCampaign id={self.id} name={self.name} type={self.recall_type}>"


# -----------------------------------------------------------------------------
# Engine and Session Management
# -----------------------------------------------------------------------------

# Global engine reference (set by create_db)
_engine = None
_SessionLocal = None


def create_db(engine_url: str = None) -> None:
    """
    Create database engine and all tables.
    
    Args:
        engine_url: SQLAlchemy database URL. If None, reads from DATABASE_URL env var.
                   Supports SQLite (sqlite:///...) and PostgreSQL (postgresql://...)
    """
    import os
    global _engine, _SessionLocal
    
    # Default to env var or SQLite
    if engine_url is None:
        engine_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    
    # Handle Supabase connection pooler URL format
    # Supabase uses postgresql:// but SQLAlchemy needs postgresql+psycopg2://
    if engine_url.startswith("postgres://"):
        engine_url = engine_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif engine_url.startswith("postgresql://") and "+psycopg2" not in engine_url:
        engine_url = engine_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # Connection args differ by database type
    if "sqlite" in engine_url:
        connect_args = {"check_same_thread": False}
    else:
        # PostgreSQL - use connection pooling settings
        connect_args = {}
    
    # Create engine with appropriate settings
    if "sqlite" in engine_url:
        _engine = create_engine(engine_url, echo=False, connect_args=connect_args)
    else:
        # PostgreSQL with connection pool settings for Supabase
        _engine = create_engine(
            engine_url, 
            echo=False, 
            connect_args=connect_args,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=300,    # Recycle connections every 5 min
        )
    
    _SessionLocal = sessionmaker(bind=_engine, class_=Session, expire_on_commit=False)
    
    # Create all tables (only for SQLite - Supabase tables created via migrations)
    if "sqlite" in engine_url:
        SQLModel.metadata.create_all(_engine)


def get_engine():
    """Get the current database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call create_db() first.")
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_session() as session:
            user = session.get(User, 1)
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call create_db() first.")
    
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Database Type Detection & Supabase Compatibility
# -----------------------------------------------------------------------------

def is_using_postgres() -> bool:
    """Check if we're using PostgreSQL (Supabase) vs SQLite."""
    db_url = os.getenv("DATABASE_URL", "")
    return "postgresql" in db_url or "postgres" in db_url


def get_clinic_by_id(session: Session, clinic_id: ClinicIdType):
    """
    Get a clinic/client by ID. Works with both SQLite (int) and Supabase (UUID).
    
    For SQLite: Uses the local 'clients' table
    For Supabase: Uses 'dental_clinics' table (accessed via raw SQL if needed)
    """
    if is_using_postgres():
        # For Supabase, query dental_clinics table
        from sqlalchemy import text
        result = session.execute(
            text("SELECT * FROM dental_clinics WHERE id = :id"),
            {"id": str(clinic_id)}
        ).fetchone()
        if result:
            # Convert to dict-like object
            return result._mapping
        return None
    else:
        # SQLite - use local Client model
        return session.get(Client, int(clinic_id))


def get_clinic_by_twilio_number(session: Session, twilio_number: str):
    """
    Get clinic by Twilio number. Works with both databases.
    """
    if is_using_postgres():
        from sqlalchemy import text
        result = session.execute(
            text("SELECT * FROM dental_clinics WHERE twilio_number = :num"),
            {"num": twilio_number}
        ).fetchone()
        if result:
            return result._mapping
        return None
    else:
        from sqlmodel import select
        statement = select(Client).where(Client.twilio_number == twilio_number)
        return session.exec(statement).first()


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def enqueue_calls_for_batch(session: Session, batch_id: int, client_id: int) -> int:
    """
    Create Call rows for all leads in a batch with status 'queued'.
    
    Args:
        session: Database session
        batch_id: The batch ID to process
        client_id: The client ID for the calls
        
    Returns:
        Number of calls enqueued
    """
    from sqlmodel import select
    
    # Get all leads in this batch
    statement = select(Lead).where(Lead.batch_id == batch_id)
    leads = session.exec(statement).all()
    
    count = 0
    for lead in leads:
        call = Call(
            lead_id=lead.id,
            batch_id=batch_id,
            client_id=client_id,
            status=CallStatus.QUEUED,
            attempt=1,
        )
        session.add(call)
        count += 1
    
    session.commit()
    return count


def get_queued_calls(session: Session, limit: int = 10) -> list:
    """
    Get queued calls for processing.
    
    Args:
        session: Database session
        limit: Maximum number of calls to return
        
    Returns:
        List of Call objects with status 'queued'
    """
    from sqlmodel import select
    
    statement = (
        select(Call)
        .where(Call.status == CallStatus.QUEUED)
        .order_by(Call.created_at)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def create_demo_user(session: Session) -> User:
    """Create a demo admin user for testing with hashed password."""
    user = User(
        email="admin@dental.local",
        is_admin=True,
    )
    user.set_password("admin123")  # Hashed securely
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_demo_client(session: Session) -> Client:
    """Create a demo client for testing."""
    client = Client(
        name="Sunshine Dental",
        email="info@sunshine-dental.local",
        timezone="America/New_York",
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


# -----------------------------------------------------------------------------
# Usage Tracking Helpers
# -----------------------------------------------------------------------------

def get_current_billing_month() -> str:
    """Get current billing month in YYYY-MM format."""
    return datetime.utcnow().strftime("%Y-%m")


def record_usage(
    session: Session,
    clinic_id: int,
    usage_type: UsageType,
    quantity: float,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    unit_cost: float = 0.0,
) -> UsageRecord:
    """
    Record a usage event and update monthly summary.
    
    Args:
        session: Database session
        clinic_id: The clinic ID
        usage_type: Type of usage
        quantity: Amount (seconds for calls, count for SMS, etc.)
        reference_id: Optional reference (call ID, etc.)
        reference_type: Type of reference
        unit_cost: Cost per unit (for billing)
        
    Returns:
        The created UsageRecord
    """
    from sqlmodel import select
    
    billing_month = get_current_billing_month()
    
    # Create usage record
    record = UsageRecord(
        clinic_id=clinic_id,
        usage_type=usage_type,
        quantity=quantity,
        reference_id=reference_id,
        reference_type=reference_type,
        billing_month=billing_month,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
    )
    session.add(record)
    
    # Update or create monthly summary
    statement = select(MonthlyUsageSummary).where(
        MonthlyUsageSummary.clinic_id == clinic_id,
        MonthlyUsageSummary.billing_month == billing_month,
    )
    summary = session.exec(statement).first()
    
    if not summary:
        # Get client for base cost
        client = session.get(Client, clinic_id)
        base_cost = client.monthly_price if client else 0.0
        
        summary = MonthlyUsageSummary(
            clinic_id=clinic_id,
            billing_month=billing_month,
            base_cost=base_cost,
        )
        session.add(summary)
    
    # Update summary based on usage type
    if usage_type == UsageType.INBOUND_CALL:
        summary.inbound_seconds += int(quantity)
        summary.total_voice_seconds += int(quantity)
    elif usage_type == UsageType.OUTBOUND_CALL:
        summary.outbound_seconds += int(quantity)
        summary.total_voice_seconds += int(quantity)
    elif usage_type == UsageType.SMS_SENT:
        summary.sms_sent_count += int(quantity)
    elif usage_type == UsageType.SMS_RECEIVED:
        summary.sms_received_count += int(quantity)
    elif usage_type == UsageType.AI_TOKENS:
        summary.ai_tokens_used += int(quantity)
    elif usage_type == UsageType.TTS_CHARACTERS:
        summary.tts_characters += int(quantity)
    elif usage_type == UsageType.STT_SECONDS:
        summary.stt_seconds += int(quantity)
    
    # Calculate overage
    total_minutes = summary.total_voice_seconds // 60
    if total_minutes > summary.included_minutes:
        summary.overage_minutes = total_minutes - summary.included_minutes
        summary.overage_cost = summary.overage_minutes * summary.overage_rate
    else:
        summary.overage_minutes = 0
        summary.overage_cost = 0.0
    
    summary.total_cost = summary.base_cost + summary.overage_cost
    summary.updated_at = datetime.utcnow()
    
    session.commit()
    session.refresh(record)
    return record


def get_monthly_summary(
    session: Session,
    clinic_id: int,
    billing_month: Optional[str] = None,
) -> Optional[MonthlyUsageSummary]:
    """
    Get monthly usage summary for a clinic.
    
    Args:
        session: Database session
        clinic_id: The clinic ID
        billing_month: Month in YYYY-MM format (default: current month)
        
    Returns:
        MonthlyUsageSummary or None
    """
    from sqlmodel import select
    
    if billing_month is None:
        billing_month = get_current_billing_month()
    
    statement = select(MonthlyUsageSummary).where(
        MonthlyUsageSummary.clinic_id == clinic_id,
        MonthlyUsageSummary.billing_month == billing_month,
    )
    return session.exec(statement).first()


def get_usage_records(
    session: Session,
    clinic_id: int,
    billing_month: Optional[str] = None,
    usage_type: Optional[UsageType] = None,
    limit: int = 100,
) -> list:
    """
    Get usage records for a clinic.
    
    Args:
        session: Database session
        clinic_id: The clinic ID
        billing_month: Optional filter by month
        usage_type: Optional filter by type
        limit: Maximum records to return
        
    Returns:
        List of UsageRecord objects
    """
    from sqlmodel import select
    
    statement = select(UsageRecord).where(
        UsageRecord.clinic_id == clinic_id
    )
    
    if billing_month:
        statement = statement.where(UsageRecord.billing_month == billing_month)
    
    if usage_type:
        statement = statement.where(UsageRecord.usage_type == usage_type)
    
    statement = statement.order_by(UsageRecord.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())


def finalize_monthly_billing(
    session: Session,
    clinic_id: int,
    billing_month: str,
) -> Optional[MonthlyUsageSummary]:
    """
    Finalize monthly billing for a clinic.
    
    This marks the month as closed and prevents further updates.
    Should be called at the start of the next billing cycle.
    
    Args:
        session: Database session
        clinic_id: The clinic ID
        billing_month: Month to finalize in YYYY-MM format
        
    Returns:
        The finalized MonthlyUsageSummary or None
    """
    summary = get_monthly_summary(session, clinic_id, billing_month)
    
    if summary and not summary.is_finalized:
        summary.is_finalized = True
        summary.finalized_at = datetime.utcnow()
        session.commit()
        session.refresh(summary)
    
    return summary


# -----------------------------------------------------------------------------
# Main (Demo)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("Creating in-memory database...")
    create_db("sqlite:///:memory:")
    
    with get_session() as session:
        # Create demo data
        user = create_demo_user(session)
        print(f"Created user: {user}")
        
        client = create_demo_client(session)
        print(f"Created client: {client}")
        
        # Create a batch with some leads
        batch = UploadBatch(client_id=client.id, source="demo")
        session.add(batch)
        session.commit()
        session.refresh(batch)
        print(f"Created batch: {batch}")
        
        # Add leads
        leads_data = [
            {"name": "John Doe", "phone": "+15551234567", "email": "john@example.com"},
            {"name": "Jane Smith", "phone": "+15559876543", "email": "jane@example.com"},
            {"name": "Bob Wilson", "phone": "+15555555555", "notes": "Prefers afternoon"},
        ]
        
        for ld in leads_data:
            lead = Lead(batch_id=batch.id, **ld)
            session.add(lead)
        session.commit()
        print(f"Added {len(leads_data)} leads")
        
        # Enqueue calls
        queued = enqueue_calls_for_batch(session, batch.id, client.id)
        print(f"Enqueued {queued} calls")
        
        # Verify queued calls
        calls = get_queued_calls(session)
        print(f"Queued calls: {len(calls)}")
        for call in calls:
            print(f"  - {call}")
    
    print("\nDemo complete!")
