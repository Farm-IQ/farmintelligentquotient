"""
FarmSuite API Routes - Risk Management Endpoints
Risk assessment, monitoring, and mitigation strategy endpoints
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
    get_risk_repository,
    get_farm_intelligence_service,
)
from app.farmsuite.application.repositories import (
    FarmRepository,
    RiskRepository,
)
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application import schemas


router = APIRouter(
    prefix="/api/v1/farmsuite",
    tags=["Risk Management"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RiskAssessmentRequest(BaseModel):
    """Request for comprehensive risk assessment"""
    farm_id: UUID = Field(..., description="Farm identifier")
    include_historical: bool = Field(True, description="Include historical risk data")


class RiskAssessmentResponse(BaseModel):
    """Comprehensive risk assessment response"""
    overall_risk_score: float  # 0-100
    risk_level: str  # "low", "medium", "high", "critical"
    risk_categories: Dict[str, Dict[str, Any]]  # {category: {score, level, details}}
    critical_risks: List[Dict[str, Any]]
    risk_trends: Dict[str, str]  # {category: "improving"/"stable"/"worsening"}
    assessment_date: datetime
    next_review_date: datetime


class CriticalRiskRequest(BaseModel):
    """Request for identifying critical risks"""
    farm_id: UUID = Field(..., description="Farm identifier")
    threshold_score: float = Field(75.0, ge=0, le=100, description="Risk score threshold")


class CriticalRiskResponse(BaseModel):
    """Critical risk identification response"""
    critical_count: int
    critical_risks: List[Dict[str, Any]]
    priority_order: List[str]  # Risk IDs in priority order
    immediate_actions: List[str]
    response_deadline_date: datetime


class RiskMitigationRequest(BaseModel):
    """Request for risk mitigation strategies"""
    farm_id: UUID = Field(..., description="Farm identifier")
    risk_category: str = Field(..., description="Risk category to address")


class RiskMitigationResponse(BaseModel):
    """Risk mitigation strategies response"""
    risk_category: str
    current_risk_score: float
    mitigation_strategies: List[Dict[str, Any]]
    expected_risk_reduction: float  # 0-100 points
    implementation_cost_kes: float
    payback_period_months: Optional[float]
    timeline: List[str]
    success_metrics: List[str]


# ============================================================================
# COMPREHENSIVE RISK ASSESSMENT ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/risk/assessment",
    response_model=RiskAssessmentResponse,
    summary="Comprehensive Risk Assessment",
    description="Assess all risk categories on farm"
)
async def assess_farm_risks(
    farm_id: UUID,
    include_historical: bool = Query(True),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Comprehensive farm risk assessment
    
    Evaluates production, market, financial, and operational risks
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Generate comprehensive risk assessment
        assessment = await intelligence_service.assess_all_risks(
            farm_id=farm_id,
            include_historical=include_historical
        )
        
        if "error" in assessment:
            raise HTTPException(status_code=500, detail=assessment["error"])
        
        return RiskAssessmentResponse(
            overall_risk_score=assessment.get("overall_score", 50),
            risk_level=assessment.get("risk_level", "medium"),
            risk_categories=assessment.get("risk_categories", {}),
            critical_risks=assessment.get("critical_risks", []),
            risk_trends=assessment.get("trends", {}),
            assessment_date=datetime.fromisoformat(assessment.get("assessed_at", datetime.now().isoformat())),
            next_review_date=datetime.fromisoformat(assessment.get("next_review_date", datetime.now().isoformat()))
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assessing risks: {str(e)}")


# ============================================================================
# CRITICAL RISK IDENTIFICATION ENDPOINT
# ============================================================================

@router.get(
    "/farm/{farm_id}/risk/critical",
    response_model=CriticalRiskResponse,
    summary="Identify Critical Risks",
    description="Identify risks exceeding threshold score"
)
async def identify_critical_risks(
    farm_id: UUID,
    threshold_score: float = Query(75.0, ge=0, le=100),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Identify critical risks on farm
    
    Returns risks exceeding threshold, prioritized by severity
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Identify critical risks
        critical_risks_data = intelligence_service.get_critical_risks(
            farm_id=farm_id,
            threshold_score=threshold_score
        )
        
        if "error" in critical_risks_data:
            raise HTTPException(status_code=500, detail=critical_risks_data["error"])
        
        return CriticalRiskResponse(
            critical_count=critical_risks_data.get("critical_count", 0),
            critical_risks=critical_risks_data.get("critical_risks", []),
            priority_order=critical_risks_data.get("priority_order", []),
            immediate_actions=critical_risks_data.get("immediate_actions", []),
            response_deadline_date=datetime.fromisoformat(critical_risks_data.get("response_deadline", datetime.now().isoformat()))
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying critical risks: {str(e)}")


# ============================================================================
# RISK MITIGATION STRATEGIES ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/risk/mitigation",
    response_model=RiskMitigationResponse,
    summary="Get Mitigation Strategies",
    description="Get strategies to mitigate specific risk category"
)
async def get_mitigation_strategies(
    farm_id: UUID,
    request: RiskMitigationRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get mitigation strategies for specific risk
    
    Returns prioritized strategies with costs and timelines
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Generate mitigation strategies
        mitigation = await intelligence_service.get_mitigation_strategies(
            farm_id=farm_id,
            risk_category=request.risk_category
        )
        
        return RiskMitigationResponse(
            risk_category=request.risk_category,
            current_risk_score=mitigation.current_score,
            mitigation_strategies=mitigation.strategies,
            expected_risk_reduction=mitigation.expected_reduction,
            implementation_cost_kes=mitigation.cost,
            payback_period_months=mitigation.payback_period,
            timeline=mitigation.timeline,
            success_metrics=mitigation.metrics
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting mitigation strategies: {str(e)}")
