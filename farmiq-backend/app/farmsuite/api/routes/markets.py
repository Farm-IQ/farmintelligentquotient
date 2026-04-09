"""
FarmSuite API Routes - Market Intelligence Endpoints
Market opportunities, buyer analysis, and pricing strategies
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
    get_market_repository,
    get_farm_intelligence_service,
)
from app.farmsuite.application.repositories import (
    FarmRepository,
    MarketRepository,
)
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application import schemas


router = APIRouter(
    prefix="/api/v1/farmsuite",
    tags=["Market Intelligence"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MarketOpportunitiesRequest(BaseModel):
    """Request for market opportunities"""
    farm_id: UUID = Field(..., description="Farm identifier")
    product_types: Optional[List[str]] = Field(None, description="Filter by product types")
    min_margin_percent: float = Field(20.0, ge=0, le=100, description="Minimum margin requirement")


class MarketOpportunitiesResponse(BaseModel):
    """Market opportunities response"""
    opportunities: List[Dict[str, Any]]
    total_potential_revenue_kes: float
    top_opportunity: Dict[str, Any]
    market_window_dates: Dict[str, str]
    seasonal_recommendations: List[str]
    next_update_date: datetime


class BuyerAnalysisRequest(BaseModel):
    """Request for buyer analysis"""
    farm_id: UUID = Field(..., description="Farm identifier")
    buyer_id: Optional[UUID] = Field(None, description="Specific buyer to analyze")


class BuyerAnalysisResponse(BaseModel):
    """Buyer analysis response"""
    buyer_id: UUID
    buyer_name: str
    reliability_score: float  # 0-100
    average_price_paid_kes: float
    payment_terms: str
    purchase_history: Dict[str, Any]
    rating: str  # "excellent", "good", "fair", "poor"
    recommendation: str  # "recommended", "caution", "avoid"


class QualityPremiumRequest(BaseModel):
    """Request for quality premium analysis"""
    farm_id: UUID = Field(..., description="Farm identifier")
    crop_id: UUID = Field(..., description="Crop identifier")


class QualityPremiumResponse(BaseModel):
    """Quality premium analysis response"""
    current_quality_score: float  # 0-100
    achievable_premium_percent: float
    current_price_kes_per_unit: float
    premium_price_kes_per_unit: float
    additional_revenue_potential_annual_kes: float
    quality_improvement_priorities: List[str]
    implementation_timeline: List[str]
    investment_required_kes: float


class PricingStrategyRequest(BaseModel):
    """Request for pricing strategy"""
    farm_id: UUID = Field(..., description="Farm identifier")
    product_id: UUID = Field(..., description="Product identifier")
    sales_timeline_weeks: int = Field(4, ge=1, le=52, description="Expected sales timeline")


class PricingStrategyResponse(BaseModel):
    """Pricing strategy recommendations"""
    recommended_selling_price_kes: float
    price_range_kes: Dict[str, float]  # {min, max}
    expected_sell_through_percent: float
    alternative_strategies: List[Dict[str, Any]]
    market_comparison: Dict[str, float]
    buyer_segments: List[Dict[str, Any]]
    revenue_scenarios: List[Dict[str, Any]]


# ============================================================================
# MARKET OPPORTUNITIES ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/market/opportunities",
    response_model=MarketOpportunitiesResponse,
    summary="Market Opportunities",
    description="Identify profitable market opportunities for farm products"
)
async def get_market_opportunities(
    farm_id: UUID,
    request: MarketOpportunitiesRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Identify market opportunities
    
    Analyzes demand, pricing, and seasonal factors
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get market opportunities
        opps_data = intelligence_service.get_market_opportunities(
            farm_id=farm_id
        )
        
        if "error" in opps_data:
            raise HTTPException(status_code=500, detail=opps_data["error"])
        
        return MarketOpportunitiesResponse(
            opportunities=opps_data.get("selling_opportunities", []),
            total_potential_revenue_kes=sum([o.get("potential_revenue_kes", 0) for o in opps_data.get("selling_opportunities", [])]),
            top_opportunity=opps_data.get("selling_opportunities", [{}])[0] if opps_data.get("selling_opportunities") else {},
            market_window_dates={},
            seasonal_recommendations=opps_data.get("seasonal_recommendations", [])
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market opportunities: {str(e)}")


# ============================================================================
# BUYER ANALYSIS ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/market/buyer-analysis",
    response_model=List[BuyerAnalysisResponse],
    summary="Buyer Analysis",
    description="Analyze reliability and terms of potential buyers"
)
async def analyze_buyers(
    farm_id: UUID,
    request: BuyerAnalysisRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Analyze buyer reliability and terms
    
    Evaluates payment history, pricing, and negotiation potential
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Analyze buyers
        buyers_data = intelligence_service.get_buyer_analysis(
            farm_id=farm_id,
            buyer_id=request.buyer_id
        )
        
        if "error" in buyers_data:
            raise HTTPException(status_code=500, detail=buyers_data["error"])
        
        return [
            BuyerAnalysisResponse(
                buyer_id=UUID(b.get("buyer_id", "00000000-0000-0000-0000-000000000000")),
                buyer_name=b.get("buyer_name", "Unknown"),
                reliability_score=b.get("reliability_score", 0),
                average_price_paid_kes=b.get("average_price_paid_kes", 0),
                payment_terms=b.get("payment_terms", ""),
                purchase_history=b.get("purchase_history", {}),
                rating=b.get("rating", "fair"),
                recommendation=b.get("recommendation", "neutral")
            )
            for b in buyers_data.get("buyers", [])
        ]
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing buyers: {str(e)}")


# ============================================================================
# QUALITY PREMIUM ANALYSIS ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/market/quality-premium",
    response_model=QualityPremiumResponse,
    summary="Quality Premium Analysis",
    description="Calculate potential price premium for quality improvements"
)
async def analyze_quality_premium(
    farm_id: UUID,
    request: QualityPremiumRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Analyze quality premium potential
    
    Identifies quality improvements and resulting price premiums
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Analyze quality premium
        premium_data = intelligence_service.get_quality_premium_analysis(
            farm_id=farm_id,
            crop_id=request.crop_id
        )
        
        if "error" in premium_data:
            raise HTTPException(status_code=500, detail=premium_data["error"])
        
        return QualityPremiumResponse(
            current_quality_score=premium_data.get("current_quality_score", 0),
            achievable_premium_percent=premium_data.get("achievable_premium_percent", 0),
            current_price_kes_per_unit=premium_data.get("current_price_kes_per_unit", 0),
            premium_price_kes_per_unit=premium_data.get("premium_price_kes_per_unit", 0),
            additional_revenue_potential_annual_kes=premium_data.get("additional_revenue_potential_annual_kes", 0),
            quality_improvement_priorities=premium_data.get("quality_improvement_priorities", []),
            implementation_timeline=premium_data.get("implementation_timeline", []),
            investment_required_kes=premium_data.get("investment_required_kes", 0)
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing quality premium: {str(e)}")


# ============================================================================
# PRICING STRATEGY ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/market/pricing-strategy",
    response_model=PricingStrategyResponse,
    summary="Pricing Strategy",
    description="Get recommended pricing strategy for farm products"
)
async def get_pricing_strategy(
    farm_id: UUID,
    request: PricingStrategyRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get pricing strategy recommendations
    
    Considers market conditions, supply/demand, and timing
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get pricing strategy
        strategy_data = intelligence_service.get_pricing_strategy(
            farm_id=farm_id,
            product_id=request.product_id,
            sales_timeline_weeks=request.sales_timeline_weeks
        )
        
        if "error" in strategy_data:
            raise HTTPException(status_code=500, detail=strategy_data["error"])
        
        return PricingStrategyResponse(
            recommended_selling_price_kes=strategy_data.get("recommended_selling_price_kes", 0),
            price_range_kes=strategy_data.get("price_range_kes", {"min": 0, "target": 0, "max": 0}),
            expected_sell_through_percent=90.0,
            alternative_strategies=[],
            market_comparison={},
            buyer_segments=[],
            revenue_scenarios=[]
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pricing strategy: {str(e)}")
