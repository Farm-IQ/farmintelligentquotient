"""
FarmGrow RAG - Resilience Patterns
Circuit breaker, retry logic, and failover strategies for external service calls
"""
import asyncio
import logging
from typing import Callable, Any, Optional, TypeVar, Coroutine
from datetime import datetime, timedelta
from enum import Enum
import functools

from app.farmgrow.exceptions import (
    CircuitBreakerOpenError,
    RetryExhaustedError,
    ServiceUnavailableError,
    OllamaConnectionError,
    OllamaTimeoutError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Working normally
    OPEN = "open"              # Failing, rejecting requests
    HALF_OPEN = "half_open"    # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation
    
    Prevents cascading failures by failing fast when service is down
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests rejected immediately
    - HALF_OPEN: Testing if service recovered, allow probe requests
    """
    
    def __init__(self,
                 name: str,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        """
        Initialize circuit breaker
        
        Args:
            name: Circuit breaker name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying to recover
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"🔌 Circuit breaker '{name}' initialized (threshold={failure_threshold}, timeout={recovery_timeout}s)")
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔌 Circuit breaker '{self.name}' entering HALF_OPEN (probing)")
            else:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry in {self.recovery_timeout - int(elapsed)}s",
                    code="CIRCUIT_BREAKER_OPEN"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def acall(self, func: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs) -> T:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔌 Circuit breaker '{self.name}' entering HALF_OPEN (probing)")
            else:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry in {self.recovery_timeout - int(elapsed)}s",
                    code="CIRCUIT_BREAKER_OPEN"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"✅ Circuit breaker '{self.name}' CLOSED (service recovered)")
        else:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        logger.warning(f"⚠️  Circuit breaker '{self.name}' failure #{self.failure_count}/{self.failure_threshold}")
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"❌ Circuit breaker '{self.name}' OPEN (failures exceeded)")
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryStrategy:
    """
    Retry strategy with exponential backoff
    
    Features:
    - Exponential backoff (configurable base & multiplier)
    - Jitter to avoid thundering herd
    - Max retry attempts
    - Configurable exception types
    """
    
    def __init__(self,
                 max_attempts: int = 3,
                 base_delay: float = 0.5,
                 max_delay: float = 30.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry strategy
        
        Args:
            max_attempts: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay cap
            exponential_base: Exponential backoff multiplier
            jitter: Add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt
        
        Exponential backoff: delay = min(base * (exponential_base ^ attempt), max_delay)
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            import random
            jitter = random.uniform(0, delay * 0.1)  # 10% jitter
            delay += jitter
        
        return delay
    
    def retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhaustedError: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = self.get_delay(attempt)
                    logger.warning(f"⚠️  Retry {attempt + 1}/{self.max_attempts} after {delay:.2f}s: {str(e)}")
                    asyncio.sleep(delay)
                else:
                    logger.error(f"❌ All {self.max_attempts} retries exhausted: {str(e)}")
        
        raise RetryExhaustedError(
            f"Failed after {self.max_attempts} attempts: {str(last_exception)}",
            code="RETRY_EXHAUSTED",
            details={"last_error": str(last_exception), "attempts": self.max_attempts}
        )
    
    async def aretry(self, func: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs) -> T:
        """
        Execute async function with retry logic
        
        Args:
            func: Async function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhaustedError: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = self.get_delay(attempt)
                    logger.warning(f"⚠️  Async retry {attempt + 1}/{self.max_attempts} after {delay:.2f}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ All {self.max_attempts} async retries exhausted: {str(e)}")
        
        raise RetryExhaustedError(
            f"Failed after {self.max_attempts} attempts: {str(last_exception)}",
            code="RETRY_EXHAUSTED",
            details={"last_error": str(last_exception), "attempts": self.max_attempts}
        )


# ============================================================================
# GLOBAL CIRCUIT BREAKERS
# ============================================================================

# Ollama service circuit breaker
ollama_circuit_breaker = CircuitBreaker(
    name="ollama",
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=(OllamaConnectionError, OllamaTimeoutError)
)

# Supabase circuit breaker
supabase_circuit_breaker = CircuitBreaker(
    name="supabase",
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception
)

# Embedding service circuit breaker
embedding_circuit_breaker = CircuitBreaker(
    name="embedding",
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)


# ============================================================================
# DECORATORS
# ============================================================================

def with_retry(max_attempts: int = 3, base_delay: float = 0.5):
    """
    Decorator for retry logic
    
    Usage:
        @with_retry(max_attempts=3)
        async def my_function():
            ...
    """
    strategy = RetryStrategy(max_attempts=max_attempts, base_delay=base_delay)
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await strategy.aretry(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return strategy.retry(func, *args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator for circuit breaker protection
    
    Usage:
        @with_circuit_breaker(ollama_circuit_breaker)
        async def my_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.acall(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
