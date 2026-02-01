"""
audit_logger.py - Security Audit Logging Module

Provides comprehensive audit logging for:
- Admin/SuperAdmin actions
- Authentication events (login, logout, failed attempts)
- Data access and modifications
- Security-sensitive operations

All logs are written to both:
1. Application log (for real-time monitoring)
2. Audit log file (for compliance and forensics)

Usage:
    from audit_logger import log_admin_action, log_auth_event, log_data_access
    
    log_admin_action("user@example.com", "clinic_create", {"clinic_id": 123})
    log_auth_event("user@example.com", "login_success", ip_address="1.2.3.4")
"""

import os
import json
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# Configure audit logger
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")
os.makedirs(os.path.dirname(AUDIT_LOG_FILE) if os.path.dirname(AUDIT_LOG_FILE) else "logs", exist_ok=True)

# Create audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Prevent propagation to root logger
audit_logger.propagate = False

# File handler for audit log
audit_handler = logging.FileHandler(AUDIT_LOG_FILE)
audit_handler.setLevel(logging.INFO)

# Formatter with structured JSON output
class AuditFormatter(logging.Formatter):
    """Format audit logs as JSON for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "event_type": getattr(record, "event_type", "unknown"),
            "user": getattr(record, "user", None),
            "action": getattr(record, "action", None),
            "resource": getattr(record, "resource", None),
            "details": getattr(record, "details", {}),
            "ip_address": getattr(record, "ip_address", None),
            "user_agent": getattr(record, "user_agent", None),
            "session_id": getattr(record, "session_id", None),
            "success": getattr(record, "success", True),
            "message": record.getMessage(),
        }
        return json.dumps(log_entry, default=str)

audit_handler.setFormatter(AuditFormatter())
audit_logger.addHandler(audit_handler)


class AuditEventType(str, Enum):
    """Types of audit events."""
    ADMIN_ACTION = "admin_action"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"


class AuthEvent(str, Enum):
    """Authentication event types."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"


class AdminAction(str, Enum):
    """Admin action types."""
    CLINIC_CREATE = "clinic_create"
    CLINIC_UPDATE = "clinic_update"
    CLINIC_DELETE = "clinic_delete"
    CLINIC_VIEW = "clinic_view"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_VIEW = "user_view"
    SETTINGS_UPDATE = "settings_update"
    BILLING_UPDATE = "billing_update"
    API_KEY_GENERATE = "api_key_generate"
    API_KEY_REVOKE = "api_key_revoke"
    EXPORT_DATA = "export_data"
    SUPERADMIN_ACCESS = "superadmin_access"


def _mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive fields in log data."""
    if not isinstance(data, dict):
        return data
    
    masked = {}
    sensitive_keys = [
        "password", "password_hash", "token", "secret", "api_key",
        "credit_card", "ssn", "social_security", "dob", "date_of_birth"
    ]
    
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            masked[key] = "***REDACTED***"
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive_data(value)
        elif isinstance(value, list):
            masked[key] = [_mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
        else:
            masked[key] = value
    
    return masked


def log_admin_action(
    user: str,
    action: AdminAction,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True
) -> None:
    """
    Log an admin action.
    
    Args:
        user: Email or ID of the admin user
        action: Type of admin action performed
        details: Additional details about the action (will be masked)
        ip_address: Client IP address
        user_agent: Client user agent string
        success: Whether the action was successful
    """
    extra = {
        "event_type": AuditEventType.ADMIN_ACTION,
        "user": user,
        "action": action.value if isinstance(action, AdminAction) else action,
        "details": _mask_sensitive_data(details or {}),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": success,
    }
    
    audit_logger.info(
        f"Admin action: {action} by {user}",
        extra=extra
    )


def log_auth_event(
    user: str,
    event: AuthEvent,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True
) -> None:
    """
    Log an authentication event.
    
    Args:
        user: Email or ID of the user
        event: Type of authentication event
        ip_address: Client IP address
        user_agent: Client user agent string
        details: Additional details
        success: Whether the event was successful
    """
    extra = {
        "event_type": AuditEventType.AUTHENTICATION,
        "user": user,
        "action": event.value if isinstance(event, AuthEvent) else event,
        "details": _mask_sensitive_data(details or {}),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": success,
    }
    
    level = logging.WARNING if event in [
        AuthEvent.LOGIN_FAILED, AuthEvent.TOKEN_INVALID, AuthEvent.ACCOUNT_LOCKED
    ] else logging.INFO
    
    audit_logger.log(
        level,
        f"Auth event: {event} for {user}",
        extra=extra
    )


def log_data_access(
    user: str,
    resource: str,
    resource_id: Optional[str] = None,
    action: str = "view",
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log data access (for HIPAA compliance).
    
    Args:
        user: Email or ID of the user accessing data
        resource: Type of resource (e.g., "patient", "clinic", "call")
        resource_id: ID of the specific resource
        action: Type of access (view, export, delete)
        ip_address: Client IP address
        details: Additional context
    """
    extra = {
        "event_type": AuditEventType.DATA_ACCESS,
        "user": user,
        "action": action,
        "resource": resource,
        "details": {
            "resource_id": resource_id,
            **_mask_sensitive_data(details or {})
        },
        "ip_address": ip_address,
        "success": True,
    }
    
    audit_logger.info(
        f"Data access: {user} {action} {resource} {resource_id or ''}",
        extra=extra
    )


def log_security_event(
    event_type: str,
    description: str,
    severity: str = "warning",
    user: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event (e.g., "rate_limit_exceeded", "suspicious_activity")
        description: Human-readable description
        severity: Event severity (debug, info, warning, error, critical)
        user: Associated user (if any)
        ip_address: Client IP address
        details: Additional context
    """
    level = getattr(logging, severity.upper(), logging.WARNING)
    
    extra = {
        "event_type": AuditEventType.SECURITY_EVENT,
        "user": user,
        "action": event_type,
        "details": _mask_sensitive_data(details or {}),
        "ip_address": ip_address,
        "success": False,  # Security events are typically failures/blocks
    }
    
    audit_logger.log(level, description, extra=extra)


def get_recent_audit_logs(
    event_type: Optional[AuditEventType] = None,
    user: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve recent audit logs.
    
    Args:
        event_type: Filter by event type
        user: Filter by user
        limit: Maximum number of logs to return
        
    Returns:
        List of audit log entries
    """
    logs = []
    
    try:
        with open(AUDIT_LOG_FILE, 'r') as f:
            for line in reversed(f.readlines()):
                if len(logs) >= limit:
                    break
                    
                try:
                    entry = json.loads(line.strip())
                    
                    if event_type and entry.get("event_type") != event_type.value:
                        continue
                    if user and entry.get("user") != user:
                        continue
                        
                    logs.append(entry)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    
    return logs


def verify_audit_log_integrity(log_entry: Dict[str, Any], signature: str, secret: str) -> bool:
    """
    Verify the integrity of an audit log entry using HMAC.
    
    This is used if you implement signed audit logs for tamper detection.
    
    Args:
        log_entry: The audit log entry
        signature: The HMAC signature
        secret: The secret key used for signing
        
    Returns:
        True if the signature is valid
    """
    message = json.dumps(log_entry, sort_keys=True, default=str)
    expected_signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
