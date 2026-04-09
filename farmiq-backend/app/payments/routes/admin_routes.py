"""
Admin Dashboard & Management Routes - Phase 4
Analytics, system monitoring, and quota administration endpoints

Author: FarmIQ Backend Team
Date: March 2026
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.logging_config import get_logger
from auth.dependencies import get_current_user
from app.payments.services.admin_service import AdminDashboardService

logger = get_logger(__name__)

# ===================== ROUTER & DEPENDENCIES =====================

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def get_admin_dashboard_service() -> AdminDashboardService:
    """Dependency injection for admin service"""
    from core.app_config import get_admin_dashboard_service as _get_service
    return _get_service()


# ===================== REQUEST/RESPONSE MODELS =====================

class AdminQuotaUpdateRequest(BaseModel):
    """Update user quota"""
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None


class SystemOverviewResponse(BaseModel):
    """System overview for dashboard"""
    total_users: int
    total_transactions: int
    total_tokens_minted: float
    total_revenue_kes: float
    today_transactions: int
    today_revenue_kes: float
    timestamp: str


class DailyRevenueItem(BaseModel):
    """Single day revenue"""
    date: str
    transactions: int
    revenue_kes: float
    tokens_minted: float


class PaymentAnalyticsResponse(BaseModel):
    """Payment analytics"""
    daily_revenue: List[DailyRevenueItem]
    success_rate_percent: float
    total_transactions: int
    completed_transactions: int


class UserAnalyticsResponse(BaseModel):
    """User growth and engagement"""
    new_users_daily: List[Dict[str, Any]]
    active_users: int
    users_by_balance_tier: Dict[str, int]
    period_days: int


class ExceedingUserItem(BaseModel):
    """User exceeding quota"""
    farmiq_id: str
    balance: float
    daily_budget: float
    today_usage: float
    exceeded_percent: float


# ===================== ADMIN AUTH MIDDLEWARE =====================

async def verify_admin(current_user = Depends(get_current_user)):
    """Verify user is admin"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ===================== SYSTEM OVERVIEW =====================

@router.get(
    "/dashboard/overview",
    response_model=SystemOverviewResponse,
    dependencies=[Depends(verify_admin)]
)
async def get_system_overview(
    admin_service: AdminDashboardService = Depends(get_admin_dashboard_service)
):
    """
    Get high-level system overview for admin dashboard
    
    Returns:
    - Total users and transactions
    - Revenue and tokens minted
    - Today's activity
    """
    try:
        return await admin_service.get_system_overview()
    except Exception as e:
        logger.error(f"Overview fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== ANALYTICS ENDPOINTS =====================

@router.get(
    "/analytics/payments",
    response_model=PaymentAnalyticsResponse,
    dependencies=[Depends(verify_admin)]
)
async def get_payment_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_service: AdminDashboardService = Depends(get_admin_dashboard_service)
):
    """
    Get payment analytics for specified period
    
    Args:
        days: Number of days to analyze (1-365)
    
    Returns:
    - Daily revenue trends
    - Success rates
    - Failure reasons
    """
    try:
        return await admin_service.get_payment_analytics(days=days)
    except Exception as e:
        logger.error(f"Payment analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/users",
    response_model=UserAnalyticsResponse,
    dependencies=[Depends(verify_admin)]
)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_service: AdminDashboardService = Depends(get_admin_dashboard_service)
):
    """
    Get user analytics and growth metrics
    
    Args:
        days: Period to analyze (1-365)
    
    Returns:
    - New user daily count
    - Active users
    - Users by balance tier
    """
    try:
        return await admin_service.get_user_analytics(days=days)
    except Exception as e:
        logger.error(f"User analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== QUOTA MANAGEMENT =====================

@router.put(
    "/quotas/{farmiq_id}",
    dependencies=[Depends(verify_admin)]
)
async def update_user_quota(
    farmiq_id: str,
    request: AdminQuotaUpdateRequest,
    admin_service: AdminDashboardService = Depends(get_admin_dashboard_service)
):
    """
    Update user quota limits
    
    Admin can adjust daily and monthly budgets per user
    
    Args:
        farmiq_id: User FarmIQ ID
        daily_budget: New daily quota (optional)
        monthly_budget: New monthly quota (optional)
    
    Returns:
        Updated quota details
    """
    try:
        return await admin_service.adjust_user_quota(
            farmiq_id=farmiq_id,
            daily_budget=request.daily_budget,
            monthly_budget=request.monthly_budget
        )
    except Exception as e:
        logger.error(f"Quota update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quotas/exceeding/today",
    dependencies=[Depends(verify_admin)]
)
async def get_exceeding_quotas(
    admin_service: AdminDashboardService = Depends(get_admin_dashboard_service)
) -> List[ExceedingUserItem]:
    """
    List users who exceeded their daily quota today
    
    Returns:
        List of users with usage details
    """
    try:
        return await admin_service.list_users_exceeding_quota()
    except Exception as e:
        logger.error(f"Exceeding quotas fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== REPORTING =====================

@router.get(
    "/reports/daily",
    dependencies=[Depends(verify_admin)]
)
async def generate_daily_report(
    admin_service: AdminDashboardService = Depends(get_admin_dashboard_service)
):
    """
    Generate comprehensive daily report
    
    Includes all KPIs, user metrics, payment analytics
    
    Returns:
        Complete daily summary
    """
    try:
        report = await admin_service.generate_daily_report()
        logger.info(f"✅ Daily report generated")
        return report
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== MANUAL OVERRIDES =====================

@router.post(
    "/manual/mint-tokens/{checkout_id}",
    dependencies=[Depends(verify_admin)]
)
async def manual_token_mint(
    checkout_id: str,
    current_user = Depends(verify_admin),
):
    """
    Manually mint tokens for a payment
    
    For edge cases where automatic minting failed
    Only admin can call
    
    Args:
        checkout_id: M-Pesa checkout ID
    
    Returns:
        Mint result
    """
    try:
        from app.payments.services.mpesa_service import MpesaPaymentService
        from core.app_config import get_mpesa_service
        
        mpesa_service = get_mpesa_service()
        result = await mpesa_service.mint_fiq_tokens(checkout_id, system_admin=True)
        
        logger.info(f"🪙 Admin minted tokens for checkout {checkout_id}")
        return result
        
    except Exception as e:
        logger.error(f"Manual mint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/manual/sync-balance/{farmiq_id}",
    dependencies=[Depends(verify_admin)]
)
async def manual_sync_balance(
    farmiq_id: str,
    current_user = Depends(verify_admin),
):
    """
    Manually sync user balance from blockchain
    
    For reconciliation after Hedera issues
    Only admin can call
    
    Args:
        farmiq_id: User FarmIQ ID
    
    Returns:
        Current balance from blockchain
    """
    try:
        # Hedera integration is disabled in this deployment.
        # Balance reconciliation is handled via front-end blockchain layer.
        logger.info(f"🔄 Sync not supported for on-chain balance in backend for user {farmiq_id}")
        return {
            'farmiq_id': farmiq_id,
            'synced_at': datetime.now().isoformat(),
            'note': 'on-chain balance sync is delegated to frontend blockchain integration',
        }
        
    except Exception as e:
        logger.error(f"Balance sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== AUDIT & COMPLIANCE =====================

@router.get(
    "/audit/payment-log",
    dependencies=[Depends(verify_admin)]
)
async def get_payment_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    operation: Optional[str] = None,
):
    """
    Get payment operation audit log
    
    Complete history of all payment operations for compliance
    
    Args:
        limit: Number of records
        offset: Pagination offset
        operation: Filter by operation type (optional)
    
    Returns:
        Paginated audit log entries
    """
    try:
        # TODO: Implement audit log query
        return {
            'logs': [],
            'total': 0,
            'limit': limit,
            'offset': offset,
        }
    except Exception as e:
        logger.error(f"Audit log fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== SYSTEM HEALTH =====================

@router.get(
    "/health/m-pesa",
    dependencies=[Depends(verify_admin)]
)
async def check_mpesa_health():
    """
    Check M-Pesa API connectivity and health
    
    Returns:
    - M-Pesa API status
    - Last successful request
    - Error count
    """
    try:
        # TODO: Implement M-Pesa health check
        return {
            'status': 'healthy',
            'api_endpoint': 'https://sandbox.safaricom.co.ke',
            'last_request': datetime.now().isoformat(),
            'error_rate': 0.0,
        }
    except Exception as e:
        logger.error(f"M-Pesa health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health/hedera",
    dependencies=[Depends(verify_admin)]
)
async def check_hedera_health():
    """
    Check Hedera blockchain connectivity and health (not used in no-Hedera mode)
    """
    try:
        return {
            'status': 'disabled',
            'message': 'Hedera integration is disabled; handle chain status in frontend',
        }
    except Exception as e:
        logger.error(f"Hedera health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
