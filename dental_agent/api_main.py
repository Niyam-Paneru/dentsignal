"""
api_main.py - FastAPI Application for AI Voice Agent System

A runnable FastAPI backend for the dental clinic AI Voice Agent.

.env.example:
'''
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET=changeme
DEEPGRAM_API_KEY=
TELEPHONY_MODE=SIMULATED
TWILIO_SID=
TWILIO_TOKEN=
TWILIO_NUMBER=

SENTRY_DSN=
'''

Run with: uvicorn api_main:app --reload
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Initialize Sentry BEFORE app creation
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", "https://cec3389377af0692871ea20fa400a2ae@o4510760542470144.ingest.us.sentry.io/4510760593129472"),
    integrations=[
        FastApiIntegration(),
        StarletteIntegration(),
    ],
    # Capture 10% of transactions for performance monitoring
    traces_sample_rate=0.1,
    # Send PII like request headers for debugging
    send_default_pii=True,
    # Set environment
    environment=os.getenv("ENVIRONMENT", "development"),
    # Release tracking
    release=os.getenv("RELEASE_VERSION", "dentsignal-api@1.0.0"),
)

import csv
import io
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import Optional, Any

import jwt
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import Session, select

from db import (
    create_db,
    get_session,
    User,
    Client,
    UploadBatch,
    Lead,
    Call,
    CallResult,
    CallStatus,
    CallResultType,
    enqueue_calls_for_batch,
)
from utils import (
    normalize_phone,
    is_valid_phone,
    mask_phone,
    mask_email,
    sanitize_string,
    sanitize_filename,
    validate_csv_upload,
    setup_logger,
    PIIMaskingFilter,
    APIError,
)
from rate_limiter import RateLimitMiddleware

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme-insecure-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1

# Logging setup with rotation and PII masking
LOG_FILE = os.getenv("LOG_FILE", "logs/api.log")
os.makedirs(os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else "logs", exist_ok=True)

logger = setup_logger(
    name=__name__,
    log_file=LOG_FILE,
    level=logging.INFO,
    max_bytes=10 * 1024 * 1024,  # 10 MB
    backup_count=5,
    mask_pii=True,
)

# -----------------------------------------------------------------------------
# FastAPI App
# -----------------------------------------------------------------------------

app = FastAPI(
    title="DentSignal API",
    description="Backend API for DentSignal AI Voice Agent",
    version="1.0.0",
)

# CORS middleware (allow all origins for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (skips Twilio webhooks and health checks)
app.add_middleware(RateLimitMiddleware)

# Include existing routers (Celery-based call routes)
try:
    from dental_agent.routes_calls import router as calls_router
    from dental_agent.routes_twilio import router as twilio_router
    from dental_agent.routes_inbound import router as inbound_router
    from dental_agent.routes_admin import router as admin_router
    from dental_agent.routes_sms import router as sms_router
    from dental_agent.routes_analytics import router as analytics_router
    from dental_agent.routes_superadmin import router as superadmin_router
    from dental_agent.routes_usage import router as usage_router
    from dental_agent.routes_calendar import router as calendar_router
    from dental_agent.routes_transfer import router as transfer_router
    from dental_agent.routes_recall import router as recall_router
except ImportError:
    from routes_calls import router as calls_router
    from routes_twilio import router as twilio_router
    from routes_inbound import router as inbound_router
    from routes_admin import router as admin_router
    from routes_sms import router as sms_router
    from routes_analytics import router as analytics_router
    from routes_superadmin import router as superadmin_router
    from routes_usage import router as usage_router
    from routes_calendar import router as calendar_router
    from routes_transfer import router as transfer_router
    from routes_recall import router as recall_router

app.include_router(calls_router, tags=["Calls & Batches"])
app.include_router(twilio_router)  # Twilio webhooks (outbound)
app.include_router(inbound_router)  # Inbound voice agent routes
app.include_router(admin_router)  # Clinic management API
app.include_router(sms_router)  # SMS & patient engagement
app.include_router(analytics_router)  # Call analytics & insights
app.include_router(superadmin_router)  # Super admin dashboard
app.include_router(usage_router)  # Usage tracking & billing
app.include_router(calendar_router)  # Calendar & appointment scheduling
app.include_router(transfer_router)  # Call takeover/transfer
app.include_router(recall_router)  # Proactive recall outreach


# -----------------------------------------------------------------------------
# Startup Event
# -----------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    logger.info(f"Initializing database: {DATABASE_URL}")
    logger.info("Sentry initialized for error monitoring")
    create_db(DATABASE_URL)
    
    # Create demo user and client if they don't exist
    with get_session() as session:
        # Check for existing admin user
        existing = session.exec(select(User).where(User.email == "admin@dental.local")).first()
        if not existing:
            user = User(email="admin@dental.local", password_hash="admin123", is_admin=True)
            session.add(user)
            logger.info("Created demo admin user: admin@dental.local / admin123")
        
        # Check for existing client/clinic
        existing_client = session.exec(select(Client).where(Client.email == "info@sunshine-dental.local")).first()
        if not existing_client:
            # Get Twilio number from environment
            twilio_number = os.getenv("TWILIO_NUMBER", "+19048679643")
            
            client = Client(
                name="Sunshine Dental",
                email="info@sunshine-dental.local",
                timezone="America/New_York",
                agent_name="Sarah",
                agent_voice="aura-asteria-en",
                address="123 Smile Street, Jacksonville, FL 32256",
                phone_display="(904) 867-9643",
                hours="Monday-Friday 8am-5pm, Saturday 9am-1pm",
                services="cleanings, exams, fillings, crowns, whitening, extractions",
                insurance_accepted="Delta Dental, Cigna, Aetna, MetLife, United Healthcare",
                twilio_number=twilio_number,
                custom_instructions="Our office is closed for lunch from 12pm-1pm. For emergencies after hours, patients should go to the ER.",
                monthly_price=199.0,
                is_active=True,
            )
            session.add(client)
            logger.info(f"Created demo clinic: Sunshine Dental with number {twilio_number}")


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------

def get_db():
    """Dependency to get database session."""
    with get_session() as session:
        yield session


def get_current_user(authorization: str = None) -> Optional[dict]:
    """
    Decode JWT token from Authorization header.
    For demo: returns decoded payload or raises 401.
    """
    if not authorization:
        return None
    
    try:
        # Expect "Bearer <token>"
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
# Request/Response Models
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """Login request body."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    token: str


class LeadInput(BaseModel):
    """Single lead input."""
    name: str
    phone: str
    email: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None
    consent: bool = False  # TCPA consent required for PSTN calls

    @field_validator("phone")
    @classmethod
    def phone_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Phone is required")
        # Normalize to E.164 format
        normalized = normalize_phone(v.strip())
        if not normalized:
            raise ValueError(f"Invalid phone number format: {v}")
        return normalized
    
    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name is required")
        # Basic sanitization - remove dangerous characters
        return sanitize_string(v.strip(), max_length=200).replace('&amp;', '&').replace('&lt;', '').replace('&gt;', '')


class LeadsUploadRequest(BaseModel):
    """JSON upload request body."""
    leads: list[LeadInput]


class UploadResponse(BaseModel):
    """Response for lead upload."""
    upload_id: int
    batch_id: int
    queued_count: int
    skipped_no_consent: int = 0  # Leads skipped due to missing consent


class StartCallRequest(BaseModel):
    """n8n webhook request to start a call."""
    batch_id: Optional[int] = None
    lead: LeadInput
    callback_url: Optional[str] = None

class StartCallResponse(BaseModel):
    """Response for start call webhook."""
    call_id: int


class CallStatusUpdate(BaseModel):
    """Request to update call status/result."""
    status: Optional[CallStatus] = None
    result: Optional[CallResultType] = None
    transcript: Optional[str] = None
    booked_slot: Optional[datetime] = None
    notes: Optional[str] = None


class CallStatusResponse(BaseModel):
    """Response for call status update."""
    call_id: int
    status: str
    message: str


class CallResultOutput(BaseModel):
    """Nested call result in response."""
    id: int
    result: str
    transcript: Optional[str]
    booked_slot: Optional[datetime]
    notes: Optional[str]
    created_at: datetime


class CallOutput(BaseModel):
    """Call entry for list response."""
    id: int
    lead_id: int
    batch_id: int
    client_id: int
    status: str
    attempt: int
    created_at: datetime
    updated_at: datetime
    lead_name: Optional[str] = None
    lead_phone: Optional[str] = None
    call_result: Optional[CallResultOutput] = None


class CallListResponse(BaseModel):
    """Paginated list of calls."""
    calls: list[CallOutput]
    total: int
    limit: int
    offset: int


class TwilioWebhookRequest(BaseModel):
    """Twilio webhook payload (simplified)."""
    CallSid: Optional[str] = None
    CallStatus: Optional[str] = None
    From: Optional[str] = None
    To: Optional[str] = None
    # Add more fields as needed


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

# 1) POST /api/auth/login
@app.post("/api/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, session: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    Demo: uses plain text password matching.
    """
    user = session.exec(select(User).where(User.email == request.email)).first()
    
    if not user or user.password_hash != request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "is_admin": user.is_admin,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    logger.info(f"User logged in: {user.email}")
    return LoginResponse(token=token)


# 2a) POST /api/clients/{client_id}/leads (JSON-only endpoint)
@app.post("/api/clients/{client_id}/leads", response_model=UploadResponse)
def upload_leads_json(
    client_id: int,
    body: LeadsUploadRequest,
    allow_no_consent: bool = Query(False, description="Allow leads without consent (test mode only)"),
    session: Session = Depends(get_db),
):
    """
    Upload leads via JSON body (simpler endpoint for API testing).
    
    For PSTN calls, leads MUST have consent=true (TCPA compliance).
    Use allow_no_consent=true only for testing/simulated mode.
    """
    # Verify client exists
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check TELEPHONY_MODE - if TWILIO (real PSTN), enforce consent
    telephony_mode = os.getenv("TELEPHONY_MODE", "SIMULATED")
    require_consent = telephony_mode == "TWILIO" and not allow_no_consent
    
    leads_data = []
    skipped_no_consent = 0
    
    for lead in body.leads:
        lead_dict = lead.model_dump()
        
        # Check consent for PSTN mode
        if require_consent and not lead_dict.get("consent", False):
            skipped_no_consent += 1
            logger.warning(f"Skipping lead without consent: {mask_phone(lead_dict.get('phone', ''))}")
            continue
        
        leads_data.append(lead_dict)
    
    if not leads_data:
        if skipped_no_consent > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"All {skipped_no_consent} leads skipped: consent required for PSTN calls"
            )
        raise HTTPException(status_code=400, detail="No valid leads")
    
    # Create batch
    batch = UploadBatch(client_id=client_id, source="json")
    session.add(batch)
    session.commit()
    session.refresh(batch)
    
    # Create lead rows
    for ld in leads_data:
        lead = Lead(batch_id=batch.id, **ld)
        session.add(lead)
    session.commit()
    
    # Enqueue calls
    queued_count = enqueue_calls_for_batch(session, batch.id, client_id)
    
    logger.info(f"Created batch {batch.id} with {queued_count} queued calls, {skipped_no_consent} skipped (no consent)")
    
    return UploadResponse(
        upload_id=batch.id,
        batch_id=batch.id,
        queued_count=queued_count,
        skipped_no_consent=skipped_no_consent,
    )


# 2b) POST /api/clients/{client_id}/uploads (file upload endpoint)
@app.post("/api/clients/{client_id}/uploads", response_model=UploadResponse)
async def upload_leads(
    client_id: int,
    file: Optional[UploadFile] = File(None),
    leads_json: Optional[LeadsUploadRequest] = None,
    allow_no_consent: bool = Query(False, description="Allow leads without consent (test mode only)"),
    session: Session = Depends(get_db),
):
    """
    Upload leads via CSV file or JSON body.
    Creates UploadBatch, Lead rows, and enqueues Call rows.
    
    For PSTN calls (TELEPHONY_MODE=TWILIO), leads MUST have consent=true.
    Use allow_no_consent=true only for testing/simulated mode.
    """
    # Verify client exists
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check TELEPHONY_MODE - if TWILIO (real PSTN), enforce consent
    telephony_mode = os.getenv("TELEPHONY_MODE", "SIMULATED")
    require_consent = telephony_mode == "TWILIO" and not allow_no_consent
    
    leads_data: list[dict] = []
    skipped_no_consent = 0
    source = "json"
    
    # Parse CSV file if provided
    if file:
        source = "csv"
        
        # Validate file upload
        content = await file.read()
        is_valid, error_msg = validate_csv_upload(
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            size=len(content),
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Sanitize filename for logging
        safe_filename = sanitize_filename(file.filename or "upload.csv")
        logger.info(f"Processing CSV upload: {safe_filename} ({len(content)} bytes)")
        
        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            
            skipped_count = 0
            for row in reader:
                # Validate and normalize phone
                phone = row.get("phone", "").strip()
                normalized_phone = normalize_phone(phone) if phone else None
                
                if not normalized_phone:
                    skipped_count += 1
                    continue  # Skip rows without valid phone
                
                # Sanitize name
                name = row.get("name", "").strip()
                if name:
                    try:
                        name = sanitize_string(name, max_length=200).replace('&amp;', '&').replace('&lt;', '').replace('&gt;', '')
                    except ValueError:
                        skipped_count += 1
                        continue  # Skip rows with dangerous content
                
                leads_data.append({
                    "name": name,
                    "phone": normalized_phone,
                    "email": row.get("email", "").strip() or None,
                    "source_url": row.get("source_url", "").strip() or None,
                    "notes": row.get("notes", "").strip() or None,
                    "consent": row.get("consent", "").strip().lower() in ("true", "yes", "1"),
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")
    
    # Or parse JSON body
    elif leads_json:
        for lead in leads_json.leads:
            leads_data.append(lead.model_dump())
    
    else:
        raise HTTPException(status_code=400, detail="Provide either file or JSON leads")
    
    if not leads_data:
        raise HTTPException(status_code=400, detail="No valid leads with phone numbers")
    
    # Filter leads by consent for PSTN mode
    if require_consent:
        filtered_leads = []
        for ld in leads_data:
            if ld.get("consent", False):
                filtered_leads.append(ld)
            else:
                skipped_no_consent += 1
                logger.warning(f"Skipping lead without consent: {mask_phone(ld.get('phone', ''))}")
        leads_data = filtered_leads
        
        if not leads_data:
            raise HTTPException(
                status_code=400,
                detail=f"All {skipped_no_consent} leads skipped: consent required for PSTN calls"
            )
    
    # Create batch
    batch = UploadBatch(client_id=client_id, source=source)
    session.add(batch)
    session.commit()
    session.refresh(batch)
    
    logger.info(f"Created batch {batch.id} for client {client_id} with source '{source}'")
    
    # Create lead rows
    for ld in leads_data:
        lead = Lead(batch_id=batch.id, **ld)
        session.add(lead)
    session.commit()
    
    logger.info(f"Added {len(leads_data)} leads to batch {batch.id}")
    
    # Enqueue calls
    queued_count = enqueue_calls_for_batch(session, batch.id, client_id)
    logger.info(f"Enqueued {queued_count} calls for batch {batch.id}, {skipped_no_consent} skipped (no consent)")
    
    return UploadResponse(
        upload_id=batch.id,
        batch_id=batch.id,
        queued_count=queued_count,
        skipped_no_consent=skipped_no_consent,
    )


# 3) POST /webhook/n8n/start-call
@app.post("/webhook/n8n/start-call", response_model=StartCallResponse)
def start_call_webhook(
    request: StartCallRequest,
    session: Session = Depends(get_db),
):
    """
    n8n webhook to start a single call.
    Creates Lead if not existing, creates Call row with status 'queued'.
    """
    # Get or create batch
    batch_id = request.batch_id
    client_id = 1  # Default to first client for n8n webhooks
    
    if not batch_id:
        # Create a new batch for this single lead
        batch = UploadBatch(client_id=client_id, source="n8n")
        session.add(batch)
        session.commit()
        session.refresh(batch)
        batch_id = batch.id
        logger.info(f"Created new batch {batch_id} for n8n webhook")
    else:
        # Verify batch exists
        batch = session.get(UploadBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        client_id = batch.client_id
    
    # Create lead
    lead = Lead(
        batch_id=batch_id,
        name=request.lead.name,
        phone=request.lead.phone,
        email=request.lead.email,
        source_url=request.lead.source_url,
        notes=request.lead.notes,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    
    # Create call
    call = Call(
        lead_id=lead.id,
        batch_id=batch_id,
        client_id=client_id,
        status=CallStatus.QUEUED,
        attempt=1,
    )
    session.add(call)
    session.commit()
    session.refresh(call)
    
    logger.info(f"Created call {call.id} for lead {lead.name} via n8n webhook")
    
    return StartCallResponse(call_id=call.id)


# 4) POST /api/calls/{call_id}/status
@app.post("/api/calls/{call_id}/status", response_model=CallStatusResponse)
def update_call_status(
    call_id: int,
    request: CallStatusUpdate,
    session: Session = Depends(get_db),
):
    """
    Update call status and/or save call result.
    Called by agent worker after call completes.
    """
    call = session.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Update status if provided
    if request.status:
        call.status = request.status
        call.updated_at = datetime.utcnow()
    
    # Create/update result if result type provided
    if request.result:
        # Check for existing result
        existing_result = session.exec(
            select(CallResult).where(CallResult.call_id == call_id)
        ).first()
        
        if existing_result:
            existing_result.result = request.result
            existing_result.transcript = request.transcript or existing_result.transcript
            existing_result.booked_slot = request.booked_slot or existing_result.booked_slot
            existing_result.notes = request.notes or existing_result.notes
        else:
            result = CallResult(
                call_id=call_id,
                result=request.result,
                transcript=request.transcript,
                booked_slot=request.booked_slot,
                notes=request.notes,
            )
            session.add(result)
        
        # Mark call as completed
        call.status = CallStatus.COMPLETED
        call.updated_at = datetime.utcnow()
    
    session.commit()
    
    logger.info(f"Updated call {call_id}: status={call.status}")
    
    return CallStatusResponse(
        call_id=call_id,
        status=call.status.value,
        message="Call updated successfully",
    )


# 5) GET /api/clients/{client_id}/batches/{batch_id}/calls
@app.get("/api/clients/{client_id}/batches/{batch_id}/calls", response_model=CallListResponse)
def get_batch_calls(
    client_id: int,
    batch_id: int,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
):
    """
    Get paginated call logs for a batch.
    Includes call_result if present.
    """
    # Verify client and batch
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    batch = session.get(UploadBatch, batch_id)
    if not batch or batch.client_id != client_id:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Count total
    total_stmt = select(Call).where(Call.batch_id == batch_id)
    all_calls = session.exec(total_stmt).all()
    total = len(all_calls)
    
    # Get paginated calls
    stmt = (
        select(Call)
        .where(Call.batch_id == batch_id)
        .order_by(Call.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    calls = session.exec(stmt).all()
    
    # Build response
    call_outputs = []
    for call in calls:
        # Get lead info
        lead = session.get(Lead, call.lead_id)
        
        # Get result if exists
        result_stmt = select(CallResult).where(CallResult.call_id == call.id)
        result = session.exec(result_stmt).first()
        
        call_result = None
        if result:
            call_result = CallResultOutput(
                id=result.id,
                result=result.result.value,
                transcript=result.transcript,
                booked_slot=result.booked_slot,
                notes=result.notes,
                created_at=result.created_at,
            )
        
        call_outputs.append(CallOutput(
            id=call.id,
            lead_id=call.lead_id,
            batch_id=call.batch_id,
            client_id=call.client_id,
            status=call.status.value,
            attempt=call.attempt,
            created_at=call.created_at,
            updated_at=call.updated_at,
            lead_name=lead.name if lead else None,
            lead_phone=lead.phone if lead else None,
            call_result=call_result,
        ))
    
    return CallListResponse(
        calls=call_outputs,
        total=total,
        limit=limit,
        offset=offset,
    )


# 6) POST /api/twilio/webhook
@app.post("/api/twilio/webhook")
def twilio_webhook(request: TwilioWebhookRequest, session: Session = Depends(get_db)):
    """
    Handle Twilio status callbacks.
    Converts Twilio payload to internal format.
    """
    logger.info(f"Twilio webhook: CallSid={request.CallSid}, Status={request.CallStatus}")
    
    # For now, just log and return success
    # Real implementation would look up call by CallSid and update status
    return {"status": "ok", "received": request.model_dump()}


# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/sentry-debug")
async def trigger_sentry_error():
    """Debug endpoint to test Sentry integration. Remove in production."""
    division_by_zero = 1 / 0


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Dental AI Voice Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
