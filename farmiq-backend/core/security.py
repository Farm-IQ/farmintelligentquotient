"""
FarmIQ Security Comprehensive Module
Combines Phase 3 input validation with Phase 5 exception handling
- Input validation (SQL injection, XSS, file security)
- Standardized error handling and exception classes
- Security response formatting
"""
import re
import hashlib
import time
from typing import Optional, Dict, Set, Any
from datetime import datetime, timedelta
from functools import wraps
from uuid import UUID
import logging
import json

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SQLInjectionValidator:
    """
    Detect and prevent SQL injection attacks.
    
    Strategies:
    1. Pattern matching for common SQL injection attempts
    2. Length validation
    3. Character whitelist checking
    """
    
    # SQL injection patterns to detect
    DANGEROUS_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(-{2}|;|\'|\")",  # SQL comments and quotes
        r"(OR\s+1=1|OR\s+\'1\'=\'1)",  # Boolean-based injection
        r"(CASE\s+WHEN|IF\s*\(|IIF\s*\()",  # Conditional injection
    ]
    
    # Safe characters for agricultural data
    SAFE_CHAR_PATTERN = r"^[a-zA-Z0-9\s\.,\-\(\)_%]+$"
    
    @staticmethod
    def is_safe(value: str, context: str = "general") -> bool:
        """
        Check if value is safe from SQL injection.
        
        Args:
            value: Input string to validate
            context: Context type (general, text, id, number)
            
        Returns:
            True if safe, False if suspicious
        """
        if not isinstance(value, str):
            return True
        
        # Length check
        if len(value) > 10000:
            logger.warning(f"Input exceeds length limit: {len(value)}")
            return False
        
        # Check for dangerous patterns
        for pattern in SQLInjectionValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return False
        
        # Context-specific checks
        if context == "id":
            # IDs should be alphanumeric + underscore only
            return re.match(r"^[a-zA-Z0-9_\-]+$", value) is not None
        
        elif context == "number":
            # Numbers should only contain digits and decimal point
            return re.match(r"^[\d\.]+$", value) is not None
        
        elif context == "email":
            # Basic email validation
            return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value) is not None
        
        return True


class XSSProtector:
    """
    Prevent Cross-Site Scripting (XSS) attacks.
    
    Strategies:
    1. HTML entity encoding
    2. Script tag detection
    3. Event handler detection
    4. JavaScript protocol detection
    """
    
    # Dangerous HTML tags and attributes
    DANGEROUS_TAGS = {
        "script", "iframe", "object", "embed", "link", "meta", "style"
    }
    
    DANGEROUS_ATTRIBUTES = {
        "onload", "onerror", "onclick", "onmouseover", "onchange",
        "onsubmit", "onkeydown", "onkeyup", "onmousemove", "ondblclick",
        "onfocus", "onblur", "javascript:"
    }
    
    @staticmethod
    def is_safe(value: str) -> bool:
        """
        Check if value is safe from XSS.
        
        Args:
            value: Input string to validate
            
        Returns:
            True if safe, False if suspicious
        """
        if not isinstance(value, str):
            return True
        
        # Check for script tags
        if re.search(r"<script[^>]*>.*?</script>", value, re.IGNORECASE | re.DOTALL):
            logger.warning("XSS: Script tag detected")
            return False
        
        # Check for event handlers
        for attr in XSSProtector.DANGEROUS_ATTRIBUTES:
            if re.search(rf"{attr}\s*=", value, re.IGNORECASE):
                logger.warning(f"XSS: Event handler detected: {attr}")
                return False
        
        # Check for dangerous tags
        for tag in XSSProtector.DANGEROUS_TAGS:
            if re.search(rf"<{tag}[^>]*>", value, re.IGNORECASE):
                logger.warning(f"XSS: Dangerous tag detected: {tag}")
                return False
        
        # Check for data URIs
        if re.search(r"data:[^,]*,", value):
            logger.warning("XSS: Data URI detected")
            return False
        
        return True
    
    @staticmethod
    def sanitize(value: str) -> str:
        """
        Sanitize string by removing/escaping dangerous content.
        
        Args:
            value: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value
        
        # HTML entity encoding for dangerous characters
        replacements = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "&": "&amp;",
        }
        
        for char, entity in replacements.items():
            value = value.replace(char, entity)
        
        return value


class RateLimiter:
    """
    Rate limiting to prevent brute force and DoS attacks.
    
    Strategies:
    1. Per-user rate limiting
    2. Per-IP rate limiting
    3. Global rate limiting
    4. Sliding window algorithm
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}  # {key: [timestamps]}
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier (user_id, IP address, etc.)
            
        Returns:
            True if request allowed, False if rate limited
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside window
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > window_start
        ]
        
        # Check if within limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for: {identifier}")
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        now = time.time()
        window_start = now - self.window_seconds
        
        if identifier not in self.requests:
            return self.max_requests
        
        valid_requests = len([
            ts for ts in self.requests[identifier]
            if ts > window_start
        ])
        
        return max(0, self.max_requests - valid_requests)
    
    def cleanup_old_entries(self):
        """Remove old entries to prevent memory leak."""
        now = time.time()
        window_start = now - self.window_seconds
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                ts for ts in self.requests[identifier]
                if ts > window_start
            ]
            
            # Remove if empty
            if not self.requests[identifier]:
                del self.requests[identifier]


class InputValidator:
    """
    Comprehensive input validation for all API inputs.
    """
    
    @staticmethod
    def validate_string(
        value: str,
        min_length: int = 1,
        max_length: int = 10000,
        pattern: Optional[str] = None,
        required: bool = True
    ) -> bool:
        """Validate string input."""
        if required and not value:
            return False
        
        if not isinstance(value, str):
            return False
        
        if len(value) < min_length or len(value) > max_length:
            return False
        
        if pattern and not re.match(pattern, value):
            return False
        
        return True
    
    @staticmethod
    def validate_integer(
        value: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        required: bool = True
    ) -> bool:
        """Validate integer input."""
        if required and value is None:
            return False
        
        if not isinstance(value, int):
            return False
        
        if min_value is not None and value < min_value:
            return False
        
        if max_value is not None and value > max_value:
            return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_farmiq_id(farmiq_id: str) -> bool:
        """Validate FarmIQ ID format."""
        # Format: FQ followed by 4 digits
        pattern = r"^FQ\d{4}$"
        return bool(re.match(pattern, farmiq_id.upper()))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format."""
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return bool(re.match(pattern, uuid_str.lower()))


class FileSecurityValidator:
    """
    Validate file uploads for security.
    """
    
    # Allowed MIME types
    ALLOWED_MIMES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".com", ".pif", ".scr",  # Windows executables
        ".sh", ".bash",  # Shell scripts
        ".php", ".jsp", ".asp", ".aspx",  # Server scripts
        ".jar", ".zip", ".rar", ".7z",  # Archives (use extracted content)
    }
    
    # Max file size: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    @staticmethod
    def is_safe_file(
        filename: str,
        file_size: int,
        mime_type: Optional[str] = None
    ) -> bool:
        """
        Check if file is safe.
        
        Args:
            filename: Original filename
            file_size: File size in bytes
            mime_type: MIME type (optional)
            
        Returns:
            True if safe, False if suspicious
        """
        # Check file extension
        for ext in FileSecurityValidator.DANGEROUS_EXTENSIONS:
            if filename.lower().endswith(ext):
                logger.warning(f"Dangerous file extension: {ext}")
                return False
        
        # Check file size
        if file_size > FileSecurityValidator.MAX_FILE_SIZE:
            logger.warning(f"File exceeds max size: {file_size}")
            return False
        
        # Check MIME type if provided
        if mime_type and mime_type not in FileSecurityValidator.ALLOWED_MIMES:
            logger.warning(f"Disallowed MIME type: {mime_type}")
            return False
        
        return True


# ============================================================================
# STANDARDIZED ERROR RESPONSE MODELS (Phase 5)
# ============================================================================

class ErrorDetail(BaseModel):
    """Standardized error response format"""
    code: str = Field(..., description="Error code (e.g., 'FARM_NOT_FOUND')")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When error occurred")
    request_id: str = Field(..., description="Unique request identifier for tracing")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ErrorResponse(BaseModel):
    """Standard error response wrapper"""
    error: ErrorDetail


# ============================================================================
# ERROR CODE MAPPING (Phase 5)
# ============================================================================

ERROR_CODES = {
    # 400 - Bad Request
    400: ("INVALID_REQUEST", "Invalid request parameters"),
    422: ("VALIDATION_ERROR", "Validation error in request data"),
    
    # 403 - Forbidden
    403: ("FORBIDDEN", "You do not have permission to access this resource"),
    
    # 404 - Not Found
    404: ("NOT_FOUND", "Requested resource not found"),
    
    # 429 - Too Many Requests
    429: ("RATE_LIMIT_EXCEEDED", "Too many requests. Please try again later"),
    
    # 500 - Internal Server Error
    500: ("INTERNAL_ERROR", "An internal server error occurred"),
    
    # 503 - Service Unavailable
    503: ("SERVICE_UNAVAILABLE", "Service temporarily unavailable"),
}


# ============================================================================
# EXCEPTION CLASSES (Phase 5)
# ============================================================================

class FarmIQException(Exception):
    """Base exception for FarmIQ application"""
    
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(FarmIQException):
    """Raised when request validation fails"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(422, "VALIDATION_ERROR", message, details)


class ResourceNotFoundError(FarmIQException):
    """Raised when resource is not found"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found"
        details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(404, "NOT_FOUND", message, details)


class UnauthorizedError(FarmIQException):
    """Raised when user lacks authorization"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(403, "FORBIDDEN", message)


class RateLimitError(FarmIQException):
    """Raised when rate limit exceeded"""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(429, "RATE_LIMIT_EXCEEDED", "Too many requests", 
                        {"retry_after": retry_after})


class ServiceUnavailableError(FarmIQException):
    """Raised when service is unavailable"""
    def __init__(self, service_name: str):
        message = f"{service_name} is temporarily unavailable"
        super().__init__(503, "SERVICE_UNAVAILABLE", message, 
                        {"service": service_name})


# ============================================================================
# ERROR RESPONSE BUILDERS (Phase 5)
# ============================================================================

def build_error_response(
    status_code: int,
    error_code: Optional[str] = None,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
    details: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Build standardized error response.
    
    Args:
        status_code: HTTP status code
        error_code: Error code (defaults from status_code)
        message: Error message (defaults from status_code)
        request_id: Request tracking ID
        details: Additional context
        
    Returns:
        Standardized error response
    """
    import uuid
    
    if not request_id:
        request_id = str(uuid.uuid4())
    
    if error_code is None or message is None:
        default_code, default_message = ERROR_CODES.get(status_code, ("UNKNOWN_ERROR", "An error occurred"))
        error_code = error_code or default_code
        message = message or default_message
    
    return {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "details": details
        }
    }


# ============================================================================
# EXCEPTION HANDLERS (Phase 5 - for FastAPI)
# ============================================================================

async def security_exception_handler(request: Request, exc: FarmIQException) -> JSONResponse:
    """Handle FarmIQ exceptions with secure error messages"""
    import uuid
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    
    # Log the error with full details internally
    logger.error(
        f"Application error: {exc.error_code}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            exc.status_code,
            exc.error_code,
            exc.message,
            request_id,
            exc.details
        ),
        headers={"X-Request-ID": request_id}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with generic error message"""
    import uuid
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    
    # Log the full exception internally for debugging
    logger.error(
        f"Unexpected exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception": str(exc),
        },
        exc_info=True  # Include stack trace
    )
    
    # Return generic error to client (no internal details exposed)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id
        ),
        headers={"X-Request-ID": request_id}
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle Pydantic validation exceptions"""
    import uuid
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    
    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": str(exc),
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Invalid request parameters",
            request_id
        ),
        headers={"X-Request-ID": request_id}
    )


# ============================================================================
# CORS SECURITY CONFIG (Phase 3)
# ============================================================================

class CORSSecurityConfig:
    """CORS security configuration."""
    
    # Allowed origins (configure per environment)
    ALLOWED_ORIGINS = {
        "http://localhost:4200",  # Local development
        "http://localhost:3000",  # Alternative local
    }
    
    # Allowed methods
    ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "OPTIONS"}
    
    # Allowed headers
    ALLOWED_HEADERS = {
        "Content-Type",
        "Authorization",
        "X-FarmIQ-ID",
        "X-Requested-With",
    }
    
    @staticmethod
    def is_allowed_origin(origin: str) -> bool:
        """Check if origin is allowed."""
        return origin in CORSSecurityConfig.ALLOWED_ORIGINS
