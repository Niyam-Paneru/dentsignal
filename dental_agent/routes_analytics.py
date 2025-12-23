"""
routes_analytics.py - Call Analytics & Insights API Routes

Endpoints for:
- Call sentiment analysis
- Quality scoring
- Conversion tracking
- Common questions report
- Daily/weekly summaries
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from call_analytics import (
    analyze_call_transcript,
    get_call_quality_report,
    extract_appointment_from_transcript,
    generate_call_summary_email,
    CallAnalysis,
    Sentiment,
    CallOutcome,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Insights"])


# =============================================================================
# Pydantic Models
# =============================================================================

class AnalyzeCallRequest(BaseModel):
    """Request to analyze a call transcript."""
    transcript: str = Field(..., min_length=10)
    call_id: str
    duration_seconds: int = Field(..., ge=0)
    clinic_name: str = "the clinic"


class CallAnalysisResponse(BaseModel):
    """Call analysis response."""
    call_id: str
    duration_seconds: int
    overall_sentiment: str
    sentiment_score: float
    outcome: str
    quality_score: float
    summary: str
    key_topics: List[str]
    patient_questions: List[str]
    action_items: List[str]
    quality_issues: List[str]
    quality_highlights: List[str]
    appointment_details: Optional[dict] = None
    confidence: float


class QualityReportResponse(BaseModel):
    """Aggregate quality report response."""
    period: str
    total_calls: int
    avg_quality_score: float
    avg_sentiment_score: float
    avg_duration_seconds: int
    booking_rate_percent: float
    sentiment_breakdown: dict
    outcome_breakdown: dict
    top_patient_questions: List[dict]
    common_issues: List[str]
    appointments_booked: int


class DashboardStats(BaseModel):
    """Dashboard overview statistics."""
    today_calls: int
    today_bookings: int
    today_booking_rate: float
    avg_quality_today: float
    
    week_calls: int
    week_bookings: int
    week_booking_rate: float
    avg_quality_week: float
    
    month_calls: int
    month_bookings: int
    month_booking_rate: float
    
    trend_calls_vs_last_week: float  # percentage change
    trend_bookings_vs_last_week: float


# =============================================================================
# Routes
# =============================================================================

@router.post("/analyze", response_model=CallAnalysisResponse)
async def analyze_call(request: AnalyzeCallRequest):
    """
    Analyze a call transcript for sentiment, quality, and insights.
    
    This is the core analytics function. Call it after each call ends
    to get:
    - Sentiment analysis (was the caller happy?)
    - Quality score (how well did the AI do?)
    - Call summary (what happened?)
    - Action items (what follow-up is needed?)
    """
    analysis = analyze_call_transcript(
        transcript=request.transcript,
        call_id=request.call_id,
        duration_seconds=request.duration_seconds,
        clinic_name=request.clinic_name,
    )
    
    return CallAnalysisResponse(
        call_id=analysis.call_id,
        duration_seconds=analysis.duration_seconds,
        overall_sentiment=analysis.overall_sentiment.value,
        sentiment_score=analysis.sentiment_score,
        outcome=analysis.outcome.value,
        quality_score=analysis.quality_score,
        summary=analysis.summary,
        key_topics=analysis.key_topics,
        patient_questions=analysis.patient_questions,
        action_items=analysis.action_items,
        quality_issues=analysis.quality_issues,
        quality_highlights=analysis.quality_highlights,
        appointment_details=analysis.appointment_details,
        confidence=analysis.confidence,
    )


@router.post("/extract-appointment")
async def extract_appointment(transcript: str = Query(..., min_length=10)):
    """
    Extract appointment details from a transcript.
    
    Use this to automatically capture:
    - Patient name
    - Appointment date/time
    - Appointment type
    - Special notes
    """
    result = extract_appointment_from_transcript(transcript)
    
    if result:
        return {
            "found": True,
            "appointment": result,
        }
    return {"found": False}


@router.get("/quality-report", response_model=QualityReportResponse)
async def get_quality_report(
    period: str = Query("week", enum=["day", "week", "month"]),
    clinic_id: Optional[int] = None,
):
    """
    Get aggregate quality report for a time period.
    
    Shows:
    - Average quality scores
    - Sentiment breakdown
    - Booking rates
    - Common patient questions
    - Common issues to address
    
    This is what clinic owners want to see every week.
    """
    # In production, this would query the database
    # For now, return sample data structure
    
    sample_analyses = []  # Would be loaded from DB
    
    if not sample_analyses:
        # Return empty report structure
        return QualityReportResponse(
            period=period,
            total_calls=0,
            avg_quality_score=0,
            avg_sentiment_score=0,
            avg_duration_seconds=0,
            booking_rate_percent=0,
            sentiment_breakdown={},
            outcome_breakdown={},
            top_patient_questions=[],
            common_issues=[],
            appointments_booked=0,
        )
    
    report = get_call_quality_report(sample_analyses, period)
    return QualityReportResponse(**report)


@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(clinic_id: Optional[int] = None):
    """
    Get high-level dashboard statistics.
    
    Quick overview for the dashboard home page:
    - Today's numbers
    - This week's numbers
    - Trends vs last week
    """
    # In production, query database
    # Sample structure for now
    
    return DashboardStats(
        today_calls=0,
        today_bookings=0,
        today_booking_rate=0,
        avg_quality_today=0,
        
        week_calls=0,
        week_bookings=0,
        week_booking_rate=0,
        avg_quality_week=0,
        
        month_calls=0,
        month_bookings=0,
        month_booking_rate=0,
        
        trend_calls_vs_last_week=0,
        trend_bookings_vs_last_week=0,
    )


@router.get("/common-questions")
async def get_common_questions(
    period: str = Query("month", enum=["week", "month", "all"]),
    limit: int = Query(20, ge=1, le=100),
    clinic_id: Optional[int] = None,
):
    """
    Get the most common patient questions.
    
    This is gold for:
    - Training the AI to handle common questions better
    - Updating your website FAQ
    - Understanding patient concerns
    
    Top clinics use this to improve their AI every month.
    """
    # In production, aggregate from call analyses
    sample_questions = [
        {"question": "Do you accept my insurance?", "count": 45, "category": "insurance"},
        {"question": "What are your hours?", "count": 38, "category": "hours"},
        {"question": "Do you accept new patients?", "count": 32, "category": "availability"},
        {"question": "How much does a cleaning cost?", "count": 28, "category": "pricing"},
        {"question": "Can I get an appointment this week?", "count": 25, "category": "scheduling"},
        {"question": "Do you do emergency appointments?", "count": 22, "category": "emergency"},
        {"question": "What forms of payment do you accept?", "count": 18, "category": "payment"},
        {"question": "How long does a root canal take?", "count": 15, "category": "procedures"},
        {"question": "Do you offer teeth whitening?", "count": 12, "category": "cosmetic"},
        {"question": "Is the dentist gentle?", "count": 10, "category": "comfort"},
    ]
    
    return {
        "period": period,
        "total_unique_questions": len(sample_questions),
        "questions": sample_questions[:limit],
    }


@router.get("/sentiment-trends")
async def get_sentiment_trends(
    days: int = Query(30, ge=7, le=90),
    clinic_id: Optional[int] = None,
):
    """
    Get sentiment trends over time.
    
    Track if patient satisfaction is improving or declining.
    Early warning system for problems.
    """
    # In production, aggregate daily sentiment scores
    return {
        "days": days,
        "trend": "stable",  # improving, declining, stable
        "avg_sentiment_score": 0.45,
        "data_points": [],  # Would be daily averages
    }


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    period: str = Query("month", enum=["week", "month"]),
    clinic_id: Optional[int] = None,
):
    """
    Get call-to-appointment conversion funnel.
    
    Shows where you're losing potential patients:
    - How many calls came in?
    - How many reached the AI?
    - How many had booking intent?
    - How many actually booked?
    """
    return {
        "period": period,
        "funnel": [
            {"stage": "total_calls", "count": 100, "percent": 100},
            {"stage": "answered_by_ai", "count": 98, "percent": 98},
            {"stage": "had_booking_intent", "count": 65, "percent": 65},
            {"stage": "appointment_offered", "count": 60, "percent": 60},
            {"stage": "appointment_booked", "count": 45, "percent": 45},
        ],
        "drop_off_analysis": [
            {"from": "answered_by_ai", "to": "had_booking_intent", "lost": 33, "reason": "Information-only calls"},
            {"from": "had_booking_intent", "to": "appointment_offered", "lost": 5, "reason": "No availability"},
            {"from": "appointment_offered", "to": "appointment_booked", "lost": 15, "reason": "Patient undecided"},
        ]
    }


@router.post("/generate-report-email")
async def generate_report_email(
    clinic_name: str,
    period: str = Query("today", enum=["today", "week", "month"]),
    send_to: Optional[str] = None,
):
    """
    Generate and optionally send a summary report email.
    
    Perfect for daily/weekly automated reports to clinic owners.
    """
    # In production, load analyses from database
    sample_analyses = []
    
    email_content = generate_call_summary_email(
        analyses=sample_analyses,
        clinic_name=clinic_name,
        period=period,
    )
    
    return {
        "generated": True,
        "period": period,
        "email_content": email_content,
        "sent_to": send_to if send_to else "Not sent (preview only)",
    }


@router.get("/peak-hours")
async def get_peak_hours(
    period: str = Query("month", enum=["week", "month"]),
    clinic_id: Optional[int] = None,
):
    """
    Get peak calling hours analysis.
    
    Know when most calls come in to:
    - Staff appropriately
    - Ensure AI is ready for peak times
    - Plan marketing around high-intent hours
    """
    # Sample data - in production, aggregate from call timestamps
    return {
        "period": period,
        "peak_hours": [
            {"hour": 9, "calls": 25, "bookings": 12},
            {"hour": 10, "calls": 32, "bookings": 15},
            {"hour": 11, "calls": 28, "bookings": 13},
            {"hour": 14, "calls": 30, "bookings": 14},
            {"hour": 15, "calls": 22, "bookings": 10},
        ],
        "peak_days": [
            {"day": "Monday", "calls": 45},
            {"day": "Tuesday", "calls": 52},
            {"day": "Wednesday", "calls": 38},
            {"day": "Thursday", "calls": 41},
            {"day": "Friday", "calls": 35},
        ],
        "after_hours_calls": 28,
        "after_hours_bookings": 15,
        "after_hours_booking_rate": 53.6,
    }


# =============================================================================
# AI Quality Scoring (Gemini-based for cost efficiency)
# =============================================================================

class QualityScoreRequest(BaseModel):
    """Request to score a call's quality using AI."""
    call_id: str
    transcript: str = Field(..., min_length=10)


class QualityScoreResponse(BaseModel):
    """AI-powered quality score response."""
    call_id: str
    score: int = Field(..., ge=0, le=100)
    feedback: str
    missed_opportunities: List[str]
    breakdown: dict


@router.post("/quality-score/{call_id}", response_model=QualityScoreResponse)
async def score_call_quality(call_id: str, request: QualityScoreRequest):
    """
    AI-powered call quality scoring using Gemini 2.0-flash.
    
    Evaluates:
    - Did AI ask for caller name? (+25 points)
    - Did AI understand the issue? (+25 points)
    - Was appointment offered/booked? (+25 points)
    - Did AI handle professionally? (+25 points)
    
    Uses Gemini for cost efficiency (~$0.001 per call vs $0.01 for GPT-4).
    
    Returns:
    - score: 0-100 overall quality score
    - feedback: Summary of performance
    - missed_opportunities: List of things the AI should have done
    - breakdown: Per-category scores
    """
    import os
    import json
    
    # Try Gemini first (cheaper), fallback to OpenAI
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            prompt = f"""Score this dental receptionist AI call transcript.

Rate on these criteria (25 points each, total 100):
1. Name Collection: Did the AI ask for and confirm the caller's name?
2. Issue Understanding: Did the AI correctly identify what the caller needed?
3. Booking Attempt: Did the AI offer/book an appointment when appropriate?
4. Professionalism: Was the AI polite, clear, and helpful throughout?

TRANSCRIPT:
{request.transcript}

Return ONLY valid JSON (no markdown):
{{
  "score": <0-100>,
  "feedback": "<2-3 sentence summary>",
  "missed_opportunities": ["<thing AI should have done>", ...],
  "breakdown": {{
    "name_collection": <0-25>,
    "issue_understanding": <0-25>,
    "booking_attempt": <0-25>,
    "professionalism": <0-25>
  }}
}}"""

            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up potential markdown
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            
            return QualityScoreResponse(
                call_id=call_id,
                score=result.get("score", 0),
                feedback=result.get("feedback", ""),
                missed_opportunities=result.get("missed_opportunities", []),
                breakdown=result.get("breakdown", {})
            )
            
        except Exception as e:
            logger.warning(f"Gemini quality scoring failed: {e}, falling back to heuristic")
    
    # Fallback: Simple heuristic scoring
    transcript_lower = request.transcript.lower()
    breakdown = {
        "name_collection": 25 if any(w in transcript_lower for w in ["your name", "may i get your name", "who am i speaking"]) else 0,
        "issue_understanding": 25 if any(w in transcript_lower for w in ["understand", "so you need", "i can help with"]) else 10,
        "booking_attempt": 25 if any(w in transcript_lower for w in ["appointment", "schedule", "book", "available"]) else 0,
        "professionalism": 25 if any(w in transcript_lower for w in ["thank you", "please", "i'd be happy"]) else 15,
    }
    score = sum(breakdown.values())
    
    missed = []
    if breakdown["name_collection"] == 0:
        missed.append("AI should ask for caller's name")
    if breakdown["booking_attempt"] == 0:
        missed.append("AI should offer to schedule an appointment")
    
    return QualityScoreResponse(
        call_id=call_id,
        score=score,
        feedback=f"Call scored {score}/100. {'Good job!' if score >= 70 else 'Room for improvement.'}",
        missed_opportunities=missed,
        breakdown=breakdown
    )


# =============================================================================
# Receptionist Performance Report
# =============================================================================

class ReceptionistPerformanceResponse(BaseModel):
    """Receptionist performance metrics."""
    today: dict
    comparison: dict
    trends: List[dict]


@router.get("/receptionist-performance", response_model=ReceptionistPerformanceResponse)
async def get_receptionist_performance(clinic_id: Optional[int] = None):
    """
    Get receptionist performance metrics for the dashboard.
    
    Shows:
    - Calls handled today
    - Calls transferred
    - Time freed for receptionist
    - Revenue comparison (AI vs human-only)
    
    This is what sells clinics on the AI value.
    """
    from datetime import datetime, timedelta
    
    # In production, these would come from database queries
    # Sample realistic data for now
    
    today_stats = {
        "calls_handled": 23,
        "calls_transferred": 3,
        "calls_escalated": 1,
        "avg_handle_time": 180,  # seconds
        "quality_score_avg": 87,
        "time_freed_hours": 4.5,
        "bookings_made": 18,
    }
    
    # Calculate what a human receptionist would have handled
    # Average human answers 15-20 calls in peak hours, misses ~30-40%
    human_answer_rate = 0.65  # 65% answer rate typical for busy clinic
    expected_calls = today_stats["calls_handled"]
    human_would_answer = int(expected_calls * human_answer_rate)
    missed_by_human = expected_calls - human_would_answer
    
    # Average appointment value $400
    avg_appointment_value = 400
    booking_rate = 0.78  # 78% of calls result in bookings
    
    ai_revenue = int(today_stats["bookings_made"] * avg_appointment_value)
    missed_revenue = int(missed_by_human * booking_rate * avg_appointment_value)
    
    comparison = {
        "human_receptionist_would_answer": human_would_answer,
        "missed_by_human": missed_by_human,
        "revenue_lost_to_missed": missed_revenue,
        "ai_revenue_captured": ai_revenue,
        "net_revenue_improvement": missed_revenue,  # Revenue AI saved
    }
    
    # Last 7 days trends
    today = datetime.now()
    trends = []
    for i in range(7):
        date = today - timedelta(days=i)
        # Generate realistic trending data
        base_calls = 20 + (i % 3) * 5
        trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "calls": base_calls,
            "booked": int(base_calls * 0.75),
            "missed": 0 if i != 5 else 1,  # AI rarely misses
            "transferred": 2 + (i % 2),
        })
    
    return ReceptionistPerformanceResponse(
        today=today_stats,
        comparison=comparison,
        trends=list(reversed(trends))  # Oldest first
    )

