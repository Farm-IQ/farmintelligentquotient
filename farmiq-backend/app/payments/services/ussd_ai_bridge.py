"""
USSD AI Services Bridge
Connects FarmGrow, FarmScore, FarmSuite to USSD for AI-powered farming advice
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class USSDFarmGrowBridge:
    """
    Bridge between USSD and FarmGrow AI service
    Provides crop recommendations via simple text menu
    """

    def __init__(self, farmgrow_service=None):
        self.farmgrow_service = farmgrow_service

    async def get_crop_recommendations_menu(self) -> str:
        """Display crop recommendation options"""
        menu = """
FarmGrow - AI Crop Recommendations
============================
1. Get Today's Recommendation
2. Best Crops This Season
3. Market Price Info
4. Pest/Disease Alerts
5. Weather Forecast
0. Back

Enter choice:
"""
        return menu

    async def get_today_recommendation(self, farmiq_id: str, farm_id: str) -> str:
        """Get AI recommendation for today"""
        try:
            if not self.farmgrow_service:
                return """FarmGrow Data:
Weather: Sunny, 28°C
Soil: Well-drained loam
Recommendation: Water vegetables at 6am
Best time: Early morning
Status: Optimal conditions

Reply 1 for more details"""

            # Call FarmGrow service
            recommendation = await self.farmgrow_service.get_daily_recommendation(farmiq_id, farm_id)

            if recommendation:
                response = f"""Today's Crop Recommendation
============================
{recommendation.get('recommendation', 'N/A')}

Weather: {recommendation.get('weather_condition', 'N/A')}
Temperature: {recommendation.get('temperature', 'N/A')}°C

Action: {recommendation.get('action', 'N/A')}

Reply 1 for more
Reply 0 to go back
"""
                return response
            else:
                return "No recommendations available.\n0. Back"
        except Exception as e:
            logger.error(f"Error getting recommendation: {str(e)}")
            return f"Error: {str(e)[:50]}\n0. Back"

    async def get_best_crops(self, county: str, season: str = "current") -> str:
        """Get best crops for county and season"""
        try:
            best_crops = {
                "Kakamega": ["Maize", "Beans", "Banana", "Cassava"],
                "Kiambu": ["Avocado", "Coffee", "Cabbage", "Potatoes"],
                "Nakuru": ["Maize", "Wheat", "Pyrethrum", "Carrots"],
                "Uasin Gishu": ["Maize", "Beans", "Sorghum", "Millet"],
                "Nairobi": ["Vegetables", "Herbs", "Flowers", "Fruits"],
            }

            crops = best_crops.get(county, ["Maize", "Beans", "Vegetables"])

            response = f"""Best Crops for {county}
============================
"""
            for i, crop in enumerate(crops, 1):
                response += f"{i}. {crop}\n"

            response += """\nPrices (Avg):
Maize: 50 KES/kg
Beans: 120 KES/kg
Vegetables: 80 KES/kg

Reply number for info
0. Back"""
            return response
        except Exception as e:
            logger.error(f"Error getting best crops: {str(e)}")
            return f"Error: {str(e)[:50]}\n0. Back"

    async def get_market_prices(self, crop: str) -> str:
        """Get current market prices for crop"""
        try:
            # Sample market data
            market_data = {
                "Maize": {"current": 50, "low": 45, "high": 65, "trend": "up"},
                "Beans": {"current": 120, "low": 110, "high": 150, "trend": "stable"},
                "Potatoes": {"current": 40, "low": 35, "high": 55, "trend": "down"},
                "Vegetables": {"current": 80, "low": 60, "high": 100, "trend": "up"},
            }

            data = market_data.get(crop, {"current": 0, "low": 0, "high": 0, "trend": "unknown"})

            response = f"""Market Price - {crop}
============================
Current: {data['current']} KES/kg
Low: {data['low']} KES/kg
High: {data['high']} KES/kg
Trend: {data['trend']}

Updated: Today
Best to: {'SELL' if data['trend'] == 'up' else 'HOLD' if data['trend'] == 'stable' else 'WAIT'}

1. More info
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting market prices: {str(e)}")
            return f"Error\n0. Back"

    async def get_pest_alerts(self, farm_id: str, county: str) -> str:
        """Get current pest/disease alerts"""
        try:
            alerts = {
                "Kakamega": [
                    "Fall Armyworm detected (HIGH ALERT)",
                    "Maize streak virus spreading",
                ],
                "Kiambu": [
                    "Coffee leaf rust warning",
                    "Potato blight risk HIGH",
                ],
                "Nakuru": [
                    "Armyworm in wheat fields",
                    "Normal conditions",
                ],
            }

            current_alerts = alerts.get(county, ["No major alerts"])

            response = """Pest & Disease Alerts
============================
"""
            for i, alert in enumerate(current_alerts[:3], 1):
                response += f"{i}. {alert}\n"

            response += """\n1. Control measures
2. Report pest
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            return f"Error\n0. Back"

    async def get_weather_forecast(self, farm_id: str) -> str:
        """Get 7-day weather forecast"""
        try:
            forecast = {
                "today": {"temp": "28°C", "condition": "Sunny", "rain": "0mm"},
                "tomorrow": {"temp": "27°C", "condition": "Partly cloudy", "rain": "0mm"},
                "7day_avg": {"rain": "15mm", "condition": "Mostly sunny"},
            }

            response = """7-Day Weather Forecast
============================
Today: {today[condition]}, {today[temp]}
Tomorrow: {tomorrow[condition]}, {tomorrow[temp]}

Expected Rain: {7day_avg[rain]} (next 7 days)

Farming Advice:
✓ Good for planting
✓ Water conservation recommended
✗ Spraying not advised today

1. Detailed forecast
0. Back
""".format(
                today=forecast["today"],
                tomorrow=forecast["tomorrow"],
                **forecast,
            )
            return response
        except Exception as e:
            logger.error(f"Error getting forecast: {str(e)}")
            return f"Error\n0. Back"


class USSDFarmScoreBridge:
    """
    Bridge between USSD and FarmScore credit scoring
    Provides credit status and loan options via USSD
    """

    def __init__(self, farmscore_service=None):
        self.farmscore_service = farmscore_service

    async def get_credit_menu(self) -> str:
        """Display credit options"""
        menu = """
FarmScore - Credit & Loans
============================
1. Check Credit Score
2. Loan Options
3. Apply for Loan
4. My Loans
5. Repayment Info
0. Back

Enter choice:
"""
        return menu

    async def get_credit_score(self, farmiq_id: str) -> str:
        """Get user's credit score"""
        try:
            # Sample credit score format for USSD
            response = f"""Your FarmScore
============================
Credit Score: 72/100

Rating: GOOD ✓
Status: Ready for loans

Available:
- Micro loan: 5,000 KES
- Standard loan: 50,000 KES
- Seasonal loan: 25,000 KES

1. Apply for loan
2. More details
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting credit score: {str(e)}")
            return f"Error\n0. Back"

    async def get_loan_options(self, farmiq_id: str, credit_score: int) -> str:
        """Get available loan options based on credit"""
        try:
            # Determine eligible loans based on credit score
            loans = []
            if credit_score >= 60:
                loans = [
                    ("Micro Loan", "5,000-10,000 KES", "1 month", "3% interest"),
                    ("Seasonal Loan", "25,000-50,000 KES", "4 months", "4% interest"),
                    ("Standard Loan", "50,000-100,000 KES", "6 months", "5% interest"),
                ]
            elif credit_score >= 50:
                loans = [
                    ("Micro Loan", "5,000 KES", "1 month", "4% interest"),
                    ("Seasonal Loan", "25,000 KES", "4 months", "5% interest"),
                ]
            else:
                loans = [("Micro Loan", "5,000 KES", "1 month", "5% interest")]

            response = """Available Loan Options
============================
"""
            for i, (name, amount, term, rate) in enumerate(loans, 1):
                response += f"{i}. {name}\n   {amount} | {term} | {rate}\n"

            response += """\n1. Apply for loan
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting loan options: {str(e)}")
            return f"Error\n0. Back"

    async def apply_for_loan(self, farmiq_id: str, loan_type: str, amount: int) -> str:
        """Start loan application"""
        try:
            response = f"""Loan Application
============================
Type: {loan_type}
Amount: {amount} KES
Term: 4 months

Documents needed:
1. Farm photo
2. Land ID/cert
3. Farmer reg cert

Continue application?
1. Yes
2. Cancel
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error in loan application: {str(e)}")
            return f"Error\n0. Back"

    async def get_my_loans(self, farmiq_id: str) -> str:
        """Display user's active loans"""
        try:
            response = """My Loans
============================
1. Loan #001
   Amount: 25,000 KES
   Status: Active
   Due: 2026-04-15

2. Loan #002
   Amount: 50,000 KES
   Status: Pending
   Due: 2026-05-20

1. Loan details
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting loans: {str(e)}")
            return f"Error\n0. Back"


class USSDFarmSuiteBridge:
    """
    Bridge between USSD and FarmSuite analytics
    Provides farm performance analytics via USSD
    """

    def __init__(self, farmsuite_service=None):
        self.farmsuite_service = farmsuite_service

    async def get_analytics_menu(self) -> str:
        """Display analytics options"""
        menu = """
FarmSuite - Farm Analytics
============================
1. Farm Summary
2. Production Stats
3. Financial Report
4. Pest/Disease Log
5. Yield Forecast
0. Back

Enter choice:
"""
        return menu

    async def get_farm_summary(self, farmiq_id: str) -> str:
        """Get summary of all user farms"""
        try:
            response = """Farm Summary
============================
Total Farms: 2

Farm #1: Main Plot
Size: 2 acres
Crop: Maize
Status: Growing well
Next Action: Water (2 days)

Farm #2: Vegetable Plot
Size: 0.5 acres
Crop: Vegetables
Status: Ready for harvest
Next Action: Pick now

1. Details
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting farm summary: {str(e)}")
            return f"Error\n0. Back"

    async def get_production_stats(self, farm_id: str) -> str:
        """Get production statistics"""
        try:
            response = """Production Stats
============================
Crop: Maize
Planted: 100 days ago
Expected Yield: 80 bags
Current Status: Growing

Growth: 80% ✓
Health: Good
Soil: Optimal
Water: Adequate

1. Detailed report
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return f"Error\n0. Back"

    async def get_financial_report(self, farmiq_id: str) -> str:
        """Get financial performance"""
        try:
            response = """Financial Report
============================
This Season:
Revenue: 45,000 KES
Expenses: 15,000 KES
Profit: 30,000 KES
ROI: 200%

Last 12 Months:
Total Revenue: 180,000 KES
Average Profit: 25,000 KES

1. Export report
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting financial report: {str(e)}")
            return f"Error\n0. Back"


class USSDPaymentBridge:
    """
    Bridge between USSD and Payment services
    Provides token purchase and balance check
    """

    def __init__(self, mpesa_service=None):
        self.mpesa_service = mpesa_service

    async def get_payment_menu(self) -> str:
        """Display payment options"""
        menu = """
FarmIQ Tokens
============================
1. Buy Tokens
2. Check Balance
3. Payment History
4. Referral Rewards
5. Wallet Settings
0. Back

Enter choice:
"""
        return menu

    async def get_buy_tokens_menu(self) -> str:
        """Display token packages"""
        menu = """
Token Packages
============================
1. Starter - 100 FIQ = 1,000 KES
   +10 bonus FIQ (+10%)

2. Small - 500 FIQ = 5,000 KES
   +50 bonus FIQ (+10%)

3. Medium - 1000 FIQ = 10,000 KES
   +200 bonus FIQ (+20%)

4. Large - 2000 FIQ = 20,000 KES
   +500 bonus FIQ (+25%)

Enter choice:
"""
        return menu

    async def get_balance(self, farmiq_id: str) -> str:
        """Get token balance"""
        try:
            response = """Your Balance
============================
FIQ Tokens: 250

Usage:
Today: 10 tokens
This Month: 120 tokens

Limit:
Daily: 100 tokens
Monthly: 2000 tokens

History:
1. View transactions
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return f"Error\n0. Back"

    async def show_referral_rewards(self, farmiq_id: str) -> str:
        """Show referral program"""
        try:
            response = """Referral Rewards
============================
Refer a farmer: +50 FIQ bonus

Your Referrals:
1. Bonus from 2 farmers: 100 FIQ

Total Referral Earnings:
100 FIQ = 1,000 KES

How it works:
Share your code: FARM89234
on WhatsApp or SMS

1. Share code
2. View stats
0. Back
"""
            return response
        except Exception as e:
            logger.error(f"Error getting referral: {str(e)}")
            return f"Error\n0. Back"


class USSDMainMenu:
    """
    Main USSD menu router combining all services
    """

    def __init__(self, farmgrow: USSDFarmGrowBridge, farmscore: USSDFarmScoreBridge, farmsuite: USSDFarmSuiteBridge, payment: USSDPaymentBridge):
        self.farmgrow = farmgrow
        self.farmscore = farmscore
        self.farmsuite = farmsuite
        self.payment = payment

    async def get_main_menu(self, user_role: str = "farmer") -> str:
        """Get main authenticated menu"""
        menu = f"""
FarmIQ - {user_role.title()}
============================
1. 🌾 FarmGrow (AI Crops)
2. 💰 FarmScore (Credit)
3. 📊 FarmSuite (Analytics)
4. 🎫 Buy Tokens
5. 👤 Profile
6. ℹ️ Help & Support
0. Exit

Enter choice:
"""
        return menu

    async def handle_main_menu_selection(self, choice: str) -> Tuple[str, Optional[str]]:
        """
        Route main menu selection
        Returns: (response_text, next_service)
        """
        routes = {
            "1": ("farmgrow", await self.farmgrow.get_crop_recommendations_menu()),
            "2": ("farmscore", await self.farmscore.get_credit_menu()),
            "3": ("farmsuite", await self.farmsuite.get_analytics_menu()),
            "4": ("payment", await self.payment.get_buy_tokens_menu()),
            "5": ("profile", "Profile Settings\n0. Back"),
            "6": ("help", """Help & Support
============================
1. FAQ
2. Contact us
3. Report bug
0. Back
"""),
            "0": ("exit", "Thank you for using FarmIQ!\nGoodbye."),
        }

        if choice in routes:
            service, response = routes[choice]
            return response, service
        else:
            menu = await self.get_main_menu()
            return f"Invalid choice.\n{menu}", None
