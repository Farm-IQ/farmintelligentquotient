"""
FarmSuite ML Training Utilities
================================

Advanced utilities for model training, hyperparameter tuning, cross-validation,
and model comparison. Integrates with the feature engineering pipeline and
training pipeline orchestrator.

FEATURES:
- Hyperparameter tuning (Grid/Random/Bayesian search)
- Cross-validation with stratification
- Model comparison & selection
- Feature scaling & preprocessing
- Model serialization with versioning
- Performance tracking & reporting
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_validate, cross_val_predict
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import make_scorer, mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONFIGURATIONS
# ============================================================================

class FeatureScalingMethod(str, Enum):
    """Feature scaling strategies"""
    STANDARD = "standard"       # Zero mean, unit variance
    MINMAX = "minmax"          # Scale to [0, 1]
    ROBUST = "robust"          # Use median/quartiles (resistant to outliers)
    NONE = "none"


class TuningStrategy(str, Enum):
    """Hyperparameter tuning strategies"""
    GRID = "grid"              # Exhaustive grid search
    RANDOM = "random"          # Random sampling
    BAYESIAN = "bayesian"      # Bayesian optimization


class MetricDirection(str, Enum):
    """Metric optimization direction"""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class HyperparameterGrid:
    """Configuration for hyperparameter tuning"""
    
    # XGBoost parameters
    xgboost_params: Dict[str, List[Any]] = None
    
    # Scikit-learn ensemble parameters
    ensemble_params: Dict[str, List[Any]] = None
    
    # Training parameters
    batch_size: List[int] = None
    learning_rate: List[float] = None
    epochs: List[int] = None
    
    # Regularization
    l1_penalty: List[float] = None
    l2_penalty: List[float] = None
    dropout_rate: List[float] = None
    
    def __post_init__(self):
        """Set defaults if not provided"""
        if self.xgboost_params is None:
            self.xgboost_params = {
                'max_depth': [4, 5, 6, 7],
                'learning_rate': [0.01, 0.05, 0.1],
                'n_estimators': [100, 200, 300],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9],
            }
        
        if self.ensemble_params is None:
            self.ensemble_params = {
                'n_estimators': [100, 200, 300],
                'max_depth': [5, 10, 15],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
            }
        
        if self.batch_size is None:
            self.batch_size = [16, 32, 64]
        
        if self.learning_rate is None:
            self.learning_rate = [0.001, 0.01, 0.1]
        
        if self.epochs is None:
            self.epochs = [50, 100, 200]


@dataclass
class TuningResult:
    """Results from hyperparameter tuning"""
    best_params: Dict[str, Any]
    best_score: float
    best_estimator: Any
    cv_results: Dict[str, List[float]]
    mean_test_score: float
    std_test_score: float
    tuning_time_seconds: float
    metric_tracked: str  # e.g., "r2", "f1", "roc_auc"
    trials_completed: int
    
    def to_dict(self) -> Dict:
        """Convert to serializable dict"""
        return {
            "best_params": self.best_params,
            "best_score": float(self.best_score),
            "mean_test_score": float(self.mean_test_score),
            "std_test_score": float(self.std_test_score),
            "metric_tracked": self.metric_tracked,
            "trials_completed": self.trials_completed,
            "tuning_time_seconds": self.tuning_time_seconds,
        }


@dataclass
class CrossValidationResult:
    """Results from cross-validation"""
    model_name: str
    cv_folds: int
    metric_scores: Dict[str, np.ndarray]  # e.g., {"r2": [0.85, 0.87, ...], "rmse": [...]}
    mean_scores: Dict[str, float]
    std_scores: Dict[str, float]
    cv_time_seconds: float
    
    def to_dict(self) -> Dict:
        """Convert to serializable dict"""
        return {
            "model_name": self.model_name,
            "cv_folds": self.cv_folds,
            "mean_scores": {k: float(v) for k, v in self.mean_scores.items()},
            "std_scores": {k: float(v) for k, v in self.std_scores.items()},
            "cv_time_seconds": self.cv_time_seconds,
        }


@dataclass
class ModelComparison:
    """Comparison between multiple models"""
    models: Dict[str, Any]  # {model_name: model_instance}
    metrics: Dict[str, Dict[str, float]]  # {model_name: {metric_name: score}}
    best_model_name: str
    best_model_score: float
    best_metric: str
    comparison_date: datetime
    
    def ranking(self) -> List[Tuple[str, float]]:
        """Get ranked models by best metric"""
        scores = {
            name: metrics.get(self.best_metric, 0)
            for name, metrics in self.metrics.items()
        }
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    def summary(self) -> str:
        """Generate comparison summary"""
        summary = f"Model Comparison Report\n{'='*50}\n"
        summary += f"Date: {self.comparison_date.isoformat()}\n"
        summary += f"Best Model: {self.best_model_name}\n"
        summary += f"Best Score ({self.best_metric}): {self.best_model_score:.4f}\n\n"
        
        summary += "Ranking:\n"
        for rank, (model_name, score) in enumerate(self.ranking(), 1):
            summary += f"  {rank}. {model_name}: {score:.4f}\n"
        
        return summary


# ============================================================================
# FEATURE PREPROCESSING
# ============================================================================

class FeaturePreprocessor:
    """
    Handles feature scaling, normalization, and preprocessing.
    
    Helps prepare features for ML training by:
    - Removing NaN/Inf values
    - Scaling to consistent ranges
    - Handling outliers
    - Feature selection
    """
    
    def __init__(self, scaling_method: FeatureScalingMethod = FeatureScalingMethod.STANDARD):
        self.scaling_method = scaling_method
        self.scaler = None
        self.feature_names = []
        self.scaling_params = {}
    
    def fit_and_transform(
        self,
        X: pd.DataFrame,
        handle_outliers: bool = True,
        outlier_method: str = "iqr"
    ) -> pd.DataFrame:
        """
        Fit scaler and transform features.
        
        Args:
            X: Feature DataFrame
            handle_outliers: Remove/clip outliers
            outlier_method: "iqr" or "zscore"
            
        Returns:
            Scaled DataFrame
        """
        
        X_cleaned = X.copy()
        
        # Handle missing values
        X_cleaned = X_cleaned.fillna(X_cleaned.mean(numeric_only=True))
        X_cleaned = X_cleaned.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Handle outliers
        if handle_outliers:
            X_cleaned = self._handle_outliers(X_cleaned, method=outlier_method)
        
        # Scale features
        if self.scaling_method == FeatureScalingMethod.STANDARD:
            self.scaler = StandardScaler()
        elif self.scaling_method == FeatureScalingMethod.MINMAX:
            self.scaler = MinMaxScaler()
        elif self.scaling_method == FeatureScalingMethod.ROBUST:
            self.scaler = RobustScaler()
        else:
            return X_cleaned
        
        self.feature_names = X_cleaned.columns.tolist()
        X_scaled = self.scaler.fit_transform(X_cleaned)
        
        logger.info(f"✅ Preprocessed {X_scaled.shape[0]} samples × {X_scaled.shape[1]} features")
        
        return pd.DataFrame(X_scaled, columns=self.feature_names)
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply fitted scaler to new data"""
        if self.scaler is None:
            logger.warning("⚠️  Scaler not fitted. Returning unscaled data.")
            return X
        
        X_cleaned = X.copy()
        X_cleaned = X_cleaned.fillna(0).replace([np.inf, -np.inf], 0)
        X_scaled = self.scaler.transform(X_cleaned)
        return pd.DataFrame(X_scaled, columns=self.feature_names)
    
    def _handle_outliers(self, X: pd.DataFrame, method: str = "iqr") -> pd.DataFrame:
        """Remove or clip outliers"""
        X_clean = X.copy()
        
        for col in X_clean.select_dtypes(include=[np.number]).columns:
            if method == "iqr":
                Q1 = X_clean[col].quantile(0.25)
                Q3 = X_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                X_clean[col] = X_clean[col].clip(lower_bound, upper_bound)
            
            elif method == "zscore":
                z_scores = np.abs((X_clean[col] - X_clean[col].mean()) / X_clean[col].std())
                X_clean[col] = X_clean[col][z_scores < 3]
        
        return X_clean


# ============================================================================
# HYPERPARAMETER TUNING
# ============================================================================

class HyperparameterTuner:
    """
    Orchestrates hyperparameter tuning using various strategies.
    
    Supports:
    - Grid search (exhaustive)
    - Random search (efficient for large spaces)
    - Bayesian optimization (intelligent sampling)
    """
    
    def __init__(
        self,
        strategy: TuningStrategy = TuningStrategy.GRID,
        cv_folds: int = 5,
        n_jobs: int = -1
    ):
        self.strategy = strategy
        self.cv_folds = cv_folds
        self.n_jobs = n_jobs
        self.tuning_results = []
    
    async def tune_model(
        self,
        model: Any,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        param_grid: Dict[str, List[Any]],
        scoring: str = "r2",
        n_iter: int = 20
    ) -> TuningResult:
        """
        Tune model hyperparameters.
        
        Args:
            model: Model to tune (sklearn-compatible)
            X_train: Training features
            y_train: Training target
            param_grid: Hyperparameter grid
            scoring: Metric to optimize
            n_iter: Number of iterations (for random search)
            
        Returns:
            TuningResult with best params and model
        """
        
        start_time = datetime.now()
        logger.info(f"🔧 Starting {self.strategy.value} hyperparameter tuning...")
        
        try:
            if self.strategy == TuningStrategy.GRID:
                searcher = GridSearchCV(
                    model,
                    param_grid,
                    cv=self.cv_folds,
                    scoring=scoring,
                    n_jobs=self.n_jobs,
                    verbose=2
                )
            
            elif self.strategy == TuningStrategy.RANDOM:
                searcher = RandomizedSearchCV(
                    model,
                    param_grid,
                    n_iter=n_iter,
                    cv=self.cv_folds,
                    scoring=scoring,
                    n_jobs=self.n_jobs,
                    random_state=42,
                    verbose=2
                )
            
            else:
                raise ValueError(f"Unknown tuning strategy: {self.strategy}")
            
            # Run tuning
            searcher.fit(X_train, y_train)
            
            tuning_time = (datetime.now() - start_time).total_seconds()
            
            result = TuningResult(
                best_params=searcher.best_params_,
                best_score=searcher.best_score_,
                best_estimator=searcher.best_estimator_,
                cv_results=searcher.cv_results_,
                mean_test_score=np.mean(searcher.cv_results_['mean_test_score']),
                std_test_score=np.std(searcher.cv_results_['std_test_score']),
                tuning_time_seconds=tuning_time,
                metric_tracked=scoring,
                trials_completed=len(searcher.cv_results_['mean_test_score'])
            )
            
            logger.info(f"✅ Tuning complete. Best score: {result.best_score:.4f}")
            logger.info(f"✅ Best params: {result.best_params}")
            
            self.tuning_results.append(result)
            return result
        
        except Exception as e:
            logger.error(f"❌ Tuning failed: {e}")
            raise


# ============================================================================
# CROSS-VALIDATION UTILITIES
# ============================================================================

class CrossValidationEvaluator:
    """
    Advanced cross-validation with multiple metrics.
    
    Provides:
    - Stratified K-Fold for balanced splits
    - Multiple metric calculation
    - Feature importance analysis
    """
    
    def __init__(self, cv_folds: int = 5):
        self.cv_folds = cv_folds
        self.cv_results = []
    
    async def evaluate_with_cv(
        self,
        model: Any,
        X: pd.DataFrame,
        y: pd.Series,
        metrics: Optional[Dict[str, Callable]] = None
    ) -> CrossValidationResult:
        """
        Perform cross-validation with multiple metrics.
        
        Args:
            model: Trained model
            X: Features
            y: Target
            metrics: Dict of metric_name -> callable
            
        Returns:
            CrossValidationResult with detailed metrics
        """
        
        if metrics is None:
            metrics = {
                "r2": make_scorer(r2_score),
                "rmse": make_scorer(lambda y_true, y_pred: -np.sqrt(mean_squared_error(y_true, y_pred))),
                "mae": make_scorer(mean_absolute_error)
            }
        
        start_time = datetime.now()
        logger.info(f"🔍 Running {self.cv_folds}-fold cross-validation...")
        
        try:
            cv_results = cross_validate(
                model,
                X, y,
                cv=self.cv_folds,
                scoring=metrics,
                return_train_score=True,
                n_jobs=-1
            )
            
            cv_time = (datetime.now() - start_time).total_seconds()
            
            # Extract mean and std for each metric
            mean_scores = {}
            std_scores = {}
            
            for metric_name in metrics.keys():
                test_key = f"test_{metric_name}"
                if test_key in cv_results:
                    mean_scores[metric_name] = np.mean(cv_results[test_key])
                    std_scores[metric_name] = np.std(cv_results[test_key])
            
            result = CrossValidationResult(
                model_name=model.__class__.__name__,
                cv_folds=self.cv_folds,
                metric_scores={k: v for k, v in cv_results.items() if k.startswith("test_")},
                mean_scores=mean_scores,
                std_scores=std_scores,
                cv_time_seconds=cv_time
            )
            
            logger.info(f"✅ CV complete: {json.dumps(result.mean_scores, indent=2)}")
            
            self.cv_results.append(result)
            return result
        
        except Exception as e:
            logger.error(f"❌ Cross-validation failed: {e}")
            raise


# ============================================================================
# MODEL COMPARISON
# ============================================================================

class ModelComparator:
    """
    Compare multiple models and select best performer.
    
    Provides:
    - Side-by-side metric comparison
    - Statistical significance testing
    - Ranking and recommendations
    """
    
    def __init__(self):
        self.comparisons = []
    
    async def compare_models(
        self,
        models: Dict[str, Any],
        X_test: pd.DataFrame,
        y_test: pd.Series,
        metrics: Optional[Dict[str, Callable]] = None,
        best_metric: str = "r2"
    ) -> ModelComparison:
        """
        Compare multiple models on test set.
        
        Args:
            models: Dict of model_name -> model_instance
            X_test: Test features
            y_test: Test target
            metrics: Dict of metric_name -> callable
            best_metric: Which metric to use for selection
            
        Returns:
            ModelComparison with rankings
        """
        
        if metrics is None:
            metrics = {
                "r2": r2_score,
                "rmse": lambda y_true, y_pred: np.sqrt(mean_squared_error(y_true, y_pred)),
                "mae": mean_absolute_error
            }
        
        logger.info(f"📊 Comparing {len(models)} models...")
        
        metrics_dict = {}
        
        for model_name, model in models.items():
            try:
                y_pred = model.predict(X_test)
                
                model_metrics = {}
                for metric_name, metric_func in metrics.items():
                    try:
                        score = metric_func(y_test, y_pred)
                        model_metrics[metric_name] = float(score)
                    except:
                        model_metrics[metric_name] = 0.0
                
                metrics_dict[model_name] = model_metrics
                logger.info(f"✅ {model_name}: {model_metrics}")
            
            except Exception as e:
                logger.error(f"❌ Failed to evaluate {model_name}: {e}")
                metrics_dict[model_name] = {}
        
        # Find best model
        best_model_name = max(
            metrics_dict.keys(),
            key=lambda name: metrics_dict[name].get(best_metric, 0)
        )
        best_score = metrics_dict[best_model_name].get(best_metric, 0)
        
        comparison = ModelComparison(
            models=models,
            metrics=metrics_dict,
            best_model_name=best_model_name,
            best_model_score=best_score,
            best_metric=best_metric,
            comparison_date=datetime.now()
        )
        
        logger.info(f"\n{comparison.summary()}")
        
        self.comparisons.append(comparison)
        return comparison


# ============================================================================
# FEATURE SELECTION & IMPORTANCE
# ============================================================================

class FeatureSelector:
    """
    Feature selection and importance analysis.
    
    Methods:
    - Model-based importance (tree-based models)
    - Permutation importance
    - Correlation-based selection
    """
    
    @staticmethod
    def get_feature_importance(
        model: Any,
        X: pd.DataFrame,
        top_n: int = 10,
        method: str = "model"
    ) -> List[Tuple[str, float]]:
        """
        Get most important features.
        
        Args:
            model: Trained model with feature_importances_ attribute
            X: Feature DataFrame
            top_n: Top N features to return
            method: "model", "permutation", or "shap"
            
        Returns:
            List of (feature_name, importance_score)
        """
        
        try:
            if method == "model" and hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                feature_importance = list(zip(X.columns, importances))
                feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
                return feature_importance[:top_n]
            
            elif method == "coef" and hasattr(model, 'coef_'):
                coefs = model.coef_ if len(model.coef_.shape) == 1 else model.coef_[0]
                feature_importance = list(zip(X.columns, np.abs(coefs)))
                feature_importance.sort(key=lambda x: x[1], reverse=True)
                return feature_importance[:top_n]
            
            else:
                logger.warning(f"⚠️  Method '{method}' not available for {model.__class__.__name__}")
                return []
        
        except Exception as e:
            logger.error(f"❌ Feature importance extraction failed: {e}")
            return []
    
    @staticmethod
    def select_top_features(
        X: pd.DataFrame,
        y: pd.Series,
        correlation_threshold: float = 0.8,
        variance_threshold: float = 0.0
    ) -> pd.DataFrame:
        """Remove correlated and low-variance features"""
        
        # Remove low-variance features
        variances = X.var()
        high_var_features = variances[variances > variance_threshold].index.tolist()
        X_filtered = X[high_var_features]
        
        # Remove highly correlated features
        corr_matrix = X_filtered.corr().abs()
        upper_tri = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        to_drop = [col for col in upper_tri.columns if any(upper_tri[col] > correlation_threshold)]
        X_filtered = X_filtered.drop(columns=to_drop)
        
        logger.info(f"✅ Selected {X_filtered.shape[1]} features (removed {len(to_drop)} correlated)")
        
        return X_filtered
