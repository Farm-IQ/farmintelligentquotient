"""
FarmScore ML Predictors
Consolidated credit scoring and loan recommendation models

Models:
- CreditScorer: Ensemble classifier for default probability prediction
- CreditRecommendationEngine: Dynamic loan recommendation and structuring
"""

from app.farmscore.ml.predictors.credit_model import (
    CreditScorer,
    CreditRecommendationEngine,
)

__all__ = [
    "CreditScorer",
    "CreditRecommendationEngine",
]
