"""
Market Domain Entity
Represents market conditions and opportunities for farm products
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID
from app.shared import BaseEntity, validate_range, validate_not_empty


class MarketTiming(str, Enum):
    """Market timing recommendations"""
    SELL_NOW = "sell_now"
    HOLD = "hold"
    WAIT = "wait"
    BUY = "buy"  # For inputs


class MarketOpportunity(str, Enum):
    """Types of market opportunities"""
    PRICE_PEAK = "price_peak"
    NEW_BUYER = "new_buyer"
    EXPANSION = "expansion"
    DIVERSIFICATION = "diversification"
    CONTRACT = "contract"


@dataclass
class Market(BaseEntity):
    """
    Market domain entity
    Represents market conditions and pricing intelligence
    """
    farm_id: UUID = None
    user_id: str = ""
    product: str = ""  # What's being tracked (maize, tomato, fertilizer, etc)
    current_market_price: float = 0.0  # In KES
    price_trend: float = 0.0  # -1 to 1 (declining to rising)
    price_volatility: float = 0.0  # 0-1 (stability of prices)
    price_forecast_30d: float = 0.0  # Predicted price in 30 days
    price_forecast_confidence: float = 0.5  # 0-1 confidence in forecast
    demand_level: float = 0.5  # 0-1 current demand
    demand_trend: float = 0.0  # -1 to 1 (declining to rising)
    supply_level: float = 0.5  # 0-1 current supply
    buyer_concentration: float = 0.0  # 0-1 (how concentrated are buyers)
    num_active_buyers: int = 0
    num_potential_buyers: int = 0
    avg_price_last_year: Optional[float] = None
    seasonal_patterns: Dict[str, float] = field(default_factory=dict)  # month -> avg price
    market_timing_recommendation: MarketTiming = MarketTiming.HOLD
    identified_opportunities: List[MarketOpportunity] = field(default_factory=list)
    competitive_products: List[Dict[str, Any]] = field(default_factory=list)  # {name, price, quality}
    distribution_channels: List[str] = field(default_factory=list)
    quality_premium_available: bool = False
    estimated_quality_premium_percent: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate market data"""
        validate_not_empty(self.product, "product")
        validate_range(self.price_trend, -1, 1, "price_trend")
        validate_range(self.price_volatility, 0, 1, "price_volatility")
        validate_range(self.price_forecast_confidence, 0, 1, "price_forecast_confidence")
        validate_range(self.demand_level, 0, 1, "demand_level")
        validate_range(self.demand_trend, -1, 1, "demand_trend")
        validate_range(self.supply_level, 0, 1, "supply_level")
        validate_range(self.buyer_concentration, 0, 1, "buyer_concentration")
    
    def get_price_trend_direction(self) -> str:
        """Get human-readable price trend"""
        if self.price_trend > 0.3:
            return "📈 Rising"
        elif self.price_trend > 0.1:
            return "↗️  Slightly up"
        elif self.price_trend < -0.3:
            return "📉 Falling"
        elif self.price_trend < -0.1:
            return "↘️  Slightly down"
        else:
            return "→ Stable"
    
    def get_demand_trend_direction(self) -> str:
        """Get human-readable demand trend"""
        if self.demand_trend > 0.3:
            return "📈 Increasing demand"
        elif self.demand_trend > 0.1:
            return "↗️  Slightly increasing"
        elif self.demand_trend < -0.3:
            return "📉 Decreasing demand"
        else:
            return "→ Stable demand"
    
    def calculate_price_opportunity_score(self) -> float:
        """
        Calculate opportunity score for selling
        Considers: current price vs history, trend, forecast, demand
        Returns 0-1 where 1 is best selling opportunity
        """
        if self.avg_price_last_year is None or self.avg_price_last_year == 0:
            return 0.5
        
        # Price percentile relative to last year
        price_percentile = min(self.current_market_price / self.avg_price_last_year, 2.0) / 2.0
        
        # Demand factor (high demand is good)
        demand_factor = self.demand_level
        
        # Trend factor (upward trend is good)
        trend_factor = (self.price_trend + 1) / 2  # Convert -1..1 to 0..1
        
        # Forecast factor (if price expected to go higher, wait)
        forecast_factor = 0.5 if self.price_forecast_30d < self.current_market_price else 1.0
        
        # Weighted calculation
        opportunity = (
            price_percentile * 0.3 +
            demand_factor * 0.3 +
            trend_factor * 0.2 +
            forecast_factor * 0.2
        )
        
        return min(opportunity, 1.0)
    
    def get_market_recommendation(self) -> str:
        """Get detailed market recommendation"""
        opportunity_score = self.calculate_price_opportunity_score()
        
        if self.market_timing_recommendation == MarketTiming.SELL_NOW:
            return f"✅ Good time to sell at {self.current_market_price} KES (opportunity score: {opportunity_score:.0%})"
        elif self.market_timing_recommendation == MarketTiming.WAIT:
            return f"⏳ Wait for better prices. Forecast: {self.price_forecast_30d} KES in 30 days"
        elif self.market_timing_recommendation == MarketTiming.HOLD:
            return f"➡️  Hold stock. Price stable at {self.current_market_price} KES"
        else:
            return "ℹ️  Market conditions neutral"
    
    def get_supply_demand_ratio(self) -> float:
        """Calculate supply-demand ratio"""
        if self.supply_level == 0:
            return 0
        return self.supply_level / max(self.demand_level, 0.1)
    
    def is_buyer_concentration_high(self) -> bool:
        """Check if market is concentrated (few buyers)"""
        return self.buyer_concentration > 0.7
    
    def get_buyer_diversity_recommendation(self) -> str:
        """Get recommendation for buyer diversification"""
        if self.is_buyer_concentration_high():
            return "⚠️  Highly concentrated buyer market. Diversify buyers to reduce risk."
        elif self.buyer_concentration > 0.5:
            return "ℹ️  Moderate buyer concentration. Consider expanding buyer base."
        else:
            return "✓ Good buyer diversity. Your negotiating power is strong."
    
    def get_quality_premium_value(self, base_quantity: float) -> float:
        """Calculate additional revenue from quality premium"""
        if not self.quality_premium_available:
            return 0
        return base_quantity * self.current_market_price * (self.estimated_quality_premium_percent / 100)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'farm_id': str(self.farm_id),
            'user_id': self.user_id,
            'product': self.product,
            'price_trend_direction': self.get_price_trend_direction(),
            'demand_trend_direction': self.get_demand_trend_direction(),
            'opportunity_score': self.calculate_price_opportunity_score(),
            'recommendation': self.get_market_recommendation(),
            'buyer_diversity_status': self.get_buyer_diversity_recommendation(),
            'supply_demand_ratio': self.get_supply_demand_ratio(),
        })
        return base_dict
