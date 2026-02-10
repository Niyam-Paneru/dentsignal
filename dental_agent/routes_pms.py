"""
routes_pms.py - Practice Management System Integration API

Provides endpoints for:
- PMS integration configuration (Open Dental, Dentrix, Eaglesoft)
- Connection testing and status
- Direct PMS operations (patients, appointments, providers)
- Availability checking via PMS
- Appointment booking via PMS

These endpoints power the dashboard PMS settings and provide
the voice agent with real PMS data for appointment scheduling.
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from db import get_session, Client, PMSIntegration
from open_dental_service import (
    OpenDentalService,
    OpenDentalConfig,
    OpenDentalApiMode,
    create_open_dental_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pms", tags=["PMS Integration"])

# DentSignal's Open Dental Developer Key (shared across all clinics)
OD_DEVELOPER_KEY = os.getenv("OPEN_DENTAL_DEVELOPER_KEY", "")


# =============================================================================
# Request/Response Models
# =============================================================================

class PMSConfigRequest(BaseModel):
    """Request model for configuring PMS integration."""
    provider: str = Field(..., description="PMS provider: open_dental, dentrix, eaglesoft")
    
    # Open Dental settings
    od_customer_key: Optional[str] = Field(None, description="Open Dental customer API key")
    od_api_mode: str = Field("remote", description="API mode: remote, service, local")
    od_base_url: Optional[str] = Field(None, description="Override URL for service/local mode")
    od_clinic_num: Optional[int] = Field(None, description="ClinicNum for multi-location")
    
    # Future: Dentrix/Eaglesoft
    dentrix_api_key: Optional[str] = None
    eaglesoft_api_key: Optional[str] = None


class PMSConfigResponse(BaseModel):
    """Response model for PMS configuration."""
    provider: str
    is_active: bool
    connection_status: str
    connection_error: Optional[str] = None
    last_connection_test: Optional[str] = None
    od_api_mode: Optional[str] = None
    od_clinic_num: Optional[int] = None
    od_permission_tier: Optional[str] = None
    sync_appointments: bool = True
    sync_patients: bool = True
    auto_create_patients: bool = True


class ConnectionTestResponse(BaseModel):
    """Response from connection test."""
    success: bool
    message: str
    provider_count: Optional[int] = None


class AvailabilityRequest(BaseModel):
    """Request to check availability via PMS."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time_preference: Optional[str] = Field(None, description="early_morning, morning, afternoon, evening, any")
    appointment_type: Optional[str] = Field(None, description="cleaning, checkup, procedure, emergency, consultation")
    is_new_patient: bool = False


class BookAppointmentRequest(BaseModel):
    """Request to book an appointment via PMS."""
    patient_name: str
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format")
    reason: str
    phone_number: Optional[str] = None
    is_new_patient: bool = False
    urgency: str = "routine"
    notes: Optional[str] = None


class CancelAppointmentRequest(BaseModel):
    """Request to cancel an appointment via PMS."""
    patient_name: str
    appointment_date: Optional[str] = None
    reason: Optional[str] = None
    reschedule: bool = False


class PatientLookupRequest(BaseModel):
    """Request to look up a patient in PMS."""
    patient_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None


# =============================================================================
# Helpers
# =============================================================================

def _get_clinic_id(clinic_id: Optional[int] = None) -> int:
    """Get clinic ID (placeholder - in production, resolve from auth)."""
    return clinic_id or 1


async def _get_od_service(
    pms_integration: PMSIntegration,
) -> OpenDentalService:
    """Create an OpenDentalService from PMS integration settings."""
    if not OD_DEVELOPER_KEY:
        raise HTTPException(
            status_code=500,
            detail="Open Dental developer key not configured. Set OPEN_DENTAL_DEVELOPER_KEY env var.",
        )
    
    if not pms_integration.od_customer_key:
        raise HTTPException(
            status_code=400,
            detail="Open Dental customer key not set. Configure it in PMS settings.",
        )
    
    return create_open_dental_service(
        developer_key=OD_DEVELOPER_KEY,
        customer_key=pms_integration.od_customer_key,
        api_mode=pms_integration.od_api_mode or "remote",
        base_url=pms_integration.od_base_url,
        clinic_num=pms_integration.od_clinic_num,
    )


async def _get_pms_and_service(
    clinic_id: int,
    session: Session,
) -> tuple[PMSIntegration, OpenDentalService]:
    """Get PMS integration config and create the service. Raises 404/400 if not configured."""
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == clinic_id)
    ).first()
    
    if not pms:
        raise HTTPException(status_code=404, detail="PMS integration not configured for this clinic.")
    
    if not pms.is_active:
        raise HTTPException(status_code=400, detail="PMS integration is not active.")
    
    if pms.provider != "open_dental":
        raise HTTPException(
            status_code=400,
            detail=f"PMS provider '{pms.provider}' is not yet supported. Only Open Dental is available.",
        )
    
    service = await _get_od_service(pms)
    return pms, service


# =============================================================================
# Configuration Endpoints
# =============================================================================

@router.get("/config")
async def get_pms_config(
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Get current PMS integration configuration for a clinic."""
    cid = _get_clinic_id(clinic_id)
    
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == cid)
    ).first()
    
    if not pms:
        return {
            "provider": "none",
            "is_active": False,
            "connection_status": "not_configured",
            "available_providers": [
                {
                    "id": "open_dental",
                    "name": "Open Dental",
                    "status": "available",
                    "description": "Full integration with Open Dental PMS. Supports appointment scheduling, patient management, and real-time availability.",
                    "pricing": "Free for read-only, $30/mo for full scheduling",
                },
                {
                    "id": "dentrix",
                    "name": "Dentrix",
                    "status": "coming_soon",
                    "description": "Integration with Henry Schein Dentrix. Coming Q1 2025.",
                },
                {
                    "id": "eaglesoft",
                    "name": "Eaglesoft",
                    "status": "coming_soon",
                    "description": "Integration with Patterson Eaglesoft. Coming Q1 2025.",
                },
                {
                    "id": "curve",
                    "name": "Curve Dental",
                    "status": "coming_soon",
                    "description": "Integration with Curve Dental (cloud-based). Coming Q2 2025.",
                },
            ],
        }
    
    return PMSConfigResponse(
        provider=pms.provider,
        is_active=pms.is_active,
        connection_status=pms.connection_status,
        connection_error=pms.connection_error,
        last_connection_test=pms.last_connection_test.isoformat() if pms.last_connection_test else None,
        od_api_mode=pms.od_api_mode,
        od_clinic_num=pms.od_clinic_num,
        od_permission_tier=pms.od_permission_tier,
        sync_appointments=pms.sync_appointments,
        sync_patients=pms.sync_patients,
        auto_create_patients=pms.auto_create_patients,
    )


@router.post("/config")
async def save_pms_config(
    request: PMSConfigRequest,
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Save or update PMS integration configuration."""
    cid = _get_clinic_id(clinic_id)
    
    # Validate provider
    valid_providers = ["open_dental", "dentrix", "eaglesoft", "curve", "none"]
    if request.provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of: {valid_providers}")
    
    # Check for unsupported providers
    if request.provider in ("dentrix", "eaglesoft", "curve"):
        raise HTTPException(
            status_code=400,
            detail=f"{request.provider.title()} integration is coming soon. Only Open Dental is currently supported.",
        )
    
    # Get or create PMS integration
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == cid)
    ).first()
    
    if not pms:
        pms = PMSIntegration(clinic_id=cid)
        session.add(pms)
    
    # Update fields
    pms.provider = request.provider
    pms.updated_at = datetime.utcnow()
    
    if request.provider == "open_dental":
        if request.od_customer_key:
            pms.od_customer_key = request.od_customer_key
        pms.od_api_mode = request.od_api_mode
        pms.od_base_url = request.od_base_url
        pms.od_clinic_num = request.od_clinic_num
        pms.connection_status = "not_tested"
    elif request.provider == "none":
        pms.is_active = False
        pms.connection_status = "not_configured"
    
    session.commit()
    session.refresh(pms)
    
    return {
        "success": True,
        "message": f"PMS configuration saved for {request.provider}.",
        "next_step": "Test the connection to verify your API keys work.",
    }


@router.post("/test-connection")
async def test_pms_connection(
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Test the PMS connection with saved credentials."""
    cid = _get_clinic_id(clinic_id)
    
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == cid)
    ).first()
    
    if not pms:
        raise HTTPException(status_code=404, detail="PMS not configured. Save configuration first.")
    
    if pms.provider != "open_dental":
        raise HTTPException(status_code=400, detail=f"Connection test not available for {pms.provider}.")
    
    try:
        service = await _get_od_service(pms)
        result = await service.test_connection()
        
        # Update connection status
        pms.last_connection_test = datetime.utcnow()
        pms.connection_status = "connected" if result["success"] else "failed"
        pms.connection_error = None if result["success"] else result["message"]
        
        if result["success"]:
            pms.is_active = True
            # If we can read providers, at minimum we have free tier
            pms.od_permission_tier = "free"
        
        pms.updated_at = datetime.utcnow()
        session.commit()
        
        await service.close()
        
        return ConnectionTestResponse(**result)
        
    except Exception as e:
        logger.error(f"PMS connection test failed: {e}")
        pms.last_connection_test = datetime.utcnow()
        pms.connection_status = "failed"
        pms.connection_error = "Connection failed"
        pms.updated_at = datetime.utcnow()
        session.commit()
        
        return ConnectionTestResponse(
            success=False,
            message="Connection failed. Please verify credentials and network access.",
        )


@router.put("/settings")
async def update_pms_settings(
    sync_appointments: Optional[bool] = None,
    sync_patients: Optional[bool] = None,
    auto_create_patients: Optional[bool] = None,
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Update PMS sync settings."""
    cid = _get_clinic_id(clinic_id)
    
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == cid)
    ).first()
    
    if not pms:
        raise HTTPException(status_code=404, detail="PMS not configured.")
    
    if sync_appointments is not None:
        pms.sync_appointments = sync_appointments
    if sync_patients is not None:
        pms.sync_patients = sync_patients
    if auto_create_patients is not None:
        pms.auto_create_patients = auto_create_patients
    
    pms.updated_at = datetime.utcnow()
    session.commit()
    
    return {"success": True, "message": "PMS settings updated."}


@router.delete("/config")
async def remove_pms_config(
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Remove PMS integration (disconnect)."""
    cid = _get_clinic_id(clinic_id)
    
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == cid)
    ).first()
    
    if not pms:
        raise HTTPException(status_code=404, detail="PMS not configured.")
    
    pms.is_active = False
    pms.provider = "none"
    pms.connection_status = "not_configured"
    pms.od_customer_key = None
    pms.updated_at = datetime.utcnow()
    session.commit()
    
    return {"success": True, "message": "PMS integration disconnected."}


# =============================================================================
# PMS Data Endpoints (proxied to Open Dental)
# =============================================================================

@router.get("/providers")
async def get_pms_providers(
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Get providers (dentists & hygienists) from PMS."""
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        providers = await service.get_providers()
        return {
            "providers": [
                {
                    "id": p.prov_num,
                    "name": p.display_name,
                    "abbr": p.abbr,
                    "type": "hygienist" if p.is_secondary else "dentist",
                }
                for p in providers
            ]
        }
    finally:
        await service.close()


@router.get("/operatories")
async def get_pms_operatories(
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Get operatories (treatment rooms) from PMS."""
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        ops = await service.get_operatories()
        return {
            "operatories": [
                {
                    "id": o.op_num,
                    "name": o.name,
                    "abbrev": o.abbrev,
                    "provider_dentist": o.provider_dentist,
                    "provider_hygienist": o.provider_hygienist,
                    "is_hygiene": o.is_hygiene,
                }
                for o in ops
            ]
        }
    finally:
        await service.close()


@router.post("/check-availability")
async def check_pms_availability(
    request: AvailabilityRequest,
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """
    Check appointment availability via PMS.
    
    Used by both the dashboard and the voice agent.
    """
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        result = await service.voice_check_availability(
            date_str=request.date,
            time_preference=request.time_preference,
            appointment_type=request.appointment_type,
            is_new_patient=request.is_new_patient,
        )
        return result
    finally:
        await service.close()


@router.post("/book-appointment")
async def book_pms_appointment(
    request: BookAppointmentRequest,
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """
    Book an appointment via PMS.
    
    Creates patient in PMS if needed, finds matching slot, books appointment.
    """
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        result = await service.voice_book_appointment(
            patient_name=request.patient_name,
            date_str=request.date,
            time_str=request.time,
            reason=request.reason,
            phone_number=request.phone_number,
            is_new_patient=request.is_new_patient,
            urgency=request.urgency,
            notes=request.notes,
        )
        return result
    finally:
        await service.close()


@router.post("/cancel-appointment")
async def cancel_pms_appointment(
    request: CancelAppointmentRequest,
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Cancel an appointment via PMS."""
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        result = await service.voice_cancel_appointment(
            patient_name=request.patient_name,
            appointment_date=request.appointment_date,
            reason=request.reason,
            reschedule=request.reschedule,
        )
        return result
    finally:
        await service.close()


@router.post("/lookup-patient")
async def lookup_pms_patient(
    request: PatientLookupRequest,
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Look up a patient in the PMS."""
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        result = await service.voice_lookup_patient(
            patient_name=request.patient_name,
            phone_number=request.phone_number,
            date_of_birth=request.date_of_birth,
        )
        return result
    finally:
        await service.close()


@router.get("/appointments")
async def get_pms_appointments(
    date_str: Optional[str] = Query(None, alias="date"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    patient_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Get appointments from PMS with optional filters."""
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        # Parse dates
        target_date = None
        start_date = None
        end_date = None
        
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_start:
            start_date = datetime.strptime(date_start, "%Y-%m-%d").date()
        if date_end:
            end_date = datetime.strptime(date_end, "%Y-%m-%d").date()
        
        # If patient name given, search for patient first
        pat_num = None
        if patient_name:
            parts = patient_name.split()
            patients = await service.search_patients(
                first_name=parts[0] if parts else None,
                last_name=parts[-1] if len(parts) > 1 else None,
            )
            if patients:
                pat_num = patients[0].pat_num
        
        appointments = await service.get_appointments(
            pat_num=pat_num,
            target_date=target_date,
            date_start=start_date,
            date_end=end_date,
            status=status,
        )
        
        return {
            "appointments": [a.to_dict() for a in appointments],
            "count": len(appointments),
        }
    finally:
        await service.close()


@router.get("/slots")
async def get_pms_slots(
    date_str: Optional[str] = Query(None, alias="date"),
    days_ahead: int = Query(7),
    length_minutes: int = Query(30),
    provider_num: Optional[int] = Query(None),
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """
    Get available appointment slots from PMS.
    
    Returns both raw slot data and AI-formatted text.
    """
    cid = _get_clinic_id(clinic_id)
    pms, service = await _get_pms_and_service(cid, session)
    
    try:
        target = None
        if date_str:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Get formatted slots for AI
        formatted = await service.get_available_slots_formatted(
            target_date=target,
            days_ahead=days_ahead,
            length_minutes=length_minutes,
        )
        
        # Also get raw slots
        slots = await service.get_available_slots(
            date_start=target or date.today(),
            date_end=(target or date.today()) + timedelta(days=days_ahead),
            length_minutes=length_minutes,
            provider_num=provider_num,
        )
        
        return {
            "formatted": formatted,
            "slots": [s.to_dict() for s in slots],
            "count": len(slots),
        }
    finally:
        await service.close()


# =============================================================================
# Status Endpoint
# =============================================================================

@router.get("/status")
async def get_pms_status(
    clinic_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    """Get current PMS integration status summary."""
    cid = _get_clinic_id(clinic_id)
    
    pms = session.exec(
        select(PMSIntegration).where(PMSIntegration.clinic_id == cid)
    ).first()
    
    if not pms or pms.provider == "none":
        return {
            "configured": False,
            "provider": "none",
            "message": "No PMS integration configured. Set up Open Dental to enable real-time scheduling.",
        }
    
    return {
        "configured": True,
        "provider": pms.provider,
        "is_active": pms.is_active,
        "connection_status": pms.connection_status,
        "last_test": pms.last_connection_test.isoformat() if pms.last_connection_test else None,
        "features": {
            "sync_appointments": pms.sync_appointments,
            "sync_patients": pms.sync_patients,
            "auto_create_patients": pms.auto_create_patients,
            "permission_tier": pms.od_permission_tier,
        },
    }
