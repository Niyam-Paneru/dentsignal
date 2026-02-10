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

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlmodel import select

from db import get_session, Client, InboundCall
from models import ClinicCreate, ClinicUpdate, ClinicResponse, APIResponse
from prompt_builder import get_available_voices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Admin"])

# Import auth dependency from auth module (avoids circular import)
try:
    from dental_agent.auth import require_auth, JWT_SECRET, JWT_ALGORITHM
except ImportError:
    from auth import require_auth, JWT_SECRET, JWT_ALGORITHM

import jwt

async def verify_admin_token(authorization: str = Header(None, alias="Authorization")):
    """Verify JWT token for admin access."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


# -----------------------------------------------------------------------------
# Clinic CRUD Operations
# -----------------------------------------------------------------------------

@router.post("/clinics", response_model=APIResponse)
async def create_clinic(
    clinic_data: ClinicCreate,
    user: dict = Depends(verify_admin_token)
):
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
    user: dict = Depends(verify_admin_token),
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
async def get_clinic(
    clinic_id: int,
    user: dict = Depends(verify_admin_token),
):
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
async def update_clinic(
    clinic_id: int,
    updates: ClinicUpdate,
    user: dict = Depends(verify_admin_token),
):
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
async def delete_clinic(
    clinic_id: int,
    hard_delete: bool = Query(False),
    user: dict = Depends(verify_admin_token),
):
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
    user: dict = Depends(verify_admin_token),
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
    twilio_number: str = Query(..., description="Twilio number in E.164 format (e.g., +19048679643)"),
    user: dict = Depends(verify_admin_token),
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
        
        logger.info("Assigned Twilio number to clinic")
        
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
async def list_available_voices(user: dict = Depends(verify_admin_token)):
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
async def preview_clinic_prompt(
    clinic_id: int,
    user: dict = Depends(verify_admin_token),
):
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
async def get_dashboard_stats(user: dict = Depends(verify_admin_token)):
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


# -----------------------------------------------------------------------------
# Phone Number Provisioning (Automated Twilio Setup)
# -----------------------------------------------------------------------------

from pydantic import BaseModel

class ProvisionNumberRequest(BaseModel):
    """Request to provision a new Twilio number for a clinic."""
    clinic_id: int
    area_code: Optional[str] = None
    phone_number: Optional[str] = None  # Specific number to buy
    friendly_name: Optional[str] = None


@router.get("/admin/available-numbers")
async def list_available_numbers(
    area_code: Optional[str] = Query(None, description="Area code to search (e.g., 512)"),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(verify_admin_token),
):
    """
    List available Twilio phone numbers to purchase.
    
    Use this to show clients which numbers are available in their area.
    """
    from twilio_service import list_available_numbers as twilio_list_numbers
    
    result = twilio_list_numbers(area_code=area_code, limit=limit)
    
    if isinstance(result, dict) and result.get("error"):
        logger.error("Failed to list available numbers")
        raise HTTPException(status_code=500, detail="Failed to list available numbers")
    
    return {
        "available_numbers": result,
        "count": len(result) if isinstance(result, list) else 0,
    }


@router.post("/admin/provision-number")
async def provision_phone_number(
    request: ProvisionNumberRequest,
    user: dict = Depends(verify_admin_token),
):
    """
    Purchase a Twilio phone number and auto-configure webhooks for a clinic.
    
    This is the main endpoint for setting up new clinics!
    
    It will:
    1. Buy the phone number from Twilio
    2. Configure voice webhook → /inbound/voice
    3. Configure SMS webhook → /api/sms/inbound
    4. Update the clinic record with the new number
    
    Example:
        POST /api/admin/provision-number
        {
            "clinic_id": 123,
            "area_code": "512",
            "friendly_name": "Austin Dental Clinic"
        }
    """
    from twilio_service import provision_clinic_number
    
    # Verify clinic exists
    with get_session() as session:
        clinic = session.get(Client, request.clinic_id)
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found")
        
        if clinic.twilio_number:
            raise HTTPException(
                status_code=400,
                detail="Clinic already has a number assigned"
            )
    
    # Provision the number
    result = provision_clinic_number(
        clinic_id=request.clinic_id,
        area_code=request.area_code,
        phone_number=request.phone_number,
        friendly_name=request.friendly_name or clinic.name,
    )
    
    if not result.get("success"):
        logger.error("Failed to provision number")
        raise HTTPException(status_code=500, detail="Failed to provision number")
    
    # Update clinic with new number
    with get_session() as session:
        clinic = session.get(Client, request.clinic_id)
        if clinic:
            clinic.twilio_number = result["phone_number"]
            clinic.phone_display = result["phone_number"]  # Can be updated later
            session.commit()
    
    return {
        "success": True,
        "clinic_id": request.clinic_id,
        "phone_number": result["phone_number"],
        "twilio_sid": result["sid"],
        "webhooks": result["webhooks"],
        "message": "Phone number purchased and configured! Clinic is ready to receive calls.",
    }


@router.get("/admin/clinic-numbers")
async def list_all_clinic_numbers():
    """
    List all phone numbers in your Twilio account.
    
    Useful for auditing webhook configurations.
    """
    from twilio_service import list_clinic_numbers
    
    result = list_clinic_numbers()
    
    if isinstance(result, dict) and result.get("error"):
        logger.error("Failed to list clinic numbers")
        raise HTTPException(status_code=500, detail="Failed to list clinic numbers")
    
    return {
        "numbers": result,
        "count": len(result) if isinstance(result, list) else 0,
    }


@router.post("/admin/fix-webhooks/{phone_sid}")
async def fix_number_webhooks(phone_sid: str):
    """
    Update webhooks for an existing Twilio number.
    
    Use this if a number was set up manually with wrong webhooks.
    
    Args:
        phone_sid: Twilio Phone Number SID (starts with "PN")
    """
    from twilio_service import update_number_webhooks
    
    result = update_number_webhooks(phone_sid)
    
    if not result.get("success"):
        logger.error("Failed to update webhooks")
        raise HTTPException(status_code=500, detail="Failed to update webhooks")
    
    return result


@router.delete("/admin/release-number/{phone_sid}")
async def release_phone_number(phone_sid: str, clinic_id: Optional[int] = None):
    """
    Release (delete) a Twilio phone number.
    
    Use when a clinic cancels their subscription.
    
    WARNING: This permanently releases the number back to Twilio!
    
    Args:
        phone_sid: Twilio Phone Number SID
        clinic_id: Optional clinic ID to clear from database
    """
    from twilio_service import release_number
    
    result = release_number(phone_sid)
    
    if not result.get("success"):
        logger.error("Failed to release number")
        raise HTTPException(status_code=500, detail="Failed to release number")
    
    # Clear from clinic record if provided
    if clinic_id:
        with get_session() as session:
            clinic = session.get(Client, clinic_id)
            if clinic:
                clinic.twilio_number = None
                session.commit()
    
    return result
