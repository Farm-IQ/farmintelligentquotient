"""
Risk Assessment Service
Pure business logic for farm risk identification and mitigation
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from app.shared import BaseService
from app.farmsuite.domain.entities.risk import Risk, RiskCategory, RiskSeverity
from app.farmsuite.domain.entities.farm import Farm


@dataclass
class RiskAssessmentService(BaseService):
    """
    Service for assessing and analyzing farm risks
    All methods are pure functions with no side effects
    """
    
    def assess_pest_risk(
        self,
        crop_type: str,
        farm_size_acres: float,
        location: str,
        recent_pest_history: List[Dict],
        current_pest_pressure: float,  # 0-1
    ) -> Dict[str, float]:
        """
        Assess pest risk for a specific crop and location
        Returns risk scores for common pests
        """
        self.validate_not_empty(crop_type, "crop_type")
        self.validate_positive(farm_size_acres, "farm_size_acres")
        self.validate_range(current_pest_pressure, 0, 1, "current_pest_pressure")
        
        # Pest susceptibility by crop
        pest_map = {
            "maize": {
                "fall_armyworm": 0.8,
                "stemborer": 0.75,
                "termites": 0.6,
                "cutworms": 0.65,
            },
            "tomato": {
                "whitefly": 0.85,
                "leaf_miner": 0.8,
                "spider_mite": 0.7,
                "aphids": 0.75,
            },
            "bean": {
                "bruchid": 0.7,
                "leaf_beetle": 0.65,
                "spider_mite": 0.6,
                "aphids": 0.7,
            },
            "potato": {
                "potato_beetle": 0.65,
                "aphids": 0.75,
                "whitefly": 0.7,
                "mites": 0.6,
            },
        }
        
        crop_lower = crop_type.lower()
        base_susceptibility = pest_map.get(crop_lower, {})
        
        # Scale by current pressure (if high pressure detected, risk is higher)
        pest_risks = {}
        for pest, susceptibility in base_susceptibility.items():
            # Risk = base susceptibility * location factor * pressure
            risk = susceptibility * (0.7 + current_pest_pressure * 0.3)
            pest_risks[pest] = min(risk, 1.0)
        
        return pest_risks
    
    def assess_disease_risk(
        self,
        crop_type: str,
        rainfall_last_month_mm: float,
        humidity_avg_percent: float,
        temperature_avg_celsius: float,
        recent_disease_history: List[str],
    ) -> Dict[str, float]:
        """
        Assess disease risk based on environmental conditions
        Returns risk scores for common diseases
        """
        self.validate_not_empty(crop_type, "crop_type")
        self.validate_positive(rainfall_last_month_mm, "rainfall_last_month_mm")
        self.validate_range(humidity_avg_percent, 0, 100, "humidity_avg_percent")
        
        # Disease maps by crop and conditions
        disease_map = {
            "maize": {
                "leaf_blight": {"rain": 0.3, "humidity": 0.5, "temp": None},
                "rust": {"rain": 0.2, "humidity": 0.4, "temp": None},
                "grey_leaf_spot": {"rain": 0.25, "humidity": 0.45, "temp": None},
            },
            "tomato": {
                "late_blight": {"rain": 0.4, "humidity": 0.6, "temp": None},
                "early_blight": {"rain": 0.35, "humidity": 0.55, "temp": None},
                "septoria_leaf_spot": {"rain": 0.3, "humidity": 0.5, "temp": None},
                "powdery_mildew": {"rain": 0.1, "humidity": 0.3, "temp": None},
            },
            "bean": {
                "anthracnose": {"rain": 0.4, "humidity": 0.6, "temp": None},
                "rust": {"rain": 0.3, "humidity": 0.5, "temp": None},
                "blight": {"rain": 0.35, "humidity": 0.55, "temp": None},
            },
            "potato": {
                "late_blight": {"rain": 0.5, "humidity": 0.7, "temp": None},
                "early_blight": {"rain": 0.35, "humidity": 0.55, "temp": None},
                "bacterial_wilt": {"rain": 0.3, "humidity": 0.5, "temp": None},
            },
        }
        
        crop_lower = crop_type.lower()
        diseases = disease_map.get(crop_lower, {})
        
        # Calculate risk for each disease based on conditions
        disease_risks = {}
        
        # Normalize environmental factors to 0-1 scale
        rain_factor = min(rainfall_last_month_mm / 200, 1.0)  # 200mm = high risk
        humidity_factor = humidity_avg_percent / 100
        
        for disease, condition_weights in diseases.items():
            rain_contrib = condition_weights.get("rain", 0) * rain_factor if condition_weights.get("rain") else 0
            humidity_contrib = condition_weights.get("humidity", 0) * humidity_factor if condition_weights.get("humidity") else 0
            
            base_risk = rain_contrib + humidity_contrib
            
            # Increase risk if disease was present recently
            if disease in recent_disease_history:
                base_risk *= 1.3  # 30% increase for historical presence
            
            disease_risks[disease] = min(base_risk, 1.0)
        
        return disease_risks
    
    def assess_weather_vulnerability(
        self,
        crop_type: str,
        soil_type: str,
        irrigation_available: bool,
        water_storage_capacity: float,  # mm equivalent
    ) -> Dict[str, float]:
        """
        Assess vulnerability to weather risks
        Returns risk scores for drought, flooding, etc.
        """
        self.validate_not_empty(crop_type, "crop_type")
        self.validate_not_empty(soil_type, "soil_type")
        
        vulnerabilities = {}
        
        # Drought risk
        drought_base = {
            "maize": 0.4,
            "bean": 0.5,
            "tomato": 0.6,
            "potato": 0.3,
        }
        
        base_drought = drought_base.get(crop_type.lower(), 0.4)
        
        # Irrigation reduces drought risk
        irrigation_factor = 0.3 if irrigation_available else 1.0
        # Water storage reduces drought risk
        water_factor = max(1.0 - (water_storage_capacity / 100), 0.3)
        
        vulnerabilities["drought"] = base_drought * irrigation_factor * water_factor
        
        # Flooding risk (soil type dependent)
        flooding_soil_map = {
            "clay": 0.8,      # Clay drains poorly
            "silt": 0.6,
            "loam": 0.3,      # Loam has good drainage
            "sandy": 0.1,     # Sandy drains well
        }
        
        soil_flooding_factor = flooding_soil_map.get(soil_type.lower(), 0.5)
        vulnerabilities["flooding"] = soil_flooding_factor
        
        # Temperature extremes
        temp_crop_map = {
            "maize": 0.4,
            "bean": 0.5,
            "tomato": 0.6,  # More sensitive to temperature
            "potato": 0.35,
        }
        
        vulnerabilities["temperature_extremes"] = temp_crop_map.get(crop_type.lower(), 0.4)
        
        # Wind damage
        vulnerabilities["wind_damage"] = 0.3  # Generally low, unless location specific
        
        return vulnerabilities
    
    def assess_financial_risk(
        self,
        operating_leverage: float,  # % of costs that are fixed
        revenue_stability: float,   # 0-1 (1 = very stable)
        debt_to_production_value: float,  # Ratio
        market_concentration: float,  # 0-1 (concentration of sales)
    ) -> Dict[str, float]:
        """
        Assess financial risks
        Returns risk scores for different financial scenarios
        """
        self.validate_range(operating_leverage, 0, 100, "operating_leverage")
        self.validate_range(revenue_stability, 0, 1, "revenue_stability")
        
        risks = {}
        
        # Cash flow risk (high operating leverage + low revenue stability)
        leverage_factor = operating_leverage / 100
        stability_factor = 1 - revenue_stability
        risks["cash_flow_shortage"] = (leverage_factor * 0.6 + stability_factor * 0.4)
        
        # Debt risk
        debt_risk = min(debt_to_production_value / 2, 1.0)  # 2x is high risk
        risks["debt_pressure"] = debt_risk
        
        # Market concentration risk
        risks["buyer_concentration"] = market_concentration
        
        # Input cost vulnerability
        risks["input_cost_volatility"] = 0.4 + (leverage_factor * 0.3)
        
        return {k: min(v, 1.0) for k, v in risks.items()}
    
    def assess_operational_risk(
        self,
        workforce_stability: float,  # 0-1 (1 = very stable)
        equipment_age_years: int,
        maintenance_record_quality: str,  # "excellent", "good", "poor"
        diversification_index: float,  # 0-1 (crop diversity)
    ) -> Dict[str, float]:
        """
        Assess operational risks
        Returns risk scores for labor, equipment, and operational issues
        """
        self.validate_range(workforce_stability, 0, 1, "workforce_stability")
        self.validate_range(diversification_index, 0, 1, "diversification_index")
        
        risks = {}
        
        # Labor shortage risk (opposite of stability)
        risks["labor_shortage"] = 1 - workforce_stability
        
        # Equipment failure risk (age and maintenance)
        maintenance_factor = {
            "excellent": 0.1,
            "good": 0.4,
            "poor": 0.8,
        }.get(maintenance_record_quality.lower(), 0.5)
        
        age_factor = min(equipment_age_years / 10, 1.0)  # 10 years = high risk
        risks["equipment_failure"] = (age_factor * 0.6 + maintenance_factor * 0.4)
        
        # Lack of diversification risk
        risks["low_diversification"] = 1 - diversification_index
        
        # Skill gap risk
        risks["skill_gap"] = 0.3 + (workspace_stability := 1 - workforce_stability) * 0.2
        
        return {k: min(v, 1.0) for k, v in risks.items()}
    
    def calculate_overall_farm_risk_score(
        self,
        pest_risk_avg: float,
        disease_risk_avg: float,
        weather_vulnerability_avg: float,
        financial_risk_avg: float,
        operational_risk_avg: float,
    ) -> float:
        """
        Calculate overall farm risk score (0-1)
        Weighted average of all risk categories
        """
        risk = (
            pest_risk_avg * 0.15 +
            disease_risk_avg * 0.15 +
            weather_vulnerability_avg * 0.25 +
            financial_risk_avg * 0.25 +
            operational_risk_avg * 0.20
        )
        
        return min(risk, 1.0)
    
    def get_critical_risks(
        self,
        all_risks: Dict[str, Dict[str, float]],
        threshold: float = 0.6
    ) -> List[Dict[str, any]]:
        """
        Identify critical risks that exceed threshold
        Returns list of risks above threshold with details
        """
        critical = []
        
        for category, risks in all_risks.items():
            for risk_name, score in risks.items():
                if score >= threshold:
                    critical.append({
                        "category": category,
                        "risk": risk_name,
                        "score": score,
                        "severity": self._score_to_severity(score),
                    })
        
        # Sort by score descending
        return sorted(critical, key=lambda x: x["score"], reverse=True)
    
    def _score_to_severity(self, score: float) -> str:
        """Convert risk score to severity level"""
        if score >= 0.75:
            return "CRITICAL"
        elif score >= 0.5:
            return "HIGH"
        elif score >= 0.25:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_risk_mitigation_strategies(
        self,
        category: str,
        risk_name: str,
        risk_score: float
    ) -> List[str]:
        """
        Get specific mitigation strategies for a risk
        Returns actionable recommendations
        """
        strategies_map = {
            "pest": {
                "fall_armyworm": [
                    "Scout fields weekly for egg clusters",
                    "Use pheromone traps for early detection",
                    "Apply biopesticides (Bt) at egg stage",
                    "Recruit natural enemies (parasitoids)",
                ],
                "whitefly": [
                    "Use yellow sticky traps for monitoring",
                    "Spray insecticidal soap or neem oil",
                    "Control weeds that harbor whiteflies",
                    "Rotate crops to break pest cycle",
                ],
            },
            "disease": {
                "late_blight": [
                    "Plant resistant varieties",
                    "Improve air circulation with pruning",
                    "Apply fungicide preventatively in high humidity",
                    "Remove infected leaves immediately",
                ],
                "early_blight": [
                    "Remove lower infected leaves",
                    "Improve soil drainage",
                    "Apply copper-based fungicide",
                    "Rotate crops",
                ],
            },
            "weather": {
                "drought": [
                    "Install/improve irrigation system",
                    "Mulch to retain soil moisture",
                    "Plant drought-tolerant varieties",
                    "Build rainwater harvesting infrastructure",
                ],
                "flooding": [
                    "Improve field drainage",
                    "Plant on raised beds",
                    "Diversify to flood-tolerant crops",
                    "Monitor weather forecasts",
                ],
            },
            "financial": {
                "cash_flow_shortage": [
                    "Secure production credit before season",
                    "Negotiate input supplier payment terms",
                    "Diversify to reduce single product dependency",
                    "Build emergency savings fund",
                ],
                "low_prices": [
                    "Join farmer groups for bulk selling",
                    "Develop relationships with consistent buyers",
                    "Add value through processing",
                    "Plan to harvest during low-supply periods",
                ],
            },
        }
        
        # Get specific strategies
        strategies = strategies_map.get(category, {}).get(risk_name.lower(), [])
        
        # If no specific strategy, return general mitigation
        if not strategies:
            strategies = [
                f"Monitor {risk_name} closely",
                "Consult with extension officer for expert advice",
                "Document monitoring results",
                "Develop contingency plan",
            ]
        
        return strategies
    
    def calculate_risk_reduction_potential(
        self,
        current_risk_score: float,
        mitigation_actions: List[str]
    ) -> Tuple[float, float]:
        """
        Estimate potential risk reduction from proposed actions
        Returns: (potential_reduced_score, reduction_percentage)
        """
        # Each mitigation action reduces risk by 10-15%
        reduction_per_action = 0.12
        total_reduction = min(len(mitigation_actions) * reduction_per_action, 0.5)  # Cap at 50%
        
        reduced_score = current_risk_score * (1 - total_reduction)
        reduction_percent = (current_risk_score - reduced_score) / current_risk_score * 100
        
        return reduced_score, reduction_percent
