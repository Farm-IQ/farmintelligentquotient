"""
ML Model Registry and Management System
========================================

Centralized registry for managing Phase 2 trained ML models.
Handles model loading, caching, versioning, and fallback strategies.
"""

import os
import pickle
import logging
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATACLASSES
# ============================================================================

class ModelType(Enum):
    """Supported ML model types"""
    YIELD_PREDICTOR = "yield_predictor"
    EXPENSE_FORECASTER = "expense_forecaster"
    DISEASE_CLASSIFIER = "disease_classifier"
    MARKET_PREDICTOR = "market_predictor"
    ROI_OPTIMIZER = "roi_optimizer"


class ModelStatus(Enum):
    """Model availability status"""
    LOADED = "loaded"
    CACHED = "cached"
    NOT_FOUND = "not_found"
    ERROR = "error"
    FALLBACK_MOCK = "fallback_mock"


@dataclass
class ModelMetadata:
    """Metadata for a registered model"""
    model_type: ModelType
    version: str
    phase: str  # e.g., "phase2", "phase3"
    file_path: str
    status: ModelStatus = ModelStatus.NOT_FOUND
    loaded_at: Optional[datetime] = None
    description: str = ""
    input_features: Dict[str, Any] = field(default_factory=dict)
    output_features: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class PredictionMetadata:
    """Metadata for a prediction made by a model"""
    model_type: ModelType
    model_version: str
    timestamp: datetime
    farm_id: str
    features_used: int
    is_mock_prediction: bool = False
    execution_time_ms: float = 0.0
    confidence_level: float = 0.0


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class MLModelRegistry:
    """
    Central registry for Phase 2 ML models.
    Tracks model metadata, versions, and availability.
    """
    
    # Model locations
    MODEL_DIR = Path(__file__).parent / "models"
    
    # Model definitions
    MODEL_DEFINITIONS = {
        ModelType.YIELD_PREDICTOR: {
            "file": "yield_predictor_v1.pkl",
            "description": "XGBoost yield prediction model",
            "input_features": 50,
            "primary_output": "yield_kg_per_acre",
            "secondary_outputs": ["confidence_interval", "trend"]
        },
        ModelType.EXPENSE_FORECASTER: {
            "file": "expense_forecaster_v1.pkl",
            "description": "Prophet/ARIMA expense forecasting model",
            "input_features": 20,
            "primary_output": "monthly_expenses",
            "secondary_outputs": ["variance", "category_breakdown"]
        },
        ModelType.DISEASE_CLASSIFIER: {
            "file": "disease_classifier_v1.pkl",
            "description": "GradientBoosting disease risk classifier",
            "input_features": 30,
            "primary_output": "risk_score",
            "secondary_outputs": ["severity", "treatment_recommendations"]
        },
        ModelType.MARKET_PREDICTOR: {
            "file": "market_predictor_v1.pkl",
            "description": "ARIMA market price predictor",
            "input_features": 15,
            "primary_output": "price_forecast",
            "secondary_outputs": ["volatility", "trend"]
        },
        ModelType.ROI_OPTIMIZER: {
            "file": "roi_optimizer_v1.pkl",
            "description": "MILP ROI optimization model",
            "input_features": 100,
            "primary_output": "optimal_allocation",
            "secondary_outputs": ["roi_improvement", "sensitivity"]
        }
    }
    
    def __init__(self):
        self.registry: Dict[ModelType, ModelMetadata] = {}
        self.initialize_registry()
    
    def initialize_registry(self):
        """Initialize registry with all known models"""
        for model_type, definition in self.MODEL_DEFINITIONS.items():
            file_path = self.MODEL_DIR / definition["file"]
            
            # Check if model exists
            status = ModelStatus.NOT_FOUND
            error_msg = None
            
            if file_path.exists():
                status = ModelStatus.NOT_FOUND  # Will be LOADED after first use
            else:
                error_msg = f"Model file not found: {file_path}"
                logger.warning(error_msg)
            
            metadata = ModelMetadata(
                model_type=model_type,
                version="v1.0",
                phase="phase2",
                file_path=str(file_path),
                status=status,
                description=definition["description"],
                input_features={"count": definition["input_features"]},
                output_features={
                    "primary": definition["primary_output"],
                    "secondary": definition["secondary_outputs"]
                },
                error_message=error_msg
            )
            
            self.registry[model_type] = metadata
    
    def get_model_info(self, model_type: ModelType) -> ModelMetadata:
        """Get metadata for a specific model"""
        if model_type not in self.registry:
            raise ValueError(f"Unknown model type: {model_type}")
        return self.registry[model_type]
    
    def mark_loaded(self, model_type: ModelType, execution_time: float = 0.0):
        """Mark model as successfully loaded"""
        if model_type in self.registry:
            self.registry[model_type].status = ModelStatus.LOADED
            self.registry[model_type].loaded_at = datetime.now()
            logger.info(f"✅ {model_type.value} loaded successfully ({execution_time:.1f}ms)")
    
    def mark_error(self, model_type: ModelType, error_msg: str):
        """Mark model as having an error"""
        if model_type in self.registry:
            self.registry[model_type].status = ModelStatus.ERROR
            self.registry[model_type].error_message = error_msg
            logger.error(f"❌ {model_type.value} error: {error_msg}")
    
    def mark_fallback(self, model_type: ModelType):
        """Mark model as using fallback mock implementation"""
        if model_type in self.registry:
            self.registry[model_type].status = ModelStatus.FALLBACK_MOCK
            logger.warning(f"⚠️ {model_type.value} using fallback mock implementation")
    
    def get_all_status(self) -> Dict[str, str]:
        """Get status of all models"""
        status = {}
        for model_type, metadata in self.registry.items():
            status[model_type.value] = metadata.status.value
        return status


# ============================================================================
# MODEL MANAGER
# ============================================================================

class MLModelManager:
    """
    Manages loading, caching, and access to Phase 2 ML models.
    Provides unified interface for all model operations.
    """
    
    def __init__(self, registry: MLModelRegistry):
        self.registry = registry
        self.cache: Dict[ModelType, Any] = {}  # In-memory model cache
        self.logger = logging.getLogger(__name__)
    
    def load_model(self, model_type: ModelType, use_cache: bool = True) -> Optional[Any]:
        """
        Load a model from disk or cache.
        
        Args:
            model_type: Type of model to load
            use_cache: Use cached model if available
            
        Returns:
            Loaded model or None if not found/error
        """
        # Check cache first
        if use_cache and model_type in self.cache:
            self.logger.debug(f"Loading {model_type.value} from cache")
            return self.cache[model_type]
        
        # Get model metadata
        try:
            metadata = self.registry.get_model_info(model_type)
        except ValueError as e:
            self.logger.error(f"Invalid model type: {e}")
            return None
        
        # Load from disk
        file_path = Path(metadata.file_path)
        
        if not file_path.exists():
            self.registry.mark_error(model_type, f"File not found: {file_path}")
            return None
        
        try:
            import time
            start_time = time.time()
            
            with open(file_path, 'rb') as f:
                model = pickle.load(f)
            
            load_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Update registry
            self.registry.mark_loaded(model_type, load_time)
            
            # Cache model
            self.cache[model_type] = model
            
            return model
        
        except Exception as e:
            error_msg = f"Failed to load model: {str(e)}"
            self.registry.mark_error(model_type, error_msg)
            self.logger.error(error_msg)
            return None
    
    def get_model(self, model_type: ModelType) -> Optional[Any]:
        """
        Get a model, loading if necessary.
        Automatically uses cache.
        """
        return self.load_model(model_type, use_cache=True)
    
    def unload_model(self, model_type: ModelType):
        """Remove model from cache"""
        if model_type in self.cache:
            del self.cache[model_type]
            self.logger.info(f"Model {model_type.value} unloaded from cache")
    
    def clear_cache(self):
        """Clear all cached models"""
        self.cache.clear()
        self.logger.info("All models cleared from cache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached models"""
        return {
            "cached_models": list(self.cache.keys()),
            "count": len(self.cache),
            "memory_usage_mb": sum(
                self._estimate_size(m) for m in self.cache.values()
            ) / (1024 * 1024)
        }
    
    @staticmethod
    def _estimate_size(obj) -> float:
        """Rough estimate of object size in bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            return 0
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get full registry status"""
        status = self.registry.get_all_status()
        cache_info = self.get_cache_info()
        
        return {
            "models": status,
            "cache": cache_info,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

_global_registry: Optional[MLModelRegistry] = None
_global_manager: Optional[MLModelManager] = None


def get_model_registry() -> MLModelRegistry:
    """Get or create global model registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = MLModelRegistry()
    return _global_registry


def get_model_manager() -> MLModelManager:
    """Get or create global model manager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = MLModelManager(get_model_registry())
    return _global_manager


def initialize_ml_system():
    """Initialize ML model system"""
    registry = get_model_registry()
    manager = get_model_manager()
    
    status = manager.get_registry_status()
    logger.info(f"ML System initialized")
    logger.info(f"Model Status: {status}")
    
    return registry, manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ModelType',
    'ModelStatus',
    'ModelMetadata',
    'PredictionMetadata',
    'MLModelRegistry',
    'MLModelManager',
    'get_model_registry',
    'get_model_manager',
    'initialize_ml_system',
]
