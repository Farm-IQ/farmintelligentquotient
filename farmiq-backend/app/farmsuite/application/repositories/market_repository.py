"""
Market Repository
Data access layer for Market entities
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from app.shared import BaseRepository
from app.farmsuite.domain.entities.market import Market
from core.database import DatabaseRepository


class MarketRepository(BaseRepository[Market]):
    """
    Repository for Market entities
    Handles all Market CRUD operations and market intelligence queries
    """
    
    def __init__(self, db: DatabaseRepository):
        """
        Initialize MarketRepository
        
        Args:
            db: DatabaseRepository instance
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def get_market_by_product(
        self,
        farm_id: UUID,
        product: str
    ) -> Optional[Market]:
        """
        Get market intelligence for a specific product
        
        Args:
            farm_id: Farm identifier
            product: Product type
            
        Returns:
            Market entity or None
        """
        try:
            response = await self.db.select_many(
                'market_intelligence',
                {"farm_id": str(farm_id), "product": product},
                limit=1
            )
            return self._map_to_entity(response[0]) if response else None
        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}")
            return None
    
    async def get_farm_market_data(
        self,
        farm_id: UUID
    ) -> List[Market]:
        """
        Get all market intelligence for a farm's products
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of Market entities
        """
        try:
            response = await self.db.select_many(
                'market_intelligence',
                {"farm_id": str(farm_id)}
            )
            return [self._map_to_entity(row) for row in response]
        except Exception as e:
            self.logger.error(f"Error fetching farm market data: {e}")
            return []
    
    def get_highest_opportunity_products(
        self,
        farm_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get products ranked by market opportunity
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of products with opportunity scores
        """
        try:
            markets = self.get_farm_market_data(farm_id)
            
            products = [
                {
                    "product": m.product,
                    "opportunity_score": m.calculate_price_opportunity_score(),
                    "current_price": m.current_market_price,
                    "forecast_price": m.price_forecast_30d,
                    "demand_level": m.demand_level,
                }
                for m in markets
            ]
            
            # Sort by opportunity score descending
            return sorted(products, key=lambda x: x["opportunity_score"], reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting opportunity products: {e}")
            return []
    
    def get_markets_with_supply_shortage(
        self,
        farm_id: UUID
    ) -> List[Market]:
        """
        Get markets with high demand and low supply (high opportunity)
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of Market entities with supply shortage
        """
        try:
            markets = self.get_farm_market_data(farm_id)
            
            # Supply shortage = high demand and low supply
            shortages = [
                m for m in markets
                if m.get_supply_demand_ratio() < 0.8 and m.demand_level > 0.6
            ]
            
            return sorted(shortages, key=lambda m: m.demand_level, reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting shortage markets: {e}")
            return []
    
    def get_price_volatile_products(
        self,
        farm_id: UUID,
        threshold: float = 0.7
    ) -> List[Market]:
        """
        Get products with high price volatility (risk)
        
        Args:
            farm_id: Farm identifier
            threshold: Volatility threshold (0-1)
            
        Returns:
            List of volatile Market entities
        """
        try:
            markets = self.get_farm_market_data(farm_id)
            return [m for m in markets if m.price_volatility > threshold]
        except Exception as e:
            self.logger.error(f"Error getting volatile markets: {e}")
            return []
    
    def update_market_prices(
        self,
        market_id: UUID,
        current_price: float,
        forecast_price: float,
        price_trend: float
    ) -> Optional[Market]:
        """
        Update market price data
        
        Args:
            market_id: Market identifier
            current_price: Current market price
            forecast_price: Forecasted price
            price_trend: Price trend (-1 to 1)
            
        Returns:
            Updated Market entity
        """
        try:
            data = {
                "current_market_price": current_price,
                "price_forecast_30d": forecast_price,
                "price_trend": price_trend,
            }
            return self.update(market_id, data)
        except Exception as e:
            self.logger.error(f"Error updating market prices: {e}")
            return None
    
    def get_buyer_concentration_risk(
        self,
        farm_id: UUID
    ) -> Dict[str, Any]:
        """
        Analyze buyer concentration risk across all products
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            Dictionary with concentration risk analysis
        """
        try:
            markets = self.get_farm_market_data(farm_id)
            
            concentrated = [m for m in markets if m.is_buyer_concentration_high()]
            diversified = [m for m in markets if not m.is_buyer_concentration_high()]
            
            return {
                "total_products": len(markets),
                "concentrated_products": len(concentrated),
                "diversified_products": len(diversified),
                "high_risk_products": [m.product for m in concentrated],
                "recommendation": (
                    "HIGH RISK: Most products have concentrated buyers. "
                    "Expand buyer networks."
                    if len(concentrated) > len(diversified)
                    else "GOOD: Buyer base is well distributed."
                ),
            }
        except Exception as e:
            self.logger.error(f"Error analyzing buyer concentration: {e}")
            return {}
    
    def get_quality_premium_opportunities(
        self,
        farm_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Identify products with available quality premiums
        
        Args:
            farm_id: Farm identifier
            
        Returns:
            List of quality premium opportunities
        """
        try:
            markets = self.get_farm_market_data(farm_id)
            
            premiums = [
                {
                    "product": m.product,
                    "premium_percent": m.estimated_quality_premium_percent,
                    "base_price": m.current_market_price,
                    "premium_value_per_unit": (
                        m.current_market_price * m.estimated_quality_premium_percent / 100
                    ),
                }
                for m in markets
                if m.quality_premium_available
            ]
            
            return sorted(premiums, key=lambda x: x["premium_percent"], reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting quality premium opportunities: {e}")
            return []
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Market:
        """Map database row to Market entity"""
        if isinstance(data, Market):
            return data
        
        return Market(
            id=data.get("id"),
            farm_id=data.get("farm_id"),
            user_id=data.get("user_id"),
            product=data.get("product"),
            current_market_price=data.get("current_market_price", 0),
            price_trend=data.get("price_trend", 0),
            price_volatility=data.get("price_volatility", 0),
            price_forecast_30d=data.get("price_forecast_30d", 0),
            price_forecast_confidence=data.get("price_forecast_confidence", 0.5),
            demand_level=data.get("demand_level", 0),
            demand_trend=data.get("demand_trend", 0),
            supply_level=data.get("supply_level", 0),
            buyer_concentration=data.get("buyer_concentration", 0),
            num_active_buyers=data.get("num_active_buyers", 0),
            num_potential_buyers=data.get("num_potential_buyers", 0),
            avg_price_last_year=data.get("avg_price_last_year"),
            seasonal_patterns=data.get("seasonal_patterns", {}),
            identified_opportunities=data.get("identified_opportunities", []),
            competitive_products=data.get("competitive_products", []),
            distribution_channels=data.get("distribution_channels", []),
            quality_premium_available=data.get("quality_premium_available", False),
            estimated_quality_premium_percent=data.get("estimated_quality_premium_percent", 0),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
