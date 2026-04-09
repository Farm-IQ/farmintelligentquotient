"""
M-Pesa Exceptions - Custom exception types for M-Pesa operations
"""


class MpesaException(Exception):
    """Base exception for all M-Pesa related errors"""
    pass


class AuthenticationException(MpesaException):
    """Raised when OAuth authentication fails"""
    pass


class StkPushException(MpesaException):
    """Raised when STK Push operation fails"""
    pass


class TransactionException(MpesaException):
    """Raised when transaction operation fails"""
    pass


class ReversalException(MpesaException):
    """Raised when transaction reversal fails"""
    pass


class TaxRemittanceException(MpesaException):
    """Raised when tax remittance fails"""
    pass


class InvalidPhoneNumberException(MpesaException):
    """Raised when phone number format is invalid"""
    pass


class InsufficientBalanceException(MpesaException):
    """Raised when account balance is insufficient"""
    pass


class TransactionTimeoutException(MpesaException):
    """Raised when transaction times out"""
    pass


class InvalidCredentialsException(MpesaException):
    """Raised when M-Pesa credentials are invalid"""
    pass
