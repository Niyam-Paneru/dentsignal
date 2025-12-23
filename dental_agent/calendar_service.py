"""
calendar_service.py - Calendar Integration Service

Provides integration with Google Calendar and Calendly for:
- Real-time availability checking
- Appointment booking during calls
- No-show tracking and follow-up
- Calendar sync

Supports multiple calendar providers per clinic.
"""

import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass

# Google Calendar imports
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# HTTP client for Calendly
import httpx

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Enums and Data Classes
# -----------------------------------------------------------------------------

class CalendarProvider(str, Enum):
    """Supported calendar providers."""
    GOOGLE = "google"
    CALENDLY = "calendly"
    MANUAL = "manual"  # No integration, manual tracking


class AppointmentStatus(str, Enum):
    """Status of an appointment."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
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


@dataclass
class TimeSlot:
    """Represents an available time slot."""
    start: datetime
    end: datetime
    provider_name: Optional[str] = None  # Dentist name if assigned
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "provider_name": self.provider_name,
            "duration_minutes": int((self.end - self.start).total_seconds() / 60)
        }


@dataclass
class AppointmentDetails:
    """Details for creating an appointment."""
    patient_name: str
    patient_phone: str
    patient_email: Optional[str]
    appointment_type: AppointmentType
    start_time: datetime
    duration_minutes: int = 60
    notes: Optional[str] = None
    provider_name: Optional[str] = None  # Specific dentist
    is_new_patient: bool = False


@dataclass
class CalendarConfig:
    """Calendar configuration for a clinic."""
    provider: CalendarProvider
    # Google Calendar
    google_calendar_id: Optional[str] = None
    google_credentials_json: Optional[str] = None  # Service account JSON
    # Calendly
    calendly_api_key: Optional[str] = None
    calendly_user_uri: Optional[str] = None
    calendly_event_type_uri: Optional[str] = None
    # General settings
    slot_duration_minutes: int = 60
    buffer_minutes: int = 15  # Buffer between appointments
    business_hours: Optional[Dict[str, Dict[str, str]]] = None  # {"monday": {"start": "09:00", "end": "17:00"}}


# -----------------------------------------------------------------------------
# Appointment Duration Mapping
# -----------------------------------------------------------------------------

APPOINTMENT_DURATIONS = {
    AppointmentType.CLEANING: 60,
    AppointmentType.CHECKUP: 30,
    AppointmentType.EMERGENCY: 45,
    AppointmentType.CONSULTATION: 30,
    AppointmentType.FILLING: 60,
    AppointmentType.CROWN: 90,
    AppointmentType.ROOT_CANAL: 120,
    AppointmentType.EXTRACTION: 60,
    AppointmentType.WHITENING: 90,
    AppointmentType.INVISALIGN: 60,
    AppointmentType.OTHER: 60,
}


# -----------------------------------------------------------------------------
# Google Calendar Integration
# -----------------------------------------------------------------------------

class GoogleCalendarService:
    """Google Calendar integration using service account."""
    
    def __init__(self, credentials_json: str, calendar_id: str):
        """
        Initialize Google Calendar service.
        
        Args:
            credentials_json: Service account credentials JSON string
            calendar_id: Google Calendar ID to use
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError("google-api-python-client not installed. Run: pip install google-api-python-client google-auth")
        
        self.calendar_id = calendar_id
        self.service = self._build_service(credentials_json)
    
    def _build_service(self, credentials_json: str):
        """Build the Google Calendar service client."""
        creds_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        return build('calendar', 'v3', credentials=credentials)
    
    def get_busy_times(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get busy time periods from calendar.
        
        Returns list of (start, end) tuples for busy periods.
        """
        try:
            body = {
                "timeMin": datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z',
                "timeMax": datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z',
                "items": [{"id": self.calendar_id}]
            }
            
            result = self.service.freebusy().query(body=body).execute()
            busy_times = []
            
            for busy in result.get('calendars', {}).get(self.calendar_id, {}).get('busy', []):
                start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                busy_times.append((start, end))
            
            return busy_times
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return []
    
    def get_available_slots(
        self,
        target_date: date,
        duration_minutes: int = 60,
        business_hours: Dict[str, Dict[str, str]] = None
    ) -> List[TimeSlot]:
        """
        Get available time slots for a specific date.
        
        Args:
            target_date: Date to check availability
            duration_minutes: Required slot duration
            business_hours: Dict mapping day names to {start, end} times
        """
        if business_hours is None:
            business_hours = {
                "monday": {"start": "09:00", "end": "17:00"},
                "tuesday": {"start": "09:00", "end": "17:00"},
                "wednesday": {"start": "09:00", "end": "17:00"},
                "thursday": {"start": "09:00", "end": "17:00"},
                "friday": {"start": "09:00", "end": "17:00"},
            }
        
        day_name = target_date.strftime("%A").lower()
        if day_name not in business_hours:
            return []  # Closed on this day
        
        hours = business_hours[day_name]
        start_time = datetime.strptime(hours["start"], "%H:%M").time()
        end_time = datetime.strptime(hours["end"], "%H:%M").time()
        
        day_start = datetime.combine(target_date, start_time)
        day_end = datetime.combine(target_date, end_time)
        
        # Get busy times
        busy_times = self.get_busy_times(target_date, target_date)
        
        # Generate available slots
        available_slots = []
        current = day_start
        
        while current + timedelta(minutes=duration_minutes) <= day_end:
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any busy time
            is_available = True
            for busy_start, busy_end in busy_times:
                # Normalize to naive datetime for comparison
                busy_start_naive = busy_start.replace(tzinfo=None)
                busy_end_naive = busy_end.replace(tzinfo=None)
                
                if not (slot_end <= busy_start_naive or current >= busy_end_naive):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(TimeSlot(start=current, end=slot_end))
            
            current += timedelta(minutes=30)  # 30-minute slot intervals
        
        return available_slots
    
    def create_appointment(
        self,
        details: AppointmentDetails
    ) -> Optional[str]:
        """
        Create appointment in Google Calendar.
        
        Returns: Google Calendar event ID if successful, None otherwise
        """
        try:
            end_time = details.start_time + timedelta(minutes=details.duration_minutes)
            
            event = {
                'summary': f"{details.appointment_type.value.title()} - {details.patient_name}",
                'description': self._build_description(details),
                'start': {
                    'dateTime': details.start_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
            }
            
            result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Created Google Calendar event: {result.get('id')}")
            return result.get('id')
            
        except HttpError as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return None
    
    def cancel_appointment(self, event_id: str) -> bool:
        """Cancel/delete an appointment by event ID."""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Cancelled Google Calendar event: {event_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to cancel event {event_id}: {e}")
            return False
    
    def update_appointment(
        self,
        event_id: str,
        new_time: Optional[datetime] = None,
        new_status: Optional[AppointmentStatus] = None
    ) -> bool:
        """Update an existing appointment."""
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            if new_time:
                duration = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')) - \
                           datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                
                event['start']['dateTime'] = new_time.isoformat()
                event['end']['dateTime'] = (new_time + duration).isoformat()
            
            if new_status:
                # Add status to description
                desc = event.get('description', '')
                event['description'] = f"Status: {new_status.value}\n\n{desc}"
            
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return True
            
        except HttpError as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            return False
    
    def _build_description(self, details: AppointmentDetails) -> str:
        """Build event description from appointment details."""
        lines = [
            f"Patient: {details.patient_name}",
            f"Phone: {details.patient_phone}",
        ]
        if details.patient_email:
            lines.append(f"Email: {details.patient_email}")
        if details.is_new_patient:
            lines.append("⭐ NEW PATIENT")
        if details.provider_name:
            lines.append(f"Provider: {details.provider_name}")
        if details.notes:
            lines.append(f"\nNotes: {details.notes}")
        
        return "\n".join(lines)


# -----------------------------------------------------------------------------
# Calendly Integration
# -----------------------------------------------------------------------------

class CalendlyService:
    """Calendly integration for scheduling."""
    
    BASE_URL = "https://api.calendly.com"
    
    def __init__(self, api_key: str, user_uri: str, event_type_uri: str):
        """
        Initialize Calendly service.
        
        Args:
            api_key: Calendly API key (Personal Access Token)
            user_uri: User URI from Calendly
            event_type_uri: Default event type URI
        """
        self.api_key = api_key
        self.user_uri = user_uri
        self.event_type_uri = event_type_uri
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_available_times(
        self,
        start_date: date,
        end_date: date
    ) -> List[TimeSlot]:
        """Get available time slots from Calendly."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/event_type_available_times",
                    headers=self.headers,
                    params={
                        "event_type": self.event_type_uri,
                        "start_time": datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z',
                        "end_time": datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z',
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                slots = []
                for slot in data.get("collection", []):
                    start = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                    # Calendly returns end time based on event type duration
                    slots.append(TimeSlot(
                        start=start.replace(tzinfo=None),
                        end=start.replace(tzinfo=None) + timedelta(hours=1)  # Default 1hr
                    ))
                
                return slots
                
            except httpx.HTTPError as e:
                logger.error(f"Calendly API error: {e}")
                return []
    
    async def create_booking(
        self,
        details: AppointmentDetails
    ) -> Optional[str]:
        """
        Create a booking via Calendly.
        
        Note: Calendly doesn't allow direct booking via API for new contacts.
        Instead, returns a scheduling link.
        """
        # Calendly requires users to book through their UI
        # This returns a scheduling link instead
        async with httpx.AsyncClient() as client:
            try:
                # Get the event type to get the scheduling URL
                response = await client.get(
                    self.event_type_uri,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                scheduling_url = data.get("resource", {}).get("scheduling_url")
                logger.info(f"Calendly scheduling URL: {scheduling_url}")
                
                # In practice, you'd redirect the patient to this URL
                # or use Calendly's embed
                return scheduling_url
                
            except httpx.HTTPError as e:
                logger.error(f"Calendly API error: {e}")
                return None
    
    async def get_scheduled_events(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get scheduled events from Calendly."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/scheduled_events",
                    headers=self.headers,
                    params={
                        "user": self.user_uri,
                        "min_start_time": datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z',
                        "max_start_time": datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z',
                        "status": "active"
                    }
                )
                response.raise_for_status()
                return response.json().get("collection", [])
                
            except httpx.HTTPError as e:
                logger.error(f"Calendly API error: {e}")
                return []


# -----------------------------------------------------------------------------
# Unified Calendar Service
# -----------------------------------------------------------------------------

class CalendarService:
    """
    Unified calendar service that works with multiple providers.
    
    Usage:
        config = CalendarConfig(
            provider=CalendarProvider.GOOGLE,
            google_calendar_id="your-calendar-id@group.calendar.google.com",
            google_credentials_json='{"type": "service_account", ...}'
        )
        service = CalendarService(config)
        
        # Get available slots
        slots = await service.get_available_slots(date.today(), duration_minutes=60)
        
        # Book an appointment
        event_id = await service.book_appointment(AppointmentDetails(...))
    """
    
    def __init__(self, config: CalendarConfig):
        self.config = config
        self.google_service: Optional[GoogleCalendarService] = None
        self.calendly_service: Optional[CalendlyService] = None
        
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the appropriate calendar provider."""
        if self.config.provider == CalendarProvider.GOOGLE:
            if not self.config.google_calendar_id or not self.config.google_credentials_json:
                raise ValueError("Google Calendar requires calendar_id and credentials_json")
            self.google_service = GoogleCalendarService(
                self.config.google_credentials_json,
                self.config.google_calendar_id
            )
        
        elif self.config.provider == CalendarProvider.CALENDLY:
            if not self.config.calendly_api_key or not self.config.calendly_user_uri:
                raise ValueError("Calendly requires api_key and user_uri")
            self.calendly_service = CalendlyService(
                self.config.calendly_api_key,
                self.config.calendly_user_uri,
                self.config.calendly_event_type_uri or ""
            )
    
    async def get_available_slots(
        self,
        target_date: date,
        duration_minutes: int = 60,
        appointment_type: Optional[AppointmentType] = None
    ) -> List[TimeSlot]:
        """
        Get available time slots for a given date.
        
        Args:
            target_date: Date to check
            duration_minutes: Minimum slot duration needed
            appointment_type: Type of appointment (affects duration)
        
        Returns:
            List of available TimeSlot objects
        """
        # Use appointment type to determine duration if not specified
        if appointment_type and duration_minutes == 60:
            duration_minutes = APPOINTMENT_DURATIONS.get(appointment_type, 60)
        
        if self.config.provider == CalendarProvider.GOOGLE and self.google_service:
            return self.google_service.get_available_slots(
                target_date,
                duration_minutes,
                self.config.business_hours
            )
        
        elif self.config.provider == CalendarProvider.CALENDLY and self.calendly_service:
            return await self.calendly_service.get_available_times(
                target_date,
                target_date
            )
        
        else:
            # Manual mode - return all business hours as available
            return self._get_manual_slots(target_date, duration_minutes)
    
    async def get_next_available(
        self,
        appointment_type: AppointmentType,
        max_days_ahead: int = 14
    ) -> Optional[TimeSlot]:
        """
        Get the next available slot for an appointment type.
        
        Searches up to max_days_ahead to find an opening.
        """
        duration = APPOINTMENT_DURATIONS.get(appointment_type, 60)
        
        for i in range(max_days_ahead):
            check_date = date.today() + timedelta(days=i)
            slots = await self.get_available_slots(check_date, duration)
            
            if slots:
                # Return first available slot
                # Skip slots that are too soon (within 2 hours)
                min_time = datetime.now() + timedelta(hours=2)
                for slot in slots:
                    if slot.start >= min_time:
                        return slot
        
        return None
    
    async def book_appointment(
        self,
        details: AppointmentDetails
    ) -> Optional[str]:
        """
        Book an appointment.
        
        Returns:
            Event/booking ID if successful, None otherwise
        """
        if self.config.provider == CalendarProvider.GOOGLE and self.google_service:
            return self.google_service.create_appointment(details)
        
        elif self.config.provider == CalendarProvider.CALENDLY and self.calendly_service:
            return await self.calendly_service.create_booking(details)
        
        else:
            # Manual mode - just return a generated ID
            return f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    async def cancel_appointment(self, event_id: str) -> bool:
        """Cancel an appointment by event ID."""
        if self.config.provider == CalendarProvider.GOOGLE and self.google_service:
            return self.google_service.cancel_appointment(event_id)
        
        # Calendly cancellation would require webhook handling
        # Manual mode - just return success
        return True
    
    async def mark_no_show(self, event_id: str) -> bool:
        """Mark an appointment as no-show."""
        if self.config.provider == CalendarProvider.GOOGLE and self.google_service:
            return self.google_service.update_appointment(
                event_id,
                new_status=AppointmentStatus.NO_SHOW
            )
        return True
    
    def _get_manual_slots(
        self,
        target_date: date,
        duration_minutes: int
    ) -> List[TimeSlot]:
        """Generate slots for manual mode (no calendar integration)."""
        business_hours = self.config.business_hours or {
            "monday": {"start": "09:00", "end": "17:00"},
            "tuesday": {"start": "09:00", "end": "17:00"},
            "wednesday": {"start": "09:00", "end": "17:00"},
            "thursday": {"start": "09:00", "end": "17:00"},
            "friday": {"start": "09:00", "end": "17:00"},
        }
        
        day_name = target_date.strftime("%A").lower()
        if day_name not in business_hours:
            return []
        
        hours = business_hours[day_name]
        start_time = datetime.strptime(hours["start"], "%H:%M").time()
        end_time = datetime.strptime(hours["end"], "%H:%M").time()
        
        day_start = datetime.combine(target_date, start_time)
        day_end = datetime.combine(target_date, end_time)
        
        slots = []
        current = day_start
        
        while current + timedelta(minutes=duration_minutes) <= day_end:
            slots.append(TimeSlot(
                start=current,
                end=current + timedelta(minutes=duration_minutes)
            ))
            current += timedelta(minutes=30)
        
        return slots


# -----------------------------------------------------------------------------
# Voice Agent Integration Helpers
# -----------------------------------------------------------------------------

def format_available_slots_for_voice(slots: List[TimeSlot], max_slots: int = 3) -> str:
    """
    Format available slots for voice agent to speak.
    
    Example output:
    "I have openings tomorrow at 10 AM, 2 PM, or 4 PM."
    """
    if not slots:
        return "I'm sorry, I don't see any available appointments for that day."
    
    slots = slots[:max_slots]
    
    if len(slots) == 1:
        return f"I have an opening at {_format_time_for_voice(slots[0].start)}."
    
    time_strings = [_format_time_for_voice(s.start) for s in slots]
    
    if len(time_strings) == 2:
        return f"I have openings at {time_strings[0]} or {time_strings[1]}."
    
    last = time_strings.pop()
    return f"I have openings at {', '.join(time_strings)}, or {last}."


def _format_time_for_voice(dt: datetime) -> str:
    """Format datetime for natural speech."""
    hour = dt.hour
    minute = dt.minute
    
    if hour < 12:
        period = "AM"
        if hour == 0:
            hour = 12
    else:
        period = "PM"
        if hour > 12:
            hour -= 12
    
    if minute == 0:
        return f"{hour} {period}"
    elif minute == 30:
        return f"{hour}:30 {period}"
    else:
        return f"{hour}:{minute:02d} {period}"


def format_date_for_voice(target_date: date) -> str:
    """Format date for natural speech."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    if target_date == today:
        return "today"
    elif target_date == tomorrow:
        return "tomorrow"
    else:
        return target_date.strftime("%A, %B %d")  # "Monday, January 15"


def parse_appointment_type_from_text(text: str) -> AppointmentType:
    """
    Parse appointment type from natural language.
    
    Examples:
        "I need a cleaning" -> CLEANING
        "My tooth hurts really bad" -> EMERGENCY
        "Just a checkup" -> CHECKUP
    """
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["clean", "cleaning", "hygiene"]):
        return AppointmentType.CLEANING
    
    if any(word in text_lower for word in ["emergency", "urgent", "hurts", "pain", "ache", "broken", "cracked"]):
        return AppointmentType.EMERGENCY
    
    if any(word in text_lower for word in ["check", "checkup", "exam", "examination"]):
        return AppointmentType.CHECKUP
    
    if any(word in text_lower for word in ["consult", "consultation", "new patient", "first visit"]):
        return AppointmentType.CONSULTATION
    
    if any(word in text_lower for word in ["filling", "cavity"]):
        return AppointmentType.FILLING
    
    if any(word in text_lower for word in ["crown", "cap"]):
        return AppointmentType.CROWN
    
    if any(word in text_lower for word in ["root canal"]):
        return AppointmentType.ROOT_CANAL
    
    if any(word in text_lower for word in ["extract", "pull", "remove"]):
        return AppointmentType.EXTRACTION
    
    if any(word in text_lower for word in ["whiten", "whitening", "bleach"]):
        return AppointmentType.WHITENING
    
    if any(word in text_lower for word in ["invisalign", "braces", "align"]):
        return AppointmentType.INVISALIGN
    
    return AppointmentType.OTHER


# -----------------------------------------------------------------------------
# No-Show Tracking
# -----------------------------------------------------------------------------

class NoShowTracker:
    """
    Tracks no-shows and manages follow-up.
    
    Works with the database to:
    - Mark appointments as no-show
    - Track patient no-show history
    - Trigger follow-up SMS/calls
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def mark_no_show(
        self,
        appointment_id: int,
        calendar_event_id: Optional[str] = None,
        calendar_service: Optional[CalendarService] = None
    ) -> bool:
        """
        Mark an appointment as no-show.
        
        Also updates the calendar if integrated.
        """
        from db import Appointment, NoShowRecord
        
        # Update appointment in database
        appointment = self.db.get(Appointment, appointment_id)
        if not appointment:
            return False
        
        appointment.status = AppointmentStatus.NO_SHOW.value
        appointment.updated_at = datetime.utcnow()
        
        # Create no-show record
        no_show = NoShowRecord(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            clinic_id=appointment.clinic_id,
            scheduled_time=appointment.scheduled_time,
            created_at=datetime.utcnow()
        )
        self.db.add(no_show)
        
        # Update calendar if available
        if calendar_event_id and calendar_service:
            await calendar_service.mark_no_show(calendar_event_id)
        
        self.db.commit()
        return True
    
    def get_patient_no_show_count(self, patient_id: int) -> int:
        """Get the number of no-shows for a patient."""
        from db import NoShowRecord
        from sqlmodel import select, func
        
        result = self.db.exec(
            select(func.count(NoShowRecord.id))
            .where(NoShowRecord.patient_id == patient_id)
        ).one()
        
        return result or 0
    
    def get_no_shows_for_followup(
        self,
        clinic_id: int,
        hours_since: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get no-shows that need follow-up.
        
        Returns no-shows from the last N hours that haven't been followed up.
        """
        from db import NoShowRecord, Appointment, Patient
        from sqlmodel import select
        
        cutoff = datetime.utcnow() - timedelta(hours=hours_since)
        
        results = self.db.exec(
            select(NoShowRecord, Appointment, Patient)
            .join(Appointment, NoShowRecord.appointment_id == Appointment.id)
            .join(Patient, NoShowRecord.patient_id == Patient.id)
            .where(NoShowRecord.clinic_id == clinic_id)
            .where(NoShowRecord.created_at >= cutoff)
            .where(NoShowRecord.followed_up == False)
        ).all()
        
        return [
            {
                "no_show_id": ns.id,
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "patient_phone": patient.phone,
                "scheduled_time": apt.scheduled_time,
                "appointment_type": apt.appointment_type,
            }
            for ns, apt, patient in results
        ]
