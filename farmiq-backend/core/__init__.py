"""
FarmIQ Core Infrastructure Module (Phase 5 - Consolidated & Unified)
Provides complete shared infrastructure for FarmGrow RAG, FarmScore ML, and FarmSuite Intelligence

Core Modules (17 total):

1. APP CONFIGURATION
   - app_config: Multi-app configuration (FarmGrow, FarmScore, FarmSuite)

2. SECURITY & VALIDATION
   - security: Input validation (SQL injection, XSS, file upload), exception handling, error responses
   - validation: Pydantic validators, domain-specific validation (farms, products, markets, predictions)
   - middleware: FastAPI middleware (request IDs, security headers, rate limiting, audit logging)

3. CACHING & PERFORMANCE  
   - caching: In-memory LRU cache with TTL, decorators (@cache, @async_cache), invalidation, monitoring
   - logging_config: Structured JSON logging, audit trails, performance timing

4. DATA & ML
   - database: Supabase client, repository pattern, connection pooling
   - schemas: Pydantic models, shared data structures
   - ml_theory: ML model base classes (Classification, Regression, RAG), model registry
   - ollama_service: Unified Ollama LLM service interface

5. OBSERVABILITY & MONITORING
   - grafana_dashboards: 5 Grafana dashboards (FarmGrow RAG, FarmScore ML, FarmSuite, System Overview, Security)
   - metrics: Prometheus metrics, counters, histograms
   - load_testing: Load testing utilities

6. AI INTELLIGENCE HUB
   - cortex: Central tracking for FarmGrow, FarmScore, FarmSuite (request tracking, cost, analytics, correlations)

7. CONNECTION POOLING
   - db_pool: Connection pool management for Supabase PostgreSQL
   - performance: Database optimization (pooling, profiling, batch operations)

8. EMBEDDINGS & UTILITIES
   - embedding_cache: Embeddings caching and retrieval
"""

# ============================================================================
# CONFIGURATION & APP SETUP
# ============================================================================

from core.app_config import (
    AppType,
    FarmGrowConfig,
    FarmScoreConfig,
    FarmSuiteConfig,
    SharedConfig,
    AppConfigManager,
    get_farmgrow_config,
    get_farmscore_config,
    get_farmsuite_config,
    get_shared_config,
)

# ============================================================================
# SECURITY & VALIDATION
# ============================================================================

# Security: Input validation, injection prevention, exception handling
from core.security import (
    # Phase 3: Input Validators
    SQLInjectionValidator,
    XSSProtector,
    RateLimiter,
    InputValidator,
    FileSecurityValidator,
    CORSSecurityConfig,
    # Phase 5: Exception Handling & Error Responses
    ErrorDetail,
    ErrorResponse,
    FarmIQException,
    ValidationError as FarmIQValidationError,
    ResourceNotFoundError,
    UnauthorizedError,
    RateLimitError,
    ServiceUnavailableError,
    build_error_response,
)

# Validation: Pydantic validators & domain-specific rules
from core.validation import (
    # Constants
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    # Sanitization Functions
    sanitize_html,
    sanitize_input,
    # Validation Functions
    validate_string_length,
    validate_positive_number,
    validate_percentage,
    validate_location_format,
    validate_uuid,
    # RAG Query Validators
    validate_query,
    # Credit Scoring Validators
    validate_credit_input,
    # File Upload Validators
    validate_file_upload,
    # Market/Symbol Validators
    validate_symbol,
    # Timeframe Validators
    validate_timeframe,
    # Credit Loan Validators
    validate_loan_params,
    # General Utility Validators
    validate_not_none,
    validate_not_empty,
    validate_range,
    validate_positive,
    validate_non_negative,
    validate_email,
    validate_uuid,
    validate_list_not_empty,
    validate_list_length,
    validate_currency,
    normalize_whitespace,
    normalize_phone,
    # Pydantic Fields
    SafeStringField,
    # Base Models
    ValidatedNameModel,
    ValidatedDescriptionModel,
    ValidatedLocationModel,
    # Domain Validators
    FarmValidators,
    ProductionValidators,
    MarketValidators,
    PredictionValidators,
    ValidationContext,
)

# Middleware: FastAPI middleware stack
from core.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    AuditLoggingMiddleware,
    GlobalRateLimitMiddleware,
    check_rate_limit,
    rate_limit_by_farm,
    rate_limit_by_user,
)

# ============================================================================
# CACHING & PERFORMANCE
# ============================================================================

from core.caching import (
    CacheEntry,
    InMemoryCache,
    generate_cache_key,
    cache,
    async_cache,
    CacheInvalidator,
    CacheMonitor,
    ResponseCache,
    CacheWarmer,
)

from core.logging_config import (
    JSONFormatter,
    configure_logging,
    StructuredLogger,
    app_logger,
    auth_logger,
    route_logger,
    service_logger,
    database_logger,
    ml_logger,
    security_logger,
    log_authentication,
    log_authorization,
    log_api_call,
    log_database_operation,
    log_ml_prediction,
    PerformanceTimer,
)

# ============================================================================
# DATA & ML
# ============================================================================

from core.database import (
    SupabaseClientFactory,
    DatabaseRepository,
    get_supabase_client,
    get_database_repository,
)

from core.schemas import *

from core.ml_theory import (
    MLModel,
    ClassificationModel,
    RegressionModel,
    RAGModel,
    ModelRegistry,
)

from core.ollama_service import (
    OllamaService,
    get_ollama_service,
)

# ============================================================================
# OBSERVABILITY & MONITORING
# ============================================================================

from core.grafana_dashboards import (
    PanelType,
    DashboardRefresh,
    ThresholdMode,
    PrometheusTarget,
    Threshold,
    GrafanaPanel,
    GrafanaDashboard,
    DashboardPanelFactory,
    create_farmgrow_dashboard,
    create_farmscore_dashboard,
    create_farmsuite_dashboard,
    create_system_overview_dashboard,
    create_security_dashboard,
    DASHBOARDS,
    get_dashboard,
    list_dashboards,
    export_all_dashboards,
)

from core.metrics import *

from core.load_testing import *

# ============================================================================
# EMBEDDINGS & UTILITIES
# ============================================================================

from core.embedding_cache import *

# ============================================================================
# AI INTELLIGENCE HUB
# ============================================================================

from core.cortex import (
    AISystem,
    RequestType,
    RequestStatus,
    AIToken,
    AIMetrics,
    AIRequest,
    Cortex,
    track_ai_request,
)

# Cortex Helpers: Easy integration decorators and context managers
from core.cortex_helpers import (
    track_ai_request_endpoint,
    cortex_track,
    get_system_analytics,
    get_cross_system_analytics,
    get_user_activity_analytics,
    get_farm_activity_analytics,
    correlate_requests,
)

# Connection Pooling (Phase 3 & 5.2)
from core.db_pool import (
    DatabasePool,
    get_db_pool,
)

from core.performance import (
    DatabasePoolConfig,
    SimpleQueryProfiler,
    LazyLoadHelper,
    BatchOperations,
    PaginationHelper,
    transaction_scope,
    PoolMonitor,
    DatabaseStats,
)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # ========== Configuration ==========
    "AppType",
    "FarmGrowConfig",
    "FarmScoreConfig",
    "FarmSuiteConfig",
    "SharedConfig",
    "AppConfigManager",
    "get_farmgrow_config",
    "get_farmscore_config",
    "get_farmsuite_config",
    "get_shared_config",
    
    # ========== Security & Validation ==========
    # Input Validators
    "SQLInjectionValidator",
    "XSSProtector",
    "RateLimiter",
    "InputValidator",
    "FileSecurityValidator",
    "CORSSecurityConfig",
    # Exception Handling
    "ErrorDetail",
    "ErrorResponse",
    "FarmIQException",
    "FarmIQValidationError",
    "ResourceNotFoundError",
    "UnauthorizedError",
    "RateLimitError",
    "ServiceUnavailableError",
    "build_error_response",
    # Validation
    "MAX_NAME_LENGTH",
    "MAX_DESCRIPTION_LENGTH",
    "sanitize_html",
    "sanitize_input",
    "validate_string_length",
    "validate_positive_number",
    "validate_percentage",
    "validate_location_format",
    "validate_uuid",
    "validate_query",
    "validate_credit_input",
    "validate_file_upload",
    "validate_symbol",
    "SafeStringField",
    "ValidatedNameModel",
    "ValidatedDescriptionModel",
    "ValidatedLocationModel",
    "FarmValidators",
    "ProductionValidators",
    "MarketValidators",
    "PredictionValidators",
    "ValidationContext",
    # Middleware
    "RequestIDMiddleware",
    "SecurityHeadersMiddleware",
    "AuditLoggingMiddleware",
    "GlobalRateLimitMiddleware",
    "check_rate_limit",
    "rate_limit_by_farm",
    "rate_limit_by_user",
    
    # ========== Caching & Performance ==========
    "CacheEntry",
    "InMemoryCache",
    "generate_cache_key",
    "cache",
    "async_cache",
    "CacheInvalidator",
    "CacheMonitor",
    "ResponseCache",
    "CacheWarmer",
    # Logging
    "JSONFormatter",
    "configure_logging",
    "StructuredLogger",
    "app_logger",
    "auth_logger",
    "route_logger",
    "service_logger",
    "database_logger",
    "ml_logger",
    "security_logger",
    "log_authentication",
    "log_authorization",
    "log_api_call",
    "log_database_operation",
    "log_ml_prediction",
    "PerformanceTimer",
    
    # ========== Data & ML ==========
    "SupabaseClientFactory",
    "DatabaseRepository",
    "get_supabase_client",
    "get_database_repository",
    "MLModel",
    "ClassificationModel",
    "RegressionModel",
    "RAGModel",
    "ModelRegistry",
    "OllamaService",
    "get_ollama_service",
    
    # ========== Observability & Monitoring ==========
    "PanelType",
    "DashboardRefresh",
    "ThresholdMode",
    "PrometheusTarget",
    "Threshold",
    "GrafanaPanel",
    "GrafanaDashboard",
    "DashboardPanelFactory",
    "create_farmgrow_dashboard",
    "create_farmscore_dashboard",
    "create_farmsuite_dashboard",
    "create_system_overview_dashboard",
    "create_security_dashboard",
    "DASHBOARDS",
    "get_dashboard",
    "list_dashboards",
    "export_all_dashboards",
    
    # ========== AI Intelligence Hub (Cortex) ==========
    "AISystem",
    "RequestType",
    "RequestStatus",
    "AIToken",
    "AIMetrics",
    "AIRequest",
    "Cortex",
    "track_ai_request",
    
    # ========== Cortex Helpers (Integration Helpers) ==========
    "track_ai_request_endpoint",
    "cortex_track",
    "get_system_analytics",
    "get_cross_system_analytics",
    "get_user_activity_analytics",
    "get_farm_activity_analytics",
    "correlate_requests",
    
    # ========== Connection Pooling ==========
    "DatabasePool",
    "get_db_pool",
    "DatabasePoolConfig",
    "SimpleQueryProfiler",
    "LazyLoadHelper",
    "BatchOperations",
    "PaginationHelper",
    "transaction_scope",
    "PoolMonitor",
    "DatabaseStats",
]
