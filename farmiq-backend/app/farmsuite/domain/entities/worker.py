"""
Worker Domain Entity
Represents farm workers and labor productivity metrics
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID
from app.shared import BaseEntity, validate_range, validate_not_empty


class WorkerRole(str, Enum):
    """Worker roles on the farm"""
    SUPERVISOR = "supervisor"
    FIELD_WORKER = "field_worker"
    EQUIPMENT_OPERATOR = "equipment_operator"
    IRRIGATION_SPECIALIST = "irrigation_specialist"
    PEST_SCOUT = "pest_scout"
    HARVEST_MANAGER = "harvest_manager"
    SEASONAL = "seasonal"


class ProductivityCategory(str, Enum):
    """Worker productivity categories"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    UNDERPERFORMING = "underperforming"


@dataclass
class Worker(BaseEntity):
    """
    Worker domain entity
    Represents farm worker productivity and performance metrics
    """
    farm_id: UUID = None
    user_id: str = ""
    worker_name: str = ""
    worker_role: WorkerRole = WorkerRole.FIELD_WORKER
    start_date: datetime = field(default_factory=datetime.utcnow)  # When they started
    hourly_wage: Optional[float] = None
    daily_wage: Optional[float] = None
    tasks_completed: int = 0
    total_hours_worked: float = 0.0
    productivity_score: float = 50.0  # 0-100
    attendance_rate: float = 100.0  # 0-100
    quality_score: float = 50.0  # 0-100 (work quality)
    cost_per_task: Optional[float] = None
    tasks_per_day: float = 0.0
    output_per_hour: float = 0.0  # Units/hour depending on task
    error_rate: float = 0.0  # % of tasks with errors
    safety_incidents: int = 0
    certifications: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    training_recommendations: List[str] = field(default_factory=list)
    recent_performance_notes: List[str] = field(default_factory=list)
    is_active: bool = True
    performance_trend: float = 0.0  # -1 to 1 (declining to improving)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate worker data"""
        validate_not_empty(self.worker_name, "worker_name")
        validate_range(self.productivity_score, 0, 100, "productivity_score")
        validate_range(self.attendance_rate, 0, 100, "attendance_rate")
        validate_range(self.quality_score, 0, 100, "quality_score")
        validate_range(self.error_rate, 0, 100, "error_rate")
        validate_range(self.performance_trend, -1, 1, "performance_trend")
    
    def get_productivity_category(self) -> ProductivityCategory:
        """Categorize worker productivity"""
        score = self.productivity_score
        if score >= 85:
            return ProductivityCategory.EXCELLENT
        elif score >= 70:
            return ProductivityCategory.GOOD
        elif score >= 55:
            return ProductivityCategory.AVERAGE
        elif score >= 40:
            return ProductivityCategory.BELOW_AVERAGE
        else:
            return ProductivityCategory.UNDERPERFORMING
    
    def get_performance_summary(self) -> str:
        """Get human-readable performance summary"""
        category = self.get_productivity_category()
        summaries = {
            ProductivityCategory.EXCELLENT: f"⭐⭐⭐ {self.worker_name} is a top performer",
            ProductivityCategory.GOOD: f"⭐⭐ {self.worker_name} is performing well",
            ProductivityCategory.AVERAGE: f"⭐ {self.worker_name} is meeting expectations",
            ProductivityCategory.BELOW_AVERAGE: f"⚠️  {self.worker_name} needs support",
            ProductivityCategory.UNDERPERFORMING: f"🔴 {self.worker_name} requires intervention",
        }
        return summaries.get(category, "Unknown status")
    
    def calculate_overall_score(self) -> float:
        """
        Calculate overall worker score
        Combines productivity, quality, and attendance
        """
        productivity_weight = 0.4
        quality_weight = 0.35
        attendance_weight = 0.25
        
        overall = (
            self.productivity_score * productivity_weight +
            self.quality_score * quality_weight +
            self.attendance_rate * attendance_weight
        )
        
        return min(overall, 100.0)
    
    def is_high_performer(self) -> bool:
        """Check if worker is high performer"""
        return self.get_productivity_category() in [
            ProductivityCategory.EXCELLENT,
            ProductivityCategory.GOOD
        ]
    
    def needs_intervention(self) -> bool:
        """Check if worker needs performance intervention"""
        return self.get_productivity_category() in [
            ProductivityCategory.BELOW_AVERAGE,
            ProductivityCategory.UNDERPERFORMING
        ]
    
    def get_performance_trend_description(self) -> str:
        """Get human-readable performance trend"""
        if self.performance_trend > 0.3:
            return "📈 Improving rapidly"
        elif self.performance_trend > 0.1:
            return "↗️  Slight improvement"
        elif self.performance_trend < -0.3:
            return "📉 Declining rapidly"
        elif self.performance_trend < -0.1:
            return "↘️  Slight decline"
        else:
            return "→ Stable performance"
    
    def calculate_labor_efficiency(self) -> float:
        """
        Calculate labor efficiency (output per cost)
        Returns: ratio of output to cost
        Higher is better
        """
        if self.cost_per_task is None or self.cost_per_task == 0:
            return 0
        
        # Efficiency = (productivity * quality) / cost
        return (self.productivity_score * self.quality_score / 10000) / self.cost_per_task
    
    def get_roi_on_training(self, training_cost: float, months_since_training: int) -> float:
        """
        Calculate ROI on training investment
        Returns: % return on training investment per month
        """
        if months_since_training == 0:
            return 0
        
        # Assumes improved workers save time (reduce cost) or increase output
        monthly_improvement = self.performance_trend
        total_improvement = monthly_improvement * months_since_training
        
        if training_cost == 0:
            return 0
        
        # Rough estimate: 1 point improvement = 1% efficiency gain = 0.5% cost savings
        monthly_savings = total_improvement * 0.5 * self.daily_wage if self.daily_wage else 0
        
        return (monthly_savings * months_since_training / training_cost) * 100
    
    def get_action_items(self) -> List[str]:
        """Get recommended action items for worker management"""
        actions = []
        
        # Attendance issues
        if self.attendance_rate < 80:
            actions.append(f"⚠️  Address attendance issue ({self.attendance_rate:.0f}%)")
        
        # Quality issues
        if self.error_rate > 20:
            actions.append(f"📋 Provide quality training (error rate: {self.error_rate:.0f}%)")
        
        # Safety issues
        if self.safety_incidents > 0:
            actions.append(f"🛡️  Review safety protocols (incidents: {self.safety_incidents})")
        
        # Performance decline
        if self.performance_trend < -0.3:
            actions.append("📞 Schedule performance review and support conversation")
        
        # Training opportunities
        if self.training_recommendations:
            actions.append(f"📚 Provide training: {self.training_recommendations[0]}")
        
        # Recognition for high performers
        if self.is_high_performer():
            actions.append("🎉 Consider recognition or advancement opportunity")
        
        return actions if actions else ["✓ No action items needed"]
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'farm_id': str(self.farm_id),
            'user_id': self.user_id,
            'worker_role': self.worker_role.value,
            'productivity_category': self.get_productivity_category().value,
            'overall_score': self.calculate_overall_score(),
            'performance_summary': self.get_performance_summary(),
            'performance_trend': self.get_performance_trend_description(),
            'is_high_performer': self.is_high_performer(),
            'needs_intervention': self.needs_intervention(),
            'labor_efficiency': self.calculate_labor_efficiency(),
            'action_items': self.get_action_items(),
        })
        return base_dict
