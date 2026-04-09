"""
FarmGrow RAG Services Package - Complete Consolidated Version
Complete RAG system for agricultural Q&A using local Ollama models.

Core Services:
- Orchestrator: Main pipeline that chains all components
- Ingestion: Document processing, chunking, PDF extraction
- Embeddings: Text embedding generation (BGE-M3, multilingual)
- Retrieval: Hybrid retrieval (BM25 + vector similarity)
- Ranking: Multi-signal ranking with document authority
- LLM: Answer generation using Ollama (mistral/llama)
- OCR: Image text extraction from scanned documents
- Conversations: Chat history management (Supabase + fallback)
- EmbeddingStore: Local NumPy + JSON embedding storage

This consolidated package combines legacy rag/* services with modularized architecture.
"""

# Core orchestration
from app.farmgrow.services.orchestrator import (
    RAGOrchestrator,
    get_rag_orchestrator,
    RAGResponse
)

# Document processing
from app.farmgrow.services.ingestion import (
    DocumentIngestionService,
    get_ingestion_service
)

# Text embedding
from app.farmgrow.services.embeddings import (
    EmbeddingService,
    EmbeddingSimilarityCalculator
)

# Retrieval
from app.farmgrow.services.retrieval import (
    RAGRetriever,
    BM25Scorer,
    QueryRewriter,
    RetrievedChunk,
    RAGContext,
    RetrievalMethod
)

# Ranking
from app.farmgrow.services.ranking import (
    DocumentRanker,
    RankingSignal
)

# Language model
from app.farmgrow.services.llm import (
    OllamaLLMService,
    LLMResponse
)

# OCR
from app.farmgrow.services.ocr import (
    OCRService,
    get_ocr_service
)

# Conversations
from app.farmgrow.services.conversations import (
    ConversationService,
    ConversationMessage,
    Conversation,
    get_conversation_service
)

# Embedding storage
from app.farmgrow.services.embedding_store import (
    LocalEmbeddingStore,
    EmbeddingStore
)

__all__ = [
    # Orchestration
    "RAGOrchestrator",
    "get_rag_orchestrator",
    "RAGResponse",
    
    # Ingestion
    "DocumentIngestionService",
    "get_ingestion_service",
    
    # Embeddings
    "EmbeddingService",
    "EmbeddingSimilarityCalculator",
    
    # Retrieval
    "RAGRetriever",
    "BM25Scorer",
    "QueryRewriter",
    "RetrievedChunk",
    "RAGContext",
    "RetrievalMethod",
    
    # Ranking
    "DocumentRanker",
    "RankingSignal",
    
    # LLM
    "OllamaLLMService",
    "LLMResponse",
    
    # OCR
    "OCRService",
    "get_ocr_service",
    
    # Conversations
    "ConversationService",
    "ConversationMessage",
    "Conversation",
    "get_conversation_service",
    
    # Embedding Store
    "LocalEmbeddingStore",
    "EmbeddingStore",
]

__version__ = "1.0.0"
__description__ = "FarmGrow RAG System - Complete Agricultural Intelligence"
