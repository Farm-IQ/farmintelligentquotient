"""
Unified Payment Gateway Configuration
Centralizes all payment provider configurations (M-Pesa, Afrika Talking, Hedera)

Author: FarmIQ Backend Team
Date: March 2026
"""

import os
from enum import Enum
from typing import Optional
from decimal import Decimal
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


class PaymentProvider(str, Enum):
    """Supported payment providers"""
    MPESA = "mpesa"
    AIRTEL_MONEY = "airtel"
    MOBILE_MONEY = "mobile_money"


class TokenType(str, Enum):
    """Types of tokens/NFTs"""
    FIQ = "fiq"  # FarmIQ token
    FSC = "fsc"  # FarmScore credit
    CREDIT = "credit"


class TransactionStatus(str, Enum):
    """Transaction status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REVERSED = "reversed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


@dataclass
class MpesaConfig:
    """M-Pesa/Daraja API Configuration"""
    
    # OAuth & Authentication
    DARAJA_BASE_URL: str = os.getenv("DARAJA_BASE_URL", "https://sandbox.safaricom.co.ke")
    DARAJA_CONSUMER_KEY: str = os.getenv("DARAJA_CONSUMER_KEY", "")
    DARAJA_CONSUMER_SECRET: str = os.getenv("DARAJA_CONSUMER_SECRET", "")
    DARAJA_PASSKEY: str = os.getenv("DARAJA_PASSKEY", "")
    DARAJA_BUSINESS_SHORTCODE: str = os.getenv("DARAJA_BUSINESS_SHORTCODE", "174379")
    
    # API Endpoints
    OAUTH_URL: str = f"{DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    STK_PUSH_URL: str = f"{DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    QUERY_URL: str = f"{DARAJA_BASE_URL}/mpesa/stkpushquery/v1/query"
    CALLBACK_CONFIRMATION_URL: str = os.getenv(
        "CALLBACK_CONFIRMATION_URL",
        "https://farmiq.example.com/api/v1/payments/mpesa/confirmation"
    )
    CALLBACK_VALIDATION_URL: str = os.getenv(
        "CALLBACK_VALIDATION_URL",
        "https://farmiq.example.com/api/v1/payments/mpesa/validation"
    )
    
    # Configuration
    STK_PUSH_TIMEOUT_SECONDS: int = 30
    TOKEN_EXPIRY_SECONDS: int = 3600
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 2
    
    # Exchange rates
    KES_TO_FIQ_RATE: Decimal = Decimal(os.getenv("KES_TO_FIQ_RATE", "10"))  # 1 KES = 0.1 FIQ
    MINIMUM_PAYMENT_KES: Decimal = Decimal(os.getenv("MINIMUM_PAYMENT_KES", "50"))
    MAXIMUM_PAYMENT_KES: Decimal = Decimal(os.getenv("MAXIMUM_PAYMENT_KES", "150000"))
    
    def __post_init__(self):
        """Validate M-Pesa configuration"""
        if not self.DARAJA_CONSUMER_KEY:
            raise ValueError("DARAJA_CONSUMER_KEY not configured")
        if not self.DARAJA_CONSUMER_SECRET:
            raise ValueError("DARAJA_CONSUMER_SECRET not configured")


@dataclass
class AfrikaTalkingConfig:
    """Afrika Talking Configuration (USSD + SMS)"""
    
    # API Configuration
    AFRITALK_API_KEY: str = os.getenv("AFRITALK_API_KEY", "")
    AFRITALK_USERNAME: str = os.getenv("AFRITALK_USERNAME", "sandbox")
    AFRITALK_BASE_URL: str = os.getenv("AFRITALK_BASE_URL", "https://api.sandbox.africastalking.com")
    
    # USSD Configuration
    USSD_SHORT_CODE: str = os.getenv("USSD_SHORT_CODE", "*384*46648#")
    USSD_SESSION_TIMEOUT_SECONDS: int = int(os.getenv("USSD_SESSION_TIMEOUT_SECONDS", "300"))
    USSD_CALLBACK_URL: str = os.getenv(
        "USSD_CALLBACK_URL",
        "https://farmiq.example.com/api/v1/payments/ussd/callback"
    )
    
    # SMS Configuration
    SMS_SENDER_ID: str = os.getenv("SMS_SENDER_ID", "FarmIQ")
    SMS_BATCH_SIZE: int = int(os.getenv("SMS_BATCH_SIZE", "100"))
    SMS_DELIVERY_TIMEOUT_SECONDS: int = int(os.getenv("SMS_DELIVERY_TIMEOUT_SECONDS", "600"))
    
    # Rates
    SMS_COST_KES_PER_MESSAGE: Decimal = Decimal(os.getenv("SMS_COST_KES", "1"))
    
    # Retry configuration
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 2
    
    def __post_init__(self):
        """Validate Afrika Talking configuration"""
        if not self.AFRITALK_API_KEY:
            raise ValueError("AFRITALK_API_KEY not configured")


@dataclass
class HederaConfig:
    """Hedera Hashgraph Configuration (HCS + HTS)"""
    
    # Network & Account
    HEDERA_NETWORK: str = os.getenv("HEDERA_NETWORK", "testnet")
    HEDERA_ACCOUNT_ID: str = os.getenv("HEDERA_ACCOUNT_ID", "0.0.0000")
    HEDERA_PRIVATE_KEY: str = os.getenv("HEDERA_PRIVATE_KEY", "")
    
    # HCS (Consensus Service) - Immutable Audit Logging
    HEDERA_HCS_TOPIC_ID: str = os.getenv("HEDERA_HCS_TOPIC_ID", "")
    HCS_AUTO_CREATE_TOPIC: bool = os.getenv("HCS_AUTO_CREATE_TOPIC", "true").lower() == "true"
    HCS_TOPIC_MEMO: str = "FarmIQ AI Usage & Payment Audit Log"
    
    # HTS (Token Service) - FIQ Token Management
    HEDERA_TOKEN_ID: str = os.getenv("HEDERA_TOKEN_ID", "0.0.0000")
    HEDERA_TOKEN_DECIMALS: int = 2
    HEDERA_TOKEN_INITIAL_SUPPLY: int = int(os.getenv("HEDERA_TOKEN_INITIAL_SUPPLY", "1000000000"))
    HEDERA_TOKEN_SYMBOL: str = "FIQ"
    HEDERA_TOKEN_NAME: str = "FarmIQ Token"
    HEDERA_VAULT_ACCOUNT_ID: str = os.getenv("HEDERA_VAULT_ACCOUNT_ID", "0.0.0000")
    
    # HSCS (Scheduled Contract Service) - Smart Contract Execution
    HEDERA_CONTRACT_ID: str = os.getenv("HEDERA_CONTRACT_ID", "0.0.0000")
    CONTRACT_GAS_LIMIT: int = int(os.getenv("CONTRACT_GAS_LIMIT", "100000"))
    
    # Configuration
    GAS_PRICE_TINYBARS: int = int(os.getenv("GAS_PRICE_TINYBARS", "1"))
    MAX_TRANSACTION_FEE_HBARS: float = float(os.getenv("MAX_TRANSACTION_FEE_HBARS", "2"))
    
    # Retry configuration
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 2
    
    def __post_init__(self):
        """Validate Hedera configuration"""
        if not self.HEDERA_PRIVATE_KEY:
            raise ValueError("HEDERA_PRIVATE_KEY not configured")
        if not self.HEDERA_ACCOUNT_ID or self.HEDERA_ACCOUNT_ID == "0.0.0000":
            raise ValueError("HEDERA_ACCOUNT_ID not configured")


@dataclass
class PaymentGatewayConfig:
    """Unified Payment Gateway Configuration"""
    
    # Providers
    mpesa: MpesaConfig = None
    afritalk: AfrikaTalkingConfig = None
    hedera: HederaConfig = None
    
    # Default provider
    DEFAULT_PROVIDER: PaymentProvider = PaymentProvider.MPESA
    
    # Global configuration
    PAYMENT_CONFIRMATION_TIMEOUT_SECONDS: int = int(os.getenv("PAYMENT_CONFIRMATION_TIMEOUT", "600"))
    TRANSACTION_RETENTION_DAYS: int = int(os.getenv("TRANSACTION_RETENTION_DAYS", "30"))
    
    # Feature flags
    ENABLE_MOCK_PAYMENTS: bool = os.getenv("ENABLE_MOCK_PAYMENTS", "false").lower() == "true"
    ENABLE_HEDERA_LOGGING: bool = os.getenv("ENABLE_HEDERA_LOGGING", "true").lower() == "true"
    ENABLE_SMS_NOTIFICATIONS: bool = os.getenv("ENABLE_SMS_NOTIFICATIONS", "true").lower() == "true"
    ENABLE_CREDIT_HOLD: bool = os.getenv("ENABLE_CREDIT_HOLD", "true").lower() == "true"
    
    # Webhook security
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    WEBHOOK_SIGNATURE_ALGORITHM: str = "sha256"
    
    def __init__(self):
        """Initialize all payment configurations"""
        try:
            self.mpesa = MpesaConfig()
        except ValueError as e:
            print(f"Warning: M-Pesa not configured: {e}")
        
        try:
            self.afritalk = AfrikaTalkingConfig()
        except ValueError as e:
            print(f"Warning: Afrika Talking not configured: {e}")
        
        try:
            self.hedera = HederaConfig()
        except ValueError as e:
            print(f"Warning: Hedera not configured: {e}")
        
        if not self.mpesa and not self.afritalk:
            raise ValueError("At least one payment provider must be configured")


# Global config instance (lazy-loaded)
_payment_config: Optional[PaymentGatewayConfig] = None


def get_payment_config() -> PaymentGatewayConfig:
    """Get singleton payment gateway configuration"""
    global _payment_config
    if _payment_config is None:
        _payment_config = PaymentGatewayConfig()
    return _payment_config


def get_mpesa_config() -> MpesaConfig:
    """Get M-Pesa configuration"""
    config = get_payment_config()
    if not config.mpesa:
        raise ValueError("M-Pesa not configured")
    return config.mpesa


def get_afritalk_config() -> AfrikaTalkingConfig:
    """Get Afrika Talking configuration"""
    config = get_payment_config()
    if not config.afritalk:
        raise ValueError("Afrika Talking not configured")
    return config.afritalk


def get_hedera_config() -> HederaConfig:
    """Get Hedera configuration"""
    config = get_payment_config()
    if not config.hedera:
        raise ValueError("Hedera not configured")
    return config.hedera
