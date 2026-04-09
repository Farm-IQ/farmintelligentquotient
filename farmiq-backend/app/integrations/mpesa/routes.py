"""
M-Pesa Routes - FastAPI endpoints for M-Pesa operations
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging
import json

from app.integrations.mpesa.schemas import (
    StkPushRequest,
    StkPushResponse,
    StkPushStatusRequest,
    ReversalRequest,
    TaxRemittanceRequest,
    TransactionStatusRequest,
)
from app.integrations.mpesa.mpesa_service import MpesaService
from app.integrations.mpesa.daraja_client import DarajaClient, DarajaEnvironment
from core.database import get_db_pool
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mpesa", tags=["mpesa"])


# ============================================================================
# Dependencies
# ============================================================================

async def get_mpesa_service(db_pool = Depends(get_db_pool)) -> MpesaService:
    """Dependency to get M-Pesa service"""
    
    # Initialize Daraja client
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
    business_shortcode = os.getenv("MPESA_BUSINESS_SHORTCODE", "174379")
    passkey = os.getenv("MPESA_PASSKEY")
    environment = os.getenv("MPESA_ENVIRONMENT", "sandbox")
    
    env = DarajaEnvironment.SANDBOX if environment == "sandbox" else DarajaEnvironment.PRODUCTION
    
    daraja_client = DarajaClient(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        business_shortcode=business_shortcode,
        passkey=passkey,
        environment=env
    )
    
    return MpesaService(daraja_client, db_pool)


# ============================================================================
# STK Push (M-Pesa Express) Endpoints
# ============================================================================

@router.post("/token-purchase", response_model=Dict[str, Any])
async def initiate_token_purchase(
    request: StkPushRequest,
    user_id: str = Query(..., description="FarmIQ user ID"),
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Initiate FIQ token purchase via M-Pesa STK Push
    
    Request:
    {
        "phone_number": "254712345678",
        "amount": 500,
        "account_reference": "500FIQ",
        "transaction_desc": "Token Purchase",
        "callback_url": "https://..."
    }
    """
    
    try:
        logger.info(f"Token purchase request: {user_id} - {request.amount} FIQ")
        
        result = await mpesa_service.initiate_token_purchase(
            user_id=user_id,
            phone_number=request.phone_number,
            fiq_amount=int(request.amount),
            callback_url=request.callback_url
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Token purchase error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-status")
async def check_payment_status(
    checkout_request_id: str = Query(..., description="CheckoutRequestID from STK Push"),
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Check status of STK Push payment request
    
    Query params:
        - checkout_request_id: CheckoutRequestID from STK Push response
    """
    
    try:
        result = await mpesa_service.check_payment_status(checkout_request_id)
        return result
    
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Account Operations
# ============================================================================

@router.get("/account-balance")
async def get_account_balance(
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Query M-Pesa account balance
    
    Requires M-Pesa initiator credentials from environment
    """
    
    try:
        initiator_name = os.getenv("MPESA_INITIATOR_NAME", "testapi")
        initiator_password = os.getenv("MPESA_INITIATOR_PASSWORD", "")
        queue_timeout_url = os.getenv("MPESA_QUEUE_TIMEOUT_URL")
        result_url = os.getenv("MPESA_RESULT_URL")
        
        if not all([initiator_name, initiator_password, queue_timeout_url, result_url]):
            raise ValueError("Missing M-Pesa initiator credentials")
        
        result = await mpesa_service.get_account_balance(
            initiator_name=initiator_name,
            initiator_password=initiator_password,
            queue_timeout_url=queue_timeout_url,
            result_url=result_url
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Balance query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Transaction Queries
# ============================================================================

@router.post("/transaction-status")
async def query_transaction_status(
    request: TransactionStatusRequest,
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Query specific M-Pesa transaction status
    
    Request:
    {
        "transaction_id": "PDS123456789",
        "initiator_name": "testapi",
        "initiator_password": "...",
        "queue_timeout_url": "https://...",
        "result_url": "https://..."
    }
    """
    
    try:
        result = await mpesa_service.query_transaction_status(
            transaction_id=request.transaction_id,
            initiator_name=request.initiator_name,
            initiator_password=request.initiator_password,
            queue_timeout_url=request.queue_timeout_url,
            result_url=request.result_url
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Transaction query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Reversals
# ============================================================================

@router.post("/reverse")
async def reverse_transaction(
    request: ReversalRequest,
    user_id: Optional[str] = Query(None, description="FarmIQ user ID"),
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Reverse M-Pesa transaction
    
    Request:
    {
        "transaction_id": "PDS123456789",
        "amount": 500,
        "initiator_name": "testapi",
        "initiator_password": "...",
        "queue_timeout_url": "https://...",
        "result_url": "https://...",
        "remarks": "Refund"
    }
    """
    
    try:
        logger.info(f"Reversal request: {request.transaction_id} ({request.amount} KES)")
        
        result = await mpesa_service.reverse_transaction(
            transaction_id=request.transaction_id,
            amount=request.amount,
            initiator_name=request.initiator_name,
            initiator_password=request.initiator_password,
            queue_timeout_url=request.queue_timeout_url,
            result_url=request.result_url,
            user_id=user_id,
            reason=request.remarks
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Reversal error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Tax Remittance
# ============================================================================

@router.post("/remit-tax")
async def remit_tax(
    request: TaxRemittanceRequest,
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Remit taxes to KRA
    
    Request:
    {
        "amount": 50000,
        "prn": "A000123456B",
        "initiator_name": "testapi",
        "initiator_password": "...",
        "queue_timeout_url": "https://...",
        "result_url": "https://...",
        "remarks": "Monthly tax payment"
    }
    """
    
    try:
        logger.info(f"Tax remittance request: {request.prn} ({request.amount} KES)")
        
        result = await mpesa_service.remit_tax(
            prn=request.prn,
            amount=request.amount,
            initiator_name=request.initiator_name,
            initiator_password=request.initiator_password,
            queue_timeout_url=request.queue_timeout_url,
            result_url=request.result_url,
            tax_period=None
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Tax remittance error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# M-Pesa Callback Endpoints
# ============================================================================

@router.post("/callback/stk-push")
async def stk_push_callback(
    request: Request,
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """
    Webhook endpoint for STK Push callbacks from M-Pesa
    
    M-Pesa posts:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "...",
                "CheckoutRequestID": "...",
                "ResultCode": 0,
                "ResultDesc": "...",
                "CallbackMetadata": { ... }
            }
        }
    }
    """
    
    try:
        body = await request.json()
        
        logger.info(f"STK Push callback received")
        
        # Extract callback data
        stk_callback = body.get("Body", {}).get("stkCallback", {})
        result_code = stk_callback.get("ResultCode")
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        
        # Log callback to database
        db = await db_pool.acquire()
        try:
            query = """
            INSERT INTO mpesa_callbacks (
                callback_type, checkout_request_id, result_code,
                result_desc, raw_payload, source_ip, received_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW());
            """
            
            await db.execute(
                query,
                "stk_push",
                checkout_request_id,
                result_code,
                stk_callback.get("ResultDesc"),
                json.dumps(stk_callback),
                request.client.host if request.client else None
            )
        
        finally:
            await db_pool.release(db)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"STK Push callback error: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}


@router.post("/callback/balance")
async def balance_callback(
    request: Request,
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """Webhook endpoint for account balance query callbacks"""
    
    try:
        body = await request.json()
        
        logger.info(f"Balance callback received")
        
        result = body.get("Result", {})
        result_code = result.get("ResultCode")
        conversation_id = result.get("ConversationID")
        
        # Log callback
        db = await db_pool.acquire()
        try:
            query = """
            INSERT INTO mpesa_callbacks (
                callback_type, conversation_id, result_code,
                result_desc, raw_payload, source_ip, received_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW());
            """
            
            await db.execute(
                query,
                "balance",
                conversation_id,
                result_code,
                result.get("ResultDesc"),
                json.dumps(result),
                request.client.host if request.client else None
            )
        
        finally:
            await db_pool.release(db)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Balance callback error: {str(e)}", exc_info=True)
        return {"status": "error"}


@router.post("/callback/transaction-status")
async def transaction_status_callback(
    request: Request,
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """Webhook endpoint for transaction status query callbacks"""
    
    try:
        body = await request.json()
        
        logger.info(f"Transaction status callback received")
        
        result = body.get("Result", {})
        result_code = result.get("ResultCode")
        transaction_id = result.get("TransactionID")
        
        # Log callback
        db = await db_pool.acquire()
        try:
            query = """
            INSERT INTO mpesa_callbacks (
                callback_type, request_id, result_code,
                result_desc, raw_payload, source_ip, received_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW());
            """
            
            await db.execute(
                query,
                "transaction_status",
                transaction_id,
                result_code,
                result.get("ResultDesc"),
                json.dumps(result),
                request.client.host if request.client else None
            )
        
        finally:
            await db_pool.release(db)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Transaction status callback error: {str(e)}", exc_info=True)
        return {"status": "error"}


@router.post("/callback/reversal")
async def reversal_callback(
    request: Request,
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """Webhook endpoint for reversal callbacks"""
    
    try:
        body = await request.json()
        
        logger.info(f"Reversal callback received")
        
        result = body.get("Result", {})
        result_code = result.get("ResultCode")
        conversation_id = result.get("ConversationID")
        
        # Log callback
        db = await db_pool.acquire()
        try:
            query = """
            INSERT INTO mpesa_callbacks (
                callback_type, conversation_id, result_code,
                result_desc, raw_payload, source_ip, received_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW());
            """
            
            await db.execute(
                query,
                "reversal",
                conversation_id,
                result_code,
                result.get("ResultDesc"),
                json.dumps(result),
                request.client.host if request.client else None
            )
        
        finally:
            await db_pool.release(db)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Reversal callback error: {str(e)}", exc_info=True)
        return {"status": "error"}


@router.post("/callback/tax-remittance")
async def tax_remittance_callback(
    request: Request,
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """Webhook endpoint for tax remittance callbacks"""
    
    try:
        body = await request.json()
        
        logger.info(f"Tax remittance callback received")
        
        result = body.get("Result", {})
        result_code = result.get("ResultCode")
        conversation_id = result.get("ConversationID")
        
        # Log callback
        db = await db_pool.acquire()
        try:
            query = """
            INSERT INTO mpesa_callbacks (
                callback_type, conversation_id, result_code,
                result_desc, raw_payload, source_ip, received_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW());
            """
            
            await db.execute(
                query,
                "tax_remittance",
                conversation_id,
                result_code,
                result.get("ResultDesc"),
                json.dumps(result),
                request.client.host if request.client else None
            )
        
        finally:
            await db_pool.release(db)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Tax remittance callback error: {str(e)}", exc_info=True)
        return {"status": "error"}


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check(
    mpesa_service: MpesaService = Depends(get_mpesa_service)
) -> Dict[str, Any]:
    """
    Health check - Verify M-Pesa connectivity
    """
    
    try:
        # Try to get access token
        token = await mpesa_service.daraja.get_access_token()
        
        return {
            "status": "healthy",
            "service": "M-Pesa Daraja",
            "shortcode": mpesa_service.daraja.business_shortcode,
            "environment": mpesa_service.daraja.base_url,
        }
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
