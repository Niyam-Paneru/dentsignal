"""
dnc_service.py — Do-Not-Call Registry Service (AG-9)

Centralised helpers for checking, adding and removing phone numbers
from the Do-Not-Call list.  Every outbound contact path MUST call
``is_dnc()`` before dialling or sending SMS.

Usage::

    from dnc_service import is_dnc, add_to_dnc, filter_leads_by_dnc

    # Single check
    if is_dnc(session, "+15551234567", clinic_id=1):
        ...

    # Bulk filter (upload path)
    clean, blocked = filter_leads_by_dnc(session, leads_data, clinic_id=1)
"""

import logging
from datetime import datetime
from typing import Optional, Sequence

from sqlmodel import Session, select

try:
    from dental_agent.db import DoNotCall, DNCReason
    from dental_agent.encryption import phi_hash
    from dental_agent.utils import normalize_phone
except ImportError:
    from db import DoNotCall, DNCReason
    from encryption import phi_hash
    from utils import normalize_phone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core look-up
# ---------------------------------------------------------------------------

def is_dnc(session: Session, phone: str, clinic_id: Optional[int] = None) -> bool:
    """
    Check whether *phone* is on the Do-Not-Call list.

    Checks both the clinic-specific list and the global list (clinic_id=NULL).

    Args:
        session:   Active DB session.
        phone:     Phone number (any format — normalised internally).
        clinic_id: If provided, also checks the clinic-specific DNC entries.

    Returns:
        ``True`` if the number is blocked.
    """
    normalized = normalize_phone(phone) if phone else None
    if not normalized:
        return False

    h = phi_hash(normalized)

    # Build query: active entries matching the phone hash
    stmt = (
        select(DoNotCall.id)
        .where(DoNotCall.phone_hash == h)
        .where(DoNotCall.is_active == True)  # noqa: E712
    )

    if clinic_id is not None:
        # Match global (clinic_id IS NULL) OR this clinic
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(DoNotCall.clinic_id == clinic_id, DoNotCall.clinic_id == None)  # noqa: E711
        )

    return session.exec(stmt).first() is not None


# ---------------------------------------------------------------------------
# Bulk filter helper (for upload paths)
# ---------------------------------------------------------------------------

def filter_leads_by_dnc(
    session: Session,
    leads_data: list[dict],
    clinic_id: Optional[int] = None,
) -> tuple[list[dict], int]:
    """
    Remove DNC numbers from a list of lead dicts.

    Args:
        session:    Active DB session.
        leads_data: List of lead dicts (must contain ``"phone"`` key).
        clinic_id:  Clinic to check against.

    Returns:
        (clean_leads, blocked_count)
    """
    if not leads_data:
        return leads_data, 0

    # Pre-compute the set of active DNC hashes for this clinic (batch query)
    stmt = (
        select(DoNotCall.phone_hash)
        .where(DoNotCall.is_active == True)  # noqa: E712
    )
    if clinic_id is not None:
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(DoNotCall.clinic_id == clinic_id, DoNotCall.clinic_id == None)  # noqa: E711
        )

    dnc_hashes: set[str] = {row for row in session.exec(stmt).all()}

    clean: list[dict] = []
    blocked = 0

    for lead in leads_data:
        phone = lead.get("phone", "")
        normalized = normalize_phone(phone) if phone else None
        if normalized and phi_hash(normalized) in dnc_hashes:
            blocked += 1
            logger.info(f"DNC filter: blocked lead phone ***{normalized[-4:]}")
        else:
            clean.append(lead)

    return clean, blocked


# ---------------------------------------------------------------------------
# Add / remove
# ---------------------------------------------------------------------------

def add_to_dnc(
    session: Session,
    phone: str,
    clinic_id: Optional[int] = None,
    reason: DNCReason = DNCReason.ADMIN,
    notes: Optional[str] = None,
    added_by: Optional[str] = None,
) -> DoNotCall:
    """
    Add a phone number to the DNC list.

    If the number already exists (active or inactive), it is re-activated.

    Returns:
        The ``DoNotCall`` row (new or reactivated).
    """
    normalized = normalize_phone(phone)
    if not normalized:
        raise ValueError(f"Invalid phone number: {phone}")

    h = phi_hash(normalized)

    # Check for existing entry (any status)
    existing = session.exec(
        select(DoNotCall)
        .where(DoNotCall.phone_hash == h)
        .where(
            DoNotCall.clinic_id == clinic_id
            if clinic_id is not None
            else DoNotCall.clinic_id == None  # noqa: E711
        )
    ).first()

    if existing:
        existing.is_active = True
        existing.removed_at = None
        existing.reason = reason
        existing.notes = notes
        existing.added_by = added_by
        session.add(existing)
        logger.info(f"DNC reactivated: ***{normalized[-4:]} clinic={clinic_id}")
        return existing

    entry = DoNotCall(
        clinic_id=clinic_id,
        phone=normalized,
        reason=reason,
        notes=notes,
        added_by=added_by,
    )
    session.add(entry)
    logger.info(f"DNC added: ***{normalized[-4:]} clinic={clinic_id} reason={reason.value}")
    return entry


def remove_from_dnc(
    session: Session,
    phone: str,
    clinic_id: Optional[int] = None,
) -> bool:
    """
    Soft-remove a phone number from the DNC list.

    Returns:
        ``True`` if a matching entry was found and deactivated.
    """
    normalized = normalize_phone(phone)
    if not normalized:
        return False

    h = phi_hash(normalized)

    stmt = (
        select(DoNotCall)
        .where(DoNotCall.phone_hash == h)
        .where(DoNotCall.is_active == True)  # noqa: E712
    )
    if clinic_id is not None:
        stmt = stmt.where(DoNotCall.clinic_id == clinic_id)

    entry = session.exec(stmt).first()
    if entry:
        entry.is_active = False
        entry.removed_at = datetime.utcnow()
        session.add(entry)
        logger.info(f"DNC removed: ***{normalized[-4:]} clinic={clinic_id}")
        return True
    return False


def list_dnc(
    session: Session,
    clinic_id: Optional[int] = None,
    include_inactive: bool = False,
) -> Sequence[DoNotCall]:
    """
    List DNC entries for a clinic (or global).

    Args:
        session:          Active DB session.
        clinic_id:        Filter by clinic. ``None`` = global entries only.
        include_inactive: Include soft-deleted entries.

    Returns:
        Sequence of ``DoNotCall`` rows.
    """
    stmt = select(DoNotCall)
    if clinic_id is not None:
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(DoNotCall.clinic_id == clinic_id, DoNotCall.clinic_id == None)  # noqa: E711
        )
    if not include_inactive:
        stmt = stmt.where(DoNotCall.is_active == True)  # noqa: E712
    stmt = stmt.order_by(DoNotCall.created_at.desc())
    return session.exec(stmt).all()
