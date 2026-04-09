"""
FarmIQ Backend - FastAPI Application with Proper RAG Initialization
Multi-channel AI Powered Agricultural Intelligence Platform

Authentication Model:
- Uses FarmIQ ID (e.g., FQ7K9M2X) from Angular frontend
- No JWT required - identification via FarmIQ ID
- FarmIQ ID passed in X-FarmIQ-ID header
- User context automatically resolved from database via FarmIQ ID
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, ConfigDict
import os
import logging
import uvicorn
import asyncio

# Response Models for OpenAPI documentation
class HealthResponse(BaseModel):
    """Health check response model"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "timestamp": "2026-04-02T16:26:00.000000Z",
            "components": {
                "ollama": "ready",
                "embeddings": "ready",
                "llm": "ready",
                "ocr": "ready",
                "retrieval": "ready",
                "reasoning": "ready",
                "storage": "ready",
                "conversation": "ready"
            },
            "errors": None,
            "message": "All systems operational"
        }
    })
    
    status: str = Field(..., description="Overall system status: 'healthy' or 'degraded'")
    timestamp: str = Field(..., description="ISO format timestamp of health check")
    components: Dict[str, str] = Field(..., description="Status of individual components")
    errors: Optional[Dict] = Field(None, description="Any errors encountered")
    message: str = Field(..., description="Human-readable status message")

class RootResponse(BaseModel):
    """Root endpoint response model"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "app": "FarmIQ",
            "version": "1.0.0",
            "description": "AI-Powered Agricultural Intelligence Platform",
            "documentation": "/api/redoc",
            "endpoints": {
                "health": "/health",
                "redoc": "/api/redoc"
            }
        }
    })
    
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="Application description")
    documentation: str = Field(..., description="Link to OpenAPI documentation")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")

class StatusResponse(BaseModel):
    """Status response model"""
    initialized: bool = Field(..., description="Whether services are initialized")
    errors: Dict = Field(..., description="Any initialization errors")

class ProbeResponse(BaseModel):
    """Kubernetes probe response model"""
    ready: Optional[bool] = Field(None, description="Readiness status")
    alive: Optional[bool] = Field(None, description="Liveness status")
    timestamp: str = Field(..., description="ISO format timestamp")

# Security modules (Phase 5 - Consolidated Core)
from core.security import (
    FarmIQException,
    security_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
    build_error_response,
)
from core.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    AuditLoggingMiddleware,
    GlobalRateLimitMiddleware,
)

# Logging configuration (Phase 5 - Consolidated Core)
from core.logging_config import (
    configure_logging,
    app_logger,
    route_logger,
    security_logger,
)

# Configure logging at startup (must be before logger usage)
configure_logging(level=os.getenv('LOG_LEVEL', 'INFO'), json_format=True)

# Get logger for service initialization
logger = logging.getLogger(__name__)

# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

class ServiceInitializer:
    """Handle safe initialization of all RAG services"""
    
    _initialized = False
    _services: Dict = {}
    _errors: Dict = {}
    
    @classmethod
    async def initialize_all(cls):
        """Initialize all RAG services in correct order"""
        if cls._initialized:
            return True
        
        try:
            # 1. Initialize Ollama (foundation)
            await cls._init_ollama()
            
            # 2. Initialize Storage
            await cls._init_storage()
            
            # 3. Initialize Core Services
            await cls._init_embedding_service()
            await cls._init_llm_service()
            await cls._init_ocr_service()
            
            # 4. Initialize RAG Pipeline
            await cls._init_retrieval_service()
            await cls._init_reasoning_service()
            await cls._init_document_ingestion()
            
            # 5. Initialize Conversation Management
            await cls._init_conversation_manager()
            
            cls._initialized = True
            logger.info("✅ All RAG services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            cls._errors['startup'] = str(e)
            # Continue with degraded mode
            return False
    
    @classmethod
    async def _init_ollama(cls):
        """Initialize Ollama service"""
        try:
            from core.ollama_service import get_ollama_service
            ollama = get_ollama_service()
            
            if ollama.is_ready():
                logger.info("✅ Ollama service connected")
                cls._services['ollama'] = ollama
            else:
                logger.warning("⚠️  Ollama not responding - will use CPU fallback models")
                cls._services['ollama'] = ollama
                cls._errors['ollama'] = 'Not responding'
                
        except Exception as e:
            logger.error(f"⚠️  Ollama initialization failed: {e}")
            cls._errors['ollama'] = str(e)
    
    @classmethod
    async def _init_storage(cls):
        """Initialize local embedding storage"""
        try:
            from app.farmgrow.services.embedding_store import LocalEmbeddingStore
            store = LocalEmbeddingStore()
            stats = store.get_statistics()
            logger.info(f"✅ Local storage initialized: {stats['total_chunks']} embeddings")
            cls._services['storage'] = store
            
        except Exception as e:
            logger.error(f"❌ Storage initialization failed: {e}")
            cls._errors['storage'] = str(e)
    
    @classmethod
    async def _init_embedding_service(cls):
        """Initialize embedding service"""
        try:
            from app.farmgrow.services.embeddings import EmbeddingService
            service = EmbeddingService()
            logger.info("✅ Embedding service initialized")
            cls._services['embedding'] = service
            
        except Exception as e:
            logger.error(f"⚠️  Embedding service failed: {e}")
            cls._errors['embedding'] = str(e)
    
    @classmethod
    async def _init_llm_service(cls):
        """Initialize LLM service"""
        try:
            from app.farmgrow.services.llm import OllamaLLMService
            service = OllamaLLMService(model_name="mistral:7b-instruct")
            logger.info("✅ LLM service initialized")
            
            # Verify the model being used
            logger.info(f"🔍 LLM Service Verification:")
            logger.info(f"   Model: {service.model_name}")
            logger.info(f"   Using Ollama Service: {service.ollama_service is not None}")
            logger.info(f"   Temperature: {service.temperature}")
            logger.info(f"   Max tokens: {service.max_tokens}")
            
            # Warn if still using slow model
            if 'llama3.1:8b' in service.model_name:
                logger.warning(f"⚠️  WARNING: Still using llama3.1:8b (slow model)")
                logger.warning(f"   Expected: mistral:7b (fast model)")
                logger.warning(f"   Response time will be 250-300 seconds")
            elif 'mistral' in service.model_name and '7b' in service.model_name:
                logger.info(f"✅ CORRECT: Using mistral:7b (optimized for speed)")
                logger.info(f"   Expected response time: 5-10 seconds")
            
            cls._services['llm'] = service
            
        except Exception as e:
            logger.error(f"⚠️  LLM service failed: {e}")
            cls._errors['llm'] = str(e)
    
    @classmethod
    async def _init_ocr_service(cls):
        """Initialize OCR service"""
        try:
            from app.farmgrow.services.ocr import OCRService
            service = OCRService()
            logger.info("✅ OCR service initialized")
            cls._services['ocr'] = service
            
        except Exception as e:
            logger.error(f"⚠️  OCR service failed: {e}")
            cls._errors['ocr'] = str(e)
    
    @classmethod
    async def _init_retrieval_service(cls):
        """Initialize retrieval service"""
        try:
            from app.farmgrow.services.retrieval import RAGRetriever
            from app.farmgrow.services.ingestion import DocumentIngestionService
            
            doc_service = DocumentIngestionService()
            emb_service = cls._services.get('embedding')
            
            service = RAGRetriever(emb_service, doc_service)
            logger.info("✅ Retrieval service initialized")
            cls._services['retrieval'] = service
            
        except Exception as e:
            logger.error(f"⚠️  Retrieval service failed: {e}")
            cls._errors['retrieval'] = str(e)
    
    @classmethod
    async def _init_reasoning_service(cls):
        """Initialize reasoning service"""
        try:
            from app.farmgrow.services.llm import OllamaLLMService
            # Reasoning logic is now integrated into OllamaLLMService
            service = cls._services.get('llm')
            logger.info("✅ Reasoning service initialized")
            cls._services['reasoning'] = service
            
        except Exception as e:
            logger.error(f"⚠️  Reasoning service failed: {e}")
            cls._errors['reasoning'] = str(e)
    
    @classmethod
    async def _init_document_ingestion(cls):
        """Initialize document ingestion"""
        try:
            from app.farmgrow.services.ingestion import DocumentIngestionService
            
            service = DocumentIngestionService(
                embedding_service=cls._services.get('embedding')
            )
            logger.info("✅ Document ingestion service initialized")
            cls._services['doc_ingestion'] = service
            
        except Exception as e:
            logger.error(f"⚠️  Document ingestion failed: {e}")
            cls._errors['doc_ingestion'] = str(e)
    
    @classmethod
    async def _init_conversation_manager(cls):
        """Initialize conversation manager"""
        try:
            from app.farmgrow.services.conversations import ConversationService
            from core.database import get_supabase_client
            supabase_client = get_supabase_client()
            
            service = ConversationService(supabase_client=supabase_client)
            logger.info("✅ Conversation manager initialized")
            cls._services['conversation'] = service
            
        except Exception as e:
            logger.error(f"⚠️  Conversation manager failed: {e}")
            cls._errors['conversation'] = str(e)
    
    @classmethod
    def get_service(cls, service_name: str):
        """Get an initialized service"""
        return cls._services.get(service_name)
    
    @classmethod
    def get_health_status(cls) -> Dict:
        """Get health status of all services"""
        return {
            'initialized': cls._initialized,
            'services': list(cls._services.keys()),
            'errors': cls._errors,
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

def get_cors_origins():
    """Get CORS origins from environment or use defaults"""
    env = os.getenv('ENVIRONMENT', 'development')
    
    origins = {
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
    
    cors_list = origins.get(env, origins['development'])
    
    # Allow custom origins via env variable
    custom_origin = os.getenv('CORS_ORIGINS')
    if custom_origin:
        cors_list.extend([origin.strip() for origin in custom_origin.split(',')])
    
    return cors_list


# ============================================================================
# FASTAPI LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("\n" + "="*60)
    print(">> FarmIQ Backend Starting")
    print("="*60)
    
    env = os.getenv('ENVIRONMENT', 'development')
    print(f"Environment: {env}")
    print(f"CORS Origins: {get_cors_origins()}")
    
    # Phase 3: Initialize Database Connection Pool (Performance Optimization)
    try:
        from core.db_pool import DatabasePool
        await DatabasePool.initialize()
        print("[OK] Database connection pool initialized (Phase 3)")
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize database pool: {e}")
        logger.info("Continuing without connection pooling...")
    
    # Initialize services
    success = await ServiceInitializer.initialize_all()
    
    if success:
        print("\n[OK] FarmIQ Backend Ready")
    else:
        print("\n[WARNING] FarmIQ Backend Started with Warnings (see logs above)")
    
    print("="*60 + "\n")
    
    yield
    
    # SHUTDOWN
    print("\n" + "="*60)
    print(">> FarmIQ Backend Shutting Down")
    print("="*60)
    
    # Phase 3: Close Database Connection Pool
    try:
        from core.db_pool import DatabasePool
        await DatabasePool.close()
        print("[OK] Database connection pool closed")
    except Exception as e:
        logger.warning(f"Warning closing database pool: {e}")
    
    print("="*60 + "\n")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="FarmIQ API",
    description="AI-Powered Agricultural Intelligence Platform with Local RAG",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disabled - using custom route instead
    redoc_url=None,  # Disabled - using custom route instead
    openapi_url="/api/openapi.json",  # OpenAPI specification
    openapi_tags=[
        {
            "name": "Core",
            "description": "Core API endpoints including health checks, status, and root information",
        },
        {
            "name": "Health",
            "description": "Health and readiness checks",
        },
        {
            "name": "FarmGrow",
            "description": "FarmGrow module endpoints",
        },
        {
            "name": "FarmGrow RAG",
            "description": "RAG-powered agricultural Q&A system with document processing and chat support",
        },
        {
            "name": "FarmScore Credit",
            "description": "Credit scoring and farm evaluation endpoints",
        },
        {
            "name": "Farm Intelligence",
            "description": "Comprehensive farm intelligence and analysis",
        },
        {
            "name": "Analytics",
            "description": "Farm analytics and metrics",
        },
        {
            "name": "Predictions",
            "description": "Farm predictions and forecasting",
        },
        {
            "name": "Production Intelligence",
            "description": "Production and yield intelligence",
        },
        {
            "name": "Market Intelligence",
            "description": "Market data and pricing intelligence",
        },
        {
            "name": "Risk Management",
            "description": "Risk assessment and management",
        },
        {
            "name": "Worker Management",
            "description": "Farm worker and labor management",
        },
        {
            "name": "Configuration",
            "description": "System configuration and settings",
        },
        {
            "name": "M-Pesa",
            "description": "M-Pesa payment integration",
        },
        {
            "name": "M-Pesa Payments",
            "description": "Payment processing and transaction management",
        },
        {
            "name": "Payments",
            "description": "Payment endpoints",
        },
        {
            "name": "AI Usage Tracking",
            "description": "AI token usage tracking and quotas",
        },
        {
            "name": "Documentation",
            "description": "API documentation and schema endpoints",
        },
    ]
)

# Add middleware in correct order (inside-out execution)
# 1. Request ID middleware (must be first to capture all requests)
app.add_middleware(RequestIDMiddleware)

# 2. Audit logging middleware (logs all requests)
app.add_middleware(AuditLoggingMiddleware)

# 3. Global rate limiting middleware (protects against DoS)
app.add_middleware(GlobalRateLimitMiddleware)

# 4. Security headers middleware (adds security headers to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# 5. CORS middleware (with restricted methods/headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Restricted from "*"
    allow_headers=["Content-Type", "X-FarmIQ-ID", "X-Request-ID", "Authorization"],  # Restricted from "*"
    max_age=600,
)

# ============================================================================
# REDOC DOCUMENTATION
# ============================================================================

@app.get("/api/redoc", include_in_schema=False)
async def get_redoc_documentation():
    """Custom ReDoc route"""
    return get_redoc_html(
        title="FarmIQ API - ReDoc",
        openapi_url="/api/openapi.json",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

# ============================================================================
# EXCEPTION HANDLERS (Phase 5.1 - Security Hardening)
# ============================================================================

# Handle FarmIQ-specific exceptions with secure error responses
@app.exception_handler(FarmIQException)
async def handle_farmiq_exception(request, exc):
    return await security_exception_handler(request, exc)


# Handle unexpected exceptions with generic error message (no information disclosure)
@app.exception_handler(Exception)
async def handle_generic_exception(request, exc):
    return await generic_exception_handler(request, exc)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=200,
    tags=["Core"],
    summary="Health Check",
    description="Returns detailed health status of all RAG pipeline components including Ollama, embeddings, LLM, OCR, retrieval, reasoning, storage, and conversation services.",
    responses={
        200: {"description": "Healthy or degraded status with component details"},
        503: {"description": "Service unavailable"}
    }
)
async def health_check() -> HealthResponse:
    """
    Complete health check endpoint
    
    Returns detailed status of all RAG pipeline components:
    - Ollama LLM connection
    - Embedding service
    - OCR service
    - Retrieval pipeline
    - Reasoning engine
    - Storage backend
    - Conversation management
    
    Returns:
        HealthResponse: Current status of all services
    """
    status = ServiceInitializer.get_health_status()
    
    # Detailed component status
    components = {
        'ollama': 'ready' if ServiceInitializer.get_service('ollama') else 'unavailable',
        'embeddings': 'ready' if ServiceInitializer.get_service('embedding') else 'unavailable',
        'llm': 'ready' if ServiceInitializer.get_service('llm') else 'unavailable',
        'ocr': 'ready' if ServiceInitializer.get_service('ocr') else 'unavailable',
        'retrieval': 'ready' if ServiceInitializer.get_service('retrieval') else 'unavailable',
        'reasoning': 'ready' if ServiceInitializer.get_service('reasoning') else 'unavailable',
        'storage': 'ready' if ServiceInitializer.get_service('storage') else 'unavailable',
        'conversation': 'ready' if ServiceInitializer.get_service('conversation') else 'unavailable',
    }
    
    overall_status = 'healthy' if status['initialized'] and not status['errors'] else 'degraded'
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        components=components,
        errors=status['errors'] if status['errors'] else None,
        message='All systems operational' if overall_status == 'healthy' else 'Running in degraded mode'
    )


@app.get(
    "/",
    response_model=RootResponse,
    status_code=200,
    tags=["Core"],
    summary="API Root",
    description="Returns API metadata and available endpoints information"
)
async def root() -> RootResponse:
    """
    Root endpoint with API info
    
    Returns:
        RootResponse: API information including version, description, documentation link, and available endpoints
    
    Example:
        GET / HTTP/1.1
        Host: localhost:8000
    """
    return RootResponse(
        app='FarmIQ',
        version='1.0.0',
        description='AI-Powered Agricultural Intelligence Platform',
        documentation='/api/redoc',
        endpoints={
            'health': '/health',
            'redoc': '/api/redoc',
            'redoc': '/api/redoc',
            'openapi': '/api/openapi.json',
            'rag_chatbot': '/api/v1/rag-chatbot',
            'agronomy': '/api/v1/agronomy',
            'farmgrow': '/api/v1/farmgrow',
            'farmscore': '/api/v1/farmscore',
            'farmsuite': '/api/v1/farmsuite',
            'mpesa': '/api/v1/mpesa'
        }
    )


@app.get(
    "/status",
    status_code=200,
    tags=["Core"],
    summary="System Status",
    description="Get detailed system status including initialization state and any errors"
)
async def get_status() -> Dict:
    """
    Get detailed system status
    
    Returns:
        Dict: System initialization status and error details
    """
    return ServiceInitializer.get_health_status()


@app.get(
    "/readiness",
    status_code=200,
    tags=["Core"],
    summary="Readiness Probe",
    description="Kubernetes readiness probe - returns 200 if ready to accept traffic, 503 if not ready"
)
async def readiness_check() -> ProbeResponse:
    """
    Kubernetes readiness probe
    
    Returns 200 if ready to accept traffic, 503 if not ready
    
    Returns:
        ProbeResponse: Readiness status and timestamp
    """
    status = ServiceInitializer.get_health_status()
    
    if status['initialized'] and not status['errors']:
        return ProbeResponse(
            ready=True,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )
    else:
        return ProbeResponse(
            ready=False,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )


@app.get(
    "/liveness",
    status_code=200,
    tags=["Core"],
    summary="Liveness Probe",
    description="Kubernetes liveness probe - returns 200 if app is alive and should not be restarted"
)
async def liveness_check() -> ProbeResponse:
    """
    Kubernetes liveness probe
    
    Returns 200 if app is alive, 503 if it should be restarted
    
    Returns:
        ProbeResponse: Liveness status and timestamp
    """
    return ProbeResponse(
        alive=True,
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )


# ============================================================================
# DEPENDENCY INJECTION FUNCTIONS
# ============================================================================

async def get_rag_orchestrator():
    """Get RAG orchestrator service"""
    from app.farmgrow.services.orchestrator import RAGOrchestrator
    
    ingestion = ServiceInitializer.get_service('doc_ingestion')
    embedding = ServiceInitializer.get_service('embedding')
    storage = ServiceInitializer.get_service('storage')
    retrieval = ServiceInitializer.get_service('retrieval')
    ranking = None  # Optional for now
    llm = ServiceInitializer.get_service('llm')
    conversation = ServiceInitializer.get_service('conversation')
    
    if not all([ingestion, embedding, storage, retrieval, llm, conversation]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG services not fully initialized"
        )
    
    return RAGOrchestrator(
        ingestion_service=ingestion,
        embedding_service=embedding,
        embedding_store=storage,
        retrieval_service=retrieval,
        ranking_service=ranking,
        llm_service=llm,
        conversation_service=conversation
    )


async def get_embedding_service():
    """Get embedding service"""
    service = ServiceInitializer.get_service('embedding')
    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not initialized"
        )
    return service


async def get_llm_service():
    """Get LLM service"""
    service = ServiceInitializer.get_service('llm')
    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service not initialized"
        )
    return service


async def get_conversation_service():
    """Get conversation service"""
    service = ServiceInitializer.get_service('conversation')
    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation service not initialized"
        )
    return service


# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# Include all routes
# Import routers directly from app subpackages
# (No need for wrapper files at routes/ - direct imports are cleaner)
from app.farmgrow.routes import router as farmgrow_router
from app.farmscore.routes import router as farmscore_router
from app.farmsuite.routes import router as farmsuite_router
from app.shared.routes.mpesa_routes import router as mpesa_router
from app.ai_usage.routes import router as ai_usage_router

app.include_router(farmgrow_router)
app.include_router(farmscore_router)
app.include_router(farmsuite_router)
app.include_router(mpesa_router)
app.include_router(ai_usage_router)


# ============================================================================
# STARTUP VERIFICATION
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Verify services are ready"""
    status = ServiceInitializer.get_health_status()
    if status['errors']:
        logger.warning(f"Startup warnings: {status['errors']}")


# ============================================================================
# ERROR HANDLERS - ALREADY REGISTERED IN SECURITY MODULE
# ============================================================================

# Exception handlers are already registered in core.security
# No additional handlers needed here to avoid conflicts


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=os.getenv('ENVIRONMENT', 'development') == 'development'
    )
