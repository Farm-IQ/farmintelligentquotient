"""
FarmSuite Phase 3: Synthetic Data Generator for Kenya
===============================================

Generates realistic Kenyan smallholder farm data matching the normalized schema.

PURPOSE:
- Train models before real farm data is available
- A/B test different farming strategies & interventions
- Create benchmark scenarios for comparison
- Stress test ML pipeline with diverse scenarios
- Demo system with meaningful examples

KENYAN CONTEXT:
- Farm sizes: 2-5 acres (typical smallholder)
- Crops: Maize, beans, tomatoes, kale, potatoes, carrots, onions
- Livestock: Dairy cattle, poultry, goats, sheep, pigs
- Counties: 47 Kenyan counties (Nairobi, Kisii, Nakuru, Kiambu, etc.)
- Seasons: Dual cropping (March-June / Oct-Dec)
- Currency: Kenyan Shilling (KES)

FARM SCENARIOS:
1. Subsistence (1-2 acres, survival farming, low inputs)
2. Smallholder Mixed (2-4 acres, crops + livestock, moderate inputs)
3. Market-Oriented (3-6 acres, target-driven, improved varieties)
4. Livestock-Focused (2-5 acres, dairy/poultry primary)
5. Horticulture (1.5-4 acres, high-value vegetables)
6. Diversified (4-8 acres, multiple enterprises)

OUTPUTS:
- 1000+ synthetic farms generated per run
- Complete 12-month transaction history
- Realistic seasonal patterns
- Market price fluctuations
- Production risks (pests, disease)
- Training-ready DataFrame
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import random

logger = logging.getLogger(__name__)


# ============================================================================
# KENYAN AGRICULTURAL DATA - ENUMS
# ============================================================================

class KenyanCounty(str, Enum):
    """47 Kenyan Counties"""
    NAIROBI = "Nairobi"
    KISII = "Kisii"
    NAKURU = "Nakuru"
    KIAMBU = "Kiambu"
    MOMBASA = "Mombasa"
    UASIN_GISHU = "Uasin Gishu"
    NYERI = "Nyeri"
    NYANDARUA = "Nyandarua"
    VIHIGA = "Vihiga"
    MURANGA = "Muranga"
    KERICHO = "Kericho"
    KAKAMEGA = "Kakamega"
    KISUMU = "Kisumu"
    OKEYO = "Okeyo"
    BUNGOMA = "Bungoma"
    TRANS_NZOIA = "Trans Nzoia"
    MAKUENI = "Makueni"
    KAJIADO = "Kajiado"
    SAMBURU = "Samburu"
    TURKANA = "Turkana"
    WEST_POKOT = "West Pokot"
    ELGEYO_MARAKWET = "Elgeyo Marakwet"
    LAIKIPIA = "Laikipia"
    ISIOLO = "Isiolo"
    MERU = "Meru"
    THARAKA_NITHI = "Tharaka Nithi"
    EMBU = "Embu"
    MACHAKOS = "Machakos"
    KILIFI = "Kilifi"
    LAMU = "Lamu"
    TAITA_TAVETA = "Taita Taveta"
    NAROK = "Narok"
    MIGORI = "Migori"
    HOMA_BAY = "Homa Bay"
    SIAYA = "Siaya"
    NYAMIRA = "Nyamira"
    BOMET = "Bomet"
    WAJIR = "Wajir"
    GARISSA = "Garissa"
    MANDERA = "Mandera"


class CropType(str, Enum):
    """Major Kenyan crops"""
    MAIZE = "Maize"
    BEANS = "Beans"
    TOMATOES = "Tomatoes"
    KALE = "Kale"
    POTATOES = "Potatoes"
    CARROTS = "Carrots"
    CABBAGE = "Cabbage"
    ONIONS = "Onions"
    PEPPER = "Pepper"
    CUCUMBER = "Cucumber"


class LivestockType(str, Enum):
    """Kenyan livestock"""
    DAIRY_CATTLE = "Dairy Cattle"
    BEEF_CATTLE = "Beef Cattle"
    POULTRY = "Poultry"
    GOATS = "Goats"
    SHEEP = "Sheep"
    PIGS = "Pigs"


class FarmScenario(str, Enum):
    """Different farm typologies"""
    SUBSISTENCE = "subsistence"
    SMALLHOLDER_MIXED = "smallholder_mixed"
    MARKET_ORIENTED = "market_oriented"
    LIVESTOCK_FOCUSED = "livestock_focused"
    HORTICULTURE = "horticulture"
    DIVERSIFIED = "diversified"


# ============================================================================
# CROP & LIVESTOCK SPECIFICATIONS
# ============================================================================

CROP_SPECS = {
    "Maize": {
        "altitude_suitable_min_masl": 500,
        "altitude_suitable_max_masl": 2400,
        "rainfall_mm_min": 500,
        "rainfall_mm_max": 1500,
        "yield_kg_per_acre_low": 400,
        "yield_kg_per_acre_high": 800,
        "planting_seasons": ["March-May", "October-December"],
        "maturity_days": 120,
        "input_cost_per_acre_low": 12000,
        "input_cost_per_acre_high": 25000,
        "market_price_kes_per_kg_low": 22,
        "market_price_kes_per_kg_high": 35,
    },
    "Tomatoes": {
        "altitude_suitable_min_masl": 800,
        "altitude_suitable_max_masl": 2000,
        "rainfall_mm_min": 600,
        "rainfall_mm_max": 1200,
        "yield_kg_per_acre_low": 8000,
        "yield_kg_per_acre_high": 14000,
        "planting_seasons": ["Year-round"],
        "maturity_days": 70,
        "input_cost_per_acre_low": 60000,
        "input_cost_per_acre_high": 100000,
        "market_price_kes_per_kg_low": 25,
        "market_price_kes_per_kg_high": 60,
    },
    "Beans": {
        "altitude_suitable_min_masl": 400,
        "altitude_suitable_max_masl": 2100,
        "rainfall_mm_min": 450,
        "rainfall_mm_max": 1100,
        "yield_kg_per_acre_low": 300,
        "yield_kg_per_acre_high": 600,
        "planting_seasons": ["March-May", "October-December"],
        "maturity_days": 90,
        "input_cost_per_acre_low": 8000,
        "input_cost_per_acre_high": 15000,
        "market_price_kes_per_kg_low": 60,
        "market_price_kes_per_kg_high": 120,
    },
    "Kale": {
        "altitude_suitable_min_masl": 800,
        "altitude_suitable_max_masl": 2400,
        "rainfall_mm_min": 600,
        "rainfall_mm_max": 1500,
        "yield_kg_per_acre_low": 6000,
        "yield_kg_per_acre_high": 12000,
        "planting_seasons": ["Year-round"],
        "maturity_days": 50,
        "input_cost_per_acre_low": 15000,
        "input_cost_per_acre_high": 30000,
        "market_price_kes_per_kg_low": 15,
        "market_price_kes_per_kg_high": 40,
    },
    "Potatoes": {
        "altitude_suitable_min_masl": 1500,
        "altitude_suitable_max_masl": 2700,
        "rainfall_mm_min": 800,
        "rainfall_mm_max": 1200,
        "yield_kg_per_acre_low": 5000,
        "yield_kg_per_acre_high": 12000,
        "planting_seasons": ["February-April", "July-September"],
        "maturity_days": 90,
        "input_cost_per_acre_low": 40000,
        "input_cost_per_acre_high": 70000,
        "market_price_kes_per_kg_low": 20,
        "market_price_kes_per_kg_high": 45,
    },
}

LIVESTOCK_SPECS = {
    "Dairy Cattle": {
        "optimal_farm_size_acres": 3,
        "animals_per_acre": 1.2,
        "daily_milk_production_liters": 8,
        "milk_price_kes_per_liter": 35,
        "daily_feed_cost_kes": 300,
        "healthcare_cost_monthly_kes": 2000,
        "acquisition_cost_kes": 45000,
    },
    "Poultry": {
        "optimal_farm_size_acres": 0.25,
        "animals_per_100_sqm": 100,
        "eggs_per_bird_monthly": 20,
        "egg_price_kes_per_dozen": 120,
        "daily_feed_cost_per_bird_kes": 5,
        "healthcare_cost_monthly_kes": 500,
        "acquisition_cost_per_bird_kes": 300,
    },
    "Goats": {
        "optimal_farm_size_acres": 0.5,
        "animals_per_acre": 3,
        "milk_production_liters_daily": 2,
        "milk_price_kes_per_liter": 40,
        "daily_feed_cost_kes": 80,
        "healthcare_cost_monthly_kes": 1000,
        "acquisition_cost_kes": 10000,
    },
}

KENYAN_COUNTIES_ALTITUDE = {
    "Nairobi": 1700, "Kisii": 1500, "Nakuru": 1900, "Kiambu": 1600,
    "Mombasa": 20, "Uasin Gishu": 2000, "Nyeri": 1750, "Kericho": 2000,
    "Kajiado": 1500, "Muranga": 1800, "Nyamira": 1500, "Bomet": 1950,
}


# ============================================================================
# SYNTHETIC DATA CLASSES
# ============================================================================

@dataclass
class SyntheticFarmer:
    """Synthetic farmer profile"""
    farmer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    county: str = ""
    years_experience: int = 0
    education_level: str = "primary"
    farm_size_acres: float = 2.5
    farm_scenario: str = "smallholder_mixed"
    household_size: int = 5
    contact_phone: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SyntheticCrop:
    """Synthetic crop production record"""
    farm_id: str = ""
    crop_name: str = ""
    area_cultivated_acres: float = 1.0
    planting_date: datetime = field(default_factory=datetime.now)
    maturity_days: int = 120
    current_growth_stage: str = "vegetative"
    expected_yield_kg: float = 500
    actual_yield_kg: Optional[float] = None
    input_cost_kes: float = 15000
    market_price_kes_per_kg: float = 25
    pest_pressure_score: float = 0.3
    disease_pressure_score: float = 0.2
    soil_health_score: float = 60


@dataclass
class SyntheticLivestock:
    """Synthetic livestock unit"""
    farm_id: str = ""
    livestock_type: str = ""
    head_count: int = 2
    production_type: str = "milk"
    daily_production_liters: float = 8.0
    daily_production_quantity: float = 20.0
    daily_feed_cost_kes: float = 300
    health_status: str = "healthy"
    last_health_check: datetime = field(default_factory=datetime.now)


@dataclass
class SyntheticExpense:
    """Synthetic farm expense"""
    farm_id: str = ""
    date: datetime = field(default_factory=datetime.now)
    category: str = ""
    description: str = ""
    amount_kes: float = 0
    notes: str = ""


@dataclass
class SyntheticIncome:
    """Synthetic farm income"""
    farm_id: str = ""
    date: datetime = field(default_factory=datetime.now)
    commodity: str = ""
    quantity_kg: float = 0
    unit_price_kes: float = 0
    total_kes: float = 0
    buyer_type: str = "market"
    notes: str = ""


# ============================================================================
# SYNTHETIC DATA GENERATOR
# ============================================================================

class SyntheticFarmDataGenerator:
    """
    Generate realistic Kenyan farm scenarios for training
    
    Scenarios:
    1. Subsistence - Basic survival, mixed crops, minimal inputs
    2. Smallholder Mixed - Crops + some livestock, moderate inputs
    3. Market-Oriented - Target driven, improved varieties, good inputs
    4. Livestock Focused - Dairy/poultry primary, supporting crops
    5. Horticulture - High-value vegetables, intensive inputs
    6. Diversified - Multiple enterprises, risk management focus
    
    Usage:
    ```python
    gen = SyntheticFarmDataGenerator(seed=42)
    
    # Generate single farm
    farm = gen.generate_complete_farm(FarmScenario.MARKET_ORIENTED)
    
    # Generate training dataset
    df = gen.generate_training_dataset(count=1000)
    ```
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_farmer(self, scenario: FarmScenario = FarmScenario.SMALLHOLDER_MIXED) -> SyntheticFarmer:
        """Generate synthetic farmer profile"""
        
        scenario_params = {
            FarmScenario.SUBSISTENCE: {
                "farm_size": (1.0, 2.0),
                "experience": (3, 8),
                "education": "primary"
            },
            FarmScenario.SMALLHOLDER_MIXED: {
                "farm_size": (2.0, 4.0),
                "experience": (5, 15),
                "education": "primary"
            },
            FarmScenario.MARKET_ORIENTED: {
                "farm_size": (3.0, 6.0),
                "experience": (8, 20),
                "education": "secondary"
            },
            FarmScenario.LIVESTOCK_FOCUSED: {
                "farm_size": (2.0, 5.0),
                "experience": (7, 18),
                "education": "secondary"
            },
            FarmScenario.HORTICULTURE: {
                "farm_size": (1.5, 4.0),
                "experience": (10, 25),
                "education": "secondary"
            },
            FarmScenario.DIVERSIFIED: {
                "farm_size": (4.0, 8.0),
                "experience": (12, 30),
                "education": "tertiary"
            }
        }
        
        params = scenario_params.get(scenario, scenario_params[FarmScenario.SMALLHOLDER_MIXED])
        
        farmer = SyntheticFarmer(
            name=f"Farmer_{random.randint(1000, 9999)}",
            county=random.choice([c.value for c in KenyanCounty]),
            farm_size_acres=np.random.uniform(*params["farm_size"]),
            years_experience=random.randint(*params["experience"]),
            farm_scenario=scenario.value,
            education_level=params["education"],
            household_size=random.randint(4, 10),
            contact_phone=f"+254{random.randint(700000000, 799999999)}"
        )
        
        return farmer
    
    def generate_crops(self, farm: SyntheticFarmer, count: int = 2) -> List[SyntheticCrop]:
        """Generate crop production records for farm"""
        
        crops = []
        
        # Select crops suitable for county altitude
        county_altitude = KENYAN_COUNTIES_ALTITUDE.get(farm.county, 1500)
        suitable_crops = [
            crop for crop, specs in CROP_SPECS.items()
            if specs["altitude_suitable_min_masl"] <= county_altitude <= specs["altitude_suitable_max_masl"]
        ]
        
        if not suitable_crops:
            suitable_crops = list(CROP_SPECS.keys())
        
        selected_crops = random.sample(suitable_crops, min(count, len(suitable_crops)))
        total_area = farm.farm_size_acres
        areas_per_crop = np.random.dirichlet(np.ones(len(selected_crops))) * total_area * 0.7
        
        for crop_name, area in zip(selected_crops, areas_per_crop):
            specs = CROP_SPECS[crop_name]
            
            base_yield = np.random.uniform(specs["yield_kg_per_acre_low"], specs["yield_kg_per_acre_high"])
            experience_multiplier = 0.8 + (farm.years_experience / 30) * 0.4
            expected_yield = base_yield * experience_multiplier
            
            pest_pressure = np.random.beta(2, 5)
            disease_pressure = np.random.beta(2, 5)
            yield_reduction = 1.0 - (pest_pressure * 0.3 + disease_pressure * 0.2)
            actual_yield = expected_yield * yield_reduction if random.random() > 0.3 else None
            
            crop = SyntheticCrop(
                farm_id=farm.farmer_id,
                crop_name=crop_name,
                area_cultivated_acres=area,
                maturity_days=specs["maturity_days"],
                expected_yield_kg=expected_yield,
                actual_yield_kg=actual_yield,
                input_cost_kes=np.random.uniform(
                    specs["input_cost_per_acre_low"],
                    specs["input_cost_per_acre_high"]
                ) * area,
                market_price_kes_per_kg=np.random.uniform(
                    specs["market_price_kes_per_kg_low"],
                    specs["market_price_kes_per_kg_high"]
                ),
                pest_pressure_score=float(pest_pressure),
                disease_pressure_score=float(disease_pressure),
                soil_health_score=np.random.uniform(40, 85)
            )
            
            crops.append(crop)
        
        return crops
    
    def generate_livestock(self, farm: SyntheticFarmer) -> List[SyntheticLivestock]:
        """Generate livestock records"""
        
        livestock_units = []
        
        livestock_probability = {
            FarmScenario.SUBSISTENCE: 0.3,
            FarmScenario.SMALLHOLDER_MIXED: 0.6,
            FarmScenario.MARKET_ORIENTED: 0.8,
            FarmScenario.LIVESTOCK_FOCUSED: 0.95,
            FarmScenario.HORTICULTURE: 0.4,
            FarmScenario.DIVERSIFIED: 0.9,
        }
        
        if random.random() > livestock_probability.get(FarmScenario(farm.farm_scenario), 0.5):
            return []
        
        livestock_to_keep = []
        
        if random.random() > 0.4:
            head_count = random.randint(2, 5) if farm.farm_scenario != FarmScenario.SUBSISTENCE.value else 1
            livestock_to_keep.append(("Dairy Cattle", head_count))
        
        if random.random() > 0.5:
            head_count = random.randint(10, 50)
            livestock_to_keep.append(("Poultry", head_count))
        
        if random.random() > 0.7:
            head_count = random.randint(3, 10)
            livestock_to_keep.append(("Goats", head_count))
        
        for livestock_type, head_count in livestock_to_keep:
            specs = LIVESTOCK_SPECS.get(livestock_type, {})
            
            production_liters = specs.get("daily_milk_production_liters", 0) * head_count
            
            unit = SyntheticLivestock(
                farm_id=farm.farmer_id,
                livestock_type=livestock_type,
                head_count=head_count,
                daily_production_liters=float(production_liters),
                daily_feed_cost_kes=specs.get("daily_feed_cost_kes", 200) * head_count,
                health_status=random.choice(["healthy", "fair", "needs_treatment"]),
            )
            
            livestock_units.append(unit)
        
        return livestock_units
    
    def generate_expenses(self, farm: SyntheticFarmer, months: int = 12) -> List[SyntheticExpense]:
        """Generate 12 months of expense records"""
        
        expenses = []
        
        base_monthly_expense = {
            FarmScenario.SUBSISTENCE.value: 25000,
            FarmScenario.SMALLHOLDER_MIXED.value: 40000,
            FarmScenario.MARKET_ORIENTED.value: 65000,
            FarmScenario.LIVESTOCK_FOCUSED.value: 60000,
            FarmScenario.HORTICULTURE.value: 75000,
            FarmScenario.DIVERSIFIED.value: 85000,
        }
        
        monthly_base = base_monthly_expense.get(farm.farm_scenario, 40000)
        seasonal_pattern = [1.5, 1.8, 1.6, 1.0, 0.8, 0.7, 0.8, 0.9, 1.0, 1.5, 1.8, 1.6]
        
        expense_categories = {
            "Seeds & Seedlings": (0.20, 0.25),
            "Fertilizer & Soil": (0.15, 0.20),
            "Pesticides & Fungicides": (0.08, 0.12),
            "Labor": (0.20, 0.25),
            "Water & Irrigation": (0.05, 0.10),
            "Transportation": (0.05, 0.08),
            "Tools & Equipment": (0.05, 0.10),
            "Veterinary & Feed": (0.10, 0.15),
            "Market/Cooperative Fees": (0.05, 0.08),
            "Other": (0.02, 0.05),
        }
        
        for month in range(months):
            seasonal_multiplier = seasonal_pattern[month % 12]
            monthly_total = monthly_base * seasonal_multiplier
            
            remaining = monthly_total
            categories_list = list(expense_categories.items())
            random.shuffle(categories_list)
            
            for i, (category, (percent_low, percent_high)) in enumerate(categories_list):
                if i == len(categories_list) - 1:
                    amount = remaining
                else:
                    percent = np.random.uniform(percent_low, percent_high)
                    amount = monthly_total * percent
                    remaining -= amount
                
                expense_date = datetime.now() - timedelta(days=30 * (months - month))
                
                expense = SyntheticExpense(
                    farm_id=farm.farmer_id,
                    date=expense_date + timedelta(days=random.randint(0, 28)),
                    category=category,
                    description=f"{category} - Monthly allocation",
                    amount_kes=amount
                )
                
                expenses.append(expense)
        
        return expenses
    
    def generate_income(self, farm: SyntheticFarmer, crops: List[SyntheticCrop], 
                       livestock: List[SyntheticLivestock], months: int = 12) -> List[SyntheticIncome]:
        """Generate income records"""
        
        income_records = []
        
        for crop in crops:
            if crop.actual_yield_kg and crop.actual_yield_kg > 0:
                harvest_date = crop.planting_date + timedelta(days=crop.maturity_days)
                quantity_per_sale = crop.actual_yield_kg / random.randint(2, 4)
                
                for sale_week in range(random.randint(2, 4)):
                    sale_date = harvest_date + timedelta(days=sale_week * 7 + random.randint(0, 6))
                    actual_price = crop.market_price_kes_per_kg * np.random.uniform(0.9, 1.1)
                    
                    income = SyntheticIncome(
                        farm_id=farm.farmer_id,
                        date=sale_date,
                        commodity=crop.crop_name,
                        quantity_kg=quantity_per_sale,
                        unit_price_kes=actual_price,
                        total_kes=quantity_per_sale * actual_price,
                        buyer_type=random.choice(["market", "cooperative", "retailer"])
                    )
                    
                    income_records.append(income)
        
        for livestock_unit in livestock:
            for month in range(months):
                sale_date = datetime.now() - timedelta(days=30 * (months - month)) + timedelta(days=random.randint(0, 28))
                
                if livestock_unit.livestock_type == "Dairy Cattle":
                    monthly_production = livestock_unit.daily_production_liters * 30
                    price_per_liter = LIVESTOCK_SPECS["Dairy Cattle"]["milk_price_kes_per_liter"] * np.random.uniform(0.95, 1.05)
                    
                    income = SyntheticIncome(
                        farm_id=farm.farmer_id,
                        date=sale_date,
                        commodity=f"{livestock_unit.livestock_type} - Milk",
                        quantity_kg=monthly_production,
                        unit_price_kes=price_per_liter,
                        total_kes=monthly_production * price_per_liter / 30,
                        buyer_type="cooperative"
                    )
                    income_records.append(income)
                
                elif livestock_unit.livestock_type == "Poultry":
                    for week in range(4):
                        weekly_eggs = livestock_unit.head_count * 140 / 4
                        dozens = weekly_eggs / 12
                        price_per_dozen = LIVESTOCK_SPECS["Poultry"]["egg_price_kes_per_dozen"]
                        
                        income = SyntheticIncome(
                            farm_id=farm.farmer_id,
                            date=sale_date + timedelta(days=week * 7),
                            commodity="Eggs",
                            quantity_kg=weekly_eggs,
                            unit_price_kes=price_per_dozen,
                            total_kes=dozens * price_per_dozen,
                            buyer_type=random.choice(["market", "retailer"])
                        )
                        income_records.append(income)
        
        return income_records
    
    def generate_complete_farm(self, scenario: FarmScenario = FarmScenario.SMALLHOLDER_MIXED,
                              months_history: int = 12) -> Dict[str, Any]:
        """Generate complete synthetic farm dataset"""
        
        farmer = self.generate_farmer(scenario)
        crops = self.generate_crops(farmer, count=random.randint(1, 3))
        livestock = self.generate_livestock(farmer)
        expenses = self.generate_expenses(farmer, months=months_history)
        income = self.generate_income(farmer, crops, livestock, months=months_history)
        
        return {
            "farmer": asdict(farmer),
            "crops": [asdict(c) for c in crops],
            "livestock": [asdict(l) for l in livestock],
            "expenses": [asdict(e) for e in expenses],
            "income": [asdict(i) for i in income],
        }
    
    def generate_training_dataset(self, count: int = 100, 
                                 scenarios: Optional[List[FarmScenario]] = None) -> pd.DataFrame:
        """Generate training dataset with multiple farms"""
        
        if scenarios is None:
            scenarios = list(FarmScenario)
        
        farms_data = []
        logger.info(f"📊 Generating {count} synthetic farms for training")
        
        for i in range(count):
            scenario = random.choice(scenarios)
            farm_data = self.generate_complete_farm(scenario, months_history=12)
            
            # Compute features
            farmer_dict = farm_data["farmer"]
            
            total_crop_area = sum(c["area_cultivated_acres"] for c in farm_data["crops"])
            total_crop_input_cost = sum(c["input_cost_kes"] for c in farm_data["crops"])
            total_crop_expected_revenue = sum(
                c["expected_yield_kg"] * c["market_price_kes_per_kg"] for c in farm_data["crops"]
            )
            
            total_livestock_head = sum(l["head_count"] for l in farm_data["livestock"])
            total_livestock_daily_cost = sum(l["daily_feed_cost_kes"] for l in farm_data["livestock"])
            
            total_12m_expense = sum(e["amount_kes"] for e in farm_data["expenses"])
            total_12m_income = sum(i["total_kes"] for i in farm_data["income"])
            
            avg_pest_pressure = np.mean([c["pest_pressure_score"] for c in farm_data["crops"]]) if farm_data["crops"] else 0
            avg_disease_pressure = np.mean([c["disease_pressure_score"] for c in farm_data["crops"]]) if farm_data["crops"] else 0
            avg_soil_health = np.mean([c["soil_health_score"] for c in farm_data["crops"]]) if farm_data["crops"] else 50
            
            row = {
                "farm_id": farmer_dict["farmer_id"],
                "farmer_name": farmer_dict["name"],
                "county": farmer_dict["county"],
                "years_experience": farmer_dict["years_experience"],
                "education_level": farmer_dict["education_level"],
                "farm_size_acres": farmer_dict["farm_size_acres"],
                "scenario": scenario.value,
                "household_size": farmer_dict["household_size"],
                
                # Crop metrics
                "total_cultivated_acres": total_crop_area,
                "crop_count": len(farm_data["crops"]),
                "total_crop_input_cost_kes": total_crop_input_cost,
                "total_crop_expected_revenue_kes": total_crop_expected_revenue,
                "avg_pest_pressure": float(avg_pest_pressure),
                "avg_disease_pressure": float(avg_disease_pressure),
                "avg_soil_health_score": float(avg_soil_health),
                
                # Livestock metrics
                "livestock_count": total_livestock_head,
                "livestock_units": len(farm_data["livestock"]),
                "daily_livestock_cost_kes": total_livestock_daily_cost,
                
                # Financial metrics
                "total_12m_expense_kes": total_12m_expense,
                "total_12m_income_kes": total_12m_income,
                "net_12m_kes": total_12m_income - total_12m_expense,
                "monthly_avg_expense_kes": total_12m_expense / 12,
                "monthly_avg_income_kes": total_12m_income / 12,
                "expense_to_income_ratio": total_12m_expense / total_12m_income if total_12m_income > 0 else 999,
                
                # Risk & health scores
                "financial_risk_score": np.clip(total_12m_expense / total_12m_income if total_12m_income > 0 else 1.0, 0, 1),
                "production_risk_score": float((avg_pest_pressure + avg_disease_pressure) / 2),
                "diversification_index": (len(farm_data["crops"]) + len(farm_data["livestock"])) / 4,
            }
            
            farms_data.append(row)
        
        logger.info(f"✅ Generated {count} farms, ready for training")
        return pd.DataFrame(farms_data)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_synthetic_generator(seed: Optional[int] = None) -> SyntheticFarmDataGenerator:
    """Factory function for generator"""
    return SyntheticFarmDataGenerator(seed=seed)


if __name__ == "__main__":
    # Example usage
    gen = SyntheticFarmDataGenerator(seed=42)
    
    print("🌾 Generating single farm...")
    farm = gen.generate_complete_farm(FarmScenario.MARKET_ORIENTED)
    print(f"   Farmer: {farm['farmer']['name']}")
    print(f"   County: {farm['farmer']['county']}")
    print(f"   Crops: {[c['crop_name'] for c in farm['crops']]}")
    print(f"   Livestock: {[l['livestock_type'] for l in farm['livestock']]}")
    
    print("\n📊 Generating training dataset (100 farms)...")
    df = gen.generate_training_dataset(count=100)
    print(f"   Shape: {df.shape}")
    print(f"   Scenarios: {df['scenario'].unique()}")
    print(f"\n   Sample farm:")
    print(df.iloc[0])

    

# Define scenarios
SCENARIOS = {
    FarmScenario.SMALLHOLDER_MAIZE: ScenarioTemplate(
        name="Smallholder Maize Farmer",
        farm_size_acres=(2.0, 3.0),
        crops=["maize", "beans"],
        crop_areas_acres={"maize": (1.5, 2.0), "beans": (0.5, 1.0)},
        livestock=[],
        livestock_counts={},
        monthly_revenue_kes=(80000, 150000),
        monthly_expense_kes=(30000, 60000),
        yield_per_acre_kg={
            "maize": (400, 600),
            "beans": (300, 500)
        },
        workers={},
        risk_profile={
            "pest_pressure": 0.6,
            "disease_pressure": 0.4,
            "animal_health": 0.0,
            "market_volatility": 0.3
        }
    ),
    
    FarmScenario.VEGETABLE_FARMER: ScenarioTemplate(
        name="Vegetable Farmer",
        farm_size_acres=(1.5, 2.0),
        crops=["tomatoes", "kale", "spinach"],
        crop_areas_acres={
            "tomatoes": (0.5, 0.75),
            "kale": (0.4, 0.6),
            "spinach": (0.3, 0.5)
        },
        livestock=["chickens"],
        livestock_counts={"chickens": (20, 50)},
        monthly_revenue_kes=(150000, 300000),
        monthly_expense_kes=(70000, 120000),
        yield_per_acre_kg={
            "tomatoes": (8000, 12000),
            "kale": (5000, 8000),
            "spinach": (4000, 6000)
        },
        workers={"farm_hand": 1, "supervisor": 0},
        risk_profile={
            "pest_pressure": 0.8,
            "disease_pressure": 0.7,
            "animal_health": 0.3,
            "market_volatility": 0.6
        }
    ),
    
    FarmScenario.DAIRY_FARMER: ScenarioTemplate(
        name="Dairy Farmer",
        farm_size_acres=(3.0, 5.0),
        crops=["fodder", "maize"],
        crop_areas_acres={
            "fodder": (1.5, 2.0),
            "maize": (1.0, 1.5)
        },
        livestock=["dairy_cattle"],
        livestock_counts={"dairy_cattle": (3, 5)},
        monthly_revenue_kes=(200000, 400000),
        monthly_expense_kes=(120000, 200000),
        yield_per_acre_kg={
            "fodder": (6000, 8000),
            "maize": (400, 600)
        },
        workers={"farm_hand": 2},
        risk_profile={
            "pest_pressure": 0.4,
            "disease_pressure": 0.5,
            "animal_health": 0.7,
            "market_volatility": 0.2
        }
    ),
    
    FarmScenario.DIVERSIFIED: ScenarioTemplate(
        name="Diversified Agro-Dealer",
        farm_size_acres=(8.0, 12.0),
        crops=["maize", "beans", "tomatoes", "kale", "banana"],
        crop_areas_acres={
            "maize": (3, 4),
            "beans": (1.5, 2),
            "tomatoes": (1, 1.5),
            "kale": (0.8, 1),
            "banana": (1.5, 2)
        },
        livestock=["dairy_cattle", "chickens"],
        livestock_counts={
            "dairy_cattle": (8, 12),
            "chickens": (100, 200)
        },
        monthly_revenue_kes=(400000, 800000),
        monthly_expense_kes=(200000, 350000),
        yield_per_acre_kg={
            "maize": (500, 700),
            "beans": (400, 600),
            "tomatoes": (9000, 12000),
            "kale": (6000, 8000),
            "banana": (8000, 12000)
        },
        workers={
            "farm_manager": 1,
            "supervisor": 1,
            "farm_hand": 4
        },
        risk_profile={
            "pest_pressure": 0.4,
            "disease_pressure": 0.3,
            "animal_health": 0.4,
            "market_volatility": 0.2
        }
    )
}


# ============================================================================
# SYNTHETIC DATA GENERATOR
# ============================================================================

class SyntheticFarmDataGenerator:
    """
    Generates realistic synthetic farm data for testing and training.
    
    Usage:
    ```python
    generator = SyntheticFarmDataGenerator()
    
    # Generate single farm profile
    farm_data = generator.generate_farm(
        scenario=FarmScenario.VEGETABLE_FARMER,
        months=12
    )
    
    # Generate training dataset (1000 farms)
    training_data = generator.generate_training_set(
        num_farms=1000,
        scenario_dist={
            FarmScenario.SMALLHOLDER_MAIZE: 0.5,
            FarmScenario.VEGETABLE_FARMER: 0.25,
            FarmScenario.DAIRY_FARMER: 0.15,
            FarmScenario.DIVERSIFIED: 0.1
        }
    )
    ```
    """
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            np.random.seed(seed)
        self.logger = logging.getLogger(__name__)
    
    def generate_farm(
        self,
        scenario: FarmScenario,
        months: int = 12,
        farm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate synthetic farm data for specified scenario.
        
        Args:
            scenario: Farm scenario template
            months: Months of historical data to generate
            farm_id: Custom farm ID (generated if None)
            
        Returns: Complete farm profile dict
        """
        
        if farm_id is None:
            farm_id = f"synthetic_{scenario.value}_{np.random.randint(10000, 99999)}"
        
        template = SCENARIOS[scenario]
        
        logger.info(f"🌱 Generating synthetic farm: {farm_id} ({template.name})")
        
        # Generate farm base
        farm_base = self._generate_farm_base(farm_id, template)
        
        # Generate transactions
        transactions = self._generate_transactions(farm_base, template, months)
        
        # Generate crops
        crops = self._generate_crops(farm_id, template, months)
        
        # Generate livestock
        livestock = self._generate_livestock(farm_id, template, months)
        
        # Generate workers
        workers = self._generate_workers(farm_id, template)
        
        # Generate incidents (pests, disease, health)
        incidents = self._generate_incidents(farm_id, template, months)
        
        return {
            "farm_id": farm_id,
            "scenario": scenario.value,
            "farm_base": farm_base,
            "transactions": transactions,
            "crops": crops,
            "livestock": livestock,
            "workers": workers,
            "incidents": incidents,
            "generated_at": datetime.now().isoformat(),
            "months": months
        }
    
    def _generate_farm_base(self, farm_id: str, template: ScenarioTemplate) -> Dict:
        """Generate farm base information"""
        return {
            "id": farm_id,
            "name": f"Farm {farm_id[-5:]}",
            "county": np.random.choice(["Kiambu", "Muranga", "Kisii", "Nakuru", "Nairobi"]),
            "farm_type": template.name,
            "total_area_acres": np.random.uniform(*template.farm_size_acres),
            "status": "active",
            "user_id": f"user_{farm_id[-5:]}",
            "created_at": (datetime.now() - timedelta(days=365)).isoformat(),
            "years_farming": np.random.randint(3, 15),
            "training_hours": np.random.randint(0, 100),
            "advisory_engagement_index": np.random.uniform(0.2, 1.0)
        }
    
    def _generate_transactions(
        self,
        farm_base: Dict,
        template: ScenarioTemplate,
        months: int
    ) -> Dict[str, List]:
        """Generate income and expense transactions"""
        
        start_date = datetime.now() - timedelta(days=30*months)
        
        expenses = []
        income = []
        
        for month in range(months):
            month_date = start_date + timedelta(days=30*month)
            
            # Generate expenses
            monthly_expense = np.random.uniform(*template.monthly_expense_kes)
            
            # Distribute across categories
            expense_categories = {
                "seeds/inputs": 0.35,
                "fertilizer": 0.25,
                "pesticides": 0.15,
                "labor": 0.15,
                "other": 0.10
            }
            
            for category, pct in expense_categories.items():
                amount = monthly_expense * pct
                expenses.append({
                    "expense_date": month_date.isoformat(),
                    "category": category,
                    "amount_kes": round(amount, 2),
                    "description": f"Monthly {category}"
                })
            
            # Generate income
            monthly_income = np.random.uniform(*template.monthly_revenue_kes)
            
            # Distribute across crops/livestock
            if template.crops:
                per_crop = monthly_income / len(template.crops)
                for crop in template.crops:
                    amount = per_crop * np.random.uniform(0.8, 1.2)
                    income.append({
                        "revenue_date": month_date.isoformat(),
                        "source": crop,
                        "amount_kes": round(amount, 2),
                        "description": f"Sale of {crop}"
                    })
            
            if template.livestock:
                per_animal = monthly_income / len(template.livestock)
                for animal in template.livestock:
                    amount = per_animal * np.random.uniform(0.8, 1.2)
                    income.append({
                        "revenue_date": month_date.isoformat(),
                        "source": animal,
                        "amount_kes": round(amount, 2),
                        "description": f"Sale/production from {animal}"
                    })
        
        return {
            "expenses": expenses,
            "income": income
        }
    
    def _generate_crops(
        self,
        farm_id: str,
        template: ScenarioTemplate,
        months: int
    ) -> List[Dict]:
        """Generate crop production data"""
        
        crops = []
        start_date = datetime.now() - timedelta(days=30*months)
        
        for crop_name in template.crops:
            area_acres = np.random.uniform(*template.crop_areas_acres[crop_name])
            yield_kg_acre = np.random.uniform(*template.yield_per_acre_kg[crop_name])
            
            crops.append({
                "id": f"crop_{farm_id}_{crop_name}_{np.random.randint(1000, 9999)}",
                "farm_id": farm_id,
                "crop_name": crop_name,
                "crop_type": "vegetable" if crop_name in ["tomatoes", "kale"] else "cereal",
                "area_acres": round(area_acres, 2),
                "expected_yield_kg": round(yield_kg_acre * area_acres, 1),
                "actual_yield_kg": round(yield_kg_acre * area_acres * np.random.uniform(0.8, 1.1), 1),
                "total_input_cost_kes": round(
                    area_acres * yield_kg_acre * 5,  # ~5 KES per kg input cost
                    2
                ),
                "planting_date": (start_date + timedelta(days=np.random.randint(0, 60))).isoformat(),
                "expected_harvest_date": (start_date + timedelta(days=np.random.randint(90, 150))).isoformat(),
                "cultivation_status": np.random.choice(["growing", "harvesting", "harvested"]),
                "pest_pressure_level": np.random.choice(["low", "medium", "high"]) if np.random.random() < template.risk_profile["pest_pressure"] else "low",
                "disease_pressure_level": np.random.choice(["low", "medium", "high"]) if np.random.random() < template.risk_profile["disease_pressure"] else "low",
            })
        
        return crops
    
    def _generate_livestock(
        self,
        farm_id: str,
        template: ScenarioTemplate,
        months: int
    ) -> List[Dict]:
        """Generate livestock data"""
        
        livestock = []
        
        for animal_type, (min_count, max_count) in template.livestock_counts.items():
            count = np.random.randint(int(min_count), int(max_count))
            
            livestock.append({
                "id": f"livestock_{farm_id}_{animal_type}_{np.random.randint(1000, 9999)}",
                "farm_id": farm_id,
                "livestock_name": animal_type,
                "livestock_type": animal_type,
                "current_head_count": count,
                "status": "active",
                "health_status": np.random.choice(["healthy", "sick", "critical"]) if np.random.random() < template.risk_profile["animal_health"] else "healthy",
                "productivity_status": "high" if np.random.random() > 0.3 else "low",
                "mortality_rate_percent": np.random.uniform(0, 5),
                "milk_production_liters_day": round(np.random.uniform(5, 15), 1) if animal_type == "dairy_cattle" else 0,
                "egg_production_per_day": int(np.random.uniform(10, 50)) if animal_type == "chickens" else 0,
            })
        
        return livestock
    
    def _generate_workers(self, farm_id: str, template: ScenarioTemplate) -> List[Dict]:
        """Generate worker data"""
        
        workers = []
        
        for role, count in template.workers.items():
            for i in range(count):
                workers.append({
                    "worker_id": f"worker_{farm_id}_{role}_{i}",
                    "farm_id": farm_id,
                    "role": role,
                    "assignment_status": "active",
                    "performance_rating": np.random.uniform(2.5, 5.0),
                    "salary_per_month_kes": {
                        "farm_manager": 25000,
                        "supervisor": 15000,
                        "farm_hand": 8000
                    }.get(role, 8000),
                    "hours_worked_per_week": np.random.uniform(35, 50),
                    "attendance_rate": np.random.uniform(0.85, 0.99) * 100,
                })
        
        return workers
    
    def _generate_incidents(
        self,
        farm_id: str,
        template: ScenarioTemplate,
        months: int
    ) -> List[Dict]:
        """Generate health incidents (pests, disease, health issues)"""
        
        incidents = []
        start_date = datetime.now() - timedelta(days=30*months)
        
        # Pest occurrences
        if template.risk_profile["pest_pressure"] > 0.3:
            for _ in range(int(template.risk_profile["pest_pressure"] * months)):
                incidents.append({
                    "type": "pest_occurrence",
                    "date": (start_date + timedelta(days=np.random.randint(0, 30*months))).isoformat(),
                    "severity": "high",
                    "estimate_loss_percent": np.random.uniform(5, 25),
                    "treatment_applied": bool(np.random.random() > 0.3),
                    "treatment_efficiency": np.random.uniform(0.6, 0.95) if np.random.random() > 0.3 else None
                })
        
        # Disease occurrences
        if template.risk_profile["disease_pressure"] > 0.3:
            for _ in range(int(template.risk_profile["disease_pressure"] * months)):
                incidents.append({
                    "type": "disease_occurrence",
                    "date": (start_date + timedelta(days=np.random.randint(0, 30*months))).isoformat(),
                    "severity": "medium",
                    "estimate_loss_percent": np.random.uniform(3, 20),
                    "treatment_applied": bool(np.random.random() > 0.2),
                    "treatment_efficiency": np.random.uniform(0.5, 0.9) if np.random.random() > 0.2 else None
                })
        
        return incidents
    
    def generate_training_set(
        self,
        num_farms: int = 100,
        scenario_dist: Optional[Dict[FarmScenario, float]] = None,
        months: int = 12
    ) -> pd.DataFrame:
        """
        Generate large training dataset with multiple farms.
        
        Args:
            num_farms: Number of synthetic farms
            scenario_dist: Distribution of scenarios {scenario: probability}
            months: Months of history per farm
            
        Returns: DataFrame with farm profiles and features (pre-engineered)
        """
        
        if scenario_dist is None:
            scenario_dist = {
                FarmScenario.SMALLHOLDER_MAIZE: 0.4,
                FarmScenario.VEGETABLE_FARMER: 0.35,
                FarmScenario.DAIRY_FARMER: 0.15,
                FarmScenario.DIVERSIFIED: 0.1
            }
        
        logger.info(f"📊 Generating training dataset: {num_farms} synthetic farms")
        
        farms_data = []
        
        for i in range(num_farms):
            # Sample scenario based on distribution
            scenario = np.random.choice(
                list(scenario_dist.keys()),
                p=list(scenario_dist.values())
            )
            
            farm_profile = self.generate_farm(scenario, months)
            farms_data.append(farm_profile)
        
        # Convert to DataFrame format ready for FeatureEngineer
        # This would be flattened/normalized in real implementation
        df = pd.DataFrame([
            {
                "farm_id": farm["farm_id"],
                "scenario": farm["scenario"],
                # Features would be engineered from the full profile
            }
            for farm in farms_data
        ])
        
        logger.info(f"✅ Generated dataset: {len(df)} farms, {months} months history each")
        
        return df


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

_generator: Optional[SyntheticFarmDataGenerator] = None

def get_synthetic_generator() -> SyntheticFarmDataGenerator:
    """Get or create SyntheticFarmDataGenerator singleton"""
    global _generator
    if _generator is None:
        _generator = SyntheticFarmDataGenerator(seed=42)
    return _generator
