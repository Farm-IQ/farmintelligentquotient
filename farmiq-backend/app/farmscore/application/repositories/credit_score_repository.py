"""
Credit Score Repository
Data access for CreditScore entities
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.shared import BaseRepository
from app.farmscore.domain.entities import CreditScore, CreditRiskLevel
from core.database import DatabaseRepository


class CreditScoreRepository(BaseRepository[CreditScore]):
    """
    Repository for CreditScore entities
    Handles persistence and retrieval of credit assessments
    """
    
    def __init__(self, db: DatabaseRepository):
        super().__init__()
        self.db = db
    
    async def create(self, entity: CreditScore) -> CreditScore:
        """Create a new credit score record"""
        credit_data = {
            'id': str(entity.id),
            'farmer_id': str(entity.farmer_id),
            'user_id': entity.user_id,
            'score': entity.score,
            'risk_level': entity.risk_level.value,
            'default_probability': entity.default_probability,
            'approval_likelihood': entity.approval_likelihood,
            'recommended_credit_limit_kes': entity.recommended_credit_limit_kes,
            'recommended_loan_term_months': entity.recommended_loan_term_months,
            'recommended_interest_rate': entity.recommended_interest_rate,
            'shap_explanation': entity.shap_explanation,
            'improvement_recommendations': entity.improvement_recommendations,
            'model_version': entity.model_version,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'is_active': entity.is_active,
        }
        
        await self.db.insert_one('farmiq_credit_profiles', credit_data)
        self.logger.info(f"Created credit score {entity.id} for farmer {entity.farmer_id}")
        return entity
    
    async def get_by_id(self, entity_id: UUID | str | int) -> Optional[CreditScore]:
        """Get credit score by ID"""
        result = await self.db.select_one(
            'farmiq_credit_profiles',
            {'id': str(entity_id)}
        )
        
        if not result:
            return None
        
        return self._map_to_entity(result)
    
    async def get_latest_by_farmer(self, farmer_id: UUID | str) -> Optional[CreditScore]:
        """Get latest credit score for a farmer"""
        results = await self.db.select_many(
            'farmiq_credit_profiles',
            filters={'farmer_id': str(farmer_id)},
            limit=1,
            order_by=('created_at', False)
        )
        
        if not results:
            return None
        
        return self._map_to_entity(results[0])
    
    async def get_latest_by_user(self, user_id: str) -> Optional[CreditScore]:
        """Get latest credit score for a user"""
        results = await self.db.select_many(
            'farmiq_credit_profiles',
            filters={'user_id': user_id},
            limit=1,
            order_by=('created_at', False)
        )
        
        if not results:
            return None
        
        return self._map_to_entity(results[0])
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[tuple] = None
    ) -> List[CreditScore]:
        """List credit scores with optional filtering"""
        filters = filters or {}
        results = await self.db.select_many(
            'farmiq_credit_profiles',
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by or ('created_at', False)
        )
        
        return [self._map_to_entity(r) for r in results]
    
    async def update(self, entity_id: UUID | str | int, data: Dict[str, Any]) -> CreditScore:
        """Update credit score"""
        data['updated_at'] = datetime.utcnow()
        result = await self.db.update_one(
            'farmiq_credit_profiles',
            {'id': str(entity_id)},
            data
        )
        
        self.logger.info(f"Updated credit score {entity_id}")
        return self._map_to_entity(result)
    
    async def delete(self, entity_id: UUID | str | int) -> bool:
        """Delete credit score (soft delete)"""
        success = await self.db.soft_delete(
            'farmiq_credit_profiles',
            {'id': str(entity_id)}
        )
        
        if success:
            self.logger.info(f"Deleted credit score {entity_id}")
        return bool(success)
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count credit scores"""
        filters = filters or {}
        return await self.db.count('farmiq_credit_profiles', filters)
    
    async def get_cached_valid_score(self, farmer_id: UUID | str) -> Optional[CreditScore]:
        """Get cached valid credit score for farmer (TTL check)"""
        score = await self.get_latest_by_farmer(farmer_id)
        
        if score and score.is_cache_valid():
            return score
        
        return None
    
    def _map_to_entity(self, data: Dict[str, Any]) -> CreditScore:
        """Map database record to CreditScore entity"""
        return CreditScore(
            id=UUID(data['id']) if isinstance(data['id'], str) else data['id'],
            farmer_id=UUID(data['farmer_id']) if isinstance(data['farmer_id'], str) else data['farmer_id'],
            user_id=data['user_id'],
            score=data['score'],
            risk_level=CreditRiskLevel(data['risk_level']),
            default_probability=data['default_probability'],
            approval_likelihood=data['approval_likelihood'],
            recommended_credit_limit_kes=data['recommended_credit_limit_kes'],
            recommended_loan_term_months=data['recommended_loan_term_months'],
            recommended_interest_rate=data['recommended_interest_rate'],
            shap_explanation=data.get('shap_explanation', {}),
            improvement_recommendations=data.get('improvement_recommendations', []),
            model_version=data.get('model_version', '1.0'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True),
        )
