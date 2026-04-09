"""
Farmer Repository
Data access for Farmer entities
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from app.shared import BaseRepository
from app.farmscore.domain.entities import Farmer
from core.database import DatabaseRepository, get_database_repository


class FarmerRepository(BaseRepository[Farmer]):
    """
    Repository for Farmer entities
    Handles persistence and retrieval
    """
    
    def __init__(self, db: DatabaseRepository):
        super().__init__()
        self.db = db
    
    async def create(self, entity: Farmer) -> Farmer:
        """Create a new farmer"""
        farmer_data = {
            'id': str(entity.id),
            'user_id': entity.user_id,
            'first_name': entity.first_name,
            'last_name': entity.last_name,
            'email': entity.email,
            'phone': entity.phone,
            'farm_size_acres': entity.farm_size_acres,
            'years_farming': entity.years_farming,
            'crop_types': entity.crop_types,
            'livestock_types': entity.livestock_types,
            'coop_membership_years': entity.coop_membership_years,
            'training_hours': entity.training_hours,
            'created_at': entity.created_at,
            'is_active': entity.is_active,
        }
        
        await self.db.insert_one('farmer_profiles', farmer_data)
        self.logger.info(f"Created farmer {entity.id}")
        return entity
    
    async def get_by_id(self, entity_id: UUID | str | int) -> Optional[Farmer]:
        """Get farmer by ID"""
        result = await self.db.select_one(
            'farmer_profiles',
            {'id': str(entity_id)}
        )
        
        if not result:
            return None
        
        return self._map_to_entity(result)
    
    async def get_by_user_id(self, user_id: str) -> Optional[Farmer]:
        """Get farmer by user ID"""
        result = await self.db.select_one(
            'farmer_profiles',
            {'user_id': user_id}
        )
        
        if not result:
            return None
        
        return self._map_to_entity(result)
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[tuple] = None
    ) -> List[Farmer]:
        """List farmers with optional filtering"""
        filters = filters or {}
        results = await self.db.select_many(
            'farmer_profiles',
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
        
        return [self._map_to_entity(r) for r in results]
    
    async def update(self, entity_id: UUID | str | int, data: Dict[str, Any]) -> Farmer:
        """Update farmer"""
        result = await self.db.update_one(
            'farmer_profiles',
            {'id': str(entity_id)},
            data
        )
        
        self.logger.info(f"Updated farmer {entity_id}")
        return self._map_to_entity(result)
    
    async def delete(self, entity_id: UUID | str | int) -> bool:
        """Delete farmer (soft delete)"""
        success = await self.db.soft_delete(
            'farmer_profiles',
            {'id': str(entity_id)}
        )
        
        if success:
            self.logger.info(f"Deleted farmer {entity_id}")
        return bool(success)
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count farmers"""
        filters = filters or {}
        return await self.db.count('farmer_profiles', filters)
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Farmer:
        """Map database record to Farmer entity"""
        return Farmer(
            id=UUID(data['id']) if isinstance(data['id'], str) else data['id'],
            user_id=data['user_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            farm_size_acres=data.get('farm_size_acres', 1.0),
            years_farming=data.get('years_farming', 1),
            crop_types=data.get('crop_types', []),
            livestock_types=data.get('livestock_types', []),
            coop_membership_years=data.get('coop_membership_years', 0),
            training_hours=data.get('training_hours', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True),
        )
