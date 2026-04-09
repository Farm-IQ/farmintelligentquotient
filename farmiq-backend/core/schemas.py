"""
FarmSuite AI - Core Database Models (Pydantic Schemas)
Used for validation and type safety across all APIs
Follows clean architecture patterns with separation of concerns
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


# ============================================================================
# ENUMS FOR TYPE SAFETY
# ============================================================================

class CreditRiskLevel(str, Enum):
    """FarmIQ Credit Risk Levels (from ML model output)"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DocumentCategory(str, Enum):
    """Document categories for FarmGrow RAG"""
    CROP_GUIDE = "crop_guide"
    PEST_MANAGEMENT = "pest_management"
    SOIL_MANAGEMENT = "soil_management"
    WATER_MANAGEMENT = "water_management"
    MARKET_INFO = "market_info"
    LOAN_GUIDE = "loan_guide"


# ============================================================================
# FARMGROW RAG MODELS
# ============================================================================

class DocumentChunkSchema(BaseModel):
    """A single chunk of text from a document"""
    id: Optional[uuid.UUID] = None
    document_id: uuid.UUID
    chunk_index: int
    chunk_text: str = Field(..., min_length=10)
    chunk_size_tokens: Optional[int] = None
    page_number: Optional[int] = None
    chunk_type: str = "content"
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class EmbeddingSchema(BaseModel):
    """Vector embedding for a document chunk"""
    id: Optional[uuid.UUID] = None
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    embedding_vector: List[float] = Field(..., min_length=1024, max_length=1024)
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    class Config:
        from_attributes = True


class DocumentSchema(BaseModel):
    """Document metadata and content"""
    id: Optional[uuid.UUID] = None
    original_filename: str
    document_title: Optional[str] = None
    file_type: str  # 'pdf', 'image', 'text', 'docx'
    file_size_bytes: Optional[int] = None
    document_category: Optional[DocumentCategory] = None
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    detected_language: str = "en"
    ocr_engine: Optional[str] = None
    ocr_confidence: Optional[float] = None
    uploaded_by: Optional[uuid.UUID] = None
    processing_status: str = "pending"
    processing_error: Optional[str] = None
    indexed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RAGConversationSchema(BaseModel):
    """RAG conversation session"""
    id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    conversation_type: str = "general"
    context: Dict[str, Any] = Field(default_factory=dict)
    retrieval_method: str = "hybrid"
    top_k_chunks: int = 5
    similarity_threshold: float = 0.3
    is_active: bool = True
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RAGMessageSchema(BaseModel):
    """Single message in RAG conversation"""
    id: Optional[uuid.UUID] = None
    conversation_id: uuid.UUID
    message_role: str  # 'user' or 'assistant'
    message_content: str
    message_input_type: str = "text"
    retrieved_chunk_ids: Optional[List[uuid.UUID]] = None
    retrieved_chunks_metadata: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    sources: Optional[Dict[str, Any]] = None
    hallucination_score: Optional[float] = None
    citation_correctness: Optional[float] = None
    user_rating: Optional[int] = None
    llm_model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[Dict[str, int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('user_rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

    class Config:
        from_attributes = True


# ============================================================================
# FARMIQ CREDIT SCORING MODELS
# ============================================================================

class LoanScenarioSchema(BaseModel):
    """Individual loan scenario with terms and payment details"""
    loan_amount: float = Field(..., gt=0, description="Loan amount in KES")
    term_months: int = Field(..., gt=0, description="Loan term in months")
    monthly_payment: float = Field(..., gt=0, description="Monthly payment in KES")
    total_interest: float = Field(..., ge=0, description="Total interest to be paid")
    interest_rate_percent: float = Field(..., ge=0, description="Annual interest rate %")
    is_sustainable: bool = Field(default=True, description="Whether payment is sustainable")
    payment_to_revenue_ratio: Optional[float] = Field(None, ge=0, le=1, description="Monthly payment as % of revenue")


class RepaymentCapacitySchema(BaseModel):
    """Farmer's capacity to repay loans"""
    capacity_score: float = Field(..., ge=0, le=1, description="Capacity score [0,1]")
    status: str = Field(..., description="Status: excellent/good/fair/tight/insufficient")
    monthly_revenue: Optional[float] = Field(None, ge=0, description="Monthly revenue in KES")
    disposable_income: Optional[float] = Field(None, ge=0, description="Income after expenses")
    monthly_payment: float = Field(..., ge=0, description="Proposed monthly payment")
    payment_to_revenue_ratio: float = Field(..., ge=0, le=1, description="Payment to revenue ratio")
    payment_to_disposable_ratio: float = Field(..., ge=0, description="Payment to disposable income ratio")


class FarmIQScoreSchema(BaseModel):
    """Enhanced FarmIQ Credit Score Result with multiple scenarios"""
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    fiq_score: float = Field(..., ge=0, le=100, description="Credit score [0-100]")
    fiq_percentile: Optional[float] = Field(None, ge=0, le=100, description="Percentile ranking")
    credit_risk_level: CreditRiskLevel = Field(..., description="Risk level")
    default_probability: float = Field(..., ge=0, le=1, description="Probability of default")
    approval_likelihood: float = Field(..., ge=0, le=1, description="Loan approval likelihood")
    
    # Credit and loan recommendations
    recommended_credit_limit_kes: float = Field(..., ge=0, description="Recommended credit limit")
    recommended_loan_term_months: int = Field(..., gt=0, description="Recommended term in months")
    recommended_interest_rate: float = Field(..., ge=0, description="Recommended annual interest rate %")
    monthly_payment_estimate: float = Field(..., ge=0, description="Estimated monthly payment")
    
    # Multiple loan scenarios for customer choice
    loan_scenarios: List[LoanScenarioSchema] = Field(default_factory=list, description="Multiple loan options")
    
    # Repayment capacity analysis
    repayment_capacity: Optional[RepaymentCapacitySchema] = Field(None, description="Capacity analysis")
    
    # Explainability
    feature_importance: Dict[str, float] = Field(default_factory=dict, description="Feature importance/SHAP values")
    shap_values: Dict[str, float] = Field(default_factory=dict, description="SHAP explanation values")
    key_strengths: List[str] = Field(default_factory=list, description="Credit strengths")
    key_weaknesses: List[str] = Field(default_factory=list, description="Risk factors")
    improvement_recommendations: List[str] = Field(default_factory=list, description="How to improve creditworthiness")
    
    # Model metadata
    model_version: Optional[str] = Field(None, description="Model version used")
    model_type: str = Field(default="ensemble", description="ensemble or logistic_regression")
    ensemble_confidence: Optional[float] = Field(None, ge=0, le=1, description="Ensemble model confidence")
    uncertainty_estimate: Optional[float] = Field(None, ge=0, description="Probability uncertainty (std dev)")
    
    # Approval tracking
    approval_status: str = Field(default="pending", description="Approval status")
    approval_note: Optional[str] = Field(None, description="Approval notes")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    score_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreditScoringRequestSchema(BaseModel):
    """Request for credit scoring calculation"""
    user_id: str = Field(..., description="User/FarmIQ ID")
    farmer_id: Optional[str] = Field(None, description="Farmer ID if different from user_id")
    recalculate: bool = Field(default=False, description="Force recalculation even if cached")
    features: Optional[Dict[str, Any]] = Field(None, description="Additional features to override")


class CreditScoringResponseSchema(BaseModel):
    """Response from credit scoring calculation"""
    fiq_score: float
    risk_level: str
    default_probability: float
    credit_limit: float
    loan_term_months: int
    interest_rate_percent: float
    recommendations: List[str]
    explanation: Dict[str, Any]
    calculation_time_ms: float


class LoanApplicationSchema(BaseModel):
    """Loan Application Schema"""
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    credit_profile_id: Optional[uuid.UUID] = None
    requested_amount_kes: float = Field(..., gt=0)
    requested_term_months: int = Field(..., gt=0)
    loan_purpose: Optional[str] = None
    application_status: str = "submitted"
    approved_amount_kes: Optional[float] = None
    approved_term_months: Optional[int] = None
    approved_interest_rate: Optional[float] = None
    approval_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    disbursement_date: Optional[datetime] = None
    total_to_repay_kes: Optional[float] = None
    total_repaid_kes: float = 0
    remaining_balance_kes: Optional[float] = None
    repayment_status: str = "pending"
    next_due_date: Optional[datetime] = None
    days_overdue: int = 0
    payment_behavior_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    maturity_date: Optional[datetime] = None

    class Config:
        from_attributes = True





# ============================================================================
# ML MODEL REGISTRY MODELS
# ============================================================================

class MLModelRegistrySchema(BaseModel):
    """ML Model Registry Entry (with ML theory annotations)"""
    id: Optional[uuid.UUID] = None
    model_name: str
    model_type: str  # 'farmgrow_rag', 'farmiq_credit', 'farmscore_forex'
    model_version: str
    architecture_description: Optional[str] = None
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    feature_count: Optional[int] = None
    feature_list: Optional[List[str]] = None
    
    # Training info
    training_dataset_size: Optional[int] = None
    training_split_ratio: Dict[str, float] = Field(default_factory=dict)
    training_date: Optional[str] = None
    
    # Validation metrics
    training_accuracy: Optional[float] = None
    validation_accuracy: Optional[float] = None
    test_accuracy: Optional[float] = None
    
    # ML Theory: Complexity & Generalization
    training_error: Optional[float] = None
    validation_error: Optional[float] = None
    generalization_gap: Optional[float] = None
    vc_dimension_estimate: Optional[int] = None
    rademacher_complexity: Optional[float] = None
    expected_hoeffding_error: Optional[float] = None
    
    # Cross-validation
    cross_validation_folds: int = 5
    cross_validation_scores: Dict[str, float] = Field(default_factory=dict)
    cross_validation_mean: Optional[float] = None
    cross_validation_std: Optional[float] = None
    
    # Regularization (Structural Risk Minimization)
    regularization_type: Optional[str] = None
    regularization_strength: Optional[float] = None
    
    is_production: bool = False
    is_deprecated: bool = False
    description: Optional[str] = None
    ml_theory_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class RAGQueryRequest(BaseModel):
    """RAG Query Request - supports both query and message fields"""
    query: Optional[str] = None  # Query text (alternative to message)
    message: Optional[str] = None  # Chat message (can include image references like [Image: filename])
    user_id: Optional[str] = None  # User ID from frontend (optional, can come from auth)
    conversation_id: Optional[str] = None  # String UUID for conversation
    create_new_conversation: bool = False
    context: Optional[Dict[str, Any]] = None
    input_type: str = "text"  # "text", "image", "mixed"
    stream: bool = False  # Whether to stream response
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.3, ge=0, le=1)
    retrieval_method: str = "hybrid"  # hybrid, vector_only, bm25_only
    
    @property
    def get_query_text(self) -> str:
        """Get the actual query text - prefer query, fallback to message"""
        return self.query or self.message or "Please help"


class RAGQueryResponse(BaseModel):
    """RAG Query Response"""
    query: str
    answer: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    processing_time_ms: int
    hallucination_score: Optional[float] = None
    cited_correctly: Optional[bool] = None


class CreditScoringRequest(BaseModel):
    """Credit Scoring Request"""
    user_id: uuid.UUID
    farmer_id: Optional[uuid.UUID] = None
    recalculate: bool = False  # Force recalculation


class CreditScoringResponse(BaseModel):
    """Credit Scoring Response"""
    score_result: FarmIQScoreSchema
    success: bool
    message: str



