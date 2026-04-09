"""
Payment & Integration Errors Module
Comprehensive error handling for payments, USSD, M-Pesa, Afrika Talking, and Hedera

Author: FarmIQ Backend Team
Date: March 2026
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for payment system"""
    
    # M-Pesa errors
    MPESA_AUTH_FAILED = "mpesa_auth_failed"
    MPESA_INVALID_AMOUNT = "mpesa_invalid_amount"
    MPESA_STK_TIMEOUT = "mpesa_stk_timeout"
    MPESA_USER_CANCELLED = "mpesa_user_cancelled"
    MPESA_INSUFFICIENT_FUNDS = "mpesa_insufficient_funds"
    MPESA_INVALID_PHONE = "mpesa_invalid_phone"
    MPESA_NETWORK_ERROR = "mpesa_network_error"
    MPESA_CALLBACK_ERROR = "mpesa_callback_error"
    
    # Afrika Talking errors
    AFRITALK_AUTH_FAILED = "afritalk_auth_failed"
    AFRITALK_INVALID_PHONE = "afritalk_invalid_phone"
    AFRITALK_SMS_FAILED = "afritalk_sms_failed"
    AFRITALK_USSD_FAILED = "afritalk_ussd_failed"
    AFRITALK_INSUFFICIENT_BALANCE = "afritalk_insufficient_balance"
    AFRITALK_NETWORK_ERROR = "afritalk_network_error"
    AFRITALK_SESSION_EXPIRED = "afritalk_session_expired"
    
    # Hedera errors
    HEDERA_CONNECTION_FAILED = "hedera_connection_failed"
    HEDERA_TRANSACTION_FAILED = "hedera_transaction_failed"
    HEDERA_INSUFFICIENT_HBARS = "hedera_insufficient_hbars"
    HEDERA_TOKEN_NOT_FOUND = "hedera_token_not_found"
    HEDERA_ACCOUNT_NOT_ASSOCIATED = "hedera_account_not_associated"
    HEDERA_ACCOUNT_FROZEN = "hedera_account_frozen"
    HEDERA_INVALID_AMOUNT = "hedera_invalid_amount"
    HEDERA_TIMEOUT = "hedera_timeout"
    
    # Payment gateway errors
    GATEWAY_CONFIG_ERROR = "gateway_config_error"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_NOT_AVAILABLE = "provider_not_available"
    INVALID_PROVIDER = "invalid_provider"
    PAYMENT_FAILED = "payment_failed"
    TOKEN_MINT_FAILED = "token_mint_failed"
    ESCROW_LOCK_FAILED = "escrow_lock_failed"
    
    # Business logic errors
    INSUFFICIENT_TOKENS = "insufficient_tokens"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INVALID_TRANSACTION = "invalid_transaction"
    TRANSACTION_EXPIRED = "transaction_expired"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    INVALID_AMOUNT = "invalid_amount"
    USER_NOT_FOUND = "user_not_found"
    
    # Validation errors
    VALIDATION_ERROR = "validation_error"
    INVALID_PHONE_FORMAT = "invalid_phone_format"
    INVALID_AMOUNT_FORMAT = "invalid_amount_format"
    MISSING_REQUIRED_FIELD = "missing_required_field"


class PaymentException(Exception):
    """Base exception for payment system"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        http_status_code: int = 400,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.http_status_code = http_status_code
        super().__init__(f"[{error_code}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to response dict"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
        }


class MpesaException(PaymentException):
    """M-Pesa specific exception"""
    pass


class AfrikaTalkingException(PaymentException):
    """Afrika Talking specific exception"""
    pass


class HederaException(PaymentException):
    """Hedera specific exception"""
    pass


class PaymentGatewayException(PaymentException):
    """Payment gateway orchestration exception"""
    pass


class ValidationException(PaymentException):
    """Input validation exception"""
    
    def __init__(
        self,
        message: str,
        field: str = None,
        value: Any = None,
    ):
        details = {"field": field, "value": str(value)} if field else {}
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            http_status_code=422,
        )


class ConfigurationException(PaymentException):
    """Configuration error exception"""
    
    def __init__(self, message: str, provider: str = None):
        super().__init__(
            error_code=ErrorCode.GATEWAY_CONFIG_ERROR,
            message=message,
            details={"provider": provider},
            http_status_code=500,
        )


# Error recovery strategies
class ErrorRecoveryStrategy(str, Enum):
    """Strategies for handling errors"""
    RETRY = "retry"
    FALLBACK = "fallback"
    MANUAL_INTERVENTION = "manual_intervention"
    FAIL_SAFE = "fail_safe"
    IGNORE = "ignore"


class ErrorRecoveryHandler:
    """Handle error recovery based on error type"""
    
    # Retry strategy for transient errors
    RETRY_ERRORS = {
        ErrorCode.MPESA_NETWORK_ERROR,
        ErrorCode.MPESA_STK_TIMEOUT,
        ErrorCode.AFRITALK_NETWORK_ERROR,
        ErrorCode.HEDERA_TIMEOUT,
        ErrorCode.HEDERA_CONNECTION_FAILED,
    }
    
    # Fallback strategy for provider unavailability
    FALLBACK_ERRORS = {
        ErrorCode.PROVIDER_NOT_AVAILABLE,
        ErrorCode.AFRITALK_INSUFFICIENT_BALANCE,
    }
    
    # Manual intervention required
    MANUAL_ERRORS = {
        ErrorCode.MPESA_CALLBACK_ERROR,
        ErrorCode.MPESA_USER_CANCELLED,
        ErrorCode.DUPLICATE_TRANSACTION,
    }
    
    @staticmethod
    def get_strategy(error_code: ErrorCode) -> ErrorRecoveryStrategy:
        """Determine recovery strategy based on error"""
        if error_code in ErrorRecoveryHandler.RETRY_ERRORS:
            return ErrorRecoveryStrategy.RETRY
        elif error_code in ErrorRecoveryHandler.FALLBACK_ERRORS:
            return ErrorRecoveryStrategy.FALLBACK
        elif error_code in ErrorRecoveryHandler.MANUAL_ERRORS:
            return ErrorRecoveryStrategy.MANUAL_INTERVENTION
        else:
            return ErrorRecoveryStrategy.FAIL_SAFE
    
    @staticmethod
    def should_retry(error_code: ErrorCode) -> bool:
        """Check if error should be retried"""
        return error_code in ErrorRecoveryHandler.RETRY_ERRORS
    
    @staticmethod
    def is_retriable_with_backoff(error_code: ErrorCode) -> bool:
        """Check if error should be retried with exponential backoff"""
        transient_errors = {
            ErrorCode.MPESA_NETWORK_ERROR,
            ErrorCode.AFRITALK_NETWORK_ERROR,
            ErrorCode.HEDERA_CONNECTION_FAILED,
            ErrorCode.HEDERA_TIMEOUT,
        }
        return error_code in transient_errors


# Helper functions
def map_mpesa_error(mpesa_error_code: str, mpesa_message: str = "") -> ErrorCode:
    """Map M-Pesa error code to PaymentException error code"""
    error_map = {
        "1": ErrorCode.MPESA_INSUFFICIENT_FUNDS,
        "2": ErrorCode.MPESA_INVALID_PHONE,
        "1001": ErrorCode.MPESA_USER_CANCELLED,
        "2001": ErrorCode.MPESA_STK_TIMEOUT,
        "500": ErrorCode.MPESA_NETWORK_ERROR,
    }
    return error_map.get(mpesa_error_code, ErrorCode.MPESA_NETWORK_ERROR)


def map_afritalk_error(status_code: int, message: str = "") -> ErrorCode:
    """Map Afrika Talking error to PaymentException error code"""
    if status_code == 401:
        return ErrorCode.AFRITALK_AUTH_FAILED
    elif status_code == 422:
        if "phone" in message.lower():
            return ErrorCode.AFRITALK_INVALID_PHONE
        return ErrorCode.VALIDATION_ERROR
    elif status_code == 429:
        return ErrorCode.AFRITALK_INSUFFICIENT_BALANCE
    else:
        return ErrorCode.AFRITALK_NETWORK_ERROR


def map_hedera_error(hedera_error: Exception) -> ErrorCode:
    """Map Hedera error to PaymentException error code"""
    error_str = str(hedera_error).lower()
    
    if "connection" in error_str or "timeout" in error_str:
        return ErrorCode.HEDERA_CONNECTION_FAILED
    elif "insufficient" in error_str:
        return ErrorCode.HEDERA_INSUFFICIENT_HBARS
    elif "not found" in error_str or "token" in error_str:
        return ErrorCode.HEDERA_TOKEN_NOT_FOUND
    elif "frozen" in error_str:
        return ErrorCode.HEDERA_ACCOUNT_FROZEN
    else:
        return ErrorCode.HEDERA_TRANSACTION_FAILED


# Structured error logging
class ErrorLogger:
    """Structured error logging for debugging"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def log_payment_error(
        self,
        error: PaymentException,
        context: Dict[str, Any] = None,
    ):
        """Log payment error with context"""
        self.logger.error(
            f"Payment error: {error.error_code}",
            error_code=error.error_code.value,
            message=error.message,
            details=error.details,
            context=context or {},
        )
    
    def log_retry_attempt(
        self,
        error_code: ErrorCode,
        attempt: int,
        max_attempts: int,
    ):
        """Log retry attempt"""
        self.logger.warning(
            f"Retrying after error: {error_code}",
            error_code=error_code.value,
            attempt=attempt,
            max_attempts=max_attempts,
        )
    
    def log_fallback_activated(
        self,
        from_provider: str,
        to_provider: str,
    ):
        """Log fallback to alternative provider"""
        self.logger.warning(
            f"Fallback activated",
            from_provider=from_provider,
            to_provider=to_provider,
        )
