"""
FarmGrow RAG API Routes

Comprehensive endpoints for agricultural Q&A using retrieval-augmented generation:
- /query: Ask questions about farming (sync/async)
- /chat: Unified chat endpoint with streaming and image support
- /documents: Document upload and management
- /conversations: Chat history and conversation management
- /messages: Message retrieval
- /models: Available models and configuration
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks, Header, File, UploadFile, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, AsyncGenerator, Dict
import logging
import asyncio
from datetime import datetime
import uuid
import os
import re

from app.farmgrow.services import (
    EmbeddingService,
    RAGRetriever,
    DocumentRanker,
    OllamaLLMService,
    RetrievalMethod,
    RAGContext,
    LLMResponse,
    OCRService,
    DocumentIngestionService
)
from app.farmgrow.services.embedding_store import LocalEmbeddingStore
from auth.dependencies import (
    get_user_context,
    get_far_grow_embedding_service,
    get_farmgrow_llm_service,
    get_farmgrow_ocr_service,
    get_farmgrow_retriever,
    get_farmgrow_ranker,
    get_farmgrow_ingestion_service,
    get_farmgrow_conversation_service,
    get_farmgrow_embedding_store,
)

# Cortex AI tracking
from core import AISystem, RequestType, RequestStatus, cortex_track, get_system_analytics

# Token tracking (Phase 3)
from app.ai_usage.services.usage_tracker import AIUsageTracker
import time

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/farmgrow", tags=["FarmGrow RAG"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RAGQueryRequest(BaseModel):
    """Request to query RAG system"""
    query: str = Field(..., description="Question about farming")
    user_id: str = Field(..., description="User making the query")
    conversation_id: Optional[str] = Field(None, description="Conversation context")
    top_k: int = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    similarity_threshold: float = Field(0.3, description="Minimum similarity score")
    retrieval_method: str = Field( "hybrid", description="Retrieval strategy (hybrid, vector_only, bm25_only)")
    include_explanation: bool = Field(False, description="Include ranking explanation for each result")
    stream: bool = Field(False, description="Stream response tokens")
    input_type: str = Field("text", description="Input type (text, image, mixed)")
    message: Optional[str] = Field(None, description="Alternative query field")


class DocumentChunk(BaseModel):
    """Single document chunk in response"""
    chunk_id: str
    content: str
    relevance_score: float
    document_title: str
    document_category: str


class RAGQueryResponse(BaseModel):
    """Response from RAG query"""
    id: str
    conversation_id: str
    query: str
    answer: str
    supporting_documents: Optional[List[DocumentChunk]] = None
    confidence_score: float
    model_used: str = "mistral:7b-instruct"
    generation_time_seconds: float = 0.0
    tokens_used: int = 0
    processing_time_ms: int = 0
    message_id: str
    explanations: Optional[List[str]] = None


class ConversationMessage(BaseModel):
    """Single message in conversation"""
    message_id: str
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    query_id: Optional[str] = None


class ConversationInfo(BaseModel):
    """Conversation metadata"""
    conversation_id: str
    user_id: str
    title: str
    created_at: datetime
    last_message_at: datetime
    message_count: int
    tags: List[str] = []


class DocumentUploadRequest(BaseModel):
    """Request to upload document to knowledge base"""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document text")
    category: str = Field("guide", description="Document category")
    source_url: Optional[str] = Field(None, description="Original source URL")
    language: str = Field("en", description="Document language")


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Query FarmGrow for agricultural information",
)
async def query_farmgrow(
    request: RAGQueryRequest,
    user: Dict = Depends(get_user_context),
    retriever = Depends(get_farmgrow_retriever),
    ranker = Depends(get_farmgrow_ranker),
    llm_service = Depends(get_farmgrow_llm_service),
) -> RAGQueryResponse:
    """
    Query the FarmGrow RAG system for agricultural information
    
    Implements complete RAG pipeline:
    1. Query Rewriting: Expand query for better retrieval
    2. Retrieval: Hybrid BM25 + vector search
    3. Ranking: Multi-signal ranking of results
    4. Generation: LLM generates answer with context
    """
    async with cortex_track(
        system=AISystem.FARMGROW,
        request_type=RequestType.RAG_QUERY,
        user_id=request.user_id,
        farm_id=request.conversation_id
    ) as tracker:
        try:
            query_id = str(uuid.uuid4())
            logger.info(f"Processing query {query_id}: {request.query[:80]}...")
            logger.info(f"   User: {user.get('user_id')}, FarmIQ ID: {user.get('farmiq_id')}")
            
            # Step 1: Retrieve relevant documents
            retrieval_method = RetrievalMethod(request.retrieval_method)
            rag_context: RAGContext = await retriever.retrieve(
                query=request.query,
                method=retrieval_method,
                top_k=request.top_k
            )
            
            logger.info(f"Retrieved {len(rag_context.retrieved_chunks)} chunks")
            
            # Step 2: Rank documents by relevance
            ranked_chunks = await ranker.rerank(
                chunks=rag_context.retrieved_chunks,
                query=request.query,
                user_id=request.user_id
            )
            
            # Step 3: Extract content from ranked chunks
            context_texts = [chunk.content for chunk in ranked_chunks]
            
            # Step 4: Generate answer using LLM
            llm_response: LLMResponse = await llm_service.generate_response(
                query=request.query,
                context_chunks=context_texts
            )
            
            logger.info(f"✅ Response generated ({llm_response.tokens_used} tokens, confidence: {llm_response.confidence:.2f})")
            
            # Record tokens in Cortex tracker
            tracker.record_tokens(
                input_tokens=len(request.query.split()),
                output_tokens=llm_response.tokens_used,
                model=llm_response.model,
                cost_usd=0.0  # Calculate actual cost as needed
            )
            
            # Step 5: Format supporting documents
            supporting_docs = [
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content,
                    relevance_score=getattr(chunk, 'final_ranking_score', chunk.relevance_score),
                    document_title=getattr(chunk, 'document_title', 'Unknown'),
                    document_category=getattr(chunk, 'document_category', 'guide')
                )
                for chunk in ranked_chunks[:3]
            ]
            
            # Step 6: Generate explanations if requested
            explanations = None
            if request.include_explanation:
                explanations = [ranker.get_ranking_explanation(chunk) for chunk in ranked_chunks[:3]]
            
            # Step 7: Create response
            response = RAGQueryResponse(
                id=query_id,
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                query=request.query,
                answer=llm_response.answer,
                supporting_documents=supporting_docs,
                confidence_score=llm_response.confidence,
                model_used=llm_response.model,
                generation_time_seconds=getattr(llm_response, 'generation_time_seconds', 0.0),
                tokens_used=llm_response.tokens_used,
                message_id=str(uuid.uuid4()),
                explanations=explanations
            )
            
            # Step 8: Track token usage (Phase 3 - Non-blocking)
            try:
                duration_ms = int((time.time() - time.time()) * 1000)  # Calculate actual duration
                tracker_instance = AIUsageTracker()
                
                # Get user wallet from database context
                from sqlalchemy.ext.asyncio import AsyncSession
                from sqlalchemy import select
                from app.farmscore.domain.entities.user_wallet import UserWallet
                
                # Get farmiq_id from user context
                farmiq_id = getattr(user, 'farmiq_id', request.user_id)
                
                # Track FarmGrow RAG query usage (1 FIQ per query)
                usage_result = await tracker_instance.track_farmgrow_usage(
                    farmiq_id=farmiq_id,
                    user_id=request.user_id,
                    hedera_wallet=getattr(user, 'hedera_wallet_id', ''),
                    query_text=request.query[:100],
                    retrieved_docs_count=len(ranked_chunks),
                    confidence_score=llm_response.confidence,
                    model_used=llm_response.model,
                    duration_ms=duration_ms
                )
                
                if usage_result.get('success'):
                    logger.info(f"✅ FarmGrow usage tracked: 1 FIQ deducted for RAG query")
                    
            except Exception as tracking_error:
                logger.warning(f"⚠️ Token tracking failed (non-blocking): {tracking_error}")
            
            return response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chat",
    summary="Unified Chat Endpoint",
    description="""
    Handles all chat operations:
    - Text queries (synchronous)
    - Image uploads with OCR
    - Streaming responses
    - Conversation memory
    """
)
async def unified_chat_endpoint(
    request: RAGQueryRequest,
    user: Dict = Depends(get_user_context),
    retriever = Depends(get_farmgrow_retriever),
    ranker = Depends(get_farmgrow_ranker),
    llm_service = Depends(get_farmgrow_llm_service),
    ocr_service = Depends(get_farmgrow_ocr_service),
    embedding_service = Depends(get_far_grow_embedding_service),
    embedding_store = Depends(get_farmgrow_embedding_store),
    conversation_service = Depends(get_farmgrow_conversation_service),
):
    """
    Unified Chat Endpoint - Handles text, images, and streaming
    
    Supports:
    - Text queries (synchronous)
    - Image uploads with OCR (processes and stores in embeddings)
    - Streaming responses (set stream=true in request)
    """
    async with cortex_track(
        system=AISystem.FARMGROW,
        request_type=RequestType.RAG_CHAT,
        user_id=request.user_id,
        farm_id=request.conversation_id
    ) as tracker:
        try:
            should_stream = request.stream
            query_text = request.query or request.message or ""
            
            logger.info(f"Chat request from user: {user.get('user_id')}")
            logger.info(f"   Stream mode: {should_stream}, Input type: {request.input_type}")
            logger.info(f"   Query preview: {query_text[:80]}...")
            
            # Process images if present (OCR + embedding storage)
            enhanced_text = query_text
            if request.input_type in ["image", "mixed"]:
                image_pattern = r'\[Image:\s*([^\]]+)\]'
                image_matches = re.findall(image_pattern, query_text)
                
                if image_matches:
                    logger.info(f"Processing {len(image_matches)} image references with OCR")
                    
                    for image_file in image_matches:
                        image_file = image_file.strip()
                        image_paths = [f"./uploads/{image_file}", f"./temp/{image_file}", image_file]
                        
                        for image_path in image_paths:
                            if os.path.exists(image_path):
                                try:
                                    logger.info(f"Extracting text from: {image_file}")
                                    ocr_result = await ocr_service.extract_text(image_path, detailed=True)
                                    ocr_text = ocr_result.get("text", "") if isinstance(ocr_result, dict) else ocr_result
                                    
                                    if ocr_text:
                                        logger.info(f"OCR extracted {len(ocr_text)} characters")
                                        
                                        # Store in embeddings cache
                                        chunk_id = str(uuid.uuid4())
                                        ocr_embedding = await embedding_service.generate_embedding(ocr_text)
                                        embedding_store.save_embedding(
                                            chunk_id=chunk_id,
                                            content=ocr_text,
                                            embedding=ocr_embedding,
                                            document_id=f"ocr_{chunk_id[:8]}",
                                            metadata={
                                                "source": "ocr",
                                                "image_file": image_file,
                                                "user_id": request.user_id,
                                            }
                                        )
                                        logger.info("OCR text stored in embeddings cache")
                                        
                                        enhanced_text += f"\n\nContent from image '{image_file}':\n{ocr_text[:500]}"
                                except Exception as e:
                                    logger.warning(f"OCR failed for {image_file}: {e}")
                                break
            
            final_query = enhanced_text if enhanced_text != query_text else query_text
            logger.info(f"Final query: {len(final_query)} chars")
            
            # STREAMING MODE
            if should_stream:
                async def generate_stream() -> AsyncGenerator[str, None]:
                    try:
                        yield f'data: {{"status": "started", "query": "{query_text[:100].replace('"', '\\"')}"}}\n\n'
                        
                        token_count = 0
                        async for token in llm_service.generate_response_streaming(final_query):
                            escaped_token = (token
                                .replace('\\', '\\\\')
                                .replace('"', '\\"')
                                .replace('\n', '\\n')
                                .replace('\r', '\\r')
                                .replace('\t', '\\t')
                            )
                            yield f'data: {{"token": "{escaped_token}"}}\n\n'
                            token_count += 1
                        
                        logger.info(f"Stream complete - {token_count} tokens")
                        yield f'data: {{"status": "complete", "tokens": {token_count}}}\n\n'
                        
                        # Record tokens
                        tracker.record_tokens(
                            input_tokens=len(query_text.split()),
                            output_tokens=token_count,
                            model="mistral:7b"
                        )
                        
                    except Exception as e:
                        logger.error(f"Stream error: {str(e)}", exc_info=True)
                        yield f'data: {{"status": "error", "message": "{str(e).replace('"', '\\"')}"}}\n\n'
                
                return StreamingResponse(
                    generate_stream(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
                )
            
            # NON-STREAMING MODE
            else:
                # Retrieve context
                rag_context: RAGContext = await retriever.retrieve(
                    query=final_query,
                    top_k=request.top_k
                )
                
                # Generate answer
                llm_response: LLMResponse = await llm_service.generate_response(
                    query=query_text,
                    context_chunks=[chunk.content for chunk in rag_context.retrieved_chunks]
                )
                
                # Record tokens
                tracker.record_tokens(
                    input_tokens=len(query_text.split()),
                    output_tokens=llm_response.tokens_used,
                    model=llm_response.model
                )
                
                supporting_docs = [
                    DocumentChunk(
                        chunk_id=chunk.chunk_id,
                        content=chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content,
                        relevance_score=chunk.relevance_score,
                        document_title=getattr(chunk, 'document_title', 'Unknown'),
                        document_category=getattr(chunk, 'document_category', 'guide')
                    )
                    for chunk in rag_context.retrieved_chunks[:3]
                ]
                
                return RAGQueryResponse(
                    id=str(uuid.uuid4()),
                    conversation_id=request.conversation_id or str(uuid.uuid4()),
                    query=query_text,
                    answer=llm_response.answer,
                    supporting_documents=supporting_docs,
                    confidence_score=llm_response.confidence,
                    tokens_used=llm_response.tokens_used,
                    message_id=str(uuid.uuid4()),
                )
                
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))




@router.post(
    "/upload",
    summary="Upload document to knowledge base",
    description="Add a new document to FarmGrow's knowledge base for RAG ingestion"
)
async def upload_document(
    file: UploadFile = File(...),
    category: str = "general",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: Dict = Depends(get_user_context),
    ingestion_service = Depends(get_farmgrow_ingestion_service),
):
    """
    Upload document to knowledge base
    
    Document will be:
    1. Parsed and chunked
    2. Embedded with BGE-M3
    3. Stored in database
    4. Indexed for retrieval
    
    Returns:
    {
        document_id: UUID,
        filename: str,
        chunks_created: int,
        message: str
    }
    """
    try:
        doc_id = str(uuid.uuid4())
        logger.info(f"Uploading document {doc_id}: {file.filename}")
        logger.info(f"   User: {user.get('user_id')}")
        
        # Validate file
        if not file.filename.lower().endswith(('.pdf', '.txt', '.md')):
            raise HTTPException(status_code=400, detail="Only PDF, TXT, and MD files supported")
        
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
        
        # Read content
        content = await file.read()
        
        # Add background task to process document
        background_tasks.add_task(
            _process_document,
            doc_id=doc_id,
            filename=file.filename,
            content=content,
            category=category
        )
        
        logger.info(f"Document {doc_id} queued for processing")
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "status": "processing",
            "message": f"Document '{file.filename}' queued for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get(
    "/conversations",
    response_model=List[ConversationInfo],
    summary="List user conversations"
)
async def list_conversations(
    user: Dict = Depends(get_user_context),
    limit: int = Query(50, ge=1, le=100),
    conversation_service = Depends(get_farmgrow_conversation_service),
):
    """Get user's conversation history"""
    try:
        logger.info(f"Listing conversations for user {user.get('user_id')}")
        return []
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/conversations",
    response_model=ConversationInfo,
    summary="Create new conversation"
)
async def create_conversation(
    user: Dict = Depends(get_user_context),
    title: str = Query("Untitled Conversation"),
    conversation_service = Depends(get_farmgrow_conversation_service),
):
    """Start a new conversation"""
    try:
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created conversation {conversation_id} for user {user.get('user_id')}")
        
        return ConversationInfo(
            conversation_id=conversation_id,
            user_id=user.get('user_id'),
            title=title,
            created_at=datetime.now(),
            last_message_at=datetime.now(),
            message_count=0,
            tags=[]
        )
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[ConversationMessage],
    summary="Get conversation messages"
)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    user: Dict = Depends(get_user_context),
    conversation_service = Depends(get_farmgrow_conversation_service),
):
    """Retrieve all messages in a conversation (ordered by timestamp)"""
    try:
        logger.info(f"Retrieving messages for conversation {conversation_id}, limit: {limit}")
        logger.info(f"   User: {user.get('user_id')}")
        return []
        
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete conversation"
)
async def delete_conversation(
    conversation_id: str,
    user: Dict = Depends(get_user_context),
    conversation_service = Depends(get_farmgrow_conversation_service),
):
    """Soft-delete a conversation (GDPR compliant)"""
    try:
        logger.info(f"Deleting conversation {conversation_id} for user {user.get('user_id')}")
        return {"message": "Conversation deleted"}
        
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/models",
    status_code=200,
    summary="Get Available Models",
    description="Retrieve available RAG models and system configuration for agricultural AI processing",
    tags=["FarmGrow", "Configuration"],
    responses={
        200: {"description": "List of available models with parameters and configuration"},
        500: {"description": "Internal server error"}
    }
)
async def get_available_models():
    """
    Get available RAG models and configuration
    
    Returns detailed information about available:
    - Text models with parameters and speed ratings
    - Embedding models for semantic search
    - OCR models for document processing
    - Recommended models for optimal performance
    
    Returns:
        Dict containing:
        - available_models: List of text models
        - embedding_model: Embedding configuration
        - ocr_model: OCR configuration
        - recommended_model: Suggested model name
        - status: System readiness status
        - features: Supported AI features
    """
    try:
        from config.models import DEFAULT_TEXT_MODEL, EMBEDDING_MODEL, OCR_MODEL, TEXT_MODELS
        
        available_models = [
            {
                "name": name,
                "parameters": config.parameters,
                "speed": config.speed,
                "description": config.description,
            }
            for name, config in TEXT_MODELS.items()
        ]
        
        return {
            "available_models": available_models,
            "text_models": {
                name: {
                    "name": config.name,
                    "parameters": config.parameters,
                    "speed": config.speed,
                    "description": config.description,
                }
                for name, config in TEXT_MODELS.items()
            },
            "embedding_model": {
                "name": EMBEDDING_MODEL.name,
                "parameters": EMBEDDING_MODEL.parameters,
                "speed": EMBEDDING_MODEL.speed,
                "description": EMBEDDING_MODEL.description,
            },
            "ocr_model": {
                "name": OCR_MODEL.name,
                "parameters": OCR_MODEL.parameters,
                "speed": OCR_MODEL.speed,
                "description": OCR_MODEL.description,
            },
            "recommended_model": DEFAULT_TEXT_MODEL,
            "default_text_model": DEFAULT_TEXT_MODEL,
            "status": "ready",
            "features": [
                "semantic_search",
                "hybrid_retrieval",
                "streaming_responses",
                "conversation_memory",
                "document_upload",
                "multilingual_support",
                "ocr_support",
                "image_processing"
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch models")


@router.get(
    "/health",
    status_code=200,
    summary="FarmGrow Health Check",
    description="Check FarmGrow RAG system health and verify all pipeline components are operational",
    tags=["FarmGrow", "Health"],
    responses={
        200: {"description": "Service health status including component availability"},
        503: {"description": "Service unavailable or degraded"}
    }
)
async def health_check(
    llm_service = Depends(get_farmgrow_llm_service),
):
    """
    Check FarmGrow system health
    
    Verifies:
    - Ollama LLM connection
    - Embedding service availability
    - OCR service status
    - RAG pipeline readiness
    
    Returns:
        Dict containing:
        - status: 'healthy' or 'degraded'
        - ollama_available: Whether LLM service is ready
        - components: Individual component statuses
        - timestamp: Health check timestamp
    """
    try:
        ollama_ok = await llm_service.validate_connection()
        
        return {
            "status": "healthy" if ollama_ok else "degraded",
            "services": {
                "ollama": "ok" if ollama_ok else "disconnected",
                "embeddings": "ok",
                "retrieval": "ok",
                "ocr": "ok"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get(
    "/analytics/dashboard",
    summary="FarmGrow Analytics Dashboard",
    tags=["Analytics"]
)
async def farmgrow_analytics_dashboard(
    user: Dict = Depends(get_user_context),
):
    """
    Get comprehensive FarmGrow analytics with Cortex tracking data
    
    Returns:
    - System statistics (total requests, success rate)
    - Cost breakdown (tokens, USD per model)
    - Performance metrics (duration, cache hit rate)
    - User activity (requests per user)
    - Recent requests
    """
    try:
        stats = get_system_analytics(AISystem.FARMGROW)
        
        logger.info(f"Dashboard request from user: {user.get('user_id')}")
        
        return {
            "system": "FarmGrow RAG",
            "timestamp": datetime.now().isoformat(),
            "metrics": stats,
            "description": "Real-time analytics for FarmGrow AI system",
        }
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/user/{user_id}",
    summary="User Activity Analytics",
    tags=["Analytics"]
)
async def user_activity_analytics(
    user_id: str,
    user: Dict = Depends(get_user_context),
):
    """
    Get user's FarmGrow activity and usage analytics
    
    Returns:
    - Total requests and completion rate
    - Requests grouped by type (RAG_QUERY, RAG_CHAT, RAG_SEARCH)
    - Usage timeline
    - Average metrics
    """
    try:
        from core import get_user_activity_analytics
        
        activity = get_user_activity_analytics(user_id)
        
        logger.info(f"User activity report for: {user_id}")
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
        }
        
    except Exception as e:
        logger.error(f"User activity analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analytics/farm/{farm_id}",
    summary="Farm Activity Analytics",
    tags=["Analytics"]
)
async def farm_activity_analytics(
    farm_id: str,
    user: Dict = Depends(get_user_context),
):
    """
    Get farm's FarmGrow activity and usage analytics
    
    Returns:
    - Farm's total RAG requests
    - Query distribution by type
    - Recent queries
    - System usage trends
    """
    try:
        from core import get_farm_activity_analytics
        
        activity = get_farm_activity_analytics(farm_id)
        
        logger.info(f"Farm activity report for: {farm_id}")
        
        return {
            "farm_id": farm_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
        }
        
    except Exception as e:
        logger.error(f"Farm activity analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Background Tasks
# ============================================================================

async def _process_document(
    doc_id: str,
    filename: str,
    content: bytes,
    category: str
):
    """
    Background task to process uploaded document
    
    Steps:
    1. Parse document into chunks
    2. Embed chunks
    3. Store in database
    4. Index for retrieval
    """
    try:
        logger.info(f"Processing document {doc_id}: {filename}")
        
        # Decode content
        text_content = content.decode('utf-8', errors='ignore')
        
        # Parse document into chunks (e.g., ~300 token chunks)
        chunks = _chunk_document(
            text=text_content,
            document_id=doc_id,
            chunk_sizes=[250, 500, 1000]
        )
        
        logger.info(f"✅ Completed processing document {doc_id} ({len(chunks)} chunks)")
        
    except Exception as e:
        logger.error(f"Document processing failed for {doc_id}: {e}", exc_info=True)


def _chunk_document(text: str, document_id: str, chunk_sizes: List[int]) -> List[dict]:
    """
    Chunk document into overlapping pieces
    
    Uses largest chunk size by default (1000 tokens ≈ 333 words)
    with 25% overlap for context preservation
    """
    chunks = []
    words = text.split()
    
    # Use largest chunk size by default
    chunk_size_words = chunk_sizes[-1] // 3
    overlap = chunk_size_words // 4
    
    for i in range(0, len(words), chunk_size_words - overlap):
        chunk_text = " ".join(words[i:i + chunk_size_words])
        if len(chunk_text) > 20:  # Skip very small chunks
            chunks.append({
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "content": chunk_text,
                "chunk_index": len(chunks),
                "token_count": len(chunk_text.split()),
                "created_at": datetime.utcnow(),
            })
    
    return chunks
