"""
routes_dnc.py — Do-Not-Call Admin API Routes (AG-9)

Endpoints:
- POST   /api/dnc            — Add a phone number to the DNC list
- DELETE  /api/dnc            — Remove a phone number from the DNC list
- GET     /api/dnc            — List DNC entries for a clinic
- POST    /api/dnc/check      — Check if a number is on the DNC list

These routes require authentication (JWT token).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from pydantic import BaseModel, Field

try:
    from dental_agent.db import get_session, DoNotCall, DNCReason
    from dental_agent.dnc_service import add_to_dnc, remove_from_dnc, list_dnc, is_dnc
    from dental_agent.utils import normalize_phone, mask_phone
except ImportError:
    from db import get_session, DoNotCall, DNCReason
    from dnc_service import add_to_dnc, remove_from_dnc, list_dnc, is_dnc
    from utils import normalize_phone, mask_phone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dnc", tags=["Do-Not-Call"])

# Import auth
try:
    from dental_agent.auth import require_auth, JWT_SECRET, JWT_ALGORITHM
except ImportError:
    from auth import require_auth, JWT_SECRET, JWT_ALGORITHM

import jwt


# ---------------------------------------------------------------------------
# Auth helper (same pattern as routes_admin.py)
# ---------------------------------------------------------------------------

async def verify_admin_token(authorization: str = Header(None, alias="Authorization")):
    """Verify JWT token for DNC admin access."""
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


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class DNCAddRequest(BaseModel):
    phone: str = Field(..., description="Phone number in any format")
    clinic_id: Optional[int] = Field(None, description="Clinic ID (omit for global)")
    reason: str = Field("admin", description="Reason: patient_request|complaint|legal|wrong_number|admin")
    notes: Optional[str] = Field(None, description="Optional notes")


class DNCRemoveRequest(BaseModel):
    phone: str = Field(..., description="Phone number to remove")
    clinic_id: Optional[int] = Field(None, description="Clinic ID (omit for global)")


class DNCCheckRequest(BaseModel):
    phone: str = Field(..., description="Phone number to check")
    clinic_id: Optional[int] = Field(None, description="Clinic ID (omit for global)")


class DNCEntryResponse(BaseModel):
    id: int
    clinic_id: Optional[int]
    phone_masked: str
    reason: str
    notes: Optional[str]
    added_by: Optional[str]
    created_at: str
    is_active: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_dnc_entry(
    body: DNCAddRequest,
    user: dict = Depends(verify_admin_token),
):
    """Add a phone number to the Do-Not-Call list."""
    # Validate reason enum
    try:
        reason_enum = DNCReason(body.reason)
    except ValueError:
        valid = [r.value for r in DNCReason]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason '{body.reason}'. Valid: {valid}",
        )

    normalized = normalize_phone(body.phone)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    with get_session() as session:
        entry = add_to_dnc(
            session,
            phone=body.phone,
            clinic_id=body.clinic_id,
            reason=reason_enum,
            notes=body.notes,
            added_by=user.get("sub", "unknown"),
        )
        session.commit()
        session.refresh(entry)

        logger.info(
            f"DNC entry added via API: ***{normalized[-4:]} "
            f"clinic={body.clinic_id} by={user.get('sub', 'unknown')}"
        )

        return {
            "success": True,
            "message": f"Phone {mask_phone(normalized)} added to DNC list",
            "entry": {
                "id": entry.id,
                "clinic_id": entry.clinic_id,
                "reason": entry.reason.value if hasattr(entry.reason, "value") else entry.reason,
                "is_active": entry.is_active,
            },
        }


@router.delete("")
async def remove_dnc_entry(
    body: DNCRemoveRequest,
    user: dict = Depends(verify_admin_token),
):
    """Remove a phone number from the Do-Not-Call list (soft-delete)."""
    normalized = normalize_phone(body.phone)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    with get_session() as session:
        removed = remove_from_dnc(session, phone=body.phone, clinic_id=body.clinic_id)
        session.commit()

    if not removed:
        raise HTTPException(status_code=404, detail="Phone number not found on DNC list")

    logger.info(
        f"DNC entry removed via API: ***{normalized[-4:]} "
        f"clinic={body.clinic_id} by={user.get('sub', 'unknown')}"
    )

    return {
        "success": True,
        "message": f"Phone {mask_phone(normalized)} removed from DNC list",
    }


@router.get("")
async def list_dnc_entries(
    clinic_id: Optional[int] = Query(None, description="Filter by clinic ID"),
    include_inactive: bool = Query(False, description="Include removed entries"),
    user: dict = Depends(verify_admin_token),
):
    """List DNC entries for a clinic (or global)."""
    with get_session() as session:
        entries = list_dnc(session, clinic_id=clinic_id, include_inactive=include_inactive)

        results = []
        for entry in entries:
            phone_display = mask_phone(entry.phone) if entry.phone else "***"
            results.append(
                DNCEntryResponse(
                    id=entry.id,
                    clinic_id=entry.clinic_id,
                    phone_masked=phone_display,
                    reason=entry.reason.value if hasattr(entry.reason, "value") else str(entry.reason),
                    notes=entry.notes,
                    added_by=entry.added_by,
                    created_at=entry.created_at.isoformat() if entry.created_at else "",
                    is_active=entry.is_active,
                )
            )

    return {
        "success": True,
        "count": len(results),
        "entries": [r.model_dump() for r in results],
    }


@router.post("/check")
async def check_dnc(
    body: DNCCheckRequest,
    user: dict = Depends(verify_admin_token),
):
    """Check whether a phone number is on the DNC list."""
    normalized = normalize_phone(body.phone)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    with get_session() as session:
        blocked = is_dnc(session, phone=body.phone, clinic_id=body.clinic_id)

    return {
        "success": True,
        "phone_masked": mask_phone(normalized),
        "is_dnc": blocked,
    }
