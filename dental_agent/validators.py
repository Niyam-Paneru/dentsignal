"""
validators.py - Enhanced Input Validation Module

Provides strict validation for all user inputs to prevent:
- XSS attacks
- SQL injection (defense in depth)
- Command injection
- Path traversal
- NoSQL injection
- Other injection attacks

Usage:
    from validators import validate_clinic_name, sanitize_input, XSS_PATTERN
    
    if not validate_clinic_name(name):
        raise ValueError("Invalid clinic name")
    
    clean_input = sanitize_input(user_input)
"""

import re
from typing import Optional, Pattern
from pydantic import field_validator, ValidationInfo


# =============================================================================
# SECURITY PATTERNS
# =============================================================================

# XSS Detection Patterns
# NOTE: Avoid greedy/backtracking HTML regexps (CodeQL "Bad HTML filtering regexp").
# Use simple substring or anchored patterns instead of matching full tag pairs.
XSS_PATTERNS: list[Pattern] = [
    re.compile(r'<\s*script', re.IGNORECASE),  # Detect opening script tag only
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick, onerror, etc.
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'<\s*iframe', re.IGNORECASE),
    re.compile(r'<\s*object', re.IGNORECASE),
    re.compile(r'<\s*embed', re.IGNORECASE),
    re.compile(r'<\s*form', re.IGNORECASE),
    re.compile(r'<\s*input', re.IGNORECASE),
    re.compile(r'document\.cookie', re.IGNORECASE),
    re.compile(r'document\.location', re.IGNORECASE),
    re.compile(r'window\.location', re.IGNORECASE),
    re.compile(r'eval\s*\(', re.IGNORECASE),
    re.compile(r'expression\s*\(', re.IGNORECASE),
    re.compile(r'\\x[0-9a-fA-F]{2}', re.IGNORECASE),  # Hex encoding
    re.compile(r'&#x?[0-9a-fA-F]+;', re.IGNORECASE),  # HTML entities
]

# SQL Injection Patterns
SQLI_PATTERNS: list[Pattern] = [
    re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)', re.IGNORECASE),
    re.compile(r'(\-\-|\#|\/\*|\*\/)', re.IGNORECASE),  # Comment sequences
    re.compile(r'(\bUNION\s+ALL\s+SELECT\b)', re.IGNORECASE),
    re.compile(r'(\bOR\s+\d+\s*=\s*\d+)', re.IGNORECASE),
    re.compile(r'(\bAND\s+\d+\s*=\s*\d+)', re.IGNORECASE),
    re.compile(r'(\bSLEEP\s*\()', re.IGNORECASE),
    re.compile(r'(\bBENCHMARK\s*\()', re.IGNORECASE),
    re.compile(r'(\bWAITFOR\s+DELAY\b)', re.IGNORECASE),
]

# Path Traversal Patterns
PATH_TRAVERSAL_PATTERNS: list[Pattern] = [
    re.compile(r'\.\./', re.IGNORECASE),
    re.compile(r'\.\.\\', re.IGNORECASE),
    re.compile(r'%2e%2e%2f', re.IGNORECASE),  # URL encoded ../
    re.compile(r'%2e%2e/', re.IGNORECASE),
    re.compile(r'\.\.(%2f|\\)', re.IGNORECASE),
    re.compile(r'\\+\.\.\\+', re.IGNORECASE),
]

# Command Injection Patterns
CMD_INJECTION_PATTERNS: list[Pattern] = [
    re.compile(r'[;&|`]\s*\w+', re.IGNORECASE),
    re.compile(r'\$\(', re.IGNORECASE),
    re.compile(r'`[^`]*`', re.IGNORECASE),
    re.compile(r'\|\s*\w+', re.IGNORECASE),
    re.compile(r'&&\s*\w+', re.IGNORECASE),
]

# NoSQL Injection Patterns
NOSQLI_PATTERNS: list[Pattern] = [
    re.compile(r'\$where', re.IGNORECASE),
    re.compile(r'\$regex', re.IGNORECASE),
    re.compile(r'\$ne', re.IGNORECASE),
    re.compile(r'\$gt', re.IGNORECASE),
    re.compile(r'\$lt', re.IGNORECASE),
    re.compile(r'\$exists', re.IGNORECASE),
]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def contains_pattern(value: str, patterns: list[Pattern]) -> bool:
    """Check if value contains any of the given patterns."""
    for pattern in patterns:
        if pattern.search(value):
            return True
    return False


def validate_no_xss(value: Optional[str]) -> bool:
    """Validate that input doesn't contain XSS patterns."""
    if not value:
        return True
    return not contains_pattern(value, XSS_PATTERNS)


def validate_no_sqli(value: Optional[str]) -> bool:
    """Validate that input doesn't contain SQL injection patterns."""
    if not value:
        return True
    return not contains_pattern(value, SQLI_PATTERNS)


def validate_no_path_traversal(value: Optional[str]) -> bool:
    """Validate that input doesn't contain path traversal patterns."""
    if not value:
        return True
    return not contains_pattern(value, PATH_TRAVERSAL_PATTERNS)


def validate_no_cmd_injection(value: Optional[str]) -> bool:
    """Validate that input doesn't contain command injection patterns."""
    if not value:
        return True
    return not contains_pattern(value, CMD_INJECTION_PATTERNS)


def validate_no_nosqli(value: Optional[str]) -> bool:
    """Validate that input doesn't contain NoSQL injection patterns."""
    if not value:
        return True
    return not contains_pattern(value, NOSQLI_PATTERNS)


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing dangerous characters.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t\r')
    
    return value


def validate_clinic_name(name: str) -> bool:
    """
    Validate clinic name.
    
    Rules:
    - 2-200 characters
    - Letters, numbers, spaces, and common punctuation only
    - No XSS or injection patterns
    """
    if not name or len(name) < 2 or len(name) > 200:
        return False
    
    # Check allowed characters
    if not re.match(r'^[\w\s\-\'&.,()]+$', name, re.UNICODE):
        return False
    
    # Check for injection patterns
    if not validate_no_xss(name) or not validate_no_sqli(name):
        return False
    
    return True


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Accepts formats:
    - (555) 123-4567
    - 555-123-4567
    - 5551234567
    - +15551234567
    """
    if not phone:
        return False
    
    # Remove common formatting characters
    digits_only = re.sub(r'[\s\-\(\)\.+]', '', phone)
    
    # Check length (10 digits for US, 11 with country code)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False
    
    # Check for injection patterns
    if not validate_no_xss(phone):
        return False
    
    return True


def validate_email_local_part(email: str) -> bool:
    """Validate email local part for suspicious patterns."""
    if not email or '@' not in email:
        return False
    
    local_part = email.split('@')[0]
    
    # Check for suspicious patterns in local part
    suspicious_patterns = [
        r'\.\./',  # Path traversal
        r'<script',
        r'javascript:',
        r'on\w+=',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, local_part, re.IGNORECASE):
            return False
    
    return True


def validate_safe_string(value: str, min_length: int = 1, max_length: int = 500) -> bool:
    """
    Validate a generic safe string.
    
    Args:
        value: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        True if valid, False otherwise
    """
    if not value or len(value) < min_length or len(value) > max_length:
        return False
    
    # Check all security patterns
    if contains_pattern(value, XSS_PATTERNS):
        return False
    if contains_pattern(value, SQLI_PATTERNS):
        return False
    if contains_pattern(value, CMD_INJECTION_PATTERNS):
        return False
    
    return True


# =============================================================================
# PYDANTIC VALIDATORS
# =============================================================================

def xss_validator(field_name: str):
    """Create a Pydantic validator for XSS checking."""
    @field_validator(field_name, mode='before')
    @classmethod
    def validate(cls, v):
        if v is not None and not validate_no_xss(str(v)):
            raise ValueError(f"{field_name} contains potentially dangerous content")
        return v
    return validate


def sqli_validator(field_name: str):
    """Create a Pydantic validator for SQL injection checking."""
    @field_validator(field_name, mode='before')
    @classmethod
    def validate(cls, v):
        if v is not None and not validate_no_sqli(str(v)):
            raise ValueError(f"{field_name} contains potentially dangerous content")
        return v
    return validate


def length_validator(field_name: str, min_len: int = 1, max_len: int = 500):
    """Create a Pydantic validator for length checking."""
    @field_validator(field_name, mode='after')
    @classmethod
    def validate(cls, v):
        if v is not None:
            str_v = str(v)
            if len(str_v) < min_len or len(str_v) > max_len:
                raise ValueError(f"{field_name} must be between {min_len} and {max_len} characters")
        return v
    return validate


# =============================================================================
# SECURITY HEADERS FOR VALIDATION
# =============================================================================

class SecurityHeaders:
    """Security-related HTTP headers for validation."""
    
    REQUIRED_HEADERS = {
        'production': [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Strict-Transport-Security',
        ],
        'development': [
            'X-Content-Type-Options',
            'X-Frame-Options',
        ]
    }
    
    @classmethod
    def validate_response_headers(cls, headers: dict, environment: str = 'production') -> list:
        """
        Validate that response has required security headers.
        
        Returns:
            List of missing headers
        """
        missing = []
        required = cls.REQUIRED_HEADERS.get(environment, cls.REQUIRED_HEADERS['production'])
        
        for header in required:
            if header not in headers:
                missing.append(header)
        
        return missing
