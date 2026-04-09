"""
Worker Repository
Data access layer for Worker entities
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from app.shared import BaseRepository
from app.farmsuite.domain.entities.worker import Worker, WorkerRole, ProductivityCategory
from core.database import DatabaseRepository


class WorkerRepository(BaseRepository[Worker]):
    """
    Repository for Worker entities
    Handles all Worker CRUD operations and labor analytics
    """
    
    def __init__(self, db: DatabaseRepository):
        """
        Initialize WorkerRepository
        
        Args:
            db: DatabaseRepository instance
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def get_farm_workers(
        self,
        farm_id: UUID,
        include_inactive: bool = False
    ) -> List[Worker]:
        """
        Get all workers for a farm
        
        Args:
            farm_id: Farm identifier
            include_inactive: Whether to include inactive workers
            
        Returns:
            List of Worker entities
        """
        try:
            response = await self.db.select_many(
                'farm_workers',
                {"farm_id": str(farm_id)}
            )
            
            workers = [self._map_to_entity(row) for row in response]
            
            if not include_inactive:
                workers = [w for w in workers if w.is_active]
            
            return sorted(
                workers,
                key=lambda w: w.overall_score(),
                reverse=True
            )
        except Exception as e:
            self.logger.error(f"Error fetching farm workers: {e}")
            return []
    
    async def get_workers_by_role(
        self,
        farm_id: UUID,
        role: WorkerRole
    ) -> List[Worker]:
        """
        Get workers with specific role
        
        Args:
            farm_id: Farm identifier
            role: Worker role to filter
            
        Returns:
            List of Worker entities
        """
        try:
            response = await self.db.select_many(
                'farm_workers',
                {
                    "farm_id": str(farm_id),
                    "worker_role": role.value if hasattr(role, 'value') else str(role)
                }
            )
            return [self._map_to_entity(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching workers by role: {e}")
            return []
    
    def get_high_performers(
        self,
        farm_id: UUID
    ) -> List[Worker]:
        """
        Get high-performing workers
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of Worker entities with excellent ratings
        """
        try:
            workers = self.get_farm_workers(farm_id)
            return [w for w in workers if w.is_high_performer()]
        except Exception as e:
            self.logger.error(f"Error fetching high performers: {e}")
            return []
    
    def get_workers_needing_support(
        self,
        farm_id: UUID
    ) -> List[Worker]:
        """
        Get workers with performance issues
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of Worker entities needing intervention
        """
        try:
            workers = self.get_farm_workers(farm_id)
            return [w for w in workers if w.needs_intervention()]
        except Exception as e:
            self.logger.error(f"Error fetching workers needing support: {e}")
            return []
    
    async def get_worker_by_name(
        self,
        farm_id: UUID,
        worker_name: str
    ) -> Optional[Worker]:
        """
        Get worker by name
        
        Args:
            farm_id: Farm identifier
            worker_name: Worker's name
            
        Returns:
            Worker entity or None
        """
        try:
            response = await self.db.select_many(
                'farm_workers',
                {
                    "farm_id": str(farm_id),
                    "worker_name": worker_name
                },
                limit=1
            )
            return self._map_to_entity(response[0]) if response else None
        except Exception as e:
            self.logger.error(f"Error fetching worker: {e}")
            return None
    
    def update_worker_performance(
        self,
        worker_id: UUID,
        productivity_score: float,
        quality_score: float,
        attendance_rate: float,
        performance_trend: float
    ) -> Optional[Worker]:
        """
        Update worker performance metrics
        
        Args:
            worker_id: Worker identifier
            productivity_score: Updated productivity (0-100)
            quality_score: Updated quality (0-100)
            attendance_rate: Updated attendance (0-100)
            performance_trend: Trend direction (-1 to 1)
            
        Returns:
            Updated Worker entity
        """
        try:
            data = {
                "productivity_score": productivity_score,
                "quality_score": quality_score,
                "attendance_rate": attendance_rate,
                "performance_trend": performance_trend,
            }
            return self.update(worker_id, data)
        except Exception as e:
            self.logger.error(f"Error updating worker performance: {e}")
            return None
    
    def get_labor_statistics(
        self,
        farm_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive labor statistics
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with labor metrics
        """
        try:
            workers = self.get_farm_workers(farm_id)
            
            if not workers:
                return {"total_workers": 0}
            
            import statistics
            
            # Count by category
            category_counts = {}
            for category in ProductivityCategory:
                count = len([
                    w for w in workers
                    if w.get_productivity_category() == category
                ])
                category_counts[category.value] = count
            
            # Calculate averages
            avg_productivity = statistics.mean([w.productivity_score for w in workers])
            avg_quality = statistics.mean([w.quality_score for w in workers])
            avg_attendance = statistics.mean([w.attendance_rate for w in workers])
            
            # Payroll
            total_daily_cost = sum([
                w.daily_wage or 0 for w in workers if w.is_active
            ])
            
            return {
                "total_workers": len(workers),
                "active_workers": len([w for w in workers if w.is_active]),
                "by_category": category_counts,
                "by_role": {
                    role.value: len(self.get_workers_by_role(farm_id, role))
                    for role in WorkerRole
                },
                "average_productivity": avg_productivity,
                "average_quality": avg_quality,
                "average_attendance": avg_attendance,
                "total_daily_payroll": total_daily_cost,
                "high_performers": len(self.get_high_performers(farm_id)),
                "needs_support": len(self.get_workers_needing_support(farm_id)),
            }
        except Exception as e:
            self.logger.error(f"Error calculating labor statistics: {e}")
            return {}
    
    def record_safety_incident(
        self,
        worker_id: UUID
    ) -> Optional[Worker]:
        """
        Record a safety incident for a worker
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Updated Worker entity
        """
        try:
            worker = self.read(worker_id)
            if not worker:
                return None
            
            data = {"safety_incidents": worker.safety_incidents + 1}
            return self.update(worker_id, data)
        except Exception as e:
            self.logger.error(f"Error recording safety incident: {e}")
            return None
    
    def add_training_recommendation(
        self,
        worker_id: UUID,
        recommendation: str
    ) -> Optional[Worker]:
        """
        Add training recommendation for a worker
        
        Args:
            worker_id: Worker identifier
            recommendation: Training recommendation
            
        Returns:
            Updated Worker entity
        """
        try:
            worker = self.read(worker_id)
            if not worker:
                return None
            
            recommendations = worker.training_recommendations + [recommendation]
            data = {"training_recommendations": recommendations}
            return self.update(worker_id, data)
        except Exception as e:
            self.logger.error(f"Error adding training recommendation: {e}")
            return None
    
    def get_cost_per_output_analysis(
        self,
        farm_id: UUID
    ) -> Dict[str, Any]:
        """
        Analyze cost-per-output efficiency for workers
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with efficiency analysis
        """
        try:
            workers = self.get_farm_workers(farm_id)
            
            efficiency_data = []
            for worker in workers:
                efficiency = worker.calculate_labor_efficiency()
                efficiency_data.append({
                    "worker": worker.worker_name,
                    "role": worker.worker_role.value,
                    "efficiency_score": efficiency,
                    "productivity": worker.productivity_score,
                    "cost_per_task": worker.cost_per_task,
                })
            
            # Sort by efficiency
            return sorted(efficiency_data, key=lambda x: x["efficiency_score"], reverse=True)
        except Exception as e:
            self.logger.error(f"Error analyzing cost efficiency: {e}")
            return []
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Worker:
        """Map database row to Worker entity"""
        if isinstance(data, Worker):
            return data
        
        return Worker(
            id=data.get("id"),
            farm_id=data.get("farm_id"),
            user_id=data.get("user_id"),
            worker_name=data.get("worker_name"),
            worker_role=WorkerRole(data.get("worker_role", "field_worker")),
            start_date=data.get("start_date"),
            hourly_wage=data.get("hourly_wage"),
            daily_wage=data.get("daily_wage"),
            tasks_completed=data.get("tasks_completed", 0),
            total_hours_worked=data.get("total_hours_worked", 0),
            productivity_score=data.get("productivity_score", 50),
            attendance_rate=data.get("attendance_rate", 100),
            quality_score=data.get("quality_score", 50),
            cost_per_task=data.get("cost_per_task"),
            tasks_per_day=data.get("tasks_per_day", 0),
            output_per_hour=data.get("output_per_hour", 0),
            error_rate=data.get("error_rate", 0),
            safety_incidents=data.get("safety_incidents", 0),
            certifications=data.get("certifications", []),
            strengths=data.get("strengths", []),
            improvement_areas=data.get("improvement_areas", []),
            training_recommendations=data.get("training_recommendations", []),
            recent_performance_notes=data.get("recent_performance_notes", []),
            is_active=data.get("is_active", True),
            performance_trend=data.get("performance_trend", 0),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
