"""
FarmIQ Application Configuration (Phase 5.3)
Multi-app configuration support for FarmGrow, FarmScore, and FarmSuite
Centralized settings for all three agricultural intelligence platforms
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# APP TYPES
# ============================================================================

class AppType(str, Enum):
    """Supported application types"""
    FARMGROW = "farmgrow"       # RAG-based farming insights
    FARMSCORE = "farmscore"     # ML-based scoring and predictions
    FARMSUITE = "farmsuite"     # Integrated intelligence platform


# ============================================================================
# FARMGROW CONFIGURATION
# ============================================================================

class FarmGrowConfig:
    """Configuration for FarmGrow RAG application"""
    
    # RAG Settings
    RAG_CHUNK_SIZE = 1000
    RAG_CHUNK_OVERLAP = 100
    RAG_TOP_K = 5  # Number of chunks to retrieve per query
    
    # Ollama LLM Settings
    OLLAMA_MODEL = "mistral"
    OLLAMA_TEMPERATURE = 0.7
    OLLAMA_MAX_TOKENS = 2000
    OLLAMA_TIMEOUT_SECONDS = 60
    
    # Embeddings Settings
    EMBEDDINGS_MODEL = "all-minilm"  # via Ollama
    EMBEDDINGS_DIMENSION = 384
    EMBEDDINGS_CACHE_TTL = 86400 * 7  # 7 days
    
    # Document Processing
    SUPPORTED_FILE_TYPES = {".pdf", ".txt", ".docx", ".csv"}
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
    
    # API Rate Limits (farmgrow-specific)
    RAG_QUERY_RATE_LIMIT = 20  # per minute per user
    DOCUMENT_UPLOAD_RATE_LIMIT = 5  # per minute per user
    BATCH_INGEST_RATE_LIMIT = 2  # per minute per user
    
    # Caching
    QUERY_CACHE_TTL = 3600  # 1 hour
    EMBEDDING_CACHE_SIZE = 10000
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get FarmGrow configuration as dictionary"""
        return {
            "rag": {
                "chunk_size": FarmGrowConfig.RAG_CHUNK_SIZE,
                "chunk_overlap": FarmGrowConfig.RAG_CHUNK_OVERLAP,
                "top_k": FarmGrowConfig.RAG_TOP_K,
            },
            "ollama": {
                "model": FarmGrowConfig.OLLAMA_MODEL,
                "temperature": FarmGrowConfig.OLLAMA_TEMPERATURE,
                "max_tokens": FarmGrowConfig.OLLAMA_MAX_TOKENS,
                "timeout_seconds": FarmGrowConfig.OLLAMA_TIMEOUT_SECONDS,
            },
            "embeddings": {
                "model": FarmGrowConfig.EMBEDDINGS_MODEL,
                "dimension": FarmGrowConfig.EMBEDDINGS_DIMENSION,
                "cache_ttl": FarmGrowConfig.EMBEDDINGS_CACHE_TTL,
            },
            "rate_limits": {
                "rag_query": FarmGrowConfig.RAG_QUERY_RATE_LIMIT,
                "document_upload": FarmGrowConfig.DOCUMENT_UPLOAD_RATE_LIMIT,
                "batch_ingest": FarmGrowConfig.BATCH_INGEST_RATE_LIMIT,
            },
            "caching": {
                "query_ttl": FarmGrowConfig.QUERY_CACHE_TTL,
                "embedding_cache_size": FarmGrowConfig.EMBEDDING_CACHE_SIZE,
            }
        }


# ============================================================================
# FARMSCORE CONFIGURATION
# ============================================================================

class FarmScoreConfig:
    """Configuration for FarmScore ML application"""
    
    # ML Model Settings
    ML_MODELS = [
        "YieldPredictor",
        "ExpenseForecaster",
        "DiseaseClassifier",
        "MarketPredictor",
        "ROIOptimizer",
    ]
    
    # Training Settings
    TRAIN_TEST_SPLIT = 0.8
    VALIDATION_SPLIT = 0.1
    BATCH_SIZE = 32
    EPOCHS = 50
    LEARNING_RATE = 0.001
    
    # Prediction Settings
    PREDICTION_CONFIDENCE_THRESHOLD = 0.7
    FALLBACK_TO_BASELINE = True  # Use baseline when confidence < threshold
    
    # Feature Engineering
    ENGINEER_SEASONAL_FEATURES = True
    ENGINEER_INTERACTION_FEATURES = True
    FEATURE_SCALING = "standard"  # standard or minmax
    
    # API Rate Limits (farmscore-specific)
    PREDICTION_RATE_LIMIT = 100  # per minute per farm
    TRAINING_RATE_LIMIT = 5  # per day (training is expensive)
    MODEL_STATUS_RATE_LIMIT = 50  # per minute
    
    # Caching & Performance
    PREDICTION_CACHE_TTL = 1800  # 30 minutes
    FEATURE_CACHE_TTL = 3600  # 1 hour
    MODEL_INFO_CACHE_TTL = 86400  # 24 hours
    
    # Metrics & Monitoring
    TRACK_PREDICTION_LATENCY = True
    TRACK_MODEL_ACCURACY = True
    MIN_SAMPLES_FOR_TRAINING = 100
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get FarmScore configuration as dictionary"""
        return {
            "models": FarmScoreConfig.ML_MODELS,
            "training": {
                "train_test_split": FarmScoreConfig.TRAIN_TEST_SPLIT,
                "validation_split": FarmScoreConfig.VALIDATION_SPLIT,
                "batch_size": FarmScoreConfig.BATCH_SIZE,
                "epochs": FarmScoreConfig.EPOCHS,
                "learning_rate": FarmScoreConfig.LEARNING_RATE,
            },
            "prediction": {
                "confidence_threshold": FarmScoreConfig.PREDICTION_CONFIDENCE_THRESHOLD,
                "fallback_to_baseline": FarmScoreConfig.FALLBACK_TO_BASELINE,
            },
            "feature_engineering": {
                "seasonal_features": FarmScoreConfig.ENGINEER_SEASONAL_FEATURES,
                "interaction_features": FarmScoreConfig.ENGINEER_INTERACTION_FEATURES,
                "scaling": FarmScoreConfig.FEATURE_SCALING,
            },
            "rate_limits": {
                "prediction": FarmScoreConfig.PREDICTION_RATE_LIMIT,
                "training": FarmScoreConfig.TRAINING_RATE_LIMIT,
                "model_status": FarmScoreConfig.MODEL_STATUS_RATE_LIMIT,
            },
            "caching": {
                "prediction_ttl": FarmScoreConfig.PREDICTION_CACHE_TTL,
                "feature_ttl": FarmScoreConfig.FEATURE_CACHE_TTL,
                "model_info_ttl": FarmScoreConfig.MODEL_INFO_CACHE_TTL,
            }
        }


# ============================================================================
# FARMSUITE CONFIGURATION
# ============================================================================

class FarmSuiteConfig:
    """Configuration for FarmSuite integrated intelligence platform"""
    
    # Integration Settings
    INTEGRATE_FARMGROW = True  # Use FarmGrow insights
    INTEGRATE_FARMSCORE = True  # Use FarmScore predictions
    
    # Dashboard Settings
    DASHBOARD_REFRESH_INTERVAL = 300  # 5 minutes
    DASHBOARD_METRICS_RETENTION = 30 * 86400  # 30 days
    
    # Alerting Settings
    ALERT_ENABLED = True
    ALERT_CHANNELS = ["email", "api", "webhook"]
    ALERT_SEVERITY_LEVELS = ["info", "warning", "critical"]
    
    # Analytics Settings
    TRACK_USER_BEHAVIOR = True
    TRACK_API_METRICS = True
    ANALYTICS_RETENTION_DAYS = 90
    
    # API Rate Limits (farmsuite-specific)
    DASHBOARD_RATE_LIMIT = 30  # per minute per user
    ALERT_CONFIG_RATE_LIMIT = 10  # per minute
    ANALYTICS_RATE_LIMIT = 50  # per minute
    
    # Caching & Performance
    DASHBOARD_CACHE_TTL = 300  # 5 minutes
    ANALYTICS_CACHE_TTL = 3600  # 1 hour
    METRICS_CACHE_TTL = 60  # 1 minute
    
    # Multi-tenant Support
    ENABLE_MULTI_TENANCY = False
    DEFAULT_TENANT_QUOTA_GB = 100
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get FarmSuite configuration as dictionary"""
        return {
            "integration": {
                "farmgrow": FarmSuiteConfig.INTEGRATE_FARMGROW,
                "farmscore": FarmSuiteConfig.INTEGRATE_FARMSCORE,
            },
            "dashboard": {
                "refresh_interval": FarmSuiteConfig.DASHBOARD_REFRESH_INTERVAL,
                "metrics_retention_days": FarmSuiteConfig.DASHBOARD_METRICS_RETENTION // 86400,
            },
            "alerting": {
                "enabled": FarmSuiteConfig.ALERT_ENABLED,
                "channels": FarmSuiteConfig.ALERT_CHANNELS,
                "severity_levels": FarmSuiteConfig.ALERT_SEVERITY_LEVELS,
            },
            "analytics": {
                "track_user_behavior": FarmSuiteConfig.TRACK_USER_BEHAVIOR,
                "track_api_metrics": FarmSuiteConfig.TRACK_API_METRICS,
                "retention_days": FarmSuiteConfig.ANALYTICS_RETENTION_DAYS,
            },
            "rate_limits": {
                "dashboard": FarmSuiteConfig.DASHBOARD_RATE_LIMIT,
                "alert_config": FarmSuiteConfig.ALERT_CONFIG_RATE_LIMIT,
                "analytics": FarmSuiteConfig.ANALYTICS_RATE_LIMIT,
            },
            "caching": {
                "dashboard_ttl": FarmSuiteConfig.DASHBOARD_CACHE_TTL,
                "analytics_ttl": FarmSuiteConfig.ANALYTICS_CACHE_TTL,
                "metrics_ttl": FarmSuiteConfig.METRICS_CACHE_TTL,
            }
        }


# ============================================================================
# SHARED/COMMON CONFIGURATION
# ============================================================================

class SharedConfig:
    """Shared configuration across all apps"""
    
    # Database & Storage
    DATABASE_CONNECT_TIMEOUT = 10
    DATABASE_QUERY_TIMEOUT = 30
    DATABASE_POOL_SIZE = 20
    DATABASE_POOL_MAX_OVERFLOW = 5
    CACHE_DEFAULT_TTL = 300  # 5 minutes
    
    # Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_SPECIAL_CHARS = True
    SESSION_TIMEOUT_MINUTES = 60
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = 24
    
    # Logging & Monitoring
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "json"  # json or text
    ENABLE_REQUEST_LOGGING = True
    ENABLE_PERFORMANCE_LOGGING = True
    
    # API Settings
    API_TITLE = "FarmIQ Vision"
    API_DESCRIPTION = "Agricultural Intelligence Platform"
    API_VERSION = "2.0.0"
    ENABLE_CORS = True
    CORS_ORIGINS = [
        "http://localhost:4200",
        "http://localhost:3000",
    ]
    
    # Health Check Settings
    HEALTH_CHECK_INTERVAL = 60  # seconds
    HEALTH_CHECK_TIMEOUT = 10
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get shared configuration as dictionary"""
        return {
            "database": {
                "connect_timeout": SharedConfig.DATABASE_CONNECT_TIMEOUT,
                "query_timeout": SharedConfig.DATABASE_QUERY_TIMEOUT,
                "pool_size": SharedConfig.DATABASE_POOL_SIZE,
                "pool_max_overflow": SharedConfig.DATABASE_POOL_MAX_OVERFLOW,
            },
            "security": {
                "password_min_length": SharedConfig.PASSWORD_MIN_LENGTH,
                "password_require_special_chars": SharedConfig.PASSWORD_REQUIRE_SPECIAL_CHARS,
                "session_timeout_minutes": SharedConfig.SESSION_TIMEOUT_MINUTES,
                "jwt_algorithm": SharedConfig.JWT_ALGORITHM,
                "jwt_expiry_hours": SharedConfig.JWT_EXPIRY_HOURS,
            },
            "logging": {
                "level": SharedConfig.LOG_LEVEL,
                "format": SharedConfig.LOG_FORMAT,
                "request_logging": SharedConfig.ENABLE_REQUEST_LOGGING,
                "performance_logging": SharedConfig.ENABLE_PERFORMANCE_LOGGING,
            },
            "api": {
                "title": SharedConfig.API_TITLE,
                "description": SharedConfig.API_DESCRIPTION,
                "version": SharedConfig.API_VERSION,
                "cors_enabled": SharedConfig.ENABLE_CORS,
                "cors_origins": SharedConfig.CORS_ORIGINS,
            }
        }


# ============================================================================
# APPLICATION CONFIGURATION MANAGER
# ============================================================================

class AppConfigManager:
    """Central configuration manager for all apps"""
    
    @staticmethod
    def get_app_config(app_type: AppType) -> Dict[str, Any]:
        """
        Get configuration for specific app type
        
        Args:
            app_type: Type of app (farmgrow, farmscore, farmsuite)
            
        Returns:
            Configuration dictionary
        """
        app_type = AppType(app_type) if isinstance(app_type, str) else app_type
        
        configs = {
            AppType.FARMGROW: FarmGrowConfig.get_config(),
            AppType.FARMSCORE: FarmScoreConfig.get_config(),
            AppType.FARMSUITE: FarmSuiteConfig.get_config(),
        }
        
        # Add shared config to each app's config
        config = configs.get(app_type, {})
        config["shared"] = SharedConfig.get_config()
        
        logger.info(f"Loaded configuration for {app_type.value}")
        return config
    
    @staticmethod
    def get_all_configs() -> Dict[str, Dict[str, Any]]:
        """Get configuration for all apps"""
        return {
            AppType.FARMGROW.value: AppConfigManager.get_app_config(AppType.FARMGROW),
            AppType.FARMSCORE.value: AppConfigManager.get_app_config(AppType.FARMSCORE),
            AppType.FARMSUITE.value: AppConfigManager.get_app_config(AppType.FARMSUITE),
        }
    
    @staticmethod
    def get_shared_config() -> Dict[str, Any]:
        """Get shared configuration only"""
        return SharedConfig.get_config()
    
    @staticmethod
    def validate_app_type(app_type: str) -> bool:
        """Validate if app type is supported"""
        try:
            AppType(app_type)
            return True
        except ValueError:
            logger.error(f"Invalid app type: {app_type}")
            return False
    
    @staticmethod
    def get_rate_limit(app_type: AppType, endpoint: str) -> Optional[int]:
        """
        Get rate limit for specific app endpoint
        
        Args:
            app_type: Type of app
            endpoint: Endpoint name
            
        Returns:
            Rate limit (requests per minute) or None
        """
        app_type = AppType(app_type) if isinstance(app_type, str) else app_type
        config = AppConfigManager.get_app_config(app_type)
        
        rate_limits = config.get("rate_limits", {})
        return rate_limits.get(endpoint)
    
    @staticmethod
    def get_cache_ttl(app_type: AppType, cache_key: str) -> Optional[int]:
        """
        Get cache TTL for specific cache key
        
        Args:
            app_type: Type of app
            cache_key: Cache key name
            
        Returns:
            TTL in seconds or None
        """
        app_type = AppType(app_type) if isinstance(app_type, str) else app_type
        config = AppConfigManager.get_app_config(app_type)
        
        caching = config.get("caching", {})
        return caching.get(cache_key)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_farmgrow_config() -> Dict[str, Any]:
    """Get FarmGrow configuration"""
    return AppConfigManager.get_app_config(AppType.FARMGROW)


def get_farmscore_config() -> Dict[str, Any]:
    """Get FarmScore configuration"""
    return AppConfigManager.get_app_config(AppType.FARMSCORE)


def get_farmsuite_config() -> Dict[str, Any]:
    """Get FarmSuite configuration"""
    return AppConfigManager.get_app_config(AppType.FARMSUITE)


def get_shared_config() -> Dict[str, Any]:
    """Get shared configuration"""
    return AppConfigManager.get_shared_config()
