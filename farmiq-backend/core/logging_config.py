"""
FarmIQ Structured Logging Configuration (Phase 5.1b)
JSON-based logging for monitoring, debugging, and security auditing
"""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import traceback
import sys


# ============================================================================
# JSON FORMATTER
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON logs
    Includes timestamp, level, message, and context
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log entry
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra context if available
        if hasattr(record, "__dict__"):
            # Extract custom fields added via extra parameter
            for key, value in record.__dict__.items():
                # Skip built-in fields
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'message', 'pathname', 'process', 'processName', 'relativeCreated',
                    'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                    'msg', 'asctime'
                ]:
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        elif record.stack_info:
            log_data["stack"] = record.stack_info
        
        return json.dumps(log_data, default=str)


# ============================================================================
# LOGGER INITIALIZATION
# ============================================================================

def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for the entire application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for logs
        log_file: Optional file path for log output
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Failed to create log file: {e}")


# ============================================================================
# CONTEXT-AWARE LOGGING
# ============================================================================

class StructuredLogger:
    """
    Wrapper around Python logger for structured logging
    Simplifies adding context to logs
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set context that will be added to all subsequent logs"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context"""
        self.context.clear()
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method with context"""
        # Merge provided kwargs with stored context
        log_context = {**self.context, **kwargs}
        
        # Get logger method
        log_method = getattr(self.logger, level.lower())
        
        # Log with extra data
        log_method(message, extra=log_context)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log("CRITICAL", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self._log("ERROR", message, exc_info=True, **kwargs)


# ============================================================================
# PREDEFINED LOGGERS FOR MODULES
# ============================================================================

# Application loggers
app_logger = StructuredLogger("farmiq.app")
auth_logger = StructuredLogger("farmiq.auth")
route_logger = StructuredLogger("farmiq.routes")
service_logger = StructuredLogger("farmiq.services")
database_logger = StructuredLogger("farmiq.database")
ml_logger = StructuredLogger("farmiq.ml")
security_logger = StructuredLogger("farmiq.security")


# ============================================================================
# AUDIT LOGGING HELPERS
# ============================================================================

def log_authentication(
    user_id: str,
    success: bool,
    request_id: str,
    ip_address: str,
    reason: Optional[str] = None
):
    """Log authentication attempt"""
    security_logger.info(
        f"Authentication {'succeeded' if success else 'failed'}",
        user_id=user_id,
        success=success,
        request_id=request_id,
        ip_address=ip_address,
        reason=reason,
        event_type="AUTH",
    )


def log_authorization(
    user_id: str,
    resource: str,
    action: str,
    allowed: bool,
    request_id: str,
    reason: Optional[str] = None
):
    """Log authorization check"""
    security_logger.info(
        f"Authorization {'allowed' if allowed else 'denied'}",
        user_id=user_id,
        resource=resource,
        action=action,
        allowed=allowed,
        request_id=request_id,
        reason=reason,
        event_type="AUTHZ",
    )


def log_api_call(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str,
    request_id: str,
    error: Optional[str] = None
):
    """Log API call with metrics"""
    level = "INFO" if 200 <= status_code < 400 else "WARNING" if status_code < 500 else "ERROR"
    
    route_logger._log(
        level,
        f"{method} {path} {status_code}",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        request_id=request_id,
        error=error,
        event_type="API_CALL",
    )


def log_database_operation(
    operation: str,
    table: str,
    duration_ms: float,
    rows_affected: int,
    request_id: str,
    error: Optional[str] = None
):
    """Log database operation"""
    level = "INFO" if error is None else "ERROR"
    
    database_logger._log(
        level,
        f"{operation} on {table}",
        operation=operation,
        table=table,
        duration_ms=duration_ms,
        rows_affected=rows_affected,
        request_id=request_id,
        error=error,
        event_type="DB_OP",
    )


def log_ml_prediction(
    model_type: str,
    farm_id: str,
    confidence: float,
    duration_ms: float,
    request_id: str,
    is_fallback: bool = False,
    error: Optional[str] = None
):
    """Log ML prediction operation"""
    level = "INFO" if error is None else "WARNING"
    
    ml_logger._log(
        level,
        f"{model_type} prediction for farm {farm_id}",
        model_type=model_type,
        farm_id=farm_id,
        confidence=confidence,
        duration_ms=duration_ms,
        request_id=request_id,
        is_fallback=is_fallback,
        error=error,
        event_type="ML_PRED",
    )


# ============================================================================
# PERFORMANCE LOGGING
# ============================================================================

class PerformanceTimer:
    """
    Context manager for timing code blocks
    Logs duration automatically on exit
    """
    
    def __init__(self, operation: str, logger: StructuredLogger, **context):
        self.operation = operation
        self.logger = logger
        self.context = context
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        from datetime import datetime
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from datetime import datetime
        self.duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(
                f"{self.operation} completed",
                duration_ms=self.duration_ms,
                **self.context
            )
        else:
            self.logger.error(
                f"{self.operation} failed",
                duration_ms=self.duration_ms,
                error=str(exc_val),
                **self.context
            )
        
        return False  # Don't suppress exceptions
