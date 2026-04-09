"""
FarmGrow Ranking Service
Reranks retrieved documents using multiple relevance signals

Multi-Signal Reranking:
1. Semantic relevance (embedding similarity)
2. Keyword relevance (BM25 score)
3. Document quality (user ratings, authority)
4. Recency (freshness of information)
5. User interaction history (relevance for this user)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class RankingSignal:
    """A single ranking signal component"""
    name: str
    score: float
    weight: float
    description: str = ""


class DocumentRanker:
    """
    Multi-signal Document Ranker
    
    Combines multiple relevance signals for improved ranking:
    
    Final Score = Σ (signal_score * signal_weight)
    Where signals include:
    - Semantic similarity (density from embeddings)
    - Keyword relevance (BM25 score)  
    - Document authority (ratings, citations, trust)
    - Recency/freshness (publication date, update date)
    - User history (if available)
    
    Attributes:
        signal_weights: Weight for each ranking signal
        base_weights: Default signal weights
    """
    
    def __init__(
        self,
        semantic_weight: float = 0.35,
        keyword_weight: float = 0.25,
        authority_weight: float = 0.20,
        recency_weight: float = 0.15,
        user_history_weight: float = 0.05
    ):
        """
        Initialize document ranker with signal weights
        
        Weights should sum to ~1.0
        
        Args:
            semantic_weight: Weight for embedding similarity
            keyword_weight: Weight for BM25 score
            authority_weight: Weight for document authority (rating, relevance)
            recency_weight: Weight for document freshness
            user_history_weight: Weight for user interaction signals
        """
        self.base_weights = {
            "semantic": semantic_weight,
            "keyword": keyword_weight,
            "authority": authority_weight,
            "recency": recency_weight,
            "user_history": user_history_weight
        }
        
        # Validate weights sum to approximately 1.0
        total_weight = sum(self.base_weights.values())
        if not 0.95 <= total_weight <= 1.05:
            logger.warning(f"Ranking weights sum to {total_weight}, not 1.0")
        
        logger.info(f"Initialized DocumentRanker with weights: {self.base_weights}")
    
    async def rerank(
        self,
        chunks: List,
        query: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List:
        """
        Rerank chunks using multiple signals
        
        Args:
            chunks: Retrieved chunks with relevance_score
            query: Original query for context
            user_id: User ID for personalization
            context: Additional context (e.g., user preferences)
            
        Returns:
            Reranked chunks sorted by final score
        """
        reranked = []
        
        for chunk in chunks:
            signals = []
            
            # Signal 1: Semantic similarity (embeddings)
            semantic_signal = RankingSignal(
                name="semantic",
                score=self._normalize_score(
                    chunk.relevance_score if chunk.retrieval_method == "vector" else 0.5,
                    0.0, 1.0
                ),
                weight=self.base_weights["semantic"],
                description="Embedding cosine similarity"
            )
            signals.append(semantic_signal)
            
            # Signal 2: Keyword relevance (BM25)
            keyword_score = chunk.relevance_score if chunk.retrieval_method == "bm25" else 0.5
            keyword_signal = RankingSignal(
                name="keyword",
                score=self._normalize_score(keyword_score, 0.0, 1.0),
                weight=self.base_weights["keyword"],
                description="BM25 keyword matching"
            )
            signals.append(keyword_signal)
            
            # Signal 3: Document authority
            authority_score = await self._calculate_authority_score(chunk)
            authority_signal = RankingSignal(
                name="authority",
                score=authority_score,
                weight=self.base_weights["authority"],
                description="Document authority and quality"
            )
            signals.append(authority_signal)
            
            # Signal 4: Recency
            recency_score = await self._calculate_recency_score(chunk)
            recency_signal = RankingSignal(
                name="recency",
                score=recency_score,
                weight=self.base_weights["recency"],
                description="Document freshness/recency"
            )
            signals.append(recency_signal)
            
            # Signal 5: User history (if available)
            user_history_score = await self._calculate_user_history_score(chunk, user_id)
            user_history_signal = RankingSignal(
                name="user_history",
                score=user_history_score,
                weight=self.base_weights["user_history"],
                description="User interaction history"
            )
            signals.append(user_history_signal)
            
            # Calculate final score as weighted sum
            final_score = sum(sig.score * sig.weight for sig in signals)
            
            # Attach signals and final score to chunk
            chunk.ranking_signals = signals
            chunk.final_ranking_score = final_score
            
            reranked.append(chunk)
        
        # Sort by final score (descending)
        reranked.sort(key=lambda x: x.final_ranking_score, reverse=True)
        
        logger.info(f"Reranked {len(reranked)} chunks, top score: {reranked[0].final_ranking_score:.3f}" if reranked else "No chunks to rerank")
        
        return reranked
    
    async def _calculate_authority_score(self, chunk) -> float:
        """
        Calculate document authority score (0-1)
        
        Combines:
        - User ratings (average rating / 5)
        - Citation count (normalized)
        - Document trust level
        - Category relevance
        
        Args:
            chunk: Document chunk with metadata
            
        Returns:
            Authority score 0-1
        """
        score = 0.5  # Base score
        
        # User ratings (if available)
        if hasattr(chunk, "user_rating") and chunk.user_rating:
            rating_score = chunk.user_rating / 5.0  # Normalize to 0-1
            score = 0.7 * score + 0.3 * rating_score
        
        # Document category authority
        if hasattr(chunk, "document_category") and chunk.document_category:
            category_weights = {
                "official": 1.0,
                "agricultural_extension": 0.95,
                "research": 0.90,
                "guide": 0.75,
                "blog": 0.50,
                "user_generated": 0.40
            }
            category_score = category_weights.get(chunk.document_category.lower(), 0.5)
            score = 0.8 * score + 0.2 * category_score
        
        return min(1.0, max(0.0, score))
    
    async def _calculate_recency_score(self, chunk) -> float:
        """
        Calculate recency/freshness score (0-1)
        
        Documents from the last 6 months are fresher
        Very old documents (>5 years) get lower scores
        
        Args:
            chunk: Document chunk with metadata
            
        Returns:
            Recency score 0-1
        """
        if not hasattr(chunk, "created_at") or not chunk.created_at:
            return 0.5  # Neutral score if no date
        
        try:
            doc_date = chunk.created_at
            if isinstance(doc_date, str):
                # Parse ISO format date
                doc_date = datetime.fromisoformat(doc_date.replace("Z", "+00:00"))
            
            current_date = datetime.now(doc_date.tzinfo) if doc_date.tzinfo else datetime.now()
            days_old = (current_date - doc_date).days
            
            # Score function: Fresh (0 days) = 1.0, older = decreases
            # 30 days = 0.95, 180 days = 0.70, 365 days = 0.50, 1825 days (5y) = 0.10
            if days_old < 0:
                return 1.0  # Future date (shouldn't happen)
            elif days_old < 30:
                return 1.0
            elif days_old < 180:
                return max(0.7, 1.0 - (days_old / 180) * 0.3)
            elif days_old < 365:
                return max(0.5, 0.7 - (days_old - 180) / 185 * 0.2)
            elif days_old < 1825:  # 5 years
                return max(0.1, 0.5 - (days_old - 365) / 1460 * 0.4)
            else:
                return 0.1  # Very old
                
        except Exception as e:
            logger.error(f"Error calculating recency score: {e}")
            return 0.5
    
    async def _calculate_user_history_score(
        self,
        chunk,
        user_id: Optional[str] = None
    ) -> float:
        """
        Calculate user interaction history score (0-1)
        
        Factors:
        - Documents user has previously liked
        - Documents similar to user's past queries
        - Documents from user's preferred categories
        
        Args:
            chunk: Document chunk
            user_id: User ID for history lookup
            
        Returns:
            User history score 0-1
        """
        if not user_id:
            return 0.0  # No personalization without user ID
        
        # In a real system, would query user interaction history
        # For now, return neutral score
        # Example: could be 0.8 if user previously rated similar documents highly
        
        base_score = 0.5
        
        # Could enhance with:
        # - User preference profiles
        # - Similar documents user engaged with
        # - User query history patterns
        
        return base_score
    
    def _normalize_score(
        self,
        value: float,
        min_val: float = 0.0,
        max_val: float = 1.0
    ) -> float:
        """
        Normalize score to [0, 1] range
        
        Args:
            value: Raw score value
            min_val: Minimum expected value
            max_val: Maximum expected value
            
        Returns:
            Normalized score in [0, 1]
        """
        if max_val == min_val:
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        return min(1.0, max(0.0, normalized))
    
    def get_ranking_explanation(self, chunk) -> str:
        """
        Generate human-readable explanation of ranking
        
        Args:
            chunk: Ranked chunk with signals
            
        Returns:
            Description of ranking factors
        """
        if not hasattr(chunk, "ranking_signals"):
            return "No ranking explanation available"
        
        explanation_parts = []
        for signal in chunk.ranking_signals:
            percent = signal.score * 100
            explanation_parts.append(
                f"{signal.name.title()}: {percent:.0f}% (weight: {signal.weight:.0%})"
            )
        
        final = getattr(chunk, "final_ranking_score", 0) * 100
        explanation = " | ".join(explanation_parts)
        explanation += f" → Final: {final:.0f}%"
        
        return explanation
