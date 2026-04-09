"""
Application-level Exception Handlers
Maps domain exceptions to HTTP response codes
"""

from fastapi import HTTPException, status


class ApplicationException(HTTPException):
    """Base application exception with HTTP mapping"""
    def __init__(self, detail: str, status_code: int):
        super().__init__(status_code=status_code, detail=detail)


class BadRequestException(ApplicationException):
    """400 Bad Request"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(ApplicationException):
    """401 Unauthorized"""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(ApplicationException):
    """403 Forbidden"""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(ApplicationException):
    """404 Not Found"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(ApplicationException):
    """409 Conflict"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class UnprocessableEntityException(ApplicationException):
    """422 Unprocessable Entity"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class InternalServerErrorException(ApplicationException):
    """500 Internal Server Error"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServiceUnavailableException(ApplicationException):
    """503 Service Unavailable"""
    def __init__(self, detail: str = "Service unavailable"):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def map_domain_exception_to_http(exc: Exception) -> HTTPException:
    """Map domain exceptions to HTTP exceptions"""
    from app.shared.exceptions.domain_exceptions import (
        DomainException, ValidationError, EntityNotFoundError,
        InvalidStateError, InsufficientDataError, ModelNotAvailableError,
        CalculationError
    )
    
    if isinstance(exc, ValidationError):
        return BadRequestException(str(exc))
    elif isinstance(exc, EntityNotFoundError):
        return NotFoundException(str(exc))
    elif isinstance(exc, InvalidStateError):
        return ConflictException(str(exc))
    elif isinstance(exc, InsufficientDataError):
        return UnprocessableEntityException(str(exc))
    elif isinstance(exc, ModelNotAvailableError):
        return ServiceUnavailableException(str(exc))
    elif isinstance(exc, CalculationError):
        return InternalServerErrorException(str(exc))
    elif isinstance(exc, DomainException):
        return InternalServerErrorException(str(exc))
    
    return InternalServerErrorException("An unexpected error occurred")
