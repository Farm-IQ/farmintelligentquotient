"""
Credit Score Domain Entity
Pure business logic for credit scoring
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID
from app.shared import BaseEntity, validate_range, validate_positive, validate_non_negative


class CreditRiskLevel(str, Enum):
    """Credit risk levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class CreditScore(BaseEntity):
    """
    Credit Score domain entity
    Represents a farmer's credit score assessment
    """
    farmer_id: UUID = None
    user_id: str = ""
    score: float = 0.0  # 0-100
    risk_level: CreditRiskLevel = CreditRiskLevel.MEDIUM
    default_probability: float = 0.5  # 0-1
    approval_likelihood: float = 0.5  # 0-1
    recommended_credit_limit_kes: float = 0.0
    recommended_loan_term_months: int = 12
    recommended_interest_rate: float = 0.0
    shap_explanation: Dict[str, Any] = field(default_factory=dict)
    improvement_recommendations: list = field(default_factory=list)
    model_version: str = "1.0"
    cache_ttl_days: int = 90
    
    def __post_init__(self):
        """Validate credit score data"""
        validate_range(self.score, 0.0, 100.0, "credit score")
        validate_range(self.default_probability, 0.0, 1.0, "default probability")
        validate_range(self.approval_likelihood, 0.0, 1.0, "approval likelihood")
        validate_positive(self.recommended_credit_limit_kes, "credit limit")
        validate_positive(self.recommended_loan_term_months, "loan term")
        validate_non_negative(self.recommended_interest_rate, "interest rate")
    
    def is_cache_valid(self) -> bool:
        """Check if cached score is still valid"""
        age_days = (datetime.utcnow() - self.updated_at).days
        return age_days <= self.cache_ttl_days
    
    def is_eligible_for_loan(self) -> bool:
        """Determine if farmer is eligible for loan"""
        return (
            self.risk_level != CreditRiskLevel.VERY_HIGH and
            self.approval_likelihood > 0.5 and
            self.score > 40
        )
    
    def get_risk_category(self) -> str:
        """Get human-readable risk category"""
        risk_descriptions = {
            CreditRiskLevel.VERY_LOW: "Excellent credit profile",
            CreditRiskLevel.LOW: "Good credit profile",
            CreditRiskLevel.MEDIUM: "Acceptable credit profile",
            CreditRiskLevel.HIGH: "Risky credit profile",
            CreditRiskLevel.VERY_HIGH: "Very risky credit profile",
        }
        return risk_descriptions.get(self.risk_level, "Unknown")
    
    def get_top_improvements(self, limit: int = 3) -> list:
        """Get top improvement recommendations"""
        return self.improvement_recommendations[:limit]
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'farmer_id': str(self.farmer_id),
            'user_id': self.user_id,
            'score': self.score,
            'risk_level': self.risk_level.value,
            'risk_category': self.get_risk_category(),
            'default_probability': self.default_probability,
            'approval_likelihood': self.approval_likelihood,
            'recommended_credit_limit_kes': self.recommended_credit_limit_kes,
            'recommended_loan_term_months': self.recommended_loan_term_months,
            'recommended_interest_rate': self.recommended_interest_rate,
            'is_eligible_for_loan': self.is_eligible_for_loan(),
            'is_cache_valid': self.is_cache_valid(),
        })
        return base_dict
