"""
FarmSuite Application Schemas
Request/Response DTOs for FarmSuite APIs
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class FarmSchema:
    """Farm response schema"""
    id: str
    user_id: str
    farm_name: str
    total_acres: float
    location: str
    health_score: float
    diversification_index: float


@dataclass
class ProductionSchema:
    """Production metrics schema"""
    farm_id: str
    crop: str
    yield_kg_per_acre: float
    monthly_revenue_kes: float
    consistency_score: float
    production_month: str


@dataclass
class PredictionSchema:
    """Prediction response schema"""
    id: str
    farm_id: str
    prediction_type: str
    subject: str
    predicted_value: float
    confidence: float
    predicted_unit: str


@dataclass
class RiskSchema:
    """Risk item schema"""
    id: str
    farm_id: str
    risk_name: str
    risk_category: str
    risk_score: float
    risk_severity_level: str
    mitigation_strategies: List[str]


@dataclass
class MarketSchema:
    """Market intelligence schema"""
    product: str
    current_market_price: float
    price_trend: str
    demand_level: float
    opportunity_score: float
    recommendation: str


@dataclass
class WorkerSchema:
    """Worker profile schema"""
    id: str
    worker_name: str
    worker_role: str
    productivity_score: float
    overall_score: float
    performance_category: str


@dataclass
class DashboardSchema:
    """Farm dashboard schema"""
    farm: Dict[str, Any]
    production: Dict[str, Any]
    risks: Dict[str, Any]
    predictions: Dict[str, Any]
    markets: Dict[str, Any]
    labor: Dict[str, Any]


@dataclass
class ReportSchema:
    """Weekly report schema"""
    generated_at: str
    farm_id: str
    dashboard: Dict[str, Any]
    production_insights: Dict[str, Any]
    risk_summary: Dict[str, Any]
    market_opportunities: Dict[str, Any]
    labor_insights: Dict[str, Any]


__all__ = [
    "FarmSchema",
    "ProductionSchema",
    "PredictionSchema",
    "RiskSchema",
    "MarketSchema",
    "WorkerSchema",
    "DashboardSchema",
    "ReportSchema",
]
