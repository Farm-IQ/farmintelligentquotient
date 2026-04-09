"""
Feature Engineering Pipeline for FarmSuite ML Models
=====================================================

Transforms raw farm data into ML-ready features for predictive models.

Features Generated:
1. Farm Scale Features (10 features)
   - Total acres, crop diversity index, livestock diversity
   - Equipment value, worker efficiency ratio
   
2. Production Efficiency Features (15 features)
   - Yield per acre, production consistency, input efficiency
   - ROI metric, seasonal variation, production trend
   
3. Soil & Environmental Features (12 features)
   - Soil health score, pH balance, organic matter content
   - Rainfall zone, temperature avg/min/max, irrigation efficiency
   
4. Health & Risk Indicators (10 features)
   - Disease pressure score, pest pressure score, water stress index
   - Nutrient deficiency risk, farm health composite score
   
5. Economic Features (8 features)
   - Total monthly expenses, input costs, labor costs per acre
   - Market price trend, price volatility, profitability ratio
   
6. Market Intelligence Features (7 features)
   - Commodity prices, demand level, market opportunity score
   - Competition intensity, buyer strength index
   
7. Worker & Labor Features (6 features)
   - Worker count, average productivity, training level
   - Labor availability index, workforce stability

Total: 68 ML-ready features per farm

Usage:
```python
engineer = FeatureEngineer()
features_df = await engineer.engineer_features(raw_farm_data)
```
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class SoilType(str, Enum):
    """Soil types in Kenya"""
    CLAY = "clay"
    LOAM = "loam"
    SANDY = "sandy"
    VOLCANIC = "volcanic"
    PEAT = "peat"


class RainfallZone(str, Enum):
    """Kenyan rainfall zones"""
    VERY_DRY = "very_dry"
    DRY = "dry"
    SEMI_ARID = "semi_arid"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass
class FeatureSet:
    """Container for engineered features"""
    farm_id: str
    features: Dict[str, float]
    feature_count: int
    engineering_date: datetime
    data_quality_score: float  # 0-1: percentage of features successfully engineered
    missing_features: List[str] = None
    
    def __post_init__(self):
        self.missing_features = []


class FeatureEngineer:
    """
    Main feature engineering orchestrator.
    
    Transforms raw farm data into standardized ML features.
    Handles missing values, scaling, and feature validation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_names = self._get_feature_names()
        self.scaler_stats = {}  # For normalization min/max values
    
    def _get_feature_names(self) -> List[str]:
        """Define all 68 engineered features"""
        
        farm_scale = [
            "total_acres", "crop_diversity_index", "livestock_diversity_index",
            "equipment_value_kes", "worker_efficiency_ratio", "farm_maturity_years",
            "farm_registration_status", "insurance_coverage_percent", 
            "access_to_extension_services", "mobile_phone_access"
        ]
        
        production = [
            "yield_kg_per_acre", "production_consistency_score", "input_efficiency_ratio",
            "roi_percent", "seasonal_variation_score", "production_trend",
            "crop_rotation_index", "intercropping_adoption", "fallow_land_percent",
            "irrigation_adoption_percent", "seed_quality_score", "fertilizer_efficiency",
            "pesticide_efficiency", "water_use_efficiency", "labor_productivity_kg_per_worker"
        ]
        
        soil_env = [
            "soil_health_score", "soil_ph_balance", "organic_matter_percent",
            "nitrogen_availability", "phosphorus_availability", "potassium_availability",
            "rainfall_zone_encoded", "rainfall_annual_mm", "temperature_avg_celsius",
            "temperature_min_celsius", "temperature_max_celsius", "frost_risk_days_per_year"
        ]
        
        health_risk = [
            "disease_pressure_score", "pest_pressure_score", "water_stress_index",
            "nutrient_deficiency_risk", "soil_erosion_risk", "weed_pressure_score",
            "farm_health_composite_score", "risk_exposure_index", "disaster_vulnerability_score",
            "climate_change_adaptation_index"
        ]
        
        economic = [
            "total_monthly_expense_kes", "input_cost_per_acre_kes", "labor_cost_per_acre_kes",
            "transport_cost_percent", "storage_cost_percent", "market_price_trend",
            "price_volatility_percent", "profitability_ratio"
        ]
        
        market = [
            "commodity_price_per_unit_kes", "demand_level_index", "market_opportunity_score",
            "competition_intensity", "buyer_strength_index", "supply_consistency_score",
            "price_predictability_score"
        ]
        
        labor = [
            "worker_count", "average_worker_productivity_kg_per_day", "training_level_score",
            "labor_availability_index", "workforce_stability_percent", "seasonal_worker_ratio"
        ]
        
        return farm_scale + production + soil_env + health_risk + economic + market + labor
    
    async def engineer_features(
        self,
        farm_data: Dict[str, Any],
        return_feature_set: bool = True
    ) -> FeatureSet | Dict[str, float]:
        """
        Transform raw farm data into ML-ready features.
        
        Args:
            farm_data: Raw farm data dictionary
            return_feature_set: Return FeatureSet object or just dict
            
        Returns:
            FeatureSet or Dict of engineered features
        """
        
        try:
            farm_id = farm_data.get("id", "unknown")
            features = {}
            missing_features = []
            
            # 1. Farm Scale Features
            farm_features = self._engineer_farm_scale_features(farm_data)
            features.update(farm_features)
            
            # 2. Production Features
            prod_features = self._engineer_production_features(farm_data)
            features.update(prod_features)
            
            # 3. Soil & Environmental Features
            soil_features = self._engineer_soil_env_features(farm_data)
            features.update(soil_features)
            
            # 4. Health & Risk Features
            health_features = self._engineer_health_risk_features(farm_data, farm_features)
            features.update(health_features)
            
            # 5. Economic Features
            econ_features = self._engineer_economic_features(farm_data)
            features.update(econ_features)
            
            # 6. Market Features
            market_features = self._engineer_market_features(farm_data)
            features.update(market_features)
            
            # 7. Labor Features
            labor_features = self._engineer_labor_features(farm_data)
            features.update(labor_features)
            
            # Validate features
            for feature_name in self.feature_names:
                if feature_name not in features:
                    features[feature_name] = 0.0
                    missing_features.append(feature_name)
            
            # Calculate data quality
            data_quality = (len(self.feature_names) - len(missing_features)) / len(self.feature_names)
            
            if return_feature_set:
                return FeatureSet(
                    farm_id=farm_id,
                    features=features,
                    feature_count=len(features),
                    engineering_date=datetime.now(),
                    data_quality_score=data_quality,
                    missing_features=missing_features
                )
            else:
                return features
        
        except Exception as e:
            self.logger.error(f"Feature engineering failed for farm {farm_data.get('id')}: {e}")
            raise
    
    def _engineer_farm_scale_features(self, farm_data: Dict) -> Dict[str, float]:
        """Engineer 10 farm scale features"""
        
        total_acres = farm_data.get("total_acres", 1.0)
        crop_types = farm_data.get("crop_types", [])
        livestock_types = farm_data.get("livestock_types", [])
        worker_count = farm_data.get("worker_count", 1)
        
        features = {
            "total_acres": float(total_acres),
            "crop_diversity_index": min(len(set(crop_types)) / 5.0, 1.0),  # 0-1 normalized
            "livestock_diversity_index": min(len(set(livestock_types)) / 4.0, 1.0),
            "equipment_value_kes": float(farm_data.get("equipment_value_kes", 100000)),
            "worker_efficiency_ratio": min(100 / max(total_acres * worker_count, 1), 1.0),  # Persons per 100 acres
            "farm_maturity_years": float(farm_data.get("years_farming", 5)),
            "farm_registration_status": 1.0 if farm_data.get("is_registered", False) else 0.0,
            "insurance_coverage_percent": float(farm_data.get("insurance_coverage_percent", 0)),
            "access_to_extension_services": 1.0 if farm_data.get("has_extension_access", False) else 0.0,
            "mobile_phone_access": 1.0 if farm_data.get("has_mobile_phone", False) else 0.0,
        }
        
        return features
    
    def _engineer_production_features(self, farm_data: Dict) -> Dict[str, float]:
        """Engineer 15 production efficiency features"""
        
        production = farm_data.get("production", {})
        
        yield_kg_per_acre = float(production.get("yield_kg_per_acre", 500))
        total_acres = farm_data.get("total_acres", 1.0)
        total_production = production.get("total_production_kg", yield_kg_per_acre * total_acres)
        input_cost = farm_data.get("total_input_cost_kes", 50000)
        
        # Production revenue
        market_price = farm_data.get("market_price_kes_per_unit", 40)
        revenue = total_production * market_price
        roi = ((revenue - input_cost) / input_cost * 100) if input_cost > 0 else 0
        
        # Historical yields for consistency
        yield_history = production.get("yield_history_last_3_years", [yield_kg_per_acre] * 3)
        consistency = 1.0 - (np.std(yield_history) / np.mean(yield_history)) if np.mean(yield_history) > 0 else 0.5
        
        features = {
            "yield_kg_per_acre": yield_kg_per_acre,
            "production_consistency_score": max(0, min(consistency, 1.0)),
            "input_efficiency_ratio": min(total_production / max(input_cost / 1000, 1), 10.0),
            "roi_percent": max(0, min(roi, 500.0)),  # Cap at 500%
            "seasonal_variation_score": 1.0 - min(np.std(yield_history) / 100 if len(yield_history) > 1 else 0.1, 1.0),
            "production_trend": float(1.0 if yield_history[-1] > yield_history[0] else 0.5),  # 1 if improving
            "crop_rotation_index": 1.0 if farm_data.get("practices", {}).get("crop_rotation", False) else 0.0,
            "intercropping_adoption": 1.0 if farm_data.get("practices", {}).get("intercropping", False) else 0.0,
            "fallow_land_percent": float(farm_data.get("practices", {}).get("fallow_percent", 0)) / 100.0,
            "irrigation_adoption_percent": float(farm_data.get("irrigation_method", "rainfed") != "rainfed"),
            "seed_quality_score": float(farm_data.get("practices", {}).get("seed_quality", 0.8)),
            "fertilizer_efficiency": min(float(farm_data.get("practices", {}).get("fertilizer_efficiency", 0.7)), 1.0),
            "pesticide_efficiency": min(float(farm_data.get("practices", {}).get("pest_control_efficiency", 0.6)), 1.0),
            "water_use_efficiency": min(float(farm_data.get("practices", {}).get("water_efficiency", 0.7)), 1.0),
            "labor_productivity_kg_per_worker": yield_kg_per_acre / max(farm_data.get("worker_count", 1), 1),
        }
        
        return features
    
    def _engineer_soil_env_features(self, farm_data: Dict) -> Dict[str, float]:
        """Engineer 12 soil and environmental features"""
        
        soil = farm_data.get("soil", {})
        location = farm_data.get("location", {})
        
        # Soil health composite
        soil_health = (
            soil.get("health_score", 0.6) * 0.4 +
            (soil.get("organic_matter_percent", 3) / 5.0) * 0.3 +
            (soil.get("ph_balance", 7) / 8.0) * 0.3
        )
        
        # Rainfall zone mapping
        rainfall_zone = farm_data.get("rainfall_zone", RainfallZone.MODERATE)
        zone_encoding = {
            RainfallZone.VERY_DRY: 1.0,
            RainfallZone.DRY: 2.0,
            RainfallZone.SEMI_ARID: 3.0,
            RainfallZone.MODERATE: 4.0,
            RainfallZone.HIGH: 5.0,
        }
        
        features = {
            "soil_health_score": min(soil_health, 1.0),
            "soil_ph_balance": min(abs(soil.get("ph_balance", 7) - 7) / 2.0, 1.0),  # Closer to 7 is better
            "organic_matter_percent": min(soil.get("organic_matter_percent", 3) / 8.0, 1.0),
            "nitrogen_availability": min(soil.get("nitrogen_mg_per_kg", 15) / 50.0, 1.0),
            "phosphorus_availability": min(soil.get("phosphorus_mg_per_kg", 10) / 30.0, 1.0),
            "potassium_availability": min(soil.get("potassium_mg_per_kg", 200) / 400.0, 1.0),
            "rainfall_zone_encoded": zone_encoding.get(rainfall_zone, 3.0) / 5.0,
            "rainfall_annual_mm": float(location.get("annual_rainfall_mm", 800)) / 2000.0,
            "temperature_avg_celsius": (float(location.get("temperature_avg", 20)) - 10) / 20.0,  # Normalized
            "temperature_min_celsius": (float(location.get("temperature_min", 10)) - 0) / 20.0,
            "temperature_max_celsius": (float(location.get("temperature_max", 30)) - 20) / 20.0,
            "frost_risk_days_per_year": 1.0 - (float(location.get("frost_risk_days", 0)) / 180.0),
        }
        
        return features
    
    def _engineer_health_risk_features(self, farm_data: Dict, farm_features: Dict) -> Dict[str, float]:
        """Engineer 10 health and risk indicator features"""
        
        health = farm_data.get("health_assessment", {})
        
        # Composite health score
        farm_health = (
            health.get("disease_score", 0.4) * 0.25 +
            health.get("pest_score", 0.4) * 0.25 +
            health.get("water_stress_score", 0.3) * 0.25 +
            health.get("nutrition_score", 0.6) * 0.25
        )
        
        features = {
            "disease_pressure_score": min(health.get("disease_score", 0.4), 1.0),
            "pest_pressure_score": min(health.get("pest_score", 0.4), 1.0),
            "water_stress_index": min(health.get("water_stress_score", 0.3), 1.0),
            "nutrient_deficiency_risk": 1.0 - min(health.get("nutrition_score", 0.6), 1.0),
            "soil_erosion_risk": min(health.get("erosion_risk", 0.3), 1.0),
            "weed_pressure_score": min(health.get("weed_pressure", 0.3), 1.0),
            "farm_health_composite_score": min(farm_health, 1.0),
            "risk_exposure_index": min(
                (health.get("disease_score", 0.4) + health.get("pest_score", 0.4)) / 2.0,
                1.0
            ),
            "disaster_vulnerability_score": min(health.get("disaster_risk", 0.2), 1.0),
            "climate_change_adaptation_index": 1.0 - min(health.get("climate_vulnerability", 0.5), 1.0),
        }
        
        return features
    
    def _engineer_economic_features(self, farm_data: Dict) -> Dict[str, float]:
        """Engineer 8 economic features"""
        
        expenses = farm_data.get("expenses", {})
        production = farm_data.get("production", {})
        
        total_monthly = float(expenses.get("total_monthly_kes", 50000))
        total_acres = farm_data.get("total_acres", 1.0)
        input_cost = float(farm_data.get("total_input_cost_kes", 50000))
        
        # Historical expenses for trend
        expense_history = expenses.get("monthly_history_last_3_months", [total_monthly] * 3)
        trend = expense_history[-1] / expense_history[0] if expense_history[0] > 0 else 1.0
        volatility = np.std(expense_history) / np.mean(expense_history) if np.mean(expense_history) > 0 else 0.2
        
        # Revenue calculation
        yield_kg_per_acre = production.get("yield_kg_per_acre", 500)
        market_price = farm_data.get("market_price_kes_per_unit", 40)
        revenue_per_acre = yield_kg_per_acre * market_price
        profit_per_acre = revenue_per_acre - (input_cost / total_acres)
        profitability = profit_per_acre / revenue_per_acre if revenue_per_acre > 0 else 0
        
        features = {
            "total_monthly_expense_kes": min(total_monthly / 100000.0, 2.0),  # Normalized
            "input_cost_per_acre_kes": min(input_cost / total_acres / 50000.0, 2.0),
            "labor_cost_per_acre_kes": min(float(expenses.get("labor_cost_per_acre", 10000)) / 50000.0, 1.0),
            "transport_cost_percent": min(float(expenses.get("transport_percent", 5)) / 20.0, 1.0),
            "storage_cost_percent": min(float(expenses.get("storage_percent", 5)) / 20.0, 1.0),
            "market_price_trend": min(float(farm_data.get("price_trend", 1.0)), 2.0),
            "price_volatility_percent": min(volatility, 1.0),
            "profitability_ratio": max(0, min(profitability, 1.0)),
        }
        
        return features
    
    def _engineer_market_features(self, farm_data: Dict) -> Dict[str, float]:
        """Engineer 7 market intelligence features"""
        
        market = farm_data.get("market_intelligence", {})
        
        features = {
            "commodity_price_per_unit_kes": min(float(farm_data.get("market_price_kes_per_unit", 40)) / 100.0, 2.0),
            "demand_level_index": min(float(market.get("demand_level", 0.7)), 1.0),
            "market_opportunity_score": min(float(market.get("opportunity_score", 0.6)), 1.0),
            "competition_intensity": min(float(market.get("competition", 0.5)), 1.0),
            "buyer_strength_index": min(float(market.get("buyer_strength", 0.6)), 1.0),
            "supply_consistency_score": min(float(market.get("supply_consistency", 0.7)), 1.0),
            "price_predictability_score": min(float(market.get("price_predictability", 0.5)), 1.0),
        }
        
        return features
    
    def _engineer_labor_features(self, farm_data: Dict) -> Dict[str, float]:
        """Engineer 6 labor and workforce features"""
        
        worker_count = farm_data.get("worker_count", 1)
        total_acres = farm_data.get("total_acres", 1.0)
        yield_kg_per_acre = farm_data.get("production", {}).get("yield_kg_per_acre", 500)
        
        features = {
            "worker_count": min(float(worker_count) / 10.0, 1.0),  # Normalized
            "average_worker_productivity_kg_per_day": min(yield_kg_per_acre / max(worker_count, 1) / 200.0, 2.0),
            "training_level_score": min(float(farm_data.get("worker_training_score", 0.5)), 1.0),
            "labor_availability_index": min(float(farm_data.get("labor_availability", 0.7)), 1.0),
            "workforce_stability_percent": min(float(farm_data.get("worker_retention_percent", 70)) / 100.0, 1.0),
            "seasonal_worker_ratio": min(float(farm_data.get("seasonal_worker_count", 0)) / max(worker_count, 1), 1.0),
        }
        
        return features
    
    async def engineer_batch(
        self,
        farms_data: List[Dict[str, Any]],
        return_dataframe: bool = True
    ) -> pd.DataFrame | List[FeatureSet]:
        """
        Engineer features for multiple farms.
        
        Args:
            farms_data: List of raw farm data dicts
            return_dataframe: Return as DataFrame or list of FeatureSets
            
        Returns:
            DataFrame with one row per farm, or list of FeatureSet objects
        """
        
        feature_sets = []
        
        for farm_data in farms_data:
            try:
                feature_set = await self.engineer_features(farm_data, return_feature_set=True)
                feature_sets.append(feature_set)
            except Exception as e:
                self.logger.warning(f"Failed to engineer features for farm {farm_data.get('id')}: {e}")
                continue
        
        if return_dataframe:
            # Convert to DataFrame
            rows = []
            for fs in feature_sets:
                row = {"farm_id": fs.farm_id}
                row.update(fs.features)
                rows.append(row)
            
            return pd.DataFrame(rows)
        else:
            return feature_sets
