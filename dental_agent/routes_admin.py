"""
routes_admin.py - Admin API Routes for Clinic Management

Endpoints:
- POST /api/clinics - Create a new clinic
- GET /api/clinics - List all clinics
- GET /api/clinics/{id} - Get clinic details
- PATCH /api/clinics/{id} - Update clinic
- DELETE /api/clinics/{id} - Delete clinic (soft delete)
- GET /api/clinics/{id}/calls - List calls for a clinic
- POST /api/clinics/{id}/assign-number - Assign Twilio number

These routes require authentication (JWT token).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from db import get_session, Client, InboundCall
from models import ClinicCreate, ClinicUpdate, ClinicResponse, APIResponse
from prompt_builder import get_available_voices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Admin"])


# -----------------------------------------------------------------------------
# Clinic CRUD Operations
# -----------------------------------------------------------------------------

@router.post("/clinics", response_model=APIResponse)
async def create_clinic(clinic_data: ClinicCreate):
    """
    Create a new clinic.
    
    This creates a Client record in the database with voice agent configuration.
    A Twilio number should be assigned separately using the assign-number endpoint.
    """
    with get_session() as session:
        # Check for duplicate email
        existing = session.exec(
            select(Client).where(Client.email == clinic_data.email)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"A clinic with email {clinic_data.email} already exists"
            )
        
        # Create the clinic
        clinic = Client(
            name=clinic_data.name,
            email=clinic_data.email,
            timezone=clinic_data.timezone,
            agent_name=clinic_data.agent_name,
            agent_voice=clinic_data.agent_voice,
            custom_instructions=clinic_data.custom_instructions,
            address=clinic_data.address,
            phone_display=clinic_data.phone_display,
            hours=clinic_data.hours,
            services=clinic_data.services,
            insurance_accepted=clinic_data.insurance_accepted,
            owner_email=clinic_data.owner_email or clinic_data.email,
            monthly_price=clinic_data.monthly_price,
            is_active=True,
        )
        
        session.add(clinic)
        session.commit()
        session.refresh(clinic)
        
        logger.info(f"Created clinic: {clinic.id} - {clinic.name}")
        
        return APIResponse(
            success=True,
            message=f"Clinic '{clinic.name}' created successfully",
            data={
                "id": clinic.id,
                "name": clinic.name,
                "email": clinic.email,
                "agent_name": clinic.agent_name,
            }
        )


@router.get("/clinics")
async def list_clinics(
    active_only: bool = Query(True, description="Only return active clinics"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List all clinics with pagination."""
    with get_session() as session:
        statement = select(Client).order_by(Client.created_at.desc())
        
        if active_only:
            statement = statement.where(Client.is_active == True)
        
        statement = statement.offset(offset).limit(limit)
        clinics = session.exec(statement).all()
        
        # Get total count
        count_statement = select(Client)
        if active_only:
            count_statement = count_statement.where(Client.is_active == True)
        total = len(session.exec(count_statement).all())
        
        return {
            "clinics": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "twilio_number": c.twilio_number,
                    "agent_name": c.agent_name,
                    "is_active": c.is_active,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in clinics
            ],
            "total": total,
            "offset": offset,
            "limit": limit,
        }


@router.get("/clinics/{clinic_id}")
async def get_clinic(clinic_id: int):
    """Get detailed information about a specific clinic."""
    with get_session() as session:
        clinic = session.get(Client, clinic_id)
        
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        # Get call statistics
        calls_statement = select(InboundCall).where(InboundCall.clinic_id == clinic_id)
        calls = session.exec(calls_statement).all()
        
        total_calls = len(calls)
        completed_calls = sum(1 for c in calls if c.status and c.status.value == "completed")
        
        return {
            "clinic": {
                "id": clinic.id,
                "name": clinic.name,
                "email": clinic.email,
                "timezone": clinic.timezone,
                "twilio_number": clinic.twilio_number,
                "agent_name": clinic.agent_name,
                "agent_voice": clinic.agent_voice,
                "custom_instructions": clinic.custom_instructions,
                "address": clinic.address,
                "phone_display": clinic.phone_display,
                "hours": clinic.hours,
                "services": clinic.services,
                "insurance_accepted": clinic.insurance_accepted,
                "owner_email": clinic.owner_email,
                "monthly_price": clinic.monthly_price,
                "is_active": clinic.is_active,
                "created_at": clinic.created_at.isoformat() if clinic.created_at else None,
                "updated_at": clinic.updated_at.isoformat() if clinic.updated_at else None,
            },
            "statistics": {
                "total_calls": total_calls,
                "completed_calls": completed_calls,
            }
        }


@router.patch("/clinics/{clinic_id}", response_model=APIResponse)
async def update_clinic(clinic_id: int, updates: ClinicUpdate):
    """Update a clinic's configuration."""
    with get_session() as session:
        clinic = session.get(Client, clinic_id)
        
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(clinic, key):
                setattr(clinic, key, value)
        
        clinic.updated_at = datetime.utcnow()
        
        session.commit()
        session.refresh(clinic)
        
        logger.info(f"Updated clinic {clinic_id}: {list(update_data.keys())}")
        
        return APIResponse(
            success=True,
            message=f"Clinic '{clinic.name}' updated successfully",
            data={"updated_fields": list(update_data.keys())}
        )


@router.delete("/clinics/{clinic_id}", response_model=APIResponse)
async def delete_clinic(clinic_id: int, hard_delete: bool = Query(False)):
    """
    Delete a clinic.
    
    By default, this performs a soft delete (sets is_active=False).
    Use hard_delete=True to permanently remove the record.
    """
    with get_session() as session:
        clinic = session.get(Client, clinic_id)
        
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        if hard_delete:
            session.delete(clinic)
            message = f"Clinic '{clinic.name}' permanently deleted"
        else:
            clinic.is_active = False
            clinic.updated_at = datetime.utcnow()
            message = f"Clinic '{clinic.name}' deactivated"
        
        session.commit()
        
        logger.info(f"Deleted clinic {clinic_id} (hard={hard_delete})")
        
        return APIResponse(
            success=True,
            message=message,
            data=None
        )


# -----------------------------------------------------------------------------
# Clinic-specific Operations
# -----------------------------------------------------------------------------

@router.get("/clinics/{clinic_id}/calls")
async def get_clinic_calls(
    clinic_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """Get all calls for a specific clinic."""
    with get_session() as session:
        clinic = session.get(Client, clinic_id)
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        statement = (
            select(InboundCall)
            .where(InboundCall.clinic_id == clinic_id)
            .order_by(InboundCall.started_at.desc())
        )
        
        if status:
            statement = statement.where(InboundCall.status == status)
        
        statement = statement.offset(offset).limit(limit)
        calls = session.exec(statement).all()
        
        return {
            "clinic_id": clinic_id,
            "clinic_name": clinic.name,
            "calls": [
                {
                    "id": call.id,
                    "from_number": call.from_number,
                    "status": call.status.value if call.status else None,
                    "outcome": call.outcome.value if call.outcome else None,
                    "duration_seconds": call.duration_seconds,
                    "caller_name": call.caller_name,
                    "is_new_patient": call.is_new_patient,
                    "reason_for_call": call.reason_for_call,
                    "started_at": call.started_at.isoformat() if call.started_at else None,
                }
                for call in calls
            ],
            "count": len(calls),
            "offset": offset,
            "limit": limit,
        }


@router.post("/clinics/{clinic_id}/assign-number", response_model=APIResponse)
async def assign_twilio_number(
    clinic_id: int,
    twilio_number: str = Query(..., description="Twilio number in E.164 format (e.g., +19048679643)")
):
    """
    Assign a Twilio phone number to a clinic.
    
    The number should be purchased through Twilio Console or API first.
    This endpoint just links it to the clinic in our database.
    """
    with get_session() as session:
        clinic = session.get(Client, clinic_id)
        
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        # Check if number is already assigned to another clinic
        existing = session.exec(
            select(Client).where(
                Client.twilio_number == twilio_number,
                Client.id != clinic_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Number {twilio_number} is already assigned to clinic '{existing.name}'"
            )
        
        clinic.twilio_number = twilio_number
        clinic.updated_at = datetime.utcnow()
        
        session.commit()
        
        logger.info(f"Assigned {twilio_number} to clinic {clinic_id}")
        
        return APIResponse(
            success=True,
            message=f"Number {twilio_number} assigned to {clinic.name}",
            data={
                "clinic_id": clinic_id,
                "twilio_number": twilio_number,
            }
        )


# -----------------------------------------------------------------------------
# Voice Configuration
# -----------------------------------------------------------------------------

@router.get("/voices")
async def list_available_voices():
    """Get list of available Deepgram voices for agent configuration."""
    voices = get_available_voices()
    
    return {
        "voices": [
            {
                "id": voice_id,
                "name": info["name"],
                "gender": info["gender"],
                "accent": info["accent"],
            }
            for voice_id, info in voices.items()
        ]
    }


@router.post("/clinics/{clinic_id}/test-prompt")
async def preview_clinic_prompt(clinic_id: int):
    """
    Preview the system prompt that would be used for this clinic.
    
    Useful for debugging and testing prompt configuration.
    """
    with get_session() as session:
        clinic = session.get(Client, clinic_id)
        
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        from prompt_builder import PromptBuilder
        builder = PromptBuilder(clinic)
        
        return {
            "clinic_id": clinic_id,
            "clinic_name": clinic.name,
            "system_prompt": builder.build_system_prompt(),
            "greeting": builder.build_greeting(),
            "voice_id": builder.get_voice_id(),
            "voice_info": builder.get_voice_info(),
        }


# -----------------------------------------------------------------------------
# Dashboard Statistics
# -----------------------------------------------------------------------------

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics."""
    with get_session() as session:
        # Count clinics
        clinics = session.exec(select(Client)).all()
        active_clinics = sum(1 for c in clinics if c.is_active)
        
        # Count calls
        calls = session.exec(select(InboundCall)).all()
        
        # Calculate stats
        total_calls = len(calls)
        completed_calls = sum(1 for c in calls if c.status and c.status.value == "completed")
        total_duration = sum(c.duration_seconds or 0 for c in calls)
        
        # Calls today
        today = datetime.utcnow().date()
        calls_today = sum(
            1 for c in calls 
            if c.started_at and c.started_at.date() == today
        )
        
        return {
            "clinics": {
                "total": len(clinics),
                "active": active_clinics,
            },
            "calls": {
                "total": total_calls,
                "completed": completed_calls,
                "today": calls_today,
                "total_duration_seconds": total_duration,
                "average_duration_seconds": total_duration // completed_calls if completed_calls > 0 else 0,
            }
        }
