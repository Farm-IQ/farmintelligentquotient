"""
FarmSuite Intelligence Platform - Core AI/ML Module
===============================================

FarmSuite is the intelligent brain of the FarmIQ backend.
It grows with farmer data and enables predictive farm management.

ARCHITECTURE:
- Pipelines: Data extraction & feature engineering from normalized schema
- ML: Predictive models (yield, expenses, risk scoring, worker productivity)
- Synthetic: Data generation for training models before real farm data
- Services: Data preparation, prediction orchestration, benchmarking
- Routes: FastAPI endpoints for intelligence queries

PHASES:
✅ Phase 1: Data Integration & Feature Engineering
   - Extract data from farm_expenses, farm_income, farm_crops, etc
   - Engineer 50+ features per farm
   - Build temporal sequences for forecasting

✅ Phase 2: Predictive Intelligence & Training
   - Yield forecasting (XGBoost)
   - Expense prediction (Prophet/ARIMA)
   - Disease/pest risk scoring
   - Worker productivity optimization
   - ROI optimization
   - Market price prediction

GROWTH MECHANISM:
- Day 1-30: Individual farm learns baseline
- Month 2-3: Cohort models (5-10 similar farms -> local recommendations)
- Month 4-12: Region models (50+ farms -> predictive patterns)
- Year 2+: Multi-year seasonal patterns captured

SYNTHETIC DATA:
- Generate realistic farm scenarios matching your schema
- Train models before real data accumulates
- A/B test interventions (what if scenarios)
"""

# Core imports
# Note: DataExtractionService and FeatureEngineer are TODO (not yet implemented)
# These will be implemented in Phase 2

from app.farmsuite.ml.training.model_manager import ModelManager

# Domain usable services
from app.farmsuite.domain.services.prediction import PredictionService
from app.farmsuite.domain.services.production_calculation import ProductionCalculationService
from app.farmsuite.domain.services.risk_assessment import RiskAssessmentService

# Models and repositories
from app.farmsuite.ml.predictors.base_models import (
    BasePredictorModel,
    ModelType,
    ModelAlgorithm,
    PredictionResult,
    ModelMetadata,
)

__all__ = [
    # Services
    "ModelManager",
    "PredictionService",
    "ProductionCalculationService",
    "RiskAssessmentService",
    # Models
    "BasePredictorModel",
    "ModelType",
    "ModelAlgorithm",
    "PredictionResult",
    "ModelMetadata",
]
