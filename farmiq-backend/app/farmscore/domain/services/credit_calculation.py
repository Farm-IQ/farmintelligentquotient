"""
Credit Scoring Domain Service
Pure business logic for credit calculations
"""

from typing import Dict, Any, List, Optional
from app.shared import BaseService, ValidationError, CalculationError
from app.farmscore.domain.entities import CreditScore, CreditRiskLevel, Farmer


class CreditCalculationService(BaseService):
    """
    Domain service for credit calculations
    Pure business logic - no database or ML models
    """
    
    async def validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input data for credit scoring"""
        required_fields = [
            'farm_size_acres', 'years_farming', 'monthly_revenue',
            'monthly_expense', 'training_hours', 'coop_membership_years'
        ]
        for field in required_fields:
            if field not in input_data:
                raise ValidationError(f"Missing required field: {field}")
    
    def calculate_financial_health_score(
        self,
        monthly_revenue: float,
        monthly_expense: float,
        liquid_savings: float
    ) -> float:
        """
        Calculate financial health score (0-30 points)
        
        Factors:
        - Revenue stability
        - Expense ratio
        - Liquidity
        """
        if monthly_revenue <= 0:
            return 0.0
        
        # Revenue-to-expense ratio (ideal is 1.3+)
        expense_ratio = monthly_expense / monthly_revenue
        ratio_score = min(30 * max(0, (1.3 - expense_ratio) / 0.5), 30)
        
        return max(0, ratio_score)
    
    def calculate_experience_score(
        self,
        years_farming: int,
        training_hours: int,
        advisory_visits: int = 0
    ) -> float:
        """
        Calculate experience score (0-20 points)
        
        Factors:
        - Years of farming
        - Training received
        - Advisory engagement
        """
        # Years of experience (0-10 points, 10 years = 10 points)
        years_score = min(10 * (years_farming / 10), 10)
        
        # Training (0-7 points, 100 hours = 7 points)
        training_score = min(7 * (training_hours / 100), 7)
        
        # Advisory engagement (0-3 points, 12 visits/year = 3 points)
        advisory_score = min(3 * (advisory_visits / 12), 3)
        
        return min(years_score + training_score + advisory_score, 20)
    
    def calculate_support_network_score(
        self,
        coop_membership_years: int,
        group_membership: bool = False
    ) -> float:
        """
        Calculate support network score (0-20 points)
        
        Factors:
        - Cooperative membership
        - Group participation
        """
        coop_score = min(10 * (coop_membership_years / 5), 10)
        group_score = 10 if group_membership else 0
        
        return coop_score + group_score
    
    def calculate_production_efficiency_score(
        self,
        farm_size_acres: float,
        yield_kg_per_acre: float,
        crop_diversity: int = 1
    ) -> float:
        """
        Calculate production efficiency score (0-30 points)
        
        Factors:
        - Farm size appropriateness
        - Yield performance
        - Crop diversity
        """
        # Farm scale score (0-10, optimal 2-5 acres)
        if 0.5 <= farm_size_acres <= 5:
            scale_score = 10
        elif farm_size_acres < 0.5 or farm_size_acres > 10:
            scale_score = 5
        else:
            scale_score = 8
        
        # Yield score (0-12, reference: 40kg/acre for maize)
        yield_score = min(12 * (yield_kg_per_acre / 40), 12)
        
        # Diversity score (0-8, 3+ crops = 8)
        diversity_score = min(8 * (crop_diversity / 3), 8)
        
        return scale_score + yield_score + diversity_score
    
    def calculate_credit_score(
        self,
        financial_health: float,
        experience: float,
        support_network: float,
        production_efficiency: float
    ) -> float:
        """
        Calculate final credit score (0-100)
        
        Combines all component scores with weighted average
        """
        # Total possible: 100 points
        # Weights: financial (30%), experience (20%), support network (20%), production (30%)
        score = (
            financial_health * 0.30 +
            experience * 0.20 +
            support_network * 0.20 +
            production_efficiency * 0.30
        )
        
        return min(max(score, 0), 100)
    
    def determine_risk_level(self, score: float) -> CreditRiskLevel:
        """Determine risk level from score"""
        if score >= 80:
            return CreditRiskLevel.VERY_LOW
        elif score >= 65:
            return CreditRiskLevel.LOW
        elif score >= 50:
            return CreditRiskLevel.MEDIUM
        elif score >= 35:
            return CreditRiskLevel.HIGH
        else:
            return CreditRiskLevel.VERY_HIGH
    
    def calculate_default_probability(self, risk_level: CreditRiskLevel) -> float:
        """Calculate probability of default from risk level"""
        probability_map = {
            CreditRiskLevel.VERY_LOW: 0.02,
            CreditRiskLevel.LOW: 0.08,
            CreditRiskLevel.MEDIUM: 0.20,
            CreditRiskLevel.HIGH: 0.35,
            CreditRiskLevel.VERY_HIGH: 0.60,
        }
        return probability_map.get(risk_level, 0.5)
    
    def calculate_approval_likelihood(
        self,
        credit_score: float,
        default_probability: float
    ) -> float:
        """Calculate likelihood of loan approval"""
        # Score-based component (0-1)
        score_component = credit_score / 100.0
        
        # Default probability component (inverse)
        default_component = 1 - default_probability
        
        # Combined (65% score, 35% default)
        likelihood = (score_component * 0.65) + (default_component * 0.35)
        
        return min(max(likelihood, 0), 1)
    
    def recommend_credit_limit(
        self,
        monthly_revenue: float,
        years_farming: int,
        credit_score: float
    ) -> float:
        """
        Recommend credit limit in KES
        
        Based on:
        - Monthly revenue capacity
        - Experience
        - Credit score
        """
        # Base: 3-4 months of revenue
        base_multiplier = 3 if credit_score < 50 else (4 if credit_score < 70 else 5)
        base_limit = monthly_revenue * base_multiplier
        
        # Experience adjustment
        experience_factor = min(1 + (years_farming / 20), 1.5)
        
        # Score adjustment
        if credit_score < 40:
            score_factor = 0.5
        elif credit_score < 60:
            score_factor = 0.8
        else:
            score_factor = 1.0
        
        limit = base_limit * experience_factor * score_factor
        
        # Cap at reasonable levels
        return min(max(limit, 10000), 1000000)
    
    def recommend_interest_rate(
        self,
        risk_level: CreditRiskLevel,
        credit_score: float
    ) -> float:
        """
        Recommend interest rate (%)
        
        Base rate: 8%, adjusted by risk
        """
        base_rate = 8.0
        
        rate_adjustments = {
            CreditRiskLevel.VERY_LOW: -2.0,  # 6%
            CreditRiskLevel.LOW: -1.0,       # 7%
            CreditRiskLevel.MEDIUM: 0.0,     # 8%
            CreditRiskLevel.HIGH: 2.0,       # 10%
            CreditRiskLevel.VERY_HIGH: 4.0,  # 12%
        }
        
        adjustment = rate_adjustments.get(risk_level, 0)
        rate = base_rate + adjustment
        
        return min(max(rate, 2.0), 25.0)  # Between 2% and 25%
