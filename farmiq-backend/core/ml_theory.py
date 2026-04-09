"""
FarmSuite AI - ML Model Base Classes & ML Theory Framework
Implements learning theory principles:
- Hoeffding Inequality & PAC Learning
- VC Dimension & Generalization Bounds
- Structural Risk Minimization (SRM)
- Bias-Variance Decomposition
- Cross-validation & Model Selection
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ML THEORY ENUMS & DATACLASSES
# ============================================================================

class LearningTheoryPrinciple(str, Enum):
    """ML Learning Theory Principles Referenced"""
    HOEFFDING_INEQUALITY = "hoeffding_inequality"
    VC_DIMENSION = "vc_dimension"
    RADEMACHER_COMPLEXITY = "rademacher_complexity"
    STRUCTURAL_RISK_MINIMIZATION = "structural_risk_minimization"
    BIAS_VARIANCE_DECOMPOSITION = "bias_variance_decomposition"
    CROSS_VALIDATION = "cross_validation"
    REGULARIZATION = "regularization"
    EMPIRICAL_RISK_MINIMIZATION = "empirical_risk_minimization"


class RegularizationType(str, Enum):
    """Regularization types (SRM)"""
    NONE = "none"
    L1 = "l1"  # LASSO
    L2 = "l2"  # Ridge/Tikhonov
    L1L2 = "l1l2"  # Elastic Net
    EARLY_STOPPING = "early_stopping"


@dataclass
class GeneralizationBound:
    """
    Hoeffding Inequality: PAC Learning Bound
    
    With probability 1-δ, the true error is bounded by:
    E[error] ≤ E_in[error] + sqrt(ln(2K/δ) / 2N)
    
    Where:
    - E[error]: True (out-of-sample) error
    - E_in[error]: In-sample error
    - K: Hypothesis set size / VC dimension proxy
    - δ: Confidence level (e.g., 0.05)
    - N: Training set size
    """
    in_sample_error: float  # E_in
    out_sample_error: float  # E_out (estimated via validation)
    hypothesis_complexity: int  # K (e.g., VC dimension)
    sample_size: int  # N
    confidence_delta: float = 0.05
    
    @property
    def hoeffding_bound(self) -> float:
        """Calculate Hoeffding inequality bound"""
        if self.sample_size == 0:
            return float('inf')
        return np.sqrt(np.log(2 * self.hypothesis_complexity / self.confidence_delta) / (2 * self.sample_size))
    
    @property
    def generalization_error(self) -> float:
        """E_in + bound"""
        return self.in_sample_error + self.hoeffding_bound
    
    @property
    def generalization_gap(self) -> float:
        """E_out - E_in (bias-variance tradeoff)"""
        return self.out_sample_error - self.in_sample_error


@dataclass
class BiasVarianceDecomposition:
    """
    Bias-Variance Decomposition:
    Expected Error = Bias² + Variance + Noise
    
    - Bias: Model systematically underfits data (undercapacity)
    - Variance: Model overfits to training noise (overcapacity)
    - Noise: Irreducible error
    """
    bias_squared: float
    variance: float
    noise: float
    
    @property
    def total_expected_error(self) -> float:
        return self.bias_squared + self.variance + self.noise
    
    @property
    def model_complexity_appropriate(self) -> bool:
        """Check if bias and variance are roughly balanced"""
        return abs(self.bias_squared - self.variance) < 0.1


@dataclass
class CrossValidationMetrics:
    """K-Fold Cross-Validation Results"""
    fold_scores: List[float]  # Accuracy/metric for each fold
    fold_count: int
    shuffle: bool = False
    stratified: bool = False
    random_state: Optional[int] = None
    
    @property
    def mean_score(self) -> float:
        return np.mean(self.fold_scores)
    
    @property
    def std_score(self) -> float:
        return np.std(self.fold_scores)
    
    @property
    def ci_95(self) -> Tuple[float, float]:
        """95% Confidence interval"""
        mean = self.mean_score
        std_error = self.std_score / np.sqrt(self.fold_count)
        margin = 1.96 * std_error
        return (mean - margin, mean + margin)


# ============================================================================
# BASE CLASSES FOR ML SYSTEMS
# ============================================================================

class MLModel(ABC):
    """
    Base class for all FarmSuite ML Models
    Ensures adherence to ML theory principles and best practices
    """
    
    def __init__(
        self, 
        model_name: str,
        model_type: str,  # 'classification', 'regression', 'ranking'
        vc_dimension_estimate: Optional[int] = None,
        regularization_type: RegularizationType = RegularizationType.L2,
        regularization_strength: float = 0.1,
        ml_theory_notes: str = ""
    ):
        self.model_name = model_name
        self.model_type = model_type
        self.vc_dimension_estimate = vc_dimension_estimate
        self.regularization_type = regularization_type
        self.regularization_strength = regularization_strength
        self.ml_theory_notes = ml_theory_notes
        
        # Metrics storage
        self.training_error: Optional[float] = None
        self.validation_error: Optional[float] = None
        self.test_error: Optional[float] = None
        self.cross_validation_metrics: Optional[CrossValidationMetrics] = None
        self.generalization_bound: Optional[GeneralizationBound] = None
        self.bias_variance: Optional[BiasVarianceDecomposition] = None
    
    @abstractmethod
    def train(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train model with optional validation set
        
        Returns:
            Training metrics dict
        """
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        pass
    
    @abstractmethod
    def evaluate(
        self, 
        X_test: np.ndarray, 
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate on test set"""
        pass
    
    @abstractmethod
    def cross_validate(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        k_folds: int = 5,
        shuffle: bool = True,
        stratified: bool = False
    ) -> CrossValidationMetrics:
        """Perform k-fold cross-validation (defense against overfitting)"""
        pass
    
    @abstractmethod
    def explain_prediction(self, x_single: np.ndarray) -> Dict[str, Any]:
        """
        Explain single prediction (SHAP, LIME, feature importance)
        Required for credit scoring and forex systems
        """
        pass
    
    def calculate_generalization_bound(
        self, 
        training_size: int,
        confidence_delta: float = 0.05
    ) -> GeneralizationBound:
        """
        Calculate Hoeffding inequality bound
        Requires: training_error, validation_error, vc_dimension_estimate
        """
        if self.training_error is None or self.validation_error is None:
            raise ValueError("Must set training_error and validation_error first")
        
        if self.vc_dimension_estimate is None:
            self.vc_dimension_estimate = 10  # Conservative estimate
        
        self.generalization_bound = GeneralizationBound(
            in_sample_error=self.training_error,
            out_sample_error=self.validation_error,
            hypothesis_complexity=self.vc_dimension_estimate,
            sample_size=training_size,
            confidence_delta=confidence_delta
        )
        
        logger.info(
            f"Generalization Bound (Hoeffding): {self.generalization_bound.hoeffding_bound:.4f}\n"
            f"Generalization Error: {self.generalization_bound.generalization_error:.4f}"
        )
        
        return self.generalization_bound
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get comprehensive model summary with ML theory metrics"""
        summary = {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "regularization": {
                "type": self.regularization_type.value,
                "strength": self.regularization_strength
            },
            "complexity": {
                "vc_dimension_estimate": self.vc_dimension_estimate
            },
            "performance": {
                "training_error": self.training_error,
                "validation_error": self.validation_error,
                "test_error": self.test_error
            },
            "theory_metrics": {
                "generalization_bound": self.generalization_bound.__dict__ if self.generalization_bound else None,
                "bias_variance": self.bias_variance.__dict__ if self.bias_variance else None,
                "cross_validation": {
                    "mean": self.cross_validation_metrics.mean_score,
                    "std": self.cross_validation_metrics.std_score,
                    "ci_95": self.cross_validation_metrics.ci_95
                } if self.cross_validation_metrics else None
            },
            "ml_theory_notes": self.ml_theory_notes
        }
        return summary


class RegressionModel(MLModel):
    """Base for regression models (FarmScore volatility, returns)"""
    
    def __init__(self, **kwargs):
        super().__init__(model_type='regression', **kwargs)
    
    @abstractmethod
    def predict_with_uncertainty(
        self, 
        X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with confidence intervals"""
        pass


class ClassificationModel(MLModel):
    """Base for classification models (FarmIQ credit scoring, FarmScore signals)"""
    
    def __init__(self, **kwargs):
        super().__init__(model_type='classification', **kwargs)
    
    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities"""
        pass
    
    @abstractmethod
    def get_calibration_curve(
        self, 
        X_val: np.ndarray, 
        y_val: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get calibration curve (Platt or Isotonic)
        Ensures predicted probabilities match true probabilities
        """
        pass


class RAGModel(ABC):
    """Base class for RAG components (not classical ML but needs explainability)"""
    
    @abstractmethod
    def get_relevance_score(self, query: str, document: str) -> float:
        """Calculate relevance between query and document"""
        pass
    
    @abstractmethod
    def explain_relevance(
        self, 
        query: str, 
        document: str
    ) -> Dict[str, Any]:
        """Explain why a document is relevant to query"""
        pass


# ============================================================================
# MODEL REGISTRY INTERFACE
# ============================================================================

class ModelRegistry:
    """
    Registry for tracking all trained models
    Implements MLOps best practices
    """
    
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
    
    def register_model(
        self,
        model_name: str,
        model_version: str,
        model_obj: MLModel,
        metrics: Dict[str, float],
        ml_theory_metrics: Dict[str, Any]
    ) -> None:
        """Register trained model"""
        key = f"{model_name}:{model_version}"
        self.models[key] = {
            "model": model_obj,
            "metrics": metrics,
            "ml_theory_metrics": ml_theory_metrics,
            "registered_at": np.datetime64('now')
        }
        logger.info(f"✅ Model registered: {key}")
    
    def get_model(self, model_name: str, version: Optional[str] = None) -> Optional[MLModel]:
        """Get model by name and optional version"""
        if version:
            key = f"{model_name}:{version}"
            return self.models.get(key, {}).get("model")
        
        # Get latest version
        matching_keys = [k for k in self.models if k.startswith(model_name)]
        if matching_keys:
            latest_key = sorted(matching_keys)[-1]
            return self.models[latest_key]["model"]
        
        return None
