"""
call_analytics.py - Post-Call Intelligence & Analytics

Provides:
- Sentiment analysis (was the caller happy/frustrated?)
- Call summary generation (what happened in the call?)
- Quality scoring (how well did the AI handle the call?)
- Intent extraction (what did the caller want?)
- Common questions tracking (what do patients ask most?)

This module transforms raw call data into actionable insights.

USES GEMINI for 50% cost savings on batch analysis!
"""

import os
import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Import AI providers (Gemini for analysis, OpenAI fallback)
try:
    from ai_providers import gemini_generate, ai_complete, TaskType, AIProvider
    USE_MULTI_PROVIDER = True
except ImportError:
    USE_MULTI_PROVIDER = False
    logger.warning("ai_providers not available, using OpenAI only")


class Sentiment(str, Enum):
    """Caller sentiment classification."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    FRUSTRATED = "frustrated"


class CallOutcome(str, Enum):
    """What happened on the call."""
    APPOINTMENT_BOOKED = "appointment_booked"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    QUESTION_ANSWERED = "question_answered"
    TRANSFERRED_TO_HUMAN = "transferred_to_human"
    VOICEMAIL_LEFT = "voicemail_left"
    HUNG_UP = "hung_up"
    WRONG_NUMBER = "wrong_number"
    NO_ANSWER = "no_answer"
    UNKNOWN = "unknown"


@dataclass
class CallAnalysis:
    """Complete analysis of a call."""
    call_id: str
    duration_seconds: int
    
    # Sentiment
    overall_sentiment: Sentiment
    sentiment_score: float  # -1.0 to 1.0
    sentiment_shifts: List[Dict[str, Any]]  # Track mood changes during call
    
    # Outcome
    outcome: CallOutcome
    appointment_details: Optional[Dict[str, Any]]
    
    # Quality
    quality_score: float  # 0-100
    quality_issues: List[str]  # Problems detected
    quality_highlights: List[str]  # Things done well
    
    # Content
    summary: str  # 2-3 sentence summary
    key_topics: List[str]  # Main topics discussed
    patient_questions: List[str]  # Questions the patient asked
    action_items: List[str]  # Follow-up actions needed
    
    # Metadata
    analyzed_at: datetime
    confidence: float  # How confident are we in this analysis


def analyze_call_transcript(
    transcript: str,
    call_id: str,
    duration_seconds: int,
    clinic_name: str = "the clinic",
) -> CallAnalysis:
    """
    Perform comprehensive analysis of a call transcript.
    
    USES GEMINI for 50% cost savings! Falls back to OpenAI if needed.
    
    Args:
        transcript: Full conversation transcript
        call_id: Unique call identifier
        duration_seconds: Call duration
        clinic_name: Name of the dental clinic
    
    Returns:
        CallAnalysis with all insights
    """
    analysis_prompt = f"""Analyze this dental clinic phone call transcript and provide a detailed analysis.

TRANSCRIPT:
{transcript}

Provide your analysis in the following JSON format:
{{
    "overall_sentiment": "very_positive|positive|neutral|negative|very_negative|frustrated",
    "sentiment_score": <float from -1.0 (very negative) to 1.0 (very positive)>,
    "sentiment_shifts": [
        {{"time": "early|middle|late", "sentiment": "...", "reason": "..."}}
    ],
    "outcome": "appointment_booked|appointment_rescheduled|appointment_cancelled|question_answered|transferred_to_human|voicemail_left|hung_up|wrong_number|unknown",
    "appointment_details": {{
        "date": "...",
        "time": "...",
        "type": "...",
        "patient_name": "..."
    }} or null,
    "quality_score": <0-100>,
    "quality_issues": ["list of problems, if any"],
    "quality_highlights": ["things the AI did well"],
    "summary": "2-3 sentence summary of what happened",
    "key_topics": ["main topics discussed"],
    "patient_questions": ["questions the caller asked"],
    "action_items": ["follow-up actions needed"],
    "confidence": <0.0-1.0>
}}

Focus on:
1. Was the patient satisfied? Did they get what they needed?
2. Did the AI handle the call professionally?
3. Were there any awkward moments or misunderstandings?
4. What could have been done better?
5. What follow-up is needed?"""

    system_instruction = "You are an expert call quality analyst for dental clinics. Analyze calls objectively and provide actionable insights. Always respond with valid JSON only, no markdown."
    
    try:
        # Use Gemini for 50% cost savings!
        if USE_MULTI_PROVIDER:
            logger.info(f"Analyzing call {call_id} with Gemini (50% cost savings)")
            response = gemini_generate(
                prompt=analysis_prompt,
                system_instruction=system_instruction,
                json_mode=True,
                temperature=0.3,
            )
            
            if response.success and response.content:
                analysis_data = response.content if isinstance(response.content, dict) else json.loads(response.content)
                logger.info(f"Gemini analysis complete. Cost: ${response.cost_estimate:.6f}")
            else:
                logger.warning(f"Gemini failed: {response.error}, falling back to basic analysis")
                return _basic_analysis(transcript, call_id, duration_seconds)
        else:
            # Fallback to OpenAI if multi-provider not available
            import httpx
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
            
            if not OPENAI_API_KEY:
                return _basic_analysis(transcript, call_id, duration_seconds)
            
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(OPENAI_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                analysis_data = json.loads(result["choices"][0]["message"]["content"])
        
        return CallAnalysis(
            call_id=call_id,
            duration_seconds=duration_seconds,
            overall_sentiment=Sentiment(analysis_data.get("overall_sentiment", "neutral")),
            sentiment_score=float(analysis_data.get("sentiment_score", 0.0)),
            sentiment_shifts=analysis_data.get("sentiment_shifts", []),
            outcome=CallOutcome(analysis_data.get("outcome", "unknown")),
            appointment_details=analysis_data.get("appointment_details"),
            quality_score=float(analysis_data.get("quality_score", 70)),
            quality_issues=analysis_data.get("quality_issues", []),
            quality_highlights=analysis_data.get("quality_highlights", []),
            summary=analysis_data.get("summary", "Call analysis unavailable."),
            key_topics=analysis_data.get("key_topics", []),
            patient_questions=analysis_data.get("patient_questions", []),
            action_items=analysis_data.get("action_items", []),
            analyzed_at=datetime.now(),
            confidence=float(analysis_data.get("confidence", 0.8)),
        )
            
    except Exception as e:
        logger.error(f"Failed to analyze call {call_id}: {e}")
        return _basic_analysis(transcript, call_id, duration_seconds)


def _basic_analysis(
    transcript: str,
    call_id: str,
    duration_seconds: int,
) -> CallAnalysis:
    """
    Fallback analysis when OpenAI is unavailable.
    Uses keyword matching for basic insights.
    """
    transcript_lower = transcript.lower()
    
    # Basic sentiment from keywords
    positive_words = ["thank", "great", "perfect", "wonderful", "appreciate", "happy"]
    negative_words = ["frustrated", "angry", "terrible", "worst", "cancel", "complaint"]
    
    positive_count = sum(1 for w in positive_words if w in transcript_lower)
    negative_count = sum(1 for w in negative_words if w in transcript_lower)
    
    if positive_count > negative_count + 2:
        sentiment = Sentiment.POSITIVE
        sentiment_score = 0.6
    elif negative_count > positive_count + 2:
        sentiment = Sentiment.NEGATIVE
        sentiment_score = -0.6
    else:
        sentiment = Sentiment.NEUTRAL
        sentiment_score = 0.0
    
    # Basic outcome detection
    if any(w in transcript_lower for w in ["booked", "scheduled", "appointment confirmed"]):
        outcome = CallOutcome.APPOINTMENT_BOOKED
    elif any(w in transcript_lower for w in ["cancel", "cancelled"]):
        outcome = CallOutcome.APPOINTMENT_CANCELLED
    elif any(w in transcript_lower for w in ["reschedule", "change"]):
        outcome = CallOutcome.APPOINTMENT_RESCHEDULED
    elif any(w in transcript_lower for w in ["transfer", "speak to"]):
        outcome = CallOutcome.TRANSFERRED_TO_HUMAN
    else:
        outcome = CallOutcome.QUESTION_ANSWERED
    
    return CallAnalysis(
        call_id=call_id,
        duration_seconds=duration_seconds,
        overall_sentiment=sentiment,
        sentiment_score=sentiment_score,
        sentiment_shifts=[],
        outcome=outcome,
        appointment_details=None,
        quality_score=70.0,
        quality_issues=[],
        quality_highlights=["Basic analysis - AI analysis unavailable"],
        summary=f"Call lasted {duration_seconds // 60} minutes. Outcome: {outcome.value}.",
        key_topics=["dental appointment"],
        patient_questions=[],
        action_items=[],
        analyzed_at=datetime.now(),
        confidence=0.3,
    )


def get_call_quality_report(
    call_analyses: List[CallAnalysis],
    period: str = "week",
) -> Dict[str, Any]:
    """
    Generate aggregate quality report for multiple calls.
    
    Args:
        call_analyses: List of analyzed calls
        period: Time period label (day, week, month)
    
    Returns:
        Aggregate statistics and trends
    """
    if not call_analyses:
        return {"error": "No calls to analyze"}
    
    total_calls = len(call_analyses)
    
    # Sentiment breakdown
    sentiment_counts = {}
    for analysis in call_analyses:
        s = analysis.overall_sentiment.value
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
    
    # Outcome breakdown
    outcome_counts = {}
    for analysis in call_analyses:
        o = analysis.outcome.value
        outcome_counts[o] = outcome_counts.get(o, 0) + 1
    
    # Average scores
    avg_quality = sum(a.quality_score for a in call_analyses) / total_calls
    avg_sentiment = sum(a.sentiment_score for a in call_analyses) / total_calls
    avg_duration = sum(a.duration_seconds for a in call_analyses) / total_calls
    
    # Booking rate
    booked = sum(1 for a in call_analyses if a.outcome == CallOutcome.APPOINTMENT_BOOKED)
    booking_rate = (booked / total_calls) * 100
    
    # Common questions
    all_questions = []
    for analysis in call_analyses:
        all_questions.extend(analysis.patient_questions)
    
    # Count question frequency
    question_freq = {}
    for q in all_questions:
        q_normalized = q.lower().strip()
        question_freq[q_normalized] = question_freq.get(q_normalized, 0) + 1
    
    top_questions = sorted(question_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Common issues
    all_issues = []
    for analysis in call_analyses:
        all_issues.extend(analysis.quality_issues)
    
    return {
        "period": period,
        "total_calls": total_calls,
        "avg_quality_score": round(avg_quality, 1),
        "avg_sentiment_score": round(avg_sentiment, 2),
        "avg_duration_seconds": round(avg_duration),
        "booking_rate_percent": round(booking_rate, 1),
        "sentiment_breakdown": sentiment_counts,
        "outcome_breakdown": outcome_counts,
        "top_patient_questions": [{"question": q, "count": c} for q, c in top_questions],
        "common_issues": list(set(all_issues))[:10],
        "appointments_booked": booked,
    }


def extract_appointment_from_transcript(transcript: str) -> Optional[Dict[str, Any]]:
    """
    Extract appointment details from a call transcript.
    
    Returns structured data about any appointment mentioned.
    """
    if not OPENAI_API_KEY:
        return None
    
    try:
        prompt = f"""Extract any appointment details from this dental clinic call transcript.

TRANSCRIPT:
{transcript}

If an appointment was discussed, return JSON:
{{
    "found": true,
    "patient_name": "...",
    "date": "YYYY-MM-DD or relative like 'tomorrow', 'next Monday'",
    "time": "HH:MM AM/PM",
    "appointment_type": "cleaning|checkup|emergency|consultation|procedure|other",
    "notes": "any special notes"
}}

If no appointment was discussed, return:
{{"found": false}}"""

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        with httpx.Client(timeout=15.0) as client:
            response = client.post(OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            data = json.loads(content)
            
            if data.get("found"):
                return data
            return None
            
    except Exception as e:
        logger.error(f"Failed to extract appointment: {e}")
        return None


def generate_call_summary_email(
    analyses: List[CallAnalysis],
    clinic_name: str,
    period: str = "today",
) -> str:
    """
    Generate a daily/weekly email summary of call activity.
    
    Perfect for clinic owners who want to stay informed.
    """
    if not analyses:
        return f"No calls recorded for {clinic_name} {period}."
    
    report = get_call_quality_report(analyses, period)
    
    booked = report["appointments_booked"]
    total = report["total_calls"]
    quality = report["avg_quality_score"]
    
    email = f"""
📊 {clinic_name} - Call Summary for {period.title()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 CALL VOLUME
   Total Calls: {total}
   Avg Duration: {report['avg_duration_seconds'] // 60} min {report['avg_duration_seconds'] % 60} sec

📅 APPOINTMENTS
   Booked: {booked}
   Booking Rate: {report['booking_rate_percent']}%

⭐ QUALITY SCORE
   Average: {quality}/100
   
"""
    
    # Sentiment emoji
    sentiment = report.get("sentiment_breakdown", {})
    if sentiment:
        email += "😊 PATIENT SENTIMENT\n"
        for s, count in sentiment.items():
            emoji = {"very_positive": "😄", "positive": "🙂", "neutral": "😐", "negative": "😕", "very_negative": "😢", "frustrated": "😤"}.get(s, "•")
            email += f"   {emoji} {s.replace('_', ' ').title()}: {count}\n"
        email += "\n"
    
    # Top questions
    questions = report.get("top_patient_questions", [])
    if questions:
        email += "❓ TOP PATIENT QUESTIONS\n"
        for i, q in enumerate(questions[:5], 1):
            email += f"   {i}. {q['question'][:50]}... ({q['count']}x)\n"
        email += "\n"
    
    # Action items from today's calls
    action_items = []
    for a in analyses:
        action_items.extend(a.action_items)
    
    if action_items:
        email += "📋 ACTION ITEMS\n"
        for item in action_items[:5]:
            email += f"   • {item}\n"
        email += "\n"
    
    email += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View full dashboard: [Dashboard Link]

Powered by Dental AI Voice Agent
"""
    
    return email
