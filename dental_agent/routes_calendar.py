"""
routes_calendar.py - Calendar and Appointment Management API

Provides endpoints for:
- Calendar integration setup (Google Calendar, Calendly)
- Appointment booking and management
- Real-time availability checking
- No-show tracking and follow-up

These endpoints power both the dashboard and the voice agent's
ability to check availability and book appointments during calls.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from db import (
    get_session,
    Client,
    Appointment,
    Patient,
    NoShowRecord,
    CalendarIntegration,
    AppointmentStatus,
    AppointmentType,
)
from calendar_service import (
    CalendarService,
    CalendarConfig,
    CalendarProvider,
    AppointmentDetails,
    TimeSlot,
    format_available_slots_for_voice,
    parse_appointment_type_from_text,
    APPOINTMENT_DURATIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calendar", tags=["Calendar & Appointments"])


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class CalendarSetupRequest(BaseModel):
    """Request to set up calendar integration."""
    provider: str = Field(..., description="Calendar provider: 'google', 'calendly', or 'manual'")
    # Google Calendar
    google_calendar_id: Optional[str] = None
    google_credentials_json: Optional[str] = None
    # Calendly
    calendly_api_key: Optional[str] = None
    calendly_user_uri: Optional[str] = None
    calendly_event_type_uri: Optional[str] = None
    # Settings
    slot_duration_minutes: int = 60
    buffer_minutes: int = 15
    business_hours: Optional[dict] = None


class CalendarSetupResponse(BaseModel):
    """Response after setting up calendar."""
    success: bool
    message: str
    provider: str
    is_connected: bool


class AvailabilityRequest(BaseModel):
    """Request for availability check."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_type: Optional[str] = None
    duration_minutes: Optional[int] = None


class TimeSlotResponse(BaseModel):
    """Available time slot."""
    start: str
    end: str
    duration_minutes: int
    provider_name: Optional[str] = None


class AvailabilityResponse(BaseModel):
    """Response with available slots."""
    date: str
    slots: List[TimeSlotResponse]
    slots_count: int
    voice_description: str  # For AI to speak


class AppointmentCreateRequest(BaseModel):
    """Request to create an appointment."""
    # Patient info
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = None
    is_new_patient: bool = False
    
    # Appointment details
    scheduled_time: str = Field(..., description="ISO format datetime")
    appointment_type: str = "checkup"
    duration_minutes: Optional[int] = None
    provider_name: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    
    # Source
    source: str = "phone"  # phone, website, walk-in, ai
    inbound_call_id: Optional[int] = None


class AppointmentResponse(BaseModel):
    """Appointment details response."""
    id: int
    patient_name: str
    patient_phone: str
    scheduled_time: str
    appointment_type: str
    duration_minutes: int
    status: str
    provider_name: Optional[str]
    calendar_event_id: Optional[str]
    confirmation_sent: bool
    created_at: str


class AppointmentUpdateRequest(BaseModel):
    """Request to update an appointment."""
    scheduled_time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    provider_name: Optional[str] = None


class NoShowMarkRequest(BaseModel):
    """Request to mark appointment as no-show."""
    notes: Optional[str] = None
    send_followup_sms: bool = True


class NoShowResponse(BaseModel):
    """No-show record response."""
    id: int
    appointment_id: int
    patient_name: str
    patient_phone: str
    scheduled_time: str
    followed_up: bool
    rescheduled: bool


class NoShowStatsResponse(BaseModel):
    """No-show statistics."""
    total_no_shows: int
    this_month: int
    last_month: int
    follow_up_pending: int
    rescheduled_count: int
    no_show_rate: float  # Percentage


# -----------------------------------------------------------------------------
# Calendar Integration Endpoints
# -----------------------------------------------------------------------------

@router.post("/setup", response_model=CalendarSetupResponse)
async def setup_calendar_integration(
    clinic_id: int,
    request: CalendarSetupRequest,
    db: Session = Depends(get_session)
):
    """
    Set up or update calendar integration for a clinic.
    
    Supports:
    - Google Calendar (service account)
    - Calendly (API key)
    - Manual (no integration, just database tracking)
    """
    # Verify clinic exists
    clinic = db.get(Client, clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    # Check for existing integration
    existing = db.exec(
        select(CalendarIntegration).where(CalendarIntegration.clinic_id == clinic_id)
    ).first()
    
    if existing:
        # Update existing
        integration = existing
    else:
        # Create new
        integration = CalendarIntegration(clinic_id=clinic_id)
    
    # Update fields
    integration.provider = request.provider
    integration.slot_duration_minutes = request.slot_duration_minutes
    integration.buffer_minutes = request.buffer_minutes
    
    if request.business_hours:
        integration.business_hours_json = json.dumps(request.business_hours)
    
    if request.provider == "google":
        integration.google_calendar_id = request.google_calendar_id
        integration.google_credentials_json = request.google_credentials_json
    elif request.provider == "calendly":
        integration.calendly_api_key = request.calendly_api_key
        integration.calendly_user_uri = request.calendly_user_uri
        integration.calendly_event_type_uri = request.calendly_event_type_uri
    
    integration.updated_at = datetime.utcnow()
    
    # Test connection if not manual
    is_connected = True
    message = "Calendar integration saved successfully"
    
    if request.provider == "google" and request.google_credentials_json:
        try:
            config = CalendarConfig(
                provider=CalendarProvider.GOOGLE,
                google_calendar_id=request.google_calendar_id,
                google_credentials_json=request.google_credentials_json
            )
            service = CalendarService(config)
            # Test by getting today's slots
            slots = await service.get_available_slots(date.today())
            message = f"Connected! Found {len(slots)} available slots today."
        except Exception as e:
            is_connected = False
            message = f"Connection failed: {str(e)}"
            logger.error(f"Google Calendar connection failed: {e}")
    
    integration.is_active = is_connected
    
    if not existing:
        db.add(integration)
    db.commit()
    
    return CalendarSetupResponse(
        success=True,
        message=message,
        provider=request.provider,
        is_connected=is_connected
    )


@router.get("/integration/{clinic_id}")
async def get_calendar_integration(
    clinic_id: int,
    db: Session = Depends(get_session)
):
    """Get calendar integration settings for a clinic."""
    integration = db.exec(
        select(CalendarIntegration).where(CalendarIntegration.clinic_id == clinic_id)
    ).first()
    
    if not integration:
        return {
            "has_integration": False,
            "provider": "manual",
            "is_active": False
        }
    
    return {
        "has_integration": True,
        "provider": integration.provider,
        "is_active": integration.is_active,
        "slot_duration_minutes": integration.slot_duration_minutes,
        "buffer_minutes": integration.buffer_minutes,
        "business_hours": json.loads(integration.business_hours_json) if integration.business_hours_json else None,
        "last_sync": integration.last_sync.isoformat() if integration.last_sync else None
    }


# -----------------------------------------------------------------------------
# Availability Endpoints
# -----------------------------------------------------------------------------

@router.get("/availability/{clinic_id}", response_model=AvailabilityResponse)
async def get_availability(
    clinic_id: int,
    target_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    appointment_type: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    Get available time slots for a specific date.
    
    This is the primary endpoint used by the voice agent to check
    availability during calls.
    """
    # Parse date
    try:
        check_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get calendar integration
    integration = db.exec(
        select(CalendarIntegration).where(CalendarIntegration.clinic_id == clinic_id)
    ).first()
    
    # Parse appointment type
    apt_type = None
    if appointment_type:
        try:
            apt_type = AppointmentType(appointment_type.lower())
        except ValueError:
            apt_type = parse_appointment_type_from_text(appointment_type)
    
    # Determine duration
    if duration_minutes is None:
        duration_minutes = APPOINTMENT_DURATIONS.get(apt_type, 60) if apt_type else 60
    
    # Get slots
    if integration and integration.is_active and integration.provider != "manual":
        # Use calendar service
        business_hours = json.loads(integration.business_hours_json) if integration.business_hours_json else None
        
        config = CalendarConfig(
            provider=CalendarProvider(integration.provider),
            google_calendar_id=integration.google_calendar_id,
            google_credentials_json=integration.google_credentials_json,
            calendly_api_key=integration.calendly_api_key,
            calendly_user_uri=integration.calendly_user_uri,
            calendly_event_type_uri=integration.calendly_event_type_uri,
            slot_duration_minutes=integration.slot_duration_minutes,
            buffer_minutes=integration.buffer_minutes,
            business_hours=business_hours
        )
        
        service = CalendarService(config)
        slots = await service.get_available_slots(check_date, duration_minutes, apt_type)
    else:
        # Use database only - check existing appointments
        slots = await _get_database_availability(db, clinic_id, check_date, duration_minutes)
    
    # Format response
    slot_responses = [
        TimeSlotResponse(
            start=s.start.isoformat(),
            end=s.end.isoformat(),
            duration_minutes=int((s.end - s.start).total_seconds() / 60),
            provider_name=s.provider_name
        )
        for s in slots
    ]
    
    return AvailabilityResponse(
        date=target_date,
        slots=slot_responses,
        slots_count=len(slot_responses),
        voice_description=format_available_slots_for_voice(slots)
    )


@router.get("/next-available/{clinic_id}")
async def get_next_available(
    clinic_id: int,
    appointment_type: str = "checkup",
    max_days: int = Query(14, ge=1, le=60),
    db: Session = Depends(get_session)
):
    """
    Find the next available slot for an appointment type.
    
    Searches up to max_days ahead.
    """
    try:
        apt_type = AppointmentType(appointment_type.lower())
    except ValueError:
        apt_type = parse_appointment_type_from_text(appointment_type)
    
    duration = APPOINTMENT_DURATIONS.get(apt_type, 60)
    
    for i in range(max_days):
        check_date = date.today() + timedelta(days=i)
        
        # Skip past times for today
        min_time = datetime.now() + timedelta(hours=2)
        
        # Get availability (simplified - uses database only for speed)
        slots = await _get_database_availability(db, clinic_id, check_date, duration)
        
        for slot in slots:
            if slot.start >= min_time:
                return {
                    "found": True,
                    "date": check_date.isoformat(),
                    "start": slot.start.isoformat(),
                    "end": slot.end.isoformat(),
                    "voice_description": f"The next available appointment is on {check_date.strftime('%A, %B %d')} at {slot.start.strftime('%I:%M %p')}."
                }
    
    return {
        "found": False,
        "message": f"No availability found in the next {max_days} days",
        "voice_description": f"I'm sorry, I don't see any openings in the next {max_days} days. Would you like me to add you to our waitlist?"
    }


async def _get_database_availability(
    db: Session,
    clinic_id: int,
    check_date: date,
    duration_minutes: int
) -> List[TimeSlot]:
    """
    Get available slots based on database appointments only.
    
    Used when no external calendar is integrated.
    """
    # Default business hours
    business_hours = {
        "monday": {"start": "09:00", "end": "17:00"},
        "tuesday": {"start": "09:00", "end": "17:00"},
        "wednesday": {"start": "09:00", "end": "17:00"},
        "thursday": {"start": "09:00", "end": "17:00"},
        "friday": {"start": "09:00", "end": "17:00"},
    }
    
    day_name = check_date.strftime("%A").lower()
    if day_name not in business_hours:
        return []
    
    hours = business_hours[day_name]
    day_start = datetime.combine(check_date, datetime.strptime(hours["start"], "%H:%M").time())
    day_end = datetime.combine(check_date, datetime.strptime(hours["end"], "%H:%M").time())
    
    # Get existing appointments for this date
    existing = db.exec(
        select(Appointment)
        .where(Appointment.clinic_id == clinic_id)
        .where(Appointment.scheduled_time >= day_start)
        .where(Appointment.scheduled_time < day_end)
        .where(Appointment.status.in_([
            AppointmentStatus.SCHEDULED.value,
            AppointmentStatus.CONFIRMED.value
        ]))
    ).all()
    
    # Build list of busy times
    busy_times = []
    for apt in existing:
        apt_end = apt.scheduled_time + timedelta(minutes=apt.duration_minutes)
        busy_times.append((apt.scheduled_time, apt_end))
    
    # Generate available slots
    slots = []
    current = day_start
    
    while current + timedelta(minutes=duration_minutes) <= day_end:
        slot_end = current + timedelta(minutes=duration_minutes)
        
        # Check if slot is available
        is_available = True
        for busy_start, busy_end in busy_times:
            if not (slot_end <= busy_start or current >= busy_end):
                is_available = False
                break
        
        if is_available:
            slots.append(TimeSlot(start=current, end=slot_end))
        
        current += timedelta(minutes=30)  # 30-minute intervals
    
    return slots


# -----------------------------------------------------------------------------
# Appointment Management Endpoints
# -----------------------------------------------------------------------------

@router.post("/appointments/{clinic_id}", response_model=AppointmentResponse)
async def create_appointment(
    clinic_id: int,
    request: AppointmentCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """
    Create a new appointment.
    
    This endpoint:
    1. Creates the appointment in the database
    2. Syncs to external calendar if integrated
    3. Sends confirmation SMS (async)
    """
    # Parse scheduled time
    try:
        scheduled_time = datetime.fromisoformat(request.scheduled_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    
    # Parse appointment type
    try:
        apt_type = AppointmentType(request.appointment_type.lower())
    except ValueError:
        apt_type = AppointmentType.OTHER
    
    # Determine duration
    duration = request.duration_minutes or APPOINTMENT_DURATIONS.get(apt_type, 60)
    
    # Check for conflicts
    conflict = db.exec(
        select(Appointment)
        .where(Appointment.clinic_id == clinic_id)
        .where(Appointment.scheduled_time == scheduled_time)
        .where(Appointment.status.in_([
            AppointmentStatus.SCHEDULED.value,
            AppointmentStatus.CONFIRMED.value
        ]))
    ).first()
    
    if conflict:
        raise HTTPException(
            status_code=409,
            detail="This time slot is already booked"
        )
    
    # Find or create patient
    patient = db.exec(
        select(Patient)
        .where(Patient.clinic_id == clinic_id)
        .where(Patient.phone == request.patient_phone)
    ).first()
    
    if not patient:
        # Parse name
        name_parts = request.patient_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        patient = Patient(
            clinic_id=clinic_id,
            first_name=first_name,
            last_name=last_name,
            phone=request.patient_phone,
            email=request.patient_email,
            is_new_patient=request.is_new_patient
        )
        db.add(patient)
        db.flush()
    
    # Create appointment
    appointment = Appointment(
        clinic_id=clinic_id,
        patient_id=patient.id,
        scheduled_time=scheduled_time,
        duration_minutes=duration,
        appointment_type=apt_type,
        status=AppointmentStatus.SCHEDULED,
        provider_name=request.provider_name,
        source=request.source,
        inbound_call_id=request.inbound_call_id,
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        patient_email=request.patient_email,
        is_new_patient=request.is_new_patient,
        reason=request.reason,
        notes=request.notes
    )
    
    # Sync to external calendar
    integration = db.exec(
        select(CalendarIntegration).where(CalendarIntegration.clinic_id == clinic_id)
    ).first()
    
    if integration and integration.is_active and integration.provider != "manual":
        try:
            config = CalendarConfig(
                provider=CalendarProvider(integration.provider),
                google_calendar_id=integration.google_calendar_id,
                google_credentials_json=integration.google_credentials_json,
                calendly_api_key=integration.calendly_api_key,
                calendly_user_uri=integration.calendly_user_uri,
                calendly_event_type_uri=integration.calendly_event_type_uri
            )
            
            service = CalendarService(config)
            
            details = AppointmentDetails(
                patient_name=request.patient_name,
                patient_phone=request.patient_phone,
                patient_email=request.patient_email,
                appointment_type=apt_type,
                start_time=scheduled_time,
                duration_minutes=duration,
                notes=request.notes,
                provider_name=request.provider_name,
                is_new_patient=request.is_new_patient
            )
            
            event_id = await service.book_appointment(details)
            appointment.calendar_event_id = event_id
            appointment.calendar_provider = integration.provider
            
        except Exception as e:
            logger.error(f"Failed to sync to calendar: {e}")
            # Continue without calendar sync
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    # Send confirmation SMS in background
    background_tasks.add_task(_send_appointment_confirmation, appointment, db)
    
    return AppointmentResponse(
        id=appointment.id,
        patient_name=appointment.patient_name,
        patient_phone=appointment.patient_phone,
        scheduled_time=appointment.scheduled_time.isoformat(),
        appointment_type=appointment.appointment_type.value,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status.value,
        provider_name=appointment.provider_name,
        calendar_event_id=appointment.calendar_event_id,
        confirmation_sent=False,  # Will be sent in background
        created_at=appointment.created_at.isoformat()
    )


@router.get("/appointments/{clinic_id}")
async def list_appointments(
    clinic_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_session)
):
    """List appointments for a clinic with optional filters."""
    query = select(Appointment).where(Appointment.clinic_id == clinic_id)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.where(Appointment.scheduled_time >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.where(Appointment.scheduled_time < end)
    
    if status:
        query = query.where(Appointment.status == status)
    
    query = query.order_by(Appointment.scheduled_time.desc()).limit(limit)
    
    appointments = db.exec(query).all()
    
    return {
        "appointments": [
            {
                "id": apt.id,
                "patient_name": apt.patient_name,
                "patient_phone": apt.patient_phone,
                "scheduled_time": apt.scheduled_time.isoformat(),
                "appointment_type": apt.appointment_type.value,
                "duration_minutes": apt.duration_minutes,
                "status": apt.status.value,
                "provider_name": apt.provider_name,
                "is_new_patient": apt.is_new_patient,
                "source": apt.source
            }
            for apt in appointments
        ],
        "count": len(appointments)
    }


@router.get("/appointments/{clinic_id}/{appointment_id}")
async def get_appointment(
    clinic_id: int,
    appointment_id: int,
    db: Session = Depends(get_session)
):
    """Get appointment details."""
    appointment = db.exec(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.clinic_id == clinic_id)
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient_name,
        "patient_phone": appointment.patient_phone,
        "patient_email": appointment.patient_email,
        "scheduled_time": appointment.scheduled_time.isoformat(),
        "appointment_type": appointment.appointment_type.value,
        "duration_minutes": appointment.duration_minutes,
        "status": appointment.status.value,
        "provider_name": appointment.provider_name,
        "calendar_event_id": appointment.calendar_event_id,
        "is_new_patient": appointment.is_new_patient,
        "source": appointment.source,
        "reason": appointment.reason,
        "notes": appointment.notes,
        "reminder_24h_sent": appointment.reminder_24h_sent,
        "reminder_2h_sent": appointment.reminder_2h_sent,
        "confirmation_sent": appointment.confirmation_sent,
        "created_at": appointment.created_at.isoformat(),
        "confirmed_at": appointment.confirmed_at.isoformat() if appointment.confirmed_at else None
    }


@router.patch("/appointments/{clinic_id}/{appointment_id}")
async def update_appointment(
    clinic_id: int,
    appointment_id: int,
    request: AppointmentUpdateRequest,
    db: Session = Depends(get_session)
):
    """Update an appointment."""
    appointment = db.exec(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.clinic_id == clinic_id)
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if request.scheduled_time:
        new_time = datetime.fromisoformat(request.scheduled_time)
        
        # Check for conflicts
        conflict = db.exec(
            select(Appointment)
            .where(Appointment.clinic_id == clinic_id)
            .where(Appointment.scheduled_time == new_time)
            .where(Appointment.id != appointment_id)
            .where(Appointment.status.in_([
                AppointmentStatus.SCHEDULED.value,
                AppointmentStatus.CONFIRMED.value
            ]))
        ).first()
        
        if conflict:
            raise HTTPException(status_code=409, detail="Time slot conflict")
        
        appointment.scheduled_time = new_time
    
    if request.status:
        try:
            appointment.status = AppointmentStatus(request.status)
            if request.status == "confirmed":
                appointment.confirmed_at = datetime.utcnow()
            elif request.status == "completed":
                appointment.completed_at = datetime.utcnow()
            elif request.status == "cancelled":
                appointment.cancelled_at = datetime.utcnow()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if request.notes is not None:
        appointment.notes = request.notes
    
    if request.provider_name is not None:
        appointment.provider_name = request.provider_name
    
    appointment.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Appointment updated"}


@router.delete("/appointments/{clinic_id}/{appointment_id}")
async def cancel_appointment(
    clinic_id: int,
    appointment_id: int,
    db: Session = Depends(get_session)
):
    """Cancel an appointment."""
    appointment = db.exec(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.clinic_id == clinic_id)
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = datetime.utcnow()
    appointment.updated_at = datetime.utcnow()
    
    # Cancel in external calendar if integrated
    if appointment.calendar_event_id:
        integration = db.exec(
            select(CalendarIntegration).where(CalendarIntegration.clinic_id == clinic_id)
        ).first()
        
        if integration and integration.is_active:
            try:
                config = CalendarConfig(
                    provider=CalendarProvider(integration.provider),
                    google_calendar_id=integration.google_calendar_id,
                    google_credentials_json=integration.google_credentials_json
                )
                service = CalendarService(config)
                await service.cancel_appointment(appointment.calendar_event_id)
            except Exception as e:
                logger.error(f"Failed to cancel calendar event: {e}")
    
    db.commit()
    
    return {"success": True, "message": "Appointment cancelled"}


# -----------------------------------------------------------------------------
# No-Show Tracking Endpoints
# -----------------------------------------------------------------------------

@router.post("/appointments/{clinic_id}/{appointment_id}/no-show")
async def mark_no_show(
    clinic_id: int,
    appointment_id: int,
    request: NoShowMarkRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Mark an appointment as no-show and create follow-up record."""
    appointment = db.exec(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .where(Appointment.clinic_id == clinic_id)
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update appointment status
    appointment.status = AppointmentStatus.NO_SHOW
    appointment.updated_at = datetime.utcnow()
    
    # Create no-show record
    no_show = NoShowRecord(
        appointment_id=appointment_id,
        patient_id=appointment.patient_id,
        clinic_id=clinic_id,
        scheduled_time=appointment.scheduled_time,
        appointment_type=appointment.appointment_type,
        followup_notes=request.notes
    )
    db.add(no_show)
    
    # Update patient no-show count
    if appointment.patient_id:
        patient = db.get(Patient, appointment.patient_id)
        if patient:
            patient.no_show_count += 1
    
    # Update calendar if integrated
    if appointment.calendar_event_id:
        integration = db.exec(
            select(CalendarIntegration).where(CalendarIntegration.clinic_id == clinic_id)
        ).first()
        
        if integration and integration.is_active:
            try:
                config = CalendarConfig(
                    provider=CalendarProvider(integration.provider),
                    google_calendar_id=integration.google_calendar_id,
                    google_credentials_json=integration.google_credentials_json
                )
                service = CalendarService(config)
                await service.mark_no_show(appointment.calendar_event_id)
            except Exception as e:
                logger.error(f"Failed to update calendar: {e}")
    
    db.commit()
    
    # Send follow-up SMS in background
    if request.send_followup_sms and appointment.patient_phone:
        background_tasks.add_task(_send_no_show_followup, appointment, db)
    
    return {"success": True, "message": "Marked as no-show", "no_show_id": no_show.id}


@router.get("/no-shows/{clinic_id}", response_model=List[NoShowResponse])
async def list_no_shows(
    clinic_id: int,
    pending_only: bool = Query(False, description="Only show pending follow-ups"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_session)
):
    """List no-show records for a clinic."""
    query = (
        select(NoShowRecord, Appointment)
        .join(Appointment, NoShowRecord.appointment_id == Appointment.id)
        .where(NoShowRecord.clinic_id == clinic_id)
    )
    
    if pending_only:
        query = query.where(NoShowRecord.followed_up == False)
    
    query = query.order_by(NoShowRecord.created_at.desc()).limit(limit)
    
    results = db.exec(query).all()
    
    return [
        NoShowResponse(
            id=ns.id,
            appointment_id=ns.appointment_id,
            patient_name=apt.patient_name or "Unknown",
            patient_phone=apt.patient_phone or "",
            scheduled_time=ns.scheduled_time.isoformat(),
            followed_up=ns.followed_up,
            rescheduled=ns.rescheduled_appointment_id is not None
        )
        for ns, apt in results
    ]


@router.get("/no-shows/{clinic_id}/stats", response_model=NoShowStatsResponse)
async def get_no_show_stats(
    clinic_id: int,
    db: Session = Depends(get_session)
):
    """Get no-show statistics for a clinic."""
    from sqlmodel import func
    
    # Total no-shows
    total = db.exec(
        select(func.count(NoShowRecord.id))
        .where(NoShowRecord.clinic_id == clinic_id)
    ).one() or 0
    
    # This month
    this_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = db.exec(
        select(func.count(NoShowRecord.id))
        .where(NoShowRecord.clinic_id == clinic_id)
        .where(NoShowRecord.created_at >= this_month_start)
    ).one() or 0
    
    # Last month
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_month = db.exec(
        select(func.count(NoShowRecord.id))
        .where(NoShowRecord.clinic_id == clinic_id)
        .where(NoShowRecord.created_at >= last_month_start)
        .where(NoShowRecord.created_at < this_month_start)
    ).one() or 0
    
    # Pending follow-ups
    pending = db.exec(
        select(func.count(NoShowRecord.id))
        .where(NoShowRecord.clinic_id == clinic_id)
        .where(NoShowRecord.followed_up == False)
    ).one() or 0
    
    # Rescheduled
    rescheduled = db.exec(
        select(func.count(NoShowRecord.id))
        .where(NoShowRecord.clinic_id == clinic_id)
        .where(NoShowRecord.rescheduled_appointment_id != None)
    ).one() or 0
    
    # Calculate no-show rate (this month)
    total_appointments_this_month = db.exec(
        select(func.count(Appointment.id))
        .where(Appointment.clinic_id == clinic_id)
        .where(Appointment.scheduled_time >= this_month_start)
    ).one() or 1  # Avoid division by zero
    
    no_show_rate = (this_month / total_appointments_this_month) * 100
    
    return NoShowStatsResponse(
        total_no_shows=total,
        this_month=this_month,
        last_month=last_month,
        follow_up_pending=pending,
        rescheduled_count=rescheduled,
        no_show_rate=round(no_show_rate, 1)
    )


@router.post("/no-shows/{clinic_id}/{no_show_id}/follow-up")
async def mark_followed_up(
    clinic_id: int,
    no_show_id: int,
    notes: Optional[str] = None,
    rescheduled_appointment_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """Mark a no-show as followed up."""
    no_show = db.exec(
        select(NoShowRecord)
        .where(NoShowRecord.id == no_show_id)
        .where(NoShowRecord.clinic_id == clinic_id)
    ).first()
    
    if not no_show:
        raise HTTPException(status_code=404, detail="No-show record not found")
    
    no_show.followed_up = True
    no_show.followed_up_at = datetime.utcnow()
    
    if notes:
        no_show.followup_notes = notes
    
    if rescheduled_appointment_id:
        no_show.rescheduled_appointment_id = rescheduled_appointment_id
    
    db.commit()
    
    return {"success": True, "message": "Marked as followed up"}


# -----------------------------------------------------------------------------
# Background Tasks
# -----------------------------------------------------------------------------

async def _send_appointment_confirmation(appointment: Appointment, db: Session):
    """Send confirmation SMS for new appointment."""
    try:
        from twilio_service import send_sms
        
        time_str = appointment.scheduled_time.strftime("%A, %B %d at %I:%M %p")
        message = (
            f"Your dental appointment is confirmed for {time_str}. "
            f"Reply YES to confirm or call us to reschedule. "
            f"- {appointment.patient_name.split()[0]}, we look forward to seeing you!"
        )
        
        send_sms(appointment.patient_phone, message)
        
        # Update appointment
        appointment.confirmation_sent = True
        db.commit()
        
        logger.info(f"Sent confirmation SMS for appointment {appointment.id}")
        
    except Exception as e:
        logger.error(f"Failed to send confirmation SMS: {e}")


async def _send_no_show_followup(appointment: Appointment, db: Session):
    """Send follow-up SMS after no-show."""
    try:
        from twilio_service import send_sms
        
        message = (
            f"Hi {appointment.patient_name.split()[0]}, we missed you at your dental appointment today. "
            f"We hope everything is okay! Please call us to reschedule at your earliest convenience."
        )
        
        send_sms(appointment.patient_phone, message)
        
        # Update no-show record
        no_show = db.exec(
            select(NoShowRecord).where(NoShowRecord.appointment_id == appointment.id)
        ).first()
        
        if no_show:
            no_show.followup_sms_sent = True
            db.commit()
        
        logger.info(f"Sent no-show follow-up SMS for appointment {appointment.id}")
        
    except Exception as e:
        logger.error(f"Failed to send no-show SMS: {e}")
