"""
Cortex AI Tracking & Monitoring System (Phase 5.4 - Intelligence Hub)
Central intelligence hub for tracking, monitoring, and coordinating FarmGrow (RAG), FarmScore (ML), and FarmSuite (Intelligence)

Cortex provides:
- Unified AI request tracking across all three platforms
- Cross-app intelligence coordination
- AI usage analytics and cost tracking
- Model performance monitoring
- Request correlation and tracing
- Intelligence aggregation from all three AI systems
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import json
import uuid
import logging
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class AISystem(str, Enum):
    """Supported AI systems in FarmIQ"""
    FARMGROW = "farmgrow"      # RAG-based document retrieval + LLM
    FARMSCORE = "farmscore"    # ML prediction models
    FARMSUITE = "farmsuite"    # Intelligence aggregation


class RequestType(str, Enum):
    """Types of AI requests"""
    RAG_QUERY = "rag_query"                    # FarmGrow: Document retrieval + generation
    RAG_CHAT = "rag_chat"                      # FarmGrow: Multi-turn chat
    RAG_SEARCH = "rag_search"                  # FarmGrow: Semantic search
    ML_YIELD_PREDICTION = "ml_yield"           # FarmScore: Yield prediction
    ML_EXPENSE_FORECAST = "ml_expense"         # FarmScore: Expense forecasting
    ML_DISEASE_CLASSIFY = "ml_disease"         # FarmScore: Disease classification
    ML_MARKET_PREDICT = "ml_market"            # FarmScore: Market prediction
    INTELLIGENCE_AGGREGATE = "intelligence"    # FarmSuite: Multi-AI synthesis
    INTELLIGENCE_DASHBOARD = "dashboard"       # FarmSuite: Dashboard generation


class RequestStatus(str, Enum):
    """AI request status"""
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AIToken:
    """Token usage tracking for LLM/embedding APIs"""
    system: AISystem
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = field(init=False)
    cost_usd: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class AIMetrics:
    """Performance metrics for a single AI request"""
    system: AISystem
    request_type: RequestType
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: RequestStatus = RequestStatus.INITIATED
    tokens: Optional[AIToken] = None
    input_size: int = 0      # Query/input size in bytes
    output_size: int = 0     # Response size in bytes
    cache_hit: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'system': self.system.value,
            'request_type': self.request_type.value,
            'status': self.status.value,
            'duration_ms': self.duration_ms,
            'tokens': asdict(self.tokens) if self.tokens else None,
            'cache_hit': self.cache_hit,
            'timestamp': self.start_time.isoformat(),
        }


@dataclass
class AIRequest:
    """Unified AI request tracking across all three systems"""
    request_id: str
    system: AISystem
    request_type: RequestType
    user_id: str
    farm_id: Optional[str] = None
    correlations: Set[str] = field(default_factory=set)  # Related request IDs
    metrics: AIMetrics = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'system': self.system.value,
            'request_type': self.request_type.value,
            'user_id': self.user_id,
            'farm_id': self.farm_id,
            'correlations': list(self.correlations),
            'metrics': self.metrics.to_dict() if isinstance(self.metrics, AIMetrics) else self.metrics,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


# ============================================================================
# CORTEX CENTRAL HUB
# ============================================================================

class Cortex:
    """
    Central Intelligence Hub for FarmIQ
    
    Tracks and coordinates all AI requests across FarmGrow, FarmScore, and FarmSuite
    Provides real-time analytics, cost tracking, and intelligence aggregation
    """
    
    # Request tracking
    _requests: Dict[str, AIRequest] = {}
    _user_requests: Dict[str, List[str]] = defaultdict(list)
    _farm_requests: Dict[str, List[str]] = defaultdict(list)
    _system_requests: Dict[AISystem, List[str]] = defaultdict(list)
    
    # Analytics
    _metrics_store: List[AIMetrics] = []
    _tokens_store: List[AIToken] = []
    
    # Configuration
    _max_requests_stored = 10000
    _max_metrics_stored = 50000
    
    @classmethod
    def create_request(
        cls,
        system: AISystem,
        request_type: RequestType,
        user_id: str,
        farm_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new AI request and return its tracking ID
        
        Args:
            system: Which AI system (FarmGrow, FarmScore, FarmSuite)
            request_type: Type of request (query, prediction, etc.)
            user_id: FarmIQ user ID making the request
            farm_id: Optional farm context
            metadata: Optional request metadata
        
        Returns:
            request_id for tracking this request
        """
        request_id = str(uuid.uuid4())
        
        request = AIRequest(
            request_id=request_id,
            system=system,
            request_type=request_type,
            user_id=user_id,
            farm_id=farm_id,
            metadata=metadata or {},
            metrics=AIMetrics(
                system=system,
                request_type=request_type,
                start_time=datetime.utcnow(),
            )
        )
        
        # Store request
        cls._requests[request_id] = request
        cls._user_requests[user_id].append(request_id)
        if farm_id:
            cls._farm_requests[farm_id].append(request_id)
        cls._system_requests[system].append(request_id)
        
        logger.info(
            f"🧠 Cortex: New {system.value} request",
            extra={
                'request_id': request_id,
                'request_type': request_type.value,
                'user_id': user_id,
                'farm_id': farm_id,
            }
        )
        
        return request_id
    
    @classmethod
    def update_metrics(
        cls,
        request_id: str,
        status: RequestStatus,
        duration_ms: float,
        tokens: Optional[AIToken] = None,
        input_size: int = 0,
        output_size: int = 0,
        cache_hit: bool = False,
        error_message: Optional[str] = None,
    ):
        """Update metrics for a request as it progresses"""
        if request_id not in cls._requests:
            logger.warning(f"Request {request_id} not found in Cortex")
            return
        
        request = cls._requests[request_id]
        request.metrics.status = status
        request.metrics.end_time = datetime.utcnow()
        request.metrics.duration_ms = duration_ms
        request.metrics.input_size = input_size
        request.metrics.output_size = output_size
        request.metrics.cache_hit = cache_hit
        request.metrics.error_message = error_message
        
        if tokens:
            request.metrics.tokens = tokens
            cls._tokens_store.append(tokens)
        
        if status == RequestStatus.COMPLETED:
            request.completed_at = datetime.utcnow()
        
        cls._metrics_store.append(request.metrics)
    
    @classmethod
    def correlate_requests(cls, request_ids: List[str]):
        """
        Correlate multiple AI requests (e.g., FarmGrow query → FarmScore prediction → FarmSuite synthesis)
        
        Marks all requests in the list as related to each other
        """
        request_id_set = set(request_ids)
        for req_id in request_ids:
            if req_id in cls._requests:
                cls._requests[req_id].correlations = request_id_set - {req_id}
    
    @classmethod
    def get_request(cls, request_id: str) -> Optional[AIRequest]:
        """Get a specific request"""
        return cls._requests.get(request_id)
    
    @classmethod
    def get_user_history(cls, user_id: str, limit: int = 100) -> List[AIRequest]:
        """Get AI request history for a user"""
        request_ids = cls._user_requests[user_id][-limit:]
        return [cls._requests[rid] for rid in request_ids if rid in cls._requests]
    
    @classmethod
    def get_farm_activity(cls, farm_id: str, limit: int = 100) -> List[AIRequest]:
        """Get AI activity for a specific farm"""
        request_ids = cls._farm_requests[farm_id][-limit:]
        return [cls._requests[rid] for rid in request_ids if rid in cls._requests]
    
    @classmethod
    def get_system_requests(cls, system: AISystem, limit: int = 100) -> List[AIRequest]:
        """Get recent requests for a specific AI system"""
        request_ids = cls._system_requests[system][-limit:]
        return [cls._requests[rid] for rid in request_ids if rid in cls._requests]
    
    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================
    
    @classmethod
    def get_system_stats(cls, system: Optional[AISystem] = None) -> Dict[str, Any]:
        """Get statistics for one or all AI systems"""
        if system:
            metrics = [m for m in cls._metrics_store if m.system == system]
        else:
            metrics = cls._metrics_store
        
        if not metrics:
            return {'total_requests': 0}
        
        completed = [m for m in metrics if m.status == RequestStatus.COMPLETED]
        failed = [m for m in metrics if m.status == RequestStatus.FAILED]
        
        total_duration = sum(m.duration_ms for m in metrics)
        total_tokens = sum(t.total_tokens for t in cls._tokens_store)
        total_cost = sum(t.cost_usd for t in cls._tokens_store)
        
        return {
            'system': system.value if system else 'all',
            'total_requests': len(metrics),
            'completed': len(completed),
            'failed': len(failed),
            'success_rate': len(completed) / len(metrics) * 100 if metrics else 0,
            'avg_duration_ms': total_duration / len(metrics) if metrics else 0,
            'total_duration_ms': total_duration,
            'total_tokens': total_tokens,
            'total_cost_usd': total_cost,
            'cache_hit_rate': (
                sum(1 for m in metrics if m.cache_hit) / len(metrics) * 100
                if metrics else 0
            ),
        }
    
    @classmethod
    def get_cross_system_patterns(cls) -> Dict[str, Any]:
        """
        Analyze patterns across all three AI systems
        
        Returns insights on how FarmGrow, FarmScore, and FarmSuite interact
        """
        # Find correlated requests
        correlations = defaultdict(int)
        for request in cls._requests.values():
            if request.correlations:
                system_combo = tuple(sorted([
                    request.system.value,
                    *[cls._requests[cid].system.value for cid in request.correlations if cid in cls._requests]
                ]))
                correlations[system_combo] += 1
        
        return {
            'total_requests': len(cls._requests),
            'total_metrics': len(cls._metrics_store),
            'total_tokens': sum(t.total_tokens for t in cls._tokens_store),
            'total_cost_usd': sum(t.cost_usd for t in cls._tokens_store),
            'system_interactions': dict(correlations),
            'farmgrow_stats': cls.get_system_stats(AISystem.FARMGROW),
            'farmscore_stats': cls.get_system_stats(AISystem.FARMSCORE),
            'farmsuite_stats': cls.get_system_stats(AISystem.FARMSUITE),
        }
    
    @classmethod
    def get_cost_breakdown(cls) -> Dict[str, float]:
        """Get cost breakdown by system"""
        cost_by_system = defaultdict(float)
        for token in cls._tokens_store:
            cost_by_system[token.system.value] += token.cost_usd
        
        return dict(cost_by_system)
    
    @classmethod
    def get_performance_timeline(cls, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics over time"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        recent_metrics = [
            m for m in cls._metrics_store
            if m.start_time.timestamp() >= cutoff
        ]
        
        # Group by hour
        timeline = defaultdict(lambda: {
            'requests': 0,
            'avg_duration_ms': 0,
            'total_duration_ms': 0,
            'errors': 0,
        })
        
        for metric in recent_metrics:
            hour_key = metric.start_time.strftime('%Y-%m-%d %H:00')
            timeline[hour_key]['requests'] += 1
            timeline[hour_key]['total_duration_ms'] += metric.duration_ms
            if metric.status == RequestStatus.FAILED:
                timeline[hour_key]['errors'] += 1
        
        # Calculate averages
        for hour_key, stats in timeline.items():
            if stats['requests'] > 0:
                stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['requests']
        
        return dict(timeline)
    
    @classmethod
    def export_analytics(cls) -> str:
        """Export all analytics as JSON"""
        return json.dumps(
            {
                'timestamp': datetime.utcnow().isoformat(),
                'cross_system_patterns': cls.get_cross_system_patterns(),
                'cost_breakdown': cls.get_cost_breakdown(),
                'performance_timeline': cls.get_performance_timeline(),
            },
            indent=2,
            default=str,
        )
    
    @classmethod
    def cleanup(cls, max_age_hours: int = 24):
        """
        Clean up old request records to prevent memory issues
        
        Keeps only recent requests for stateful tracking
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        # Clean requests
        old_requests = [
            rid for rid, req in cls._requests.items()
            if req.created_at.timestamp() < cutoff
        ]
        
        for rid in old_requests:
            del cls._requests[rid]
        
        # Clean metrics
        cls._metrics_store = [m for m in cls._metrics_store if m.start_time.timestamp() >= cutoff]
        
        # Clean tokens
        cls._tokens_store = [t for t in cls._tokens_store if t.timestamp.timestamp() >= cutoff]
        
        logger.info(f"🧠 Cortex cleanup: removed {len(old_requests)} old requests")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def track_ai_request(
    system: AISystem,
    request_type: RequestType,
    user_id: str,
    farm_id: Optional[str] = None,
):
    """
    Context manager for tracking AI requests
    
    Usage:
        async with track_ai_request(AISystem.FARMGROW, RequestType.RAG_QUERY, user_id) as tracker:
            result = await farmgrow_service.query(tracker.request_id)
            tracker.record(duration_ms=150, tokens=tokens_used, cache_hit=True)
    """
    class RequestTracker:
        def __init__(self, request_id: str):
            self.request_id = request_id
        
        def record(
            self,
            duration_ms: float,
            tokens: Optional[AIToken] = None,
            input_size: int = 0,
            output_size: int = 0,
            cache_hit: bool = False,
            error: Optional[str] = None,
        ):
            status = RequestStatus.FAILED if error else RequestStatus.COMPLETED
            Cortex.update_metrics(
                self.request_id,
                status=status,
                duration_ms=duration_ms,
                tokens=tokens,
                input_size=input_size,
                output_size=output_size,
                cache_hit=cache_hit,
                error_message=error,
            )
    
    request_id = Cortex.create_request(system, request_type, user_id, farm_id)
    return RequestTracker(request_id)
