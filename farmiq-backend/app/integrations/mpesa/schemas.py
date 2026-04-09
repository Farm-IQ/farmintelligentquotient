"""
M-Pesa Daraja Pydantic Schemas - Type validation for all API interactions
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# Enums for M-Pesa Response Codes
# ============================================================================

class MpesaResponseCode(str, Enum):
    """M-Pesa API response codes"""
    SUCCESS = "0"
    FAILURE = "1"
    DUPLICATE = "2"
    CANCELLED = "1032"


class MpesaResultCode(str, Enum):
    """M-Pesa transaction result codes"""
    SUCCESS = "0"
    INSUFFICIENT_BALANCE = "4"
    DECLINED_LIMIT = "8"
    EXPIRED = "1037"
    USER_CANCELLED = "8006"
    OFFLINE = "SFC_ICO003"


class TransactionType(str, Enum):
    """M-Pesa transaction types"""
    PAY_BILL = "CustomerPayBillOnline"
    BUY_GOODS = "CustomerBuyGoodsOnline"


class IdentifierType(int, Enum):
    """M-Pesa identifier types"""
    MSISDN = 1
    TILL_NUMBER = 2
    SHORTCODE = 4
    ORGANIZATION = 4


# ============================================================================
# STK Push (M-Pesa Express) Models
# ============================================================================

class StkPushRequest(BaseModel):
    """Request model for STK Push"""
    
    phone_number: str = Field(..., description="Customer phone in 254XXXXXXXXX format")
    amount: float = Field(..., gt=0, description="Amount in KES")
    account_reference: str = Field(..., max_length=12, description="Account reference")
    transaction_desc: str = Field(..., max_length=13, description="Transaction description")
    callback_url: str = Field(..., description="Callback URL for results")
    
    @validator("phone_number")
    def validate_phone(cls, v):
        """Validate phone number format"""
        if not v.startswith("254") or len(v) != 12:
            raise ValueError("Phone must be in format 254XXXXXXXXX")
        return v


class StkPushResponse(BaseModel):
    """Response model for STK Push"""
    
    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResponseDescription: str
    CustomerMessage: str


class StkPushStatusRequest(BaseModel):
    """Request to query STK Push status"""
    
    checkout_request_id: str = Field(..., description="CheckoutRequestID from STK Push")


class StkPushStatusResponse(BaseModel):
    """Response from STK Push status query"""
    
    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResultCode: str
    ResultDesc: str
    ResponseDescription: str


# ============================================================================
# Account Balance Models
# ============================================================================

class AccountBalanceRequest(BaseModel):
    """Request to query account balance"""
    
    initiator_name: str = Field(..., description="M-Pesa initiator username")
    initiator_password: str = Field(..., description="M-Pesa initiator password")
    queue_timeout_url: str = Field(..., description="Timeout notification URL")
    result_url: str = Field(..., description="Result notification URL")


class BalanceParameterItem(BaseModel):
    """Individual balance item"""
    
    Key: str
    Value: str


class AccountBalanceResponse(BaseModel):
    """Response from account balance query"""
    
    OriginatorConversationID: str
    ConversationID: str
    ResponseCode: str
    ResponseDescription: str


# ============================================================================
# Transaction Status Models
# ============================================================================

class TransactionStatusRequest(BaseModel):
    """Request to query transaction status"""
    
    transaction_id: str = Field(..., description="M-Pesa receipt number")
    initiator_name: str = Field(..., description="M-Pesa initiator username")
    initiator_password: str = Field(..., description="M-Pesa initiator password")
    queue_timeout_url: str = Field(..., description="Timeout notification URL")
    result_url: str = Field(..., description="Result notification URL")
    original_conversation_id: Optional[str] = Field(None, description="Original conversation ID")


class TransactionStatusResponse(BaseModel):
    """Response from transaction status query"""
    
    OriginatorConversationID: str
    ConversationID: str
    ResponseCode: str
    ResponseDescription: str
    ResultCode: Optional[str] = None
    ResultDesc: Optional[str] = None


# ============================================================================
# Reversal Models
# ============================================================================

class ReversalRequest(BaseModel):
    """Request to reverse transaction"""
    
    transaction_id: str = Field(..., description="M-Pesa receipt number to reverse")
    amount: float = Field(..., gt=0, description="Amount to reverse in KES")
    initiator_name: str = Field(..., description="M-Pesa initiator username")
    initiator_password: str = Field(..., description="M-Pesa initiator password")
    queue_timeout_url: str = Field(..., description="Timeout notification URL")
    result_url: str = Field(..., description="Result notification URL")
    remarks: str = Field("Transaction Reversal", max_length=100, description="Reversal remarks")


class ReversalResponse(BaseModel):
    """Response from reversal request"""
    
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str
    RequestId: Optional[str] = None


# ============================================================================
# Tax Remittance Models
# ============================================================================

class TaxRemittanceRequest(BaseModel):
    """Request to remit taxes to KRA"""
    
    amount: float = Field(..., gt=0, description="Tax amount in KES")
    prn: str = Field(..., description="Payment Registration Number from KRA")
    initiator_name: str = Field(..., description="M-Pesa initiator username")
    initiator_password: str = Field(..., description="M-Pesa initiator password")
    queue_timeout_url: str = Field(..., description="Timeout notification URL")
    result_url: str = Field(..., description="Result notification URL")
    remarks: str = Field("Tax Remittance to KRA", max_length=100)


class TaxRemittanceResponse(BaseModel):
    """Response from tax remittance"""
    
    OriginatorConversationID: str
    ConversationID: str
    ResponseCode: str
    ResponseDescription: str
    ResultCode: Optional[str] = None
    ResultDesc: Optional[str] = None


# ============================================================================
# Webhook Callback Models
# ============================================================================

class StkPushCallbackMetadata(BaseModel):
    """Metadata from STK Push callback"""
    
    Item: List[Dict[str, Any]]


class StkPushCallback(BaseModel):
    """STK Push callback from Africa's Talking"""
    
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[StkPushCallbackMetadata] = None


class StkPushCallbackWrapper(BaseModel):
    """Wrapper for STK Push callback"""
    
    Body: Dict[str, Any]


class BalanceCallbackResult(BaseModel):
    """Balance query callback result"""
    
    ConversationID: str
    OriginatorConversationID: str
    ResultCode: int
    ResultDesc: str
    ResultType: int
    ResultParameters: Optional[Dict[str, Any]] = None


class BalanceCallbackWrapper(BaseModel):
    """Wrapper for balance callback"""
    
    Result: BalanceCallbackResult


class TransactionStatusCallbackResult(BaseModel):
    """Transaction status callback result"""
    
    ConversationID: str
    OriginatorConversationID: str
    ResultCode: int
    ResultDesc: str
    ResultType: int
    TransactionID: Optional[str] = None
    ResultParameters: Optional[Dict[str, Any]] = None


class TransactionStatusCallbackWrapper(BaseModel):
    """Wrapper for transaction status callback"""
    
    Result: TransactionStatusCallbackResult


class ReversalCallbackResult(BaseModel):
    """Reversal callback result"""
    
    ConversationID: str
    OriginatorConversationID: str
    ResultCode: int
    ResultDesc: str
    ResultType: int
    TransactionID: Optional[str] = None
    ResultParameters: Optional[Dict[str, Any]] = None


class ReversalCallbackWrapper(BaseModel):
    """Wrapper for reversal callback"""
    
    Result: ReversalCallbackResult


class TaxRemittanceCallbackResult(BaseModel):
    """Tax remittance callback result"""
    
    ConversationID: str
    OriginatorConversationID: str
    ResultCode: int
    ResultDesc: str
    ResultType: int
    TransactionID: Optional[str] = None
    ResultParameters: Optional[Dict[str, Any]] = None


class TaxRemittanceCallbackWrapper(BaseModel):
    """Wrapper for tax remittance callback"""
    
    Result: TaxRemittanceCallbackResult


# ============================================================================
# Service Response Models
# ============================================================================

class MpesaTransactionRecord(BaseModel):
    """M-Pesa transaction record for database"""
    
    request_id: str
    transaction_type: str
    phone_number: str
    amount: float
    status: str
    merchant_request_id: Optional[str] = None
    checkout_request_id: Optional[str] = None
    mpesa_receipt_number: Optional[str] = None
    result_code: Optional[int] = None
    result_desc: Optional[str] = None
    raw_response: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MpesaReversalRecord(BaseModel):
    """M-Pesa reversal record for database"""
    
    request_id: str
    original_transaction_id: str
    reversal_amount: float
    status: str
    result_code: Optional[int] = None
    result_desc: Optional[str] = None
    reversal_receipt: Optional[str] = None
    raw_response: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MpesaTaxRecord(BaseModel):
    """M-Pesa tax remittance record"""
    
    request_id: str
    prn: str
    tax_amount: float
    status: str
    result_code: Optional[int] = None
    result_desc: Optional[str] = None
    transaction_id: Optional[str] = None
    raw_response: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Error Response Models
# ============================================================================

class MpesaErrorResponse(BaseModel):
    """Error response from M-Pesa"""
    
    error: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
