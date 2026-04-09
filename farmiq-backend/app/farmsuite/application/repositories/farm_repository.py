"""
Farm Repository
Data access layer for Farm entities
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from app.shared import BaseRepository
from app.farmsuite.domain.entities.farm import Farm
from core.database import DatabaseRepository
import logging


class FarmRepository(BaseRepository[Farm]):
    """
    Repository for Farm entities
    Handles all Farm CRUD operations and queries
    """
    
    def __init__(self, db: DatabaseRepository):
        """
        Initialize FarmRepository
        
        Args:
            db: DatabaseRepository instance
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def create(self, entity: Farm) -> Farm:
        """Create a new farm"""
        farm_data = {
            'id': str(entity.id),
            'user_id': str(entity.user_id),
            'farm_name': entity.farm_name,
            'total_acres': entity.total_acres,
            'location': entity.location,
            'crop_types': entity.crop_types,
            'livestock_types': entity.livestock_types,
            'soil_type': entity.soil_type,
            'rainfall_zone': entity.rainfall_zone,
            'irrigation_method': entity.irrigation_method,
            'worker_count': entity.worker_count,
            'equipment_value_kes': entity.equipment_value_kes,
        }
        await self.db.insert_one('farms', farm_data)
        self.logger.info(f"Created farm {entity.id}")
        return entity
    
    async def get_by_id(self, entity_id: UUID | str) -> Optional[Farm]:
        """Get farm by ID"""
        result = await self.db.select_one('farms', {'id': str(entity_id)})
        if not result:
            return None
        return self._map_to_farm(result)
    
    async def get_farms_by_user(self, user_id: str, limit: int = 100) -> List[Farm]:
        """
        Get all farms for a specific user
        
        Args:
            user_id: User identifier
            limit: Maximum number of farms to return
            
        Returns:
            List of Farm entities
        """
        try:
            response = await self.db.select_many(
                'farms',
                {'user_id': user_id},
                limit=limit
            )
            return [self._map_to_farm(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching farms for user {user_id}: {e}")
            return []
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[Farm]:
        """Get list of farms"""
        results = await self.db.select_many(
            'farms',
            {},
            offset=skip,
            limit=limit
        )
        return [self._map_to_farm(row) for row in results]
    
    async def update(self, entity: Farm) -> Farm:
        """Update an existing farm"""
        farm_data = {
            'farm_name': entity.farm_name,
            'total_acres': entity.total_acres,
            'location': entity.location,
            'crop_types': entity.crop_types,
            'livestock_types': entity.livestock_types,
            'soil_type': entity.soil_type,
            'rainfall_zone': entity.rainfall_zone,
            'irrigation_method': entity.irrigation_method,
            'worker_count': entity.worker_count,
            'equipment_value_kes': entity.equipment_value_kes,
        }
        await self.db.update_one(
            'farms',
            {'id': str(entity.id)},
            farm_data
        )
        self.logger.info(f"Updated farm {entity.id}")
        return entity
    
    async def delete(self, entity_id: UUID | str) -> bool:
        """Delete a farm"""
        result = await self.db.delete_one(
            'farms',
            {'id': str(entity_id)}
        )
        self.logger.info(f"Deleted farm {entity_id}")
        return result
    
    async def count(self) -> int:
        """Count total farms"""
        result = await self.db.count('farms')
        return result if result else 0
    
    def _map_to_farm(self, row: Dict[str, Any]) -> Farm:
        """Map database row to Farm entity"""
        return Farm(
            id=row.get('id'),
            user_id=row.get('user_id'),
            farm_name=row.get('farm_name'),
            total_acres=row.get('total_acres'),
            location=row.get('location'),
            crop_types=row.get('crop_types', []),
            livestock_types=row.get('livestock_types', []),
            soil_type=row.get('soil_type'),
            rainfall_zone=row.get('rainfall_zone'),
            irrigation_method=row.get('irrigation_method'),
            worker_count=row.get('worker_count', 0),
            equipment_value_kes=row.get('equipment_value_kes', 0),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
    
    async def get_farm_by_name(self, farm_name: str, user_id: str) -> Optional[Farm]:
        """
        Get farm by name for a specific user
        
        Args:
            farm_name: Farm name
            user_id: User identifier
            
        Returns:
            Farm entity or None if not found
        """
        try:
            response = await self.db.select_many(
                'farms',
                {"farm_name": farm_name, "user_id": user_id},
                limit=1
            )
            return self._map_to_farm(response[0]) if response else None
        except Exception as e:
            self.logger.error(f"Error fetching farm {farm_name}: {e}")
            return None
    
    async def get_farms_by_location(self, location: str, limit: int = 50) -> List[Farm]:
        """
        Get farms by location (useful for regional analytics)
        
        Args:
            location: Location identifier
            limit: Maximum results
            
        Returns:
            List of Farm entities
        """
        try:
            response = await self.db.select_many(
                'farms',
                {"location": location},
                limit=limit
            )
            return [self._map_to_farm(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching farms in {location}: {e}")
            return []
    
    async def get_top_healthy_farms(self, limit: int = 10) -> List[Farm]:
        """
        Get farms with highest health scores
        
        Args:
            limit: Number of farms to return
            
        Returns:
            List of Farm entities ordered by health score
        """
        try:
            # Note: Supabase ordering requires the column to be indexed for best performance
            response = await self.db.select_many(
                'farms',
                filters={},
                limit=limit,
                order_by=('health_score', False)  # False = descending
            )
            return [self._map_to_farm(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching top healthy farms: {e}")
            return []
    
    async def update_farm_health_score(
        self,
        farm_id: UUID,
        health_score: float
    ) -> Optional[Farm]:
        """
        Update farm health score
        
        Args:
            farm_id: Farm identifier
            health_score: New health score (0-100)
            
        Returns:
            Updated Farm entity or None if not found
        """
        try:
            await self.db.execute_query(
                "UPDATE farms SET health_score = $1 WHERE id = $2",
                [health_score, str(farm_id)]
            )
            return await self.get_by_id(farm_id)
        except Exception as e:
            self.logger.error(f"Error updating farm health score: {e}")
            return None
    
    async def update_farm_diversification(
        self,
        farm_id: UUID,
        diversification_index: float,
        crops: List[str]
    ) -> Optional[Farm]:
        """
        Update farm diversification metrics
        
        Args:
            farm_id: Farm identifier
            diversification_index: Diversification score (0-1)
            crops: List of crops being grown
            
        Returns:
            Updated Farm entity
        """
        try:
            await self.db.execute_query(
                "UPDATE farms SET diversification_index = $1, crop_types = $2 WHERE id = $3",
                [diversification_index, crops, str(farm_id)]
            )
            return await self.get_by_id(farm_id)
        except Exception as e:
            self.logger.error(f"Error updating farm diversification: {e}")
            return None
    
    async def get_farm_stats(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive farm statistics
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with farm statistics
        """
        try:
            farm = await self.get_by_id(farm_id)
            if not farm:
                return {}
            
            stats = {
                "farm_id": str(farm.id),
                "farm_name": farm.farm_name,
                "total_acres": farm.total_acres,
                "location": farm.location,
                "created_at": farm.created_at,
                "last_updated": farm.updated_at,
            }
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting farm stats: {e}")
            return {}
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Farm:
        """Map database row to Farm entity"""
        if isinstance(data, Farm):
            return data
        
        return Farm(
            id=data.get("id"),
            user_id=data.get("user_id"),
            farm_name=data.get("farm_name"),
            total_acres=data.get("total_acres"),
            location=data.get("location"),
            crops=data.get("crops", []),
            diversification_index=data.get("diversification_index", 0),
            health_score=data.get("health_score", 50),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
