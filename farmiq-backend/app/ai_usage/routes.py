"""
AI Usage Tracking API Routes
Exposes endpoints for balance checks, usage history, audits, and quota management
"""

import os
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.ai_usage.services.usage_tracker import AIUsageTracker
# from core.security import get_current_user  # TODO: Implement proper auth

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/ai-usage", tags=["AI Usage Tracking"])
tracker = AIUsageTracker()


# ===================== Pydantic Models =====================

class BalanceResponse(BaseModel):
    balance: float
    unit: str = "FIQ"
    last_updated: Optional[datetime]


class UsageLogEntry(BaseModel):
    id: str
    service_type: str
    operation: str
    tokens_deducted: float
    balance_after: float
    success: bool
    duration_ms: Optional[int]
    created_at: datetime


class UsageSummary(BaseModel):
    service_type: str
    usage_date: str
    call_count: int
    total_tokens_used: float
    success_count: int
    failure_count: int


class QuotaStatus(BaseModel):
    daily_budget: Optional[float]
    daily_remaining: Optional[float]
    daily_used: Optional[float]
    monthly_budget: Optional[float]
    monthly_remaining: Optional[float]
    monthly_used: Optional[float]


class QuotaUpdate(BaseModel):
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None


class AuditLog(BaseModel):
    hcs_sequence_number: int
    hcs_message_hash: str
    log_type: str
    created_at: datetime


# ===================== Endpoints =====================

@router.get("/balance/{farmiq_id}", response_model=BalanceResponse)
async def get_token_balance(
    farmiq_id: str,
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Get user's current FIQ token balance
    
    Args:
        farmiq_id: User's FarmIQ identifier
    
    Returns:
        Current balance in FIQ tokens
    """
    try:
        # Verify user owns this farmiq_id (security check)
        wallet = await tracker.db.fetch_one(
            "SELECT fiq_token_balance, fiq_balance_last_updated FROM user_wallets WHERE farmiq_id = :id",
            {'id': farmiq_id}
        )
        
        if not wallet:
            raise HTTPException(status_code=404, detail="User wallet not found")
        
        return BalanceResponse(
            balance=wallet['fiq_token_balance'],
            last_updated=wallet['fiq_balance_last_updated']
        )
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")


@router.get("/usage/history/{farmiq_id}", response_model=List[UsageLogEntry])
async def get_usage_history(
    farmiq_id: str,
    service_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Get AI usage history for user
    
    Args:
        farmiq_id: User's FarmIQ identifier
        service_type: Filter by service (FARMSCORE, FARMGROW, etc)
        limit: Max results (1-500, default 50)
    
    Returns:
        List of usage logs
    """
    try:
        logs = await tracker.get_usage_history(
            farmiq_id=farmiq_id,
            service_type=service_type,
            limit=limit
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/summary/{farmiq_id}", response_model=List[UsageSummary])
async def get_usage_summary(
    farmiq_id: str,
    days: int = Query(30, ge=1, le=365),
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Get aggregated daily usage summary
    
    Args:
        farmiq_id: User's FarmIQ identifier
        days: Number of days to summarize (1-365, default 30)
    
    Returns:
        Daily usage summaries
    """
    try:
        query = """
            SELECT 
                service_type,
                usage_date,
                call_count,
                total_tokens_used,
                success_count,
                failure_count
            FROM daily_ai_usage_summary
            WHERE farmiq_id = :farmiq_id AND usage_date >= CURRENT_DATE - :days
            ORDER BY usage_date DESC
        """
        
        summaries = await tracker.db.fetch(
            query,
            {'farmiq_id': farmiq_id, 'days': days}
        )
        
        return [dict(s) for s in summaries] if summaries else []
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")


@router.get("/quota/{farmiq_id}", response_model=QuotaStatus)
async def get_quota_status(
    farmiq_id: str,
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Get user's current quota status and remaining budget
    
    Args:
        farmiq_id: User's FarmIQ identifier
    
    Returns:
        Daily and monthly quota information
    """
    try:
        quota = await tracker.check_quota_status(farmiq_id)
        
        if not quota:
            return QuotaStatus(
                daily_budget=None,
                daily_remaining=None,
                daily_used=None,
                monthly_budget=None,
                monthly_remaining=None,
                monthly_used=None,
            )
        
        return QuotaStatus(**quota)
    except Exception as e:
        logger.error(f"Failed to get quota: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quota")


@router.post("/quota/{farmiq_id}")
async def set_quota(
    farmiq_id: str,
    quota_update: QuotaUpdate,
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Set or update user's token spending quota
    
    Args:
        farmiq_id: User's FarmIQ identifier
        quota_update: Daily and/or monthly budget in FIQ
    
    Returns:
        Confirmation of quota update
    """
    try:
        success = await tracker.set_user_quota(
            farmiq_id=farmiq_id,
            daily_budget=quota_update.daily_budget,
            monthly_budget=quota_update.monthly_budget,
        )
        
        if success:
            logger.info(
                f"✅ Quota set",
                farmiq_id=farmiq_id,
                daily=quota_update.daily_budget,
                monthly=quota_update.monthly_budget,
            )
            return {
                'status': 'success',
                'message': 'Quota updated',
                'daily_budget': quota_update.daily_budget,
                'monthly_budget': quota_update.monthly_budget,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to set quota")
    except Exception as e:
        logger.error(f"Failed to set quota: {e}")
        raise HTTPException(status_code=500, detail="Failed to set quota")


@router.get("/audit/{farmiq_id}", response_model=List[AuditLog])
async def get_hcs_audit_trail(
    farmiq_id: str,
    limit: int = Query(50, ge=1, le=500),
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Get immutable HCS audit log references
    
    Args:
        farmiq_id: User's FarmIQ identifier
        limit: Max results (1-500, default 50)
    
    Returns:
        List of HCS audit log references
    """
    try:
        query = """
            SELECT 
                hcs_sequence_number,
                hcs_message_hash,
                log_type,
                created_at
            FROM hcs_audit_references
            WHERE farmiq_id = :farmiq_id
            ORDER BY created_at DESC
            LIMIT :limit
        """
        
        audits = await tracker.db.fetch(
            query,
            {'farmiq_id': farmiq_id, 'limit': limit}
        )
        
        return [dict(a) for a in audits] if audits else []
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")


@router.get("/stats/service-breakdown")
async def get_service_statistics():
    """
    Get overall service usage statistics (admin only)
    
    Returns:
        Usage breakdown by service type
    """
    try:
        query = """
            SELECT * FROM v_service_usage_stats
            ORDER BY total_calls DESC
        """
        
        stats = await tracker.db.fetch(query)
        return [dict(s) for s in stats] if stats else []
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/stats/top-users")
async def get_top_users(
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get top users by token usage in last 30 days (admin only)
    
    Args:
        limit: Number of top users to return
    
    Returns:
        List of top users
    """
    try:
        query = """
            SELECT * FROM v_top_users_30days
            LIMIT :limit
        """
        
        users = await tracker.db.fetch(query, {'limit': limit})
        return [dict(u) for u in users] if users else []
    except Exception as e:
        logger.error(f"Failed to get top users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve top users")


@router.get("/compliance/events/{farmiq_id}")
async def get_compliance_events(
    farmiq_id: str,
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Get compliance and audit events for user
    
    Args:
        farmiq_id: User's FarmIQ identifier
        severity: Filter by severity (INFO, WARNING, CRITICAL)
        limit: Max results
    
    Returns:
        List of compliance events
    """
    try:
        query = """
            SELECT 
                id, event_type, severity, event_details,
                resolved, created_at
            FROM compliance_logs
            WHERE farmiq_id = :farmiq_id
        """
        params = {'farmiq_id': farmiq_id}
        
        if severity:
            query += " AND severity = :severity"
            params['severity'] = severity
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        events = await tracker.db.fetch(query, params)
        return [dict(e) for e in events] if events else []
    except Exception as e:
        logger.error(f"Failed to get compliance events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance events")


@router.post("/debug/sync-balance/{farmiq_id}")
async def sync_balance_from_hedera(
    farmiq_id: str,
    # current_user=Depends(get_current_user),  # TODO: Add auth
):
    """
    Manually sync user's balance from Hedera to Supabase
    Useful for auditing or recovering lost data
    
    Args:
        farmiq_id: User's FarmIQ identifier
    
    Returns:
        Sync result
    """
    try:
        wallet = await tracker.db.fetch_one(
            "SELECT hedera_wallet_id FROM user_wallets WHERE farmiq_id = :id",
            {'id': farmiq_id}
        )
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Query Hedera for balance
        balance_hts = await tracker.hts.get_account_token_balance(
            account_id=wallet['hedera_wallet_id'],
            token_id=os.getenv('HEDERA_FIQ_TOKEN_ID'),
        )
        
        balance_fiq = (balance_hts or 0) / 100 if balance_hts else 0
        
        # Update Supabase
        await tracker.db.execute("""
            UPDATE user_wallets
            SET fiq_token_balance = :balance,
                fiq_balance_last_updated = NOW()
            WHERE farmiq_id = :farmiq_id
        """, {
            'balance': balance_fiq,
            'farmiq_id': farmiq_id,
        })
        
        logger.info(
            f"✅ Balance synced",
            farmiq_id=farmiq_id,
            balance=balance_fiq,
        )
        
        return {
            'status': 'success',
            'balance': balance_fiq,
            'synced_at': datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to sync balance: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync balance")
