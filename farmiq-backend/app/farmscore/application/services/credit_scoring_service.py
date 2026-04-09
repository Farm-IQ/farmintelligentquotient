"""
Credit Scoring Application Service
Orchestrates domain logic and data access
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging

from app.shared import BaseService, ValidationError, EntityNotFoundError, CalculationError
from app.farmscore.domain import (
    CreditCalculationService,
    Farmer,
    CreditScore,
    CreditRiskLevel,
)
from app.farmscore.application.repositories import FarmerRepository, CreditScoreRepository
from app.farmscore.application.schemas import (
    CreditScoringRequest,
    CreditScoringResponse,
)


class CreditScoringApplicationService(BaseService):
    """
    Application service for credit scoring
    Orchestrates domain logic with infrastructure
    """
    
    def __init__(
        self,
        farmer_repo: FarmerRepository,
        credit_repo: CreditScoreRepository,
        domain_service: CreditCalculationService
    ):
        super().__init__()
        self.farmer_repo = farmer_repo
        self.credit_repo = credit_repo
        self.domain_service = domain_service
    
    async def validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input data"""
        await self.domain_service.validate_input(input_data)
    
    async def score_farmer(
        self,
        request: CreditScoringRequest,
        farmer_data: Optional[Dict[str, Any]] = None
    ) -> CreditScore:
        """
        Score a farmer using ensemble model and domain logic
        
        Process:
        1. Check cache if not recalculating
        2. Fetch or create farmer profile
        3. Calculate component scores
        4. Calculate final credit score
        5. Store result with TTL
        
        Args:
            request: Credit scoring request
            farmer_data: Optional enriched farmer data
            
        Returns:
            CreditScore entity
        """
        # Step 1: Check cache
        if not request.recalculate:
            cached_score = await self.credit_repo.get_cached_valid_score(
                request.farmer_id or request.user_id
            )
            if cached_score:
                self.logger.info(f"Returning cached score for {request.user_id}")
                return cached_score
        
        # Step 2: Fetch farmer or use provided data
        if request.farmer_id:
            farmer = await self.farmer_repo.get_by_id(request.farmer_id)
            if not farmer:
                raise EntityNotFoundError("Farmer", request.farmer_id)
        else:
            farmer = await self.farmer_repo.get_by_user_id(request.user_id)
        
        # Merge provided data with farmer profile
        scoring_data = farmer_data or await self._get_farmer_scoring_data(farmer)
        
        # Step 3: Calculate component scores
        financial_health = self.domain_service.calculate_financial_health_score(
            request.monthly_revenue,
            request.monthly_expense,
            scoring_data.get('liquid_savings', 0)
        )
        
        experience = self.domain_service.calculate_experience_score(
            scoring_data.get('years_farming', 1),
            scoring_data.get('training_hours', 0),
            scoring_data.get('advisory_visits', 0)
        )
        
        support_network = self.domain_service.calculate_support_network_score(
            scoring_data.get('coop_membership_years', 0),
            scoring_data.get('group_membership', False)
        )
        
        production_efficiency = self.domain_service.calculate_production_efficiency_score(
            scoring_data.get('farm_size_acres', 1),
            scoring_data.get('yield_kg_per_acre', 20),
            len(farmer.crop_types) if farmer else 1
        )
        
        # Step 4: Calculate final score
        credit_score = self.domain_service.calculate_credit_score(
            financial_health,
            experience,
            support_network,
            production_efficiency
        )
        
        risk_level = self.domain_service.determine_risk_level(credit_score)
        default_probability = self.domain_service.calculate_default_probability(risk_level)
        approval_likelihood = self.domain_service.calculate_approval_likelihood(
            credit_score,
            default_probability
        )
        
        recommended_limit = self.domain_service.recommend_credit_limit(
            request.monthly_revenue,
            scoring_data.get('years_farming', 1),
            credit_score
        )
        
        recommended_rate = self.domain_service.recommend_interest_rate(
            risk_level,
            credit_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            credit_score,
            financial_health,
            experience,
            support_network
        )
        
        # Step 5: Create and store credit score
        credit_score_entity = CreditScore(
            farmer_id=UUID(request.farmer_id) if request.farmer_id else UUID(farmer.id) if farmer else UUID(),
            user_id=request.user_id,
            score=credit_score,
            risk_level=risk_level,
            default_probability=default_probability,
            approval_likelihood=approval_likelihood,
            recommended_credit_limit_kes=recommended_limit,
            recommended_loan_term_months=24,  # Default to 24 months
            recommended_interest_rate=recommended_rate,
            improvement_recommendations=recommendations,
        )
        
        await self.credit_repo.create(credit_score_entity)
        self.log_operation("CREDIT_SCORE", "Farmer", request.user_id, "created")
        
        return credit_score_entity
    
    def _generate_recommendations(
        self,
        score: float,
        financial_health: float,
        experience: float,
        support_network: float
    ) -> list:
        """Generate improvement recommendations"""
        recommendations = []
        
        if financial_health < 15:
            recommendations.append("Improve expense-to-revenue ratio by optimizing farm costs")
        
        if experience < 10:
            recommendations.append("Increase agricultural training and skill development")
        
        if support_network < 10:
            recommendations.append("Join agricultural cooperatives for better market access")
        
        if score < 50:
            recommendations.append("Diversify crop production to improve resilience")
        
        if score < 60:
            recommendations.append("Maintain consistent financial records for credibility")
        
        return recommendations[:3]  # Top 3 recommendations
    
    async def _get_farmer_scoring_data(self, farmer: Optional[Farmer]) -> Dict[str, Any]:
        """Extract scoring data from farmer profile"""
        if not farmer:
            return {
                'farm_size_acres': 1.0,
                'years_farming': 1,
                'training_hours': 0,
                'coop_membership_years': 0,
                'yield_kg_per_acre': 20,
                'liquid_savings': 0,
                'advisory_visits': 0,
                'group_membership': False,
            }
        
        return {
            'farm_size_acres': farmer.farm_size_acres,
            'years_farming': farmer.years_farming,
            'training_hours': farmer.training_hours,
            'coop_membership_years': farmer.coop_membership_years,
            'yield_kg_per_acre': 20,  # Default, would come from actual data
            'liquid_savings': 0,  # Would come from financial data
            'advisory_visits': 0,  # Would come from interaction history
            'group_membership': len(farmer.crop_types) > 1,  # Proxy for group engagement
        }
