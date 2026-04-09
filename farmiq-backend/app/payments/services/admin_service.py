"""
Admin Dashboard & Management Service - Phase 4
Analytics, user management, quota administration, and reporting

Author: FarmIQ Backend Team
Date: March 2026
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from fastapi import HTTPException, Depends
import logging

logger = logging.getLogger(__name__)


class AdminDashboardService:
    """
    Admin dashboard for FarmIQ system monitoring and management
    Provides analytics, user management, and quota administration
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    # ===================== SYSTEM ANALYTICS =====================
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """
        Get high-level system overview for admin dashboard
        
        Returns:
            System stats including users, transactions, tokens
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get counts
                users = await conn.fetchval("SELECT COUNT(*) FROM user_wallets WHERE wallet_status = 'ACTIVE'")
                transactions = await conn.fetchval("SELECT COUNT(*) FROM mpesa_transactions WHERE payment_status = 'COMPLETED'")
                tokens_minted = await conn.fetchval("SELECT COALESCE(SUM(tokens_purchased), 0) FROM mpesa_transactions WHERE payment_status = 'COMPLETED'")
                revenue = await conn.fetchval("SELECT COALESCE(SUM(amount_kes), 0) FROM mpesa_transactions WHERE payment_status = 'COMPLETED'")
                
                # Get today's stats
                today_transactions = await conn.fetchval(
                    "SELECT COUNT(*) FROM mpesa_transactions WHERE DATE(created_at) = CURRENT_DATE AND payment_status = 'COMPLETED'"
                )
                today_revenue = await conn.fetchval(
                    "SELECT COALESCE(SUM(amount_kes), 0) FROM mpesa_transactions WHERE DATE(created_at) = CURRENT_DATE AND payment_status = 'COMPLETED'"
                )
                
                return {
                    'total_users': users,
                    'total_transactions': transactions,
                    'total_tokens_minted': float(tokens_minted),
                    'total_revenue_kes': float(revenue),
                    'today_transactions': today_transactions,
                    'today_revenue_kes': float(today_revenue),
                    'timestamp': datetime.now().isoformat(),
                }
                
        except Exception as e:
            logger.error(f"Error fetching system overview: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_user_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get user analytics for the period
        
        Args:
            days: Number of days to analyze
        
        Returns:
            User growth, engagement, and retention metrics
        """
        try:
            async with self.db_pool.acquire() as conn:
                start_date = datetime.now() - timedelta(days=days)
                
                # Daily new users
                new_users_daily = await conn.fetch(
                    """
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM user_wallets
                    WHERE created_at >= $1
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """,
                    start_date
                )
                
                # Active users (made purchases)
                active_users = await conn.fetchval(
                    """
                    SELECT COUNT(DISTINCT farmiq_id) FROM mpesa_transactions
                    WHERE created_at >= $1 AND payment_status = 'COMPLETED'
                    """,
                    start_date
                )
                
                # User tiers
                users_by_balance = await conn.fetch(
                    """
                    SELECT
                        CASE
                            WHEN fiq_token_balance < 10 THEN 'Low Balance'
                            WHEN fiq_token_balance < 100 THEN 'Medium Balance'
                            WHEN fiq_token_balance < 500 THEN 'Good Balance'
                            ELSE 'Premium Balance'
                        END as tier,
                        COUNT(*) as count
                    FROM user_wallets
                    GROUP BY tier
                    """
                )
                
                return {
                    'new_users_daily': [{'date': str(row['date']), 'count': row['count']} for row in new_users_daily],
                    'active_users': active_users,
                    'users_by_balance_tier': {row['tier']: row['count'] for row in users_by_balance},
                    'period_days': days,
                }
                
        except Exception as e:
            logger.error(f"Error fetching user analytics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_payment_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get payment analytics
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Payment trends, conversion rates, revenue metrics
        """
        try:
            async with self.db_pool.acquire() as conn:
                start_date = datetime.now() - timedelta(days=days)
                
                # Daily revenue
                daily_revenue = await conn.fetch(
                    """
                    SELECT DATE(created_at) as date, 
                           COUNT(*) as transactions,
                           SUM(amount_kes) as revenue,
                           SUM(tokens_purchased) as tokens
                    FROM mpesa_transactions
                    WHERE created_at >= $1 AND payment_status = 'COMPLETED'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """,
                    start_date
                )
                
                # Payment success rate
                total = await conn.fetchval(
                    "SELECT COUNT(*) FROM mpesa_transactions WHERE created_at >= $1",
                    start_date
                )
                completed = await conn.fetchval(
                    "SELECT COUNT(*) FROM mpesa_transactions WHERE created_at >= $1 AND payment_status = 'COMPLETED'",
                    start_date
                )
                success_rate = (completed / total * 100) if total > 0 else 0
                
                # Failed payments reason
                failures = await conn.fetch(
                    """
                    SELECT mpesa_result_description, COUNT(*) as count
                    FROM mpesa_transactions
                    WHERE created_at >= $1 AND payment_status != 'COMPLETED'
                    GROUP BY mpesa_result_description
                    order BY count DESC
                    LIMIT 5
                    """,
                    start_date
                )
                
                return {
                    'daily_revenue': [{
                        'date': str(row['date']),
                        'transactions': row['transactions'],
                        'revenue_kes': float(row['revenue']) if row['revenue'] else 0,
                        'tokens_minted': float(row['tokens']) if row['tokens'] else 0,
                    } for row in daily_revenue],
                    'success_rate_percent': round(success_rate, 2),
                    'total_transactions': total,
                    'completed_transactions': completed,
                    'top_failure_reasons': [{
                        'reason': row['mpesa_result_description'],
                        'count': row['count']
                    } for row in failures],
                }
                
        except Exception as e:
            logger.error(f"Error fetching payment analytics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===================== USER QUOTA MANAGEMENT =====================
    
    async def adjust_user_quota(
        self,
        farmiq_id: str,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Admin endpoint to adjust user quota limits
        
        Args:
            farmiq_id: FarmIQ user ID
            daily_budget: New daily quota
            monthly_budget: New monthly quota
        
        Returns:
            Updated quota details
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get or create quota record
                quota = await conn.fetchrow(
                    "SELECT * FROM user_quotas WHERE farmiq_id = $1",
                    farmiq_id
                )
                
                if quota:
                    # Update existing
                    updates = []
                    params = [farmiq_id]
                    param_count = 2
                    
                    if daily_budget is not None:
                        updates.append(f"daily_budget = ${param_count}")
                        params.append(daily_budget)
                        param_count += 1
                    
                    if monthly_budget is not None:
                        updates.append(f"monthly_budget = ${param_count}")
                        params.append(monthly_budget)
                        param_count += 1
                    
                    if updates:
                        query = f"UPDATE user_quotas SET {', '.join(updates)}, updated_at = NOW() WHERE farmiq_id = $1 RETURNING *"
                        quota = await conn.fetchrow(query, *params)
                else:
                    # Create new
                    quota = await conn.fetchrow(
                        """
                        INSERT INTO user_quotas (farmiq_id, daily_budget, monthly_budget)
                        VALUES ($1, $2, $3)
                        RETURNING *
                        """,
                        farmiq_id,
                        daily_budget or 100.0,
                        monthly_budget or 2000.0
                    )
                
                logger.info(f"✅ Updated quotas for {farmiq_id}: daily={quota['daily_budget']}, monthly={quota['monthly_budget']}")
                
                return {
                    'farmiq_id': farmiq_id,
                    'daily_budget': float(quota['daily_budget']),
                    'monthly_budget': float(quota['monthly_budget']),
                    'updated_at': quota['updated_at'].isoformat(),
                }
                
        except Exception as e:
            logger.error(f"Error adjusting user quota: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_users_exceeding_quota(self) -> List[Dict[str, Any]]:
        """
        List users who have exceeded their daily quota today
        
        Returns:
            List of users with usage details
        """
        try:
            async with self.db_pool.acquire() as conn:
                exceeding = await conn.fetch(
                    """
                    SELECT
                        w.farmiq_id,
                        w.fiq_token_balance,
                        q.daily_budget,
                        COALESCE(SUM(CASE WHEN DATE(a.created_at) = CURRENT_DATE THEN a.tokens_deducted ELSE 0 END), 0) as today_usage
                    FROM user_wallets w
                    LEFT JOIN user_quotas q ON q.farmiq_id = w.farmiq_id
                    LEFT JOIN ai_usage_log a ON a.farmiq_id = w.farmiq_id
                    GROUP BY w.farmiq_id, w.fiq_token_balance, q.daily_budget
                    HAVING COALESCE(SUM(CASE WHEN DATE(a.created_at) = CURRENT_DATE THEN a.tokens_deducted ELSE 0 END), 0) >= COALESCE(q.daily_budget, 100)
                    """
                )
                
                return [{
                    'farmiq_id': row['farmiq_id'],
                    'balance': float(row['fiq_token_balance']),
                    'daily_budget': float(row['daily_budget']),
                    'today_usage': float(row['today_usage']),
                    'exceeded_percent': (row['today_usage'] / row['daily_budget'] * 100) if row['daily_budget'] > 0 else 0,
                } for row in exceeding]
                
        except Exception as e:
            logger.error(f"Error listing exceeding users: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===================== REPORTING =====================
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive daily report for stakeholders
        
        Returns:
            Daily summary with all key metrics
        """
        try:
            overview = await self.get_system_overview()
            payments = await self.get_payment_analytics(days=1)
            
            report = {
                'date': datetime.now().date().isoformat(),
                'system_overview': overview,
                'payment_stats': payments,
                'top_users': await self._get_top_spenders(limit=10),
                'generated_at': datetime.now().isoformat(),
            }
            
            logger.info(f"✅ Daily report generated")
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_top_spenders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top token spenders"""
        try:
            async with self.db_pool.acquire() as conn:
                top = await conn.fetch(
                    """
                    SELECT farmiq_id, COUNT(*) as purchases, SUM(tokens_purchased) as total_tokens
                    FROM mpesa_transactions
                    WHERE payment_status = 'COMPLETED'
                    GROUP BY farmiq_id
                    ORDER BY total_tokens DESC
                    LIMIT $1
                    """,
                    limit
                )
                
                return [{
                    'farmiq_id': row['farmiq_id'],
                    'purchases': row['purchases'],
                    'total_tokens': float(row['total_tokens']),
                } for row in top]
                
        except Exception as e:
            logger.error(f"Error getting top spenders: {e}")
            return []
