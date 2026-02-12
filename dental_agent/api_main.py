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

'''

Run with: uvicorn api_main:app --reload
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

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
    mask_name,
    sanitize_string,
    sanitize_filename,
    sanitize_html,
    validate_csv_upload,
    setup_logger,
    PIIMaskingFilter,
    APIError,
    requires_consent,
    filter_leads_by_consent,
    check_lead_consent,
)
from rate_limiter import RateLimitMiddleware
from dnc_service import filter_leads_by_dnc
from brute_force import brute_force_guard

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Import auth configuration from auth module (avoids circular imports)
try:
    from dental_agent.auth import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS, require_auth, get_current_user
except ImportError:
    from auth import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS, require_auth, get_current_user

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

# CORS middleware - restrict to known origins
# In production, set ALLOWED_ORIGINS env variable to exact domains
# SECURITY: Never use allow_credentials=True with wildcard or dynamic origins
import os

_default_origins = "http://localhost:3000,http://localhost:5173"  # DevSkim: ignore DS137138 - localhost CORS for dev only
cors_origins_env = os.getenv("ALLOWED_ORIGINS", _default_origins)
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

# SECURITY: Validate origins - block dangerous configurations
if "*" in cors_origins:
    logger.error("SECURITY: ALLOWED_ORIGINS contains wildcard '*'. This is dangerous with credentials.")
    # Remove wildcard to prevent security vulnerability
    cors_origins = [o for o in cors_origins if o != "*"]
    if not cors_origins:
        cors_origins = _default_origins.split(",")

# Only allow credentials with explicitly configured origins (not defaults in production)
is_production = os.getenv("ENVIRONMENT") == "production"
allow_creds = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"

if is_production and cors_origins_env == _default_origins:
    logger.warning("Using default CORS origins in production. Set ALLOWED_ORIGINS env var.")
    # Disable credentials if using default origins in production
    allow_creds = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-User-Email"],
    max_age=600,
)

# Rate limiting middleware (skips Twilio webhooks and health checks)
# Disabled via env var for testing to avoid burst limit false positives
if os.getenv("DISABLE_RATE_LIMIT", "0") != "1":
    app.add_middleware(RateLimitMiddleware)

# Include existing routers (Celery-based call routes)
try:
    from dental_agent.routes_calls import router as calls_router
    from dental_agent.routes_twilio import router as twilio_router, require_twilio_auth
    from dental_agent.routes_inbound import router as inbound_router
    from dental_agent.routes_admin import router as admin_router
    from dental_agent.routes_sms import router as sms_router
    from dental_agent.routes_analytics import router as analytics_router
    from dental_agent.routes_superadmin import router as superadmin_router
    from dental_agent.routes_usage import router as usage_router
    from dental_agent.routes_calendar import router as calendar_router
    from dental_agent.routes_transfer import router as transfer_router
    from dental_agent.routes_recall import router as recall_router
    from dental_agent.routes_pms import router as pms_router
    from dental_agent.routes_dnc import router as dnc_router
except ImportError:
    from routes_calls import router as calls_router
    from routes_twilio import router as twilio_router, require_twilio_auth
    from routes_inbound import router as inbound_router
    from routes_admin import router as admin_router
    from routes_sms import router as sms_router
    from routes_analytics import router as analytics_router
    from routes_superadmin import router as superadmin_router
    from routes_usage import router as usage_router
    from routes_calendar import router as calendar_router
    from routes_transfer import router as transfer_router
    from routes_recall import router as recall_router
    from routes_pms import router as pms_router
    from routes_dnc import router as dnc_router
    from routes_compliance import router as compliance_router

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
app.include_router(pms_router)  # PMS integration (Open Dental, Dentrix, etc.)
app.include_router(dnc_router)  # Do-Not-Call registry (AG-9)
app.include_router(compliance_router)  # BAA + retention + deletion (AG-11)


# =============================================================================
# Security Headers Middleware
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 0 (disabled — CSP is the modern replacement)
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (strict — API serves JSON only)
    - Referrer-Policy
    - Permissions-Policy
    - Cross-Origin-Opener-Policy
    - Cross-Origin-Resource-Policy
    """
    
    # Separate CSP for API (strict) vs docs/OpenAPI UI
    _API_CSP = (
        "default-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none';"
    )
    
    # Swagger/ReDoc UI needs scripts and styles — slightly relaxed but NO unsafe-eval
    _DOCS_CSP = (
        "default-src 'none'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    
    _DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Disable X-XSS-Protection (CSP is the modern replacement;
        # XSS-Protection can introduce vulnerabilities in old IE)
        response.headers["X-XSS-Protection"] = "0"
        
        # HSTS - force HTTPS (only in production)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        # CSP — strict for API, slightly relaxed for Swagger/ReDoc UI
        if request.url.path in self._DOCS_PATHS:
            response.headers["Content-Security-Policy"] = self._DOCS_CSP
        else:
            response.headers["Content-Security-Policy"] = self._API_CSP
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Cross-origin isolation headers
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Permissions policy — deny all browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


# -----------------------------------------------------------------------------
# Access Control Helpers
# -----------------------------------------------------------------------------

def assert_client_access(user: dict, client_id: int, session: Session) -> Client:
    """
    Verify the authenticated user has access to client_id.
    
    - Admin users can access any client.
    - Non-admin users can only access clients where client.owner_email == user.email.
    
    Returns the Client object if access is granted.
    Raises 404 if client not found, 403 if access denied.
    """
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Admins can access any client
    if user.get("is_admin"):
        return client
    
    # Non-admin: must own the client
    if client.owner_email and client.owner_email == user.get("email"):
        return client
    
    logger.warning(
        f"Access denied: user {mask_email(user.get('email', ''))} "
        f"attempted to access client {client_id}"
    )
    raise HTTPException(status_code=403, detail="Access denied to this client")


# -----------------------------------------------------------------------------
# Startup Event
# -----------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    logger.info(f"Initializing database: {DATABASE_URL}")
    create_db(DATABASE_URL)
    
    # SECURITY: Demo user creation is OPT-IN only via ENABLE_DEMO_USER
    # This prevents accidental creation of admin accounts in production
    if os.getenv("ENABLE_DEMO_USER", "0") == "1":
        with get_session() as session:
            # Check for existing admin user
            existing = session.exec(select(User).where(User.email == "admin@dental-demo.com")).first()
            if not existing:
                import secrets
                # Use DEMO_USER_PASSWORD if set (tests), otherwise random
                demo_pass = os.getenv("DEMO_USER_PASSWORD") or secrets.token_urlsafe(12)[:16]
                user = User(email="admin@dental-demo.com", is_admin=True)
                user.set_password(demo_pass)
                session.add(user)
                session.commit()
                logger.warning(f"DEVELOPMENT MODE: Created demo admin user: admin@dental-demo.com / {demo_pass}")
                logger.warning("Demo user creation is enabled via ENABLE_DEMO_USER=1 - NEVER use in production")
        
            # Check for existing client/clinic (inside same session)
            existing_client = session.exec(select(Client).where(Client.email == "info@sunshine-dental-demo.com")).first()
            if not existing_client:
                # Get telephony number from environment
                phone_number = os.getenv("TWILIO_NUMBER", os.getenv("TELNYX_NUMBER", "+19048679643"))
                
                client = Client(
                    name="Sunshine Dental",
                    email="info@sunshine-dental-demo.com",
                    timezone="America/New_York",
                    agent_name="Sarah",
                    agent_voice="aura-asteria-en",
                    address="123 Smile Street, Jacksonville, FL 32256",
                    phone_display="(904) 867-9643",
                    hours="Monday-Friday 8am-5pm, Saturday 9am-1pm",
                    services="cleanings, exams, fillings, crowns, whitening, extractions",
                    insurance_accepted="Delta Dental, Cigna, Aetna, MetLife, United Healthcare",
                    twilio_number=phone_number,
                    custom_instructions="Our office is closed for lunch from 12pm-1pm. For emergencies after hours, patients should go to the ER.",
                    monthly_price=199.0,
                    is_active=True,
                )
                session.add(client)
                session.commit()
                logger.info(f"Created demo clinic: Sunshine Dental with number {phone_number}")


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------

def get_db():
    """Dependency to get database session."""
    with get_session() as session:
        yield session


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
def login(request: LoginRequest, raw_request: Request, session: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    Demo: uses plain text password matching.

    Brute-force protection (AG-10):
      • Per-account: 5 failures → 15 min lockout
      • Per-IP: 20 failures → 15 min block
    """
    client_ip = raw_request.client.host if raw_request.client else "unknown"

    # AG-10: Check brute-force limits BEFORE credential verification
    brute_force_guard.check_and_raise(request.email, client_ip)

    user = session.exec(select(User).where(User.email == request.email)).first()
    
    if not user or not user.check_password(request.password):
        # AG-10: Record failed attempt
        brute_force_guard.record_failure(request.email, client_ip)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # AG-10: Reset account counter on success
    brute_force_guard.record_success(request.email, client_ip)

    # Create JWT using timezone-aware datetime (Python 3.12+ compatible)
    from datetime import timezone
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "is_admin": user.is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),  # Issued at time
        "type": "access",  # Token type for validation
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    logger.info(f"User logged in: {mask_email(user.email)}")
    return LoginResponse(token=token)


# 2a) POST /api/clients/{client_id}/leads (JSON-only endpoint)
@app.post("/api/clients/{client_id}/leads", response_model=UploadResponse)
def upload_leads_json(
    client_id: int,
    body: LeadsUploadRequest,
    current_user: dict = Depends(require_auth),
    session: Session = Depends(get_db),
):
    """
    Upload leads via JSON body (simpler endpoint for API testing).
    Requires authentication. User must have access to the specified client.
    
    For PSTN calls, leads MUST have consent=true (TCPA compliance).
    Consent is enforced centrally via enforce_consent() — no bypass flag.
    """
    # Verify client exists and user has access
    client = assert_client_access(current_user, client_id, session)
    
    # Collect lead dicts
    leads_data = [lead.model_dump() for lead in body.leads]
    
    # Centralized consent filter (AG-4)
    leads_data, skipped_no_consent = filter_leads_by_consent(
        leads_data, logger_instance=logger
    )
    
    if not leads_data:
        if skipped_no_consent > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"All {skipped_no_consent} leads skipped: consent required for PSTN calls"
            )
        raise HTTPException(status_code=400, detail="No valid leads")
    
    # DNC filter (AG-9)
    leads_data, skipped_dnc = filter_leads_by_dnc(session, leads_data, clinic_id=client_id)
    
    if not leads_data:
        raise HTTPException(
            status_code=400,
            detail=f"All leads blocked: {skipped_no_consent} no consent, {skipped_dnc} on DNC list"
        )
    
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
    
    logger.info(f"Created batch {batch.id} with {queued_count} queued calls, {skipped_no_consent} skipped (no consent), {skipped_dnc} DNC")
    
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
    current_user: dict = Depends(require_auth),
    session: Session = Depends(get_db),
):
    """
    Upload leads via CSV file or JSON body.
    Creates UploadBatch, Lead rows, and enqueues Call rows.
    Requires authentication. User must have access to the specified client.
    
    For PSTN calls (TELEPHONY_MODE=TWILIO), leads MUST have consent=true.
    Consent is enforced centrally via enforce_consent() — no bypass flag.
    """
    # Verify client exists and user has access
    client = assert_client_access(current_user, client_id, session)
    
    leads_data: list[dict] = []
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
            logger.error(f"Failed to parse CSV: {e}")
            raise HTTPException(status_code=400, detail="Failed to parse CSV")
    
    # Or parse JSON body
    elif leads_json:
        for lead in leads_json.leads:
            leads_data.append(lead.model_dump())
    
    else:
        raise HTTPException(status_code=400, detail="Provide either file or JSON leads")
    
    if not leads_data:
        raise HTTPException(status_code=400, detail="No valid leads with phone numbers")
    
    # Centralized consent filter (AG-4)
    leads_data, skipped_no_consent = filter_leads_by_consent(
        leads_data, logger_instance=logger
    )
    
    if not leads_data:
        if skipped_no_consent > 0:
            raise HTTPException(
                status_code=400,
                detail=f"All {skipped_no_consent} leads skipped: consent required for PSTN calls"
            )
        raise HTTPException(status_code=400, detail="No valid leads")
    
    # DNC filter (AG-9)
    leads_data, skipped_dnc = filter_leads_by_dnc(session, leads_data, clinic_id=client_id)
    
    if not leads_data:
        raise HTTPException(
            status_code=400,
            detail=f"All leads blocked: {skipped_no_consent} no consent, {skipped_dnc} on DNC list"
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
    logger.info(f"Enqueued {queued_count} calls for batch {batch.id}, {skipped_no_consent} skipped (no consent), {skipped_dnc} DNC")
    
    return UploadResponse(
        upload_id=batch.id,
        batch_id=batch.id,
        queued_count=queued_count,
        skipped_no_consent=skipped_no_consent,
    )


# 4) POST /api/calls/{call_id}/status
@app.post("/api/calls/{call_id}/status", response_model=CallStatusResponse)
def update_call_status(
    call_id: int,
    request: CallStatusUpdate,
    current_user: dict = Depends(require_auth),
    session: Session = Depends(get_db),
):
    """
    Update call status and/or save call result.
    Requires authentication.
    """
    call = session.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Sanitize text fields to prevent stored XSS (AG-5)
    safe_transcript = sanitize_html(request.transcript) if request.transcript else request.transcript
    safe_notes = sanitize_html(request.notes) if request.notes else request.notes

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
            existing_result.transcript = safe_transcript or existing_result.transcript
            existing_result.booked_slot = request.booked_slot or existing_result.booked_slot
            existing_result.notes = safe_notes or existing_result.notes
        else:
            result = CallResult(
                call_id=call_id,
                result=request.result,
                transcript=safe_transcript,
                booked_slot=request.booked_slot,
                notes=safe_notes,
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
    current_user: dict = Depends(require_auth),
    session: Session = Depends(get_db),
):
    """
    Get paginated call logs for a batch.
    Includes call_result if present. Requires authentication.
    """
    # Verify client exists and user has access
    client = assert_client_access(current_user, client_id, session)
    
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
async def twilio_webhook(
    request: Request,
    _twilio_auth=Depends(require_twilio_auth),
    session: Session = Depends(get_db),
):
    """
    Handle Twilio status callbacks.
    Requires valid Twilio X-Twilio-Signature (skipped in SIMULATED mode).
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    
    logger.info(f"Twilio webhook: CallSid={call_sid}, Status={call_status}")
    
    # For now, just log and return success
    # Real implementation would look up call by CallSid and update status
    return {"status": "ok", "call_sid": call_sid, "call_status": call_status}


# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


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
