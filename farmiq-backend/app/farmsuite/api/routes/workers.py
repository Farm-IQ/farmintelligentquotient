"""
FarmSuite API Routes - Worker Management Endpoints
Worker performance monitoring, analytics, and optimization
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared import domain_exceptions as exceptions
from app.farmsuite.application.repositories import (
    FarmRepository,
    WorkerRepository,
)
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application import schemas
from auth.dependencies import (
    get_user_context,
    get_farm_repository,
    get_farm_intelligence_service,
)


router = APIRouter(
    prefix="/api/v1/farmsuite",
    tags=["Worker Management"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class WorkerPerformanceRequest(BaseModel):
    """Request for worker performance metrics"""
    farm_id: UUID = Field(..., description="Farm identifier")
    period_days: int = Field(30, ge=1, le=365, description="Performance period in days")


class WorkerPerformanceMetric(BaseModel):
    """Individual worker performance metric"""
    worker_id: UUID
    worker_name: str
    productivity_score: float  # 0-100
    efficiency_rating: str  # "excellent", "good", "fair", "poor"
    tasks_completed: int
    average_task_duration_hours: float
    quality_score: float  # 0-100
    attendance_rate_percent: float
    trend: str  # "improving", "stable", "declining"


class WorkerPerformanceResponse(BaseModel):
    """Worker performance response"""
    farm_id: UUID
    period_start_date: datetime
    period_end_date: datetime
    total_workers: int
    average_productivity_score: float
    workers: List[WorkerPerformanceMetric]
    top_performer: WorkerPerformanceMetric
    performance_trends: Dict[str, str]
    optimization_opportunities: List[str]


class WorkerRecommendationRequest(BaseModel):
    """Request for worker optimization recommendations"""
    farm_id: UUID = Field(..., description="Farm identifier")
    focus_area: str = Field("productivity", description="optimization focus: 'productivity', 'skills', 'utilization', 'cost'")


class WorkerOptimizationStrategy(BaseModel):
    """Individual optimization strategy"""
    worker_id: UUID
    worker_name: str
    current_performance: float  # 0-100
    target_performance: float
    improvement_potential: float
    recommended_actions: List[str]
    training_needs: List[str]
    expected_impact: Dict[str, Any]


class WorkerRecommendationResponse(BaseModel):
    """Worker recommendations response"""
    strategies: List[WorkerOptimizationStrategy]
    aggregate_impact: Dict[str, float]
    implementation_timeline: List[str]
    required_investment_kes: float
    expected_roi_percent: float
    training_budget_kes: float


class TrainingNeedsRequest(BaseModel):
    """Request for worker training needs assessment"""
    farm_id: UUID = Field(..., description="Farm identifier")
    skill_category: Optional[str] = Field(None, description="Specific skill to assess")


class TrainingProgram(BaseModel):
    """Training program recommendation"""
    program_name: str
    target_workers: List[str]
    duration_hours: float
    skill_area: str
    expected_improvement_percent: float
    cost_kes: float
    provider_recommendation: str


class TrainingNeedsResponse(BaseModel):
    """Training needs assessment response"""
    total_skill_gaps: int
    critical_gaps: List[str]
    recommended_programs: List[TrainingProgram]
    total_training_investment_kes: float
    expected_productivity_gain_percent: float
    priority_training_order: List[str]
    timeline: List[str]


# ============================================================================
# WORKER PERFORMANCE ENDPOINT
# ============================================================================

@router.get(
    "/farm/{farm_id}/workers/performance",
    response_model=WorkerPerformanceResponse,
    summary="Worker Performance",
    description="Get worker productivity and performance metrics"
)
async def get_worker_performance(
    farm_id: UUID,
    period_days: int = Query(30, ge=1, le=365),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get worker performance metrics
    
    Measures productivity, efficiency, quality, and attendance
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get performance metrics
        perf_data = intelligence_service.get_worker_performance(
            farm_id=farm_id,
            period_days=period_days
        )
        
        if "error" in perf_data:
            raise HTTPException(status_code=500, detail=perf_data["error"])
        
        workers = []
        for w in perf_data.get("workers", []):
            workers.append(WorkerPerformanceMetric(
                worker_id=UUID(w.get("worker_id", "00000000-0000-0000-0000-000000000000")),
                worker_name=w.get("worker_name", ""),
                productivity_score=w.get("productivity_score", 0),
                efficiency_rating=w.get("efficiency_rating", "fair"),
                tasks_completed=w.get("tasks_completed", 0),
                average_task_duration_hours=w.get("average_task_duration_hours", 0),
                quality_score=w.get("quality_score", 0),
                attendance_rate_percent=w.get("attendance_rate_percent", 0),
                trend=w.get("trend", "stable")
            ))
        
        top_performer = perf_data.get("top_performer", {})
        
        return WorkerPerformanceResponse(
            farm_id=farm_id,
            period_start_date=datetime.fromisoformat(perf_data.get("period_start_date", datetime.now().isoformat())),
            period_end_date=datetime.fromisoformat(perf_data.get("period_end_date", datetime.now().isoformat())),
            total_workers=perf_data.get("total_workers", 0),
            average_productivity_score=perf_data.get("average_productivity_score", 0),
            workers=workers,
            top_performer=WorkerPerformanceMetric(
                worker_id=UUID(top_performer.get("worker_id", "00000000-0000-0000-0000-000000000000")) if top_performer else UUID("00000000-0000-0000-0000-000000000000"),
                worker_name=top_performer.get("worker_name", "") if top_performer else "",
                productivity_score=top_performer.get("productivity_score", 0) if top_performer else 0,
                efficiency_rating=top_performer.get("efficiency_rating", "fair") if top_performer else "fair",
                tasks_completed=top_performer.get("tasks_completed", 0) if top_performer else 0,
                average_task_duration_hours=top_performer.get("average_task_duration_hours", 0) if top_performer else 0,
                quality_score=top_performer.get("quality_score", 0) if top_performer else 0,
                attendance_rate_percent=top_performer.get("attendance_rate_percent", 0) if top_performer else 0,
                trend=top_performer.get("trend", "stable") if top_performer else "stable"
            ) if top_performer else (workers[0] if workers else WorkerPerformanceMetric(
                worker_id=UUID("00000000-0000-0000-0000-000000000000"),
                worker_name="",
                productivity_score=0,
                efficiency_rating="fair",
                tasks_completed=0,
                average_task_duration_hours=0,
                quality_score=0,
                attendance_rate_percent=0,
                trend="stable"
            )),
            performance_trends=perf_data.get("performance_trends", {}),
            optimization_opportunities=perf_data.get("optimization_opportunities", [])
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting worker performance: {str(e)}")


# ============================================================================
# WORKER OPTIMIZATION RECOMMENDATIONS ENDPOINT
# ============================================================================

@router.post(
    "/farm/{farm_id}/workers/recommendations",
    response_model=WorkerRecommendationResponse,
    summary="Worker Optimization",
    description="Get recommendations for worker optimization"
)
async def get_worker_recommendations(
    farm_id: UUID,
    request: WorkerRecommendationRequest = Body(...),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get worker optimization recommendations
    
    Identifies performance gaps and improvement opportunities
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get recommendations
        rec_data = intelligence_service.get_worker_optimization(
            farm_id=farm_id,
            focus_area=request.focus_area
        )
        
        if "error" in rec_data:
            raise HTTPException(status_code=500, detail=rec_data["error"])
        
        strategies = []
        for s in rec_data.get("strategies", []):
            strategies.append(WorkerOptimizationStrategy(
                worker_id=UUID(s.get("worker_id", "00000000-0000-0000-0000-000000000000")),
                worker_name=s.get("worker_name", ""),
                current_performance=s.get("current_performance", 0),
                target_performance=s.get("target_performance", 0),
                improvement_potential=s.get("improvement_potential", 0),
                recommended_actions=s.get("recommended_actions", []),
                training_needs=s.get("training_needs", []),
                expected_impact=s.get("expected_impact", {})
            ))
        
        return WorkerRecommendationResponse(
            strategies=strategies,
            aggregate_impact=rec_data.get("aggregate_impact", {}),
            implementation_timeline=rec_data.get("implementation_timeline", []),
            required_investment_kes=rec_data.get("required_investment_kes", 0),
            expected_roi_percent=rec_data.get("expected_roi_percent", 0),
            training_budget_kes=rec_data.get("training_budget_kes", 0)
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting worker recommendations: {str(e)}")


# ============================================================================
# TRAINING NEEDS ASSESSMENT ENDPOINT
# ============================================================================

@router.get(
    "/farm/{farm_id}/workers/training-needs",
    response_model=TrainingNeedsResponse,
    summary="Training Needs",
    description="Get training needs assessment"
)
async def get_training_needs(
    farm_id: UUID,
    skill_category: Optional[str] = Query(None),
    user: Dict = Depends(get_user_context),
    farm_repo: FarmRepository = Depends(get_farm_repository),
    intelligence_service: FarmIntelligenceService = Depends(get_farm_intelligence_service),
):
    """
    Get training needs assessment for workers
    
    Identifies skill gaps and recommends training programs
    """
    try:
        # Verify farm exists
        farm = farm_repo.read(farm_id)
        if not farm:
            raise exceptions.ResourceNotFoundError(f"Farm {farm_id} not found")
        
        # Verify user owns this farm
        if str(farm.user_id) != str(user['user_id']):
            raise HTTPException(status_code=403, detail="Not authorized to access this farm")
        
        # Get training needs assessment
        train_data = intelligence_service.get_training_needs(
            farm_id=farm_id,
            skill_category=skill_category
        )
        
        if "error" in train_data:
            raise HTTPException(status_code=500, detail=train_data["error"])
        
        # Build training programs list
        programs = []
        for prog in train_data.get("recommended_programs", []):
            programs.append(TrainingProgram(
                program_name=prog.get("program_name", ""),
                target_workers=prog.get("target_workers", []),
                duration_hours=prog.get("duration_hours", 0),
                skill_area=prog.get("skill_area", ""),
                expected_improvement_percent=prog.get("expected_improvement_percent", 0),
                cost_kes=prog.get("cost_kes", 0),
                provider_recommendation=prog.get("provider_recommendation", "")
            ))
        
        return TrainingNeedsResponse(
            total_skill_gaps=train_data.get("total_skill_gaps", 0),
            critical_gaps=train_data.get("critical_gaps", []),
            recommended_programs=programs,
            total_training_investment_kes=train_data.get("total_training_investment_kes", 0),
            expected_productivity_gain_percent=train_data.get("expected_productivity_gain_percent", 0),
            priority_training_order=train_data.get("priority_training_order", []),
            timeline=train_data.get("timeline", [])
        )
        
    except exceptions.DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assessing training needs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assessing training needs: {str(e)}")
