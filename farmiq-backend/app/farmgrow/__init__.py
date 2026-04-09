"""
FarmGrow RAG System Package

Agricultural question-answering system using Retrieval-Augmented Generation:
- Hybrid vector + BM25 retrieval
- Multi-signal document ranking
- Local LLM inference via Ollama
- Source citation and confidence scoring

FarmGrow Architecture:
┌──────────────────┐
│  User Query      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│ Query Rewriting & Expansion  │
└────────┬─────────────────────┘
         │
         ├─────────────────────┬──────────────────┐
         ▼                     ▼                  ▼
    ┌─────────┐         ┌──────────┐       ┌──────────┐
    │ Embedding│         │ BM25     │       │ Rewriting│
    │ Service  │         │ Scorer   │       │          │
    └────┬────┘         └────┬─────┘       └──────────┘
         │                   │
         └─────────┬─────────┘
                   ▼
           ┌──────────────────┐
           │ Hybrid Retriever │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Document Ranker  │ (Multi-signal)
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Ollama LLM       │
           │ Service          │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Context Assembly │
           │ & Response       │
           └──────────────────┘

Services:
- embeddings: BGE-M3 text embeddings with caching
- retrieval: Hybrid BM25 + vector search with deduplication
- ranking: Multi-signal re-ranking (semantic, keyword, authority, recency)
- llm: Ollama interface with prompt engineering
"""

from app.farmgrow.services import (
    EmbeddingService,
    EmbeddingSimilarityCalculator,
    RAGRetriever,
    BM25Scorer,
    QueryRewriter,
    RetrievedChunk,
    RAGContext,
    RetrievalMethod,
    DocumentRanker,
    RankingSignal,
    OllamaLLMService,
    LLMResponse
)

__all__ = [
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
    "LLMResponse"
]
