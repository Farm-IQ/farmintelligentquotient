"""
Production Repository
Data access layer for Production entities
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import statistics
import logging
from app.shared import BaseRepository
from app.farmsuite.domain.entities.production import Production
from core.database import DatabaseRepository


class ProductionRepository(BaseRepository[Production]):
    """
    Repository for Production entities  
    Handles all Production CRUD operations and analytics queries
    """
    
    def __init__(self, db: DatabaseRepository):
        """
        Initialize ProductionRepository
        
        Args:
            db: DatabaseRepository instance
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def create(self, entity: Production) -> Production:
        """Create a new production record"""
        production_data = {
            'id': str(entity.id),
            'farm_id': str(entity.farm_id),
            'user_id': str(entity.user_id),
            'crop': entity.crop,
            'yield_kg_per_acre': entity.yield_kg_per_acre,
            'monthly_revenue_kes': entity.monthly_revenue_kes,
            'consistency_score': entity.consistency_score,
            'production_month': entity.production_month,
            'season': entity.season,
        }
        await self.db.insert_one('farm_production', production_data)
        self.logger.info(f"Created production record {entity.id}")
        return entity
    
    async def get_by_id(self, entity_id: UUID | str) -> Optional[Production]:
        """Get production by ID"""
        result = await self.db.select_one('farm_production', {'id': str(entity_id)})
        if not result:
            return None
        return self._map_to_entity(result)
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[Production]:
        """Get list of production records"""
        results = await self.db.select_many(
            'farm_production',
            {},
            offset=skip,
            limit=limit
        )
        return [self._map_to_entity(row) for row in results]
    
    async def update(self, entity: Production) -> Production:
        """Update an existing production record"""
        await self.db.update_one(
            'farm_production',
            {'id': str(entity.id)},
            {
                'crop': entity.crop,
                'yield_kg_per_acre': entity.yield_kg_per_acre,
                'monthly_revenue_kes': entity.monthly_revenue_kes,
                'consistency_score': entity.consistency_score,
                'season': entity.season
            }
        )
        self.logger.info(f"Updated production record {entity.id}")
        return entity
    
    async def delete(self, entity_id: UUID | str) -> bool:
        """Delete a production record"""
        await self.db.delete_one(
            'farm_production',
            {'id': str(entity_id)}
        )
        self.logger.info(f"Deleted production record {entity_id}")
        return True
    
    async def count(self) -> int:
        """Count total production records"""
        result = await self.db.count('farm_production')
        return result if result else 0
    
    async def get_farm_production_history(
        self,
        farm_id: UUID,
        months: int = 12,
        limit: int = 100
    ) -> List[Production]:
        """
        Get production history for a farm
        
        Args:
            farm_id: Farm identifier
            months: Number of months to look back
            limit: Maximum records to return
            
        Returns:
            List of Production entities
        """
        try:
            start_date = datetime.now() - timedelta(days=months * 30)
            response = await self.db.select_many(
                'farm_production',
                {'farm_id': str(farm_id)},
                limit=limit
            )
            # Filter by date
            return [
                self._map_to_entity(row) for row in response
                if row.get("created_at") >= start_date
            ]
        except Exception as e:
            self.logger.error(f"Error fetching production history: {e}")
            return []
    
    async def get_crop_production(
        self,
        farm_id: UUID,
        crop: str
    ) -> List[Production]:
        """
        Get all production records for a specific crop
        
        Args:
            farm_id: Farm identifier
            crop: Crop type
            
        Returns:
            List of Production entities
        """
        try:
            response = await self.db.select_many(
                'farm_production',
                {'farm_id': str(farm_id), 'crop': crop}
            )
            return [self._map_to_entity(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching crop production: {e}")
            return []
    
    async def get_latest_production(self, farm_id: UUID) -> Optional[Production]:
        """
        Get most recent production record
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Most recent Production entity or None
        """
        try:
            response = await self.db.select_many(
                'farm_production',
                {'farm_id': str(farm_id)},
                limit=1,
                order_by=('created_at', False)  # False = descending
            )
            return self._map_to_entity(response[0]) if response else None
        except Exception as e:
            self.logger.error(f"Error fetching latest production: {e}")
            return None
    
    async def get_monthly_production_summary(
        self,
        farm_id: UUID,
        months: int = 12
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get monthly production summary
        
        Args:
            farm_id: Farm identifier
            months: Number of months to summarize
            
        Returns:
            Dictionary mapping month to production summary stats
        """
        try:
            productions = await self.get_farm_production_history(farm_id, months)
            
            summary = {}
            for prod in productions:
                month_key = prod.created_at.strftime("%Y-%m")
                
                if month_key not in summary:
                    summary[month_key] = {
                        "total_yield_kg": 0,
                        "total_revenue": 0,
                        "avg_price_per_kg": 0,
                        "count": 0,
                        "crops": set(),
                    }
                
                summary[month_key]["total_yield_kg"] += prod.yield_kg_per_acre
                summary[month_key]["total_revenue"] += prod.monthly_revenue_kes
                summary[month_key]["count"] += 1
                summary[month_key]["crops"].add(prod.crop)
            
            # Convert sets to lists for JSON serialization
            for month, data in summary.items():
                data["crops"] = list(data["crops"])
                if data["count"] > 0:
                    data["avg_price_per_kg"] = (
                        data["total_revenue"] / max(data["total_yield_kg"], 1)
                    )
            
            return summary
        except Exception as e:
            self.logger.error(f"Error getting monthly summary: {e}")
            return {}
    
    async def get_production_by_crop_and_season(
        self,
        farm_id: UUID,
        crop: str,
        season: str  # "short_rains", "long_rains"
    ) -> List[Production]:
        """
        Get production for specific crop in specific season
        
        Args:
            farm_id: Farm identifier
            crop: Crop type
            season: Season identifier
            
        Returns:
            List of Production entities
        """
        try:
            response = await self.db.select_many(
                'farm_production',
                {'farm_id': str(farm_id), 'crop': crop, 'season': season}
            )
            return [self._map_to_entity(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching seasonal production: {e}")
            return []
    
    async def get_production_efficiency_metrics(
        self,
        farm_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate production efficiency metrics
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with efficiency metrics
        """
        try:
            productions = await self.get_farm_production_history(farm_id, 12)
            
            if not productions:
                return {}
            
            yields = [p.yield_kg_per_acre for p in productions]
            revenues = [p.monthly_revenue_kes for p in productions]
            
            metrics = {
                "avg_yield_kg_per_acre": statistics.mean(yields),
                "total_revenue": sum(revenues),
                "avg_monthly_revenue": statistics.mean(revenues),
                "yield_std_dev": statistics.stdev(yields) if len(yields) > 1 else 0,
                "revenue_std_dev": statistics.stdev(revenues) if len(revenues) > 1 else 0,
                "consistency_score": max(
                    100 - (statistics.stdev(yields) / statistics.mean(yields) * 100)
                    if statistics.mean(yields) > 0 else 0,
                    0
                ) if len(yields) > 1 else 50,
            }
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error calculating efficiency metrics: {e}")
            return {}
    
    async def get_production_by_month(
        self,
        farm_id: UUID,
        month: int,
        limit: int = 12  # Last 12 occurrences of the month
    ) -> List[Production]:
        """
        Get production records from a specific month across multiple years
        Useful for seasonal analysis
        
        Args:
            farm_id: Farm identifier
            month: Month number (1-12)
            limit: Maximum years to include
            
        Returns:
            List of Production entities
        """
        try:
            response = await self.db.select_many(
                'farm_production',
                {'farm_id': str(farm_id)},
                limit=limit * 12
            )
            
            # Filter to specific month
            return [
                self._map_to_entity(row) for row in response
                if row.get("created_at") and row.get("created_at").month == month
            ]
        except Exception as e:
            self.logger.error(f"Error fetching monthly production: {e}")
            return []
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Production:
        """Map database row to Production entity"""
        if isinstance(data, Production):
            return data
        
        return Production(
            id=data.get("id"),
            farm_id=data.get("farm_id"),
            user_id=data.get("user_id"),
            crop=data.get("crop"),
            yield_kg_per_acre=data.get("yield_kg_per_acre", 0),
            monthly_revenue_kes=data.get("monthly_revenue_kes", 0),
            consistency_score=data.get("consistency_score", 50),
            production_month=data.get("production_month"),
            season=data.get("season"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
