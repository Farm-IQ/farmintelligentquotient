"""
FarmSuite API Routes - Farm Analysis Endpoints
HTTP endpoints for farm profile and dashboard analysis
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from app.shared import domain_exceptions as exceptions
from app.farmsuite.domain.entities.farm import Farm
from auth.dependencies import (
    get_user_context,
    get_farm_repository,
    get_farm_intelligence_service,
)
from app.farmsuite.application.repositories import FarmRepository
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application import schemas


router = APIRouter(
    prefix="/api/v1/farmsuite",
    tags=["Farm Intelligence"]
)


# ============================================================================
# FARM PROFILE ENDPOINTS
# ============================================================================

@router.get(
    "/farms/{farm_id}",
    response_model=schemas.FarmSchema,
    summary="Get Farm Profile",
    description="Get complete farm profile and metadata"
)
async def get_farm_profile(
    farm_id: UUID = Path(..., description="Farm identifier"),
    user: Dict = Depends(get_user_context),
    farm_repository: FarmRepository = Depends(get_farm_repository),
):
    """
    Get farm profile with health metrics
    
    Returns farm details including health score, diversification index, and crops
    """
    try:
        farm = farm_repository.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Return schema
        return schemas.FarmSchema(
            id=str(farm.id),
            user_id=farm.user_id,
            farm_name=farm.farm_name,
            total_acres=farm.total_acres,
            location=farm.location,
            health_score=farm.health_score,
            diversification_index=farm.diversification_index,
        )
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching farm: {str(e)}")


@router.get(
    "/farms",
    response_model=List[schemas.FarmSchema],
    summary="List User Farms",
    description="Get all farms for authenticated user"
)
async def list_farms(
    user: Dict = Depends(get_user_context),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    farm_repository: FarmRepository = Depends(get_farm_repository),
):
    """
    List all farms for user
    
    Returns paginated list of farms
    """
    try:
        farms = farm_repository.get_farms_by_user(user['user_id'], limit=limit + skip)
        farms = farms[skip:skip + limit]
        
        return [
            schemas.FarmSchema(
                id=str(f.id),
                user_id=f.user_id,
                farm_name=f.farm_name,
                total_acres=f.total_acres,
                location=f.location,
                health_score=f.health_score,
                diversification_index=f.diversification_index,
            )
            for f in farms
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing farms: {str(e)}")


@router.put(
    "/farms/{farm_id}/health",
    response_model=schemas.FarmSchema,
    summary="Update Farm Health Score",
    description="Manually update farm health score after assessment"
)
async def update_farm_health(
    farm_id: UUID = Path(..., description="Farm identifier"),
    health_score: float = Query(..., ge=0, le=100, description="Health score 0-100"),
    user: Dict = Depends(get_user_context),
    farm_repository: FarmRepository = Depends(get_farm_repository),
):
    """
    Update farm health score
    
    Called after comprehensive farm health assessment
    """
    try:
        existing_farm = farm_repository.read(farm_id)
        if not existing_farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(existing_farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        updated = farm_repository.update_farm_health_score(farm_id, health_score)
        if not updated:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        return schemas.FarmSchema(
            id=str(updated.id),
            user_id=updated.user_id,
            farm_name=updated.farm_name,
            total_acres=updated.total_acres,
            location=updated.location,
            health_score=updated.health_score,
            diversification_index=updated.diversification_index,
        )
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FARM DASHBOARD ENDPOINTS
# ============================================================================

@router.get(
    "/farms/{farm_id}/dashboard",
    response_model=schemas.DashboardSchema,
    summary="Get Farm Dashboard",
    description="Comprehensive farm dashboard with all intelligence"
)
async def get_farm_dashboard(
    farm_id: UUID = Path(..., description="Farm identifier"),
    user: Dict = Depends(get_user_context),
    farm_repository: FarmRepository = Depends(get_farm_repository),
    farm_intelligence: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get comprehensive farm dashboard
    
    Returns:
    - Farm basic info
    - Production metrics
    - Critical risks
    - Active predictions
    - Market data
    - Labor metrics
    """
    try:
        # Verify farm exists and user owns it
        farm = farm_repository.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        dashboard = farm_intelligence.get_farm_dashboard(farm_id)
        
        if not dashboard:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        return schemas.DashboardSchema(
            farm=dashboard.get("farm", {}),
            production=dashboard.get("production", {}),
            risks=dashboard.get("risks", {}),
            predictions=dashboard.get("predictions", {}),
            markets=dashboard.get("markets", {}),
            labor=dashboard.get("labor", {}),
        )
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard: {str(e)}")


@router.get(
    "/farms/{farm_id}/weekly-report",
    response_model=schemas.ReportSchema,
    summary="Get Weekly Farm Report",
    description="Comprehensive weekly intelligence report"
)
async def get_weekly_report(
    farm_id: UUID = Path(..., description="Farm identifier"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Generate comprehensive weekly report
    
    Includes:
    - Dashboard overview
    - Production insights and recommendations
    - Risk summary and mitigation strategies
    - Market opportunities
    - Labor insights and ratings
    """
    try:
        report = farm_intelligence.generate_weekly_report(farm_id)
        
        if not report or "farm_id" not in report:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        return schemas.ReportSchema(
            generated_at=report.get("generated_at", datetime.now().isoformat()),
            farm_id=report.get("farm_id"),
            dashboard=report.get("dashboard", {}),
            production_insights=report.get("production_insights", {}),
            risk_summary=report.get("risk_summary", {}),
            market_opportunities=report.get("market_opportunities", {}),
            labor_insights=report.get("labor_insights", {}),
        )
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get(
    "/farms/{farm_id}/action-items",
    summary="Get Prioritized Action Items",
    description="Get actionable recommendations for farm manager"
)
async def get_action_items(
    farm_id: UUID = Path(..., description="Farm identifier"),
    priority_filter: Optional[str] = Query(None, description="Filter by CRITICAL, HIGH, MEDIUM, LOW"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Get prioritized action items for farm manager
    
    Returns list of actionable recommendations sorted by priority:
    - CRITICAL: Immediate action required
    - HIGH: Should address soon
    - MEDIUM: Plan to address
    - LOW: Nice to have
    """
    try:
        items = farm_intelligence.generate_action_items(farm_id)
        
        if priority_filter:
            items = [item for item in items if item["priority"] == priority_filter]
        
        return {"total_items": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting action items: {str(e)}")


@router.get(
    "/farms/{farm_id}/health-score",
    summary="Get Farm Health Score",
    description="Calculate overall farm intelligence and health score"
)
async def get_farm_health_score(
    farm_id: UUID = Path(..., description="Farm identifier"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Calculate overall farm health and intelligence score
    
    Score components (0-100):
    - Production efficiency (35%)
    - Risk management (30%)
    - Labor management (20%)
    - Market positioning (15%)
    """
    try:
        score = farm_intelligence.calculate_farm_score(farm_id)
        
        if score == 0:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Categorize score
        if score >= 80:
            category = "EXCELLENT"
        elif score >= 60:
            category = "GOOD"
        elif score >= 40:
            category = "FAIR"
        else:
            category = "POOR"
        
        return {
            "farm_id": str(farm_id),
            "health_score": score,
            "category": category,
            "message": f"Farm health is {category.lower()}. Focus on areas with lowest scores.",
        }
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating score: {str(e)}")


# ============================================================================
# FARM INSIGHTS ENDPOINTS
# ============================================================================

@router.get(
    "/farms/{farm_id}/production-insights",
    summary="Get Production Analysis",
    description="Production metrics and improvement recommendations"
)
async def get_production_insights(
    farm_id: UUID = Path(..., description="Farm identifier"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Get production analysis with recommendations
    
    Includes:
    - Yield efficiency
    - Consistency score
    - Profit margin
    - Average production metrics
    - Actionable recommendations
    """
    try:
        insights = farm_intelligence.get_production_insights(farm_id)
        
        if "message" in insights and "error" in insights["message"].lower():
            raise exceptions.ResourceNotFoundError(f"No production data for farm {farm_id}")
        
        return insights
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting insights: {str(e)}")


@router.get(
    "/farms/{farm_id}/risk-summary",
    summary="Get Risk Assessment",
    description="Comprehensive farm risk assessment"
)
async def get_risk_summary(
    farm_id: UUID = Path(..., description="Farm identifier"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Get comprehensive risk assessment
    
    Includes:
    - Risk summary with counts by severity
    - Overall farm risk score and level
    - Critical risks requiring immediate attention
    - Mitigation strategies for each critical risk
    """
    try:
        summary = farm_intelligence.get_risk_summary(farm_id)
        
        if not summary or not summary.get("summary"):
            raise exceptions.ResourceNotFoundError(f"No risk data for farm {farm_id}")
        
        return summary
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting risk summary: {str(e)}")


@router.get(
    "/farms/{farm_id}/market-opportunities",
    summary="Get Market Intelligence",
    description="Market opportunities and selling recommendations"
)
async def get_market_opportunities(
    farm_id: UUID = Path(..., description="Farm identifier"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Get market intelligence and opportunities
    
    Includes:
    - Products ranked by selling opportunity
    - Products with supply shortages
    - Buyer concentration risk analysis
    - Quality premium opportunities
    """
    try:
        opportunities = farm_intelligence.get_market_opportunities(farm_id)
        
        if not opportunities or not opportunities.get("selling_opportunities"):
            raise exceptions.ResourceNotFoundError(f"No market data for farm {farm_id}")
        
        return opportunities
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting opportunities: {str(e)}")


@router.get(
    "/farms/{farm_id}/labor-insights",
    summary="Get Labor Analytics",
    description="Workforce productivity and management insights"
)
async def get_labor_insights(
    farm_id: UUID = Path(..., description="Farm identifier"),
    farm_intelligence: FarmIntelligenceService = Depends(),
):
    """
    Get labor analytics and insights
    
    Includes:
    - Workforce statistics (count, costs, productivity)
    - High-performing workers
    - Workers needing support with recommendations
    - Cost-per-output efficiency analysis
    """
    try:
        insights = farm_intelligence.get_labor_insights(farm_id)
        
        if not insights or not insights.get("statistics"):
            raise exceptions.ResourceNotFoundError(f"No labor data for farm {farm_id}")
        
        return insights
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting labor insights: {str(e)}")
