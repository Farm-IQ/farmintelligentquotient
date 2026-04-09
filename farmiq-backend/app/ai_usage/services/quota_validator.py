"""
Shared Quota Validator - Phase 3
Validates daily and monthly quotas across all AI systems
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from core.database import get_database_repository

logger = logging.getLogger(__name__)


class QuotaValidator:
    """
    Validates user quotas across FarmGrow, FarmScore, and FarmSuite
    
    Quotas:
    - Daily budget: Max tokens per day
    - Monthly budget: Max tokens per month
    """

    def __init__(self):
        """Initialize quota validator"""
        self.db = None  # Database set dynamically in async methods

    async def check_quota(
        self,
        farmiq_id: str,
        tokens_required: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Check if user has sufficient quota for next operation
        
        Args:
            farmiq_id: User's FarmIQ ID
            tokens_required: Tokens needed for operation (default 1.0)
            
        Returns:
            {
                'has_quota': bool,
                'reason': str,
                'daily_remaining': float,
                'monthly_remaining': float,
                'daily_limit': float,
                'monthly_limit': float,
                'error': str (if any)
            }
        """
        try:
            # Get user wallet and quota
            wallet_data = await self._get_wallet_quota(farmiq_id)
            if not wallet_data:
                return {
                    'has_quota': False,
                    'reason': 'User wallet not found',
                    'error': f'No wallet configured for {farmiq_id}',
                }
            
            daily_budget = wallet_data.get('daily_budget', float('inf'))
            monthly_budget = wallet_data.get('monthly_budget', float('inf'))
            fiq_balance = wallet_data.get('fiq_token_balance', 0)
            
            # Check sufficient balance
            if fiq_balance < tokens_required:
                return {
                    'has_quota': False,
                    'reason': f'Insufficient balance: {fiq_balance} FIQ',
                    'daily_remaining': daily_budget,
                    'monthly_remaining': monthly_budget,
                    'daily_limit': daily_budget,
                    'monthly_limit': monthly_budget,
                    'error': f'Need {tokens_required} FIQ, have {fiq_balance}',
                }
            
            # Check daily quota
            daily_used = await self._get_daily_usage(farmiq_id)
            daily_remaining = daily_budget - daily_used
            
            if daily_remaining < tokens_required:
                return {
                    'has_quota': False,
                    'reason': f'Daily quota exceeded: {daily_used}/{daily_budget}',
                    'daily_remaining': max(0, daily_remaining),
                    'monthly_remaining': monthly_budget,
                    'daily_limit': daily_budget,
                    'monthly_limit': monthly_budget,
                    'error': f'Daily quota exceeded',
                }
            
            # Check monthly quota
            monthly_used = await self._get_monthly_usage(farmiq_id)
            monthly_remaining = monthly_budget - monthly_used
            
            if monthly_remaining < tokens_required:
                return {
                    'has_quota': False,
                    'reason': f'Monthly quota exceeded: {monthly_used}/{monthly_budget}',
                    'daily_remaining': daily_remaining,
                    'monthly_remaining': max(0, monthly_remaining),
                    'daily_limit': daily_budget,
                    'monthly_limit': monthly_budget,
                    'error': f'Monthly quota exceeded',
                }
            
            # User has sufficient quota
            return {
                'has_quota': True,
                'reason': 'Quota available',
                'daily_remaining': daily_remaining,
                'monthly_remaining': monthly_remaining,
                'daily_limit': daily_budget,
                'monthly_limit': monthly_budget,
            }
            
        except Exception as e:
            logger.error(f"Quota check error: {e}")
            return {
                'has_quota': False,
                'reason': 'Quota check failed',
                'error': str(e),
            }

    async def _get_wallet_quota(self, farmiq_id: str) -> Optional[Dict[str, Any]]:
        """Get user's wallet and quota configuration"""
        try:
            # Query user_wallets table
            query = """
            SELECT 
                fiq_token_balance,
                user_quotas.daily_budget,
                user_quotas.monthly_budget
            FROM user_wallets
            LEFT JOIN user_quotas ON user_wallets.id = user_quotas.wallet_id
            WHERE user_wallets.farmiq_id = %s AND user_wallets.wallet_status = 'ACTIVE'
            LIMIT 1
            """
            
            # Execute query through database session
            from sqlalchemy import text
            result = await self.db.execute(text(query), {'farmiq_id': farmiq_id})
            row = result.fetchone()
            
            if row:
                return {
                    'fiq_token_balance': float(row[0]) if row[0] else 0,
                    'daily_budget': float(row[1]) if row[1] else 100.0,  # Default 100 FIQ/day
                    'monthly_budget': float(row[2]) if row[2] else 2000.0,  # Default 2000 FIQ/month
                }
            return None
            
        except Exception as e:
            logger.error(f"Error fetching wallet quota: {e}")
            return None

    async def _get_daily_usage(self, farmiq_id: str) -> float:
        """Get total tokens used today"""
        try:
            today = datetime.now().date()
            query = """
            SELECT COALESCE(SUM(tokens_deducted), 0) as total
            FROM ai_usage_log
            WHERE farmiq_id = %s 
            AND DATE(created_at) = %s 
            AND success = TRUE
            """
            
            from sqlalchemy import text
            result = await self.db.execute(
                text(query), 
                {'farmiq_id': farmiq_id, 'today': today}
            )
            row = result.fetchone()
            
            return float(row[0]) if row and row[0] else 0.0
            
        except Exception as e:
            logger.error(f"Error fetching daily usage: {e}")
            return 0.0

    async def _get_monthly_usage(self, farmiq_id: str) -> float:
        """Get total tokens used this month"""
        try:
            now = datetime.now()
            month_start = now.replace(day=1)
            
            query = """
            SELECT COALESCE(SUM(tokens_deducted), 0) as total
            FROM ai_usage_log
            WHERE farmiq_id = %s 
            AND created_at >= %s 
            AND success = TRUE
            """
            
            from sqlalchemy import text
            result = await self.db.execute(
                text(query), 
                {'farmiq_id': farmiq_id, 'month_start': month_start}
            )
            row = result.fetchone()
            
            return float(row[0]) if row and row[0] else 0.0
            
        except Exception as e:
            logger.error(f"Error fetching monthly usage: {e}")
            return 0.0

    async def update_quotas(
        self,
        farmiq_id: str,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Update user's quota limits
        
        Args:
            farmiq_id: User's FarmIQ ID
            daily_budget: New daily quota (if updating)
            monthly_budget: New monthly quota (if updating)
            
        Returns:
            Operation result
        """
        try:
            updates = {}
            if daily_budget is not None:
                updates['daily_budget'] = daily_budget
            if monthly_budget is not None:
                updates['monthly_budget'] = monthly_budget
            
            if not updates:
                return {'success': False, 'error': 'No updates provided'}
            
            # Update query
            from sqlalchemy import text, update
            stmt = update('user_quotas').where(
                user_quotas.c.farmiq_id == farmiq_id
            ).values(**updates)
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            logger.info(f"Updated quotas for {farmiq_id}: {updates}")
            
            return {
                'success': True,
                'updated': updates,
            }
            
        except Exception as e:
            logger.error(f"Error updating quotas: {e}")
            return {
                'success': False,
                'error': str(e),
            }
