"""
FarmSuite Farm Intelligence API - Main Router (v4.0 Refactored)
================================================================================

Comprehensive FastAPI routes for farm intelligence, predictions, and management

Endpoint Categories (all use v4.0 layered architecture):

FARM ANALYSIS:
- GET  /api/v1/farmsuite/farms/{farm_id} - Farm profile
- GET  /api/v1/farmsuite/farms - List farms
- GET  /api/v1/farmsuite/farm/{farm_id}/dashboard - Farm dashboard

PRODUCTION INTELLIGENCE:
- GET  /api/v1/farmsuite/farm/{farm_id}/production/metrics - Production metrics
- POST /api/v1/farmsuite/farm/{farm_id}/production/efficiency - Efficiency analysis
- POST /api/v1/farmsuite/farm/{farm_id}/production/nutrient-budget - Nutrient budget
- POST /api/v1/farmsuite/farm/{farm_id}/production/water-planning - Water planning

PREDICTIONS:
- POST /api/v1/farmsuite/predict/yield - Yield prediction
- POST /api/v1/farmsuite/predict/expenses - Expense forecast
- POST /api/v1/farmsuite/predict/disease-risk - Disease risk assessment
- POST /api/v1/farmsuite/predict/market-price - Market price prediction
- POST /api/v1/farmsuite/predict/roi-optimization - ROI optimization

RISK MANAGEMENT:
- POST /api/v1/farmsuite/farm/{farm_id}/risk/assessment - Comprehensive risk assessment
- GET  /api/v1/farmsuite/farm/{farm_id}/risk/critical - Critical risk identification
- POST /api/v1/farmsuite/farm/{farm_id}/risk/mitigation - Mitigation strategies

MARKET INTELLIGENCE:
- POST /api/v1/farmsuite/farm/{farm_id}/market/opportunities - Market opportunities
- POST /api/v1/farmsuite/farm/{farm_id}/market/buyer-analysis - Buyer analysis
- POST /api/v1/farmsuite/farm/{farm_id}/market/quality-premium - Quality premium analysis
- POST /api/v1/farmsuite/farm/{farm_id}/market/pricing-strategy - Pricing strategy

WORKER MANAGEMENT:
- GET  /api/v1/farmsuite/farm/{farm_id}/workers/performance - Worker performance
- POST /api/v1/farmsuite/farm/{farm_id}/workers/recommendations - Worker optimization
- POST /api/v1/farmsuite/farm/{farm_id}/workers/training-needs - Training needs assessment
"""

from fastapi import APIRouter

# Import v4.0 refactored API routes
from app.farmsuite.api.routes import (
    farm_analysis,
    predictions,
    risks,
    markets,
    workers,
    production,
)

# Create main FarmSuite router
router = APIRouter()

# Include all modular route handlers
router.include_router(farm_analysis.router)
router.include_router(predictions.router)
router.include_router(risks.router)
router.include_router(markets.router)
router.include_router(workers.router)
router.include_router(production.router)

__all__ = ["router"]
