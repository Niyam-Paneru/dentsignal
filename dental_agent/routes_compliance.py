"""
routes_compliance.py — HIPAA Compliance API Routes (AG-11)

Endpoints:
  BAA Management:
  - POST   /api/compliance/baa           — Add a BAA record
  - GET    /api/compliance/baa           — List BAA records for a clinic
  - PUT    /api/compliance/baa/{baa_id}  — Update a BAA record
  - DELETE /api/compliance/baa/{baa_id}  — Delete a BAA record
  - GET    /api/compliance/baa/status    — Compliance summary (signed vs missing)

  Retention Policies:
  - GET    /api/compliance/retention         — Get retention policy for clinic
  - PUT    /api/compliance/retention         — Update retention policy

  Data Deletion (HIPAA Right of Deletion):
  - POST   /api/compliance/deletion-request  — Submit a deletion request
  - GET    /api/compliance/deletion-request  — List deletion requests
  - POST   /api/compliance/deletion-request/{id}/execute — Execute a deletion
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from pydantic import BaseModel, Field
from sqlmodel import Session, select

try:
    from dental_agent.db import (
        get_session,
        BusinessAssociateAgreement,
        BAAStatus,
        VendorType,
        RetentionPolicy,
        DataDeletionRequest,
    )
except ImportError:
    from db import (
        get_session,
        BusinessAssociateAgreement,
        BAAStatus,
        VendorType,
        RetentionPolicy,
        DataDeletionRequest,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["Compliance & HIPAA"])

# Import auth
try:
    from dental_agent.auth import require_auth, JWT_SECRET, JWT_ALGORITHM
except ImportError:
    from auth import require_auth, JWT_SECRET, JWT_ALGORITHM

import jwt


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

async def verify_admin_token(authorization: str = Header(None, alias="Authorization")):
    """Verify JWT token for compliance admin access."""
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
# Request / Response Models
# ---------------------------------------------------------------------------

class BAACreateRequest(BaseModel):
    clinic_id: str
    vendor_name: str = Field(max_length=255)
    vendor_type: VendorType = VendorType.OTHER
    baa_status: BAAStatus = BAAStatus.PENDING
    signed_date: Optional[str] = None
    expiry_date: Optional[str] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None


class BAAUpdateRequest(BaseModel):
    vendor_name: Optional[str] = None
    vendor_type: Optional[VendorType] = None
    baa_status: Optional[BAAStatus] = None
    signed_date: Optional[str] = None
    expiry_date: Optional[str] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None


class RetentionPolicyRequest(BaseModel):
    clinic_id: str
    call_recording_days: int = Field(default=90, ge=1)
    call_transcript_days: int = Field(default=365, ge=1)
    patient_data_days: int = Field(default=2555, ge=365)    # Min 1 year
    audit_log_days: int = Field(default=2555, ge=365)       # Min 1 year


class DeletionRequestCreate(BaseModel):
    clinic_id: str
    patient_identifier: str = Field(max_length=255)
    requested_by: str = Field(max_length=255)
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Known sub-processors that require BAAs
# ---------------------------------------------------------------------------

REQUIRED_VENDORS = [
    {"name": "Supabase", "type": VendorType.DATABASE},
    {"name": "Telnyx", "type": VendorType.TELEPHONY},
    {"name": "Deepgram", "type": VendorType.AI_PROVIDER},
    {"name": "Azure OpenAI", "type": VendorType.AI_PROVIDER},
    {"name": "DigitalOcean", "type": VendorType.CLOUD_HOSTING},
]


# ===========================================================================
# BAA Endpoints
# ===========================================================================

@router.post("/baa", status_code=status.HTTP_201_CREATED)
async def create_baa(
    req: BAACreateRequest,
    token: dict = Depends(verify_admin_token),
):
    """Add a BAA record for a sub-processor."""
    with get_session() as session:
        baa = BusinessAssociateAgreement(
            clinic_id=req.clinic_id,
            vendor_name=req.vendor_name,
            vendor_type=req.vendor_type,
            baa_status=req.baa_status,
            signed_date=datetime.fromisoformat(req.signed_date) if req.signed_date else None,
            expiry_date=datetime.fromisoformat(req.expiry_date) if req.expiry_date else None,
            document_url=req.document_url,
            notes=req.notes,
        )
        session.add(baa)
        session.commit()
        session.refresh(baa)
        logger.info("BAA created: vendor=%s clinic=%s", req.vendor_name, req.clinic_id)
        return {"ok": True, "baa_id": baa.id, "vendor": baa.vendor_name, "status": baa.baa_status}


@router.get("/baa")
async def list_baas(
    clinic_id: str = Query(...),
    token: dict = Depends(verify_admin_token),
):
    """List all BAA records for a clinic."""
    with get_session() as session:
        stmt = select(BusinessAssociateAgreement).where(
            BusinessAssociateAgreement.clinic_id == clinic_id
        )
        baas = session.exec(stmt).all()
        return {
            "ok": True,
            "count": len(baas),
            "baas": [
                {
                    "id": b.id,
                    "vendor_name": b.vendor_name,
                    "vendor_type": b.vendor_type,
                    "baa_status": b.baa_status,
                    "signed_date": b.signed_date.isoformat() if b.signed_date else None,
                    "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
                    "document_url": b.document_url,
                    "notes": b.notes,
                }
                for b in baas
            ],
        }


@router.put("/baa/{baa_id}")
async def update_baa(
    baa_id: int,
    req: BAAUpdateRequest,
    token: dict = Depends(verify_admin_token),
):
    """Update an existing BAA record."""
    with get_session() as session:
        baa = session.get(BusinessAssociateAgreement, baa_id)
        if not baa:
            raise HTTPException(status_code=404, detail="BAA not found")

        for field, value in req.model_dump(exclude_unset=True).items():
            if field in ("signed_date", "expiry_date") and value is not None:
                value = datetime.fromisoformat(value)
            setattr(baa, field, value)
        baa.updated_at = datetime.utcnow()

        session.add(baa)
        session.commit()
        session.refresh(baa)
        logger.info("BAA updated: id=%s vendor=%s", baa_id, baa.vendor_name)
        return {"ok": True, "baa_id": baa.id, "status": baa.baa_status}


@router.delete("/baa/{baa_id}")
async def delete_baa(
    baa_id: int,
    token: dict = Depends(verify_admin_token),
):
    """Delete a BAA record."""
    with get_session() as session:
        baa = session.get(BusinessAssociateAgreement, baa_id)
        if not baa:
            raise HTTPException(status_code=404, detail="BAA not found")
        session.delete(baa)
        session.commit()
        logger.info("BAA deleted: id=%s vendor=%s", baa_id, baa.vendor_name)
        return {"ok": True, "deleted": baa_id}


@router.get("/baa/status")
async def baa_compliance_status(
    clinic_id: str = Query(...),
    token: dict = Depends(verify_admin_token),
):
    """
    Check compliance status — which required vendors have signed BAAs
    and which are missing.
    """
    with get_session() as session:
        stmt = select(BusinessAssociateAgreement).where(
            BusinessAssociateAgreement.clinic_id == clinic_id
        )
        existing = session.exec(stmt).all()
        signed_vendors = {
            b.vendor_name.lower()
            for b in existing
            if b.baa_status == BAAStatus.SIGNED
        }

        results = []
        for vendor in REQUIRED_VENDORS:
            is_signed = vendor["name"].lower() in signed_vendors
            results.append({
                "vendor": vendor["name"],
                "type": vendor["type"],
                "baa_signed": is_signed,
            })

        all_signed = all(r["baa_signed"] for r in results)
        return {
            "ok": True,
            "clinic_id": clinic_id,
            "hipaa_ready": all_signed,
            "vendors": results,
            "message": (
                "All required BAAs are signed. You may claim HIPAA-compliant."
                if all_signed
                else "Some BAAs are missing. Current status: HIPAA-ready infrastructure."
            ),
        }


# ===========================================================================
# Retention Policy Endpoints
# ===========================================================================

@router.get("/retention")
async def get_retention_policy(
    clinic_id: str = Query(...),
    token: dict = Depends(verify_admin_token),
):
    """Get data retention policy for a clinic (returns defaults if none set)."""
    with get_session() as session:
        stmt = select(RetentionPolicy).where(RetentionPolicy.clinic_id == clinic_id)
        policy = session.exec(stmt).first()
        if not policy:
            return {
                "ok": True,
                "is_default": True,
                "clinic_id": clinic_id,
                "call_recording_days": 90,
                "call_transcript_days": 365,
                "patient_data_days": 2555,
                "audit_log_days": 2555,
            }
        return {
            "ok": True,
            "is_default": False,
            "clinic_id": policy.clinic_id,
            "call_recording_days": policy.call_recording_days,
            "call_transcript_days": policy.call_transcript_days,
            "patient_data_days": policy.patient_data_days,
            "audit_log_days": policy.audit_log_days,
        }


@router.put("/retention")
async def update_retention_policy(
    req: RetentionPolicyRequest,
    token: dict = Depends(verify_admin_token),
):
    """Create or update data retention policy for a clinic."""
    with get_session() as session:
        stmt = select(RetentionPolicy).where(RetentionPolicy.clinic_id == req.clinic_id)
        policy = session.exec(stmt).first()
        if policy:
            policy.call_recording_days = req.call_recording_days
            policy.call_transcript_days = req.call_transcript_days
            policy.patient_data_days = req.patient_data_days
            policy.audit_log_days = req.audit_log_days
            policy.updated_at = datetime.utcnow()
        else:
            policy = RetentionPolicy(
                clinic_id=req.clinic_id,
                call_recording_days=req.call_recording_days,
                call_transcript_days=req.call_transcript_days,
                patient_data_days=req.patient_data_days,
                audit_log_days=req.audit_log_days,
            )
        session.add(policy)
        session.commit()
        session.refresh(policy)
        logger.info("Retention policy updated: clinic=%s", req.clinic_id)
        return {"ok": True, "clinic_id": policy.clinic_id, "policy": {
            "call_recording_days": policy.call_recording_days,
            "call_transcript_days": policy.call_transcript_days,
            "patient_data_days": policy.patient_data_days,
            "audit_log_days": policy.audit_log_days,
        }}


# ===========================================================================
# Data Deletion Request Endpoints
# ===========================================================================

@router.post("/deletion-request", status_code=status.HTTP_201_CREATED)
async def create_deletion_request(
    req: DeletionRequestCreate,
    token: dict = Depends(verify_admin_token),
):
    """Submit a patient data deletion request (HIPAA right of deletion)."""
    with get_session() as session:
        dr = DataDeletionRequest(
            clinic_id=req.clinic_id,
            patient_identifier=req.patient_identifier,
            requested_by=req.requested_by,
            reason=req.reason,
        )
        session.add(dr)
        session.commit()
        session.refresh(dr)
        logger.info("Deletion request created: id=%s clinic=%s", dr.id, req.clinic_id)
        return {"ok": True, "request_id": dr.id, "status": dr.status}


@router.get("/deletion-request")
async def list_deletion_requests(
    clinic_id: str = Query(...),
    token: dict = Depends(verify_admin_token),
):
    """List all deletion requests for a clinic."""
    with get_session() as session:
        stmt = select(DataDeletionRequest).where(
            DataDeletionRequest.clinic_id == clinic_id
        )
        requests = session.exec(stmt).all()
        return {
            "ok": True,
            "count": len(requests),
            "requests": [
                {
                    "id": r.id,
                    "patient_identifier": r.patient_identifier,
                    "requested_by": r.requested_by,
                    "reason": r.reason,
                    "status": r.status,
                    "data_types_deleted": json.loads(r.data_types_deleted) if r.data_types_deleted else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                    "created_at": r.created_at.isoformat(),
                }
                for r in requests
            ],
        }


@router.post("/deletion-request/{request_id}/execute")
async def execute_deletion_request(
    request_id: int,
    token: dict = Depends(verify_admin_token),
):
    """
    Execute a data deletion request.

    This scaffold marks the request as completed and records which data
    categories were targeted. In production, integrate with actual data
    stores to purge records.
    """
    with get_session() as session:
        dr = session.get(DataDeletionRequest, request_id)
        if not dr:
            raise HTTPException(status_code=404, detail="Deletion request not found")
        if dr.status == "completed":
            raise HTTPException(status_code=409, detail="Deletion already completed")

        # Scaffold: record what WOULD be deleted
        deleted_types = [
            "call_recordings",
            "call_transcripts",
            "patient_record",
            "appointment_history",
        ]
        dr.status = "completed"
        dr.data_types_deleted = json.dumps(deleted_types)
        dr.completed_at = datetime.utcnow()

        session.add(dr)
        session.commit()
        session.refresh(dr)
        logger.info("Deletion executed: id=%s clinic=%s types=%s", dr.id, dr.clinic_id, deleted_types)
        return {
            "ok": True,
            "request_id": dr.id,
            "status": dr.status,
            "data_types_deleted": deleted_types,
            "note": "Scaffold — wire to actual data purge in production",
        }
