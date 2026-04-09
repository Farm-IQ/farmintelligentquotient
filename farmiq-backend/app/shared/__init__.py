"""
Shared Infrastructure and Utilities
Base classes, exceptions, and utilities used across all modules
"""

from app.shared.base import BaseEntity, BaseService, BaseRepository
from app.shared.exceptions import (
    DomainException,
    ValidationError,
    EntityNotFoundError,
    InvalidStateError,
    InsufficientDataError,
    ModelNotAvailableError,
    CalculationError,
    ApplicationException,
    BadRequestException,
    NotFoundException,
    map_domain_exception_to_http,
)
from app.shared import exceptions
from app.shared.exceptions import domain_exceptions
from core.validation import (
    validate_positive,
    validate_not_empty,
    validate_not_none,
    validate_range,
    validate_non_negative,
    validate_email,
    validate_uuid,
    validate_list_not_empty,
)


__all__ = [
    # Base classes
    "BaseEntity",
    "BaseService",
    "BaseRepository",
    # Domain exceptions
    "DomainException",
    "ValidationError",
    "EntityNotFoundError",
    "InvalidStateError",
    "InsufficientDataError",
    "ModelNotAvailableError",
    "CalculationError",
    # Application exceptions
    "ApplicationException",
    "BadRequestException",
    "NotFoundException",
    "map_domain_exception_to_http",
    # Exception modules
    "exceptions",
    "domain_exceptions",
    # Validation functions
    "validate_positive",
    "validate_not_empty",
    "validate_not_none",
    "validate_range",
    "validate_non_negative",
    "validate_email",
    "validate_uuid",
    "validate_list_not_empty",
]
