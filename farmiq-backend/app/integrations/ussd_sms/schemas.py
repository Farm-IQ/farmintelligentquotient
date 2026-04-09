"""
Pydantic models for Africa's Talking USSD and SMS integration
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ===================== USSD MODELS =====================

class USSDRequestCodes(str, Enum):
    """USSD request codes from Africa's Talking"""
    CON = "CON"  # Continue menu
    END = "END"  # End session


class USSDRequest(BaseModel):
    """Request from Africa's Talking USSD API"""
    sessionId: str = Field(..., description="Unique session identifier")
    serviceCode: str = Field(..., description="USSD service code (*384*49848#)")
    phoneNumber: str = Field(..., description="Phone number of user (+254...)")
    text: str = Field(default="", description="User input - empty for first request")
    networkCode: Optional[str] = None


class USSDResponse(BaseModel):
    """Response to send back to Africa's Talking"""
    response: str = Field(..., description="CON or END followed by menu text")
    
    class Config:
        schema_extra = {
            "example": {
                "response": "CON What would you like to do?\n1. Check Balance\n2. Buy Tokens\n3. Get Help"
            }
        }


class USSDSessionData(BaseModel):
    """Stored session data"""
    session_id: str
    phone_number: str
    user_id: Optional[str] = None
    farmiq_id: Optional[str] = None
    current_menu: str
    user_input_history: List[str] = []
    navigation_depth: int = 0
    temp_data: Dict[str, Any] = {}
    created_at: datetime
    last_updated: datetime


# ===================== SMS MODELS =====================

class SMSStatusCode(int, Enum):
    """Africa's Talking SMS status codes"""
    PROCESSED = 100
    SENT = 101
    QUEUED = 102
    RISK_HOLD = 401
    INVALID_SENDER_ID = 402
    INVALID_PHONE_NUMBER = 403
    UNSUPPORTED_NUMBER_TYPE = 404
    INSUFFICIENT_BALANCE = 405
    USER_IN_BLACKLIST = 406
    COULD_NOT_ROUTE = 407
    DO_NOT_DISTURB = 409
    INTERNAL_SERVER_ERROR = 500
    GATEWAY_ERROR = 501
    REJECTED_BY_GATEWAY = 502


class SMSSendRequest(BaseModel):
    """Request to send SMS via Africa's Talking"""
    username: str
    api_key: str
    recipients: List[str] = Field(..., description="List of phone numbers in international format")
    message: str = Field(..., description="SMS message content")
    sender_id: str = Field(..., description="Sender ID or shortcode")
    enqueue: Optional[int] = 1  # 0 or 1


class SMSRecipient(BaseModel):
    """Individual SMS recipient response"""
    statusCode: int
    number: str
    status: str
    cost: str
    messageId: str


class SMSSendResponse(BaseModel):
    """Response from sending SMS"""
    message: str
    recipients: List[SMSRecipient]


class SMSFetchRequest(BaseModel):
    """Request to fetch incoming SMS messages"""
    username: str
    api_key: str
    last_received_id: int = 0


class SMSMessage(BaseModel):
    """Individual SMS message"""
    linkId: Optional[str] = None
    text: str
    to: str  # Shortcode received on
    id: int
    date: datetime
    from_: str = Field(..., alias="from")


class SMSFetchResponse(BaseModel):
    """Response from fetching SMS messages"""
    messages: List[SMSMessage]


class SMSDeliveryStatus(str, Enum):
    """Possible SMS delivery statuses"""
    SENT = "Sent"
    SUBMITTED = "Submitted"
    BUFFERED = "Buffered"
    REJECTED = "Rejected"
    SUCCESS = "Success"
    FAILED = "Failed"
    ABSENT_SUBSCRIBER = "AbsentSubscriber"
    EXPIRED = "Expired"


class SMSDeliveryReport(BaseModel):
    """SMS Delivery Report notification from Africa's Talking"""
    id: str
    status: str  # SMS delivery status
    phone_number: str
    network_code: str
    failure_reason: Optional[str] = None
    retry_count: Optional[int] = None


class SMSIncomingMessage(BaseModel):
    """Incoming SMS message notification from Africa's Talking"""
    date: datetime
    from_: str = Field(..., alias="from")
    id: str
    link_id: Optional[str] = None
    text: str
    to: str  # Shortcode
    cost: str
    network_code: str


class SMSOptOut(BaseModel):
    """SMS Opt-out notification"""
    sender_id: str
    phone_number: str


class SMSNotificationType(str, Enum):
    """Types of SMS notifications"""
    DELIVERY_REPORT = "delivery_report"
    INCOMING_MESSAGE = "incoming_message"
    BULK_OPT_OUT = "bulk_opt_out"
    SUBSCRIPTION_NOTIFICATION = "subscription_notification"


# ===================== FARMIQ INTEGRATION MODELS =====================

class USSDMenuOption(BaseModel):
    """Single menu option"""
    key: str
    display_text: str
    action: str  # navigation, api_call, token_purchase, etc
    next_menu: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class USSDMenu(BaseModel):
    """USSD Menu definition"""
    menu_id: str
    title: str
    description: Optional[str] = None
    options: List[USSDMenuOption]
    response_type: str = "CON"  # CON or END


class TokenPurchaseUSSD(BaseModel):
    """USSD Token Purchase Flow"""
    phone_number: str
    amount_fiq: int
    amount_kes: int
    mpesa_checkbox_id: str


class USSDTokenBalance(BaseModel):
    """Token balance response via USSD"""
    user_id: str
    fiq_balance: int
    total_earned: int
    last_sync: datetime


class SMSNotificationLog(BaseModel):
    """Log entry for SMS notifications"""
    id: str
    notification_type: str
    phone_number: Optional[str] = None
    content: Dict[str, Any]
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BulkSMSCampaign(BaseModel):
    """Bulk SMS campaign"""
    campaign_id: str
    name: str
    message: str
    recipient_count: int
    sender_id: str
    status: str  # draft, scheduled, sending, completed, failed
    total_cost_kes: float
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ===================== ERROR & VALIDATION =====================

class ATErrorResponse(BaseModel):
    """Error response format from Africa's Talking"""
    error: str
    details: Optional[Dict[str, Any]] = None


class USSDErrorResponse(BaseModel):
    """USSD error response"""
    response: str = "END An error occurred. Please try again later."


class SMSErrorResponse(BaseModel):
    """SMS error response"""
    error: bool = True
    message: str
    status_code: int
