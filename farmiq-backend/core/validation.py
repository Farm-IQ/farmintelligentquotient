"""
FarmIQ Input Validation Framework (Phase 5.1b)
Enhanced Pydantic validators and sanitization for all API requests
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Dict, Any, List
from uuid import UUID
import re
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

# String length limits
MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 5000
MAX_COMMENT_LENGTH = 1000
MAX_ENUM_VALUE_LENGTH = 100

# Pattern validation
VALID_LOCATION_PATTERN = r'^[a-zA-Z0-9\s,.-]+$'  # Location format
VALID_EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
VALID_PHONE_PATTERN = r'^[\d\s\-+()]+$'  # Phone number format


# ============================================================================
# CUSTOM VALIDATORS
# ============================================================================

def validate_string_length(value: str, max_length: int, field_name: str) -> str:
    """Validate string doesn't exceed max length"""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    
    value = value.strip()  # Remove leading/trailing whitespace
    
    if len(value) == 0:
        raise ValueError(f"{field_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters (got {len(value)})")
    
    return value


def validate_positive_number(value: float, field_name: str) -> float:
    """Validate number is positive"""
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")
    return value


def validate_percentage(value: float, field_name: str) -> float:
    """Validate value is between 0 and 100"""
    if value < 0 or value > 100:
        raise ValueError(f"{field_name} must be between 0 and 100 (got {value})")
    return value


def validate_location_format(value: str) -> str:
    """Validate location string format"""
    if not re.match(VALID_LOCATION_PATTERN, value):
        raise ValueError("Location contains invalid characters")
    return value.strip()


def sanitize_html(value: str) -> str:
    """Remove potentially dangerous HTML/script content"""
    # Do not allow common XSS patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'on\w+\s*=',  # onclick=, onerror=, etc.
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
    ]
    
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
    
    return value.strip()


# ============================================================================
# RAG QUERY VALIDATORS
# ============================================================================

def validate_query(query: str, min_length: int = 3, max_length: int = 2000) -> str:
    """
    Validate RAG query string
    
    Args:
        query: Query text
        min_length: Minimum query length (default 3)
        max_length: Maximum query length (default 2000)
        
    Returns:
        Sanitized query string
        
    Raises:
        ValueError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    
    query = query.strip()
    sanitize_html(query)  # Sanitize
    
    if len(query) < min_length:
        raise ValueError(f"Query must be at least {min_length} characters long")
    
    if len(query) > max_length:
        raise ValueError(f"Query cannot exceed {max_length} characters")
    
    # Check for valid characters (allow alphanumeric, spaces, basic punctuation)
    if not re.match(r"^[a-zA-Z0-9\s\.\,\?\!\-\'\"]+$", query):
        raise ValueError("Query contains invalid characters")
    
    return query


# ============================================================================
# CREDIT SCORING VALIDATORS
# ============================================================================

def validate_credit_input(user_id: str, farmer_id: str) -> None:
    """
    Validate credit scoring request inputs
    
    Args:
        user_id: User identifier
        farmer_id: Farmer identifier
        
    Raises:
        ValueError: If inputs are invalid
    """
    if not user_id:
        raise ValueError("user_id is required")
    
    if not isinstance(user_id, str) or len(user_id) < 5:
        raise ValueError("Invalid user_id format (must be string, 5+ chars)")
    
    if not farmer_id:
        raise ValueError("farmer_id is required")
    
    if not isinstance(farmer_id, str) or len(farmer_id) < 5:
        raise ValueError("Invalid farmer_id format (must be string, 5+ chars)")


# ============================================================================
# FILE UPLOAD VALIDATORS
# ============================================================================

def validate_file_upload(filename: str, file_size: int, content_type: str, max_size_mb: int = 50) -> None:
    """
    Validate file upload parameters
    
    Args:
        filename: Name of uploaded file
        file_size: Size of file in bytes
        content_type: MIME type of file
        max_size_mb: Maximum allowed file size in MB
        
    Raises:
        ValueError: If file is invalid
    """
    if not filename:
        raise ValueError("No filename provided")
    
    # Check file type
    allowed_types = ["application/pdf", "text/plain", "text/markdown"]
    if content_type not in allowed_types:
        raise ValueError(
            f"Invalid file type: {content_type}. "
            f"Allowed: {', '.join(allowed_types)}"
        )
    
    # Check file size
    if file_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File size exceeds {max_size_mb}MB limit")
    
    # Check filename length
    if len(filename) > 255:
        raise ValueError("Filename exceeds 255 character limit")
    
    # Prevent directory traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename: path traversal detected")
    
    return None


# ============================================================================
# MARKET/SYMBOL VALIDATORS
# ============================================================================

def validate_symbol(symbol: str, allowed_symbols: Optional[list] = None) -> str:
    """
    Validate trading/market symbol format
    
    Args:
        symbol: Trading symbol (e.g., EURUSD, MAIZE)
        allowed_symbols: Optional list of allowed symbols
        
    Returns:
        Validated symbol (uppercase)
        
    Raises:
        ValueError: If symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")
    
    symbol = symbol.strip().upper()
    
    # Check format: alphanumeric, 2-10 characters
    if not re.match(r'^[A-Z0-9]{2,10}$', symbol):
        raise ValueError("Symbol must be 2-10 alphanumeric characters")
    
    # Check against allowed list if provided
    if allowed_symbols and symbol not in allowed_symbols:
        raise ValueError(f"Symbol {symbol} not in allowed list")
    
    return symbol


# ============================================================================
# TIMEFRAME VALIDATORS
# ============================================================================

def validate_timeframe(timeframe: str, allowed_timeframes: Optional[list] = None) -> str:
    """
    Validate trading timeframe format
    
    Args:
        timeframe: Timeframe (e.g., H1, D1, W1, M1)
        allowed_timeframes: Optional list of allowed timeframes
        
    Returns:
        Validated timeframe (uppercase)
        
    Raises:
        ValueError: If timeframe is invalid
    """
    if not timeframe or not isinstance(timeframe, str):
        raise ValueError("Timeframe must be a non-empty string")
    
    timeframe = timeframe.strip().upper()
    
    # Check format: alphanumeric, 2-3 characters
    if not re.match(r'^[A-Z0-9]{2,3}$', timeframe):
        raise ValueError("Timeframe must be 2-3 alphanumeric characters (e.g., H1, D1)")
    
    # Check against allowed list if provided
    if allowed_timeframes and timeframe not in allowed_timeframes:
        raise ValueError(
            f"Timeframe {timeframe} not supported. "
            f"Allowed: {', '.join(allowed_timeframes)}"
        )
    
    return timeframe


# ============================================================================
# CREDIT LOAN VALIDATORS
# ============================================================================

def validate_loan_params(
    amount: float,
    term_months: int,
    min_amount: float = 1000,
    max_amount: float = 10_000_000,
    min_term: int = 6,
    max_term: int = 36,
) -> None:
    """
    Validate loan application parameters
    
    Args:
        amount: Loan amount
        term_months: Loan term in months
        min_amount: Minimum allowed amount (default 1000)
        max_amount: Maximum allowed amount (default 10M)
        min_term: Minimum loan term in months (default 6)
        max_term: Maximum loan term in months (default 36)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("Loan amount must be a positive number")
    
    if amount < min_amount or amount > max_amount:
        raise ValueError(
            f"Loan amount must be between {min_amount:,.0f} "
            f"and {max_amount:,.0f}"
        )
    
    if not isinstance(term_months, int) or term_months <= 0:
        raise ValueError("Loan term must be a positive integer")
    
    if term_months < min_term or term_months > max_term:
        raise ValueError(
            f"Loan term must be between {min_term} and {max_term} months"
        )


# ============================================================================
# GENERAL UTILITY VALIDATORS (from app/shared/utils)
# ============================================================================

def validate_not_none(value: Any, field_name: str) -> Any:
    """Validate that value is not None"""
    if value is None:
        raise ValueError(f"{field_name} cannot be None")
    return value


def validate_not_empty(value: str, field_name: str, min_length: int = 1) -> str:
    """Validate that string is not empty"""
    if not value or len(value.strip()) < min_length:
        raise ValueError(f"{field_name} is too short (minimum {min_length} characters)")
    return value.strip()


def validate_range(
    value: float | int,
    min_val: float | int,
    max_val: float | int,
    field_name: str
) -> float | int:
    """Validate that value is within range [min_val, max_val]"""
    if value < min_val or value > max_val:
        raise ValueError(
            f"{field_name} must be between {min_val} and {max_val}, got {value}"
        )
    return value


def validate_positive(value: float | int, field_name: str) -> float | int:
    """Validate that value is positive (> 0)"""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    return value


def validate_non_negative(value: float | int, field_name: str) -> float | int:
    """Validate that value is non-negative (>= 0)"""
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative, got {value}")
    return value


def validate_email(email: str, field_name: str = "email") -> str:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        field_name: Field name for error message
        
    Returns:
        Validated email
        
    Raises:
        ValueError: If invalid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid {field_name} format: {email}")
    return email


def validate_uuid(value: str, field_name: str = "id") -> str:
    """
    Validate UUID format
    
    Args:
        value: UUID string to validate
        field_name: Field name for error message
        
    Returns:
        Validated UUID
        
    Raises:
        ValueError: If invalid UUID format
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(pattern, value.lower()):
        raise ValueError(f"Invalid {field_name} format (expected UUID)")
    return value


def validate_list_not_empty(value: list, field_name: str) -> list:
    """
    Validate that list is not empty
    
    Args:
        value: List to validate
        field_name: Field name for error message
        
    Returns:
        Validated list
        
    Raises:
        ValueError: If list is empty
    """
    if not value or len(value) == 0:
        raise ValueError(f"{field_name} cannot be empty")
    return value


def validate_list_length(
    value: list,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "list"
) -> list:
    """
    Validate list length
    
    Args:
        value: List to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Field name for error message
        
    Returns:
        Validated list
        
    Raises:
        ValueError: If list length is invalid
    """
    if min_length is not None and len(value) < min_length:
        raise ValueError(f"{field_name} must have at least {min_length} items")
    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{field_name} must have at most {max_length} items")
    return value


def validate_currency(value: float, field_name: str = "amount") -> float:
    """
    Validate currency amount (non-negative, max 2 decimals)
    
    Args:
        value: Currency amount to validate
        field_name: Field name for error message
        
    Returns:
        Validated currency amount
        
    Raises:
        ValueError: If invalid currency format
    """
    value = validate_non_negative(value, field_name)
    if round(value, 2) != value:
        raise ValueError(f"{field_name} cannot have more than 2 decimal places")
    return value


def normalize_whitespace(value: str) -> str:
    """
    Normalize whitespace in string (reduce multiple spaces to single space)
    
    Args:
        value: String to normalize
        
    Returns:
        Normalized string
    """
    return ' '.join(value.split())


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number (remove non-digits)
    
    Args:
        phone: Phone number string
        
    Returns:
        Normalized phone number (digits only)
    """
    return re.sub(r'\D', '', phone)


# ============================================================================
# BASE REQUEST MODELS WITH VALIDATION
# ============================================================================

class SafeStringField(str):
    """String field with automatic sanitization"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        if not isinstance(v, str):
            raise ValueError("Must be string")
        return sanitize_html(v.strip())


class ValidatedNameModel(BaseModel):
    """Base model with validated name field"""
    
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH, description="Name")
    
    @validator('name')
    def validate_name(cls, v):
        return validate_string_length(v, MAX_NAME_LENGTH, "name")


class ValidatedDescriptionModel(BaseModel):
    """Base model with validated description field"""
    
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    
    @validator('description', pre=True, always=True)
    def validate_description(cls, v):
        if v is None:
            return None
        return validate_string_length(v, MAX_DESCRIPTION_LENGTH, "description")


class ValidatedLocationModel(BaseModel):
    """Base model with validated location field"""
    
    location: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    
    @validator('location')
    def validate_location(cls, v):
        v = validate_string_length(v, MAX_NAME_LENGTH, "location")
        return validate_location_format(v)


# ============================================================================
# SANITIZATION UTILITIES
# ============================================================================

def sanitize_input(value: str, max_length: int = MAX_NAME_LENGTH) -> str:
    """Sanitize and validate user input string"""
    if not isinstance(value, str):
        raise ValueError("Input must be string")
    
    value = value.strip()
    value = sanitize_html(value)
    
    if len(value) > max_length:
        value = value[:max_length]
    
    if len(value) == 0:
        raise ValueError("Input cannot be empty")
    
    return value


def validate_uuid(value: str) -> UUID:
    """Validate and parse UUID"""
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid UUID format: {value}")


# ============================================================================
# FARM-SPECIFIC VALIDATORS
# ============================================================================

class FarmValidators:
    """Validators specific to farm operations"""
    
    @staticmethod
    def validate_acres(value: float) -> float:
        """Validate farm acreage is positive"""
        return validate_positive_number(value, "total_acres")
    
    @staticmethod
    def validate_health_score(value: float) -> float:
        """Validate health score is 0-100"""
        return validate_percentage(value, "health_score")
    
    @staticmethod
    def validate_diversification_index(value: float) -> float:
        """Validate diversification index is 0-100"""
        return validate_percentage(value, "diversification_index")


# ============================================================================
# PRODUCTION-SPECIFIC VALIDATORS
# ============================================================================

class ProductionValidators:
    """Validators specific to production/crop operations"""
    
    @staticmethod
    def validate_yield(value: float) -> float:
        """Validate yield is positive"""
        return validate_positive_number(value, "yield_kg_per_acre")
    
    @staticmethod
    def validate_cost(value: float) -> float:
        """Validate cost is positive"""
        return validate_positive_number(value, "cost")
    
    @staticmethod
    def validate_revenue(value: float) -> float:
        """Validate revenue is positive"""
        return validate_positive_number(value, "revenue")
    
    @staticmethod
    def validate_moisture_content(value: float) -> float:
        """Validate moisture content is 0-100%"""
        return validate_percentage(value, "moisture_content")


# ============================================================================
# MARKET-SPECIFIC VALIDATORS
# ============================================================================

class MarketValidators:
    """Validators specific to market operations"""
    
    @staticmethod
    def validate_price(value: float) -> float:
        """Validate price is positive"""
        return validate_positive_number(value, "price")
    
    @staticmethod
    def validate_demand(value: float) -> float:
        """Validate demand level is 0-100"""
        return validate_percentage(value, "demand_level")


# ============================================================================
# PREDICTION-SPECIFIC VALIDATORS
# ============================================================================

class PredictionValidators:
    """Validators specific to prediction operations"""
    
    @staticmethod
    def validate_confidence(value: float) -> float:
        """Validate confidence score is 0-1"""
        if value < 0 or value > 1:
            raise ValueError(f"Confidence must be between 0 and 1 (got {value})")
        return value
    
    @staticmethod
    def validate_months_ahead(value: int) -> int:
        """Validate months ahead prediction"""
        if value < 1 or value > 24:
            raise ValueError("Months ahead must be between 1 and 24")
        return value
    
    @staticmethod
    def validate_forecast_weeks(value: int) -> int:
        """Validate forecast weeks"""
        if value < 1 or value > 52:
            raise ValueError("Forecast weeks must be between 1 and 52")
        return value


# ============================================================================
# GLOBAL VALIDATION CONTEXT
# ============================================================================

class ValidationContext:
    """Track validation errors and context"""
    
    def __init__(self, request_id: str, endpoint: str):
        self.request_id = request_id
        self.endpoint = endpoint
        self.errors = []
    
    def add_error(self, field: str, message: str):
        """Add validation error"""
        self.errors.append({"field": field, "message": message})
        logger.warning(
            f"Validation error on {self.endpoint}",
            extra={
                "request_id": self.request_id,
                "field": field,
                "message": message,
            }
        )
    
    def has_errors(self) -> bool:
        """Check if any errors"""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[Dict[str, str]]:
        """Get all errors"""
        return self.errors
