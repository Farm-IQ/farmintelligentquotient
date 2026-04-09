"""
Base Entity for Domain-Driven Design
All domain entities inherit from this class
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class BaseEntity:
    """
    Base class for all domain entities
    Provides common attributes and behavior
    """
    
    id: Optional[UUID] = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = field(default=True)
    
    def __eq__(self, other):
        """Entities are equal if they have the same ID"""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id
    
    def __hash__(self):
        """Hash based on ID"""
        return hash(self.id)
    
    def mark_as_updated(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Soft delete by deactivating"""
        self.is_active = False
        self.mark_as_updated()
    
    def activate(self):
        """Reactivate a deactivated entity"""
        self.is_active = True
        self.mark_as_updated()
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
        }
