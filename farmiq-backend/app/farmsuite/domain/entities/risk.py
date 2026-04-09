"""
Risk Domain Entity
Represents identified risks for a farm
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID
from app.shared import BaseEntity, validate_range, validate_not_empty


class RiskCategory(str, Enum):
    """Categories of farm risks"""
    PEST = "pest"
    DISEASE = "disease"
    WEATHER = "weather"
    MARKET = "market"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Risk(BaseEntity):
    """
    Risk domain entity
    Represents identified risks and their mitigation strategies
    """
    farm_id: UUID = None
    user_id: str = ""
    risk_category: RiskCategory = RiskCategory.PEST
    risk_name: str = ""  # Specific risk identifier
    risk_probability: float = 0.0  # 0-1, likelihood of occurrence
    risk_severity_if_occurs: float = 0.0  # 0-1, impact if it happens
    risk_score: float = 0.0  # Combined probability * severity
    current_pressure: float = 0.0  # 0-1, current detected pressure level (pest count, disease % etc)
    vulnerability_index: float = 0.0  # 0-1, farm's vulnerability to this risk
    affected_crops: List[str] = field(default_factory=list)
    affected_area_acres: Optional[float] = None
    mitigation_strategies: List[str] = field(default_factory=list)
    early_warning_indicators: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    monitoring_frequency_days: Optional[int] = None  # How often to check
    estimated_loss_if_occurs: Optional[float] = None  # In KES
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate risk data"""
        validate_not_empty(self.risk_name, "risk_name")
        validate_range(self.risk_probability, 0, 1, "risk_probability")
        validate_range(self.risk_severity_if_occurs, 0, 1, "risk_severity_if_occurs")
        validate_range(self.risk_score, 0, 1, "risk_score")
        validate_range(self.current_pressure, 0, 1, "current_pressure")
        validate_range(self.vulnerability_index, 0, 1, "vulnerability_index")
    
    def calculate_risk_score(self) -> float:
        """Calculate composite risk score"""
        # Risk Score = Probability × Severity × Vulnerability × Pressure
        # Pressure as a modifier (if high pressure, risk is more imminent)
        pressure_modifier = 1 + (self.current_pressure * 0.5)
        calculated_score = (
            self.risk_probability * 
            self.risk_severity_if_occurs * 
            self.vulnerability_index * 
            pressure_modifier
        )
        return min(calculated_score, 1.0)  # Cap at 1.0
    
    def get_severity_level(self) -> RiskSeverity:
        """Get severity level based on risk score"""
        if self.risk_score >= 0.75:
            return RiskSeverity.CRITICAL
        elif self.risk_score >= 0.5:
            return RiskSeverity.HIGH
        elif self.risk_score >= 0.25:
            return RiskSeverity.MEDIUM
        else:
            return RiskSeverity.LOW
    
    def is_critical(self) -> bool:
        """Check if risk is critical"""
        return self.get_severity_level() == RiskSeverity.CRITICAL
    
    def is_high_priority(self) -> bool:
        """Check if risk requires immediate attention"""
        return self.current_pressure > 0.5 or self.risk_score > 0.6
    
    def get_urgency_message(self) -> str:
        """Get human-readable urgency message"""
        severity = self.get_severity_level()
        messages = {
            RiskSeverity.CRITICAL: f"⚠️  CRITICAL: {self.risk_name} requires immediate action",
            RiskSeverity.HIGH: f"⚠️  HIGH: {self.risk_name} should be monitored closely",
            RiskSeverity.MEDIUM: f"ℹ️  MEDIUM: {self.risk_name} warrants preventive measures",
            RiskSeverity.LOW: f"✓ LOW: {self.risk_name} is low priority",
        }
        return messages.get(severity, "Unknown risk level")
    
    def get_next_monitoring_date(self, from_date: 'datetime') -> 'datetime':
        """Calculate next recommended monitoring date"""
        from datetime import timedelta
        if self.monitoring_frequency_days is None:
            # Default based on severity
            severity = self.get_severity_level()
            freq_map = {
                RiskSeverity.CRITICAL: 1,
                RiskSeverity.HIGH: 3,
                RiskSeverity.MEDIUM: 7,
                RiskSeverity.LOW: 14,
            }
            freq = freq_map.get(severity, 14)
        else:
            freq = self.monitoring_frequency_days
        
        return from_date + timedelta(days=freq)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'farm_id': str(self.farm_id),
            'user_id': self.user_id,
            'risk_category': self.risk_category.value,
            'risk_severity_level': self.get_severity_level().value,
            'is_critical': self.is_critical(),
            'is_high_priority': self.is_high_priority(),
            'urgency_message': self.get_urgency_message(),
        })
        return base_dict
