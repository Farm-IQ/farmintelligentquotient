"""
Cortex AI Tracking Helpers

Helper functions and decorators to easily integrate Cortex tracking into FastAPI endpoints.
Simplifies request tracking, metric recording, and analytics across FarmGrow, FarmScore, FarmSuite.

Features:
- Automatic timing and error tracking
- Token usage recording
- Cross-app request correlation support
- Minimal endpoint code changes required
"""

from functools import wraps
from typing import Optional, Dict, Any, Callable, List
import time
import logging
from contextlib import asynccontextmanager

from core.cortex import Cortex, AISystem, RequestType, RequestStatus, AIToken, AIMetrics

logger = logging.getLogger(__name__)


# ============================================================================
# DECORATORS FOR ENDPOINTS
# ============================================================================

def track_ai_request_endpoint(
    system: AISystem,
    request_type: RequestType,
    extract_user_id: Optional[Callable] = None,
    extract_farm_id: Optional[Callable] = None,
    extract_tokens: Optional[Callable] = None,
):
    """
    Decorator to automatically track AI requests in FastAPI endpoints.
    
    Usage:
    ```python
    @track_ai_request_endpoint(
        system=AISystem.FARMGROW,
        request_type=RequestType.RAG_QUERY,
        extract_user_id=lambda request: request.user_id,
        extract_farm_id=lambda request: getattr(request, 'farm_id', None)
    )
    async def query_endpoint(request: RAGQueryRequest, user: Dict):
        # Your endpoint logic
        return response
    ```
    
    Args:
        system: Which AI platform (FARMGROW, FARMSCORE, FARMSUITE)
        request_type: Type of request (RAG_QUERY, ML_YIELD_PREDICTION, etc.)
        extract_user_id: Function to extract user_id from request
        extract_farm_id: Function to extract farm_id from request
        extract_tokens: Function to extract token info from response
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            request_id = None
            error = None
            
            try:
                # Extract context info
                # Try to find the request object in args/kwargs
                request_obj = None
                user_obj = None
                
                # Look for a parameter named 'request' or the first BaseModel arg
                for arg in args:
                    if hasattr(arg, '__class__') and hasattr(arg.__class__, '__mro__'):
                        if 'BaseModel' in [c.__name__ for c in arg.__class__.__mro__]:
                            request_obj = arg
                            break
                
                for key, val in kwargs.items():
                    if key == 'request' or key == 'user':
                        if hasattr(val, '__class__') and hasattr(val.__class__, '__mro__'):
                            if 'BaseModel' in [c.__name__ for c in val.__class__.__mro__] or isinstance(val, dict):
                                if key == 'request':
                                    request_obj = val
                                elif key == 'user':
                                    user_obj = val
                
                # Extract user_id and farm_id
                user_id = None
                farm_id = None
                
                if extract_user_id:
                    try:
                        user_id = extract_user_id(request_obj or kwargs.get('request') or user_obj or kwargs.get('user'))
                    except:
                        pass
                
                if extract_farm_id:
                    try:
                        farm_id = extract_farm_id(request_obj or kwargs.get('request'))
                    except:
                        pass
                
                # Create tracked request
                request_id = Cortex.create_request(
                    system=system,
                    request_type=request_type,
                    user_id=user_id,
                    farm_id=farm_id
                )
                
                logger.debug(f"Tracking request {request_id} ({system.value}/{request_type.value})")
                
                # Execute endpoint
                response = await func(*args, **kwargs)
                
                # Calculate metrics
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Try to extract tokens if provided
                tokens = None
                if extract_tokens:
                    try:
                        tokens = extract_tokens(response)
                    except:
                        pass
                
                # Record success
                Cortex.update_metrics(
                    request_id=request_id,
                    status=RequestStatus.COMPLETED,
                    duration_ms=duration_ms,
                    tokens=tokens,
                    cache_hit=False
                )
                
                logger.debug(f"Request {request_id} completed in {duration_ms}ms")
                
                return response
                
            except Exception as e:
                error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Record failure
                if request_id:
                    Cortex.update_metrics(
                        request_id=request_id,
                        status=RequestStatus.FAILED,
                        duration_ms=duration_ms,
                        error_message=error
                    )
                
                logger.error(f"Request {request_id} failed: {error}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Fallback for sync endpoints (shouldn't normally happen in FastAPI)
            start_time = time.time()
            request_id = None
            
            try:
                request_id = Cortex.create_request(
                    system=system,
                    request_type=request_type
                )
                
                response = func(*args, **kwargs)
                
                duration_ms = int((time.time() - start_time) * 1000)
                Cortex.update_metrics(
                    request_id=request_id,
                    status=RequestStatus.COMPLETED,
                    duration_ms=duration_ms
                )
                
                return response
                
            except Exception as e:
                if request_id:
                    Cortex.update_metrics(
                        request_id=request_id,
                        status=RequestStatus.FAILED,
                        duration_ms=int((time.time() - start_time) * 1000),
                        error_message=str(e)
                    )
                raise
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================================================
# CONTEXT MANAGERS FOR MANUAL TRACKING
# ============================================================================

@asynccontextmanager
async def cortex_track(
    system: AISystem,
    request_type: RequestType,
    user_id: Optional[str] = None,
    farm_id: Optional[str] = None,
    cache_hit: bool = False,
):
    """
    Async context manager for manual Cortex tracking within endpoints.
    
    Usage:
    ```python
    async def my_endpoint(request: MyRequest):
        async with cortex_track(
            system=AISystem.FARMGROW,
            request_type=RequestType.RAG_QUERY,
            user_id=request.user_id,
            farm_id=request.farm_id
        ) as tracker:
            # Your logic here
            result = await process_request(request)
            # Optionally record tokens
            tracker.record_tokens(
                input_tokens=100,
                output_tokens=250,
                model="mistral:7b"
            )
    ```
    """
    start_time = time.time()
    request_id = Cortex.create_request(
        system=system,
        request_type=request_type,
        user_id=user_id,
        farm_id=farm_id
    )
    
    class RequestTracker:
        def __init__(self, req_id: str):
            self.request_id = req_id
            self.tokens_info = None
        
        def record_tokens(
            self,
            input_tokens: int,
            output_tokens: int,
            model: str,
            cost_usd: Optional[float] = None
        ):
            """Record token usage for the request"""
            self.tokens_info = AIToken(
                system=system,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd or 0.0
            )
        
        def finish(self, status: RequestStatus = RequestStatus.COMPLETED, error_message: Optional[str] = None):
            """Manually finish the request tracking"""
            duration_ms = int((time.time() - start_time) * 1000)
            Cortex.update_metrics(
                request_id=request_id,
                status=status,
                duration_ms=duration_ms,
                tokens=self.tokens_info,
                cache_hit=cache_hit,
                error_message=error_message
            )
    
    tracker = RequestTracker(request_id)
    
    try:
        yield tracker
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        Cortex.update_metrics(
            request_id=request_id,
            status=RequestStatus.FAILED,
            duration_ms=duration_ms,
            error_message=str(e)
        )
        raise
    else:
        # If no error and finish wasn't explicitly called
        if tracker.tokens_info or not hasattr(tracker, '_finished'):
            duration_ms = int((time.time() - start_time) * 1000)
            Cortex.update_metrics(
                request_id=request_id,
                status=RequestStatus.COMPLETED,
                duration_ms=duration_ms,
                tokens=tracker.tokens_info,
                cache_hit=cache_hit
            )


# ============================================================================
# ANALYTICS HELPERS
# ============================================================================

def get_system_analytics(system: AISystem) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a specific AI system.
    
    Usage:
    ```python
    @router.get("/dashboard")
    async def dashboard():
        farmgrow_stats = get_system_analytics(AISystem.FARMGROW)
        return {"farmgrow": farmgrow_stats}
    ```
    """
    stats = Cortex.get_system_stats(system)
    return {
        "system": system.value,
        "total_requests": stats.get("total_requests", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "success_rate": stats.get("success_rate", 0),
        "avg_duration_ms": stats.get("avg_duration_ms", 0),
        "total_tokens": stats.get("total_tokens", 0),
        "total_cost_usd": stats.get("total_cost_usd", 0),
        "cache_hit_rate": stats.get("cache_hit_rate", 0),
    }


def get_cross_system_analytics() -> Dict[str, Any]:
    """
    Get analytics showing interactions between all AI systems.
    
    Usage:
    ```python
    @router.get("/intelligence/analytics")
    async def cross_system_analytics():
        return get_cross_system_analytics()
    ```
    """
    patterns = Cortex.get_cross_system_patterns()
    costs = Cortex.get_cost_breakdown()
    
    return {
        "total_requests": patterns.get("total_requests", 0),
        "request_types": patterns.get("request_types", {}),
        "system_interactions": patterns.get("system_interactions", {}),
        "per_system_stats": patterns.get("per_system_stats", {}),
        "cost_breakdown": costs,
        "timestamp": patterns.get("timestamp"),
    }


def get_user_activity_analytics(user_id: str) -> Dict[str, Any]:
    """
    Get analytics for a specific user's AI interactions.
    
    Usage:
    ```python
    @router.get("/user/{user_id}/analytics")
    async def user_analytics(user_id: str):
        return get_user_activity_analytics(user_id)
    ```
    """
    history = Cortex.get_user_history(user_id)
    
    # Calculate stats from history
    total_requests = len(history)
    completed = sum(1 for req in history if req.status == RequestStatus.COMPLETED)
    failed = sum(1 for req in history if req.status == RequestStatus.FAILED)
    
    # Group by system
    by_system = {}
    for req in history:
        system = req.system.value
        if system not in by_system:
            by_system[system] = 0
        by_system[system] += 1
    
    # Group by type
    by_type = {}
    for req in history:
        req_type = req.request_type.value
        if req_type not in by_type:
            by_type[req_type] = 0
        by_type[req_type] += 1
    
    return {
        "user_id": user_id,
        "total_requests": total_requests,
        "completed": completed,
        "failed": failed,
        "success_rate": (completed / total_requests * 100) if total_requests > 0 else 0,
        "by_system": by_system,
        "by_request_type": by_type,
    }


def get_farm_activity_analytics(farm_id: str) -> Dict[str, Any]:
    """
    Get analytics for a specific farm's AI interactions.
    
    Usage:
    ```python
    @router.get("/farm/{farm_id}/activity")
    async def farm_activity(farm_id: str):
        return get_farm_activity_analytics(farm_id)
    ```
    """
    history = Cortex.get_farm_activity(farm_id)
    
    # Calculate stats from history
    total_requests = len(history)
    completed = sum(1 for req in history if req.status == RequestStatus.COMPLETED)
    failed = sum(1 for req in history if req.status == RequestStatus.FAILED)
    
    # Group by system
    by_system = {}
    for req in history:
        system = req.system.value
        if system not in by_system:
            by_system[system] = 0
        by_system[system] += 1
    
    return {
        "farm_id": farm_id,
        "total_requests": total_requests,
        "completed": completed,
        "failed": failed,
        "success_rate": (completed / total_requests * 100) if total_requests > 0 else 0,
        "by_system": by_system,
        "recent_requests": [
            {
                "request_id": req.request_id,
                "system": req.system.value,
                "type": req.request_type.value,
                "status": req.status.value,
                "timestamp": req.timestamp.isoformat() if hasattr(req.timestamp, 'isoformat') else str(req.timestamp),
            }
            for req in history[-10:]  # Last 10 requests
        ],
    }


def correlate_requests(request_ids: List[str]) -> str:
    """
    Correlate multiple requests as related (e.g., FarmGrow query → FarmScore prediction → FarmSuite synthesis).
    
    Usage:
    ```python
    # After executing operations across systems
    correlation_id = correlate_requests([
        farmgrow_request_id,
        farmscore_request_id,
        farmsuite_request_id
    ])
    ```
    """
    Cortex.correlate_requests(request_ids)
    return request_ids[0]  # Return first request ID as correlation ID


__all__ = [
    "track_ai_request_endpoint",
    "cortex_track",
    "get_system_analytics",
    "get_cross_system_analytics",
    "get_user_activity_analytics",
    "get_farm_activity_analytics",
    "correlate_requests",
]
