"""
Farm Domain Entity
Core representation of a farm
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.shared import BaseEntity, validate_positive, validate_not_empty


@dataclass
class Farm(BaseEntity):
    """
    Farm domain entity
    Represents a complete farm with all attributes
    """
    # Core farm attributes
    user_id: str = ""
    farm_name: str = ""
    total_acres: float = 0.0
    location: str = ""  # County or region
    # Optional attributes with defaults
    crop_types: List[str] = field(default_factory=list)
    livestock_types: List[str] = field(default_factory=list)
    soil_type: Optional[str] = None
    rainfall_zone: Optional[str] = None
    irrigation_method: Optional[str] = None
    worker_count: int = 0
    equipment_value_kes: float = 0.0
    
    def __post_init__(self):
        """Validate farm data"""
        validate_not_empty(self.user_id, "user_id")
        validate_not_empty(self.farm_name, "farm_name")
        validate_positive(self.total_acres, "total_acres")
    
    def add_crop(self, crop_type: str) -> None:
        """Add crop to farm"""
        if crop_type not in self.crop_types:
            self.crop_types.append(crop_type)
            self.mark_as_updated()
    
    def add_livestock(self, livestock_type: str) -> None:
        """Add livestock to farm"""
        if livestock_type not in self.livestock_types:
            self.livestock_types.append(livestock_type)
            self.mark_as_updated()
    
    def get_diversification_score(self) -> float:
        """Calculate farm diversification (0-1)"""
        total_types = len(self.crop_types) + len(self.livestock_types)
        if total_types == 0:
            return 0.0
        # Max score at 5+ types
        return min(total_types / 5.0, 1.0)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'user_id': self.user_id,
            'farm_name': self.farm_name,
            'total_acres': self.total_acres,
            'location': self.location,
            'crop_types': self.crop_types,
            'livestock_types': self.livestock_types,
            'diversification_score': self.get_diversification_score(),
            'worker_count': self.worker_count,
        })
        return base_dict
