"""
FastAPI Dependencies for FarmIQ Authentication & Service Injection
Provides:
- FarmIQ ID validation and user context extraction
- Repository dependency injection for data access
- Service dependency injection for RAG, credit scoring, and intelligence services
"""
from fastapi import Depends, Header, HTTPException, status
from typing import Optional, Dict
from uuid import UUID
from auth.farmiq_id import FarmiqIdValidator
from core.supabase_client import supabase_client
from core.database import DatabaseRepository, get_database_repository
from app.farmsuite.application.repositories import (
    FarmRepository,
    ProductionRepository,
    PredictionRepository,
    RiskRepository,
    MarketRepository,
    WorkerRepository,
)
from app.farmsuite.application.services.farm_intelligence_service import FarmIntelligenceService
from app.farmsuite.application.services.prediction_service import PredictionService
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_farmiq_id_from_header(x_farmiq_id: Optional[str] = Header(None)) -> str:
    """
    Extract FarmIQ ID from request header (X-FarmIQ-ID)
    
    Args:
        x_farmiq_id: FarmIQ ID passed in X-FarmIQ-ID header
        
    Returns:
        Validated FarmIQ ID
        
    Raises:
        HTTPException: If FarmIQ ID is missing or invalid
    """
    if not x_farmiq_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing FarmIQ ID. Please provide X-FarmIQ-ID header."
        )
    
    if not FarmiqIdValidator.is_valid_format(x_farmiq_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FarmIQ ID format. Expected format: FQ####"
        )
    
    return x_farmiq_id.upper()


async def get_user_by_farmiq_id(farmiq_id: str = Depends(get_farmiq_id_from_header)) -> Dict:
    """
    Retrieve user profile from Supabase using FarmIQ ID
    
    Args:
        farmiq_id: Validated FarmIQ ID
        
    Returns:
        User profile dictionary containing user info
        
    Raises:
        HTTPException: If user not found or database error
    """
    try:
        client = supabase_client.client
        if not client:
            logger.error(f"Supabase client not initialized for FarmIQ ID: {farmiq_id}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable - Supabase client initialization failed"
            )
        
        # Query user_profiles by farmiq_id
        response = supabase_client.client.table('user_profiles').select(
            'id, farmiq_id, email, full_name, primary_role, created_at'
        ).eq('farmiq_id', farmiq_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for FarmIQ ID: {farmiq_id}"
            )
        
        user = response.data[0]
        logger.info(f"User authenticated with FarmIQ ID: {farmiq_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


async def get_user_context(user: Dict = Depends(get_user_by_farmiq_id)) -> Dict:
    """
    Get complete user context for request processing
    
    Args:
        user: User profile from get_user_by_farmiq_id
        
    Returns:
        Complete user context dictionary
    """
    try:
        user_id = user.get('id')
        
        # Get user roles
        roles_response = supabase_client.client.table('user_roles').select(
            'role, is_active'
        ).eq('user_id', user_id).eq('is_active', True).execute()
        
        roles = [r['role'] for r in roles_response.data] if roles_response.data else []
        
        return {
            "user_id": user_id,
            "farmiq_id": user.get('farmiq_id'),
            "email": user.get('email'),
            "full_name": user.get('full_name'),
            "primary_role": user.get('primary_role'),
            "roles": roles,
            "created_at": user.get('created_at')
        }
        
    except Exception as e:
        logger.error(f"Error building user context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build user context"
        )


# ============================================================================
# DATABASE CONNECTION & REPOSITORY DEPENDENCIES
# ============================================================================

async def get_database_connection() -> DatabaseRepository:
    """
    Get DatabaseRepository instance for FarmSuite database operations
    
    Returns:
        DatabaseRepository instance with async methods for data access
        
    Raises:
        HTTPException: If database repository cannot be initialized
    """
    try:
        db = await get_database_repository()
        if not db:
            logger.error("Failed to initialize DatabaseRepository")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        return db
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting database connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable"
        )


async def get_farm_repository(db=Depends(get_database_connection)) -> FarmRepository:
    """
    Dependency: FarmRepository for farm entity access
    
    Args:
        db: Database connection
        
    Returns:
        FarmRepository instance configured with database connection
    """
    try:
        return FarmRepository(db)
    except Exception as e:
        logger.error(f"Error initializing FarmRepository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize farm repository"
        )


async def get_production_repository(db=Depends(get_database_connection)) -> ProductionRepository:
    """
    Dependency: ProductionRepository for production data access
    
    Args:
        db: Database connection
        
    Returns:
        ProductionRepository instance
    """
    try:
        return ProductionRepository(db)
    except Exception as e:
        logger.error(f"Error initializing ProductionRepository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize production repository"
        )


async def get_prediction_repository(db=Depends(get_database_connection)) -> PredictionRepository:
    """
    Dependency: PredictionRepository for prediction storage and retrieval
    
    Args:
        db: Database connection
        
    Returns:
        PredictionRepository instance
    """
    try:
        return PredictionRepository(db)
    except Exception as e:
        logger.error(f"Error initializing PredictionRepository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize prediction repository"
        )


async def get_risk_repository(db=Depends(get_database_connection)) -> RiskRepository:
    """
    Dependency: RiskRepository for risk assessment data
    
    Args:
        db: Database connection
        
    Returns:
        RiskRepository instance
    """
    try:
        return RiskRepository(db)
    except Exception as e:
        logger.error(f"Error initializing RiskRepository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize risk repository"
        )


async def get_market_repository(db=Depends(get_database_connection)) -> MarketRepository:
    """
    Dependency: MarketRepository for market intelligence data
    
    Args:
        db: Database connection
        
    Returns:
        MarketRepository instance
    """
    try:
        return MarketRepository(db)
    except Exception as e:
        logger.error(f"Error initializing MarketRepository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize market repository"
        )


async def get_worker_repository(db=Depends(get_database_connection)) -> WorkerRepository:
    """
    Dependency: WorkerRepository for worker management
    
    Args:
        db: Database connection
        
    Returns:
        WorkerRepository instance
    """
    try:
        return WorkerRepository(db)
    except Exception as e:
        logger.error(f"Error initializing WorkerRepository: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize worker repository"
        )


async def get_farm_intelligence_service(
    farm_repo: FarmRepository = Depends(get_farm_repository),
    production_repo: ProductionRepository = Depends(get_production_repository),
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    market_repo: MarketRepository = Depends(get_market_repository),
    worker_repo: WorkerRepository = Depends(get_worker_repository),
) -> FarmIntelligenceService:
    """
    Dependency: FarmIntelligenceService with all sub-dependencies injected
    
    Main orchestration service for all farm intelligence operations.
    All repositories are injected as dependencies.
    
    Args:
        farm_repo: Farm repository
        production_repo: Production repository
        prediction_repo: Prediction repository
        risk_repo: Risk repository
        market_repo: Market repository
        worker_repo: Worker repository
        
    Returns:
        FarmIntelligenceService instance with all dependencies
    """
    try:
        # Initialize PredictionService with repositories
        prediction_service = PredictionService(
            farm_repository=farm_repo,
            production_repository=production_repo,
            prediction_repository=prediction_repo,
            risk_repository=risk_repo,
            market_repository=market_repo,
        )
        
        return FarmIntelligenceService(
            farm_repository=farm_repo,
            production_repository=production_repo,
            prediction_repository=prediction_repo,
            risk_repository=risk_repo,
            market_repository=market_repo,
            worker_repository=worker_repo,
            production_calculation_service=None,  # Stub for now
            risk_assessment_service=None,          # Stub for now
            prediction_service=prediction_service,  # Now properly initialized
        )
    except Exception as e:
        logger.error(f"Error initializing FarmIntelligenceService: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize farm intelligence service"
        )


# ============================================================================
# SERVICE INJECTION DEPENDENCIES
# ============================================================================

async def get_embedding_service():
    """Get initialized embedding service from ServiceInitializer"""
    try:
        # Import here to avoid circular imports
        from main import ServiceInitializer
        service = ServiceInitializer.get_service('embedding')
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding service not initialized"
            )
        return service
    except Exception as e:
        logger.error(f"Error accessing embedding service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to access embedding service"
        )


async def get_llm_service():
    """Get initialized LLM service from ServiceInitializer"""
    try:
        from main import ServiceInitializer
        service = ServiceInitializer.get_service('llm')
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service not initialized"
            )
        return service
    except Exception as e:
        logger.error(f"Error accessing LLM service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to access LLM service"
        )


async def get_conversation_service():
    """Get initialized conversation service from ServiceInitializer"""
    try:
        from main import ServiceInitializer
        service = ServiceInitializer.get_service('conversation')
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation service not initialized"
            )
        return service
    except Exception as e:
        logger.error(f"Error accessing conversation service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to access conversation service"
        )


async def get_retrieval_service():
    """Get initialized retrieval service from ServiceInitializer"""
    try:
        from main import ServiceInitializer
        service = ServiceInitializer.get_service('retrieval')
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Retrieval service not initialized"
            )
        return service
    except Exception as e:
        logger.error(f"Error accessing retrieval service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to access retrieval service"
        )


async def get_ingestion_service():
    """Get initialized ingestion service from ServiceInitializer"""
    try:
        from main import ServiceInitializer
        service = ServiceInitializer.get_service('doc_ingestion')
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ingestion service not initialized"
            )
        return service
    except Exception as e:
        logger.error(f"Error accessing ingestion service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to access ingestion service"
        )

# ============================================================================
# FARMGROW RAG SERVICE DEPENDENCIES
# ============================================================================

async def get_far_grow_embedding_service():
    """
    Dependency: FarmGrow specific embedding service (BAAI/bge-m3)
    
    Returns:
        EmbeddingService instance for document embedding
    """
    try:
        from app.farmgrow.services import EmbeddingService
        return EmbeddingService(model_name="BAAI/bge-m3", cache_embeddings=True)
    except Exception as e:
        logger.error(f"Error initializing FarmGrow embedding service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow embedding service"
        )


async def get_farmgrow_llm_service():
    """
    Dependency: FarmGrow LLM service (Ollama mistral:7b-instruct)
    
    Returns:
        OllamaLLMService instance for RAG response generation
    """
    try:
        from app.farmgrow.services import OllamaLLMService
        return OllamaLLMService(model_name="mistral:7b-instruct", max_tokens=1024)
    except Exception as e:
        logger.error(f"Error initializing FarmGrow LLM service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow LLM service"
        )


async def get_farmgrow_ocr_service():
    """
    Dependency: FarmGrow OCR service for image-to-text
    
    Returns:
        OCRService instance for document image processing
    """
    try:
        from app.farmgrow.services import OCRService
        from core.ollama_service import OllamaService
        
        # Get Ollama service instance and pass to OCRService
        ollama_service = OllamaService()
        return OCRService(ocr_provider="ollama", ollama_service=ollama_service)
    except Exception as e:
        logger.error(f"Error initializing FarmGrow OCR service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow OCR service"
        )


async def get_farmgrow_retriever(
    embedding_service = Depends(get_far_grow_embedding_service)
):
    """
    Dependency: FarmGrow RAG retriever with hybrid BM25 + vector search
    
    Args:
        embedding_service: Embedding service for vector search
        
    Returns:
        RAGRetriever instance configured with top-k and ranking
    """
    try:
        from app.farmgrow.services import RAGRetriever
        return RAGRetriever(embedding_service=embedding_service, top_k=5)
    except Exception as e:
        logger.error(f"Error initializing FarmGrow retriever: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow retriever"
        )


async def get_farmgrow_ranker():
    """
    Dependency: FarmGrow document ranker with multi-signal ranking
    
    Returns:
        DocumentRanker instance for relevance scoring
    """
    try:
        from app.farmgrow.services import DocumentRanker
        return DocumentRanker()
    except Exception as e:
        logger.error(f"Error initializing FarmGrow ranker: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow ranker"
        )


async def get_farmgrow_ingestion_service(
    embedding_service = Depends(get_far_grow_embedding_service),
    ocr_service = Depends(get_farmgrow_ocr_service)
):
    """
    Dependency: FarmGrow document ingestion service
    
    Handles PDF parsing, OCR, chunking, and embedding generation
    
    Args:
        embedding_service: Service for generating embeddings
        ocr_service: Service for extracting text from images
        
    Returns:
        DocumentIngestionService instance
    """
    try:
        from app.farmgrow.services import DocumentIngestionService
        return DocumentIngestionService(
            embedding_service=embedding_service,
            ocr_service=ocr_service
        )
    except Exception as e:
        logger.error(f"Error initializing FarmGrow ingestion service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow ingestion service"
        )


async def get_farmgrow_conversation_service(db=Depends(get_database_connection)):
    """
    Dependency: FarmGrow conversation service for chat history
    
    Manages conversation state, message history, and context memory
    
    Args:
        db: Database connection for conversation storage
        
    Returns:
        ConversationService instance
    """
    try:
        from app.farmgrow.services import ConversationService
        return ConversationService(db_repository=db)
    except Exception as e:
        logger.error(f"Error initializing FarmGrow conversation service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow conversation service"
        )


async def get_farmgrow_embedding_store():
    """
    Dependency: FarmGrow embedding cache management
    
    Local cache for embeddings to reduce API calls and improve performance
    
    Returns:
        LocalEmbeddingStore instance with configured storage directory
    """
    try:
        from app.farmgrow.services.embedding_store import LocalEmbeddingStore
        return LocalEmbeddingStore(storage_dir="./embeddings_cache")
    except Exception as e:
        logger.error(f"Error initializing FarmGrow embedding store: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow embedding store"
        )


async def get_farmgrow_orchestrator(
    ingestion_service = Depends(get_farmgrow_ingestion_service),
    embedding_service = Depends(get_far_grow_embedding_service),
    embedding_store = Depends(get_farmgrow_embedding_store),
    retriever = Depends(get_farmgrow_retriever),
    ranker = Depends(get_farmgrow_ranker),
    llm_service = Depends(get_farmgrow_llm_service),
    conversation_service = Depends(get_farmgrow_conversation_service),
):
    """
    Dependency: FarmGrow RAG orchestrator service
    
    Main orchestration service that combines all FarmGrow services:
    - Retrieves relevant documents via hybrid search
    - Ranks them by relevance
    - Generates LLM response
    - Manages conversation history
    
    Args:
        ingestion_service: Document ingestion service
        embedding_service: Text embedding service
        embedding_store: Embedding cache storage
        retriever: RAG retriever service
        llm_service: LLM service for response generation
        ranker: Document ranking service
        conversation_service: Conversation history service
        
    Returns:
        RAG orchestrator service instance
    """
    try:
        from app.farmgrow.services import RAGOrchestrator
        return RAGOrchestrator(
            ingestion_service=ingestion_service,
            embedding_service=embedding_service,
            embedding_store=embedding_store,
            retrieval_service=retriever,
            ranking_service=ranker,
            llm_service=llm_service,
            conversation_service=conversation_service
        )
    except Exception as e:
        logger.error(f"Error initializing FarmGrow orchestrator: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize FarmGrow orchestrator"
        )

__all__ = [
    # Authentication
    "get_farmiq_id_from_header",
    "get_user_by_farmiq_id",
    "get_user_context",
    # Database & Repositories
    "get_database_connection",
    "get_farm_repository",
    "get_production_repository",
    "get_prediction_repository",
    "get_risk_repository",
    "get_market_repository",
    "get_worker_repository",
    "get_farm_intelligence_service",
    # RAG Services
    "get_embedding_service",
    "get_llm_service",
    "get_conversation_service",
    "get_retrieval_service",
    "get_ingestion_service",
    # FarmGrow Services
    "get_far_grow_embedding_service",
    "get_farmgrow_llm_service",
    "get_farmgrow_ocr_service",
    "get_farmgrow_retriever",
    "get_farmgrow_ranker",
    "get_farmgrow_ingestion_service",
    "get_farmgrow_conversation_service",
    "get_farmgrow_embedding_store",
    "get_farmgrow_orchestrator",
]
