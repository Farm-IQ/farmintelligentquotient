"""
FarmScore Credit Scoring API Routes (v4.0 Refactored)
======================================================

Modern API endpoints using layered architecture:
- Domain: Pure business logic (credit calculation)
- Application: Service orchestration & data access
- API: FastAPI routes

Endpoints:
- POST /api/v1/farmscore/score - Calculate credit score with ensemble
- GET /api/v1/farmscore/score/{farmer_id} - Retrieve stored credit score
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import time

from core.database import DatabaseRepository, get_database_repository
from app.farmscore.application.services import CreditScoringApplicationService
from app.farmscore.application.repositories import FarmerRepository, CreditScoreRepository
from app.farmscore.application.schemas import CreditScoringRequest, CreditScoringResponse
from app.farmscore.domain.services import CreditCalculationService
from app.shared.exceptions import EntityNotFoundError, ValidationError

# Cortex AI tracking
from core import AISystem, RequestType, cortex_track, get_system_analytics

# FIQ Token Usage Tracking
from app.ai_usage.services.usage_tracker import AIUsageTracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/farmscore", tags=["FarmScore Credit"])


def get_credit_scoring_service(
    db: DatabaseRepository = Depends(get_database_repository)
) -> CreditScoringApplicationService:
    """
    Dependency: Credit scoring application service
    Wires up repositories and domain service
    """
    farmer_repo = FarmerRepository(db)
    credit_repo = CreditScoreRepository(db)
    domain_service = CreditCalculationService()
    
    return CreditScoringApplicationService(
        farmer_repo=farmer_repo,
        credit_repo=credit_repo,
        domain_service=domain_service
    )


@router.post("/score", response_model=CreditScoringResponse, status_code=status.HTTP_201_CREATED)
async def calculate_credit_score(
    request: CreditScoringRequest,
    service: CreditScoringApplicationService = Depends(get_credit_scoring_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    """
    Calculate FarmScore credit score using layered architecture
    
    Features:
    - Credit calculation from domain layer
    - Farmer data from repositories
    - Feature engineering (20 features)
    - Credit recommendations
    - Audit trail logging
    - 90-day caching
    - FIQ token deduction (1 FIQ per call)
    
    Args:
        request: Credit scoring request with farmer data
        service: Application service (credit scoring orchestration)
        db: Database repository
        
    Returns:
        CreditScoringResponse with score, risk level, and recommendations
        
    Raises:
        ValidationError: Invalid input data (400)
        EntityNotFoundError: Farmer not found (404)
        CalculationError: Credit calculation error (500)
    """
    start_time = time.time()
    tracker = AIUsageTracker()
    
    async with cortex_track(
        system=AISystem.FARMSCORE,
        request_type=RequestType.ML_YIELD_PREDICTION,
        user_id=request.user_id,
        farm_id=getattr(request, 'farm_id', None)
    ) as tracker_cortex:
        try:
            # Validate farmer_id is provided
            if not request.farmer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="farmer_id is required for credit scoring"
                )
            
            # Get or create farmer entity
            farmer = await service.farmer_repo.get_by_id(request.farmer_id)
            
            if not farmer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Farmer {request.farmer_id} not found"
                )
            
            # Score farmer using domain service (returns CreditScore entity)
            credit_score = await service.score_farmer(request)
            
            # Store result in database
            stored_score = await service.credit_repo.create(credit_score)
            
            # Build properly-mapped response
            response = CreditScoringResponse(
                id=str(stored_score.id),
                user_id=request.user_id,
                farmer_id=str(request.farmer_id),
                score=stored_score.score,
                risk_level=stored_score.risk_level.value,
                risk_category=stored_score.get_risk_category(),
                default_probability=stored_score.default_probability,
                approval_likelihood=stored_score.approval_likelihood,
                is_eligible_for_loan=stored_score.is_eligible_for_loan(),
                recommended_credit_limit_kes=stored_score.recommended_credit_limit_kes,
                recommended_loan_term_months=stored_score.recommended_loan_term_months,
                recommended_interest_rate=stored_score.recommended_interest_rate,
                improvement_recommendations=stored_score.improvement_recommendations,
                is_cache_valid=stored_score.is_cache_valid(),
                created_at=stored_score.created_at,
                updated_at=stored_score.updated_at,
            )
            
            logger.info(
                f"Credit score calculated for farmer {request.farmer_id}: "
                f"score={stored_score.score}, risk={stored_score.risk_level.value}"
            )
            
            # ============ TRACK FIQ TOKEN USAGE ============
            duration_ms = int((time.time() - start_time) * 1000)
            
            try:
                # Get user's Hedera wallet
                user_wallet = await db.fetch_one(
                    "SELECT hedera_wallet_id FROM user_wallets WHERE user_id = :id LIMIT 1",
                    {'id': request.user_id}
                )
                
                if user_wallet:
                    # Track usage and deduct tokens
                    usage_result = await tracker.track_farmscore_usage(
                        farmiq_id=user_wallet.get('farmiq_id', request.user_id),
                        user_id=request.user_id,
                        hedera_wallet=user_wallet['hedera_wallet_id'],
                        credit_score=stored_score.score,
                        model_used='ensemble_gb_rf_lr',
                        duration_ms=duration_ms,
                    )
                    
                    if not usage_result.get('success'):
                        logger.warning(
                            f"Token deduction failed for {request.user_id}: {usage_result.get('error')}"
                        )
                    else:
                        logger.info(
                            f"✅ Tracked FarmScore usage: {usage_result.get('tokens_deducted')} FIQ deducted",
                            new_balance=usage_result.get('balance_after'),
                        )
            except Exception as tracking_error:
                logger.error(f"Failed to track usage: {tracking_error}")
                # Don't fail the API call if tracking fails
            
            return response
            
        except ValidationError as e:
            logger.warning(f"Validation error in credit scoring: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Error calculating credit score: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating credit score"
            )


@router.get("/score/{farmer_id}", response_model=CreditScoringResponse, status_code=status.HTTP_200_OK)
async def get_credit_score(
    farmer_id: str,
    service: CreditScoringApplicationService = Depends(get_credit_scoring_service),
):
    """
    Retrieve the most recent credit score for a farmer
    
    If score is expired (>90 days), return 404 and recommend recalculation
    
    Args:
        farmer_id: Farmer identifier (UUID or string)
        service: Application service
        
    Returns:
        Most recent valid CreditScoringResponse
        
    Raises:
        NotFoundError: No valid credit score found for farmer (404)
        ValidationError: Invalid farmer_id format (400)
    """
    try:
        # Validate farmer_id format
        if not farmer_id or not isinstance(farmer_id, str) or len(farmer_id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid farmer_id format"
            )
        
        # Get most recent credit score
        credit_score = await service.credit_repo.get_latest_by_farmer(farmer_id)
        
        if not credit_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credit score found for farmer {farmer_id}. Please request a new score calculation."
            )
        
        # Check if score is still valid (90-day TTL)
        if not credit_score.is_cache_valid():
            logger.warning(f"Credit score expired for farmer {farmer_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credit score for farmer {farmer_id} has expired. Please request a new score calculation."
            )
        
        # Build properly-mapped response
        response = CreditScoringResponse(
            id=str(credit_score.id),
            user_id=credit_score.user_id,
            farmer_id=str(credit_score.farmer_id),
            score=credit_score.score,
            risk_level=credit_score.risk_level.value,
            risk_category=credit_score.get_risk_category(),
            default_probability=credit_score.default_probability,
            approval_likelihood=credit_score.approval_likelihood,
            is_eligible_for_loan=credit_score.is_eligible_for_loan(),
            recommended_credit_limit_kes=credit_score.recommended_credit_limit_kes,
            recommended_loan_term_months=credit_score.recommended_loan_term_months,
            recommended_interest_rate=credit_score.recommended_interest_rate,
            improvement_recommendations=credit_score.improvement_recommendations,
            is_cache_valid=credit_score.is_cache_valid(),
            created_at=credit_score.created_at,
            updated_at=credit_score.updated_at,
        )
        
        logger.info(f"Retrieved credit score for farmer {farmer_id}")
        return response
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EntityNotFoundError as e:
        logger.warning(f"Credit score not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving credit score: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving credit score"
        )


@router.post("/loan/apply", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def apply_for_loan(
    request,  # LoanApplicationRequest
    service: CreditScoringApplicationService = Depends(get_credit_scoring_service),
):
    """
    Apply for loan with credit score assessment
    
    Returns:
        Loan application with approval decision and terms
    """
    try:
        # Get latest credit score for farmer
        credit_score = await service.credit_repo.get_latest_by_farmer(request.farmer_id)
        
        if not credit_score or not credit_score.is_cache_valid():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid credit score. Please calculate score first."
            )
        
        # Check eligibility
        if not credit_score.is_eligible_for_loan():
            return {
                "status": "rejected",
                "reason": f"Credit score too low. Risk level: {credit_score.risk_level.value}",
                "recommended_next_steps": credit_score.improvement_recommendations
            }
        
        # Check amount requested vs recommended limit
        if request.requested_amount_kes > credit_score.recommended_credit_limit_kes:
            approved_amount = credit_score.recommended_credit_limit_kes
        else:
            approved_amount = request.requested_amount_kes
        
        return {
            "status": "approved",
            "approved_amount_kes": approved_amount,
            "approved_term_months": credit_score.recommended_loan_term_months,
            "interest_rate": credit_score.recommended_interest_rate,
            "monthly_payment_kes": (approved_amount / credit_score.recommended_loan_term_months) + 
                                   (approved_amount * credit_score.recommended_interest_rate / 100 / 12)
        }
        
    except Exception as e:
        logger.error(f"Error processing loan application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing loan application"
        )


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get(
    "/analytics/dashboard",
    summary="FarmScore Analytics Dashboard",
    tags=["Analytics"]
)
async def farmscore_analytics_dashboard():
    """
    Get comprehensive FarmScore analytics with Cortex tracking data
    
    Returns:
    - System statistics (total predictions, success rate)
    - Cost breakdown (tokens, USD per model)
    - Performance metrics (duration, cache hit rate)
    - Credit score distribution
    """
    try:
        stats = get_system_analytics(AISystem.FARMSCORE)
        
        logger.info("FarmScore analytics dashboard request")
        
        return {
            "system": "FarmScore Credit Scoring",
            "timestamp": datetime.now().isoformat(),
            "metrics": stats,
            "description": "Real-time analytics for FarmScore ML system",
        }
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/user/{user_id}",
    summary="User Credit Scoring Activity",
    tags=["Analytics"]
)
async def user_activity_analytics(user_id: str):
    """
    Get user's FarmScore activity and usage analytics
    
    Returns:
    - Total credit scores calculated
    - Average score and risk distribution
    - Loan applications processed
    - Usage timeline
    """
    try:
        from core import get_user_activity_analytics
        
        activity = get_user_activity_analytics(user_id)
        
        logger.info(f"User activity report for: {user_id}")
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
        }
        
    except Exception as e:
        logger.error(f"User activity analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/farm/{farm_id}",
    summary="Farm Credit Activity Analytics",
    tags=["Analytics"]
)
async def farm_activity_analytics(farm_id: str):
    """
    Get farm's FarmScore credit activity and usage analytics
    
    Returns:
    - Farm's credit scoring requests
    - Average credit scores
    - Loan approval rates
    - Risk trends
    """
    try:
        from core import get_farm_activity_analytics
        
        activity = get_farm_activity_analytics(farm_id)
        
        logger.info(f"Farm activity report for: {farm_id}")
        
        return {
            "farm_id": farm_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
        }
        
    except Exception as e:
        logger.error(f"Farm activity analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
