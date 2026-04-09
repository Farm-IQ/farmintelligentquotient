"""
FarmGrow Retrieval Service
Implements hybrid retrieval: BM25 (sparse) + Vector (dense) + Reranking

Hybrid Retrieval Strategy:
- BM25: High precision for keyword matching
- Vector: High recall for semantic similarity
- Local Storage: Fallback for when embeddings unavailable
- Lazy Loading: Generate embeddings on-demand if missing

Integrated from legacy rag_retrieval_service.py:
- Cosine similarity computation
- Local storage fallback mechanism
- Lazy embedding generation
- Fallback cascade for robustness
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class RetrievalMethod(str, Enum):
    """Different retrieval strategies"""
    HYBRID = "hybrid"           # BM25 + vector similarity
    VECTOR_ONLY = "vector_only" # Dense retrieval only
    BM25_ONLY = "bm25_only"     # Sparse retrieval only
    MULTI_VECTOR = "multi_vector"  # Multiple embedding models


@dataclass
class RetrievedChunk:
    """Single retrieved document chunk"""
    chunk_id: str
    document_id: str
    content: str
    page_number: Optional[int] = None
    relevance_score: float = 0.0
    retrieval_method: str = "unknown"
    document_title: Optional[str] = None
    document_category: Optional[str] = None


@dataclass
class RAGContext:
    """Context for RAG query containing retrieved chunks"""
    query: str
    retrieved_chunks: List[RetrievedChunk]
    top_k: int
    similarity_threshold: float
    retrieval_method: RetrievalMethod


class BM25Scorer:
    """
    BM25 Sparse Retrieval Scorer
    
    Implements Okapi BM25 algorithm for keyword-based retrieval
    
    BM25(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D|/avgdl))
    
    Where:
    - D: Document
    - Q: Query  
    - f(qi, D): Frequency of term qi in document D
    - |D|: Length of document
    - avgdl: Average document length
    - k1, b: Tuning parameters (k1≈2.0, b≈0.75)
    
    Attributes:
        k1: Term frequency saturation parameter (default: 2.0)
        b: Length normalization parameter (default: 0.75)
        idf_cache: Cache for IDF values
    """
    
    def __init__(self, k1: float = 2.0, b: float = 0.75):
        """
        Initialize BM25 scorer
        
        Args:
            k1: Term frequency saturation (higher = less saturation)
            b: Length normalization (0 = no normalization, 1 = full normalization)
        """
        self.k1 = k1
        self.b = b
        self.idf_cache: Dict[str, float] = {}
        logger.info(f"Initialized BM25Scorer with k1={k1}, b={b}")
    
    def score_query(
        self,
        query_terms: List[str],
        document_text: str,
        avg_doc_length: float,
        num_docs_with_term: Dict[str, int],
        total_docs: int
    ) -> float:
        """
        Calculate BM25 score for document given query
        
        Higher score = more relevant to query
        
        Args:
            query_terms: Tokenized query terms (lowercased)
            document_text: Document/chunk text
            avg_doc_length: Average length (in tokens) across corpus
            num_docs_with_term: Dict of term -> number of docs containing it
            total_docs: Total documents in corpus
            
        Returns:
            BM25 score (typically 0-20)
        """
        if not query_terms or not document_text:
            return 0.0
        
        doc_length = len(document_text.split())
        if doc_length == 0:
            return 0.0
        
        score = 0.0
        doc_text_lower = document_text.lower()
        
        for term in query_terms:
            # Calculate IDF (Inverse Document Frequency)
            num_docs = num_docs_with_term.get(term, 1)
            idf = np.log((total_docs - num_docs + 0.5) / (num_docs + 0.5) + 1.0)
            
            # Count term frequency in document
            tf = doc_text_lower.split().count(term.lower())
            
            # BM25 formula
            if tf > 0:
                numerator = (self.k1 + 1) * tf
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / avg_doc_length)
                score += idf * (numerator / denominator)
        
        return score


class QueryRewriter:
    """
    Query rewriting and expansion for improved retrieval
    
    Techniques:
    - Query expansion: Add related terms
    - Query reformulation: Reword for better matching
    - Multi-language support: For agricultural terminology
    
    Attributes:
        expansion_keywords: Mapping of keywords to related terms
    """
    
    def __init__(self):
        """Initialize query rewriter with agricultural domain knowledge"""
        self.expansion_keywords = {
            "crop": ["plant", "cultivation", "farming", "harvest", "growth"],
            "pest": ["insect", "disease", "infestation", "treatment", "control"],
            "yield": ["production", "output", "harvest", "productivity", "harvest"],
            "loan": ["credit", "financing", "borrowing", "fund", "money"],
            "market": ["price", "sales", "trade", "commerce", "selling"],
            "soil": ["earth", "land", "fertility", "nutrients", "amendment"],
            "water": ["irrigation", "rainfall", "moisture", "drainage", "hydration"],
            "weather": ["climate", "temperature", "rainfall", "season", "condition"]
        }
        logger.info(f"Initialized QueryRewriter with {len(self.expansion_keywords)} keyword mappings")
    
    def rewrite_query(self, query: str) -> List[str]:
        """
        Generate query variations for better retrieval
        
        Returns list of: [original, expanded variants]
        
        Args:
            query: Original user query
            
        Returns:
            List of query variations (deduplicated)
        """
        variations = [query]
        
        # Query expansion: add related terms
        query_lower = query.lower()
        for keyword, expansions in self.expansion_keywords.items():
            if keyword in query_lower:
                for expansion in expansions:
                    # Replace keyword with expansion
                    expanded = query_lower.replace(keyword, expansion)
                    variations.append(expanded)
                    
                    # Also try adding expansion
                    variations.append(f"{query} {expansion}")
        
        # Deduplicate while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen:
                unique_variations.append(var)
                seen.add(var)
        
        logger.debug(f"Generated {len(unique_variations)} query variations from: {query[:50]}...")
        return unique_variations


class RAGRetriever:
    """
    Main RAG Retriever with Fallback Support
    
    Orchestrates multiple retrieval strategies:
    - Vector similarity search (dense retrieval)
    - BM25 keyword search (sparse retrieval)
    - Local storage fallback (when embeddings unavailable)
    - Lazy embedding generation (on-demand)
    - Hybrid combination
    
    Integrated from legacy rag_retrieval_service.py for robustness
    
    Implements deduplication and reranking
    
    Attributes:
        db_repo: Database repository for data access
        embedding_service: Service for text embeddings
        top_k: Default number of results to return
        similarity_threshold: Minimum similarity score threshold
        bm25: BM25 scorer instance
        query_rewriter: Query rewriter instance
        embedding_store_path: Path to local embedding storage for fallback
    """
    
    def __init__(
        self,
        db_repo,
        embedding_service,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        embedding_store_path: str = "embeddings_cache",
        embedding_store=None
    ):
        """
        Initialize RAG retriever
        
        Args:
            db_repo: Database repository instance
            embedding_service: Embedding service instance
            top_k: Default number of retrieval results
            similarity_threshold: Minimum relevance threshold
            embedding_store_path: Path to local embedding storage
            embedding_store: LocalEmbeddingStore instance for in-memory embeddings
        """
        self.db_repo = db_repo
        self.embedding_service = embedding_service
        self.embedding_store = embedding_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.embedding_store_path = Path(embedding_store_path)
        
        self.bm25 = BM25Scorer()
        self.query_rewriter = QueryRewriter()
        logger.info(f"Initialized RAGRetriever with top_k={top_k}, threshold={similarity_threshold}")
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Formula: cos(θ) = (A·B) / (||A|| ||B||)
        
        From legacy rag_retrieval_service.py
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score in [0, 1] range for normalized positive embeddings
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    async def _load_embedding_from_storage(
        self,
        chunk_id: str
    ) -> Optional[np.ndarray]:
        """
        Load embedding from local storage (fallback mechanism).
        
        From legacy rag_retrieval_service.py
        
        Args:
            chunk_id: ID of the chunk
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            emb_file = self.embedding_store_path / f"{chunk_id}.json"
            if emb_file.exists():
                with open(emb_file, 'r') as f:
                    data = json.load(f)
                    return np.array(data.get("embedding", []))
        except Exception as e:
            logger.debug(f"Failed to load embedding from storage: {e}")
        
        return None
    
    async def _generate_embedding_lazy(
        self,
        text: str,
        chunk_id: str
    ) -> Optional[np.ndarray]:
        """
        Generate embedding on-demand (lazy loading).
        
        From legacy rag_retrieval_service.py - only generate if needed
        
        Args:
            text: Text to embed
            chunk_id: ID of the chunk (for caching)
            
        Returns:
            Generated embedding or None on failure
        """
        try:
            embedding = await self.embedding_service.generate_embedding(text)
            
            # Save to local storage for future use
            try:
                self.embedding_store_path.mkdir(parents=True, exist_ok=True)
                emb_file = self.embedding_store_path / f"{chunk_id}.json"
                with open(emb_file, 'w') as f:
                    json.dump({"embedding": embedding.tolist()}, f)
            except Exception as e:
                logger.debug(f"Failed to cache embedding: {e}")
            
            return embedding
        except Exception as e:
            logger.error(f"Lazy embedding generation failed: {e}")
            return None
    
    async def retrieve(
        self,
        query: str,
        method: RetrievalMethod = RetrievalMethod.HYBRID,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> RAGContext:
        """
        Retrieve relevant chunks for query with intelligent routing
        
        For HYBRID mode: Evaluates both vector & BM25, selects the better method
        Reduces latency by avoiding redundant retrieval when one method clearly wins
        
        Args:
            query: User query to retrieve documents for
            method: Retrieval strategy (HYBRID, VECTOR_ONLY, BM25_ONLY, MULTI_VECTOR)
            top_k: Override default top_k per-method
            similarity_threshold: Override default threshold
            
        Returns:
            RAGContext with retrieved and ranked chunks
        """
        top_k = top_k or self.top_k
        threshold = similarity_threshold or self.similarity_threshold
        
        chunks = []
        selected_method = method
        
        # INTELLIGENT HYBRID: Run both, pick the better method
        if method == RetrievalMethod.HYBRID:
            try:
                # Run both in parallel
                vector_chunks = await self._vector_retrieve(query, top_k, threshold)
                bm25_chunks = await self._bm25_retrieve(query, top_k, threshold)
                
                logger.info(f"Vector found {len(vector_chunks)} chunks (avg score: {self._avg_score(vector_chunks):.3f})")
                logger.info(f"BM25 found {len(bm25_chunks)} chunks (avg score: {self._avg_score(bm25_chunks):.3f})")
                
                # Intelligently select with AGGRESSIVE thresholds for speed
                vector_quality = self._evaluate_chunk_quality(vector_chunks)
                bm25_quality = self._evaluate_chunk_quality(bm25_chunks)
                
                logger.info(f"Quality scores - Vector: {vector_quality:.3f}, BM25: {bm25_quality:.3f}")
                
                # AGGRESSIVE ROUTING: Prefer single method for speed, only combine if roughly equal
                if vector_quality > bm25_quality * 1.8:  # Vector significantly better (increased from 1.3)
                    logger.info("🎯 Using VECTOR retrieval (higher confidence semantic match) - FASTER")
                    chunks = vector_chunks
                    selected_method = RetrievalMethod.VECTOR_ONLY
                elif bm25_quality > vector_quality * 1.8:  # BM25 significantly better (increased from 1.3)
                    logger.info("🎯 Using BM25 retrieval (better keyword matches) - FAST")
                    chunks = bm25_chunks
                    selected_method = RetrievalMethod.BM25_ONLY
                elif vector_quality > 0.85:  # High confidence vector results - prefer for speed
                    logger.info("🎯 Using VECTOR retrieval (high confidence, faster processing)")
                    chunks = vector_chunks
                    selected_method = RetrievalMethod.VECTOR_ONLY
                else:  # Only combine as last resort
                    logger.info("🎯 Combining BOTH methods (similar quality)")
                    chunks = vector_chunks + bm25_chunks
                    selected_method = RetrievalMethod.HYBRID
                    
            except Exception as e:
                logger.warning(f"Hybrid retrieval error: {e}")
                chunks = []
        
        # Single method retrieval
        elif method == RetrievalMethod.VECTOR_ONLY:
            try:
                vector_chunks = await self._vector_retrieve(query, top_k, threshold)
                chunks.extend(vector_chunks)
                logger.info(f"Vector retrieval found {len(vector_chunks)} chunks")
            except Exception as e:
                logger.warning(f"Vector retrieval failed, falling back to BM25: {e}")
                chunks.extend(await self._bm25_retrieve(query, top_k, threshold))
        
        elif method == RetrievalMethod.BM25_ONLY:
            bm25_chunks = await self._bm25_retrieve(query, top_k, threshold)
            chunks.extend(bm25_chunks)
            logger.info(f"BM25 retrieval found {len(bm25_chunks)} chunks")
        
        elif method == RetrievalMethod.MULTI_VECTOR:
            multi_chunks = await self._vector_retrieve(query, top_k, threshold)
            chunks.extend(multi_chunks)
        
        # Post-processing: dedup and re-rank
        chunks = self._deduplicate_chunks(chunks)
        chunks = sorted(chunks, key=lambda x: x.relevance_score, reverse=True)
        chunks = chunks[:top_k]
        
        logger.info(f"Final: {len(chunks)} chunks returned (method: {selected_method.name})")
        
        return RAGContext(
            query=query,
            retrieved_chunks=chunks,
            top_k=top_k,
            similarity_threshold=threshold,
            retrieval_method=selected_method
        )
    
    async def _vector_retrieve(
        self,
        query: str,
        top_k: int,
        threshold: float
    ) -> List[RetrievedChunk]:
        """
        Vector (dense) retrieval using embeddings with fallback.
        
        Retrieves chunks based on semantic similarity
        Falls back to lazy embedding generation if embeddings unavailable
        
        Args:
            query: Query text
            top_k: Number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of retrieved chunks
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            if query_embedding is None or len(query_embedding) == 0:
                logger.warning("Query embedding generation failed")
                return []
            
            # Get chunks from embedding store (not from database)
            # The embedding store now loads all embeddings from disk on init
            scores = []
            chunks = []
            
            if hasattr(self, 'embedding_store') and self.embedding_store:
                # Use embedding store directly
                stored_chunks = await self.embedding_store.search_similar(
                    query_embedding, 
                    top_k=top_k * 2,  # Get more to filter by threshold
                    threshold=threshold
                )
                
                for chunk in stored_chunks:
                    chunks.append(RetrievedChunk(
                        chunk_id=chunk.get("chunk_id"),
                        document_id=chunk.get("document_id", "unknown"),
                        content=chunk.get("content", ""),
                        page_number=None,
                        relevance_score=chunk.get("similarity", 0.0),
                        retrieval_method="vector"
                    ))
                
                logger.info(f"Vector retrieval (from embedding_store) found {len(chunks)} chunks")
            
            # If no embedding store or db_repo exists, return empty
            elif hasattr(self.db_repo, 'select_many'):
                # Legacy: use db_repo if it has database methods
                embeddings_data = await self.db_repo.select_many(
                    "embeddings",
                    limit=1000
                )
                
                # Calculate cosine similarities with fallback for missing embeddings
                scores = []
                for emb_data in embeddings_data:
                    try:
                        # Try to get embedding vector
                        vec_data = emb_data.get("embedding_vector")
                        
                        # Fallback: load from local storage
                        if not vec_data:
                            vec_data = await self._load_embedding_from_storage(
                                emb_data["chunk_id"]
                            )
                        
                        # Last resort: lazy generate
                        if vec_data is None:
                            chunk_data = await self.db_repo.select_one(
                                "document_chunks",
                                {"id": emb_data["chunk_id"]}
                            )
                            if chunk_data:
                                vec_data = await self._generate_embedding_lazy(
                                    chunk_data["chunk_text"],
                                    emb_data["chunk_id"]
                                )
                        
                        if vec_data is None:
                            continue
                        
                        if isinstance(vec_data, list):
                            vec = np.array(vec_data)
                        else:
                            vec = vec_data
                        
                        # Cosine similarity (using utility method)
                        similarity = self._cosine_similarity(query_embedding, vec)
                        
                        if similarity >= threshold:
                            scores.append((emb_data, similarity))
                    except Exception as e:
                        logger.debug(f"Failed to process embedding: {e}")
                        continue
                
                # Sort by similarity and get top_k
                scores.sort(key=lambda x: x[1], reverse=True)
                top_scores = scores[:top_k]
                
                # Load full chunk data
                for emb_data, similarity in top_scores:
                    chunk_data = await self.db_repo.select_one(
                        "document_chunks",
                    {"id": emb_data["chunk_id"]}
                )
                if chunk_data:
                    chunks.append(RetrievedChunk(
                        chunk_id=str(chunk_data["id"]),
                        document_id=str(chunk_data["document_id"]),
                        content=chunk_data["chunk_text"],
                        page_number=chunk_data.get("page_number"),
                        relevance_score=similarity,
                        retrieval_method="vector",
                        document_title=chunk_data.get("document_title")
                    ))
                
                logger.info(f"Vector retrieval (from db_repo) found {len(chunks)} chunks")
            else:
                logger.info("No document database or embedding store available - development mode")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            return []
    
    async def _bm25_retrieve(
        self,
        query: str,
        top_k: int,
        threshold: float
    ) -> List[RetrievedChunk]:
        """
        BM25 (sparse) retrieval using keywords
        
        Retrieves chunks based on keyword matching
        
        Args:
            query: Query text
            top_k: Number of results
            threshold: Minimum score threshold
            
        Returns:
            List of retrieved chunks
        """
        try:
            # Check if we have embedded chunks in embedding_store
            stored_chunks = []
            if hasattr(self, 'embedding_store') and self.embedding_store:
                # Get all chunks from embedding store
                try:
                    # embedding_store.embeddings is a dict of chunk_id -> chunk_data
                    stored_chunks = [
                        {
                            "id": chunk_id,
                            "chunk_text": data.get("content", ""),
                            "document_id": data.get("document_id", "unknown"),
                            "page_number": data.get("page_number")
                        }
                        for chunk_id, data in self.embedding_store.embeddings.items()
                    ]
                except Exception as e:
                    logger.debug(f"Failed to get chunks from embedding_store: {e}")
            elif hasattr(self.db_repo, 'select_many'):
                # Get all chunks from database
                try:
                    stored_chunks = await self.db_repo.select_many(
                        "document_chunks",
                        limit=5000
                    )
                except Exception as e:
                    logger.info(f"No document database available - development mode")
                    return []
            
            if not stored_chunks:
                logger.info("No document database available - development mode")
                return []
            
            # Tokenize query
            query_terms = query.lower().split()
            
            # Calculate average chunk length
            chunk_lengths = [len(c["chunk_text"].split()) for c in stored_chunks]
            avg_chunk_length = np.mean(chunk_lengths) if chunk_lengths else 100
            
            # Score each chunk with BM25
            scores = []
            for chunk in stored_chunks:
                score = self.bm25.score_query(
                    query_terms,
                    chunk["chunk_text"],
                    avg_chunk_length,
                    {},  # Simplified - could precompute doc frequencies
                    len(stored_chunks)
                )
                
                # Normalize score to [0, 1]
                norm_score = min(1.0, max(0.0, score / 10.0))
                
                if norm_score >= threshold:
                    scores.append((chunk, norm_score))
            
            # Sort by score and get top_k
            scores.sort(key=lambda x: x[1], reverse=True)
            top_scores = scores[:top_k]
            
            # Convert to RetrievedChunk
            chunks = [
                RetrievedChunk(
                    chunk_id=str(chunk["id"]),
                    document_id=str(chunk["document_id"]),
                    content=chunk["chunk_text"],
                    page_number=chunk.get("page_number"),
                    relevance_score=score,
                    retrieval_method="bm25",
                    document_title=chunk.get("document_title")
                )
                for chunk, score in top_scores
            ]
            
            return chunks
            
        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}")
            return []
    
    def _deduplicate_chunks(
        self,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """
        Remove duplicate chunks, keeping highest relevance score
        
        Args:
            chunks: List of retrieved chunks (may contain duplicates)
            
        Returns:
            List with duplicates removed
        """
        seen = {}
        for chunk in chunks:
            if chunk.chunk_id not in seen or chunk.relevance_score > seen[chunk.chunk_id].relevance_score:
                seen[chunk.chunk_id] = chunk
        
        return list(seen.values())    
    def _avg_score(self, chunks: List[RetrievedChunk]) -> float:
        """Calculate average relevance score of chunks"""
        if not chunks:
            return 0.0
        return sum(c.relevance_score for c in chunks) / len(chunks)
    
    def _evaluate_chunk_quality(self, chunks: List[RetrievedChunk]) -> float:
        """
        Evaluate overall quality of retrieved chunks using multiple metrics
        
        Returns: Quality score 0.0-1.0 combining:
        - Average relevance score (semantic confidence)
        - Number of strong matches (above 0.5 threshold)
        - Diversity of results
        """
        if not chunks:
            return 0.0
        
        # Metric 1: Average relevance score (0-1)
        avg_score = self._avg_score(chunks)
        
        # Metric 2: Strength diversity (count strong matches)
        strong_matches = sum(1 for c in chunks if c.relevance_score > 0.5)
        strength_ratio = min(strong_matches / len(chunks), 1.0) if chunks else 0.0
        
        # Metric 3: Result count (more results = more coverage)
        count_bonus = min(len(chunks) / 10, 1.0)  # Max bonus at 10+ results
        
        # Weighted combination (higher average is most important)
        quality_score = (avg_score * 0.6) + (strength_ratio * 0.2) + (count_bonus * 0.2)
        
        return quality_score