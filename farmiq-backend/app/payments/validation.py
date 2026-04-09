"""
Payment Input Validation Module
Validates phone numbers, amounts, and other payment inputs

Author: FarmIQ Backend Team
Date: March 2026
"""

import re
from decimal import Decimal
from typing import Tuple

from app.payments.config import MpesaConfig
from app.payments.exceptions import ValidationException, ErrorCode


class PhoneValidator:
    """Validate phone numbers for different providers"""
    
    # Kenya patterns
    SAFARICOM_PATTERN = r"^(254|0)(7[0-9]{8}|1[0-9]{8})$"  # 07xxxxxxxx or 01xxxxxxxx
    AIRTEL_PATTERN = r"^(254|0)(7[0-9]{8}|6[0-9]{8})$"     # 07xxxxxxxx or 06xxxxxxxx
    
    @staticmethod
    def normalize_phone(phone: str, country_code: str = "254") -> str:
        """
        Normalize phone number to international format
        
        Args:
            phone: Phone number (can be local or international)
            country_code: Country code (default 254 for Kenya)
            
        Returns:
            Normalized phone (254xxxxxxxxxx format)
        """
        phone = phone.strip().replace("+", "").replace("-", "").replace(" ", "")
        
        # Handle 0-prefixed local numbers
        if phone.startswith("0"):
            phone = country_code + phone[1:]
        
        # Handle incomplete numbers
        if not phone.startswith(country_code):
            phone = country_code + phone
        
        return phone
    
    @staticmethod
    def validate_safaricom(phone: str) -> Tuple[bool, str]:
        """Validate Safaricom phone number"""
        normalized = PhoneValidator.normalize_phone(phone)
        
        if re.match(PhoneValidator.SAFARICOM_PATTERN, normalized):
            return True, normalized
        
        return False, normalized
    
    @staticmethod
    def validate_airtel(phone: str) -> Tuple[bool, str]:
        """Validate Airtel phone number"""
        normalized = PhoneValidator.normalize_phone(phone)
        
        if re.match(PhoneValidator.AIRTEL_PATTERN, normalized):
            return True, normalized
        
        return False, normalized
    
    @staticmethod
    def validate_general(phone: str) -> Tuple[bool, str]:
        """General phone validation (Safaricom OR Airtel)"""
        is_valid_safaricom, normalized = PhoneValidator.validate_safaricom(phone)
        if is_valid_safaricom:
            return True, normalized
        
        is_valid_airtel, normalized = PhoneValidator.validate_airtel(phone)
        if is_valid_airtel:
            return True, normalized
        
        return False, normalized


class AmountValidator:
    """Validate payment amounts"""
    
    @staticmethod
    def validate_amount(
        amount: Decimal,
        config: MpesaConfig,
    ) -> Tuple[bool, str]:
        """
        Validate payment amount
        
        Args:
            amount: Payment amount in KES
            config: M-Pesa configuration
            
        Returns:
            (is_valid, error_message)
        """
        # Check type
        if not isinstance(amount, (int, float, Decimal)):
            return False, "Amount must be a number"
        
        amount = Decimal(str(amount))
        
        # Check positive
        if amount <= 0:
            return False, "Amount must be greater than 0"
        
        # Check minimum
        if amount < config.MINIMUM_PAYMENT_KES:
            return False, f"Minimum payment is {config.MINIMUM_PAYMENT_KES} KES"
        
        # Check maximum
        if amount > config.MAXIMUM_PAYMENT_KES:
            return False, f"Maximum payment is {config.MAXIMUM_PAYMENT_KES} KES"
        
        # Check decimal places (KES is 2 decimal places)
        if amount.as_tuple().exponent < -2:
            return False, "Amount cannot have more than 2 decimal places"
        
        return True, ""
    
    @staticmethod
    def validate_tokens_amount(amount: Decimal) -> Tuple[bool, str]:
        """Validate token amount"""
        if amount <= 0:
            return False, "Token amount must be greater than 0"
        
        if amount.as_tuple().exponent < -2:
            return False, "Token amount cannot have more than 2 decimal places"
        
        return True, ""


class FarmIQIDValidator:
    """Validate FarmIQ ID format"""
    
    # FarmIQ ID format: FIQ-<YYYY>-<NNNNN>
    # Example: FIQ-2025-00123
    FARMIQ_ID_PATTERN = r"^FIQ-\d{4}-\d{5}$"
    
    @staticmethod
    def validate(farmiq_id: str) -> Tuple[bool, str]:
        """Validate FarmIQ ID format"""
        if not isinstance(farmiq_id, str):
            return False, "FarmIQ ID must be a string"
        
        farmiq_id = farmiq_id.strip().upper()
        
        if not re.match(FarmIQIDValidator.FARMIQ_ID_PATTERN, farmiq_id):
            return False, f"Invalid FarmIQ ID format. Expected: FIQ-YYYY-NNNNN (got {farmiq_id})"
        
        return True, farmiq_id


class SessionValidator:
    """Validate USSD session data"""
    
    @staticmethod
    def validate_session_id(session_id: str) -> Tuple[bool, str]:
        """Validate USSD session ID format"""
        if not session_id or len(session_id) == 0:
            return False, "Session ID cannot be empty"
        
        # Session ID should be alphanumeric
        if not session_id.replace("-", "").replace("_", "").isalnum():
            return False, "Session ID contains invalid characters"
        
        if len(session_id) > 100:
            return False, "Session ID too long"
        
        return True, session_id


# Public validation functions
def validate_phone_number(phone: str, strict: bool = True) -> str:
    """
    Validate and normalize phone number
    
    Args:
        phone: Phone number
        strict: If True, must be Safaricom/Airtel; if False, just general format
        
    Returns:
        Normalized phone number
        
    Raises:
        ValidationException if invalid
    """
    if not phone or not isinstance(phone, str):
        raise ValidationException(
            message="Phone number is required and must be a string",
            field="phone_number",
        )
    
    if len(phone) < 9:
        raise ValidationException(
            message="Phone number too short",
            field="phone_number",
        )
    
    if len(phone) > 20:
        raise ValidationException(
            message="Phone number too long",
            field="phone_number",
        )
    
    if strict:
        is_valid, normalized = PhoneValidator.validate_general(phone)
    else:
        is_valid, normalized = PhoneValidator.validate_general(phone)
    
    if not is_valid:
        raise ValidationException(
            message=f"Invalid phone number: {phone}",
            field="phone_number",
        )
    
    return normalized


def validate_payment_amount(amount: Decimal, config: MpesaConfig) -> Decimal:
    """
    Validate payment amount
    
    Args:
        amount: Payment amount
        config: M-Pesa configuration
        
    Returns:
        Validated amount as Decimal
        
    Raises:
        ValidationException if invalid
    """
    if not isinstance(amount, (int, float, Decimal)):
        raise ValidationException(
            message="Amount must be a number",
            field="amount",
        )
    
    amount = Decimal(str(amount))
    is_valid, error_msg = AmountValidator.validate_amount(amount, config)
    
    if not is_valid:
        raise ValidationException(
            message=error_msg,
            field="amount",
            value=amount,
        )
    
    return amount


def validate_farmiq_id(farmiq_id: str) -> str:
    """
    Validate FarmIQ ID format
    
    Args:
        farmiq_id: FarmIQ ID
        
    Returns:
        Validated and normalized FarmIQ ID
        
    Raises:
        ValidationException if invalid
    """
    if not farmiq_id:
        raise ValidationException(
            message="FarmIQ ID is required",
            field="farmiq_id",
        )
    
    is_valid, validated_id = FarmIQIDValidator.validate(farmiq_id)
    
    if not is_valid:
        raise ValidationException(
            message=validated_id,  # Error message
            field="farmiq_id",
            value=farmiq_id,
        )
    
    return validated_id


def validate_ussd_session_id(session_id: str) -> str:
    """
    Validate USSD session ID
    
    Args:
        session_id: USSD session ID
        
    Returns:
        Validated session ID
        
    Raises:
        ValidationException if invalid
    """
    is_valid, result = SessionValidator.validate_session_id(session_id)
    
    if not is_valid:
        raise ValidationException(
            message=result,
            field="session_id",
        )
    
    return result


def validate_sms_text(text: str, max_length: int = 480) -> str:
    """
    Validate SMS message text
    
    Args:
        text: SMS text
        max_length: Maximum SMS length
        
    Returns:
        Validated SMS text
        
    Raises:
        ValidationException if invalid
    """
    if not text:
        raise ValidationException(
            message="SMS text cannot be empty",
            field="text",
        )
    
    if len(text) > max_length:
        raise ValidationException(
            message=f"SMS text too long (max {max_length} characters)",
            field="text",
            value=len(text),
        )
    
    return text


def validate_ussd_menu_text(text: str, max_length: int = 182) -> str:
    """
    Validate USSD menu text
    
    Args:
        text: USSD menu text
        max_length: Maximum menu text length (USSD limit)
        
    Returns:
        Validated USSD text
        
    Raises:
        ValidationException if invalid
    """
    if not text:
        raise ValidationException(
            message="USSD menu text cannot be empty",
            field="text",
        )
    
    if len(text) > max_length:
        raise ValidationException(
            message=f"USSD menu text too long (max {max_length} characters)",
            field="text",
            value=len(text),
        )
    
    return text
