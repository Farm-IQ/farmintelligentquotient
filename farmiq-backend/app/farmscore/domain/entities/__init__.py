"""
FarmScore Domain Entities
Represents core business concepts
"""

from app.farmscore.domain.entities.farmer import Farmer
from app.farmscore.domain.entities.credit_score import CreditScore, CreditRiskLevel

__all__ = [
    "Farmer",
    "CreditScore",
    "CreditRiskLevel",
]
