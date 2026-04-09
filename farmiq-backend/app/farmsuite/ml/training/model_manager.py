"""
FarmSuite Model Manager
======================

Manages model lifecycle: training, deployment, versioning, A/B testing.

Responsibilities:
- Load/save trained models to disk
- Train models on farm data
- Version control (v1.0, v1.1, v2.0 for different train dates)
- A/B testing (compare versions)
- Performance monitoring
- Automatic retraining triggers
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime
import logging
import os
from pathlib import Path
import json
import pandas as pd

from app.farmsuite.ml.predictors.base_models import (
    BasePredictorModel,
    ModelRegistry,
    ModelType,
    ModelMetadata,
    PredictionResult
)

logger = logging.getLogger(__name__)


# ============================================================================
# MODEL MANAGER
# ============================================================================

class ModelManager:
    """
    Manages lifecycle of FarmSuite ML models.
    
    Usage:
    ```python
    manager = ModelManager(models_dir="./models")
    await manager.initialize()
    
    # Load model
    model = await manager.load_model(ModelType.YIELD_PREDICTOR)
    
    # Train new model
    metrics = await manager.train_model(
        ModelType.YIELD_PREDICTOR,
        training_data,
        save=True
    )
    
    # Make prediction
    result = await model.predict(features)
    
    # Compare versions
    comparison = await manager.compare_model_versions(
        ModelType.YIELD_PREDICTOR,
        version_a="v1.0",
        version_b="v1.1"
    )
    ```
    """
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.loaded_models: Dict[ModelType, BasePredictorModel] = {}
        self.model_metadata: Dict[ModelType, List[ModelMetadata]] = {}
        
        logger.info(f"🤖 ModelManager initialized at {self.models_dir}")
    
    async def initialize(self) -> bool:
        """Initialize: load available models and metadata"""
        try:
            # Ensure all model directories exist
            for model_type in ModelType:
                model_dir = self.models_dir / model_type.value
                model_dir.mkdir(parents=True, exist_ok=True)
            
            # Load metadata for all models
            await self._load_all_metadata()
            
            logger.info("✅ ModelManager initialized")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize ModelManager: {e}")
            return False
    
    async def load_model(
        self,
        model_type: ModelType,
        version: str = "latest"
    ) -> Optional[BasePredictorModel]:
        """
        Load a trained model from disk.
        
        Args:
            model_type: Type of model to load
            version: Version to load ("latest", "v1.0", "v2.1", etc)
            
        Returns: Loaded model or None if not found
        """
        
        try:
            # Check if already loaded
            if model_type in self.loaded_models and version == "latest":
                logger.info(f"✅ Model {model_type.value} already loaded")
                return self.loaded_models[model_type]
            
            # Find model file
            model_dir = self.models_dir / model_type.value
            
            if version == "latest":
                # Get latest version
                latest_file = None
                latest_date = None
                
                for file in model_dir.glob("*.pkl"):
                    mod_time = file.stat().st_mtime
                    if latest_date is None or mod_time > latest_date:
                        latest_date = mod_time
                        latest_file = file
                
                if not latest_file:
                    logger.warning(f"⚠️ No model found for {model_type.value}")
                    return None
            else:
                latest_file = model_dir / f"{version}.pkl"
                if not latest_file.exists():
                    logger.warning(f"⚠️ Model version {version} not found")
                    return None
            
            # Create model instance
            model = ModelRegistry.create_model(model_type)
            
            # Load from disk
            success = await model.load(str(latest_file))
            
            if success:
                self.loaded_models[model_type] = model
                logger.info(f"✅ Loaded model: {model_type.value} from {latest_file}")
                return model
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error loading model {model_type.value}: {e}")
            return None
    
    async def train_model(
        self,
        model_type: ModelType,
        training_data: pd.DataFrame,
        target_column: str,
        save: bool = True,
        version: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Train a model on farm data.
        
        Args:
            model_type: Type of model to train
            training_data: Training DataFrame
            target_column: Column name for target variable
            save: Save model after training
            version: Custom version string (auto-generated if None)
            
        Returns: Performance metrics dict
        """
        
        try:
            logger.info(f"📚 Training {model_type.value} on {len(training_data)} samples")
            
            # Create model
            model = ModelRegistry.create_model(model_type)
            
            # Train
            metrics = await model.train(
                training_data,
                target_column,
                validation_split=0.2,
                test_split=0.1
            )
            
            # Save if requested
            if save:
                if version is None:
                    version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                model_dir = self.models_dir / model_type.value
                model_path = model_dir / f"{version}.pkl"
                
                await model.save(str(model_path))
                
                # Update metadata
                await self._save_model_metadata(
                    model_type,
                    version,
                    metrics,
                    len(training_data)
                )
            
            # Cache the model
            self.loaded_models[model_type] = model
            
            logger.info(f"✅ Training complete: {model_type.value}")
            return metrics
        
        except Exception as e:
            logger.error(f"❌ Error training model {model_type.value}: {e}")
            return None
    
    async def predict(
        self,
        model_type: ModelType,
        features: Dict[str, float],
        farm_id: str,
        auto_load: bool = True
    ) -> Optional[PredictionResult]:
        """
        Make prediction using a model.
        
        Args:
            model_type: Type of model to use
            features: Engineered features dict
            farm_id: Farm being predicted
            auto_load: Load model if not cached
            
        Returns: PredictionResult
        """
        
        try:
            # Load model if needed
            model = self.loaded_models.get(model_type)
            
            if model is None:
                if auto_load:
                    model = await self.load_model(model_type, version="latest")
                else:
                    logger.warning(f"⚠️ Model {model_type.value} not loaded")
                    return None
            
            # Make prediction
            result = await model.predict(features, return_explanation=True)
            
            # Update farm_id
            result.farm_id = farm_id
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error making prediction: {e}")
            return None
    
    async def get_model_performance(
        self,
        model_type: ModelType,
        version: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get performance metrics for a model version.
        
        Args:
            model_type: Type of model
            version: Specific version or "latest"
            
        Returns: Performance metrics dict
        """
        
        try:
            metadata_file = self.models_dir / model_type.value / "metadata.json"
            
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                metadata_list = json.load(f)
            
            if version == "latest" or version is None:
                # Return best performing version
                return max(metadata_list, key=lambda x: x.get("val_r2_score", 0))
            else:
                # Find specific version
                for meta in metadata_list:
                    if meta["version"] == version:
                        return meta
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error retrieving performance: {e}")
            return None
    
    async def compare_model_versions(
        self,
        model_type: ModelType,
        version_a: str = "latest",
        version_b: str = "second_latest"
    ) -> Optional[Dict]:
        """
        Compare performance of two model versions (A/B testing).
        
        Args:
            model_type: Type of model
            version_a: First version
            version_b: Second version
            
        Returns: Comparison dict with winner
        """
        
        try:
            perf_a = await self.get_model_performance(model_type, version_a)
            perf_b = await self.get_model_performance(model_type, version_b)
            
            if not perf_a or not perf_b:
                return None
            
            # Compare metrics
            improvement = {
                "r2_improvement": perf_a.get("val_r2_score", 0) - perf_b.get("val_r2_score", 0),
                "rmse_improvement": perf_b.get("rmse", float('inf')) - perf_a.get("rmse", float('inf')),
            }
            
            winner = version_a if improvement["r2_improvement"] > 0 else version_b
            
            return {
                "version_a": version_a,
                "version_b": version_b,
                "performance_a": perf_a,
                "performance_b": perf_b,
                "winner": winner,
                "improvement": improvement,
                "recommendation": f"Use {winner} (better performance)"
            }
        
        except Exception as e:
            logger.error(f"❌ Error comparing versions: {e}")
            return None
    
    async def _load_all_metadata(self):
        """Load metadata for all models"""
        for model_type in ModelType:
            metadata_file = self.models_dir / model_type.value / "metadata.json"
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        self.model_metadata[model_type] = json.load(f)
                except:
                    self.model_metadata[model_type] = []
            else:
                self.model_metadata[model_type] = []
    
    async def _save_model_metadata(
        self,
        model_type: ModelType,
        version: str,
        metrics: Dict,
        training_sample_size: int
    ):
        """Save metadata for a trained model"""
        
        metadata_file = self.models_dir / model_type.value / "metadata.json"
        
        new_metadata = {
            "model_id": f"{model_type.value}_{version}",
            "model_type": model_type.value,
            "version": version,
            "creation_date": datetime.now().isoformat(),
            "training_sample_size": training_sample_size,
            **metrics
        }
        
        # Load existing metadata
        existing = []
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                existing = json.load(f)
        
        # Append new
        existing.append(new_metadata)
        
        # Save updated
        with open(metadata_file, 'w') as f:
            json.dump(existing, f, indent=2)
        
        logger.info(f"✅ Saved metadata for {model_type.value} {version}")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

_model_manager: Optional[ModelManager] = None

async def get_model_manager(models_dir: str = "./models") -> ModelManager:
    """Get or create ModelManager singleton"""
    global _model_manager
    
    if _model_manager is None:
        _model_manager = ModelManager(models_dir)
        await _model_manager.initialize()
    
    return _model_manager
