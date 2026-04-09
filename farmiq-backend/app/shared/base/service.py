"""
Base Service for Application Layer
Provides common service patterns
"""

import logging
from typing import TypeVar, Generic, Dict, Any, Optional
from abc import ABC, abstractmethod
from app.shared.exceptions import DomainException, ValidationError, CalculationError
from core.validation import (
    validate_not_none,
    validate_not_empty,
    validate_range,
    validate_positive,
    validate_non_negative,
)

# Type variables
T = TypeVar('T')
R = TypeVar('R')


class BaseService(ABC, Generic[T]):
    """
    Base class for all application services
    Provides common patterns and error handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data
        Raise ValidationError if invalid
        """
        pass
    
    def safe_execute(self, operation_name: str, func, *args, **kwargs):
        """
        Safely execute an operation with error logging
        
        Args:
            operation_name: Name of operation for logging
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Result of function execution
            
        Raises:
            CalculationError: If operation fails
        """
        try:
            self.logger.debug(f"Executing {operation_name}")
            result = func(*args, **kwargs)
            self.logger.debug(f"Successfully completed {operation_name}")
            return result
        except DomainException:
            raise
        except Exception as e:
            self.logger.error(f"Error during {operation_name}: {str(e)}")
            raise CalculationError(f"Failed to execute {operation_name}: {str(e)}")
    
    async def safe_execute_async(self, operation_name: str, coro):
        """
        Safely execute async operation with error logging
        
        Args:
            operation_name: Name of operation for logging
            coro: Coroutine to execute
            
        Returns:
            Result of coroutine execution
            
        Raises:
            CalculationError: If operation fails
        """
        try:
            self.logger.debug(f"Executing async {operation_name}")
            result = await coro
            self.logger.debug(f"Successfully completed async {operation_name}")
            return result
        except DomainException:
            raise
        except Exception as e:
            self.logger.error(f"Error during async {operation_name}: {str(e)}")
            raise CalculationError(f"Failed to execute {operation_name}: {str(e)}")
    
    # Validation methods delegated to core.validation
    # These are convenience wrappers for use within services
    
    def validate_not_none(self, value: Any, field_name: str) -> Any:
        """Validate that value is not None (delegates to core.validation)"""
        from core.validation import validate_not_none as core_validate
        return core_validate(value, field_name)
    
    def validate_not_empty(self, value: str, field_name: str, min_length: int = 1) -> str:
        """Validate that string is not empty (delegates to core.validation)"""
        from core.validation import validate_not_empty as core_validate
        return core_validate(value, min_length, field_name)
    
    def validate_range(
        self, 
        value: float | int, 
        min_val: float | int, 
        max_val: float | int,
        field_name: str
    ) -> float | int:
        """Validate that value is within range (delegates to core.validation)"""
        return validate_range(value, min_val, max_val, field_name)
    
    def validate_positive(self, value: float | int, field_name: str) -> float | int:
        """Validate that value is positive (delegates to core.validation)"""
        return validate_positive(value, field_name)
    
    def validate_non_negative(self, value: float | int, field_name: str) -> float | int:
        """Validate that value is non-negative (delegates to core.validation)"""
        return validate_non_negative(value, field_name)
    
    def log_operation(
        self,
        operation: str,
        entity_type: str,
        entity_id: str | int,
        result: str = "success"
    ):
        """Log an operation for audit trail"""
        self.logger.info(
            f"{operation} | Entity: {entity_type} | ID: {entity_id} | Result: {result}"
        )
