"""
Production Domain Entity
Represents crop and livestock production metrics
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID
from app.shared import BaseEntity, validate_positive, validate_non_negative, validate_range


class ProductionType(str, Enum):
    """Type of production"""
    CROP = "crop"
    LIVESTOCK = "livestock"


@dataclass
class Production(BaseEntity):
    """
    Production domain entity
    Tracks actual production outcomes
    """
    farm_id: UUID = None
    user_id: str = ""
    production_type: ProductionType = ProductionType.CROP
    item_name: str = ""  # Crop/livestock type
    quantity_produced: float = 0.0  # kg for crops, units for livestock
    quantity_unit: str = ""  # "kg", "liters", "units", etc
    production_period_start: datetime = field(default_factory=datetime.utcnow)
    production_period_end: datetime = field(default_factory=datetime.utcnow)
    expected_quantity: Optional[float] = None
    input_cost_kes: float = 0.0
    output_value_kes: float = 0.0
    quality_grade: Optional[str] = None  # "A", "B", "C", etc
    yield_per_acre: Optional[float] = None
    losses_percent: float = 0.0  # Pest/disease/weather losses
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate production data"""
        validate_positive(self.quantity_produced, "quantity_produced")
        validate_non_negative(self.input_cost_kes, "input_cost_kes")
        validate_non_negative(self.output_value_kes, "output_value_kes")
        validate_range(self.losses_percent, 0, 100, "losses_percent")
    
    def get_net_income(self) -> float:
        """Calculate net income for this production"""
        return self.output_value_kes - self.input_cost_kes
    
    def get_roi(self) -> float:
        """Calculate return on investment"""
        if self.input_cost_kes <= 0:
            return 0
        return ((self.output_value_kes - self.input_cost_kes) / self.input_cost_kes) * 100
    
    def get_profit_per_unit(self) -> float:
        """Calculate profit per unit produced"""
        if self.quantity_produced <= 0:
            return 0
        return self.get_net_income() / self.quantity_produced
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'farm_id': str(self.farm_id),
            'user_id': self.user_id,
            'production_type': self.production_type.value,
            'item_name': self.item_name,
            'quantity_produced': self.quantity_produced,
            'net_income': self.get_net_income(),
            'roi_percent': self.get_roi(),
            'profit_per_unit': self.get_profit_per_unit(),
        })
        return base_dict
