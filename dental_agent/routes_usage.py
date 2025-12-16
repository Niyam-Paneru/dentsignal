"""
routes_usage.py - Usage Tracking API Routes

Endpoints for tracking and viewing clinic usage/billing.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from db import (
    get_session,
    get_monthly_summary,
    get_usage_records,
    record_usage,
    finalize_monthly_billing,
    get_current_billing_month,
    UsageType,
    UsageRecord,
    MonthlyUsageSummary,
)


router = APIRouter(prefix="/api/usage", tags=["Usage Tracking"])


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class UsageRecordResponse(BaseModel):
    """Response model for a usage record."""
    id: int
    clinic_id: int
    usage_type: str
    quantity: float
    reference_id: Optional[str]
    reference_type: Optional[str]
    billing_month: str
    unit_cost: float
    total_cost: float
    created_at: datetime

    class Config:
        from_attributes = True


class UsageSummaryResponse(BaseModel):
    """Response model for monthly usage summary."""
    clinic_id: int
    billing_month: str
    
    # Voice minutes
    total_voice_minutes: float
    inbound_minutes: float
    outbound_minutes: float
    
    # SMS
    sms_sent_count: int
    sms_received_count: int
    
    # AI usage
    ai_tokens_used: int
    
    # Billing
    included_minutes: int
    overage_minutes: int
    overage_rate: float
    base_cost: float
    overage_cost: float
    total_cost: float
    
    # Status
    is_finalized: bool
    usage_percentage: float  # Percentage of included minutes used

    class Config:
        from_attributes = True


class RecordUsageRequest(BaseModel):
    """Request model for recording usage."""
    usage_type: str  # One of UsageType values
    quantity: float
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class UsageStatsResponse(BaseModel):
    """Quick stats for dashboard display."""
    current_month: str
    total_minutes_used: float
    included_minutes: int
    remaining_minutes: float
    overage_minutes: int
    estimated_overage_cost: float
    daily_average_minutes: float
    projected_month_end_minutes: float


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/{clinic_id}/summary", response_model=UsageSummaryResponse)
def get_usage_summary(
    clinic_id: int,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
):
    """
    Get usage summary for a clinic for a specific month.
    
    Defaults to current month if no month specified.
    """
    with get_session() as session:
        summary = get_monthly_summary(session, clinic_id, month)
        
        if not summary:
            # Return empty summary
            billing_month = month or get_current_billing_month()
            return UsageSummaryResponse(
                clinic_id=clinic_id,
                billing_month=billing_month,
                total_voice_minutes=0,
                inbound_minutes=0,
                outbound_minutes=0,
                sms_sent_count=0,
                sms_received_count=0,
                ai_tokens_used=0,
                included_minutes=2000,
                overage_minutes=0,
                overage_rate=0.05,
                base_cost=0,
                overage_cost=0,
                total_cost=0,
                is_finalized=False,
                usage_percentage=0,
            )
        
        # Calculate usage percentage
        total_minutes = summary.total_voice_seconds / 60
        usage_pct = (total_minutes / summary.included_minutes * 100) if summary.included_minutes > 0 else 0
        
        return UsageSummaryResponse(
            clinic_id=summary.clinic_id,
            billing_month=summary.billing_month,
            total_voice_minutes=summary.total_voice_seconds / 60,
            inbound_minutes=summary.inbound_seconds / 60,
            outbound_minutes=summary.outbound_seconds / 60,
            sms_sent_count=summary.sms_sent_count,
            sms_received_count=summary.sms_received_count,
            ai_tokens_used=summary.ai_tokens_used,
            included_minutes=summary.included_minutes,
            overage_minutes=summary.overage_minutes,
            overage_rate=summary.overage_rate,
            base_cost=summary.base_cost,
            overage_cost=summary.overage_cost,
            total_cost=summary.total_cost,
            is_finalized=summary.is_finalized,
            usage_percentage=min(usage_pct, 100),
        )


@router.get("/{clinic_id}/stats", response_model=UsageStatsResponse)
def get_usage_stats(clinic_id: int):
    """
    Get quick usage stats for dashboard display.
    
    Includes current usage, remaining minutes, and projections.
    """
    billing_month = get_current_billing_month()
    
    with get_session() as session:
        summary = get_monthly_summary(session, clinic_id, billing_month)
        
        if not summary:
            return UsageStatsResponse(
                current_month=billing_month,
                total_minutes_used=0,
                included_minutes=2000,
                remaining_minutes=2000,
                overage_minutes=0,
                estimated_overage_cost=0,
                daily_average_minutes=0,
                projected_month_end_minutes=0,
            )
        
        # Calculate stats
        total_minutes = summary.total_voice_seconds / 60
        remaining = max(0, summary.included_minutes - total_minutes)
        
        # Calculate daily average and projection
        now = datetime.utcnow()
        days_passed = now.day
        daily_avg = total_minutes / days_passed if days_passed > 0 else 0
        
        # Days in month (approximate)
        days_in_month = 30
        projected = daily_avg * days_in_month
        projected_overage = max(0, projected - summary.included_minutes)
        
        return UsageStatsResponse(
            current_month=billing_month,
            total_minutes_used=total_minutes,
            included_minutes=summary.included_minutes,
            remaining_minutes=remaining,
            overage_minutes=summary.overage_minutes,
            estimated_overage_cost=summary.overage_cost,
            daily_average_minutes=round(daily_avg, 1),
            projected_month_end_minutes=round(projected, 0),
        )


@router.get("/{clinic_id}/records", response_model=list[UsageRecordResponse])
def get_clinic_usage_records(
    clinic_id: int,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    usage_type: Optional[str] = Query(None, description="Filter by usage type"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get detailed usage records for a clinic.
    """
    with get_session() as session:
        # Parse usage type if provided
        type_filter = None
        if usage_type:
            try:
                type_filter = UsageType(usage_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid usage_type: {usage_type}. Valid values: {[t.value for t in UsageType]}"
                )
        
        records = get_usage_records(
            session,
            clinic_id,
            billing_month=month,
            usage_type=type_filter,
            limit=limit,
        )
        
        return [
            UsageRecordResponse(
                id=r.id,
                clinic_id=r.clinic_id,
                usage_type=r.usage_type.value,
                quantity=r.quantity,
                reference_id=r.reference_id,
                reference_type=r.reference_type,
                billing_month=r.billing_month,
                unit_cost=r.unit_cost,
                total_cost=r.total_cost,
                created_at=r.created_at,
            )
            for r in records
        ]


@router.post("/{clinic_id}/record", response_model=UsageRecordResponse)
def record_clinic_usage(
    clinic_id: int,
    request: RecordUsageRequest,
):
    """
    Record a usage event for a clinic.
    
    This is typically called automatically by the voice agent,
    but can also be used for manual adjustments.
    """
    try:
        usage_type = UsageType(request.usage_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid usage_type: {request.usage_type}. Valid values: {[t.value for t in UsageType]}"
        )
    
    with get_session() as session:
        record = record_usage(
            session,
            clinic_id=clinic_id,
            usage_type=usage_type,
            quantity=request.quantity,
            reference_id=request.reference_id,
            reference_type=request.reference_type,
        )
        
        return UsageRecordResponse(
            id=record.id,
            clinic_id=record.clinic_id,
            usage_type=record.usage_type.value,
            quantity=record.quantity,
            reference_id=record.reference_id,
            reference_type=record.reference_type,
            billing_month=record.billing_month,
            unit_cost=record.unit_cost,
            total_cost=record.total_cost,
            created_at=record.created_at,
        )


@router.post("/{clinic_id}/finalize/{month}")
def finalize_month_billing(
    clinic_id: int,
    month: str,
):
    """
    Finalize billing for a specific month.
    
    This marks the month as closed and prevents further updates.
    Should be called at the end of the billing cycle.
    """
    with get_session() as session:
        summary = finalize_monthly_billing(session, clinic_id, month)
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"No usage summary found for clinic {clinic_id} in {month}"
            )
        
        return {
            "status": "finalized",
            "clinic_id": clinic_id,
            "billing_month": month,
            "total_cost": summary.total_cost,
            "finalized_at": summary.finalized_at,
        }


@router.get("/{clinic_id}/history")
def get_usage_history(
    clinic_id: int,
    months: int = Query(6, ge=1, le=24, description="Number of months to fetch"),
):
    """
    Get usage history for the past N months.
    
    Returns monthly summaries for charting/trends.
    """
    from sqlmodel import select
    
    with get_session() as session:
        statement = (
            select(MonthlyUsageSummary)
            .where(MonthlyUsageSummary.clinic_id == clinic_id)
            .order_by(MonthlyUsageSummary.billing_month.desc())
            .limit(months)
        )
        summaries = list(session.exec(statement).all())
        
        return [
            {
                "billing_month": s.billing_month,
                "total_minutes": s.total_voice_seconds / 60,
                "inbound_minutes": s.inbound_seconds / 60,
                "outbound_minutes": s.outbound_seconds / 60,
                "sms_count": s.sms_sent_count + s.sms_received_count,
                "overage_minutes": s.overage_minutes,
                "total_cost": s.total_cost,
                "is_finalized": s.is_finalized,
            }
            for s in summaries
        ]
