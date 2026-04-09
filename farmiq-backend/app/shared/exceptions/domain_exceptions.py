"""
Domain-level Exceptions
Pure business logic errors - no HTTP status codes here
"""


class DomainException(Exception):
    """Base exception for all domain errors"""
    pass


class ValidationError(DomainException):
    """Data validation failed"""
    pass


class EntityNotFoundError(DomainException):
    """Expected entity was not found"""
    def __init__(self, entity_type: str, entity_id: str | int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class InvalidStateError(DomainException):
    """Entity is in an invalid state for the requested operation"""
    pass


class InsufficientDataError(DomainException):
    """Not enough data to perform the requested operation"""
    pass


class ModelNotAvailableError(DomainException):
    """ML model is not available or not loaded"""
    pass


class CalculationError(DomainException):
    """Error during business logic calculation"""
    pass
