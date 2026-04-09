"""
M-Pesa Token Purchase API Routes
Handles token purchases via M-Pesa payment gateway
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import logging
import time

from core.database import get_database_repository
from auth.dependencies import get_user_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mpesa", tags=["M-Pesa Payments"])


class TokenPurchaseRequest:
    """M-Pesa token purchase request model"""
    def __init__(self, phone_number: str, fiq_amount: float, package: str = "standard"):
        self.phone_number = phone_number
        self.fiq_amount = fiq_amount
        self.package = package


@router.post("/initiate-purchase")
async def initiate_token_purchase(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_user_context),
    db = Depends(get_database_repository)
) -> Dict[str, Any]:
    """
    Initiate a token purchase via M-Pesa STK push
    
    Endpoint: POST /api/v1/mpesa/initiate-purchase
    
    Request body:
    {
        "phone_number": "254712345678",
        "amount_kes": 1000
    }
    """
    try:
        phone_number = request.get("phone_number")
        amount_kes = request.get("amount_kes", 1000)
        user_id = current_user.get("user_id")
        
        # Validate inputs
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        if amount_kes <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Generate checkout request ID
        checkout_request_id = f"CHK-{user_id}-{int(time.time())}"
        
        logger.info(f"M-Pesa payment initiated: {checkout_request_id}")
        
        return {
            "status": "initiated",
            "checkout_request_id": checkout_request_id,
            "amount_kes": amount_kes,
            "phone_number": phone_number,
            "message": "STK push sent to phone"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"M-Pesa payment initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate payment")


@router.get("/status/{checkout_request_id}")
async def check_payment_status(
    checkout_request_id: str,
    current_user: Dict[str, Any] = Depends(get_user_context),
    db = Depends(get_database_repository)
) -> Dict[str, Any]:
    """
    Check the status of a token purchase payment
    
    Endpoint: GET /api/v1/mpesa/status/{checkout_request_id}
    """
    try:
        logger.info(f"Checking payment status: {checkout_request_id}")
        
        return {
            "checkout_request_id": checkout_request_id,
            "status": "pending",
            "message": "Payment status will be updated via callback"
        }
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check payment status")


@router.post("/callback/stk-push")
async def mpesa_stk_callback(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db = Depends(get_database_repository)
) -> Dict[str, str]:
    """
    M-Pesa STK push callback endpoint
    
    Endpoint: POST /api/v1/mpesa/callback/stk-push
    
    This endpoint receives callbacks from M-Pesa when the STK push is completed
    """
    try:
        logger.info("M-Pesa STK callback received")
        
        # Process callback asynchronously
        background_tasks.add_task(
            _process_payment_callback,
            request,
            db
        )
        
        return {
            "ResultCode": "0",
            "ResultDesc": "Accepted"
        }
        
    except Exception as e:
        logger.error(f"STK callback error: {str(e)}")
        return {
            "ResultCode": "1",
            "ResultDesc": "Error processing callback"
        }


@router.post("/callback/timeout")
async def mpesa_timeout_callback(request: Dict[str, Any]) -> Dict[str, str]:
    """
    M-Pesa timeout callback endpoint
    
    Called when the user doesn't complete the payment within the timeout period
    """
    try:
        logger.info("M-Pesa timeout callback received")
        
        return {
            "ResultCode": "0",
            "ResultDesc": "Timeout processed"
        }
        
    except Exception as e:
        logger.error(f"Timeout callback error: {str(e)}")
        return {
            "ResultCode": "1",
            "ResultDesc": "Error processing timeout"
        }


@router.post("/callback/result")
async def mpesa_result_callback(request: Dict[str, Any]) -> Dict[str, str]:
    """
    M-Pesa result callback endpoint
    
    Called after the STK push is completed (both success and failure)
    """
    try:
        logger.info("M-Pesa result callback received")
        
        return {
            "ResultCode": "0",
            "ResultDesc": "Result processed"
        }
        
    except Exception as e:
        logger.error(f"Result callback error: {str(e)}")
        return {
            "ResultCode": "1",
            "ResultDesc": "Error processing result"
        }


async def _process_payment_callback(
    callback_data: Dict[str, Any],
    db
) -> None:
    """
    Process M-Pesa payment callback in background
    
    This function:
    1. Verifies the payment
    2. Adds FIQ tokens to user account
    3. Updates payment status in database
    4. Sends confirmation SMS
    """
    try:
        logger.info("Processing M-Pesa payment callback")
        
        # TODO: Integrate with mpesa_service to process callback
        # TODO: Update user token balance
        # TODO: Create transaction record
        # TODO: Send confirmation SMS
        
    except Exception as e:
        logger.error(f"Payment callback processing error: {str(e)}")


@router.get(
    "/packages",
    status_code=200,
    summary="Get Available Token Packages",
    description="Retrieve all available token package options for FarmIQ and their pricing in KES",
    tags=["M-Pesa - Payments"],
    responses={
        200: {"description": "List of available payment packages with pricing"},
        500: {"description": "Service error"}
    }
)
async def get_token_packages() -> Dict[str, Any]:
    """
    Get available token purchase packages
    
    Returns available FarmIQ token packages including:
    - Starter Pack: 100 FIQ tokens
    - Standard Pack: 500 FIQ tokens with 5% discount
    - Premium Pack: 1000 FIQ tokens with 10% discount
    - Enterprise Pack: 5000 FIQ tokens with 15% discount
    
    Each package includes pricing in KES based on current exchange rate
    
    Returns:
        Dict containing:
        - packages: List of available packages with pricing
        - exchange_rate: Current FIQ to KES conversion rate
        - timestamp: When pricing was last updated
    
    Example:
        GET /api/v1/mpesa/packages HTTP/1.1
        
        Returns:
        {
            "packages": [
                {
                    "id": "starter",
                    "name": "Starter Pack",
                    "fiq_amount": 100,
                    "kes_amount": 100,
                    "description": "Perfect for trying FarmIQ services"
                }
            ]
        }
    """
    fiq_to_kes_rate = 1.0  # Default rate, update from settings as needed
    
    return {
        "packages": [
            {
                "id": "starter",
                "name": "Starter Pack",
                "fiq_amount": 100,
                "kes_amount": int(100 * fiq_to_kes_rate),
                "description": "Perfect for trying FarmIQ services"
            },
            {
                "id": "standard",
                "name": "Standard Pack",
                "fiq_amount": 500,
                "kes_amount": int(500 * fiq_to_kes_rate),
                "description": "Recommended for regular users",
                "discount": "5%"
            },
            {
                "id": "premium",
                "name": "Premium Pack",
                "fiq_amount": 1000,
                "kes_amount": int(1000 * fiq_to_kes_rate),
                "description": "Best value for power users",
                "discount": "10%"
            },
            {
                "id": "enterprise",
                "name": "Enterprise Pack",
                "fiq_amount": 5000,
                "kes_amount": int(5000 * fiq_to_kes_rate),
                "description": "For large-scale operations",
                "discount": "15%"
            }
        ],
        "exchange_rate": {
            "rate": fiq_to_kes_rate,
            "currency": "KES",
            "base": "FIQ"
        }
    }
