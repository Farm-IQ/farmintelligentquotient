"""
Prediction Domain Entity
Represents farm intelligence predictions
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID
from app.shared import BaseEntity, validate_range, validate_not_empty


class PredictionType(str, Enum):
    """Types of predictions"""
    YIELD = "yield"
    PRODUCTION = "production"
    EXPENSES = "expenses"
    DISEASE_RISK = "disease_risk"
    MARKET_PRICE = "market_price"
    ROI = "roi"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Prediction(BaseEntity):
    """
    Prediction domain entity
    Represents farm intelligence predictions with confidence scores
    """
    farm_id: UUID = None
    user_id: str = ""
    prediction_type: PredictionType = PredictionType.YIELD
    subject: str = ""  # What is being predicted (crop name, expense category, etc)
    predicted_value: float = 0.0
    predicted_unit: str = ""
    confidence: float = 0.5  # 0-1
    prediction_period_start: datetime = field(default_factory=datetime.utcnow)
    prediction_period_end: datetime = field(default_factory=datetime.utcnow)
    model_version: str = ""
    factors: List[str] = field(default_factory=list)  # Key factors influencing prediction
    recommendations: List[str] = field(default_factory=list)  # Actionable recommendations
    actual_value: Optional[float] = None  # Set after period ends
    error_margin: Optional[float] = None  # ±% accuracy range
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate prediction data"""
        validate_not_empty(self.subject, "subject")
        validate_range(self.confidence, 0, 1, "confidence")
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Convert confidence score to level"""
        if self.confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def get_confidence_category(self) -> str:
        """Get human-readable confidence category"""
        level = self.get_confidence_level()
        descriptions = {
            ConfidenceLevel.HIGH: "Very confident in this prediction",
            ConfidenceLevel.MEDIUM: "Moderately confident in this prediction",
            ConfidenceLevel.LOW: "Low confidence - use with caution",
        }
        return descriptions.get(level, "Unknown confidence")
    
    def is_prediction_accurate(self, tolerance_percent: float = 10) -> Optional[bool]:
        """Check if prediction was accurate after actual value is known"""
        if self.actual_value is None:
            return None
        
        percent_error = abs(self.predicted_value - self.actual_value) / self.predicted_value * 100
        return percent_error <= tolerance_percent
    
    def get_prediction_error(self) -> Optional[float]:
        """Calculate prediction error percentage"""
        if self.actual_value is None:
            return None
        
        return abs(self.predicted_value - self.actual_value) / self.predicted_value * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'farm_id': str(self.farm_id),
            'user_id': self.user_id,
            'prediction_type': self.prediction_type.value,
            'subject': self.subject,
            'predicted_value': self.predicted_value,
            'confidence_level': self.get_confidence_level().value,
            'confidence_category': self.get_confidence_category(),
            'is_accurate': self.is_prediction_accurate(),
            'prediction_error': self.get_prediction_error(),
        })
        return base_dict
