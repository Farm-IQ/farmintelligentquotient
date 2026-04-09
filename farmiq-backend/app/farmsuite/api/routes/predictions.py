"""
FarmSuite API Routes - Predictions Endpoints
Prediction endpoints for crop yield, expenses, disease risk, market prices, and ROI optimization
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
import time

from app.shared import domain_exceptions as exceptions
from auth.dependencies import (
    get_user_context,
    get_farm_repository,
    get_production_repository,
    get_prediction_repository,
    get_risk_repository,
    get_market_repository,
    get_farm_intelligence_service,
)
from app.farmsuite.application.repositories import (
    FarmRepository,
    ProductionRepository,
    PredictionRepository,
    RiskRepository,
    MarketRepository,
)
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application import schemas

# Cortex AI tracking
from core import AISystem, RequestType, cortex_track, get_system_analytics, get_cross_system_analytics

# Token tracking (Phase 3)
from app.ai_usage.services.usage_tracker import AIUsageTracker
from app.ai_usage.services.quota_validator import QuotaValidator
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/farmsuite",
    tags=["Predictions"]
)

# Initialize shared services
usage_tracker = AIUsageTracker()
quota_validator = QuotaValidator()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class YieldPredictionRequest(BaseModel):
    """Request for yield prediction"""
    farm_id: UUID = Field(..., description="Farm identifier")
    crop_id: UUID = Field(..., description="Crop identifier")
    include_variance: bool = Field(True, description="Include confidence interval")
    months_ahead: int = Field(6, ge=1, le=12, description="Prediction horizon")


class YieldPredictionResponse(BaseModel):
    """Yield prediction response with confidence interval"""
    predicted_yield_kg_per_acre: float
    confidence_lower_bound: float
    confidence_upper_bound: float
    confidence_level: float  # 0-1 confidence score
    trend: str  # "improving", "stable", "declining"
    key_drivers: List[Dict[str, Any]]
    recommendations: List[str]
    prediction_date: datetime


class ExpenseForecastRequest(BaseModel):
    """Request for expense forecast"""
    farm_id: UUID = Field(..., description="Farm identifier")
    forecast_months: int = Field(3, ge=1, le=12, description="Months to forecast")
    include_breakdown: bool = Field(True, description="Include expense category breakdown")


class ExpenseForecastResponse(BaseModel):
    """Expense forecast response"""
    total_forecast_kes: float
    by_category: Dict[str, float]
    monthly_breakdown: List[Dict[str, float]]
    variance_estimate: float
    key_cost_drivers: List[str]
    optimization_opportunities: List[str]
    confidence_level: float


class DiseaseRiskRequest(BaseModel):
    """Request for disease and pest risk assessment"""
    farm_id: UUID = Field(..., description="Farm identifier")
    include_mitigation: bool = Field(True, description="Include mitigation strategies")


class DiseaseRiskResponse(BaseModel):
    """Disease and pest risk assessment response"""
    overall_risk_score: float  # 0-100
    risk_level: str  # "low", "medium", "high", "critical"
    identified_risks: List[Dict[str, Any]]  # {pathogen, probability, potential_loss_percent}
    seasonal_factors: Dict[str, str]
    mitigation_strategies: List[str]
    monitoring_recommendations: List[str]
    assessment_date: datetime


class MarketPricePredictionRequest(BaseModel):
    """Request for market price prediction"""
    farm_id: UUID = Field(..., description="Farm identifier")
    product_id: UUID = Field(..., description="Product identifier")
    forecast_weeks: int = Field(4, ge=1, le=26, description="Weeks to forecast")


class MarketPricePredictionResponse(BaseModel):
    """Market price prediction response"""
    predicted_price_kes_per_unit: float
    confidence_lower_bound: float
    confidence_upper_bound: float
    confidence_level: float
    trend: str  # "uptrend", "stable", "downtrend"
    weekly_forecast: List[Dict[str, float]]
    market_factors: List[str]
    timing_recommendation: str  # "sell_now", "hold", "wait"
    historical_context: Dict[str, float]


class ROIOptimizationRequest(BaseModel):
    """Request for ROI optimization recommendations"""
    farm_id: UUID = Field(..., description="Farm identifier")
    optimization_type: str = Field("general", description="optimization_type: 'general', 'crop_focused', 'cost_reduction'")


class ROIOptimizationResponse(BaseModel):
    """ROI optimization recommendations"""
    current_roi_percent: float
    optimized_roi_percent: float
    potential_improvement_percent: float
    recommendations: List[Dict[str, Any]]
    implementation_timeline: List[str]
    required_investment_kes: float
    payback_period_months: float


# ============================================================================
# YIELD PREDICTION ENDPOINT
# ============================================================================

@router.post(
    "/predict/yield",
    response_model=YieldPredictionResponse,
    summary="Predict Crop Yield",
    description="Predict expected crop yield for upcoming season"
)
async def predict_yield(
    request: YieldPredictionRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Predict crop yield for upcoming season
    
    Uses historical production data, weather patterns, and soil conditions
    Requires 1 FIQ token per prediction
    """
    start_time = time.time()
    farmiq_id = getattr(user, 'farmiq_id', str(user['user_id']))
    
    async with cortex_track(
        system=AISystem.FARMSUITE,
        request_type=RequestType.INTELLIGENCE_AGGREGATE,
        user_id=str(user['user_id']),
        farm_id=str(request.farm_id)
    ) as tracker:
        try:
            # Phase 3: Check shared quota before processing
            quota_check = await quota_validator.check_quota(farmiq_id, tokens_required=1.0)
            if not quota_check['has_quota']:
                logger.warning(f"Quota check failed for {farmiq_id}: {quota_check['reason']}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Insufficient quota: {quota_check['reason']}"
                )
            
            # Verify farm exists and user owns it
            farm = farm_repo.read(request.farm_id)
            if not farm:
                raise exceptions.ResourceNotFoundError(f"Farm {request.farm_id} not found")
            
            # Verify user owns this farm
            if str(farm.user_id) != str(user['user_id']):
                raise HTTPException(status_code=403, detail="Not authorized to access this farm")
            
            # Generate prediction using domain service
            prediction_data = await intelligence_service.get_yield_prediction(
                farm_id=request.farm_id,
                crop_id=request.crop_id,
                months_ahead=request.months_ahead,
                include_variance=request.include_variance
            )
            
            if "error" in prediction_data:
                raise HTTPException(status_code=500, detail=prediction_data["error"])
            
            # Create response object
            predicted_yield = prediction_data.get("predicted_yield_kg_per_acre", 0)
            confidence = 0.85
            
            response = YieldPredictionResponse(
                predicted_yield_kg_per_acre=predicted_yield,
                confidence_lower_bound=prediction_data.get("confidence_interval", {}).get("lower", 0),
                confidence_upper_bound=prediction_data.get("confidence_interval", {}).get("upper", 0),
                confidence_level=confidence,
                trend="stable",
                key_drivers=prediction_data.get("feature_importance", []),
                recommendations=prediction_data.get("recommendations", []),
                prediction_date=datetime.now()
            )
            
            # Phase 3: Track FarmSuite YIELD prediction (1 FIQ deducted)
            try:
                duration_ms = int((time.time() - start_time) * 1000)
                
                usage_result = await usage_tracker.track_farmsuite_usage(
                    farmiq_id=farmiq_id,
                    user_id=str(user['user_id']),
                    hedera_wallet=getattr(user, 'hedera_wallet_id', ''),
                    prediction_type='yield',
                    confidence=confidence,
                    prediction_value=predicted_yield,
                    duration_ms=duration_ms
                )
                
                if usage_result.get('success'):
                    logger.info(f"✅ FarmSuite Yield prediction tracked: 1 FIQ deducted for {farmiq_id}")
                else:
                    logger.warning(f"⚠️ Token tracking incomplete: {usage_result.get('error')}")
                    
            except Exception as tracking_error:
                logger.warning(f"⚠️ Token tracking failed (non-blocking): {tracking_error}")
            
            return response
            
        except exceptions.DomainException as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error predicting yield: {str(e)}")


# ============================================================================
# EXPENSE FORECAST ENDPOINT
# ============================================================================

@router.post(
    "/predict/expenses",
    response_model=ExpenseForecastResponse,
    summary="Forecast Farm Expenses",
    description="Forecast farm operating expenses for upcoming months"
)
async def forecast_expenses(
    request: ExpenseForecastRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Forecast farm operating expenses
    
    Predicts input costs, labor, utilities based on production schedule
    """
    async with cortex_track(
        system=AISystem.FARMSUITE,
        request_type=RequestType.INTELLIGENCE_AGGREGATE,
        user_id=str(user['user_id']),
        farm_id=str(request.farm_id)
    ) as tracker:
        try:
            # Verify farm exists and user owns it
            farm = farm_repo.read(request.farm_id)
            if not farm:
                raise exceptions.ResourceNotFoundError(f"Farm {request.farm_id} not found")
            
            # Verify user owns this farm
            if str(farm.user_id) != str(user['user_id']):
                raise HTTPException(status_code=403, detail="Not authorized to access this farm")
            
            # Generate forecast
            forecast_data = await intelligence_service.get_expense_forecast(
                farm_id=request.farm_id,
                forecast_months=request.forecast_months,
                include_breakdown=request.include_breakdown
            )
            
            if "error" in forecast_data:
                raise HTTPException(status_code=500, detail=forecast_data["error"])
            
            # Extract monthly breakdown
            monthly_breakdown = {}
            for monthly in forecast_data.get("monthly_forecasts", []):
                month_key = monthly.get("month", "")
                monthly_breakdown[month_key] = monthly.get("forecasted_amount_kes", 0)
            
            return ExpenseForecastResponse(
                total_forecast_kes=forecast_data["total_forecasted_expense_kes"],
                by_category=forecast_data.get("monthly_forecasts", [{}])[0].get("categories", {}),
                monthly_breakdown=monthly_breakdown,
                variance_estimate=0.15,  # 15% variance estimate
                key_cost_drivers=["labor", "inputs", "utilities"],
                optimization_opportunities=forecast_data.get("recommendations", []),
                confidence_level=0.80
            )
            
        except exceptions.DomainException as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error forecasting expenses: {str(e)}")


# ============================================================================
# DISEASE RISK ASSESSMENT ENDPOINT
# ============================================================================

@router.post(
    "/predict/disease-risk",
    response_model=DiseaseRiskResponse,
    summary="Assess Disease & Pest Risk",
    description="Assess risk of diseases and pests on farm"
)
async def assess_disease_risk(
    request: DiseaseRiskRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Assess disease and pest risk
    
    Evaluates environmental factors, crop susceptibility, and historical incidents
    Requires 1 FIQ token per assessment
    """
    start_time = time.time()
    farmiq_id = getattr(user, 'farmiq_id', str(user['user_id']))
    
    try:
        # Phase 3: Check shared quota before processing
        quota_check = await quota_validator.check_quota(farmiq_id, tokens_required=1.0)
        if not quota_check['has_quota']:
            logger.warning(f"Quota check failed for {farmiq_id}: {quota_check['reason']}")
            raise HTTPException(
                status_code=429,
                detail=f"Insufficient quota: {quota_check['reason']}"
            )
        
        # Verify farm exists and user owns it
        farm = farm_repo.read(request.farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {request.farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Generate risk assessment
        risk_data = await intelligence_service.assess_disease_risks(
            farm_id=request.farm_id,
            include_mitigation=request.include_mitigation
        )
        
        if "error" in risk_data:
            raise HTTPException(status_code=500, detail=risk_data["error"])
        
        overall_risk = risk_data.get("overall_disease_risk_score", 0)
        
        response = DiseaseRiskResponse(
            overall_risk_score=overall_risk,
            risk_level=risk_data.get("risk_level", "medium"),
            identified_risks=risk_data.get("diseases_at_risk", []),
            seasonal_factors=risk_data.get("environmental_factors", {}),
            mitigation_strategies=risk_data.get("recommendations", []),
            monitoring_recommendations=["Monitor daily", "Check weather", "Track symptoms"],
            assessment_date=datetime.now()
        )
        
        # Phase 3: Track FarmSuite DISEASE prediction (1 FIQ deducted)
        try:
            duration_ms = int((time.time() - start_time) * 1000)
            
            usage_result = await usage_tracker.track_farmsuite_usage(
                farmiq_id=farmiq_id,
                user_id=str(user['user_id']),
                hedera_wallet=getattr(user, 'hedera_wallet_id', ''),
                prediction_type='disease',
                confidence=0.75,
                prediction_value=overall_risk,
                duration_ms=duration_ms
            )
            
            if usage_result.get('success'):
                logger.info(f"✅ FarmSuite Disease risk assessment tracked: 1 FIQ deducted for {farmiq_id}")
            else:
                logger.warning(f"⚠️ Token tracking incomplete: {usage_result.get('error')}")
                
        except Exception as tracking_error:
            logger.warning(f"⚠️ Token tracking failed (non-blocking): {tracking_error}")
        
        return response
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assessing disease risk: {str(e)}")


# ============================================================================
# MARKET PRICE PREDICTION ENDPOINT
# ============================================================================

@router.post(
    "/predict/market-price",
    response_model=MarketPricePredictionResponse,
    summary="Predict Market Price",
    description="Predict future market price for farm products"
)
async def predict_market_price(
    request: MarketPricePredictionRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Predict market price for farm products
    
    Uses historical prices, seasonal patterns, and market trends
    Requires 1 FIQ token per prediction
    """
    start_time = time.time()
    farmiq_id = getattr(user, 'farmiq_id', str(user['user_id']))
    
    try:
        # Phase 3: Check shared quota before processing
        quota_check = await quota_validator.check_quota(farmiq_id, tokens_required=1.0)
        if not quota_check['has_quota']:
            logger.warning(f"Quota check failed for {farmiq_id}: {quota_check['reason']}")
            raise HTTPException(
                status_code=429,
                detail=f"Insufficient quota: {quota_check['reason']}"
            )
        
        # Verify farm exists and user owns it
        farm = farm_repo.read(request.farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {request.farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get product name from repository
        commodity_name = "maize"  # Should be fetched from product data
        
        # Generate price prediction
        price_data = await intelligence_service.get_price_forecast(
            farm_id=request.farm_id,
            commodity=commodity_name,
            forecast_days=request.forecast_weeks * 7
        )
        
        if "error" in price_data:
            raise HTTPException(status_code=500, detail=price_data["error"])
        
        # Convert daily forecasts to weekly
        predicted_price = price_data.get("current_price_kes_per_kg", 0)
        confidence = 0.80
        
        weekly_forecast = {}
        for i, price_point in enumerate(price_data.get("forecasted_prices", [])):
            if i % 7 == 0:
                week_num = i // 7
                weekly_forecast[f"week_{week_num}"] = price_point.get("price_kes_per_kg", 0)
        
        response = MarketPricePredictionResponse(
            predicted_price_kes_per_unit=predicted_price,
            confidence_lower_bound=min([p.get("confidence_lower", 0) for p in price_data.get("forecasted_prices", [{}])]),
            confidence_upper_bound=max([p.get("confidence_upper", 0) for p in price_data.get("forecasted_prices", [{}])]),
            confidence_level=confidence,
            trend=price_data.get("trend", "stable"),
            weekly_forecast=weekly_forecast,
            market_factors=["rainfall", "market_demand", "supply_levels"],
            timing_recommendation=price_data.get("selling_recommendations", ["hold"])[0] if price_data.get("selling_recommendations") else "hold",
            historical_context={"average_price": 50, "min_price": 35, "max_price": 75}
        )
        
        # Phase 3: Track FarmSuite PRICE prediction (1 FIQ deducted)
        try:
            duration_ms = int((time.time() - start_time) * 1000)
            
            usage_result = await usage_tracker.track_farmsuite_usage(
                farmiq_id=farmiq_id,
                user_id=str(user['user_id']),
                hedera_wallet=getattr(user, 'hedera_wallet_id', ''),
                prediction_type='price',
                confidence=confidence,
                prediction_value=predicted_price,
                duration_ms=duration_ms
            )
            
            if usage_result.get('success'):
                logger.info(f"✅ FarmSuite Price prediction tracked: 1 FIQ deducted for {farmiq_id}")
            else:
                logger.warning(f"⚠️ Token tracking incomplete: {usage_result.get('error')}")
                
        except Exception as tracking_error:
            logger.warning(f"⚠️ Token tracking failed (non-blocking): {tracking_error}")
        
        return response
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting market price: {str(e)}")


# ============================================================================
# ROI OPTIMIZATION ENDPOINT
# ============================================================================

@router.post(
    "/predict/roi-optimization",
    response_model=ROIOptimizationResponse,
    summary="Optimize ROI",
    description="Get recommendations to optimize farm ROI"
)
async def optimize_roi(
    request: ROIOptimizationRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get ROI optimization recommendations
    
    Analyzes current performance and suggests improvements
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(request.farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {request.farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Map optimization type to focus area
        raise HTTPException(status_code=501, detail="ROI optimization not yet implemented")
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing ROI: {str(e)}")


# ============================================================================
# FarmSuite Analytics Endpoints
# ============================================================================

@router.get(
    "/analytics/dashboard",
    summary="FarmSuite Intelligence Analytics",
    tags=["Analytics"]
)
async def farmsuite_analytics_dashboard(user: Dict = Depends(get_user_context)):
    """
    Get comprehensive FarmSuite analytics with cross-system intelligence
    
    Returns:
    - Cross-system analytics (FarmGrow + FarmScore + FarmSuite)
    - Overall intelligence health
    - Cost breakdown across all systems
    - Performance metrics
    """
    try:
        stats = get_cross_system_analytics()
        
        return {
            "system": "FarmSuite Intelligence",
            "timestamp": datetime.now().isoformat(),
            "cross_system_analytics": stats,
            "description": "Real-time analytics across all FarmIQ AI systems",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/user/{user_id}",
    summary="User Intelligence Activity",
    tags=["Analytics"]
)
async def user_intelligence_analytics(user_id: str, user: Dict = Depends(get_user_context)):
    """
    Get user's FarmSuite intelligence usage and activity
    
    Returns:
    - Total intelligence requests
    - Predictions generated
    - System interactions
    - Usage timeline
    """
    try:
        from core import get_user_activity_analytics
        
        activity = get_user_activity_analytics(user_id)
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/farm/{farm_id}",
    summary="Farm Intelligence Analytics",
    tags=["Analytics"]
)
async def farm_intelligence_analytics(farm_id: str, user: Dict = Depends(get_user_context)):
    """
    Get farm's FarmSuite intelligence usage and activity
    
    Returns:
    - Farm's intelligence requests
    - Predictions and recommendations
    - Risk assessments
    - Market insights
    """
    try:
        from core import get_farm_activity_analytics
        
        activity = get_farm_activity_analytics(farm_id)
        
        return {
            "farm_id": farm_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        focus_area = "overall" if request.optimization_type == "general" else request.optimization_type
        
        # Generate ROI optimization
        roi_data = await intelligence_service.get_roi_optimization(
            farm_id=request.farm_id,
            focus_area=focus_area
        )
        
        if "error" in roi_data:
            raise HTTPException(status_code=500, detail=roi_data["error"])
        
        # Convert strategies to recommendations format
        recommendations = [
            {
                "title": strategy.get("strategy", ""),
                "description": f"Cost: {strategy.get('estimated_cost_kes', 0)} KES, Returns: {strategy.get('potential_revenue_increase_kes', 0)} KES",
                "impact": strategy.get("potential_revenue_increase_kes", 0),
                "difficulty": "medium",
            }
            for strategy in roi_data.get("optimization_strategies", [])
        ]
        
        return ROIOptimizationResponse(
            current_roi_percent=roi_data["current_roi_percent"],
            optimized_roi_percent=roi_data["potential_roi_percent"],
            potential_improvement_percent=roi_data["roi_improvement_percent"],
            recommendations=recommendations,
            implementation_timeline=[
                "Month 1: Quick wins",
                "Month 2-3: Medium term improvements",
                "Month 4-6: Long term initiatives"
            ],
            required_investment_kes=sum([s.get("estimated_cost_kes", 0) for s in roi_data.get("optimization_strategies", [])]),
            payback_period_months=6  # Estimated based on strategies
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing ROI: {str(e)}")
