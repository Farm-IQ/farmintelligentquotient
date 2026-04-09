"""
Prediction Repository
Data access layer for Prediction entities
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging
from app.shared import BaseRepository
from app.farmsuite.domain.entities.prediction import Prediction, PredictionType
from core.database import DatabaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    """
    Repository for Prediction entities
    Handles all Prediction CRUD operations and query logic
    """
    
    def __init__(self, db: DatabaseRepository):
        """
        Initialize PredictionRepository
        
        Args:
            db: DatabaseRepository instance
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def create(self, entity: Prediction) -> Prediction:
        """Create a new prediction"""
        prediction_data = {
            'id': str(entity.id),
            'farm_id': str(entity.farm_id),
            'user_id': str(entity.user_id),
            'prediction_type': entity.prediction_type,
            'predicted_value': entity.predicted_value,
            'confidence_score': entity.confidence_score,
            'prediction_date': entity.prediction_date,
            'target_date': entity.target_date,
            'metadata': entity.metadata or {},
        }
        await self.db.insert_one('farm_predictions', prediction_data)
        self.logger.info(f"Created prediction {entity.id}")
        return entity
    
    async def get_by_id(self, entity_id: UUID | str) -> Optional[Prediction]:
        """Get prediction by ID"""
        result = await self.db.select_one('farm_predictions', {'id': str(entity_id)})
        if not result:
            return None
        return self._map_to_entity(result)
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[Prediction]:
        """Get list of predictions"""
        results = await self.db.select_many(
            'farm_predictions',
            {},
            offset=skip,
            limit=limit
        )
        return [self._map_to_entity(row) for row in results]
    
    async def update(self, entity: Prediction) -> Prediction:
        """Update an existing prediction"""
        await self.db.update_one(
            'farm_predictions',
            {'id': str(entity.id)},
            {
                'predicted_value': entity.predicted_value,
                'confidence_score': entity.confidence_score,
                'target_date': entity.target_date,
                'metadata': entity.metadata
            }
        )
        self.logger.info(f"Updated prediction {entity.id}")
        return entity
    
    async def delete(self, entity_id: UUID | str) -> bool:
        """Delete a prediction"""
        await self.db.delete_one(
            'farm_predictions',
            {'id': str(entity_id)}
        )
        self.logger.info(f"Deleted prediction {entity_id}")
        return True
    
    async def count(self) -> int:
        """Count total predictions"""
        result = await self.db.count('farm_predictions')
        return result if result else 0
    
    async def get_farm_predictions(
        self,
        farm_id: UUID,
        limit: int = 100
    ) -> List[Prediction]:
        """
        Get all predictions for a farm
        
        Args:
            farm_id: Farm identifier
            limit: Maximum predictions to return
            
        Returns:
            List of Prediction entities
        """
        try:
            response = await self.db.select_many(
                'farm_predictions',
                {"farm_id": str(farm_id)},
                limit=limit
            )
            return [self._map_to_entity(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching farm predictions: {e}")
            return []
    
    async def get_active_predictions(
        self,
        farm_id: UUID
    ) -> List[Prediction]:
        """
        Get active (non-expired) predictions for a farm
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of active Prediction entities
        """
        try:
            now = datetime.now()
            predictions = await self.get_farm_predictions(farm_id)
            
            return [
                p for p in predictions
                if p.target_date > now
            ]
        except Exception as e:
            self.logger.error(f"Error fetching active predictions: {e}")
            return []
    
    async def get_predictions_by_type(
        self,
        farm_id: UUID,
        prediction_type: PredictionType
    ) -> List[Prediction]:
        """
        Get predictions of a specific type
        
        Args:
            farm_id: Farm identifier
            prediction_type: Type of prediction to filter
            
        Returns:
            List of matching Prediction entities
        """
        try:
            response = await self.db.select_many(
                'farm_predictions',
                {
                    "farm_id": str(farm_id),
                    "prediction_type": prediction_type.value if hasattr(prediction_type, 'value') else str(prediction_type)
                }
            )
            return [self._map_to_entity(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching predictions by type: {e}")
            return []
    
    async def get_subject_prediction(
        self,
        farm_id: UUID,
        prediction_type: PredictionType,
        subject: str
    ) -> Optional[Prediction]:
        """
        Get latest prediction for a specific subject
        
        Args:
            farm_id: Farm identifier
            prediction_type: Type of prediction
            subject: What's being predicted (crop, fertilizer, etc)
            
        Returns:
            Most recent matching Prediction or None
        """
        try:
            response = await self.db.select_many(
                'farm_predictions',
                {
                    "farm_id": str(farm_id),
                    "prediction_type": prediction_type.value if hasattr(prediction_type, 'value') else str(prediction_type),
                    "subject": subject
                },
                limit=1
            )
            return self._map_to_entity(response[0]) if response else None
        except Exception as e:
            self.logger.error(f"Error fetching subject prediction: {e}")
            return None
    
    def get_prediction_accuracy(
        self,
        farm_id: UUID,
        prediction_type: PredictionType
    ) -> Dict[str, Any]:
        """
        Calculate accuracy metrics for past predictions
        
        Args:
            farm_id: Farm identifier
            prediction_type: Type of prediction to evaluate
            
        Returns:
            Dictionary with accuracy statistics
        """
        try:
            predictions = self.get_predictions_by_type(farm_id, prediction_type)
            
            # Filter to predictions with actual values
            completed_predictions = [
                p for p in predictions
                if p.actual_value is not None
            ]
            
            if not completed_predictions:
                return {}
            
            errors = [
                abs(p.predicted_value - p.actual_value) / max(p.actual_value, 1)
                for p in completed_predictions
            ]
            
            import statistics
            
            return {
                "total_predictions": len(predictions),
                "completed_predictions": len(completed_predictions),
                "avg_error_percent": statistics.mean(errors) * 100,
                "median_error_percent": statistics.median(errors) * 100,
                "accuracy_rate": (
                    len([e for e in errors if e < 0.2]) / len(errors) * 100
                    if errors else 0
                ),  # % within 20%
            }
        except Exception as e:
            self.logger.error(f"Error calculating prediction accuracy: {e}")
            return {}
    
    def update_prediction_actual_value(
        self,
        prediction_id: UUID,
        actual_value: float
    ) -> Optional[Prediction]:
        """
        Update prediction with actual observed value
        
        Args:
            prediction_id: Prediction identifier
            actual_value: Actual value that occurred
            
        Returns:
            Updated Prediction entity
        """
        try:
            data = {"actual_value": actual_value}
            return self.update(prediction_id, data)
        except Exception as e:
            self.logger.error(f"Error updating prediction actual value: {e}")
            return None
    
    def get_high_confidence_predictions(
        self,
        farm_id: UUID,
        min_confidence: float = 0.8
    ) -> List[Prediction]:
        """
        Get high-confidence predictions
        
        Args:
            farm_id: Farm identifier
            min_confidence: Minimum confidence threshold (0-1)
            
        Returns:
            List of high-confidence Prediction entities
        """
        try:
            predictions = self.get_active_predictions(farm_id)
            return [
                p for p in predictions
                if p.confidence >= min_confidence
            ]
        except Exception as e:
            self.logger.error(f"Error fetching high confidence predictions: {e}")
            return []
    
    def get_critical_predictions(
        self,
        farm_id: UUID
    ) -> List[Prediction]:
        """
        Get predictions for critical subjects that need action
        (disease, pest, market crash, etc)
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of critical Prediction entities
        """
        try:
            predictions = self.get_active_predictions(farm_id)
            
            critical_types = [
                PredictionType.DISEASE_RISK,
                PredictionType.MARKET_PRICE
            ]
            
            return [
                p for p in predictions
                if p.prediction_type in critical_types and p.confidence > 0.5
            ]
        except Exception as e:
            self.logger.error(f"Error fetching critical predictions: {e}")
            return []
    
    def delete_expired_predictions(
        self,
        farm_id: UUID
    ) -> int:
        """
        Delete expired predictions for a farm
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Number of predictions deleted
        """
        try:
            predictions = self.get_farm_predictions(farm_id)
            now = datetime.now()
            
            deleted_count = 0
            for p in predictions:
                if p.prediction_period_end < now:
                    self.delete(p.id)
                    deleted_count += 1
            
            self.logger.info(f"Deleted {deleted_count} expired predictions")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error deleting expired predictions: {e}")
            return 0
    
    def get_prediction_timeline(
        self,
        farm_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get timeline of predictions (sorted by prediction date)
        
        Args:
            farm_id: Farm identifier
            limit: Maximum predictions to return
            
        Returns:
            List of prediction summaries
        """
        try:
            predictions = self.get_farm_predictions(farm_id, limit)
            
            timeline = [
                {
                    "id": str(p.id),
                    "type": p.prediction_type.value,
                    "subject": p.subject,
                    "predicted_value": p.predicted_value,
                    "confidence": p.confidence,
                    "period_start": p.prediction_period_start.isoformat(),
                    "period_end": p.prediction_period_end.isoformat(),
                    "created_at": p.created_at.isoformat(),
                }
                for p in sorted(predictions, key=lambda x: x.created_at)
            ]
            
            return timeline
        except Exception as e:
            self.logger.error(f"Error getting prediction timeline: {e}")
            return []
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Prediction:
        """Map database row to Prediction entity"""
        if isinstance(data, Prediction):
            return data
        
        return Prediction(
            id=data.get("id"),
            farm_id=data.get("farm_id"),
            user_id=data.get("user_id"),
            prediction_type=PredictionType(data.get("prediction_type", "yield")),
            subject=data.get("subject"),
            predicted_value=data.get("predicted_value", 0),
            predicted_unit=data.get("predicted_unit", ""),
            confidence=data.get("confidence", 0.5),
            prediction_period_start=data.get("prediction_period_start"),
            prediction_period_end=data.get("prediction_period_end"),
            model_version=data.get("model_version", "1.0"),
            factors=data.get("factors", []),
            recommendations=data.get("recommendations", []),
            actual_value=data.get("actual_value"),
            error_margin=data.get("error_margin"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
