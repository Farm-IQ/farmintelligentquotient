"""
FarmSuite API Routes - Production Intelligence Endpoints
Production analysis, crop management, resource optimization
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared import domain_exceptions as exceptions
from auth.dependencies import (
    get_user_context,
    get_farm_repository,
    get_production_repository,
    get_farm_intelligence_service,
)
from app.farmsuite.application.repositories import (
    FarmRepository,
    ProductionRepository,
)
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application import schemas


router = APIRouter(
    prefix="/api/v1/farmsuite",
    tags=["Production Intelligence"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ProductionMetricsRequest(BaseModel):
    """Request for production metrics"""
    farm_id: UUID = Field(..., description="Farm identifier")
    period_days: int = Field(90, ge=1, le=365, description="Analysis period")


class CropProductionMetric(BaseModel):
    """Crop production metric"""
    crop_id: UUID
    crop_name: str
    total_production_kg: float
    yield_kg_per_acre: float
    yield_consistency: float  # 0-100
    production_cost_kes: float
    production_value_kes: float
    gross_margin_percent: float
    quality_score: float  # 0-100
    disease_pressure_score: float  # 0-100
    trend: str  # "improving", "stable", "declining"


class ProductionMetricsResponse(BaseModel):
    """Production metrics response"""
    farm_id: UUID
    period_start_date: datetime
    period_end_date: datetime
    total_crops: int
    total_production_kg: float
    total_production_value_kes: float
    average_yield_kg_per_acre: float
    average_gross_margin_percent: float
    crop_metrics: List[CropProductionMetric]
    best_performing_crop: CropProductionMetric
    improvement_opportunities: List[str]


class EfficiencyAnalysisRequest(BaseModel):
    """Request for efficiency analysis"""
    farm_id: UUID = Field(..., description="Farm identifier")
    crop_id: Optional[UUID] = Field(None, description="Specific crop (optional)")


class EfficiencyAnalysisResponse(BaseModel):
    """Efficiency analysis response"""
    overall_efficiency_score: float  # 0-100
    cost_efficiency: float
    yield_efficiency: float
    quality_efficiency: float
    resource_utilization: Dict[str, float]
    benchmarks: Dict[str, float]  # vs similar farms
    efficiency_gaps: List[str]
    improvement_recommendations: List[str]
    potential_improvement_percent: float


class NutrientBudgetRequest(BaseModel):
    """Request for nutrient budget calculation"""
    farm_id: UUID = Field(..., description="Farm identifier")
    crop_id: UUID = Field(..., description="Crop identifier")
    target_yield_kg_per_acre: float = Field(..., description="Target yield for nutrient calculation")


class NutrientBudgetResponse(BaseModel):
    """Nutrient budget response"""
    crop_id: UUID
    crop_name: str
    target_yield_kg_per_acre: float
    nutrient_requirements: Dict[str, Dict[str, float]]  # {nutrient: {amount_kg, cost_kes}}
    current_soil_nutrients: Dict[str, float]
    nutrient_deficit: Dict[str, float]
    recommended_fertilizer: List[Dict[str, Any]]
    total_nutrient_cost_kes: float
    application_schedule: List[Dict[str, Any]]
    soil_test_recommendation: str


class WaterRequirementRequest(BaseModel):
    """Request for water requirement planning"""
    farm_id: UUID = Field(..., description="Farm identifier")
    parcel_id: Optional[UUID] = Field(None, description="Specific parcel (optional)")
    planting_date: datetime = Field(..., description="Expected planting date")


class WaterRequirementResponse(BaseModel):
    """Water requirement planning response"""
    parcel_id: UUID
    growing_season_days: int
    total_water_requirement_mm: float
    monthly_water_needs: List[Dict[str, float]]
    rainfall_expectation_mm: float
    irrigation_requirement_mm: float
    irrigation_schedule: List[Dict[str, Any]]
    water_source_options: List[str]
    estimated_water_cost_kes: float
    water_efficiency_tips: List[str]


# ============================================================================
# PRODUCTION METRICS ENDPOINT
# ============================================================================

@router.get(
    "/farm/{farm_id}/production/metrics",
    response_model=ProductionMetricsResponse,
    summary="Production Metrics",
    description="Get farm production metrics and performance"
)
async def get_production_metrics(
    farm_id: UUID,
    period_days: int = Query(90, ge=1, le=365),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get production metrics
    
    Returns crop yields, production values, and quality scores
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get production metrics
        metrics_data = intelligence_service.get_production_metrics(
            farm_id=farm_id,
            period_days=period_days
        )
        
        if "error" in metrics_data:
            raise HTTPException(status_code=500, detail=metrics_data["error"])
        
        crop_metrics = []
        for c in metrics_data.get("crop_metrics", []):
            crop_metrics.append(CropProductionMetric(
                crop_id=UUID(c.get("crop_id", "00000000-0000-0000-0000-000000000000")),
                crop_name=c.get("crop_name", ""),
                total_production_kg=c.get("total_production_kg", 0),
                yield_kg_per_acre=c.get("yield_kg_per_acre", 0),
                yield_consistency=c.get("yield_consistency", 0),
                production_cost_kes=c.get("production_cost_kes", 0),
                production_value_kes=c.get("production_value_kes", 0),
                gross_margin_percent=c.get("gross_margin_percent", 0),
                quality_score=c.get("quality_score", 0),
                disease_pressure_score=c.get("disease_pressure_score", 0),
                trend=c.get("trend", "stable")
            ))
        
        best_crop = metrics_data.get("best_performing_crop", {})
        
        return ProductionMetricsResponse(
            farm_id=farm_id,
            period_start_date=datetime.fromisoformat(metrics_data.get("period_start_date", datetime.now().isoformat())),
            period_end_date=datetime.fromisoformat(metrics_data.get("period_end_date", datetime.now().isoformat())),
            total_crops=metrics_data.get("total_crops", 0),
            total_production_kg=metrics_data.get("total_production_kg", 0),
            total_production_value_kes=metrics_data.get("total_production_value_kes", 0),
            average_yield_kg_per_acre=metrics_data.get("average_yield_kg_per_acre", 0),
            average_gross_margin_percent=metrics_data.get("average_gross_margin_percent", 0),
            crop_metrics=crop_metrics,
            best_performing_crop=CropProductionMetric(
                crop_id=UUID(best_crop.get("crop_id", "00000000-0000-0000-0000-000000000000")) if best_crop else UUID("00000000-0000-0000-0000-000000000000"),
                crop_name=best_crop.get("crop_name", "") if best_crop else "",
                total_production_kg=best_crop.get("total_production_kg", 0) if best_crop else 0,
                yield_kg_per_acre=best_crop.get("yield_kg_per_acre", 0) if best_crop else 0,
                yield_consistency=85.0,
                production_cost_kes=best_crop.get("production_cost_kes", 0) if best_crop else 0,
                production_value_kes=best_crop.get("production_value_kes", 0) if best_crop else 0,
                gross_margin_percent=best_crop.get("gross_margin_percent", 0) if best_crop else 0,
                quality_score=best_crop.get("quality_score", 0) if best_crop else 0,
                disease_pressure_score=best_crop.get("disease_pressure_score", 0) if best_crop else 0,
                trend="improving"
            ) if best_crop else crop_metrics[0] if crop_metrics else CropProductionMetric(
                crop_id=UUID("00000000-0000-0000-0000-000000000000"),
                crop_name="",
                total_production_kg=0,
                yield_kg_per_acre=0,
                yield_consistency=0,
                production_cost_kes=0,
                production_value_kes=0,
                gross_margin_percent=0,
                quality_score=0,
                disease_pressure_score=0,
                trend="stable"
            ),
            improvement_opportunities=metrics_data.get("improvement_opportunities", [])
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting production metrics: {str(e)}")


# ============================================================================
# EFFICIENCY ANALYSIS ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/production/efficiency",
    response_model=EfficiencyAnalysisResponse,
    summary="Production Efficiency Analysis",
    description="Analyze production efficiency and identify improvements"
)
async def analyze_efficiency(
    farm_id: UUID,
    request: EfficiencyAnalysisRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Analyze production efficiency
    
    Evaluates cost, yield, and quality efficiency against benchmarks
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Analyze efficiency
        eff_data = intelligence_service.get_efficiency_analysis(
            farm_id=farm_id,
            crop_id=request.crop_id
        )
        
        if "error" in eff_data:
            raise HTTPException(status_code=500, detail=eff_data["error"])
        
        return EfficiencyAnalysisResponse(
            overall_efficiency_score=eff_data.get("overall_efficiency_score", 0),
            cost_efficiency=eff_data.get("cost_efficiency", 0),
            yield_efficiency=eff_data.get("yield_efficiency", 0),
            quality_efficiency=eff_data.get("quality_efficiency", 0),
            resource_utilization=eff_data.get("resource_utilization", {}),
            benchmarks=eff_data.get("benchmarks", {}),
            efficiency_gaps=eff_data.get("efficiency_gaps", []),
            improvement_recommendations=eff_data.get("improvement_recommendations", []),
            potential_improvement_percent=eff_data.get("potential_improvement_percent", 0)
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing efficiency: {str(e)}")


# ============================================================================
# NUTRIENT BUDGET CALCULATION ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/production/nutrient-budget",
    response_model=NutrientBudgetResponse,
    summary="Nutrient Budget",
    description="Calculate nutrient requirements for target yield"
)
async def calculate_nutrient_budget(
    farm_id: UUID,
    request: NutrientBudgetRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Calculate nutrient budget
    
    Determines nutrient requirements and fertilizer recommendations
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Calculate nutrient budget
        budget_data = intelligence_service.get_nutrient_budget(
            farm_id=farm_id,
            crop_id=request.crop_id,
            target_yield_kg_per_acre=request.target_yield_kg_per_acre
        )
        
        if "error" in budget_data:
            raise HTTPException(status_code=500, detail=budget_data["error"])
        
        return NutrientBudgetResponse(
            crop_id=request.crop_id,
            crop_name=budget_data.get("crop_name", ""),
            target_yield_kg_per_acre=request.target_yield_kg_per_acre,
            nutrient_requirements=budget_data.get("nutrient_requirements", {}),
            current_soil_nutrients=budget_data.get("current_soil_nutrients", {}),
            nutrient_deficit=budget_data.get("nutrient_deficit", {}),
            recommended_fertilizer=budget_data.get("recommended_fertilizer", []),
            total_nutrient_cost_kes=budget_data.get("total_nutrient_cost_kes", 0),
            application_schedule=budget_data.get("application_schedule", []),
            soil_test_recommendation=budget_data.get("soil_test_recommendation", "")
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating nutrient budget: {str(e)}")


# ============================================================================
# WATER REQUIREMENT PLANNING ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/production/water-planning",
    response_model=WaterRequirementResponse,
    summary="Water Requirement Planning",
    description="Plan water requirements and irrigation schedule"
)
async def plan_water_requirements(
    farm_id: UUID,
    request: WaterRequirementRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Plan water requirements
    
    Calculates irrigation needs and creates irrigation schedule
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Plan water requirements - mock implementation for now
        # In Phase 4, this will call ML model to predict water needs
        water_plan = {
            "parcel_id": str(request.parcel_id or farm.id),
            "growing_season_days": 120,
            "total_water_requirement_mm": 600,
            "monthly_water_needs": [
                {"month": "January", "water_mm": 50},
                {"month": "February", "water_mm": 60},
            ],
            "rainfall_expectation_mm": 200,
            "irrigation_requirement_mm": 400,
            "irrigation_schedule": [
                {"week": 1, "water_mm": 30, "method": "drip"}
            ],
            "water_source_options": ["borehole", "rainwater_harvesting"],
            "estimated_water_cost_kes": 15000,
            "water_efficiency_tips": ["Use mulch", "Irrigation in morning"]
        }
        
        return WaterRequirementResponse(
            parcel_id=request.parcel_id or farm.id,
            growing_season_days=water_plan.get("growing_season_days", 120),
            total_water_requirement_mm=water_plan.get("total_water_requirement_mm", 600),
            monthly_water_needs=water_plan.get("monthly_water_needs", []),
            rainfall_expectation_mm=water_plan.get("rainfall_expectation_mm", 200),
            irrigation_requirement_mm=water_plan.get("irrigation_requirement_mm", 400),
            irrigation_schedule=water_plan.get("irrigation_schedule", []),
            water_source_options=water_plan.get("water_source_options", []),
            estimated_water_cost_kes=water_plan.get("estimated_water_cost_kes", 0),
            water_efficiency_tips=water_plan.get("water_efficiency_tips", [])
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning water requirements: {str(e)}")
