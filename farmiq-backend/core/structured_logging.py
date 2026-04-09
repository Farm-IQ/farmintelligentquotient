"""
Phase 3 Task 3: Structured Logging System for FarmGrow RAG
Comprehensive logging for debugging, monitoring, and compliance

Features:
- Structured logs (JSON format for easy parsing)
- Multiple log levels with context
- Performance tracking (operation duration)
- Error categorization
- User action audit trail
- Query logging for agricultural insights
"""
import logging
import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
from functools import wraps
import sys


class LogLevel(Enum):
    """Structured log levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredLogger:
    """
    Structured logging for FarmGrow RAG system.
    
    All logs are JSON-formatted for easy parsing with:
    - Elasticsearch
    - Datadog
    - Splunk
    - CloudWatch
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
        self.name = name
        
        # Set default formatter
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers with JSON formatting."""
        # Console handler (development)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler (production - JSON format)
        file_handler = logging.FileHandler('logs/farmgrow.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = JsonFormatter()
        file_handler.setFormatter(file_formatter)
        
        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
        
        self.logger.setLevel(logging.DEBUG)
    
    def _format_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Format log entry as structured dictionary.
        
        Args:
            level: Log level
            message: Log message
            context: Additional context dictionary
            **kwargs: Additional key-value pairs
            
        Returns:
            Structured log dictionary
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
        }
        
        if context:
            log_entry["context"] = context
        
        log_entry.update(kwargs)
        
        return log_entry
    
    def debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Debug level log."""
        entry = self._format_log("DEBUG", message, context, **kwargs)
        self.logger.debug(json.dumps(entry))
    
    def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Info level log."""
        entry = self._format_log("INFO", message, context, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Warning level log."""
        entry = self._format_log("WARNING", message, context, **kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Error level log with exception details."""
        if exception:
            context = context or {}
            context["exception_type"] = type(exception).__name__
            context["exception_message"] = str(exception)
            context["traceback"] = traceback.format_exc()
        
        entry = self._format_log("ERROR", message, context, **kwargs)
        self.logger.error(json.dumps(entry))
    
    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Critical level log."""
        if exception:
            context = context or {}
            context["exception_type"] = type(exception).__name__
            context["exception_message"] = str(exception)
            context["traceback"] = traceback.format_exc()
        
        entry = self._format_log("CRITICAL", message, context, **kwargs)
        self.logger.critical(json.dumps(entry))


class JsonFormatter(logging.Formatter):
    """Custom formatter for JSON log output."""
    
    def format(self, record):
        """Format log record as JSON."""
        if isinstance(record.msg, dict):
            return json.dumps(record.msg)
        
        try:
            return json.dumps(json.loads(record.msg))
        except (json.JSONDecodeError, TypeError):
            return record.msg


class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, logger: StructuredLogger, operation_name: str):
        """
        Initialize timer.
        
        Args:
            logger: Structured logger instance
            operation_name: Name of operation being timed
        """
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log duration."""
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation_name}",
                context={
                    "duration_ms": duration_ms,
                    "status": "success"
                }
            )
        else:
            self.logger.error(
                f"Failed: {self.operation_name}",
                context={
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error_type": exc_type.__name__
                },
                exception=exc_val
            )
        
        return False


def log_operation(func):
    """
    Decorator to automatically log function execution.
    
    Usage:
        @log_operation
        async def my_function(text: str):
            return result
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = StructuredLogger(func.__module__)
        operation_name = f"{func.__name__}({', '.join(str(a)[:30] for a in args[1:])})"
        
        with OperationTimer(logger, operation_name):
            return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = StructuredLogger(func.__module__)
        operation_name = f"{func.__name__}({', '.join(str(a)[:30] for a in args[1:])})"
        
        with OperationTimer(logger, operation_name):
            return func(*args, **kwargs)
    
    # Return appropriate wrapper
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class QueryLogger:
    """Special logger for RAG queries."""
    
    def __init__(self):
        """Initialize query logger."""
        self.logger = StructuredLogger("farmgrow.queries")
    
    def log_query(
        self,
        user_id: str,
        query_text: str,
        query_type: str,
        tags: Optional[list] = None
    ):
        """
        Log user query.
        
        Args:
            user_id: User ID (FarmIQ ID)
            query_text: The actual query
            query_type: Type of query (chat, search, analysis)
            tags: Optional tags (crop type, region, etc.)
        """
        self.logger.info(
            "User query received",
            context={
                "user_id": user_id,
                "query_type": query_type,
                "query_length": len(query_text),
                "tags": tags or []
            }
        )
    
    def log_retrieval(
        self,
        query_id: str,
        num_results: int,
        retrieval_time_ms: float,
        sources: Optional[list] = None
    ):
        """Log document retrieval results."""
        self.logger.info(
            "Document retrieval completed",
            context={
                "query_id": query_id,
                "num_results": num_results,
                "retrieval_time_ms": retrieval_time_ms,
                "sources": sources or []
            }
        )
    
    def log_generation(
        self,
        query_id: str,
        generation_time_ms: float,
        response_length: int,
        model: str
    ):
        """Log LLM response generation."""
        self.logger.info(
            "Response generated",
            context={
                "query_id": query_id,
                "generation_time_ms": generation_time_ms,
                "response_length": response_length,
                "model": model
            }
        )
    
    def log_error(
        self,
        query_id: str,
        stage: str,
        error_message: str,
        exception: Optional[Exception] = None
    ):
        """Log query processing error."""
        self.logger.error(
            f"Query failed at {stage}",
            context={
                "query_id": query_id,
                "stage": stage
            },
            exception=exception
        )


class CacheLogger:
    """Special logger for cache operations."""
    
    def __init__(self):
        """Initialize cache logger."""
        self.logger = StructuredLogger("farmgrow.cache")
    
    def log_hit(
        self,
        cache_key: str,
        hit_count: int,
        cache_size: int
    ):
        """Log cache hit."""
        self.logger.debug(
            "Cache hit",
            context={
                "cache_key_preview": cache_key[:30],
                "hit_count": hit_count,
                "cache_size": cache_size
            }
        )
    
    def log_miss(
        self,
        cache_key: str,
        miss_count: int
    ):
        """Log cache miss."""
        self.logger.debug(
            "Cache miss",
            context={
                "cache_key_preview": cache_key[:30],
                "miss_count": miss_count
            }
        )
    
    def log_eviction(
        self,
        removed_key: str,
        cache_size: int,
        max_size: int
    ):
        """Log cache eviction."""
        self.logger.info(
            "Cache eviction (LRU)",
            context={
                "removed_key_preview": removed_key[:30],
                "cache_size": cache_size,
                "max_size": max_size
            }
        )
    
    def log_stats(
        self,
        hit_rate: float,
        total_requests: int,
        cache_size: int
    ):
        """Log cache statistics."""
        self.logger.info(
            "Cache statistics",
            context={
                "hit_rate": f"{hit_rate:.1f}%",
                "total_requests": total_requests,
                "cache_size": cache_size
            }
        )


class PerformanceLogger:
    """Special logger for performance metrics."""
    
    def __init__(self):
        """Initialize performance logger."""
        self.logger = StructuredLogger("farmgrow.performance")
    
    def log_latency(
        self,
        operation: str,
        duration_ms: float,
        threshold_ms: Optional[float] = None
    ):
        """Log operation latency."""
        status = "ok"
        if threshold_ms and duration_ms > threshold_ms:
            status = "slow"
        
        self.logger.info(
            f"Operation latency: {operation}",
            context={
                "operation": operation,
                "duration_ms": duration_ms,
                "status": status
            }
        )
    
    def log_throughput(
        self,
        operation: str,
        count: int,
        duration_sec: float
    ):
        """Log operation throughput."""
        throughput = count / duration_sec if duration_sec > 0 else 0
        
        self.logger.info(
            f"Throughput: {operation}",
            context={
                "operation": operation,
                "count": count,
                "duration_sec": duration_sec,
                "throughput_per_sec": throughput
            }
        )


# Global logger instances
_query_logger: Optional[QueryLogger] = None
_cache_logger: Optional[CacheLogger] = None
_perf_logger: Optional[PerformanceLogger] = None


def get_query_logger() -> QueryLogger:
    """Get global query logger."""
    global _query_logger
    if _query_logger is None:
        _query_logger = QueryLogger()
    return _query_logger


def get_cache_logger() -> CacheLogger:
    """Get global cache logger."""
    global _cache_logger
    if _cache_logger is None:
        _cache_logger = CacheLogger()
    return _cache_logger


def get_perf_logger() -> PerformanceLogger:
    """Get global performance logger."""
    global _perf_logger
    if _perf_logger is None:
        _perf_logger = PerformanceLogger()
    return _perf_logger
