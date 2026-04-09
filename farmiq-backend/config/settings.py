"""
Environment Settings for FarmIQ Backend
Supports multiple environments with dynamic configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """
    Main settings configuration for FarmIQ backend
    
    Attributes:
        App settings: name, version, environment, debug
        Server: host, port
        Supabase: URL, keys, JWT
        Authentication: JWT configuration
        Redis: connection URL
        CORS: origins per environment
    """
    
    # ========== APP CONFIGURATION ==========
    app_name: str = "FarmIQ"
    app_version: str = "1.0.0"
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = property(lambda self: self.environment in ['development', 'staging'])
    
    # ========== SERVER CONFIGURATION ==========
    host: str = "0.0.0.0"
    port: int = int(os.getenv('PORT', '8000'))
    
    # ========== SUPABASE CONFIGURATION ==========
    supabase_url: Optional[str] = os.getenv('SUPABASE_URL')
    supabase_key: Optional[str] = os.getenv('SUPABASE_KEY')
    supabase_service_role_key: Optional[str] = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase_jwt_secret: Optional[str] = os.getenv('SUPABASE_JWT_SECRET')
    
    # ========== SMS/COMMUNICATION ==========
    africastalking_api_key: Optional[str] = None
    africastalking_username: Optional[str] = None
    
    # ========== M-PESA DARAJA (TOKEN PURCHASES) ==========
    mpesa_consumer_key: Optional[str] = os.getenv('MPESA_CONSUMER_KEY')
    mpesa_consumer_secret: Optional[str] = os.getenv('MPESA_CONSUMER_SECRET')
    mpesa_business_shortcode: Optional[str] = os.getenv('MPESA_BUSINESS_SHORTCODE')
    mpesa_passkey: Optional[str] = os.getenv('MPESA_PASSKEY')
    mpesa_environment: str = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
    mpesa_api_url: str = os.getenv('MPESA_API_URL', 'https://sandbox.safaricom.co.ke')
    mpesa_callback_url: Optional[str] = os.getenv('MPESA_CALLBACK_URL')
    mpesa_queue_timeout_url: Optional[str] = os.getenv('MPESA_QUEUE_TIMEOUT_URL')
    mpesa_result_url: Optional[str] = os.getenv('MPESA_RESULT_URL')
    mpesa_initiator_name: Optional[str] = os.getenv('MPESA_INITIATOR_NAME')
    mpesa_initiator_password: Optional[str] = os.getenv('MPESA_INITIATOR_PASSWORD')
    mpesa_min_amount: int = int(os.getenv('MPESA_MIN_AMOUNT', '50'))
    mpesa_max_amount: int = int(os.getenv('MPESA_MAX_AMOUNT', '150000'))
    mpesa_fiq_to_kes_rate: float = float(os.getenv('MPESA_FIQ_TO_KES_RATE', '1.5'))
    
    # ========== BLOCKCHAIN (HEDERA) ==========
    hedera_account_id: Optional[str] = os.getenv('HEDERA_ACCOUNT_ID')
    hedera_private_key: Optional[str] = os.getenv('HEDERA_PRIVATE_KEY')
    hedera_network: str = os.getenv('HEDERA_NETWORK', 'testnet')
    hedera_token_id: Optional[str] = os.getenv('HEDERA_TOKEN_ID')  # FIQ Token ID
    hedera_hcs_topic_id: Optional[str] = os.getenv('HEDERA_HCS_TOPIC_ID')  # Audit log topic
    hedera_contract_id: Optional[str] = os.getenv('HEDERA_CONTRACT_ID')  # Smart contract
    
    # ========== DATABASE ==========
    supabase_url: Optional[str] = os.getenv('SUPABASE_URL')
    database_url: Optional[str] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost/farmiq'
    )
    
    # For backward compatibility
    @property
    def DATABASE_URL(self) -> str:
        """Return uppercase DATABASE_URL for backward compatibility"""
        return self.database_url or 'postgresql://postgres:postgres@localhost/farmiq'
    
    # ========== JWT AUTHENTICATION ==========
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # ========== IN-PROCESS CACHING ==========
    cache_backend: str = os.getenv('CACHE_BACKEND', 'in_memory')
    cache_max_size: int = int(os.getenv('CACHE_MAX_SIZE', '10000'))
    cache_default_ttl: int = int(os.getenv('CACHE_DEFAULT_TTL', '300'))
    cache_cleanup_interval: int = int(os.getenv('CACHE_CLEANUP_INTERVAL', '300'))
    
    # ========== AI USAGE & TOKEN QUOTAS (Phase 3) ==========
    # Default daily quota per user (in FIQ tokens)
    default_daily_quota: float = float(os.getenv('DEFAULT_DAILY_QUOTA', '100.0'))
    # Default monthly quota per user (in FIQ tokens)
    default_monthly_quota: float = float(os.getenv('DEFAULT_MONTHLY_QUOTA', '2000.0'))
    # Enable quota enforcement
    enable_quota_enforcement: bool = os.getenv('ENABLE_QUOTA_ENFORCEMENT', 'true').lower() == 'true'
    # Token cost per service type
    farmgrow_token_cost: float = float(os.getenv('FARMGROW_TOKEN_COST', '1.0'))
    farmscore_token_cost: float = float(os.getenv('FARMSCORE_TOKEN_COST', '1.0'))
    farmsuite_token_cost: float = float(os.getenv('FARMSUITE_TOKEN_COST', '1.0'))
    
    @property
    def cors_origins(self) -> List[str]:
        """
        Get CORS origins based on environment
        Can be overridden by CORS_ORIGINS env variable
        
        Returns:
            List of allowed origins
        """
        env_origins = os.getenv('CORS_ORIGINS')
        if env_origins:
            return [origin.strip() for origin in env_origins.split(',')]
        
        default_origins = {
            'development': [
                'http://localhost:4200',
                'http://localhost:3000',
                'http://localhost:8080',
            ],
            'staging': [
                'https://farmiq-staging.vercel.app',
                'https://api-staging.farmiq.com',
            ],
            'production': [
                'https://farmiq-six.vercel.app',
                'https://farmiq.com',
                'https://api.farmiq.com',
            ]
        }
        return default_origins.get(self.environment, default_origins['development'])
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra environ variables


# Global instance
settings = Settings()

# Module exports for backward compatibility
DATABASE_URL = settings.DATABASE_URL
