"""
Production Calculation Service
Pure business logic for farm production metrics and calculations
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from app.shared import BaseService
from app.farmsuite.domain.entities.production import Production
from app.farmsuite.domain.entities.farm import Farm


@dataclass
class ProductionCalculationService(BaseService):
    """
    Service for calculating production metrics and analytics
    All methods are pure functions with no side effects
    """
    
    def calculate_yield_efficiency(
        self,
        total_yield_kg: float,
        total_acres: float,
        expected_yield_per_acre: float
    ) -> float:
        """
        Calculate yield efficiency percentage
        Returns: % of expected yield achieved
        """
        self.validate_positive(total_yield_kg, "total_yield_kg")
        self.validate_positive(total_acres, "total_acres")
        self.validate_positive(expected_yield_per_acre, "expected_yield_per_acre")
        
        actual_yield_per_acre = total_yield_kg / total_acres
        efficiency = (actual_yield_per_acre / expected_yield_per_acre) * 100
        return min(efficiency, 200)  # Cap at 200%
    
    def calculate_revenue_per_acre(
        self,
        total_revenue: float,
        total_acres: float
    ) -> float:
        """Calculate revenue per acre"""
        self.validate_positive(total_revenue, "total_revenue")
        self.validate_positive(total_acres, "total_acres")
        return total_revenue / total_acres
    
    def calculate_production_consistency_score(
        self,
        monthly_yields: List[float]
    ) -> float:
        """
        Calculate consistency score based on yield variation
        Higher score = more consistent
        Returns 0-100
        """
        if not monthly_yields or len(monthly_yields) < 2:
            return 50.0
        
        # Use coefficient of variation (CV) to measure consistency
        import statistics
        try:
            mean_yield = statistics.mean(monthly_yields)
            if mean_yield == 0:
                return 50.0
            
            std_dev = statistics.stdev(monthly_yields)
            cv = (std_dev / mean_yield) * 100
            
            # Convert CV to consistency score (lower CV = higher score)
            # CV of 10% = 90 score, CV of 50% = 50 score, CV of 100% = 0 score
            consistency_score = max(100 - cv, 0)
            return min(consistency_score, 100)
        except:
            return 50.0
    
    def calculate_seasonal_multiplier(self, month: int) -> float:
        """
        Calculate seasonal production multiplier (0.5 to 1.5)
        Based on typical agricultural seasons
        Returns adjustment factor
        """
        if month < 1 or month > 12:
            return 1.0
        
        # In Kenya (East Africa pattern):
        # Dec-Mar: Short rains (planting/early growth) - 0.8x
        # Apr-Oct: Long rains & main season - 1.3x
        # Nov: Transition - 0.9x
        
        seasonal_factors = {
            1: 0.8,   # January - post main season decline
            2: 0.75,  # February - lowest
            3: 0.8,   # March - start of preparation
            4: 1.1,   # April - short rains begin
            5: 1.2,   # May - growth accelerates
            6: 1.3,   # June - peak season
            7: 1.35,  # July - peak season
            8: 1.3,   # August - still strong
            9: 1.2,   # September - start decline
            10: 1.1,  # October - harvest time
            11: 0.9,  # November - transition
            12: 0.85, # December - end of season
        }
        
        return seasonal_factors.get(month, 1.0)
    
    def calculate_cost_of_production_per_unit(
        self,
        total_costs: float,
        total_yield_kg: float
    ) -> float:
        """Calculate cost per kg produced"""
        self.validate_positive(total_costs, "total_costs")
        self.validate_positive(total_yield_kg, "total_yield_kg")
        return total_costs / total_yield_kg
    
    def calculate_profit_margin(
        self,
        total_revenue: float,
        total_costs: float
    ) -> float:
        """Calculate profit margin percentage"""
        self.validate_positive(total_revenue, "total_revenue")
        self.validate_positive(total_costs, "total_costs")
        
        profit = total_revenue - total_costs
        return (profit / total_revenue) * 100 if total_revenue > 0 else 0
    
    def calculate_roi(
        self,
        total_revenue: float,
        total_investment: float
    ) -> float:
        """
        Calculate Return on Investment
        Returns percentage ROI
        """
        self.validate_positive(total_revenue, "total_revenue")
        self.validate_positive(total_investment, "total_investment")
        
        return ((total_revenue - total_investment) / total_investment) * 100
    
    def calculate_production_growth_rate(
        self,
        current_yield: float,
        previous_yield: float,
        months_between: int = 1
    ) -> float:
        """
        Calculate production growth rate (%)
        Compound Annual Growth Rate (CAGR) if months > 1
        """
        self.validate_positive(current_yield, "current_yield")
        self.validate_positive(previous_yield, "previous_yield")
        
        if previous_yield == 0:
            return 0
        
        growth_rate = ((current_yield / previous_yield) ** (12 / max(months_between, 1)) - 1) * 100
        return growth_rate
    
    def calculate_water_efficiency(
        self,
        total_yield_kg: float,
        water_used_liters: float
    ) -> float:
        """
        Calculate water efficiency (kg per 1000 liters)
        Higher is better
        """
        self.validate_positive(total_yield_kg, "total_yield_kg")
        self.validate_positive(water_used_liters, "water_used_liters")
        
        return (total_yield_kg / max(water_used_liters, 1)) * 1000
    
    def calculate_nutrient_budget(
        self,
        crop_type: str,
        total_acres: float,
        target_yield_kg_per_acre: float
    ) -> Dict[str, float]:
        """
        Calculate nutrient requirements based on crop and target yield
        Returns dict with N, P, K requirements in kg
        """
        self.validate_not_empty(crop_type, "crop_type")
        self.validate_positive(total_acres, "total_acres")
        self.validate_positive(target_yield_kg_per_acre, "target_yield_kg_per_acre")
        
        # Standard nitrogen requirements (kg/ha) at different yield levels
        # Based on typical extension service recommendations
        nutrient_maps = {
            "maize": {
                "N_per_yield_unit": 0.02,  # kg N per kg yield
                "P_per_yield_unit": 0.004,
                "K_per_yield_unit": 0.015,
            },
            "tomato": {
                "N_per_yield_unit": 0.04,
                "P_per_yield_unit": 0.008,
                "K_per_yield_unit": 0.05,
            },
            "bean": {
                "N_per_yield_unit": 0.01,  # Legumes fix some nitrogen
                "P_per_yield_unit": 0.004,
                "K_per_yield_unit": 0.015,
            },
            "potato": {
                "N_per_yield_unit": 0.035,
                "P_per_yield_unit": 0.008,
                "K_per_yield_unit": 0.065,
            },
        }
        
        crop_lower = crop_type.lower()
        requirements = nutrient_maps.get(crop_lower, nutrient_maps["maize"])  # Default to maize
        
        total_target_yield = target_yield_kg_per_acre * total_acres
        
        return {
            "nitrogen_kg": total_target_yield * requirements["N_per_yield_unit"],
            "phosphorus_kg": total_target_yield * requirements["P_per_yield_unit"],
            "potassium_kg": total_target_yield * requirements["K_per_yield_unit"],
        }
    
    def calculate_input_to_output_ratio(
        self,
        input_cost: float,
        output_value: float
    ) -> float:
        """
        Calculate input/output ratio
        Returns how many units of output per unit of input cost
        Higher is better (more efficient)
        """
        self.validate_positive(input_cost, "input_cost")
        self.validate_positive(output_value, "output_value")
        
        return output_value / input_cost
    
    def calculate_break_even_yield(
        self,
        fixed_costs: float,
        variable_cost_per_unit: float,
        selling_price_per_unit: float
    ) -> float:
        """
        Calculate break-even yield (units needed to be produced to cover costs)
        """
        self.validate_positive(fixed_costs, "fixed_costs")
        self.validate_positive(variable_cost_per_unit, "variable_cost_per_unit")
        self.validate_positive(selling_price_per_unit, "selling_price_per_unit")
        
        contribution_margin = selling_price_per_unit - variable_cost_per_unit
        if contribution_margin <= 0:
            return float('inf')
        
        return fixed_costs / contribution_margin
    
    def calculate_production_forecast(
        self,
        historical_yields: List[float],
        months_ahead: int = 3
    ) -> Tuple[float, float]:
        """
        Simple production forecast using average with seasonal adjustment
        Returns: (forecast_yield, confidence_score)
        """
        if not historical_yields or len(historical_yields) == 0:
            return 0, 0
        
        import statistics
        avg_yield = statistics.mean(historical_yields)
        
        # Confidence based on data points
        confidence = min(len(historical_yields) / 12, 1.0)  # 0-1 based on months of data
        
        # Simple exponential smoothing for trend
        if len(historical_yields) >= 2:
            trend = (historical_yields[-1] - historical_yields[0]) / len(historical_yields)
            forecast = avg_yield + (trend * (months_ahead / 12))
        else:
            forecast = avg_yield
        
        return max(forecast, 0), confidence
    
    def get_production_health_score(
        self,
        yield_efficiency: float,  # 0-100
        consistency_score: float,  # 0-100
        profit_margin: float,     # -100 to 100+
    ) -> float:
        """
        Calculate overall production health score (0-100)
        Combines yield efficiency, consistency, and profitability
        """
        # Normalize profit margin to 0-100 scale
        profit_score = min(max(profit_margin + 50, 0), 100)
        
        # Weighted average
        health_score = (
            yield_efficiency * 0.35 +
            consistency_score * 0.35 +
            profit_score * 0.30
        )
        
        return min(health_score, 100)
    
    def get_production_recommendations(
        self,
        yield_efficiency: float,
        consistency_score: float,
        profit_margin: float,
        water_efficiency: float,
    ) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        if yield_efficiency < 70:
            recommendations.append(
                "📋 Yield is below target. Review soil health, variety selection, and pest management."
            )
        
        if consistency_score < 60:
            recommendations.append(
                "📊 High yield variability detected. Standardize practices and improve soil consistency."
            )
        
        if profit_margin < 10:
            recommendations.append(
                "💰 Low profitability. Analyze input costs and explore improved markets."
            )
        
        if water_efficiency < 3:  # Less than 3kg per 1000L
            recommendations.append(
                "💧 Water efficiency is low. Consider irrigation improvements or different varieties."
            )
        
        if not recommendations:
            recommendations.append("✅ Production metrics are strong!")
        
        return recommendations
