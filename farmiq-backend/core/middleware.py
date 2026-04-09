"""
FarmIQ Security - Middleware Components
Security headers, rate limiting, request ID tracking, and audit logging
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import logging
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST ID MIDDLEWARE
# ============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds unique X-Request-ID header to all requests and responses
    Enables request tracing across logs
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        # Get or generate request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        
        # Add to request state for use in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds essential security headers to all responses
    Protects against XSS, clickjacking, MIME sniffing, etc.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy - allow ReDoc and Swagger UI CDN for documentation
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://cdn.redoc.ly; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # For HTTPS environments (add in production config)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# ============================================================================
# AUDIT LOGGING MIDDLEWARE
# ============================================================================

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all requests and responses for audit trail
    Tracks authentication, authorization, and sensitive operations
    """
    
    # Paths that don't need full logging (noisy)
    EXEMPT_PATHS = {"/health", "/readiness", "/liveness", "/docs", "/openapi.json"}
    
    # Sensitive fields to redact in logs
    REDACT_FIELDS = {"password", "token", "secret", "apikey", "x-farmiq-id"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        # Skip logging for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        start_time = datetime.utcnow()
        
        # Capture request details
        request_log = {
            "request_id": request_id,
            "timestamp": start_time.isoformat() + "Z",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "user": request.headers.get("x-farmiq-id", "unknown"),
            "ip": request.client.host if request.client else "unknown",
        }
        
        try:
            # Process request
            response = await call_next(request)
            
            # Capture response details
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            audit_log = {
                **request_log,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
            
            # Log based on status code
            if response.status_code >= 500:
                logger.error("Server error", extra=audit_log)
            elif response.status_code >= 400:
                logger.warning("Client error", extra=audit_log)
            else:
                logger.info("Request processed", extra=audit_log)
            
            return response
            
        except Exception as e:
            # Log exceptions
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            error_log = {
                **request_log,
                "error": str(e),
                "duration_ms": duration_ms,
            }
            logger.error("Request failed", extra=error_log, exc_info=True)
            raise


# ============================================================================
# RATE LIMITER (In-Memory for Single Instance)
# ============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter
    For distributed systems, use Redis-based rate limiting (slowapi with Redis backend)
    """
    
    def __init__(self):
        # Format: {identifier: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_rate_limited(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is rate limited.
        
        Args:
            identifier: Unique identifier (user_id, ip, etc.)
            max_requests: Max requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            (is_limited, retry_after_seconds)
        """
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Remove old requests outside window
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
            
            # Check if limited
            if len(self.requests[identifier]) >= max_requests:
                # Calculate retry_after
                oldest_request = self.requests[identifier][0]
                retry_after = window_seconds - int((now - oldest_request).total_seconds())
                return True, max(1, retry_after)
            
            # Add current request
            self.requests[identifier].append(now)
            return False, None


# Global rate limiter instance
_rate_limiter = RateLimiter()


async def check_rate_limit(
    identifier: str,
    max_requests: int = 100,
    window_seconds: int = 60,
) -> Optional[int]:
    """
    Check rate limit for identifier.
    
    Returns:
        None if allowed, or retry_after seconds if limited
    """
    is_limited, retry_after = await _rate_limiter.is_rate_limited(
        identifier, max_requests, window_seconds
    )
    return retry_after if is_limited else None


# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================

class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting by IP address
    100 requests per minute per IP
    """
    
    EXEMPT_PATHS = {"/health", "/readiness", "/liveness"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        # Skip for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit (100 requests per 60 seconds)
        retry_after = await check_rate_limit(
            f"ip:{client_ip}",
            max_requests=100,
            window_seconds=60,
        )
        
        if retry_after:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": retry_after,
                    }
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        return await call_next(request)


# ============================================================================
# PER-ENDPOINT RATE LIMITING (for use with FastAPI dependency)
# ============================================================================

async def rate_limit_by_farm(
    farm_id: str,
    max_requests: int = 10,
    window_seconds: int = 60,
) -> Optional[int]:
    """
    Rate limit by farm ID
    Default: 10 requests per minute per farm (for expensive ML operations)
    Returns retry_after if limited, None if allowed
    """
    return await check_rate_limit(
        f"farm:{farm_id}",
        max_requests=max_requests,
        window_seconds=window_seconds,
    )


async def rate_limit_by_user(
    user_id: str,
    max_requests: int = 1000,
    window_seconds: int = 60,
) -> Optional[int]:
    """
    Rate limit by user ID
    Default: 1000 requests per minute per user
    Returns retry_after if limited, None if allowed
    """
    return await check_rate_limit(
        f"user:{user_id}",
        max_requests=max_requests,
        window_seconds=window_seconds,
    )
