"""
FarmGrow RAG Service - Custom Exceptions
Comprehensive error hierarchy for RAG pipeline operations
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FarmGrowException(Exception):
    """Base exception for all FarmGrow RAG errors"""
    
    def __init__(self, message: str, code: str = "FARMGROW_ERROR", details: Optional[dict] = None):
        """
        Initialize FarmGrow exception
        
        Args:
            message: Error message
            code: Error code for API responses
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API response"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# DOCUMENT INGESTION ERRORS
# ============================================================================

class DocumentIngestionError(FarmGrowException):
    """Base exception for document ingestion failures"""
    code = "INGESTION_ERROR"


class PDFParsingError(DocumentIngestionError):
    """PDF text extraction failed"""
    code = "PDF_PARSING_ERROR"


class OCRError(DocumentIngestionError):
    """OCR processing failed"""
    code = "OCR_ERROR"


class EmbeddingGenerationError(DocumentIngestionError):
    """Embedding generation failed during ingestion"""
    code = "EMBEDDING_GENERATION_ERROR"


class DocumentNotFoundError(DocumentIngestionError):
    """Document file not found"""
    code = "DOCUMENT_NOT_FOUND"


class DocumentSizeError(DocumentIngestionError):
    """Document exceeds size limit"""
    code = "DOCUMENT_SIZE_ERROR"


# ============================================================================
# EMBEDDING ERRORS
# ============================================================================

class EmbeddingError(FarmGrowException):
    """Base exception for embedding operations"""
    code = "EMBEDDING_ERROR"


class EmbeddingModelNotAvailableError(EmbeddingError):
    """Embedding model is not available"""
    code = "EMBEDDING_MODEL_NOT_AVAILABLE"


class EmbeddingDimensionMismachError(EmbeddingError):
    """Embedding dimension mismatch"""
    code = "EMBEDDING_DIMENSION_MISMATCH"


class EmbeddingStorageError(EmbeddingError):
    """Error storing or retrieving embeddings"""
    code = "EMBEDDING_STORAGE_ERROR"


# ============================================================================
# RETRIEVAL ERRORS
# ============================================================================

class RetrievalError(FarmGrowException):
    """Base exception for retrieval operations"""
    code = "RETRIEVAL_ERROR"


class NoRelevantDocumentsError(RetrievalError):
    """No relevant documents found for query"""
    code = "NO_RELEVANT_DOCUMENTS"


class VectorSearchError(RetrievalError):
    """Vector search operation failed"""
    code = "VECTOR_SEARCH_ERROR"


class BM25Error(RetrievalError):
    """BM25 ranking operation failed"""
    code = "BM25_ERROR"


# ============================================================================
# LLM ERRORS
# ============================================================================

class LLMError(FarmGrowException):
    """Base exception for LLM operations"""
    code = "LLM_ERROR"


class OllamaConnectionError(LLMError):
    """Cannot connect to Ollama service"""
    code = "OLLAMA_CONNECTION_ERROR"


class OllamaTimeoutError(LLMError):
    """Ollama request timed out"""
    code = "OLLAMA_TIMEOUT"


class ModelNotAvailableError(LLMError):
    """Required LLM model not available"""
    code = "MODEL_NOT_AVAILABLE"


class TokenLimitExceededError(LLMError):
    """Token limit exceeded for request"""
    code = "TOKEN_LIMIT_EXCEEDED"


class AnswerGenerationError(LLMError):
    """Failed to generate LLM answer"""
    code = "ANSWER_GENERATION_ERROR"


# ============================================================================
# DATABASE ERRORS
# ============================================================================

class DatabaseError(FarmGrowException):
    """Base exception for database operations"""
    code = "DATABASE_ERROR"


class SupabaseConnectionError(DatabaseError):
    """Cannot connect to Supabase"""
    code = "SUPABASE_CONNECTION_ERROR"


class ConversationNotFoundError(DatabaseError):
    """Conversation not found in database"""
    code = "CONVERSATION_NOT_FOUND"


class ConversationStorageError(DatabaseError):
    """Failed to store conversation"""
    code = "CONVERSATION_STORAGE_ERROR"


class MessageStorageError(DatabaseError):
    """Failed to store message"""
    code = "MESSAGE_STORAGE_ERROR"


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(FarmGrowException):
    """Base exception for validation failures"""
    code = "VALIDATION_ERROR"


class InvalidQueryError(ValidationError):
    """Query validation failed"""
    code = "INVALID_QUERY"


class InvalidFileTypeError(ValidationError):
    """File type not supported"""
    code = "INVALID_FILE_TYPE"


class InvalidConversationError(ValidationError):
    """Conversation ID invalid or malformed"""
    code = "INVALID_CONVERSATION"


class MissingParameterError(ValidationError):
    """Required parameter missing"""
    code = "MISSING_PARAMETER"


# ============================================================================
# SERVICE INITIALIZATION ERRORS
# ============================================================================

class ServiceInitializationError(FarmGrowException):
    """Base exception for service init failures"""
    code = "SERVICE_INITIALIZATION_ERROR"


class ServiceConfigurationError(ServiceInitializationError):
    """Service configuration error"""
    code = "SERVICE_CONFIGURATION_ERROR"


class DependencyNotAvailableError(ServiceInitializationError):
    """Required dependency not available"""
    code = "DEPENDENCY_NOT_AVAILABLE"


# ============================================================================
# CIRCUIT BREAKER & RELIABILITY ERRORS
# ============================================================================

class CircuitBreakerOpenError(FarmGrowException):
    """Circuit breaker is open, service temporarily unavailable"""
    code = "CIRCUIT_BREAKER_OPEN"


class RetryExhaustedError(FarmGrowException):
    """All retry attempts exhausted"""
    code = "RETRY_EXHAUSTED"


class ServiceUnavailableError(FarmGrowException):
    """Service temporarily unavailable"""
    code = "SERVICE_UNAVAILABLE"


# ============================================================================
# ERROR HANDLING UTILITIES
# ============================================================================

def create_error_response(error: Exception, status_code: int = 500) -> dict:
    """
    Create standardized error response for API
    
    Args:
        error: Exception that occurred
        status_code: HTTP status code
        
    Returns:
        Dictionary with error details
    """
    if isinstance(error, FarmGrowException):
        return {
            "status": "error",
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "status_code": status_code
        }
    else:
        # Convert generic exceptions
        return {
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": str(error),
            "details": {"exception_type": type(error).__name__},
            "status_code": status_code
        }


def log_error(error: Exception, context: str = "", severity: str = "error"):
    """
    Log error with context
    
    Args:
        error: Exception to log
        context: Additional context
        severity: Log level (debug, info, warning, error, critical)
    """
    log_func = getattr(logger, severity, logger.error)
    
    if isinstance(error, FarmGrowException):
        log_func(f"[{error.code}] {context}: {error.message}", extra={"details": error.details})
    else:
        log_func(f"{context}: {str(error)}", exc_info=True)
