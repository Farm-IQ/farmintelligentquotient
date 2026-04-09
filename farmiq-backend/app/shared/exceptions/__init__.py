"""
Shared Exception Module
Organized into domain and application exceptions
"""

from app.shared.exceptions.domain_exceptions import (
    DomainException,
    ValidationError,
    EntityNotFoundError,
    InvalidStateError,
    InsufficientDataError,
    ModelNotAvailableError,
    CalculationError,
)

from app.shared.exceptions.application_exceptions import (
    ApplicationException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    UnprocessableEntityException,
    InternalServerErrorException,
    ServiceUnavailableException,
    map_domain_exception_to_http,
)

__all__ = [
    # Domain
    "DomainException",
    "ValidationError",
    "EntityNotFoundError",
    "InvalidStateError",
    "InsufficientDataError",
    "ModelNotAvailableError",
    "CalculationError",
    # Application
    "ApplicationException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "UnprocessableEntityException",
    "InternalServerErrorException",
    "ServiceUnavailableException",
    "map_domain_exception_to_http",
]
