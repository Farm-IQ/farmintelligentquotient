"""
Base Repository for Data Access Layer
Provides common CRUD patterns
"""

import logging
from typing import TypeVar, Generic, Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from uuid import UUID

from app.shared.exceptions import EntityNotFoundError, CalculationError

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Base repository class for all data repositories
    Provides common CRUD operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID | str | int) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[Tuple[str, str]] = None
    ) -> List[T]:
        """List entities with optional filtering"""
        pass
    
    @abstractmethod
    async def update(self, entity_id: UUID | str | int, data: Dict[str, Any]) -> T:
        """Update entity"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID | str | int) -> bool:
        """Delete entity"""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters"""
        pass
    
    async def get_by_id_or_raise(self, entity_id: UUID | str | int) -> T:
        """Get entity by ID, raise if not found"""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(self.__class__.__name__, entity_id)
        return entity
    
    async def exists(self, entity_id: UUID | str | int) -> bool:
        """Check if entity exists"""
        entity = await self.get_by_id(entity_id)
        return entity is not None
    
    def safe_query(
        self,
        operation_name: str,
        func,
        *args,
        **kwargs
    ):
        """
        Safely execute a query with error handling
        
        Args:
            operation_name: Name of operation for logging
            func: Query function to execute
            
        Returns:
            Result of query
            
        Raises:
            CalculationError: If query fails
        """
        try:
            self.logger.debug(f"Executing query: {operation_name}")
            result = func(*args, **kwargs)
            return result
        except EntityNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Query error in {operation_name}: {str(e)}")
            raise CalculationError(f"Database query failed: {str(e)}")
