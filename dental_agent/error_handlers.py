"""
error_handlers.py - Secure Error Handling

Provides secure error responses that don't leak sensitive information:
- Generic error messages to clients
- Detailed logging for debugging
- No stack traces in production
- No database/SQL details
- No system information

Usage:
    from error_handlers import SecureHTTPException, handle_exception
    
    raise SecureHTTPException(
        status_code=404,
        message="Resource not found",
        log_message="User 123 tried to access clinic 456 which doesn't exist"
    )
"""

import os
import logging
import traceback
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


# Configure error logger
error_logger = logging.getLogger("security_errors")


# =============================================================================
# SECURE ERROR MESSAGES
# =============================================================================

# Generic error messages that don't leak implementation details
GENERIC_ERROR_MESSAGES = {
    400: "Bad request",
    401: "Authentication required",
    403: "Access denied",
    404: "Resource not found",
    409: "Conflict with current state",
    422: "Validation error",
    429: "Rate limit exceeded",
    500: "Internal server error",
    502: "Service temporarily unavailable",
    503: "Service unavailable",
}


class SecureHTTPException(HTTPException):
    """
    HTTP Exception that doesn't leak sensitive information.
    
    Attributes:
        status_code: HTTP status code
        message: Generic message for the client
        log_message: Detailed message for logs (optional)
        log_level: Logging level
        details: Additional details for logs only
    """
    
    def __init__(
        self,
        status_code: int,
        message: Optional[str] = None,
        log_message: Optional[str] = None,
        log_level: str = "warning",
        details: Optional[Dict[str, Any]] = None
    ):
        # Use generic message if none provided
        self.client_message = message or GENERIC_ERROR_MESSAGES.get(
            status_code, "An error occurred"
        )
        
        self.log_message = log_message or self.client_message
        self.log_level = log_level
        self.details = details or {}
        
        # Call parent with generic message
        super().__init__(status_code=status_code, detail=self.client_message)
    
    def log(self, request: Optional[Request] = None):
        """Log the error with full details."""
        log_data = {
            "status_code": self.status_code,
            "message": self.log_message,
            "client_message": self.client_message,
            **self.details
        }
        
        if request:
            log_data["client_host"] = request.client.host if request.client else None
            log_data["method"] = request.method
            log_data["url"] = str(request.url)
        
        log_func = getattr(error_logger, self.log_level, error_logger.warning)
        log_func(f"Security error: {self.log_message}", extra=log_data)


def sanitize_error_message(message: str) -> str:
    """
    Sanitize an error message to remove sensitive information.
    
    Args:
        message: Original error message
        
    Returns:
        Sanitized message safe for client exposure
    """
    # List of patterns that indicate sensitive information
    sensitive_patterns = [
        # SQL-related
        (r'SELECT\s+', ''),
        (r'INSERT\s+', ''),
        (r'UPDATE\s+', ''),
        (r'DELETE\s+', ''),
        (r'FROM\s+\w+', ''),
        (r'TABLE\s+\w+', ''),
        
        # File system
        (r'/[\w/]+/\w+\.\w{2,4}', '[PATH]'),
        (r'C:\\\[\w\\]+\\\w+\.\w{2,4}', '[PATH]'),
        
        # Database connections
        (r'postgresql://[^\s]+', '[DB_URL]'),
        (r'mysql://[^\s]+', '[DB_URL]'),
        (r'sqlite:///[^\s]+', '[DB_URL]'),
        
        # IP addresses
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
        
        # Stack trace indicators
        (r'File\s+"[^"]+"', ''),
        (r'line\s+\d+', ''),
        
        # Internal paths
        (r'/app/[^\s]+', '[INTERNAL_PATH]'),
        (r'/usr/[^\s]+', '[INTERNAL_PATH]'),
        (r'/var/[^\s]+', '[INTERNAL_PATH]'),
    ]
    
    import re
    sanitized = message
    for pattern, replacement in sensitive_patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


def get_secure_error_response(
    status_code: int,
    original_error: Optional[Exception] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """
    Create a secure error response.
    
    Args:
        status_code: HTTP status code
        original_error: Original exception (for logging only)
        request: Request object for context
        
    Returns:
        JSONResponse with generic error message
    """
    is_development = os.getenv("ENVIRONMENT") == "development"
    
    # Get generic message
    message = GENERIC_ERROR_MESSAGES.get(status_code, "An error occurred")
    
    response_data = {
        "error": {
            "code": status_code,
            "message": message,
        }
    }
    
    # In development, optionally include more details
    if is_development and original_error:
        response_data["error"]["debug"] = {
            "type": type(original_error).__name__,
            "details": str(original_error)[:200],  # Limit length
        }
    
    # Include request ID for support (if implemented)
    # response_data["error"]["request_id"] = get_request_id()
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def handle_exception(
    request: Request,
    exc: Exception,
    log_full_traceback: bool = True
) -> JSONResponse:
    """
    Handle any exception securely.
    
    Args:
        request: The request that caused the exception
        exc: The exception
        log_full_traceback: Whether to log full traceback
        
    Returns:
        Secure JSONResponse
    """
    if isinstance(exc, SecureHTTPException):
        exc.log(request)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.status_code, "message": exc.client_message}}
        )
    
    if isinstance(exc, HTTPException):
        # Convert regular HTTPException to secure response
        status_code = exc.status_code
        message = GENERIC_ERROR_MESSAGES.get(status_code, "An error occurred")
        
        # Log the actual error
        error_logger.error(
            f"HTTPException: {exc.detail}",
            extra={
                "status_code": status_code,
                "client_host": request.client.host if request.client else None,
                "method": request.method,
                "url": str(request.url),
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": status_code, "message": message}}
        )
    
    # Handle unexpected exceptions
    # Log full details
    error_logger.critical(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "client_host": request.client.host if request.client else None,
            "method": request.method,
            "url": str(request.url),
            "traceback": traceback.format_exc() if log_full_traceback else None,
        }
    )
    
    # Return generic 500 error
    return get_secure_error_response(500, exc, request)


# =============================================================================
# FASTAPI EXCEPTION HANDLERS
# =============================================================================

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPExceptions securely."""
    return handle_exception(request, exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions securely."""
    return handle_exception(request, exc)


def setup_exception_handlers(app):
    """
    Setup secure exception handlers for FastAPI app.
    
    Usage:
        from fastapi import FastAPI
        from error_handlers import setup_exception_handlers
        
        app = FastAPI()
        setup_exception_handlers(app)
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


# =============================================================================
# VALIDATION ERROR HANDLER
# =============================================================================

async def validation_error_handler(request: Request, exc) -> JSONResponse:
    """
    Handle Pydantic validation errors securely.
    
    Removes field paths that might reveal internal structure.
    """
    errors = []
    
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            # Only expose field name and error message, not full path
            field = error.get('loc', ['unknown'])[-1] if error.get('loc') else 'unknown'
            msg = error.get('msg', 'Validation error')
            
            errors.append({
                "field": str(field),
                "message": msg
            })
    
    # Log full validation error
    error_logger.warning(
        f"Validation error: {exc}",
        extra={
            "client_host": request.client.host if request.client else None,
            "url": str(request.url),
            "errors": errors,
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": errors
            }
        }
    )
