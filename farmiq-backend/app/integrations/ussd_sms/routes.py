"""
USSD/SMS Routes - FastAPI endpoints for Africa's Talking webhooks
"""

from fastapi import APIRouter, Request, Depends, HTTPException, logger as fastapi_logger
from typing import Dict, Any
import logging
from datetime import datetime

from app.integrations.ussd_sms.schemas import (
    USSDRequest,
    USSDResponse,
    SMSSendRequest,
    SMSSendResponse,
    SMSFetchResponse,
    SMSIncomingMessage,
    SMSDeliveryReport,
    SMSNotificationType,
)
from app.integrations.ussd_sms.ussd_service import USSDService
from app.integrations.ussd_sms.sms_service import SMSService
from app.integrations.ussd_sms.africastalking_client import AfricasTalkingClient
from core.database import get_db_pool
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ussd-sms"])

# Initialize services (these will be dependencies)
async def get_ussd_service(db_pool = Depends(get_db_pool)) -> USSDService:
    """Dependency to get USSD service"""
    return USSDService(db_pool)


async def get_sms_service(db_pool = Depends(get_db_pool)) -> SMSService:
    """Dependency to get SMS service"""
    api_key = os.getenv("AFRIKATALK_API_KEY")
    username = os.getenv("AFRIKATALK_USERNAME")
    environment = os.getenv("AFRIKATALK_ENVIRONMENT", "sandbox")
    return SMSService(api_key, username, environment)


async def get_at_client() -> AfricasTalkingClient:
    """Dependency to get Africa's Talking client"""
    api_key = os.getenv("AFRIKATALK_API_KEY")
    username = os.getenv("AFRIKATALK_USERNAME")
    environment = os.getenv("AFRIKATALK_ENVIRONMENT", "sandbox")
    
    from app.integrations.ussd_sms.africastalking_client import AfricasTalkingEnvironment
    env = AfricasTalkingEnvironment.SANDBOX if environment == "sandbox" else AfricasTalkingEnvironment.PRODUCTION
    
    return AfricasTalkingClient(username, api_key, env)


# ============================================================================
# USSD Endpoints
# ============================================================================

@router.post("/ussd/menu", response_model=Dict[str, str])
async def handle_ussd_request(
    request: Request,
    ussd_service: USSDService = Depends(get_ussd_service),
    at_client: AfricasTalkingClient = Depends(get_at_client)
) -> Dict[str, str]:
    """
    Handle USSD menu request from Africa's Talking
    
    Africa's Talking sends:
    {
        "sessionId": "unique-session-id",
        "serviceCode": "*384*49848#",
        "phoneNumber": "+254712345678",
        "text": "" (empty on first) or "*1*2*3" (concatenated selections),
        "networkCode": "63902"
    }
    
    Returns: {"response": "CON menu\\n1. Option\\n2. Option" or "END Thank you"}
    """
    
    try:
        # Get raw body for signature validation
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Note: In production, validate signature
        # signature = request.headers.get("X-Signature", "")
        # if not at_client.validate_webhook_signature(body_str, signature):
        #     logger.warning("Invalid USSD webhook signature")
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse form data
        form_data = await request.form()
        
        ussd_request = USSDRequest(
            sessionId=form_data.get("sessionId", ""),
            serviceCode=form_data.get("serviceCode", ""),
            phoneNumber=form_data.get("phoneNumber", ""),
            text=form_data.get("text", ""),
            networkCode=form_data.get("networkCode", ""),
        )
        
        logger.info(f"USSD request: {ussd_request.phoneNumber} - {ussd_request.text[:50]}")
        
        # Process USSD request
        result = await ussd_service.handle_ussd_request(
            session_id=ussd_request.sessionId,
            phone_number=ussd_request.phoneNumber,
            user_input=ussd_request.text,
            service_code=ussd_request.serviceCode,
            network_code=ussd_request.networkCode,
        )
        
        # Format response
        response_text = ""
        if result["response_type"] == "CON":
            response_text = f"CON {result['menu_text']}"
        else:
            response_text = f"END {result['menu_text']}"
        
        logger.info(f"USSD response: {response_text[:100]}")
        
        return {"response": response_text}
    
    except Exception as e:
        logger.error(f"USSD error: {str(e)}", exc_info=True)
        return {"response": "END Service temporarily unavailable. Please try again."}


@router.get("/ussd/session/{session_id}")
async def get_ussd_session(
    session_id: str,
    ussd_service: USSDService = Depends(get_ussd_service)
) -> Dict[str, Any]:
    """Get USSD session details - for debugging"""
    
    try:
        session = await ussd_service._get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "phone_number": session.get("phone_number"),
            "current_menu": session.get("current_menu"),
            "input_history": session.get("input_history", []),
            "created_at": session.get("created_at"),
            "expires_at": session.get("expires_at"),
        }
    
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SMS Endpoints
# ============================================================================

@router.post("/sms/send", response_model=SMSSendResponse)
async def send_sms(
    request: SMSSendRequest,
    sms_service: SMSService = Depends(get_sms_service),
    db_pool = Depends(get_db_pool)
) -> SMSSendResponse:
    """
    Send SMS to multiple recipients
    
    Request:
    {
        "recipients": ["+254712345678", "+254787654321"],
        "message": "Hello, this is a test message",
        "sender_id": "FarmIQLtd"
    }
    """
    
    try:
        logger.info(f"SMS send request: {len(request.recipients)} recipients")
        
        result = await sms_service.send_sms(
            recipients=request.recipients,
            message=request.message,
            sender_id=request.sender_id,
            db_pool=db_pool
        )
        
        if result.get("success"):
            return SMSSendResponse(
                success=True,
                message="SMS sent successfully",
                recipient_count=len(request.recipients),
                message_ids=result.get("message_ids", []),
                total_cost=result.get("total_cost", 0),
            )
        else:
            return SMSSendResponse(
                success=False,
                error=result.get("error", "Unknown error"),
                recipient_count=0,
            )
    
    except Exception as e:
        logger.error(f"SMS send error: {str(e)}", exc_info=True)
        return SMSSendResponse(success=False, error=str(e))


@router.post("/sms/fetch", response_model=SMSFetchResponse)
async def fetch_sms(
    sms_service: SMSService = Depends(get_sms_service),
    last_received_id: int = 0,
    db_pool = Depends(get_db_pool)
) -> SMSFetchResponse:
    """
    Fetch incoming SMS messages
    
    Query params:
        - last_received_id: ID of last fetched message (for pagination)
    """
    
    try:
        result = await sms_service.fetch_incoming_sms(last_received_id, db_pool)
        
        if result.get("success"):
            return SMSFetchResponse(
                success=True,
                message_count=result.get("count", 0),
                messages=result.get("messages", []),
                last_id=result.get("last_id", last_received_id),
            )
        else:
            return SMSFetchResponse(
                success=False,
                error=result.get("error", "Unknown error"),
            )
    
    except Exception as e:
        logger.error(f"SMS fetch error: {str(e)}", exc_info=True)
        return SMSFetchResponse(success=False, error=str(e))


@router.post("/sms/incoming")
async def handle_incoming_sms(
    request: Request,
    sms_service: SMSService = Depends(get_sms_service),
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """
    Handle incoming SMS webhook from Africa's Talking
    
    Africa's Talking sends:
    {
        "from": "+254712345678",
        "to": "45986",
        "text": "Message content",
        "id": "ATXid_...",
        "date": "2023-01-01 12:00:00",
        "networkCode": "63902"
    }
    """
    
    try:
        form_data = await request.form()
        
        message = {
            "from": form_data.get("from", ""),
            "to": form_data.get("to", ""),
            "text": form_data.get("text", ""),
            "id": form_data.get("id", ""),
            "date": form_data.get("date", ""),
            "networkCode": form_data.get("networkCode", ""),
        }
        
        logger.info(f"Incoming SMS: {message['from']} -> {message['text'][:50]}")
        
        result = await sms_service.handle_incoming_message(message, db_pool)
        
        return {"status": "ok" if result.get("success") else "error"}
    
    except Exception as e:
        logger.error(f"Incoming SMS error: {str(e)}", exc_info=True)
        return {"status": "error"}


@router.post("/sms/delivery")
async def handle_sms_delivery_report(
    request: Request,
    sms_service: SMSService = Depends(get_sms_service),
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """
    Handle SMS delivery report webhook from Africa's Talking
    
    Africa's Talking sends:
    {
        "id": "ATXid_...",
        "status": "Success|Failed|Sent|...",
        "phoneNumber": "+254712345678",
        "failureReason": "...",
        "networkCode": "63902",
        "retryCount": 0,
        "timestamp": "2023-01-01 12:00:00"
    }
    """
    
    try:
        form_data = await request.form()
        
        report = {
            "id": form_data.get("id", ""),
            "status": form_data.get("status", ""),
            "phoneNumber": form_data.get("phoneNumber", ""),
            "failureReason": form_data.get("failureReason", ""),
            "networkCode": form_data.get("networkCode", ""),
        }
        
        logger.info(f"Delivery report: {report['id']} - {report['status']}")
        
        result = await sms_service.handle_delivery_report(report, db_pool)
        
        return {"status": "ok" if result.get("success") else "error"}
    
    except Exception as e:
        logger.error(f"Delivery report error: {str(e)}", exc_info=True)
        return {"status": "error"}


@router.post("/sms/optout")
async def handle_sms_optout(
    request: Request,
    sms_service: SMSService = Depends(get_sms_service),
    db_pool = Depends(get_db_pool)
) -> Dict[str, str]:
    """
    Handle SMS opt-out notification from Africa's Talking
    
    Africa's Talking sends:
    {
        "phoneNumber": "+254712345678",
        "senderId": "FarmIQLtd",
        "id": "ATXid_..."
    }
    """
    
    try:
        form_data = await request.form()
        
        opt_out = {
            "phoneNumber": form_data.get("phoneNumber", ""),
            "senderId": form_data.get("senderId", ""),
            "id": form_data.get("id", ""),
        }
        
        logger.info(f"SMS opt-out: {opt_out['phoneNumber']}")
        
        result = await sms_service.handle_opt_out(opt_out, db_pool)
        
        return {"status": "ok" if result.get("success") else "error"}
    
    except Exception as e:
        logger.error(f"Opt-out error: {str(e)}", exc_info=True)
        return {"status": "error"}


# ============================================================================
# Health Check
# ============================================================================

@router.get("/ussd-sms/health")
async def health_check(
    at_client: AfricasTalkingClient = Depends(get_at_client)
) -> Dict[str, Any]:
    """
    Health check for USSD/SMS integration
    
    Returns account balance and connection status
    """
    
    try:
        balance = await at_client.get_balance()
        
        return {
            "status": "healthy",
            "service": "USSD/SMS",
            "balance": balance,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
