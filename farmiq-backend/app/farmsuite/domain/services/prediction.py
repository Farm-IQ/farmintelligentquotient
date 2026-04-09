"""
Prediction Service
Pure business logic for farm predictions and forecasting
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import statistics
from app.shared import BaseService
from app.farmsuite.domain.entities.prediction import Prediction, PredictionType


@dataclass
class PredictionService(BaseService):
    """
    Service for generating farm predictions
    All methods are pure functions with no side effects
    """
    
    def predict_yield(
        self,
        historical_yields: List[float],
        growth_trend: float,  # -1 to 1
        season_factor: float,  # 0.5 to 1.5
        input_intensity: float,  # 0-1 (fertilizer, water investment)
    ) -> Tuple[float, float]:
        """
        Predict next season yield
        Returns: (predicted_yield, confidence)
        """
        if not historical_yields:
            return 0, 0
        
        # Base prediction from historical average
        avg_yield = statistics.mean(historical_yields)
        
        # Adjust for trend
        trend_adjustment = 1 + (growth_trend * 0.2)
        
        # Adjust for seasonal factor
        seasonal_adjusted = avg_yield * season_factor * trend_adjustment
        
        # Input intensity can boost yield by 0-30%
        input_boost = 1 + (input_intensity * 0.3)
        predicted_yield = seasonal_adjusted * input_boost
        
        # Calculate confidence based on historical consistency
        confidence = self._calculate_forecast_confidence(historical_yields)
        
        return predicted_yield, confidence
    
    def predict_production_revenue(
        self,
        predicted_yield_kg: float,
        predicted_price_per_kg: float,
        expected_loss_percent: float = 5,  # Postharvest losses
    ) -> Tuple[float, float]:
        """
        Predict production revenue
        Returns: (predicted_revenue, confidence)
        """
        self.validate_positive(predicted_yield_kg, "predicted_yield_kg")
        self.validate_positive(predicted_price_per_kg, "predicted_price_per_kg")
        
        # Account for postharvest losses
        marketable_yield = predicted_yield_kg * (1 - expected_loss_percent / 100)
        
        predicted_revenue = marketable_yield * predicted_price_per_kg
        
        # Confidence based on yield and price prediction stability
        confidence = 0.7
        
        return predicted_revenue, confidence
    
    def predict_production_expenses(
        self,
        farm_size_acres: float,
        crop_type: str,
        input_level: str,  # "low", "medium", "high"
        historical_expenses: List[float],
    ) -> Tuple[float, float]:
        """
        Predict production expenses
        Returns: (predicted_expenses, confidence)
        """
        self.validate_positive(farm_size_acres, "farm_size_acres")
        self.validate_not_empty(crop_type, "crop_type")
        
        # Base cost per acre by crop (in KES)
        base_costs = {
            "maize": {"low": 8000, "medium": 12000, "high": 18000},
            "tomato": {"low": 15000, "medium": 25000, "high": 40000},
            "bean": {"low": 6000, "medium": 10000, "high": 15000},
            "potato": {"low": 12000, "medium": 18000, "high": 28000},
        }
        
        crop_lower = crop_type.lower()
        input_level_lower = input_level.lower()
        
        base_per_acre = base_costs.get(crop_lower, {}).get(input_level_lower, 15000)
        calculated_expense = base_per_acre * farm_size_acres
        
        # Adjust based on historical data if available
        if historical_expenses and len(historical_expenses) > 0:
            avg_historical = statistics.mean(historical_expenses)
            # Use 60% calculated, 40% historical average to smooth predictions
            predicted = calculated_expense * 0.6 + avg_historical * 0.4
        else:
            predicted = calculated_expense
        
        # Add 5% inflation factor
        predicted *= 1.05
        
        confidence = 0.75 if historical_expenses else 0.60
        
        return predicted, confidence
    
    def predict_disease_incidence(
        self,
        crop_type: str,
        rainfall_forecast_mm: float,
        temperature_forecast_celsius: float,
        humidity_forecast_percent: float,
        historical_disease_pressure: float,  # 0-1
    ) -> Tuple[float, List[str]]:
        """
        Predict disease pressure for next period
        Returns: (disease_pressure_0_1, list_of_likely_diseases)
        """
        temperature_factor = 0
        if 18 <= temperature_forecast_celsius <= 28:  # Optimal for most diseases
            temperature_factor = 0.8
        elif 15 <= temperature_forecast_celsius <= 30:
            temperature_factor = 0.6
        else:
            temperature_factor = 0.2
        
        # Humidity factor (high humidity aids disease)
        humidity_factor = humidity_forecast_percent / 100
        
        # Rainfall factor (wet conditions favor disease)
        rainfall_factor = min(rainfall_forecast_mm / 100, 1.0)
        
        # Combined disease pressure
        pressure = (
            temperature_factor * 0.3 +
            humidity_factor * 0.35 +
            rainfall_factor * 0.35
        ) * 0.8 + historical_disease_pressure * 0.2  # Weighted with history
        
        # Identify likely diseases based on conditions
        likely_diseases = []
        
        crop_lower = crop_type.lower()
        
        if humidity_factor > 0.6 and rainfall_factor > 0.5:
            if crop_lower == "tomato":
                likely_diseases = ["Late Blight", "Early Blight", "Septoria Leaf Spot"]
            elif crop_lower == "potato":
                likely_diseases = ["Late Blight", "Early Blight"]
            elif crop_lower == "maize":
                likely_diseases = ["Leaf Blight", "Grey Leaf Spot"]
            elif crop_lower == "bean":
                likely_diseases = ["Anthracnose", "Bean Blight"]
        
        if temperature_factor > 0.6 and humidity_factor > 0.5:
            if not likely_diseases:
                likely_diseases.append("Various Fungal Diseases")
        
        return min(pressure, 1.0), likely_diseases
    
    def predict_pest_incidence(
        self,
        crop_type: str,
        previous_pest_pressure: float,  # 0-1
        temperature_forecast_celsius: float,
        rainfall_forecast_mm: float,
        weeks_into_season: int,
    ) -> Tuple[float, List[str]]:
        """
        Predict pest pressure
        Returns: (pest_pressure_0_1, list_of_likely_pests)
        """
        # Pest pressures are seasonal and temperature dependent
        # Pests more active in warm, wet conditions
        
        temp_factor = min((temperature_forecast_celsius - 15) / 15, 1.0) if temperature_forecast_celsius > 15 else 0
        rainfall_factor = min(rainfall_forecast_mm / 100, 1.0)
        
        # Seasonal factor (pests increase over season, peak mid-season)
        season_curve = min((weeks_into_season / 12) * 2, 1.0)  # Peaks at week 12
        
        pressure = (
            temp_factor * 0.3 +
            rainfall_factor * 0.3 +
            season_curve * 0.2 +
            previous_pest_pressure * 0.2
        )
        
        # Identify likely pests
        likely_pests = []
        crop_lower = crop_type.lower()
        
        if temp_factor > 0.5 and rainfall_factor > 0.3:
            if crop_lower == "maize":
                likely_pests = ["Fall Armyworm", "Stem Borer", "Cutworms"]
            elif crop_lower == "tomato":
                likely_pests = ["Whitefly", "Leaf Miner", "Spider Mite"]
            elif crop_lower == "bean":
                likely_pests = ["Bean Bruchid", "Leaf Beetle", "Aphids"]
            elif crop_lower == "potato":
                likely_pests = ["Potato Beetle", "Whitefly", "Aphids"]
        
        return min(pressure, 1.0), likely_pests
    
    def predict_market_price(
        self,
        product: str,
        historical_prices: List[float],
        seasonal_pattern: Dict[int, float],  # month -> seasonal factor
        current_month: int,
        supply_trend: float,  # -1 to 1 (declining to increasing)
        demand_trend: float,  # -1 to 1
    ) -> Tuple[float, float]:
        """
        Predict market price for next period
        Returns: (predicted_price, confidence)
        """
        if not historical_prices:
            return 0, 0
        
        # Base prediction from average
        avg_price = statistics.mean(historical_prices)
        
        # Apply seasonal adjustment
        next_month = (current_month % 12) + 1
        seasonal_factor = seasonal_pattern.get(next_month, 1.0)
        
        # Supply-demand dynamics
        # Increasing supply + decreasing demand = lower prices
        supply_demand_factor = 1 + (demand_trend - supply_trend) * 0.15
        
        # Trend analysis
        if len(historical_prices) >= 2:
            recent_trend = (historical_prices[-1] - historical_prices[0]) / historical_prices[0]
            trend_factor = 1 + (recent_trend * 0.3)  # Give trend some weight
        else:
            trend_factor = 1.0
        
        predicted_price = avg_price * seasonal_factor * supply_demand_factor * trend_factor
        
        # Confidence depends on historical data quality
        confidence = min(len(historical_prices) / 12, 0.9)  # Max 90%
        
        return predicted_price, confidence
    
    def predict_roi_on_production(
        self,
        predicted_revenue: float,
        predicted_costs: float,
        investment_amount: float,
    ) -> Tuple[float, float]:
        """
        Predict ROI from production
        Returns: (predicted_roi_percent, confidence)
        """
        profit = predicted_revenue - predicted_costs
        
        if investment_amount == 0:
            roi = 0
        else:
            roi = (profit / investment_amount) * 100
        
        # Confidence is moderate since it depends on multiple predictions
        confidence = 0.65
        
        return roi, confidence
    
    def predict_water_requirement(
        self,
        crop_type: str,
        farm_size_acres: float,
        rainfall_forecast_mm: float,
        growth_stage: str,  # "establishment", "growth", "flowering", "maturity"
    ) -> float:
        """
        Predict water requirement for crop
        Returns: irrigation need in mm
        """
        # Crop water requirements (mm) by stage
        water_needs = {
            "maize": {
                "establishment": 200,
                "growth": 400,
                "flowering": 300,
                "maturity": 150,
            },
            "tomato": {
                "establishment": 250,
                "growth": 450,
                "flowering": 350,
                "maturity": 200,
            },
            "bean": {
                "establishment": 150,
                "growth": 300,
                "flowering": 200,
                "maturity": 100,
            },
            "potato": {
                "establishment": 200,
                "growth": 350,
                "flowering": 250,
                "maturity": 150,
            },
        }
        
        crop_lower = crop_type.lower()
        total_need = water_needs.get(crop_lower, {}).get(growth_stage, 300)
        
        # Subtract expected rainfall
        irrigation_need = max(total_need - rainfall_forecast_mm, 0)
        
        return irrigation_need
    
    def predict_harvest_date(
        self,
        crop_type: str,
        planting_date: datetime,
        temperature_avg: float,
        growth_factor: float = 1.0,  # 0.8 to 1.2 based on conditions
    ) -> Tuple[datetime, int]:
        """
        Predict harvest date based on crop and conditions
        Returns: (predicted_harvest_date, days_to_harvest)
        """
        # Days to maturity by crop
        maturity_days = {
            "maize": 120,
            "tomato": 80,
            "bean": 90,
            "potato": 90,
        }
        
        base_days = maturity_days.get(crop_type.lower(), 100)
        
        # Temperature affects growth
        optimal_temp = 25
        if temperature_avg < 20 or temperature_avg > 30:
            growth_factor *= 0.8  # Slower growth outside optimal range
        
        # Adjust days to maturity
        adjusted_days = base_days / growth_factor
        
        predicted_date = planting_date + timedelta(days=adjusted_days)
        days_to_harvest = int((predicted_date - datetime.now()).days)
        
        return predicted_date, max(days_to_harvest, 0)
    
    def _calculate_forecast_confidence(self, historical_data: List[float]) -> float:
        """
        Calculate confidence based on data consistency
        More consistent data = higher confidence
        """
        if not historical_data or len(historical_data) < 2:
            return 0.5
        
        # Coefficient of variation (CV)
        avg = statistics.mean(historical_data)
        if avg == 0:
            return 0.5
        
        std_dev = statistics.stdev(historical_data)
        cv = std_dev / avg
        
        # Convert CV to confidence (lower CV = higher confidence)
        confidence = max(1 - cv, 0.3)  # Min 30% confidence
        
        # More data points increase confidence
        data_bonus = min(len(historical_data) / 12, 0.2)  # Up to 20% bonus
        
        return min(confidence + data_bonus, 0.95)
    
    def generate_prediction_reasoning(
        self,
        prediction_type: PredictionType,
        predicted_value: float,
        factors: List[str],
        confidence: float,
    ) -> str:
        """
        Generate human-readable explanation for prediction
        """
        explanations = {
            PredictionType.YIELD: f"Based on historical yields and current farm conditions, we predict a yield of {predicted_value:.0f} kg.",
            PredictionType.PRODUCTION: f"Expected production revenue is estimated at KES {predicted_value:,.0f}.",
            PredictionType.EXPENSES: f"Production costs are projected at KES {predicted_value:,.0f}.",
            PredictionType.DISEASE_RISK: f"Disease pressure risk is estimated at {predicted_value:.0%}.",
            PredictionType.MARKET_PRICE: f"Market price forecast is KES {predicted_value:.0f} per unit.",
            PredictionType.ROI: f"Expected ROI is projected at {predicted_value:.1f}%.",
        }
        
        base_explanation = explanations.get(prediction_type, "")
        
        if factors:
            factors_text = ", ".join(factors)
            base_explanation += f"\n\nKey factors: {factors_text}"
        
        confidence_text = {
            0.9: "This prediction is based on strong historical data and current conditions.",
            0.7: "This prediction is moderately confident based on available data.",
            0.5: "This prediction has moderate uncertainty - use as a guide.",
            0.3: "This prediction has high uncertainty - use with caution.",
        }
        
        # Find appropriate confidence text
        for threshold in sorted(confidence_text.keys(), reverse=True):
            if confidence >= threshold:
                base_explanation += f"\n\n{confidence_text[threshold]}"
                break
        
        return base_explanation
