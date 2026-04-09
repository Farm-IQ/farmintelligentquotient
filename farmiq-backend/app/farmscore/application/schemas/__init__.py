"""
FarmScore Application Schemas
Request and Response DTOs
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class FarmerRequest(BaseModel):
    """Request DTO for creating/updating farmer"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    farm_size_acres: float = Field(default=1.0, gt=0)
    years_farming: int = Field(default=1, gt=0)
    crop_types: List[str] = Field(default_factory=list)
    livestock_types: List[str] = Field(default_factory=list)
    coop_membership_years: int = Field(default=0, ge=0)
    training_hours: int = Field(default=0, ge=0)


class FarmerResponse(BaseModel):
    """Response DTO for farmer"""
    id: str
    user_id: str
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    farm_size_acres: float
    years_farming: int
    crop_types: List[str]
    livestock_types: List[str]
    coop_membership_years: int
    training_hours: int
    created_at: datetime
    updated_at: datetime
    is_active: bool


class CreditScoringRequest(BaseModel):
    """Request DTO for credit scoring"""
    user_id: str
    farmer_id: Optional[str] = None
    monthly_revenue: float = Field(gt=0)
    monthly_expense: float = Field(ge=0)
    liquid_savings: float = Field(default=0, ge=0)
    recalculate: bool = Field(default=False)


class CreditScoringResponse(BaseModel):
    """Response DTO for credit scoring result"""
    id: str
    user_id: str
    farmer_id: str
    score: float
    risk_level: str
    risk_category: str
    default_probability: float
    approval_likelihood: float
    is_eligible_for_loan: bool
    recommended_credit_limit_kes: float
    recommended_loan_term_months: int
    recommended_interest_rate: float
    improvement_recommendations: List[str]
    is_cache_valid: bool
    created_at: datetime
    updated_at: datetime


class CreditScoreDetailResponse(CreditScoringResponse):
    """Detailed credit score response with SHAP explanation"""
    shap_explanation: Dict[str, Any]
    model_version: str


class LoanApplicationRequest(BaseModel):
    """Request DTO for loan application"""
    user_id: str
    farmer_id: Optional[str] = None
    requested_amount_kes: float = Field(gt=0)
    requested_term_months: int = Field(gt=0, le=60)
    purpose: str = Field(min_length=10)


class LoanApplicationResponse(BaseModel):
    """Response DTO for loan application"""
    id: str
    user_id: str
    requested_amount_kes: float
    approved_amount_kes: Optional[float]
    requested_term_months: int
    approved_term_months: Optional[int]
    interest_rate: Optional[float]
    status: str  # pending, approved, rejected
    credit_score: float
    risk_level: str
    approval_likelihood: float
    created_at: datetime
