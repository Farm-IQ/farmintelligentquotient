"""
Payment & Escrow API Routes
Endpoints for M-Pesa payments, escrow management, and reversals

Author: FarmIQ Backend Team
Date: March 2026
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
import logging

from core.logging_config import get_logger
from auth.dependencies import get_current_user
from app.payments.services.mpesa_service import MpesaPaymentService

logger = get_logger(__name__)

# ===================== ROUTER & DEPENDENCIES =====================

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Injection functions (configure in main.py)
async def get_mpesa_service() -> MpesaPaymentService:
    from core.app_config import get_mpesa_service as _get_mpesa_service
    return _get_mpesa_service()

# ===================== REQUEST/RESPONSE MODELS =====================

class PaymentInitiateRequest(BaseModel):
    """Request to initiate M-Pesa payment"""
    phone_number: str = Field(..., description="M-Pesa phone (2547xxxxxx)")
    amount_kes: Decimal = Field(..., gt=0, description="Amount in Kenya Shillings")

class PaymentInitiateResponse(BaseModel):
    """Response after STK Push initiated"""
    checkout_id: str
    status: str
    phone_number: str
    amount_kes: Decimal
    tokens_to_purchase: Decimal
    stk_push_sent_at: str

class PaymentStatusResponse(BaseModel):
    """Current payment status"""
    checkout_id: str
    status: str
    amount_kes: Decimal
    tokens_purchased: Decimal
    created_at: datetime
    stk_push_sent_at: datetime
    first_callback_at: Optional[datetime] = None
    mpesa_receipt: Optional[str] = None

class PaymentHistoryItem(BaseModel):
    """Single payment in history"""
    checkout_id: str
    amount_kes: Decimal
    tokens_purchased: Decimal
    payment_status: str
    created_at: datetime
    mpesa_receipt_number: Optional[str] = None

class PaymentHistoryResponse(BaseModel):
    """List of user payments"""
    transactions: list[PaymentHistoryItem]
    total: int
    limit: int
    offset: int

class EscrowStatusRequest(BaseModel):
    """Request escrow status"""
    farm_id: str

class EscrowStatusResponse(BaseModel):
    """Escrow account status"""
    loan_id: str
    tokens_locked: Decimal
    escrow_status: str
    release_condition: str
    condition_met: bool
    hours_until_expiry: float
    created_at: datetime

class ReversalRequestBody(BaseModel):
    """Request token reversal"""
    checkout_id: str
    reason: Optional[str] = "User requested refund"

class ReversalStatusResponse(BaseModel):
    """Reversal status"""
    reversal_id: str
    status: str
    tokens_to_refund: Decimal
    refund_amount_kes: Decimal
    hours_remaining: float
    created_at: datetime

# ===================== M-PESA PAYMENT ENDPOINTS =====================

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    current_user = Depends(get_current_user),
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Initiate M-Pesa STK Push payment
    
    Prompts user to enter M-Pesa PIN on their phone
    Returns checkout_id for status polling
    
    Args:
        phone_number: M-Pesa phone in format 2547xxxxxx
        amount_kes: Payment amount in Kenya Shillings
    
    Returns:
        Payment initiation details with checkout_id for tracking
    """
    try:
        result = await mpesa_service.initiate_stk_push(
            phone_number=request.phone_number,
            amount_kes=request.amount_kes,
            farmiq_id=current_user.farmiq_id,
            user_id=current_user.user_id
        )
        return result
    
    except Exception as e:
        logger.error(f"Payment initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{checkout_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    checkout_id: str,
    current_user = Depends(get_current_user),
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Check M-Pesa payment status
    
    Used by frontend to poll payment completion
    Returns current status (INITIATED, COMPLETED, FAILED, etc)
    
    Args:
        checkout_id: Checkout ID from payment initiation
    
    Returns:
        Current payment status and details
    """
    try:
        return await mpesa_service.query_payment_status(checkout_id)
    except Exception as e:
        logger.error(f"Status query failed: {str(e)}")
        raise

@router.get("/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user),
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Get user's payment history
    
    Returns list of all past purchases
    Paginated for performance
    
    Args:
        limit: Number of records (max 100)
        offset: Pagination offset
    
    Returns:
        List of payments with totals
    """
    try:
        limit = min(limit, 100)  # Cap at 100
        return await mpesa_service.get_payment_history(
            farmiq_id=current_user.farmiq_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"History query failed: {str(e)}")
        raise

# ===================== WEBHOOK ENDPOINTS =====================

@router.post("/mpesa/confirmation")
async def mpesa_confirmation_webhook(
    request: Request,
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Receive M-Pesa payment confirmation callback from Daraja API
    
    Called by Africa's Talking when user completes/cancels STK Push
    Not user-facing, called by M-Pesa servers
    
    Flow:
    1. Receive callback from M-Pesa
    2. Update transaction status to COMPLETED
    3. Trigger token minting (async background task)
    4. Return success to M-Pesa (non-blocking)
    
    Body:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "...",
                "CheckoutRequestID": "...",
                "ResultCode": 0,
                "ResultDesc": "The service request has been accepted...",
                "CallbackMetadata": {...}
            }
        }
    }
    """
    try:
        callback_data = await request.json()
        result = await mpesa_service.handle_payment_confirmation(callback_data)
        
        # If payment confirmed, mint tokens in background (non-blocking)
        if result.get("status") == "SUCCESS":
            checkout_id = result.get("checkout_id")
            logger.info(f"✅ Payment confirmed, queuing token minting: {checkout_id}")
            
            # Get farmiq_id and user_id from database for minting
            from app.payments.services.mpesa_service import MpesaPaymentService
            db_pool = mpesa_service.db_pool
            
            async def mint_tokens_async():
                """Background task to mint tokens"""
                try:
                    # Get transaction details
                    async with db_pool.acquire() as conn:
                        tx = await conn.fetchrow(
                            "SELECT farmiq_id FROM mpesa_transactions WHERE checkout_id = $1",
                            checkout_id
                        )
                    
                    if tx:
                        farmiq_id = tx["farmiq_id"]
                        logger.info(f"🪙 Minting tokens for payment: {checkout_id}")
                        
                        # Mint tokens
                        mint_result = await mpesa_service.mint_fiq_tokens(checkout_id, farmiq_id)
                        
                        logger.info(f"✅ Tokens minted: {mint_result['tokens_minted']} FIQ -> {mint_result['balance_after']}")
                    else:
                        logger.error(f"❌ Transaction not found for minting: {checkout_id}")
                
                except Exception as e:
                    logger.error(f"❌ Token minting failed (will retry): {str(e)}")
            
            # Queue minting task
            import asyncio
            asyncio.create_task(mint_tokens_async())
        
        # Always return success to M-Pesa (callback is fire-and-forget)
        return {"ResultCode": 0, "ResultDesc": "Confirmation received"}
    
    except Exception as e:
        logger.error(f"Confirmation webhook failed: {str(e)}")
        # Still return success to M-Pesa so they don't retry
        return {"ResultCode": 0, "ResultDesc": "Confirmation received"}

@router.post("/mpesa/validation")
async def mpesa_validation_webhook(request: Request):
    """
    Validate M-Pesa payment (optional validation endpoint)
    
    Called before payment completion for fraud checking
    Should respond with ResultCode 0 to approve or non-zero to reject
    """
    try:
        data = await request.json()
        logger.info(f"Payment validation request: {data.get('TransactionID')}")
        
        # TODO: Implement custom validation logic
        # - Check phone number against blocklist
        # - Verify amount within limits
        # - Check for duplicate transactions
        
        return {
            "ResultCode": 0,
            "ResultDesc": "Validation successful"
        }
    
    except Exception as e:
        logger.error(f"Validation webhook failed: {str(e)}")
        return {
            "ResultCode": 1,
            "ResultDesc": "Validation failed"
        }

# ===================== REVERSAL ENDPOINTS =====================

@router.post("/reversal/request", response_model=ReversalStatusResponse)
async def request_reversal(
    request: ReversalRequestBody,
    current_user = Depends(get_current_user),
    reversal_service: ReversalService = Depends(get_reversal_service),
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Request token reversal within 24-hour window
    
    Converts FIQ → HBAR → M-Pesa refund
    Only available within 24 hours of original purchase
    
    Args:
        checkout_id: Original payment checkout ID
        reason: Reason for reversal (optional)
    
    Returns:
        Reversal request with status and countdown
    
    Raises:
        HTTPException 400: Outside 24-hour window
        HTTPException 404: Payment not found
    """
    try:
        # Get original payment details
        payment = await mpesa_service.query_payment_status(request.checkout_id)
        
        # Initiate reversal
        result = await reversal_service.request_reversal(
            farmiq_id=current_user.farmiq_id,
            checkout_id=request.checkout_id,
            amount_kes=payment["amount_kes"]
        )
        return result
    
    except Exception as e:
        logger.error(f"Reversal request failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reversal/status/{reversal_id}", response_model=ReversalStatusResponse)
async def get_reversal_status(
    reversal_id: str,
    current_user = Depends(get_current_user),
    reversal_service: ReversalService = Depends(get_reversal_service)
):
    """
    Check reversal request status
    
    Shows current state and time remaining in 24-hour window
    
    Args:
        reversal_id: Reversal request ID
    
    Returns:
        Reversal status with countdown timer
    """
    try:
        return await reversal_service.get_reversal_status(reversal_id)
    except Exception as e:
        logger.error(f"Reversal status query failed: {str(e)}")
        raise

# ===================== ADMIN ENDPOINTS =====================

@router.post("/admin/mint-tokens/{checkout_id}")
async def admin_mint_tokens(
    checkout_id: str,
    current_user = Depends(get_current_user),
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Admin manual token minting (for edge cases)
    
    Only admin can call
    Used to manually process confirmed payments
    """
    try:
        # Check admin role
        if current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin only")
        
        result = await mpesa_service.mint_fiq_tokens(checkout_id, current_user.farmiq_id)
        return result
    
    except Exception as e:
        logger.error(f"Admin mint failed: {str(e)}")
        raise

@router.get("/admin/sync-balance/{farmiq_id}")
async def admin_sync_balance(
    farmiq_id: str,
    current_user = Depends(get_current_user),
    mpesa_service: MpesaPaymentService = Depends(get_mpesa_service)
):
    """
    Admin manual balance sync from Hedera
    
    For troubleshooting out-of-sync balances
    """
    try:
        if current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin only")
        
        result = await mpesa_service.sync_hedera_balance(farmiq_id)
        return result
    
    except Exception as e:
        logger.error(f"Admin sync failed: {str(e)}")
        raise
