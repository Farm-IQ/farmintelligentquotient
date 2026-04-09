"""
FarmGrow RAG - Input Validation
Comprehensive request validation and sanitization
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict
import re
import logging

logger = logging.getLogger(__name__)


class QueryValidation:
    """Query validation rules"""
    
    # Query constraints
    MIN_QUERY_LENGTH = 3
    MAX_QUERY_LENGTH = 5000
    MIN_TOP_K = 1
    MAX_TOP_K = 50
    MIN_SIMILARITY_THRESHOLD = 0.0
    MAX_SIMILARITY_THRESHOLD = 1.0
    
    # Allowed retrieval methods
    ALLOWED_RETRIEVAL_METHODS = ["hybrid", "vector_only", "bm25_only", "multi_vector"]
    
    @staticmethod
    def validate_query_text(query: str) -> bool:
        """
        Validate query text
        
        Args:
            query: Query text to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If invalid
        """
        query = query.strip()
        
        if not query:
            raise ValueError("Query cannot be empty")
        
        if len(query) < QueryValidation.MIN_QUERY_LENGTH:
            raise ValueError(f"Query must be at least {QueryValidation.MIN_QUERY_LENGTH} characters")
        
        if len(query) > QueryValidation.MAX_QUERY_LENGTH:
            raise ValueError(f"Query exceeds maximum length of {QueryValidation.MAX_QUERY_LENGTH} characters")
        
        # Check for SQL injection attempts
        sql_patterns = [r'DROP\s+TABLE', r'INSERT\s+INTO', r'DELETE\s+FROM', r'UNION\s+SELECT']
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in sql_patterns):
            logger.warning(f"Suspicious SQL pattern detected in query: {query[:50]}")
            raise ValueError("Query contains suspicious patterns")
        
        return True
    
    @staticmethod
    def validate_top_k(top_k: int) -> bool:
        """Validate top_k parameter"""
        if not isinstance(top_k, int):
            raise ValueError("top_k must be an integer")
        
        if top_k < QueryValidation.MIN_TOP_K or top_k > QueryValidation.MAX_TOP_K:
            raise ValueError(f"top_k must be between {QueryValidation.MIN_TOP_K} and {QueryValidation.MAX_TOP_K}")
        
        return True
    
    @staticmethod
    def validate_similarity_threshold(threshold: float) -> bool:
        """Validate similarity threshold"""
        if not isinstance(threshold, (int, float)):
            raise ValueError("Similarity threshold must be a number")
        
        if threshold < QueryValidation.MIN_SIMILARITY_THRESHOLD or threshold > QueryValidation.MAX_SIMILARITY_THRESHOLD:
            raise ValueError(f"Similarity threshold must be between {QueryValidation.MIN_SIMILARITY_THRESHOLD} and {QueryValidation.MAX_SIMILARITY_THRESHOLD}")
        
        return True
    
    @staticmethod
    def validate_retrieval_method(method: str) -> bool:
        """Validate retrieval method"""
        if method not in QueryValidation.ALLOWED_RETRIEVAL_METHODS:
            raise ValueError(f"Retrieval method must be one of: {', '.join(QueryValidation.ALLOWED_RETRIEVAL_METHODS)}")
        
        return True


class FileValidation:
    """File upload validation rules"""
    
    # Allowed file types
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx'}
    ALLOWED_MIMETYPES = {
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    # Size constraints
    MAX_FILE_SIZE_MB = 50
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename for security
        
        Args:
            filename: File name to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Remove path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Invalid filename - path traversal detected")
        
        # Check extension
        if not any(filename.lower().endswith(ext) for ext in FileValidation.ALLOWED_EXTENSIONS):
            raise ValueError(f"File type not supported. Allowed: {', '.join(FileValidation.ALLOWED_EXTENSIONS)}")
        
        # Check for suspicious characters
        if not re.match(r'^[\w\s\-\.()]+$', filename):
            raise ValueError("Filename contains invalid characters")
        
        return True
    
    @staticmethod
    def validate_file_size(file_size_bytes: int) -> bool:
        """Validate file size"""
        if file_size_bytes > FileValidation.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum of {FileValidation.MAX_FILE_SIZE_MB}MB")
        
        return True


class ConversationValidation:
    """Conversation validation rules"""
    
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 255
    ALLOWED_CONVERSATION_TYPES = ["agronomy", "credit", "equipment", "market", "general"]
    
    @staticmethod
    def validate_conversation_id(conversation_id: str) -> bool:
        """Validate conversation ID format"""
        # Should be UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, conversation_id, re.IGNORECASE):
            raise ValueError("Invalid conversation ID format")
        
        return True
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate conversation title"""
        title = title.strip()
        
        if len(title) < ConversationValidation.MIN_TITLE_LENGTH:
            raise ValueError("Title cannot be empty")
        
        if len(title) > ConversationValidation.MAX_TITLE_LENGTH:
            raise ValueError(f"Title exceeds maximum length of {ConversationValidation.MAX_TITLE_LENGTH}")
        
        return True
    
    @staticmethod
    def validate_type(conversation_type: str) -> bool:
        """Validate conversation type"""
        if conversation_type not in ConversationValidation.ALLOWED_CONVERSATION_TYPES:
            raise ValueError(f"Conversation type must be one of: {', '.join(ConversationValidation.ALLOWED_CONVERSATION_TYPES)}")
        
        return True


class DocumentValidation:
    """Document validation rules"""
    
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 255
    ALLOWED_CATEGORIES = ["crop_guide", "disease", "equipment", "market", "finance", "general"]
    
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate document title"""
        title = title.strip()
        
        if len(title) < DocumentValidation.MIN_TITLE_LENGTH:
            raise ValueError(f"Title must be at least {DocumentValidation.MIN_TITLE_LENGTH} characters")
        
        if len(title) > DocumentValidation.MAX_TITLE_LENGTH:
            raise ValueError(f"Title exceeds maximum length of {DocumentValidation.MAX_TITLE_LENGTH}")
        
        return True
    
    @staticmethod
    def validate_category(category: str) -> bool:
        """Validate document category"""
        if category not in DocumentValidation.ALLOWED_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(DocumentValidation.ALLOWED_CATEGORIES)}")
        
        return True


# ============================================================================
# PYDANTIC VALIDATION MODELS (for automatic validation)
# ============================================================================

class ValidatedQueryRequest(BaseModel):
    """Query request with built-in validation"""
    query: str = Field(..., min_length=3, max_length=5000)
    user_id: str
    conversation_id: Optional[str] = None
    top_k: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    retrieval_method: str = Field("hybrid")
    include_explanation: bool = False
    stream: bool = False
    input_type: str = "text"
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query text"""
        QueryValidation.validate_query_text(v)
        # Additional sanitization
        v = v.strip()
        # Remove extra whitespace
        v = re.sub(r'\s+', ' ', v)
        return v
    
    @validator('retrieval_method')
    def validate_retrieval_method(cls, v):
        """Validate retrieval method"""
        QueryValidation.validate_retrieval_method(v)
        return v.lower()
    
    @validator('input_type')
    def validate_input_type(cls, v):
        """Validate input type"""
        if v not in ["text", "image", "file", "mixed"]:
            raise ValueError("input_type must be one of: text, image, file, mixed")
        return v.lower()


class ValidatedDocumentRequest(BaseModel):
    """Document upload request with validation"""
    title: str = Field(..., min_length=3, max_length=255)
    category: str = Field("general")
    source_url: Optional[str] = None
    language: str = Field("en")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate document title"""
        DocumentValidation.validate_title(v)
        return v.strip()
    
    @validator('category')
    def validate_category(cls, v):
        """Validate document category"""
        DocumentValidation.validate_category(v)
        return v.lower()
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code"""
        if v not in ["en", "sw", "fr", "es"]:
            raise ValueError("Unsupported language. Supported: en, sw, fr, es")
        return v.lower()


class ValidatedConversationRequest(BaseModel):
    """Conversation creation request with validation"""
    title: str = Field("New Conversation")
    conversation_type: str = Field("general")
    context: Dict = Field(default_factory=dict)
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title"""
        ConversationValidation.validate_title(v)
        return v.strip()
    
    @validator('conversation_type')
    def validate_type(cls, v):
        """Validate conversation type"""
        ConversationValidation.validate_type(v)
        return v.lower()


# ============================================================================
# SANITIZATION UTILITIES
# ============================================================================

def sanitize_input(text: str) -> str:
    """
    Sanitize user input
    
    - Removes HTML/JavaScript
    - Removes extra whitespace
    - Limits length
    """
    if not text:
        return ""
    
    # Remove HTML/script tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Limit length
    if len(text) > 5000:
        text = text[:5000]
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    - Removes path traversal attempts
    - Removes special characters
    - Preserves extension
    """
    # Get extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = f".{ext.lower()}"
    else:
        name = filename
        ext = ""
    
    # Remove path separators
    name = name.replace('/', '_').replace('\\', '_')
    
    # Keep only safe characters
    name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    
    # Limit length
    name = name[:200]
    
    return name + ext


def escape_sql_like(text: str) -> str:
    """Escape special characters for SQL LIKE queries"""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
