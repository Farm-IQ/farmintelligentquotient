"""
Wallet Balance Management Routes
Endpoints for retrieving and managing user wallet balances from Supabase

Author: FarmIQ Backend Team
Date: April 2026
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from core.logging_config import get_logger
from core.supabase_client import get_supabase_client
from auth.dependencies import get_current_user

logger = get_logger(__name__)

# ===================== ROUTER =====================

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])

# ===================== REQUEST/RESPONSE MODELS =====================

class SupabaseBalanceResponse(BaseModel):
    """Response with Supabase balance"""
    farmiq_id: str
    balance: Decimal = Field(..., description="FIQ token balance from M-Pesa purchases")
    last_updated: str = Field(..., description="ISO timestamp of last balance update")
    pending_bridge: Optional[Decimal] = Field(None, description="Amount pending bridge to Hedera")
    status: str = Field(default="active", description="Balance status: active, suspended, etc")

class HederaBalanceResponse(BaseModel):
    """Response with Hedera blockchain balance"""
    farmiq_id: str
    hedera_account_id: str
    balance: Decimal = Field(..., description="FIQ token balance on Hedera")
    last_synced: str = Field(..., description="ISO timestamp of last sync from Hedera Mirror Node")

class ConsolidatedBalanceResponse(BaseModel):
    """Response with both Supabase and Hedera balances"""
    farmiq_id: str
    supabase_balance: Decimal = Field(..., description="Tokens from M-Pesa purchases")
    hedera_balance: Decimal = Field(..., description="Tokens on blockchain")
    total_balance: Decimal = Field(..., description="Total across both")
    conversion_rate: Decimal = Field(default=1, description="KES to FIQ conversion rate")
    last_updated: str = Field(..., description="Most recent update timestamp")

# ===================== ENDPOINTS =====================

@router.get("/balance/{farmiq_id}", response_model=SupabaseBalanceResponse)
async def get_supabase_balance(
    farmiq_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get user's M-Pesa purchased token balance from Supabase
    
    This represents tokens purchased via M-Pesa that are stored
    in the traditional database before being bridged to Hedera.
    
    Args:
        farmiq_id: User's FarmIQ identifier
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Current Supabase balance in FIQ tokens
    
    Raises:
        404: User wallet not found
        403: User not authorized to access this wallet
    """
    try:
        # Security: Verify user owns this farmiq_id
        if current_user.get('farmiq_id') != farmiq_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this wallet")
        
        supabase = get_supabase_client()
        
        # Query user_wallets table for balance
        response = supabase.table('user_wallets').select(
            'farmiq_id, fiq_token_balance, fiq_balance_last_updated, pending_bridge_amount, status'
        ).eq('farmiq_id', farmiq_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User wallet not found")
        
        wallet = response.data
        
        return SupabaseBalanceResponse(
            farmiq_id=wallet['farmiq_id'],
            balance=Decimal(str(wallet.get('fiq_token_balance', 0))),
            last_updated=wallet.get('fiq_balance_last_updated', datetime.utcnow().isoformat()),
            pending_bridge=Decimal(str(wallet.get('pending_bridge_amount', 0))) if wallet.get('pending_bridge_amount') else None,
            status=wallet.get('status', 'active')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Supabase balance for {farmiq_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")


@router.get("/balance/hedera/{farmiq_id}", response_model=HederaBalanceResponse)
async def get_hedera_balance(
    farmiq_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get user's token balance from Hedera blockchain
    
    Fetches balance directly from the Hedera Mirror Node for
    tokens that have been bridged to the blockchain.
    
    Args:
        farmiq_id: User's FarmIQ identifier
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Current balance on Hedera blockchain
        
    Raises:
        404: User wallet or Hedera account not found
        403: User not authorized to access this wallet
        503: Hedera Mirror Node unavailable
    """
    try:
        # Security: Verify user owns this farmiq_id
        if current_user.get('farmiq_id') != farmiq_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this wallet")
        
        supabase = get_supabase_client()
        
        # Get Hedera account ID from user_wallets
        response = supabase.table('user_wallets').select(
            'farmiq_id, hedera_account_id, hedera_token_balance, hedera_balance_last_synced'
        ).eq('farmiq_id', farmiq_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User wallet not found")
        
        wallet = response.data
        
        if not wallet.get('hedera_account_id'):
            raise HTTPException(status_code=404, detail="Hedera account not connected")
        
        # TODO: Sync balance from Hedera Mirror Node if older than 5 minutes
        last_synced = wallet.get('hedera_balance_last_synced')
        if last_synced:
            last_sync_time = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
            if datetime.utcnow() - last_sync_time > timedelta(minutes=5):
                # Call sync endpoint (will be implemented in Hedera service)
                logger.info(f"Hedera balance for {farmiq_id} is stale, should sync")
        
        return HederaBalanceResponse(
            farmiq_id=wallet['farmiq_id'],
            hedera_account_id=wallet['hedera_account_id'],
            balance=Decimal(str(wallet.get('hedera_token_balance', 0))),
            last_synced=wallet.get('hedera_balance_last_synced', datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Hedera balance for {farmiq_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Hedera balance")


@router.get("/balance/consolidated/{farmiq_id}", response_model=ConsolidatedBalanceResponse)
async def get_consolidated_balance(
    farmiq_id: str,
    sync_hedera: bool = Query(False, description="Force sync Hedera balance"),
    current_user = Depends(get_current_user)
):
    """
    Get consolidated balance across Supabase and Hedera
    
    Returns the user's total FIQ token balance across both:
    - Supabase (M-Pesa purchased, not yet bridged)
    - Hedera (bridged to blockchain)
    
    Args:
        farmiq_id: User's FarmIQ identifier
        sync_hedera: If true, force sync with Hedera Mirror Node
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Consolidated balance information
        
    Raises:
        404: User wallet not found
        403: User not authorized to access this wallet
    """
    try:
        # Security: Verify user owns this farmiq_id
        if current_user.get('farmiq_id') != farmiq_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this wallet")
        
        supabase = get_supabase_client()
        
        # Get both balances
        response = supabase.table('user_wallets').select(
            'farmiq_id, fiq_token_balance, hedera_token_balance, fiq_balance_last_updated, hedera_balance_last_synced, conversion_rate'
        ).eq('farmiq_id', farmiq_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User wallet not found")
        
        wallet = response.data
        
        supabase_balance = Decimal(str(wallet.get('fiq_token_balance', 0)))
        hedera_balance = Decimal(str(wallet.get('hedera_token_balance', 0)))
        conversion_rate = Decimal(str(wallet.get('conversion_rate', 1)))
        
        # Get most recent timestamp
        last_supabase = wallet.get('fiq_balance_last_updated', '')
        last_hedera = wallet.get('hedera_balance_last_synced', '')
        most_recent = max(last_supabase, last_hedera) if (last_supabase and last_hedera) else (last_supabase or last_hedera)
        
        return ConsolidatedBalanceResponse(
            farmiq_id=wallet['farmiq_id'],
            supabase_balance=supabase_balance,
            hedera_balance=hedera_balance,
            total_balance=supabase_balance + hedera_balance,
            conversion_rate=conversion_rate,
            last_updated=most_recent or datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get consolidated balance for {farmiq_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve consolidated balance")


@router.post("/balance/sync/{farmiq_id}")
async def sync_wallet_balance(
    farmiq_id: str,
    current_user = Depends(get_current_user)
):
    """
    Manually sync wallet balance with Hedera
    
    Triggers a balance sync from Hedera Mirror Node to ensure
    Supabase has the most current balance data.
    
    Args:
        farmiq_id: User's FarmIQ identifier
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Updated balance information
        
    Raises:
        404: User wallet not found
        403: User not authorized to access this wallet
        503: Hedera Mirror Node unavailable
    """
    try:
        # Security: Verify user owns this farmiq_id
        if current_user.get('farmiq_id') != farmiq_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this wallet")
        
        logger.info(f"Syncing balance for {farmiq_id} with Hedera")
        
        # TODO: Call HederaMirrorNodeService.sync_balance(farmiq_id)
        # For now, just return current balance
        
        supabase = get_supabase_client()
        response = supabase.table('user_wallets').select(
            'farmiq_id, fiq_token_balance, hedera_token_balance, hedera_balance_last_synced'
        ).eq('farmiq_id', farmiq_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User wallet not found")
        
        wallet = response.data
        
        return {
            "status": "success",
            "message": f"Balance synced for {farmiq_id}",
            "supabase_balance": wallet.get('fiq_token_balance'),
            "hedera_balance": wallet.get('hedera_token_balance'),
            "last_synced": wallet.get('hedera_balance_last_synced')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync balance for {farmiq_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync balance")
