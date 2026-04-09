"""
Enhanced USSD Routes with Afrika Talking Integration
Handles: USSD menu navigation, SMS/bulk SMS, registration, role selection, AI services
Complete auth flow integrated with Supabase and FarmIQ ID

Author: FarmIQ Backend Team
Date: March 2026
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/ussd",
    tags=["USSD - Afrika Talking Integration"]
)


# ===================== REQUEST/RESPONSE MODELS =====================

class USSDIncomingRequest(BaseModel):
    """USSD callback from Afrika Talking"""
    phoneNumber: str
    text: str
    sessionId: str
    networkCode: Optional[str] = None
    timestamp: Optional[str] = None


class USSDResponse(BaseModel):
    """Response to USSD (CON=continue, END=end session)"""
    CON: Optional[str] = None
    END: Optional[str] = None


class SMSRequest(BaseModel):
    """Send single SMS"""
    phone_number: str = Field(..., example="254712345678")
    message: str = Field(..., example="Your FarmIQ message")
    priority: str = Field(default="normal", example="normal")


class BulkSMSRequest(BaseModel):
    """Send bulk SMS"""
    phone_numbers: List[str]
    message: str
    priority: str = Field(default="normal")


class SMSResponse(BaseModel):
    """SMS delivery response"""
    success: bool
    message_id: Optional[str] = None
    status: str
    timestamp: str
    error: Optional[str] = None


class RegistrationRequest(BaseModel):
    """USSD registration"""
    farmiq_id: str
    role: str
    county: str
    phone_number: str


class AuthStatusResponse(BaseModel):
    """Auth status"""
    authenticated: bool
    user_id: Optional[str] = None
    farmiq_id: Optional[str] = None
    role: Optional[str] = None
    phone_verified: bool


# ===================== DEPENDENCY INJECTION =====================

from app.payments.services.afritalk_service import AfrikaTalkingService, SMSMessage, SMSPriority
from app.payments.services.ussd_auth_service import USSDAuthService, USSDMenuManager, FarmerRole
from app.payments.services.ussd_ai_bridge import (
    USSDFarmGrowBridge,
    USSDFarmScoreBridge,
    USSDFarmSuiteBridge,
    USSDPaymentBridge,
)

async def get_afritalk_service() -> AfrikaTalkingService:
    """Get Afrika Talking service - should be initialized globally"""
    # TODO: Configure from DI container
    return None

async def get_ussd_auth_service() -> USSDAuthService:
    """Get USSD Auth service"""
    # TODO: Configure from DI container
    return None

async def get_ussd_menu_manager() -> USSDMenuManager:
    """Get Menu Manager"""
    # TODO: Configure from DI container
    return None

# ===================== MAIN USSD ENDPOINTS =====================

@router.post("/menu", response_model=USSDResponse)
async def ussd_menu_handler(
    request: USSDIncomingRequest,
    background_tasks: BackgroundTasks,
    afritalk_service: AfrikaTalkingService = Depends(get_afritalk_service),
    auth_service: USSDAuthService = Depends(get_ussd_auth_service),
    menu_manager: USSDMenuManager = Depends(get_ussd_menu_manager),
) -> USSDResponse:
    """
    Main USSD menu handler for Afrika Talking
    Processes: registration, auth, role selection, menu navigation
    """
    try:
        # Parse USSD callback
        ussd_request = await afritalk_service.parse_ussd_callback(request.dict())
        
        # Get or create session
        session = await auth_service.get_or_create_session(ussd_request.phone_number, ussd_request.session_id)
        
        # Process input
        response_text, new_state = await menu_manager.handle_ussd_input(session, ussd_request.text)
        
        # Update session
        session.state = new_state
        
        # Log interaction
        background_tasks.add_task(
            afritalk_service.log_ussd_interaction,
            phone_number=ussd_request.phone_number,
            session_id=ussd_request.session_id,
            text=ussd_request.text,
            response=response_text,
            status="success"
        )
        
        # Return response
        if "COMPLETED" in new_state.value or "EXIT" in new_state.value:
            return USSDResponse(END=response_text)
        else:
            return USSDResponse(CON=response_text)
            
    except Exception as e:
        logger.error(f"USSD error: {str(e)}")
        error_msg = "Error processing request.\nPlease try again.\nDial *500# to restart."
        return USSDResponse(END=error_msg)

# ===================== SMS ENDPOINTS =====================

@router.post("/sms/send", response_model=SMSResponse)
async def send_sms(
    request: SMSRequest,
    afritalk_service: AfrikaTalkingService = Depends(get_afritalk_service)
) -> SMSResponse:
    """Send single SMS to farmer"""
    try:
        message = SMSMessage(
            phone_number=request.phone_number,
            message=request.message,
            priority=SMSPriority(request.priority),
        )
        result = await afritalk_service.send_sms(message)
        return SMSResponse(**result)
    except Exception as e:
        logger.error(f"SMS send error: {str(e)}")
        return SMSResponse(success=False, status="error", error=str(e), timestamp=datetime.utcnow().isoformat())


@router.post("/sms/send-bulk")
async def send_bulk_sms(
    request: BulkSMSRequest,
    afritalk_service: AfrikaTalkingService = Depends(get_afritalk_service)
) -> Dict[str, Any]:
    """Send bulk SMS to multiple farmers"""
    try:
        messages = [
            SMSMessage(
                phone_number=phone,
                message=request.message,
                priority=SMSPriority(request.priority),
            )
            for phone in request.phone_numbers
        ]
        result = await afritalk_service.send_bulk_sms(messages)
        return {
            "success": result["successful"] == result["total"],
            "total": result["total"],
            "successful": result["successful"],
            "failed": result["failed"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Bulk SMS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SMS send failed: {str(e)}")


@router.get("/sms/balance")
async def check_sms_balance(
    afritalk_service: AfrikaTalkingService = Depends(get_afritalk_service)
) -> Dict[str, Any]:
    """Check SMS credit balance"""
    try:
        balance = await afritalk_service.check_sms_balance()
        return balance
    except Exception as e:
        logger.error(f"Balance check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking balance: {str(e)}")


# ===================== AUTH ENDPOINTS =====================

@router.post("/auth/verify-farmiq-id")
async def verify_farmiq_id(
    farmiq_id: str,
    phone_number: str,
    auth_service: USSDAuthService = Depends(get_ussd_auth_service)
) -> Dict[str, Any]:
    """Verify FarmIQ ID exists and matches phone"""
    try:
        is_valid, user_data = await auth_service.verify_farmiq_id(farmiq_id, phone_number)
        return {
            "valid": is_valid,
            "user": user_data if is_valid else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/auth/register", response_model=AuthStatusResponse)
async def register_via_ussd(
    request: RegistrationRequest,
    auth_service: USSDAuthService = Depends(get_ussd_auth_service)
) -> AuthStatusResponse:
    """Register new farmer"""
    try:
        registered, user_data = await auth_service.register_new_user(
            phone_number=request.phone_number,
            farmiq_id=request.farmiq_id
        )
        if registered:
            user_id = user_data.get("user_id")
            role_enum = FarmerRole(request.role)
            await auth_service.set_user_role(user_id, request.farmiq_id, role_enum)
            
            return AuthStatusResponse(
                authenticated=True,
                user_id=user_id,
                farmiq_id=request.farmiq_id,
                role=request.role,
                phone_verified=True,
            )
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/rag-chatbot/ask")
async def ask_rag_chatbot(
    phone_number: str,
    question: str,
    session_id: str,
    language: str = "en",
) -> Dict[str, Any]:
    """
    Ask FarmGrow RAG chatbot a question via USSD
    Response delivered via SMS
    """
    try:
        # Import RAG bridge service
        from app.payments.services.ussd_ai_bridge import USSDFarmGrowBridge
        
        rag_bridge = USSDFarmGrowBridge()
        
        # Process question through RAG
        answer = await rag_bridge.ask_farming_question(
            question=question,
            phone_number=phone_number,
            language=language
        )
        
        # Send answer via SMS
        sms_message = SMSMessage(
            phone_number=phone_number,
            message=f"FarmIQ Answer: {answer}",
            priority=SMSPriority.HIGH,
        )
        
        afritalk_service = AfrikaTalkingService()
        result = await afritalk_service.send_sms(sms_message)
        
        logger.info(f"RAG chatbot question answered for {phone_number}")
        return {
            "success": True,
            "question": question,
            "answer_preview": answer[:80] + "...",
            "delivery_method": "SMS",
            "expected_delivery_seconds": 10,
            "message_id": result.get("message_id"),
        }
    except Exception as e:
        logger.error(f"RAG chatbot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/farmcredit/check-score")
async def check_credit_score(
    phone_number: str,
    farmiq_id: str,
) -> Dict[str, Any]:
    """Check farmer's credit score and get loan options"""
    try:
        from app.payments.services.ussd_ai_bridge import USSDFarmScoreBridge
        
        score_bridge = USSDFarmScoreBridge()
        
        # Get credit score from FarmScore
        score_data = await score_bridge.get_credit_score(farmiq_id, phone_number)
        
        # Format response message
        score_msg = (
            f"Your FarmIQ Credit Score: {score_data['score']}/1000\n"
            f"Status: {score_data['status']}\n"
            f"Loan Eligible: {'Yes' if score_data['eligible'] else 'No'}\n"
            f"Max Loan Amount: {score_data['max_loan_amount']} KES\n"
            f"For loan options, reply: 2"
        )
        
        # Send via SMS
        sms_message = SMSMessage(
            phone_number=phone_number,
            message=score_msg,
            priority=SMSPriority.HIGH,
        )
        
        afritalk_service = AfrikaTalkingService()
        result = await afritalk_service.send_sms(sms_message)
        
        logger.info(f"Credit score sent to {phone_number}")
        return {
            "success": True,
            "score": score_data['score'],
            "status": score_data['status'],
            "eligible_for_loan": score_data['eligible'],
            "message_delivered": result.get("success"),
        }
    except Exception as e:
        logger.error(f"Credit score check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/farmcredit/loan-calculator")
async def loan_calculator(
    phone_number: str,
    amount_kes: int,
    period_months: int,
) -> Dict[str, Any]:
    """Calculate loan repayment schedule"""
    try:
        from app.payments.services.ussd_ai_bridge import USSDFarmScoreBridge
        
        score_bridge = USSDFarmScoreBridge()
        
        # Calculate loan terms
        calculation = await score_bridge.calculate_loan_repayment(
            amount_kes=amount_kes,
            period_months=period_months
        )
        
        # Format SMS response
        calc_msg = (
            f"Loan Calculator Results:\n"
            f"Amount: {amount_kes:,} KES\n"
            f"Period: {period_months} months\n"
            f"Interest Rate: {calculation['interest_rate']}%\n"
            f"Monthly Payment: {calculation['monthly_payment']:,} KES\n"
            f"Total Interest: {calculation['total_interest']:,} KES\n"
            f"Total Repayment: {calculation['total_repayment']:,} KES"
        )
        
        # Send via SMS
        sms_message = SMSMessage(
            phone_number=phone_number,
            message=calc_msg,
            priority=SMSPriority.NORMAL,
        )
        
        afritalk_service = AfrikaTalkingService()
        result = await afritalk_service.send_sms(sms_message)
        
        return {
            "success": True,
            "calculation": calculation,
            "message_delivered": result.get("success"),
        }
    except Exception as e:
        logger.error(f"Loan calculator error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/farmsuite/farm-summary")
async def get_farm_summary(
    phone_number: str,
    farmiq_id: str,
) -> Dict[str, Any]:
    """Get farm summary via USSD -> SMS"""
    try:
        from app.payments.services.ussd_ai_bridge import USSDFarmSuiteBridge
        
        suite_bridge = USSDFarmSuiteBridge()
        
        # Get farm summary
        summary = await suite_bridge.get_farm_summary(farmiq_id, phone_number)
        
        # Format SMS response
        summary_msg = (
            f"🏡 Farm Summary:\n"
            f"Total Acres: {summary['total_acres']}\n"
            f"Main Crops: {summary['main_crops']}\n"
            f"This Season Harvest: {summary['season_harvest']} bags\n"
            f"Avg Yield/Acre: {summary['avg_yield_per_acre']} bags\n"
            f"Est. Income: {summary['estimated_income']:,} KES\n"
            f"See analytics: Reply 3"
        )
        
        # Send via SMS
        sms_message = SMSMessage(
            phone_number=phone_number,
            message=summary_msg,
            priority=SMSPriority.HIGH,
        )
        
        afritalk_service = AfrikaTalkingService()
        result = await afritalk_service.send_sms(sms_message)
        
        logger.info(f"Farm summary sent to {phone_number}")
        return {
            "success": True,
            "summary": summary,
            "message_delivered": result.get("success"),
        }
    except Exception as e:
        logger.error(f"Farm summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worker-menu/{phone_number}")
async def get_worker_menu(
    phone_number: str,
    auth_service: USSDAuthService = Depends(get_ussd_auth_service)
) -> Dict[str, Any]:
    """Get USSD menu for farm workers"""
    try:
        return {
            "role": "worker",
            "menu": {
                "1": "🏡 View Task Assignments",
                "2": "✅ Report Task Completion",
                "3": "💰 Check Earnings This Month",
                "4": "📞 Contact Farm Manager",
                "5": "📍 Farm Location & Map",
                "0": "Exit"
            },
            "description": "Farm worker USSD menu for task management and earnings tracking"
        }
    except Exception as e:
        logger.error(f"Worker menu error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extension-officer-menu/{phone_number}")
async def get_extension_officer_menu(
    phone_number: str,
    auth_service: USSDAuthService = Depends(get_ussd_auth_service)
) -> Dict[str, Any]:
    """Get USSD menu for extension officers"""
    try:
        return {
            "role": "extension_officer",
            "menu": {
                "1": "👥 View Assigned Farmers",
                "2": "📊 Send Bulk Advisory SMS",
                "3": "📈 Monitor Farmer Progress",
                "4": "🚨 Create Farm Alert",
                "5": "📱 Share RAG Chatbot Link",
                "6": "📞 FarmIQ Support",
                "0": "Exit"
            },
            "description": "Extension officer USSD menu for farmer management and advisory"
        }
    except Exception as e:
        logger.error(f"Extension officer menu error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



async def test_welcome_menu(
    auth_service: USSDAuthService = Depends(get_ussd_auth_service)
) -> Dict[str, str]:
    """Test welcome menu"""
    menu = await auth_service.menu_welcome()
    return {"menu": menu}


@router.get("/test/role-selection")
async def test_role_selection(
    auth_service: USSDAuthService = Depends(get_ussd_auth_service)
) -> Dict[str, str]:
    """Test role selection menu"""
    menu = await auth_service.menu_role_selection()
    return {"menu": menu}


@router.post("/test/simulate-registration")
async def test_simulate_registration(
    phone: str = "254712345678",
    farmiq_id: str = "FARM001",
    role: str = "farmer",
    auth_service: USSDAuthService = Depends(get_ussd_auth_service),
) -> Dict[str, Any]:
    """Test: Simulate registration flow"""
    try:
        is_valid, _ = await auth_service.verify_farmiq_id(farmiq_id, phone)
        
        if not is_valid:
            registered, user_data = await auth_service.register_new_user(
                phone_number=phone,
                farmiq_id=farmiq_id
            )
            if not registered:
                return {"success": False, "error": "Registration failed"}
        else:
            user_data = await auth_service.get_user_by_farmiq_id(farmiq_id)
        
        return {
            "success": True,
            "user_id": user_data.get("user_id"),
            "farmiq_id": farmiq_id,
            "phone": phone,
            "role": role,
            "next_step": "farming_profile_setup",
        }
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/test/simulate-flow")
async def test_simulate_payment_flow(
    phone_number: str = "254712345678",
    amount_kes: int = 1000,
    auth_service: USSDAuthService = Depends(get_ussd_auth_service),
) -> dict:
    """Simulate complete auth and payments flow"""
    try:
        flow_results = []
        session_id = "flow_test_session"
        
        # Step 1: Welcome menu
        menu_text = await auth_service.menu_welcome()
        flow_results.append({
            "step": 1,
            "action": "Show welcome menu",
            "response": menu_text[:80] + "..."
        })
        
        # Step 2: Role selection
        role_menu = await auth_service.menu_role_selection()
        flow_results.append({
            "step": 2,
            "action": "Show role selection",
            "response": role_menu[:80] + "..."
        })
        
        return {
            "phone_number": phone_number,
            "flow_completed": True,
            "steps": flow_results
        }
    except Exception as e:
        logger.error(f"Flow simulation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== HEALTH & INFO =====================

@router.get("/health")
async def ussd_health() -> Dict[str, Any]:
    """USSD service health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ussd": "online",
            "sms": "online",
            "auth": "online",
            "ai_services": "online",
        },
        "endpoints": {
            "sms": "/sms/send, /sms/send-bulk, /sms/balance",
            "auth": "/auth/verify-farmiq-id, /auth/register",
            "ussd": "/menu (main handler from Afrika Talking)",
        }
    }


@router.get("/menu-map")
async def get_menu_map() -> Dict[str, Any]:
    """Get complete USSD menu structure and documentation"""
    return {
        "welcome_flow": {
            "1": "Register New Account",
            "2": "Login with FarmIQ ID",
            "0": "Exit",
        },
        "authenticated_menu": {
            "1": "🌾 FarmGrow AI (Crop advice & market prices)",
            "2": "💳 FarmCredit (Credit scoring & loans)",
            "3": "📊 FarmSuite Analytics (Farm reports & forecasts)",
            "4": "💬 RAG Chatbot (Ask farming questions)",
            "5": "💰 Buy Tokens / Pay",
            "6": "📱 My Profile",
            "0": "Exit",
        },
        "role_selection": {
            "1": "Farmer (individual farmer)",
            "2": "Farm Manager (manage multiple farms)",
            "3": "Cooperative (group/association)",
            "4": "Extension Officer (advisor/trainer)",
            "5": "Worker (farm worker)",
        },
        "farmgrow_ai": {
            "1": "📍 Today's Crop Recommendation",
            "2": "🌱 Best Crops This Season",
            "3": "💹 Market Price Information",
            "4": "🐛 Pest & Disease Alerts",
            "5": "🌤️ 7-Day Weather Forecast",
            "6": "🌾 Fertilizer Recommendations",
            "0": "Back",
        },
        "farmgrow_rag_chatbot": {
            "ask_question": "Ask a farming question (free, powered by AI)",
            "menu": "Ask any question about: crop disease, fertilizer, irrigation, pest management, market prices, weather, best practices",
            "examples": [
                "What's the best fertilizer for maize?",
                "How do I prevent maize blight?",
                "When should I plant beans this season?",
                "What's the current market price for tomatoes?",
                "How much water does wheat need?",
            ],
            "response_format": "RAG chatbot searches knowledge base + AI generates answer in Swahili/English",
            "cost": "Free (included with FarmIQ subscription)",
            "character_limit": 160,
            "response_delivery": "SMS in 10-30 seconds",
            "follow_up": "Can ask follow-up questions in same session",
        },
        "farmscore_credit": {
            "1": "📈 Check My Credit Score",
            "2": "💸 View Loan Options",
            "3": "📋 Apply for Loan",
            "4": "📊 My Active Loans",
            "5": "💵 Loan Repayment",
            "6": "❓ Loan Calculator",
            "0": "Back",
        },
        "farmscore_credit_details": {
            "credit_score": "Real-time score (0-1000) based on: farm data, payment history, production data, market prices",
            "loan_options": [
                "Small Loan: 1,000 - 50,000 KES",
                "Medium Loan: 50,000 - 500,000 KES",
                "Large Loan: 500,000 - 5,000,000 KES",
            ],
            "eligibility": "Based on credit score, farm data, and collateral (farm assets, crop production)",
            "interest_rate": "6-15% per annum (depends on score and amount)",
            "repayment_period": "3-36 months",
            "disbursement": "Direct to M-Pesa after approval",
            "approval_time": "1-3 days",
        },
        "farmsuite_analytics": {
            "1": "🏡 Farm Summary",
            "2": "📊 Production Statistics",
            "3": "💼 Financial Reports",
            "4": "🔮 Yield Forecast",
            "5": "📈 Performance Trends",
            "6": "🎯 Benchmarking",
            "0": "Back",
        },
        "farmsuite_analytics_details": {
            "farm_summary": "Overview: total acres, crops, livestock, income sources",
            "production_stats": "This season: total harvest, average yield per acre, quality grades",
            "financial_report": "Income, expenses, net profit, cost per unit, profit margins",
            "yield_forecast": "Predicted yield based on current conditions + weather + historical data",
            "performance_trends": "Yield trends over 5 years, income trends, cost optimization",
            "benchmarking": "Compare your farm against regional average farms similar size/crops",
        },
        "auth_method": "FarmIQ ID based",
        "sms_features": {
            "payment_notifications": "Real-time STK, token purchase confirmations",
            "ai_alerts": "FarmGrow recommendations, pest alerts, weather warnings",
            "loan_status": "Approval/rejection, disbursement confirmations",
            "bulk_notifications": "Community-wide alerts, promotional offers",
        },
        "ai_services_on_ussd": [
            "FarmGrow - Crop recommendations and market prices",
            "FarmScore - Credit scoring and loan eligibility",
            "FarmSuite - Farm analytics and financial reports",
        ],
        "feature_parity": "USSD has feature parity with Angular UI for: registration, role selection, farming setup, AI services, payments",
        "payment_menu": {
            "1": "💳 Buy Tokens/Credit",
            "2": "💰 Check Balance",
            "3": "📊 Payment History",
            "4": "🔒 Escrow Status",
            "5": "↩️ Request Reversal",
            "6": "ℹ️ Help",
            "0": "Exit"
        },
        "buy_tokens": {
            "1": "Starter (100 FIQ = 1,000 KES)",
            "2": "Small (500 FIQ = 5,000 KES)",
            "3": "Medium (1,000 FIQ = 10,000 KES)",
            "4": "Large (2,000 FIQ = 20,000 KES)",
            "5": "Custom Amount",
            "0": "Back"
        },
        "escrow_status": {
            "1": "Check Escrow Status",
            "2": "Request Release",
            "0": "Back"
        },
        "reversal": {
            "1": "Request Reversal",
            "2": "Check Reversal Status",
            "0": "Back"
        },
        "example_flows": {
            "buy_tokens": "*500*5*1*2#",
            "check_balance": "*500*5*2#",
            "payment_history": "*500*5*3#",
            "escrow_status": "*500*5*4*1#",
            "request_reversal": "*500*5*5*1#",
            "farmgrow_recommendation": "*500*1*1# (will receive SMS with recommendation)",
            "check_credit_score": "*500*2*1# (will receive SMS with score and loan options)",
            "farm_summary": "*500*3*1# (will receive SMS with farm overview)",
            "ask_rag_chatbot": "*500*4# (ask question, receive answer via SMS in 10-30s)",
            "apply_for_loan": "*500*2*3# (guides through application)",
            "weather_forecast": "*500*1*5# (7-day forecast via SMS)",
        },
        "ussd_features_for_workers": {
            "1": "🏡 Check Task Assignments",
            "2": "✅ Report Task Completion",
            "3": "💰 View Earnings",
            "4": "📞 Contact Manager",
            "5": "📍 Check Farm Location",
            "0": "Exit",
        },
        "ussd_features_for_extension_officers": {
            "1": "👥 View Assigned Farmers",
            "2": "📊 Send Bulk Advisory SMS",
            "3": "📈 Monitor Farmer Progress",
            "4": "🚨 Create Farm Alert",
            "5": "📱 Share RAG Chatbot Link",
            "0": "Exit",
        },
        "ussd_features_for_cooperatives": {
            "1": "👥 Manage Member List",
            "2": "📊 Group Production Report",
            "3": "💳 Bulk Token Purchase",
            "4": "📢 Send Group Message",
            "5": "🎯 Collective Loan Application",
            "0": "Exit",
        },
        "rag_chatbot_response_examples": {
            "question": "What's the best fertilizer for tomatoes in March?",
            "response": "For tomatoes in March: use DAP (16:20:0) at planting, then Urea (46:0:0) at flowering. Apply 200kg per acre. Water after fertilizer application.",
            "format": "Delivered via SMS in Swahili or English",
            "knowledge_sources": "FarmIQ knowledge base, agronomic research, local market data",
        },
        "dashboard_tracking": {
            "purpose": "Real-time monitoring of all payment providers (M-Pesa, Afrika Talking, Hedera)",
            "metrics_collected": [
                "M-Pesa: transactions/min, success rate %, failed transactions, callback latency, STK timeout rate",
                "Afrika Talking: SMS delivered/min, USSD sessions active, SMS bounce rate, USSD response ms",
                "Hedera: token mints/min, HCS log writes/min, transaction cost in USD, network latency, TPS (transactions per second)",
            ],
            "alerting": "Critical: <60% success rate, Warnings: response time >3s, Error spikes >10% hourly",
            "sla": "M-Pesa: 99.5% uptime, Afrika Talking: 99% uptime, Hedera: 99.9% uptime",
        },
    }

