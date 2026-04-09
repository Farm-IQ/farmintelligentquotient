"""
FarmScore Repositories
Data access layer
"""

from app.farmscore.application.repositories.farmer_repository import FarmerRepository
from app.farmscore.application.repositories.credit_score_repository import CreditScoreRepository

__all__ = [
    "FarmerRepository",
    "CreditScoreRepository",
]
