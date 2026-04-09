"""
Risk Repository
Data access layer for Risk entities
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging
from app.shared import BaseRepository
from app.farmsuite.domain.entities.risk import Risk, RiskCategory, RiskSeverity
from core.database import DatabaseRepository


class RiskRepository(BaseRepository[Risk]):
    """
    Repository for Risk entities
    Handles all Risk CRUD operations and query logic
    """
    
    def __init__(self, db: DatabaseRepository):
        """
        Initialize RiskRepository
        
        Args:
            db: DatabaseRepository instance
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def get_farm_risks(
        self,
        farm_id: UUID,
        limit: int = 100
    ) -> List[Risk]:
        """
        Get all risks identified for a farm
        
        Args:
            farm_id: Farm identifier
            limit: Maximum risks to return
            
        Returns:
            List of Risk entities
        """
        try:
            response = await self.db.select_many(
                'farm_risks',
                {'farm_id': str(farm_id)},
                limit=limit
            )
            return sorted(
                [self._map_to_entity(row) for row in response],
                key=lambda r: r.risk_score,
                reverse=True  # Highest risk first
            )
        except Exception as e:
            self.logger.error(f"Error fetching farm risks: {e}")
            return []
    
    def get_critical_risks(
        self,
        farm_id: UUID
    ) -> List[Risk]:
        """
        Get critical-level risks for a farm
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of critical Risk entities
        """
        try:
            risks = self.get_farm_risks(farm_id)
            return [r for r in risks if r.is_critical()]
        except Exception as e:
            self.logger.error(f"Error fetching critical risks: {e}")
            return []
    
    async def get_risks_by_category(
        self,
        farm_id: UUID,
        category: RiskCategory
    ) -> List[Risk]:
        """
        Get risks in a specific category
        
        Args:
            farm_id: Farm identifier
            category: Risk category to filter
            
        Returns:
            List of matching Risk entities
        """
        try:
            response = await self.db.select_many(
                'farm_risks',
                {
                    "farm_id": str(farm_id),
                    "risk_category": category.value if hasattr(category, 'value') else str(category)
                }
            )
            return sorted(
                [self._map_to_entity(row) for row in response],
                key=lambda r: r.risk_score,
                reverse=True
            )
        except Exception as e:
            self.logger.error(f"Error fetching risks by category: {e}")
            return []
    
    def get_high_priority_risks(
        self,
        farm_id: UUID
    ) -> List[Risk]:
        """
        Get high-priority risks requiring immediate attention
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of high-priority Risk entities
        """
        try:
            risks = self.get_farm_risks(farm_id)
            return [r for r in risks if r.is_high_priority()]
        except Exception as e:
            self.logger.error(f"Error fetching high priority risks: {e}")
            return []
    
    async def get_risk_by_name(
        self,
        farm_id: UUID,
        risk_name: str
    ) -> Optional[Risk]:
        """
        Get risk by name
        
        Args:
            farm_id: Farm identifier
            risk_name: Name of risk to find
            
        Returns:
            Risk entity or None if not found
        """
        try:
            response = await self.db.select_many(
                'farm_risks',
                {
                    "farm_id": str(farm_id),
                    "risk_name": risk_name
                },
                limit=1
            )
            return self._map_to_entity(response[0]) if response else None
        except Exception as e:
            self.logger.error(f"Error fetching risk by name: {e}")
            return None
            return None
    
    def update_risk_assessment(
        self,
        risk_id: UUID,
        current_pressure: float,
        risk_score: float,
        severity_level: RiskSeverity
    ) -> Optional[Risk]:
        """
        Update risk assessment with latest monitoring data
        
        Args:
            risk_id: Risk identifier
            current_pressure: Current pressure level (0-1)
            risk_score: Updated risk score
            severity_level: Updated severity level
            
        Returns:
            Updated Risk entity
        """
        try:
            data = {
                "current_pressure": current_pressure,
                "risk_score": risk_score,
            }
            return self.update(risk_id, data)
        except Exception as e:
            self.logger.error(f"Error updating risk assessment: {e}")
            return None
    
    def get_risk_summary(
        self,
        farm_id: UUID
    ) -> Dict[str, Any]:
        """
        Get summary of all risks for a farm
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with risk summary statistics
        """
        try:
            risks = self.get_farm_risks(farm_id)
            
            if not risks:
                return {
                    "total_risks": 0,
                    "critical_risks": 0,
                    "high_risks": 0,
                    "medium_risks": 0,
                    "low_risks": 0,
                    "average_risk_score": 0,
                    "highest_risk": None,
                }
            
            severity_counts = {
                RiskSeverity.CRITICAL: 0,
                RiskSeverity.HIGH: 0,
                RiskSeverity.MEDIUM: 0,
                RiskSeverity.LOW: 0,
            }
            
            for risk in risks:
                severity = risk.get_severity_level()
                severity_counts[severity] += 1
            
            import statistics
            avg_score = statistics.mean([r.risk_score for r in risks])
            
            return {
                "total_risks": len(risks),
                "critical_risks": severity_counts[RiskSeverity.CRITICAL],
                "high_risks": severity_counts[RiskSeverity.HIGH],
                "medium_risks": severity_counts[RiskSeverity.MEDIUM],
                "low_risks": severity_counts[RiskSeverity.LOW],
                "average_risk_score": avg_score,
                "highest_risk": {
                    "name": risks[0].risk_name,
                    "score": risks[0].risk_score,
                    "category": risks[0].risk_category.value,
                } if risks else None,
            }
        except Exception as e:
            self.logger.error(f"Error getting risk summary: {e}")
            return {}
    
    def get_risks_needing_monitoring(
        self,
        farm_id: UUID,
        days_since_last_monitoring: int = 30
    ) -> List[Risk]:
        """
        Get risks that need monitoring update
        
        Args:
            farm_id: Farm identifier
            days_since_last_monitoring: Threshold for monitoring update
            
        Returns:
            List of Risk entities needing monitoring
        """
        try:
            risks = self.get_farm_risks(farm_id)
            now = datetime.now()
            
            needs_monitoring = []
            for risk in risks:
                next_monitoring = risk.get_next_monitoring_date(risk.updated_at)
                if next_monitoring <= now:
                    needs_monitoring.append(risk)
            
            return needs_monitoring
        except Exception as e:
            self.logger.error(f"Error getting risks needing monitoring: {e}")
            return []
    
    def get_risks_affecting_crop(
        self,
        farm_id: UUID,
        crop: str
    ) -> List[Risk]:
        """
        Get all risks affecting a specific crop
        
        Args:
            farm_id: Farm identifier
            crop: Crop name to filter
            
        Returns:
            List of Risk entities affecting the crop
        """
        try:
            risks = self.get_farm_risks(farm_id)
            return [r for r in risks if crop.lower() in [c.lower() for c in r.affected_crops]]
        except Exception as e:
            self.logger.error(f"Error getting crop-specific risks: {e}")
            return []
    
    def calculate_overall_farm_risk(
        self,
        farm_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate overall farm risk level
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with overall risk assessment
        """
        try:
            risks = self.get_farm_risks(farm_id)
            
            if not risks:
                return {
                    "overall_risk_score": 0,
                    "overall_risk_level": "LOW",
                    "recommendation": "No identified risks",
                }
            
            import statistics
            
            # Weighted average (critical risks count more)
            weighted_scores = []
            for risk in risks:
                if risk.is_critical():
                    weighted_scores.append(risk.risk_score * 1.5)
                elif risk.get_severity_level() == RiskSeverity.HIGH:
                    weighted_scores.append(risk.risk_score * 1.2)
                else:
                    weighted_scores.append(risk.risk_score)
            
            overall_score = statistics.mean(weighted_scores) if weighted_scores else 0
            
            # Map to risk level
            if overall_score >= 0.75:
                level = "CRITICAL"
                recommendation = "Urgent action required. Multiple critical risks identified."
            elif overall_score >= 0.5:
                level = "HIGH"
                recommendation = "Farm is at significant risk. Implement mitigation strategies."
            elif overall_score >= 0.25:
                level = "MEDIUM"
                recommendation = "Moderate risk level. Monitor and prepare contingencies."
            else:
                level = "LOW"
                recommendation = "Farm risks are manageable. Continue monitoring."
            
            return {
                "overall_risk_score": overall_score,
                "overall_risk_level": level,
                "recommendation": recommendation,
            }
        except Exception as e:
            self.logger.error(f"Error calculating overall farm risk: {e}")
            return {}
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Risk:
        """Map database row to Risk entity"""
        if isinstance(data, Risk):
            return data
        
        return Risk(
            id=data.get("id"),
            farm_id=data.get("farm_id"),
            user_id=data.get("user_id"),
            risk_category=RiskCategory(data.get("risk_category", "pest")),
            risk_name=data.get("risk_name"),
            risk_probability=data.get("risk_probability", 0),
            risk_severity_if_occurs=data.get("risk_severity_if_occurs", 0),
            risk_score=data.get("risk_score", 0),
            current_pressure=data.get("current_pressure", 0),
            vulnerability_index=data.get("vulnerability_index", 0),
            affected_crops=data.get("affected_crops", []),
            affected_area_acres=data.get("affected_area_acres"),
            mitigation_strategies=data.get("mitigation_strategies", []),
            early_warning_indicators=data.get("early_warning_indicators", []),
            recommended_actions=data.get("recommended_actions", []),
            monitoring_frequency_days=data.get("monitoring_frequency_days"),
            estimated_loss_if_occurs=data.get("estimated_loss_if_occurs"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
