"""
FarmSuite Prediction Service
============================

Service layer for all farm predictions (yield, expenses, disease risk, market price, ROI).
Integrates with Phase 2 ML models and provides intelligent predictions with confidence scoring.

Capabilities:
- Yield prediction with seasonal adjustments
- Expense forecasting with category breakdown
- Disease/pest risk assessment
- Market price predictions
- ROI optimization recommendations
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
import pandas as pd

from app.farmsuite.pipelines.feature_engineering import FeatureEngineer, FeatureSet
from app.farmsuite.ml.training.training_utils import FeaturePreprocessor, FeatureScalingMethod
from app.farmsuite.ml.model_registry import (
    get_model_manager,
    get_model_registry,
    ModelType,
    PredictionMetadata,
)
from app.farmsuite.application.repositories import (
    FarmRepository,
    ProductionRepository,
    PredictionRepository,
    RiskRepository,
    MarketRepository,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES FOR PREDICTIONS
# ============================================================================

@dataclass
class PredictionResult:
    """Generic prediction result wrapper"""
    farm_id: str
    prediction_type: str  # 'yield', 'expense', 'disease', 'price', 'roi'
    predicted_value: float
    confidence_level: float  # 0-1
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    trend: Optional[str] = None  # 'improving', 'stable', 'declining'
    feature_importance: Optional[List[Dict[str, float]]] = None
    recommendations: Optional[List[str]] = None
    predicted_at: datetime = None
    valid_until: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    # SHAP Explainability (like FarmScore)
    shap_explanation: Optional[Dict[str, Any]] = None  # Full SHAP explanation
    shap_top_features: Optional[List[Dict[str, float]]] = None  # Top contributing features with SHAP values
    
    def __post_init__(self):
        if self.predicted_at is None:
            self.predicted_at = datetime.now()
        if self.valid_until is None:
            self.valid_until = datetime.now() + timedelta(days=30)


@dataclass
class ExpenseForecast:
    """Expense forecast with breakdown"""
    farm_id: str
    total_amount: float
    by_category: Dict[str, float]  # input, labor, utilities, transport, etc.
    monthly_breakdown: List[Dict[str, float]]  # [{month: Jan, total: 45000, ...}...]
    variance: float  # Estimated variance
    confidence_level: float
    key_drivers: List[str]  # Top 3 cost drivers
    optimization_tips: List[str]  # Cost reduction suggestions
    forecast_date: datetime = None
    
    def __post_init__(self):
        if self.forecast_date is None:
            self.forecast_date = datetime.now()


@dataclass
class DiseaseRiskAssessment:
    """Disease and pest risk assessment"""
    farm_id: str
    overall_risk_score: float  # 0-100
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    identified_risks: List[Dict[str, Any]]  # [{pathogen, probability, potential_loss_percent}...]
    seasonal_factors: Dict[str, str]
    mitigation_strategies: List[str]
    monitoring_recommendations: List[str]
    assessment_date: datetime = None
    
    # SHAP Explainability (like FarmScore)
    shap_explanation: Optional[Dict[str, Any]] = None  # Full SHAP explanation
    shap_top_factors: Optional[List[Dict[str, float]]] = None  # Top contributing factors
    
    def __post_init__(self):
        if self.assessment_date is None:
            self.assessment_date = datetime.now()


@dataclass
class ROIOptimization:
    """ROI optimization recommendations"""
    farm_id: str
    current_roi_percent: float
    optimized_roi_percent: float
    potential_improvement_percent: float
    recommendations: List[Dict[str, Any]]
    implementation_timeline: List[str]
    required_investment_kes: float
    payback_period_months: float
    
    # SHAP Explainability (feature drivers)
    shap_explanation: Optional[Dict[str, Any]] = None  # Full SHAP explanation from ROI model
    shap_top_factors: Optional[List[Dict[str, float]]] = None  # Top factors influencing ROI improvement
    confidence_level: float = 0.75
    analysis_date: datetime = None
    
    def __post_init__(self):
        if self.analysis_date is None:
            self.analysis_date = datetime.now()


# ============================================================================
# PREDICTION SERVICE
# ============================================================================

class PredictionService:
    """
    Main prediction service orchestrating all ML models and predictions.
    
    Integrates with:
    - FeatureEngineer (Phase 2) for feature generation
    - ML models (Phase 2) for predictions
    - Repositories for farm data
    - Domain services for business logic
    """
    
    def __init__(
        self,
        farm_repository: FarmRepository,
        production_repository: ProductionRepository,
        prediction_repository: PredictionRepository,
        risk_repository: RiskRepository,
        market_repository: MarketRepository,
    ):
        self.farm_repo = farm_repository
        self.production_repo = production_repository
        self.prediction_repo = prediction_repository
        self.risk_repo = risk_repository
        self.market_repo = market_repository
        
        # Initialize ML model system
        self.model_manager = get_model_manager()
        self.model_registry = get_model_registry()
        
        # Initialize feature engineering pipeline
        self.feature_engineer = FeatureEngineer()
        self.feature_preprocessor = FeaturePreprocessor(
            scaling_method=FeatureScalingMethod.STANDARD
        )
        
        # Placeholder for ML models (will be loaded via manager)
        self.ml_models = {}
        
        self.logger = logging.getLogger(__name__)
    
    
    async def predict_yield(
        self,
        farm_id: UUID,
        crop_id: Optional[UUID] = None,
        months_ahead: int = 6,
        include_variance: bool = True
    ) -> PredictionResult:
        """
        Predict crop yield for upcoming season using ML model or fallback.
        
        Attempts to use Phase 2 YieldPredictor (XGBoost) model if available,
        falls back to mock prediction if model not found.
        
        Args:
            farm_id: Farm identifier
            crop_id: Specific crop to predict (optional, uses dominant crop if not provided)
            months_ahead: Prediction horizon (1-12 months)
            include_variance: Include confidence interval
            
        Returns:
            PredictionResult with yield prediction from ML model or mock
        """
        
        start_time = time.time()
        is_mock_prediction = False
        
        try:
            # Get farm data
            farm = self.farm_repo.read(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            # Engineer features
            farm_dict = self._farm_to_dict(farm)
            feature_set = await self.feature_engineer.engineer_features(farm_dict)
            
            # Try to load YieldPredictor model
            model = self._get_ml_model(ModelType.YIELD_PREDICTOR)
            
            if model is not None:
                # === USE REAL ML MODEL ===
                try:
                    # Extract and preprocess features for XGBoost
                    features_array = self.extract_yield_features(farm, feature_set)
                    
                    if len(features_array) == 0:
                        raise ValueError("Feature extraction failed")
                    
                    # Make prediction
                    predicted_value = float(model.predict(features_array)[0])
                    
                    # Get confidence level from model if available
                    # XGBoost doesn't have built-in confidence, so we use model-specific logic
                    # For now, use high confidence (can be improved with uncertainty quantification)
                    confidence_level = 0.85
                    
                    # Extract feature importance from XGBoost model
                    try:
                        feature_importance = model.feature_importances_
                        # Create top 5 features list
                        top_indices = np.argsort(feature_importance)[-5:][::-1]
                        top_features = [
                            {
                                "feature": f"feature_{idx}",
                                "impact": float(feature_importance[idx])
                            }
                            for idx in top_indices
                        ]
                    except:
                        # Fallback if feature importance not available
                        top_features = self._extract_top_features(
                            feature_set.features if hasattr(feature_set, 'features') else {},
                            n=5
                        )
                    
                    # Get SHAP explanation if available
                    shap_explanation = None
                    shap_top_features = None
                    try:
                        if hasattr(model, 'explain_prediction'):
                            shap_explanation = model.explain_prediction(features_array, top_features=5)
                            if shap_explanation and 'top_features' in shap_explanation:
                                shap_top_features = shap_explanation['top_features']
                                self.logger.info(f"✅ SHAP explanation generated for yield prediction")
                    except Exception as shap_error:
                        self.logger.debug(f"SHAP explanation not available: {shap_error}")
                    
                    # Create prediction result with ML model output
                    prediction = PredictionResult(
                        farm_id=str(farm_id),
                        prediction_type='yield',
                        predicted_value=predicted_value,
                        confidence_level=confidence_level,
                        trend=self._determine_yield_trend(predicted_value, farm_id),
                        feature_importance=top_features,
                        shap_explanation=shap_explanation,
                        shap_top_features=shap_top_features
                    )
                    
                    # Calculate confidence intervals using model uncertainty
                    if include_variance:
                        # Conservative confidence interval (10% width)
                        margin = predicted_value * 0.10
                        prediction.confidence_interval_lower = predicted_value - margin
                        prediction.confidence_interval_upper = predicted_value + margin
                    
                    self.logger.info(
                        f"✅ ML Yield prediction for farm {farm_id}: {predicted_value:.0f} kg/acre "
                        f"(confidence: {confidence_level:.0%})"
                    )
                
                except Exception as ml_error:
                    self.logger.warning(
                        f"⚠️ YieldPredictor inference failed: {ml_error}. Falling back to mock."
                    )
                    # Fall through to mock prediction below
                    is_mock_prediction = True
                    model = None
            
            # === FALLBACK TO MOCK PREDICTION ===
            if model is None:
                base_yield = self._get_historical_yield(farm_id)
                
                # Use mock prediction logic
                prediction = self._predict_yield_internal(
                    farm=farm,
                    features=feature_set,
                    base_yield=base_yield,
                    months_ahead=months_ahead
                )
                
                # Calculate confidence interval
                if include_variance:
                    variance = self._estimate_yield_variance(farm_id)
                    prediction.confidence_interval_lower = prediction.predicted_value * (1 - variance)
                    prediction.confidence_interval_upper = prediction.predicted_value * (1 + variance)
                
                # Get top contributing factors
                top_features = self._extract_top_features(
                    feature_set.features if hasattr(feature_set, 'features') else {},
                    n=5
                )
                prediction.feature_importance = top_features
                
                is_mock_prediction = True
                self.logger.info(f"⚠️ Using mock yield prediction for farm {farm_id}: {prediction.predicted_value:.0f} kg/acre")
            
            # Generate recommendations
            prediction.recommendations = self._generate_yield_recommendations(
                farm=farm,
                predicted_yield=prediction.predicted_value,
                base_yield=self._get_historical_yield(farm_id)
            )
            
            # Save prediction to repository
            await self.prediction_repo.create_prediction(
                farm_id=farm_id,
                prediction_type='yield',
                prediction_value=prediction.predicted_value,
                confidence=prediction.confidence_level,
                metadata={
                    'crop_id': str(crop_id) if crop_id else None,
                    'months_ahead': months_ahead,
                    'variance': (
                        prediction.confidence_interval_upper - prediction.predicted_value
                        if prediction.confidence_interval_upper else None
                    ),
                    'is_mock': is_mock_prediction,
                    'model_type': 'yield_predictor'
                }
            )
            
            # Log prediction metadata
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._log_prediction_metadata(
                model_type=ModelType.YIELD_PREDICTOR,
                farm_id=farm_id,
                features_count=len(feature_set.features) if hasattr(feature_set, 'features') else 0,
                is_mock=is_mock_prediction,
                execution_time_ms=execution_time,
                confidence=prediction.confidence_level
            )
            
            return prediction
        
        except Exception as e:
            self.logger.error(f"❌ Yield prediction failed for farm {farm_id}: {e}")
            raise
    
    
    async def forecast_expenses(
        self,
        farm_id: UUID,
        forecast_months: int = 3,
        include_breakdown: bool = True
    ) -> ExpenseForecast:
        """
        Forecast farm operating expenses for upcoming months using ML model or fallback.
        
        Attempts to use Phase 2 ExpenseForecaster (Prophet/ARIMA) model if available,
        falls back to seasonal mock prediction if model not found.
        
        Args:
            farm_id: Farm identifier
            forecast_months: Number of months to forecast (1-12)
            include_breakdown: Include category-level breakdown
            
        Returns:
            ExpenseForecast with monthly predictions from ML model or mock
        """
        
        start_time = time.time()
        is_mock_prediction = False
        
        try:
            # Get farm data
            farm = self.farm_repo.read(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            # Get historical expenses
            historical_expenses = await self.production_repo.get_farm_expense_history(
                farm_id=farm_id,
                months=12
            )
            
            # Try to load ExpenseForecaster model
            model = self._get_ml_model(ModelType.EXPENSE_FORECASTER)
            
            monthly_forecast = []
            total_forecast = 0.0
            monthly_confidence = 0.85 if model else 0.75
            
            if model is not None and historical_expenses:
                # === USE REAL ML MODEL ===
                try:
                    # Extract time-series features for Prophet/ARIMA
                    expense_features = self.extract_expense_features(farm, historical_expenses)
                    
                    if not expense_features or 'dataframe' not in expense_features:
                        raise ValueError("Feature extraction failed")
                    
                    # Get historical data
                    df = expense_features['dataframe']
                    
                    if len(df) > 0:
                        # Make multi-step forecast (next N months)
                        # Prophet/ARIMA style: iterate predictions
                        try:
                            # Try to call forecast on model
                            # For Prophet: model.make_future_dataframe() + model.predict()
                            # For ARIMA: model.get_forecast(steps=N)
                            
                            # Universal approach: get last value and apply model trends
                            base_expense = float(df['y'].iloc[-1]) if len(df) > 0 else 50000
                            
                            # Get model's seasonal factors if available
                            for month_offset in range(1, forecast_months + 1):
                                # Apply model forecast (simplified for both Prophet and ARIMA)
                                try:
                                    # Try Prophet forecast style
                                    if hasattr(model, 'make_future_dataframe'):
                                        future = model.make_future_dataframe(periods=month_offset)
                                        forecast_result = model.predict(future)
                                        month_expense = float(forecast_result['yhat'].iloc[-1])
                                    # Try ARIMA forecast style
                                    elif hasattr(model, 'get_forecast'):
                                        forecast_result = model.get_forecast(steps=month_offset)
                                        month_expense = float(forecast_result.predicted_mean.iloc[-1])
                                    else:
                                        # Fallback: use base with trend
                                        trend = (df['y'].iloc[-1] - df['y'].iloc[0]) / len(df) if len(df) > 1 else 0
                                        month_expense = base_expense + (trend * month_offset)
                                except:
                                    # Seasonal adjustment with model hint
                                    seasonal_factor = self._get_seasonal_expense_factor(month_offset)
                                    month_expense = base_expense * seasonal_factor
                                
                                # Category breakdown from historical data
                                category_totals = expense_features.get('by_category', {})
                                total_ratio = sum(category_totals.values()) if category_totals else 1
                                
                                monthly_forecast.append({
                                    'month': (datetime.now() + timedelta(days=30*month_offset)).strftime('%B'),
                                    'total_kes': float(month_expense),
                                    'input_costs': float(month_expense * (category_totals.get('input', 0.45) / total_ratio if total_ratio > 0 else 0.45)),
                                    'labor_costs': float(month_expense * (category_totals.get('labor', 0.35) / total_ratio if total_ratio > 0 else 0.35)),
                                    'utilities_transport': float(month_expense * (category_totals.get('utilities', 0.20) / total_ratio if total_ratio > 0 else 0.20)),
                                })
                                
                                total_forecast += month_expense
                        
                        except Exception as model_error:
                            self.logger.warning(
                                f"⚠️ ExpenseForecaster inference failed: {model_error}. Falling back to mock."
                            )
                            is_mock_prediction = True
                            model = None
                    else:
                        is_mock_prediction = True
                        model = None
                
                except Exception as ml_error:
                    self.logger.warning(
                        f"⚠️ ExpenseForecaster feature extraction failed: {ml_error}. Falling back to mock."
                    )
                    is_mock_prediction = True
                    model = None
            
            # === FALLBACK TO MOCK PREDICTION ===
            if model is None:
                # Calculate base monthly expense from historical data
                if historical_expenses:
                    base_expense = np.mean([e.get('total', 50000) for e in historical_expenses])
                else:
                    base_expense = 50000  # Default estimate
                
                # Forecast with seasonality
                for month_offset in range(1, forecast_months + 1):
                    seasonal_factor = self._get_seasonal_expense_factor(month_offset)
                    month_expense = base_expense * seasonal_factor
                    
                    monthly_forecast.append({
                        'month': (datetime.now() + timedelta(days=30*month_offset)).strftime('%B'),
                        'total_kes': float(month_expense),
                        'input_costs': float(month_expense * 0.45),
                        'labor_costs': float(month_expense * 0.35),
                        'utilities_transport': float(month_expense * 0.20),
                    })
                    
                    total_forecast += month_expense
                
                is_mock_prediction = True
                monthly_confidence = 0.75
                self.logger.info(f"⚠️ Using mock expense forecast for farm {farm_id}: {total_forecast:,.0f} KES")
            
            # Generate forecast object
            forecast = ExpenseForecast(
                farm_id=str(farm_id),
                total_amount=float(total_forecast),
                by_category={
                    'input_costs': float(total_forecast * 0.45),
                    'labor_costs': float(total_forecast * 0.35),
                    'utilities_transport': float(total_forecast * 0.20),
                },
                monthly_breakdown=monthly_forecast,
                variance=0.12 if not is_mock_prediction else 0.15,  # Lower variance with ML
                confidence_level=monthly_confidence,
                key_drivers=self._identify_expense_drivers(farm),
                optimization_tips=self._generate_expense_optimizations(farm),
            )
            
            # Log result
            if not is_mock_prediction:
                self.logger.info(f"✅ ML Expense forecast for farm {farm_id}: {forecast.total_amount:,.0f} KES (confidence: {monthly_confidence:.0%})")
            
            # Log prediction metadata
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._log_prediction_metadata(
                model_type=ModelType.EXPENSE_FORECASTER,
                farm_id=farm_id,
                features_count=12 if historical_expenses else 0,  # 12 months history
                is_mock=is_mock_prediction,
                execution_time_ms=execution_time,
                confidence=forecast.confidence_level
            )
            
            return forecast
        
        except Exception as e:
            self.logger.error(f"❌ Expense forecast failed for farm {farm_id}: {e}")
            raise
    
    
    async def assess_disease_risk(
        self,
        farm_id: UUID,
        include_mitigation: bool = True
    ) -> DiseaseRiskAssessment:
        """
        Assess disease and pest risk for farm using ML model or fallback.
        
        Attempts to use Phase 2 DiseaseClassifier (GradientBoosting) model if available,
        falls back to heuristic risk scoring if model not found.
        
        Args:
            farm_id: Farm identifier
            include_mitigation: Include mitigation strategies
            
        Returns:
            DiseaseRiskAssessment with risk details from ML model or mock
        """
        
        start_time = time.time()
        is_mock_prediction = False
        
        try:
            # Get farm data
            farm = self.farm_repo.read(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            # Engineer features for disease prediction
            farm_dict = self._farm_to_dict(farm)
            feature_set = await self.feature_engineer.engineer_features(farm_dict)
            
            # Try to load DiseaseClassifier model
            model = self._get_ml_model(ModelType.DISEASE_CLASSIFIER)
            
            risk_score = 0.0
            risk_level = 'low'
            shap_explanation = None
            shap_top_factors = None
            
            if model is not None:
                # === USE REAL ML MODEL ===
                try:
                    # Extract features for GradientBoosting classifier
                    disease_features = self.extract_disease_features(farm, weather_data=None)
                    
                    if len(disease_features) == 0:
                        raise ValueError("Feature extraction failed")
                    
                    # Make prediction using GradientBoosting classifier
                    try:
                        # Try predict_proba for confidence scores
                        if hasattr(model, 'predict_proba'):
                            proba = model.predict_proba(disease_features)
                            # For binary/multi-class: get max probability
                            risk_probability = float(np.max(proba[0]))
                            risk_score = risk_probability * 100  # Convert to 0-100 scale
                        else:
                            # Fallback to predict
                            prediction = model.predict(disease_features)[0]
                            risk_score = float(prediction) * 100 if prediction < 1 else float(prediction)
                        
                        # Get SHAP explanation if available
                        shap_explanation = None
                        shap_top_factors = None
                        try:
                            if hasattr(model, 'explain_prediction'):
                                shap_explanation = model.explain_prediction(disease_features, top_features=5)
                                if shap_explanation and 'top_features' in shap_explanation:
                                    shap_top_factors = shap_explanation['top_features']
                                    self.logger.info(f"✅ SHAP explanation generated for disease risk assessment")
                        except Exception as shap_error:
                            self.logger.debug(f"SHAP explanation not available: {shap_error}")
                    
                    except Exception as inference_error:
                        self.logger.warning(
                            f"⚠️ DiseaseClassifier inference failed: {inference_error}. Falling back to mock."
                        )
                        is_mock_prediction = True
                        model = None
                        shap_explanation = None
                        shap_top_factors = None
                
                except Exception as ml_error:
                    self.logger.warning(
                        f"⚠️ DiseaseClassifier feature extraction failed: {ml_error}. Falling back to mock."
                    )
                    is_mock_prediction = True
                    model = None
            
            # === FALLBACK TO MOCK PREDICTION ===
            if model is None:
                risk_score = self._calculate_disease_risk_score(
                    farm=farm,
                    features=feature_set
                )
                is_mock_prediction = True
                self.logger.info(f"⚠️ Using mock disease risk assessment for farm {farm_id}: {risk_score:.0f}/100")
            
            # Determine risk level
            if risk_score < 25:
                risk_level = 'low'
            elif risk_score < 50:
                risk_level = 'medium'
            elif risk_score < 75:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            # Identify specific risks
            identified_risks = self._identify_specific_diseases(farm, risk_score)
            
            # Assessment object
            assessment = DiseaseRiskAssessment(
                farm_id=str(farm_id),
                overall_risk_score=float(risk_score),
                risk_level=risk_level,
                identified_risks=identified_risks,
                seasonal_factors=self._get_seasonal_disease_factors(),
                mitigation_strategies=self._generate_disease_mitigation(
                    farm=farm,
                    identified_risks=identified_risks
                ) if include_mitigation else [],
                monitoring_recommendations=self._generate_monitoring_recommendations(identified_risks),
                shap_explanation=shap_explanation,
                shap_top_factors=shap_top_factors
            )
            
            # Log result
            if not is_mock_prediction:
                self.logger.info(f"✅ ML Disease risk assessment for farm {farm_id}: {risk_level} ({risk_score:.0f}/100)")
            
            # Log prediction metadata
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._log_prediction_metadata(
                model_type=ModelType.DISEASE_CLASSIFIER,
                farm_id=farm_id,
                features_count=15,  # Disease feature count
                is_mock=is_mock_prediction,
                execution_time_ms=execution_time,
                confidence=0.85 if not is_mock_prediction else 0.70
            )
            
            return assessment
        
        except Exception as e:
            self.logger.error(f"❌ Disease risk assessment failed for farm {farm_id}: {e}")
            raise
    
    
    async def predict_market_price(
        self,
        farm_id: UUID,
        product_id: Optional[UUID] = None,
        forecast_weeks: int = 4
    ) -> PredictionResult:
        """
        Predict commodity market price for upcoming weeks using ML model or fallback.
        
        Attempts to use Phase 2 MarketPredictor (ARIMA/Prophet) model if available,
        falls back to trend-based mock prediction if model not found.
        
        Args:
            farm_id: Farm identifier
            product_id: Product to predict (optional)
            forecast_weeks: Prediction horizon in weeks
            
        Returns:
            PredictionResult with price forecast from ML model or mock
        """
        
        start_time = time.time()
        is_mock_prediction = False
        
        try:
            # Get farm data and current prices
            farm = self.farm_repo.read(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            # Get market data
            market_data = await self.market_repo.get_farm_market_data(farm_id)
            base_price = market_data.get('current_price', 40) if market_data else 40
            
            # Try to load MarketPredictor model
            model = self._get_ml_model(ModelType.MARKET_PREDICTOR)
            
            predicted_price = base_price
            price_trend = 0.0
            confidence_level = 0.85 if model else 0.70
            shap_explanation = None
            shap_top_features = None
            
            if model is not None and market_data:
                # === USE REAL ML MODEL ===
                try:
                    # Get historical market data for feature extraction
                    market_history = market_data.get('price_history', [])
                    
                    if not market_history:
                        raise ValueError("No market history available for forecasting")
                    
                    # Extract price features for ARIMA/Prophet
                    price_features = self.extract_price_features(market_history)
                    
                    if not price_features or 'dataframe' not in price_features:
                        raise ValueError("Feature extraction failed")
                    
                    # Make prediction using ARIMA/Prophet time-series model
                    try:
                        df = price_features['dataframe']
                        
                        if len(df) > 0:
                            # Use last price as reference
                            last_price = float(df['y'].iloc[-1])
                            
                            # Try ARIMA forecast style
                            if hasattr(model, 'get_forecast'):
                                forecast_result = model.get_forecast(steps=forecast_weeks)
                                predicted_price = float(forecast_result.predicted_mean.iloc[-1])
                            # Try Prophet forecast style
                            elif hasattr(model, 'make_future_dataframe'):
                                future = model.make_future_dataframe(periods=forecast_weeks)
                                forecast_result = model.predict(future)
                                predicted_price = float(forecast_result['yhat'].iloc[-1])
                            else:
                                # Fallback: use trend from data
                                trend_factor = (df['y'].iloc[-1] - df['y'].iloc[0]) / len(df) if len(df) > 1 else 0
                                predicted_price = last_price + (trend_factor * forecast_weeks)
                            
                            # Calculate trend
                            price_trend = (predicted_price - last_price) / last_price if last_price > 0 else 0
                            confidence_level = 0.85
                            
                            # Get SHAP explanation if available
                            try:
                                if hasattr(model, 'explain_prediction'):
                                    # For time series, use features extracted from history
                                    price_array = np.array(df['y'].values[-10:]).reshape(1, -1) if len(df) > 0 else np.array([[base_price]])
                                    shap_explanation = model.explain_prediction(price_array, top_features=5)
                                    if shap_explanation and 'top_features' in shap_explanation:
                                        shap_top_features = shap_explanation['top_features']
                                        self.logger.info(f"✅ SHAP explanation generated for market price prediction")
                            except Exception as shap_error:
                                self.logger.debug(f"SHAP explanation not available for market price: {shap_error}")
                        else:
                            is_mock_prediction = True
                            model = None
                    
                    except Exception as model_error:
                        self.logger.warning(
                            f"⚠️ MarketPredictor inference failed: {model_error}. Falling back to mock."
                        )
                        is_mock_prediction = True
                        model = None
                
                except Exception as ml_error:
                    self.logger.warning(
                        f"⚠️ MarketPredictor feature extraction failed: {ml_error}. Falling back to mock."
                    )
                    is_mock_prediction = True
                    model = None
            
            # === FALLBACK TO MOCK PREDICTION ===
            if model is None:
                # Simple price prediction with trend
                price_trend = self._analyze_price_trend(farm_id)
                predicted_price = base_price * (1 + price_trend * 0.05)  # 5% per week trend
                confidence_level = 0.70
                is_mock_prediction = True
                self.logger.info(f"⚠️ Using mock market price prediction for farm {farm_id}: {predicted_price:.0f} KES")
            
            # Generate prediction
            prediction = PredictionResult(
                farm_id=str(farm_id),
                prediction_type='price',
                predicted_value=float(predicted_price),
                confidence_level=confidence_level,
                confidence_interval_lower=float(predicted_price * 0.90),  # 10% interval
                confidence_interval_upper=float(predicted_price * 1.10),
                trend='uptrend' if price_trend > 0 else 'downtrend' if price_trend < 0 else 'stable',
                recommendations=self._generate_pricing_recommendations(
                    farm=farm,
                    predicted_price=predicted_price,
                    trend=price_trend
                ),
                shap_explanation=shap_explanation,
                shap_top_features=shap_top_features
            )
            
            # Log result
            if not is_mock_prediction:
                self.logger.info(f"✅ ML Market price prediction for farm {farm_id}: {predicted_price:.0f} KES (confidence: {confidence_level:.0%})")
            
            # Log prediction metadata
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._log_prediction_metadata(
                model_type=ModelType.MARKET_PREDICTOR,
                farm_id=farm_id,
                features_count=len(market_data.get('price_history', [])) if market_data else 0,
                is_mock=is_mock_prediction,
                execution_time_ms=execution_time,
                confidence=prediction.confidence_level
            )
            
            return prediction
        
        except Exception as e:
            self.logger.error(f"❌ Market price prediction failed for farm {farm_id}: {e}")
            raise
    
    
    async def optimize_roi(
        self,
        farm_id: UUID,
        optimization_type: str = 'general'
    ) -> ROIOptimization:
        """
        Optimize farm ROI with targeted recommendations using ML model or fallback.
        
        Attempts to use Phase 2 ROIOptimizer (MILP) model if available,
        falls back to heuristic optimization if model not found.
        
        Args:
            farm_id: Farm identifier
            optimization_type: 'general', 'crop_focused', 'cost_reduction'
            
        Returns:
            ROIOptimization with improvement recommendations from ML model or mock
        """
        
        start_time = time.time()
        is_mock_prediction = False
        
        try:
            # Get farm data
            farm = self.farm_repo.read(farm_id)
            if not farm:
                raise ValueError(f"Farm {farm_id} not found")
            
            # Calculate current ROI
            current_roi = await self._calculate_current_roi(farm_id)
            
            # Try to load ROIOptimizer model (MILP)
            model = self._get_ml_model(ModelType.ROI_OPTIMIZER)
            
            improvement_pct = 0.15  # Default 15%
            recommendations = []
            investment = 40000
            confidence = 0.80 if model else 0.60
            shap_explanation = None
            shap_top_factors = None
            
            if model is not None:
                # === USE REAL ML MODEL (MILP) ===
                try:
                    # Get farm financials for feature extraction
                    current_revenue = getattr(farm, 'total_annual_income', 500000)
                    current_costs = getattr(farm, 'total_annual_expense', 600000)
                    available_capital = getattr(farm, 'available_capital', 100000)
                    
                    financials = {
                        'current_revenue': current_revenue,
                        'current_costs': current_costs,
                        'target_roi_percent': 20
                    }
                    
                    # Extract features for MILP optimizer
                    roi_features = self.extract_roi_features(farm, financials)
                    
                    if len(roi_features) == 0:
                        raise ValueError("Feature extraction failed")
                    
                    # Make optimization call using MILP model
                    try:
                        # MILP models typically optimize and return solution
                        if hasattr(model, 'optimize'):
                            # PuLP/CVXPY style
                            model.optimize()
                            if hasattr(model, 'solution'):
                                solution = model.solution
                                improvement_pct = float(solution.get('improvement', 0.15))
                                investment = float(solution.get('investment', 40000))
                                recommendations = solution.get('recommendations', [])
                            else:
                                raise ValueError("No optimization solution found")
                        else:
                            # Sklearn wrapper style - predict improvement
                            improvement_pred = model.predict(roi_features)[0]
                            improvement_pct = float(improvement_pred) if improvement_pred < 1 else float(improvement_pred) / 100
                            
                            # Get SHAP explanation if available
                            try:
                                if hasattr(model, 'explain_prediction'):
                                    roi_array = np.array(roi_features).reshape(1, -1) if not isinstance(roi_features, np.ndarray) else roi_features
                                    shap_explanation = model.explain_prediction(roi_array, top_features=5)
                                    if shap_explanation and 'top_features' in shap_explanation:
                                        shap_top_factors = shap_explanation['top_features']
                                        self.logger.info(f"✅ SHAP explanation generated for ROI optimization")
                            except Exception as shap_error:
                                self.logger.debug(f"SHAP explanation not available for ROI: {shap_error}")
                            
                            # Default recommendations with improved allocation
                            if optimization_type == 'crop_focused':
                                recommendations, _ = self._optimize_crop_selection(farm)
                            elif optimization_type == 'cost_reduction':
                                recommendations, _ = self._optimize_costs(farm)
                            else:
                                recommendations, _ = self._optimize_general(farm)
                    
                    except Exception as solver_error:
                        self.logger.warning(
                            f"⚠️ ROIOptimizer solving failed: {solver_error}. Falling back to mock."
                        )
                        is_mock_prediction = True
                        model = None
                
                except Exception as ml_error:
                    self.logger.warning(
                        f"⚠️ ROIOptimizer feature extraction failed: {ml_error}. Falling back to mock."
                    )
                    is_mock_prediction = True
                    model = None
            
            # === FALLBACK TO MOCK OPTIMIZATION ===
            if model is None:
                # Generate heuristic optimization recommendations based on type
                if optimization_type == 'crop_focused':
                    recommendations, improvement_pct = self._optimize_crop_selection(farm)
                    investment = 25000
                elif optimization_type == 'cost_reduction':
                    recommendations, improvement_pct = self._optimize_costs(farm)
                    investment = 15000
                else:  # 'general'
                    recommendations, improvement_pct = self._optimize_general(farm)
                    investment = 40000
                
                confidence = 0.60
                is_mock_prediction = True
                self.logger.info(f"⚠️ Using mock ROI optimization for farm {farm_id}: +{improvement_pct*100:.1f}%")
            
            # Create optimization object
            optimization = ROIOptimization(
                farm_id=str(farm_id),
                current_roi_percent=float(current_roi),
                optimized_roi_percent=float(current_roi * (1 + improvement_pct)),
                potential_improvement_percent=float(improvement_pct * 100),
                recommendations=recommendations,
                implementation_timeline=self._generate_timeline(len(recommendations)),
                required_investment_kes=float(investment),
                payback_period_months=float(investment / (current_roi * 5000) if current_roi > 0 else 12),
                shap_explanation=shap_explanation,
                shap_top_factors=shap_top_factors
            )
            
            # Log result
            if not is_mock_prediction:
                self.logger.info(f"✅ ML ROI optimization for farm {farm_id}: +{improvement_pct*100:.1f}% (confidence: {confidence:.0%})")
            
            # Log prediction metadata
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._log_prediction_metadata(
                model_type=ModelType.ROI_OPTIMIZER,
                farm_id=farm_id,
                features_count=10,  # ROI feature count
                is_mock=is_mock_prediction,
                execution_time_ms=execution_time,
                confidence=optimization.confidence_level
            )
            
            return optimization
        
        except Exception as e:
            self.logger.error(f"❌ ROI optimization failed for farm {farm_id}: {e}")
            raise
    
    
    # ========== PRIVATE HELPER METHODS ==========
    
    def _farm_to_dict(self, farm) -> Dict[str, Any]:
        """Convert farm entity to dictionary for feature engineering"""
        return {
            "id": str(farm.id),
            "total_acres": farm.total_acres or 10,
            "crop_types": farm.crop_types or ["maize"],
            "livestock_types": farm.livestock_types or [],
            "worker_count": farm.worker_count or 2,
            "years_farming": farm.years_farming or 10,
            "is_registered": farm.is_registered or False,
            "production": {
                "yield_kg_per_acre": farm.last_yield_kg_per_acre or 500,
            },
            "soil": {
                "health_score": farm.soil_health_score or 0.5,
            },
            "expenses": {
                "total_monthly_kes": farm.avg_monthly_expense or 50000,
            },
            "total_12m_income_kes": farm.total_annual_income or 500000,
            "total_12m_expense_kes": farm.total_annual_expense or 600000,
        }
    
    def _get_historical_yield(self, farm_id: UUID) -> float:
        """Get average historical yield for farm"""
        # Mock implementation - would query database
        return 750.0  # kg/acre
    
    def _predict_yield_internal(
        self,
        farm,
        features: FeatureSet,
        base_yield: float,
        months_ahead: int
    ) -> PredictionResult:
        """Internal yield prediction logic"""
        
        # Apply seasonal adjustment
        seasonal_factor = self._get_seasonal_yield_factor(datetime.now().month + months_ahead)
        predicted_yield = base_yield * seasonal_factor
        
        return PredictionResult(
            farm_id=str(farm.id),
            prediction_type='yield',
            predicted_value=float(predicted_yield),
            confidence_level=0.80,
        )
    
    def _estimate_yield_variance(self, farm_id: UUID) -> float:
        """Estimate yield variance (confidence interval width)"""
        # Mock - would analyze historical variance
        return 0.15  # ±15%
    
    def _extract_top_features(self, features: Dict, n: int = 5) -> List[Dict[str, float]]:
        """Extract top n features by magnitude"""
        features_list = [(k, abs(v)) for k, v in features.items()]
        features_list.sort(key=lambda x: x[1], reverse=True)
        return [
            {"feature": k, "impact": float(v)}
            for k, v in features_list[:n]
        ]
    
    def _generate_yield_recommendations(self, farm, predicted_yield: float, base_yield: float) -> List[str]:
        """Generate yield improvement recommendations"""
        
        if predicted_yield < base_yield * 0.9:
            return [
                "Consider soil amendment plan",
                "Evaluate irrigation efficiency",
                "Review pest management strategy",
            ]
        elif predicted_yield > base_yield * 1.1:
            return [
                "Maintain current practices",
                "Scale successful techniques",
                "Document best practices for replication",
            ]
        else:
            return [
                "Fine-tune input application",
                "Monitor weather patterns",
                "Assess water management",
            ]
    
    def _determine_yield_trend(self, current_prediction: float, farm_id: UUID) -> str:
        """
        Determine yield trend direction.
        
        Args:
            current_prediction: Current predicted yield
            farm_id: Farm identifier
            
        Returns:
            Trend string: 'improving', 'stable', or 'declining'
        """
        try:
            # Get historical yield
            historical_yield = self._get_historical_yield(farm_id)
            
            # Compare with current prediction
            if current_prediction > historical_yield * 1.1:
                return 'improving'
            elif current_prediction < historical_yield * 0.9:
                return 'declining'
            else:
                return 'stable'
        except:
            return 'stable'  # Default if trend calculation fails
    
    def _get_seasonal_expense_factor(self, month_offset: int) -> float:
        """Get seasonal expense multiplier for month"""
        # Higher expenses during planting/harvest seasons
        current_month = (datetime.now().month + month_offset - 1) % 12 + 1
        seasonal_factors = {
            1: 0.90, 2: 0.85, 3: 1.20,  # Jan-Mar (planting)
            4: 1.10, 5: 0.95, 6: 0.90,  # Apr-Jun (growth)
            7: 0.88, 8: 0.90, 9: 1.15,  # Jul-Sep (harvest)
            10: 1.20, 11: 1.10, 12: 0.95  # Oct-Dec (post-harvest)
        }
        return seasonal_factors.get(current_month, 1.0)
    
    def _identify_expense_drivers(self, farm) -> List[str]:
        """Identify top 3 expense drivers"""
        return ["Input costs", "Labor", "Transport"]
    
    def _generate_expense_optimizations(self, farm) -> List[str]:
        """Generate cost reduction suggestions"""
        return [
            "Implement precision agriculture",
            "Optimize labor scheduling",
            "Negotiate bulk input purchases",
        ]
    
    def _calculate_disease_risk_score(self, farm, features: FeatureSet) -> float:
        """Calculate overall disease risk score (0-100)"""
        # Mock - would use ML classifier in Phase 2
        base_risk = 35.0
        variance = np.random.normal(0, 10)
        return max(0, min(100, base_risk + variance))
    
    def _identify_specific_diseases(self, farm, risk_score: float) -> List[Dict[str, Any]]:
        """Identify specific diseases/pests and their probabilities"""
        
        diseases = []
        if risk_score > 40:
            diseases.append({
                "pathogen": "Fall Armyworm",
                "probability": 0.65,
                "potential_loss_percent": 25,
                "season": "June-September"
            })
        if risk_score > 50:
            diseases.append({
                "pathogen": "Gray Leaf Spot",
                "probability": 0.45,
                "potential_loss_percent": 15,
                "season": "July-August"
            })
        if risk_score > 60:
            diseases.append({
                "pathogen": "Bacterial Wilt",
                "probability": 0.35,
                "potential_loss_percent": 20,
                "season": "March-May"
            })
        
        return diseases
    
    def _get_seasonal_disease_factors(self) -> Dict[str, str]:
        """Get seasonal disease risk factors"""
        current_month = datetime.now().month
        
        return {
            "high_risk_season": "June-September (armyworm)",
            "moderate_risk_season": "March-May (bacterial)",
            "low_risk_season": "January-February (dry season)",
        }
    
    def _generate_disease_mitigation(self, farm, identified_risks: List[Dict]) -> List[str]:
        """Generate disease mitigation strategies"""
        
        strategies = ["Scout regularly", "Use pest-resistant varieties"]
        
        if any(r["pathogen"] == "Fall Armyworm" for r in identified_risks):
            strategies.append("Deploy pheromone traps")
            strategies.append("Implement crop rotation")
        
        if any(r["pathogen"] == "Gray Leaf Spot" for r in identified_risks):
            strategies.append("Improve field drainage")
            strategies.append("Use fungicides preventatively")
        
        return strategies
    
    def _generate_monitoring_recommendations(self, identified_risks: List[Dict]) -> List[str]:
        """Generate disease monitoring recommendations"""
        
        return [
            "Scout fields weekly during risk season",
            "Monitor weather for humidity/temperature",
            "Record any disease observations",
            "Consult extension officer if symptoms appear",
        ]
    
    def _analyze_price_trend(self, farm_id: UUID) -> float:
        """Analyze historical price trend (-1 to 1)"""
        # Mock - would analyze market data
        return np.random.uniform(-0.5, 0.5)
    
    def _generate_pricing_recommendations(self, farm, predicted_price: float, trend: float) -> List[str]:
        """Generate pricing recommendations"""
        
        if trend > 0.3:
            return [
                "Price is expected to increase",
                "Consider strategic storage",
                "Time sales for peak prices",
            ]
        elif trend < -0.3:
            return [
                "Prices declining",
                "Consider early sales",
                "Explore alternative markets",
            ]
        else:
            return [
                "Prices stable",
                "Sell at convenience",
                "Monitor market for changes",
            ]
    
    async def _calculate_current_roi(self, farm_id: UUID) -> float:
        """Calculate current farm ROI"""
        # Mock - would calculate from actual data
        return 0.15  # 15% ROI
    
    def _optimize_crop_selection(self, farm) -> Tuple[List[Dict], float]:
        """Optimize crop selection for ROI"""
        
        recommendations = [
            {
                "action": "Shift 30% acreage to high-value crops",
                "potential_increase": 0.25,
                "timeframe": "2-3 seasons"
            },
            {
                "action": "Introduce horticulture crops (tomatoes, peppers)",
                "potential_increase": 0.35,
                "timeframe": "1 season"
            }
        ]
        
        return recommendations, 0.30  # 30% improvement
    
    def _optimize_costs(self, farm) -> Tuple[List[Dict], float]:
        """Optimize cost structure"""
        
        recommendations = [
            {
                "action": "Reduce input costs through bulk purchasing",
                "potential_increase": 0.08,
                "timeframe": "1 month"
            },
            {
                "action": "Mechanize labor for soil preparation",
                "potential_increase": 0.12,
                "timeframe": "1 season"
            }
        ]
        
        return recommendations, 0.20  # 20% improvement
    
    def _optimize_general(self, farm) -> Tuple[List[Dict], float]:
        """General ROI optimization"""
        
        recommendations = [
            {
                "action": "Diversify crop portfolio",
                "potential_increase": 0.15,
                "timeframe": "2 seasons"
            },
            {
                "action": "Implement precision agriculture",
                "potential_increase": 0.12,
                "timeframe": "1 season"
            },
            {
                "action": "Establish direct-to-consumer sales channel",
                "potential_increase": 0.18,
                "timeframe": "3 months"
            }
        ]
        
        return recommendations, 0.45  # 45% improvement
    
    def _get_seasonal_yield_factor(self, month: int) -> float:
        """Get seasonal yield adjustment factor"""
        # Higher yield in rainy seasons
        seasonal_factors = {
            1: 0.95, 2: 0.90, 3: 1.10,  # Jan-Mar
            4: 1.15, 5: 1.20, 6: 1.10,  # Apr-Jun
            7: 0.95, 8: 0.90, 9: 1.05,  # Jul-Sep
            10: 1.15, 11: 1.10, 12: 1.00  # Oct-Dec
        }
        month = month % 12
        return seasonal_factors.get(month if month > 0 else 12, 1.0)
    
    def _generate_timeline(self, num_items: int) -> List[str]:
        """Generate implementation timeline"""
        
        if num_items <= 2:
            return ["Month 1: Implement", "Month 2-3: Monitor & Adjust"]
        elif num_items <= 4:
            return [
                "Month 1: Quick wins",
                "Month 2-3: Medium-term items",
                "Month 4-6: Long-term investments"
            ]
        else:
            return [
                "Month 1: Foundation",
                "Month 2-3: Phase 1 implementation",
                "Month 4-6: Phase 2 expansion",
                "Month 6+: Optimization & scaling"
            ]
    
    
    # ========================================================================
    # FEATURE EXTRACTION HELPERS FOR ML MODELS
    # ========================================================================
    
    def extract_yield_features(self, farm, feature_set: FeatureSet) -> np.ndarray:
        """
        Extract and preprocess features for YieldPredictor model.
        
        Args:
            farm: Farm entity
            feature_set: Engineered feature set from Phase 1
            
        Returns:
            Numpy array of scaled features ready for XGBoost model
        """
        try:
            features = np.array(feature_set.features).reshape(1, -1)
            
            # Scale features using training-consistent method
            scaled_features = self.feature_preprocessor.preprocess_features(
                features,
                strategy="fit_transform" if not hasattr(self.feature_preprocessor, 'fitted') else "transform"
            )
            
            return scaled_features
        except Exception as e:
            self.logger.error(f"Error extracting yield features: {e}")
            return np.array([])
    
    def extract_expense_features(self, farm, historical_expenses: List[Dict]) -> Dict[str, Any]:
        """
        Extract and format features for ExpenseForecaster (time series) model.
        
        Args:
            farm: Farm entity
            historical_expenses: Historical monthly/seasonal expense data
            
        Returns:
            Dictionary with time series data formatted for Prophet/ARIMA
        """
        try:
            # Prepare time series data
            df_expenses = pd.DataFrame([
                {
                    'ds': pd.to_datetime(exp.get('date')),
                    'y': float(exp.get('amount', 0)),
                    'category': exp.get('category', 'general')
                }
                for exp in historical_expenses if 'date' in exp
            ])
            
            # Group by category
            by_category = df_expenses.groupby('category')['y'].sum().to_dict()
            
            return {
                'dataframe': df_expenses,
                'farm_id': farm.id,
                'farm_size_acres': getattr(farm, 'size_acres', 0),
                'farm_type': getattr(farm, 'farm_type', 'mixed'),
                'by_category': by_category,
                'total_historical': float(df_expenses['y'].sum()) if len(df_expenses) > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error extracting expense features: {e}")
            return {}
    
    def extract_disease_features(self, farm, weather_data: Optional[Dict] = None) -> np.ndarray:
        """
        Extract and format features for DiseaseClassifier model.
        Combines farm characteristics with weather/environmental factors.
        
        Args:
            farm: Farm entity
            weather_data: Optional weather/seasonal data
            
        Returns:
            Numpy array with disease risk factors ready for Gradient Boosting
        """
        try:
            features = []
            
            # Farm structural features
            features.extend([
                getattr(farm, 'size_acres', 0),
                getattr(farm, 'soil_ph', 7.0),
                getattr(farm, 'elevation_m', 1000),
            ])
            
            # Environmental features
            if weather_data:
                features.extend([
                    weather_data.get('temperature_c', 20),
                    weather_data.get('humidity_percent', 60),
                    weather_data.get('rainfall_mm', 100),
                    weather_data.get('wind_speed_kmh', 10),
                ])
            else:
                features.extend([20, 60, 100, 10])  # Defaults
            
            # Crop-specific features
            features.extend([
                getattr(farm, 'irrigation_available', 0),
                getattr(farm, 'pesticide_use_count_annual', 5),
                getattr(farm, 'planting_density_score', 0.5),
            ])
            
            # Convert to array and reshape for model
            feature_array = np.array(features).reshape(1, -1)
            
            return feature_array
        except Exception as e:
            self.logger.error(f"Error extracting disease features: {e}")
            return np.array([])
    
    def extract_price_features(self, market_data: List[Dict]) -> Dict[str, Any]:
        """
        Extract and format features for MarketPredictor (time series) model.
        
        Args:
            market_data: Historical market price data
            
        Returns:
            Dictionary with market time series formatted for ARIMA/Prophet
        """
        try:
            # Prepare time series data
            df_prices = pd.DataFrame([
                {
                    'ds': pd.to_datetime(data.get('date')),
                    'y': float(data.get('price_kes', 0)),
                    'crop': data.get('crop', 'maize')
                }
                for data in market_data if 'date' in data
            ])
            
            # Calculate price statistics
            price_stats = {
                'mean': float(df_prices['y'].mean()) if len(df_prices) > 0 else 0,
                'std': float(df_prices['y'].std()) if len(df_prices) > 0 else 0,
                'min': float(df_prices['y'].min()) if len(df_prices) > 0 else 0,
                'max': float(df_prices['y'].max()) if len(df_prices) > 0 else 0,
            }
            
            return {
                'dataframe': df_prices,
                'statistics': price_stats,
                'crop_groups': df_prices.groupby('crop')['y'].mean().to_dict() if 'crop' in df_prices.columns else {},
                'trend_direction': 'up' if len(df_prices) > 1 and df_prices['y'].iloc[-1] > df_prices['y'].iloc[0] else 'down'
            }
        except Exception as e:
            self.logger.error(f"Error extracting price features: {e}")
            return {}
    
    def extract_roi_features(self, farm, financials: Dict) -> np.ndarray:
        """
        Extract comprehensive features for ROIOptimizer (MILP) model.
        
        Args:
            farm: Farm entity
            financials: Financial data (revenue, costs, capital)
            
        Returns:
            Numpy array with ROI optimization factors ready for MILP model
        """
        try:
            features = []
            
            # Farm configuration
            features.extend([
                getattr(farm, 'size_acres', 0),
                getattr(farm, 'capital_available_kes', 0),
                getattr(farm, 'labor_hours_annual', 0),
            ])
            
            # Financial data
            features.extend([
                financials.get('current_revenue', 0),
                financials.get('current_costs', 0),
                financials.get('target_roi_percent', 20),
            ])
            
            # Resource constraints
            features.extend([
                getattr(farm, 'water_availability_rating', 5),
                getattr(farm, 'market_access_rating', 5),
                getattr(farm, 'technology_adoption_level', 2),
            ])
            
            # Convert to array
            feature_array = np.array(features).reshape(1, -1)
            
            return feature_array
        except Exception as e:
            self.logger.error(f"Error extracting ROI features: {e}")
            return np.array([])
    
    # ========================================================================
    # ML MODEL UTILITY METHODS
    # ========================================================================
    
    def _get_ml_model(self, model_type: ModelType) -> Optional[Any]:
        """
        Get ML model, loading from cache or disk if necessary.
        Falls back gracefully if model not available.
        """
        try:
            model = self.model_manager.get_model(model_type)
            if model is None:
                self.logger.warning(f"Model {model_type.value} not available, using mock fallback")
                self.model_registry.mark_fallback(model_type)
            return model
        except Exception as e:
            self.logger.error(f"Error loading model {model_type.value}: {e}")
            self.model_registry.mark_error(model_type, str(e))
            return None
    
    def _log_prediction_metadata(
        self,
        model_type: ModelType,
        farm_id: UUID,
        features_count: int,
        is_mock: bool = False,
        execution_time_ms: float = 0.0,
        confidence: float = 0.0
    ):
        """Log metadata about prediction for monitoring"""
        metadata = PredictionMetadata(
            model_type=model_type,
            model_version="v1.0",
            timestamp=datetime.now(),
            farm_id=str(farm_id),
            features_used=features_count,
            is_mock_prediction=is_mock,
            execution_time_ms=execution_time_ms,
            confidence_level=confidence
        )
        
        self.logger.info(
            f"Prediction: {model_type.value} | Farm: {farm_id} | "
            f"Features: {features_count} | Time: {execution_time_ms:.1f}ms | "
            f"Confidence: {confidence:.2%} | Mock: {is_mock}"
        )
