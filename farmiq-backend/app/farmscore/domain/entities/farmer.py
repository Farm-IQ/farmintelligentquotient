"""
Farmer Domain Entity
Pure business logic for farmer domain
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.shared import BaseEntity, validate_not_empty, validate_positive


@dataclass
class Farmer(BaseEntity):
    """
    Farmer domain entity
    Represents a farmer with profiles and attributes
    """
    user_id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    farm_size_acres: float = 1.0
    years_farming: int = 1
    crop_types: List[str] = field(default_factory=list)
    livestock_types: List[str] = field(default_factory=list)
    coop_membership_years: int = 0
    training_hours: int = 0
    
    def __post_init__(self):
        """Validate farmer data"""
        validate_not_empty(self.user_id, "user_id")
        validate_not_empty(self.first_name, "first_name")
        validate_not_empty(self.last_name, "last_name")
        validate_positive(self.farm_size_acres, "farm_size_acres")
        validate_positive(self.years_farming, "years_farming")
    
    def get_full_name(self) -> str:
        """Get farmer's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def add_crop(self, crop_type: str) -> None:
        """Add crop type to farmer's crops"""
        if crop_type not in self.crop_types:
            self.crop_types.append(crop_type)
            self.mark_as_updated()
    
    def add_livestock(self, livestock_type: str) -> None:
        """Add livestock type to farmer's livestock"""
        if livestock_type not in self.livestock_types:
            self.livestock_types.append(livestock_type)
            self.mark_as_updated()
    
    def update_farm_info(
        self,
        farm_size_acres: Optional[float] = None,
        years_farming: Optional[int] = None
    ) -> None:
        """Update farm information"""
        if farm_size_acres is not None:
            validate_positive(farm_size_acres, "farm_size_acres")
            self.farm_size_acres = farm_size_acres
        
        if years_farming is not None:
            validate_positive(years_farming, "years_farming")
            self.years_farming = years_farming
        
        self.mark_as_updated()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'user_id': self.user_id,
            'full_name': self.get_full_name(),
            'email': self.email,
            'phone': self.phone,
            'farm_size_acres': self.farm_size_acres,
            'years_farming': self.years_farming,
            'crop_types': self.crop_types,
            'livestock_types': self.livestock_types,
        })
        return base_dict
