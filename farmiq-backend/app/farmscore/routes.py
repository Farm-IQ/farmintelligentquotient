"""
FarmScore Credit Scoring API - Main Router
Modularized FastAPI routes for credit scoring, loan applications, and analysis

Includes all credit scoring endpoints:
- POST /api/v1/farmscore/score - Calculate credit score with ensemble model
- POST /api/v1/farmscore/loan/apply - Apply for loan with risk assessment
- POST /api/v1/farmscore/loan/simulate - Simulate loan repayment scenarios
- GET /api/v1/farmscore/score/{user_id} - Retrieve cached credit score

Features:
- Gradient Boosting + Random Forest + Logistic Regression ensemble
- 20+ engineered credit features
- Probability calibration for reliable estimates
- Dynamic loan recommendations with interest rate structuring
- Repayment capacity analysis
- 90-day caching for performance
"""

from fastapi import APIRouter

# Import credit scoring router from v4.0 refactored API
from app.farmscore.api.routes.credit_scoring import router as credit_scoring_router

# Create main FarmScore router
router = APIRouter(prefix="/api/v1/farmscore", tags=["FarmScore Credit"])

# Include credit scoring router (v4.0 - uses layered architecture)
router.include_router(credit_scoring_router)

__all__ = ["router"]
