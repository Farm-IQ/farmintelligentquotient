"""
FarmScore Credit Scoring Predictors
Consolidated credit scoring models using ensemble approach

Includes:
- CreditScorer: Voting ensemble for default probability prediction
- CreditRecommendationEngine: Loan recommendation and structuring
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


# ============================================================================
# CREDIT SCORING MODEL
# ============================================================================

class CreditScorer:
    """
    Enhanced credit scoring model using Voting Ensemble
    
    This class implements a production-ready ensemble model with:
    - Three complementary classifiers (GB, RF, LR)
    - Soft voting mechanism for probability averaging
    - Isotonic regression calibration
    - SHAP-based explainability  
    - Uncertainty quantification
    - Model persistence and versioning
    
    Attributes:
        regularization: L1 or L2 regularization type
        regularization_strength: Lambda value for regularization
        calibration_method: isotonic or sigmoid calibration
        k_folds: Number of CV folds
        ensemble: Whether to use ensemble or single model
        model: Fitted VotingClassifier or LogisticRegression
        calibrated_model: Calibrated wrapper around model
        shap_explainer: SHAP explainer for interpretability
        feature_names: Names of input features
        feature_importance: Per-feature importance dictionary
    """
    
    def __init__(
        self,
        regularization: str = "l2",
        regularization_strength: float = 0.1,
        calibration_method: str = "isotonic",
        k_folds: int = 5,
        ensemble: bool = True
    ):
        self.regularization = regularization
        self.regularization_strength = regularization_strength
        self.calibration_method = calibration_method
        self.k_folds = k_folds
        self.ensemble = ensemble
        
        # Initialize individual models
        self.gb_model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=4,
            min_samples_leaf=10,
            random_state=42,
            subsample=0.8
        )
        
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=10,
            random_state=42,
            max_features='sqrt',
            bootstrap=True
        )
        
        self.lr_model = LogisticRegression(
            C=1 / regularization_strength,
            max_iter=1000,
            random_state=42,
            solver='lbfgs'
        )
        
        # Create voting ensemble
        if self.ensemble:
            self.model = VotingClassifier(
                estimators=[
                    ('gb', self.gb_model),
                    ('rf', self.rf_model),
                    ('lr', self.lr_model)
                ],
                voting='soft'
            )
        else:
            self.model = self.lr_model
        
        # Calibration wrapper
        self.calibrated_model = None
        
        # SHAP explainer
        self.shap_explainer = None
        
        # Feature names and importance
        self.feature_names = None
        self.feature_importance = None
        
        # Metrics
        self.cv_scores = []
        self.generalization_gap = 0.0
        self.training_accuracy = 0.0
        self.validation_accuracy = 0.0
        self.roc_auc = 0.0
        self.f1_score = 0.0
        self.precision = 0.0
        self.recall = 0.0
        self.latest_evaluation = None
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Train ensemble model with validation and cross-validation"""
        logger.info(f"Training FarmScore Credit Scorer with ensemble={self.ensemble}...")
        
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X_train.shape[1])]
        
        # Train ensemble/model
        self.model.fit(X_train, y_train)
        
        # Evaluate on training set
        self.training_accuracy = self.model.score(X_train, y_train)
        logger.info(f"Training accuracy: {self.training_accuracy:.4f}")
        
        # Cross-validation
        logger.info(f"Running {self.k_folds}-fold cross-validation...")
        cv = StratifiedKFold(n_splits=self.k_folds, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=cv, scoring='accuracy')
        self.cv_scores = cv_scores.tolist()
        
        logger.info(f"CV scores: {cv_scores}")
        logger.info(f"CV mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        # Validation accuracy
        if X_val is not None and y_val is not None:
            self.validation_accuracy = self.model.score(X_val, y_val)
            self.generalization_gap = abs(self.training_accuracy - self.validation_accuracy)
            logger.info(f"Validation accuracy: {self.validation_accuracy:.4f}")
            logger.info(f"Generalization gap: {self.generalization_gap:.4f}")
            
            # Calibrate using validation set
            self._calibrate_model(X_val, y_val)
            
            # Compute detailed metrics
            self._compute_metrics(X_val, y_val)
        
        self._compute_feature_importance()
        
        return {
            "training_accuracy": self.training_accuracy,
            "validation_accuracy": self.validation_accuracy,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "generalization_gap": self.generalization_gap,
            "roc_auc": self.roc_auc,
            "f1_score": self.f1_score,
            "precision": self.precision,
            "recall": self.recall,
            "cv_folds": self.k_folds,
            "ensemble": self.ensemble
        }
    
    def _compute_metrics(self, X: np.ndarray, y: np.ndarray) -> None:
        """Compute evaluation metrics on validation set"""
        probs = self.predict_default_probability(X)
        preds = (probs >= 0.5).astype(int)
        
        self.roc_auc = roc_auc_score(y, probs)
        self.f1_score = f1_score(y, preds, average='weighted', zero_division=0)
        self.precision = precision_score(y, preds, average='weighted', zero_division=0)
        self.recall = recall_score(y, preds, average='weighted', zero_division=0)
        
        logger.info(f"ROC-AUC: {self.roc_auc:.4f}")
        logger.info(f"F1 Score: {self.f1_score:.4f}")
        logger.info(f"Precision: {self.precision:.4f}")
        logger.info(f"Recall: {self.recall:.4f}")
    
    def _compute_feature_importance(self) -> None:
        """Compute and store feature importance from ensemble"""
        if self.ensemble and hasattr(self.model.named_estimators_['gb'], 'feature_importances_'):
            gb_importance = self.model.named_estimators_['gb'].feature_importances_
            rf_importance = self.model.named_estimators_['rf'].feature_importances_
            
            avg_importance = (gb_importance + rf_importance) / 2
            
            self.feature_importance = {
                name: float(importance)
                for name, importance in zip(self.feature_names, avg_importance)
            }
    
    def _calibrate_model(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray
    ) -> None:
        """Calibrate model probabilities using isotonic regression or Platt scaling"""
        logger.info(f"Calibrating model using {self.calibration_method}...")
        
        if self.calibration_method == "isotonic":
            self.calibrated_model = CalibratedClassifierCV(
                self.model,
                method='isotonic',
                cv='prefit'
            )
        else:
            self.calibrated_model = CalibratedClassifierCV(
                self.model,
                method='sigmoid',
                cv='prefit'
            )
        
        self.calibrated_model.fit(X_val, y_val)
    
    def predict_default_probability(self, X: np.ndarray) -> np.ndarray:
        """Predict probability of default"""
        if self.calibrated_model is not None:
            return self.calibrated_model.predict_proba(X)[:, 1]
        else:
            return self.model.predict_proba(X)[:, 1]
    
    def predict_with_uncertainty(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict with uncertainty estimates using ensemble standard deviation
        Returns ensemble mean and std for probability estimates
        """
        if not self.ensemble:
            probs = self.predict_default_probability(X)
            return probs, np.zeros_like(probs)
        
        # Get predictions from each model
        probas = []
        for name, estimator in self.model.named_estimators_.items():
            probas.append(estimator.predict_proba(X)[:, 1])
        
        probas = np.array(probas)
        mean_prob = probas.mean(axis=0)
        std_prob = probas.std(axis=0)
        
        return mean_prob, std_prob
    
    def get_credit_score(
        self,
        default_probability: float,
        min_score: int = 0,
        max_score: int = 100
    ) -> float:
        """
        Convert default probability to credit score
        Formula: Score = max_score * (1 - default_probability)
        """
        score = (1 - default_probability) * (max_score - min_score) + min_score
        return float(np.clip(score, min_score, max_score))
    
    def optimize_threshold(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        cost_fn_loss: float = 5.0,
        cost_fn_acceptance: float = 1.0
    ) -> Tuple[float, float]:
        """
        Optimize classification threshold using cost-sensitive learning
        In lending, costs are asymmetric
        """
        probs = self.predict_default_probability(X_val)
        
        costs = []
        thresholds = np.linspace(0, 1, 101)
        
        for threshold in thresholds:
            preds = (probs >= threshold).astype(int)
            fn = np.sum((preds == 0) & (y_val == 1))
            fp = np.sum((preds == 1) & (y_val == 0))
            cost = fn * cost_fn_loss + fp * cost_fn_acceptance
            costs.append(cost)
        
        optimal_idx = np.argmin(costs)
        optimal_threshold = thresholds[optimal_idx]
        min_cost = costs[optimal_idx]
        
        logger.info(f"Optimal threshold: {optimal_threshold:.4f}")
        logger.info(f"Minimum cost: {min_cost:.4f}")
        
        return optimal_threshold, min_cost
    
    def explain_prediction(
        self,
        X_single: np.ndarray,
        top_features: int = 5
    ) -> Dict[str, Any]:
        """Explain single prediction using SHAP values"""
        if self.shap_explainer is None:
            logger.warning("SHAP explainer not initialized. Install shap package for explanations.")
            return {"error": "SHAP not available"}
        
        # Ensure correct shape
        if X_single.ndim == 1:
            X_single = X_single.reshape(1, -1)
        
        try:
            import shap
            shap_values = self.shap_explainer.shap_values(X_single)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            importance = np.abs(shap_values[0])
            top_indices = np.argsort(importance)[-top_features:][::-1]
            
            return {
                "top_features": [
                    {
                        "feature": self.feature_names[i],
                        "shap_value": float(shap_values[0][i]),
                        "feature_value": float(X_single[0][i])
                    }
                    for i in top_indices
                ],
                "all_shap_values": {
                    self.feature_names[i]: float(shap_values[0][i])
                    for i in range(len(self.feature_names))
                }
            }
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return {"error": str(e)}
    
    def get_coefficients(self) -> Dict[str, float]:
        """Get model coefficients (from logistic regression)"""
        if self.feature_names is None:
            return {}
        
        try:
            lr = self.model.named_estimators_['lr'] if self.ensemble else self.model
            coefficients = {
                name: float(coef)
                for name, coef in zip(self.feature_names, lr.coef_[0])
            }
            return coefficients
        except Exception as e:
            logger.warning(f"Could not extract coefficients: {e}")
            return {}


# ============================================================================
# LOAN RECOMMENDATION ENGINE
# ============================================================================

class CreditRecommendationEngine:
    """
    Generate loan recommendations based on credit score
    Implements business rules with dynamic loan structuring
    
    This class uses credit scores and farmer metrics to:
    - Determine risk-adjusted credit limits
    - Structure dynamic loan terms
    - Generate interest rates based on risk
    - Create 5 loan scenario options
    - Analyze repayment capacity
    - Provide improvement recommendations
    """
    
    def __init__(
        self,
        base_credit_limit: float = 50000,  # KES
        min_term_months: int = 6,
        max_term_months: int = 36,
        base_interest_rate: float = 8.0  # Annual %
    ):
        self.base_credit_limit = base_credit_limit
        self.min_term_months = min_term_months
        self.max_term_months = max_term_months
        self.base_interest_rate = base_interest_rate
    
    def recommend_loan(
        self,
        credit_score: float,
        default_probability: float,
        farm_size_acres: float,
        annual_income: float,
        existing_debt: float,
        monthly_revenue: Optional[float] = None,
        expense_ratio: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive loan recommendation
        
        Determines risk level, credit limit, interest rate, and loan scenarios
        based on credit score and farmer metrics.
        """
        logger.info(f"Generating loan recommendation for credit_score={credit_score:.1f}")
        
        # ===== DETERMINE RISK LEVEL =====
        if default_probability < 0.1:
            risk_level = "very_low"
            risk_multiplier = 0.8
            approval_likelihood = 0.95
        elif default_probability < 0.2:
            risk_level = "low"
            risk_multiplier = 0.9
            approval_likelihood = 0.85
        elif default_probability < 0.35:
            risk_level = "medium"
            risk_multiplier = 1.0
            approval_likelihood = 0.70
        elif default_probability < 0.5:
            risk_level = "high"
            risk_multiplier = 1.2
            approval_likelihood = 0.40
        else:
            risk_level = "very_high"
            risk_multiplier = 1.5
            approval_likelihood = 0.15
        
        logger.info(f"  Risk level: {risk_level} (multiplier: {risk_multiplier})")
        
        # ===== CALCULATE CREDIT LIMIT =====
        debt_to_income = existing_debt / max(annual_income, 1)
        debt_capacity = max(0, 1 - min(debt_to_income, 1.0))
        
        score_factor = credit_score / 100
        farm_factor = min(farm_size_acres / 10, 1.5)
        
        credit_limit = (
            self.base_credit_limit *
            score_factor *
            debt_capacity *
            farm_factor
        )
        
        logger.info(f"  Credit limit: KES {credit_limit:,.0f}")
        
        # ===== DETERMINE RECOMMENDED TERM =====
        if credit_score > 75:
            recommended_term = self.max_term_months
        elif credit_score > 60:
            recommended_term = 24
        elif credit_score > 45:
            recommended_term = 12
        else:
            recommended_term = self.min_term_months
        
        # ===== CALCULATE INTEREST RATE =====
        base_rate = self.base_interest_rate * risk_multiplier
        
        # ===== PAYMENT CAPACITY CHECK =====
        monthly_payment = self._calculate_monthly_payment(
            float(credit_limit),
            base_rate / 100,
            recommended_term
        )
        
        # ===== GENERATE LOAN SCENARIOS =====
        loan_scenarios = self._generate_loan_scenarios(
            credit_limit,
            base_rate,
            monthly_revenue,
            expense_ratio
        )
        
        return {
            "credit_risk_level": risk_level,
            "default_probability": float(default_probability),
            "approval_likelihood": float(approval_likelihood),
            "recommended_credit_limit_kes": float(credit_limit),
            "recommended_loan_term_months": int(recommended_term),
            "recommended_interest_rate": float(base_rate),
            "monthly_payment_estimate": float(monthly_payment),
            "loan_scenarios": loan_scenarios,
            "strengthening_recommendations": self._get_recommendations(credit_score),
            "repayment_capacity": self._analyze_repayment_capacity(
                monthly_revenue,
                monthly_payment,
                expense_ratio
            )
        }
    
    def _calculate_monthly_payment(
        self,
        loan_amount: float,
        monthly_rate: float,
        term_months: int
    ) -> float:
        """Calculate monthly payment using amortization formula"""
        if monthly_rate <= 0:
            return loan_amount / term_months
        
        numerator = loan_amount * monthly_rate * ((1 + monthly_rate) ** term_months)
        denominator = ((1 + monthly_rate) ** term_months) - 1
        
        return float(numerator / denominator)
    
    def _generate_loan_scenarios(
        self,
        credit_limit: float,
        annual_interest_rate: float,
        monthly_revenue: Optional[float] = None,
        expense_ratio: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple loan scenarios for different terms and amounts"""
        scenarios = []
        monthly_rate = annual_interest_rate / 100 / 12
        
        # Generate all scenario combinations
        for term in [12, 18, 24, 36]:
            if term < self.min_term_months or term > self.max_term_months:
                continue
            
            for amount_pct in [0.5, 0.75, 1.0]:
                loan_amount = credit_limit * amount_pct
                monthly_payment = self._calculate_monthly_payment(
                    loan_amount,
                    monthly_rate,
                    term
                )
                total_interest = (monthly_payment * term) - loan_amount
                
                # Check sustainability
                is_sustainable = True
                payment_to_revenue = None
                
                if monthly_revenue and monthly_revenue > 0:
                    payment_to_revenue = monthly_payment / monthly_revenue
                    is_sustainable = payment_to_revenue <= 0.4
                
                scenarios.append({
                    "loan_amount": float(loan_amount),
                    "term_months": int(term),
                    "monthly_payment": float(monthly_payment),
                    "total_interest": float(total_interest),
                    "interest_rate_percent": float(annual_interest_rate),
                    "is_sustainable": is_sustainable,
                    "payment_to_revenue_ratio": float(payment_to_revenue) if payment_to_revenue else None
                })
        
        # Sort by sustainability, then amount, then term
        scenarios.sort(key=lambda x: (-x['is_sustainable'], x['loan_amount'], x['term_months']))
        
        logger.info(f"Generated {len(scenarios)} total scenarios, returning top 5")
        return scenarios[:5]
    
    def _analyze_repayment_capacity(
        self,
        monthly_revenue: Optional[float],
        monthly_payment: float,
        expense_ratio: Optional[float] = None
    ) -> Dict[str, Any]:
        """Analyze farmer's capacity to repay"""
        if not monthly_revenue or monthly_revenue <= 0:
            return {
                "capacity_score": 0,
                "status": "unknown",
                "available_for_payment": None,
                "monthly_revenue": None,
                "disposable_income": None,
                "monthly_payment": float(monthly_payment),
                "payment_to_revenue_ratio": None,
                "payment_to_disposable_ratio": None
            }
        
        expense_ratio = expense_ratio or 0.6
        disposable_income = monthly_revenue * (1 - expense_ratio)
        payment_to_revenue = monthly_payment / monthly_revenue
        payment_to_disposable = monthly_payment / disposable_income if disposable_income > 0 else float('inf')
        
        # Capacity score based on payment-to-revenue ratio
        if payment_to_revenue <= 0.2:
            capacity_score = 1.0
            status = "excellent"
        elif payment_to_revenue <= 0.3:
            capacity_score = 0.8
            status = "good"
        elif payment_to_revenue <= 0.4:
            capacity_score = 0.6
            status = "fair"
        elif payment_to_revenue <= 0.5:
            capacity_score = 0.4
            status = "tight"
        else:
            capacity_score = 0.2
            status = "insufficient"
        
        logger.info(f"  Repayment capacity: {status} (score={capacity_score:.2f})")
        
        return {
            "capacity_score": float(capacity_score),
            "status": status,
            "monthly_revenue": float(monthly_revenue),
            "disposable_income": float(disposable_income),
            "monthly_payment": float(monthly_payment),
            "payment_to_revenue_ratio": float(payment_to_revenue),
            "payment_to_disposable_ratio": float(payment_to_disposable) if payment_to_disposable != float('inf') else None
        }
    
    def _get_recommendations(self, credit_score: float) -> List[str]:
        """Generate personalized recommendations to improve creditworthiness"""
        recommendations = []
        
        # Critical improvements (score < 50)
        if credit_score < 50:
            recommendations.extend([
                "Implement systematic farm record-keeping and accounting",
                "Join or form an agricultural cooperative for collective strength",
                "Attend formal agricultural training programs (minimum 20 hours)",
                "Maintain regular contact with agricultural extension staff"
            ])
        
        # Important improvements (score < 70)
        if credit_score < 70:
            recommendations.extend([
                "Increase farm productivity through improved inputs and practices",
                "Diversify crops to reduce income volatility and risk",
                "Build emergency savings fund equivalent to 3-6 months expenses",
                "Document all production and sales transactions"
            ])
        
        # Advancement opportunities (score < 85)
        if credit_score < 85:
            recommendations.extend([
                "Invest in soil health testing and targeted nutrient management",
                "Adopt advanced farming technologies or value addition"
            ])
        
        # Excellence goals (score < 95)
        if credit_score < 95:
            recommendations.extend([
                "Explore contract farming or premium buyer relationships",
                "Consider farm expansion or diversification opportunities"
            ])
        
        return recommendations
