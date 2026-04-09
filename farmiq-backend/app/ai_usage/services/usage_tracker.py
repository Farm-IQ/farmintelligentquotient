"""
AI Usage Tracker - Orchestrates HCS + HSCS + HTS + Supabase
Handles token deduction, audit logging, and quota management
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from core.database import get_database_repository

import structlog

logger = structlog.get_logger(__name__)


class AIUsageTracker:
    """
    Central service for tracking AI usage and managing tokens
    
    Flow:
    1. Check if user has sufficient balance
    2. Check if usage is within quota
    3. Execute smart contract to deduct tokens (HSCS)
    4. Log to Supabase (queryable)
    5. Log to HCS (immutable audit)
    6. Update wallet balance
    """

    def __init__(self):
        """Initialize tracker with internal DB-only usage tracking."""
        self.db = None  # Database set dynamically in async methods

    async def track_farmscore_usage(
        self,
        farmiq_id: str,
        user_id: str,
        hedera_wallet: str,
        credit_score: float,
        model_used: str,
        duration_ms: int = None,
    ) -> Dict[str, Any]:
        """Track FarmScore (credit scoring) usage - 1 FIQ deducted"""
        
        return await self._deduct_and_log(
            farmiq_id=farmiq_id,
            user_id=user_id,
            hedera_wallet=hedera_wallet,
            service_type='FARMSCORE',
            operation='get_credit_score',
            tokens=1.0,
            metadata={
                'credit_score': credit_score,
                'model': model_used,
            },
            response_summary=f"Credit score: {credit_score:.0f}",
            duration_ms=duration_ms,
        )

    async def track_farmgrow_usage(
        self,
        farmiq_id: str,
        user_id: str,
        hedera_wallet: str,
        query: str,
        response_text: str,
        duration_ms: int = None,
    ) -> Dict[str, Any]:
        """Track FarmGrow (RAG chatbot) usage - 1 FIQ deducted"""
        
        # Truncate response for summary
        response_summary = response_text[:100] if response_text else ""
        
        return await self._deduct_and_log(
            farmiq_id=farmiq_id,
            user_id=user_id,
            hedera_wallet=hedera_wallet,
            service_type='FARMGROW',
            operation='rag_query',
            tokens=1.0,
            metadata={
                'query_length': len(query),
                'response_length': len(response_text),
            },
            response_summary=response_summary,
            duration_ms=duration_ms,
        )

    async def track_farmsuite_usage(
        self,
        farmiq_id: str,
        user_id: str,
        hedera_wallet: str,
        prediction_type: str,  # 'yield', 'disease', 'price', 'roi'
        confidence: float,
        prediction_value: Any = None,
        duration_ms: int = None,
    ) -> Dict[str, Any]:
        """
        Track FarmSuite predictions - 1 FIQ deducted
        
        Args:
            prediction_type: 'yield', 'disease', 'price', 'roi'
            confidence: Model confidence/accuracy
            prediction_value: The predicted value (kg/ha, probability, KES, %)
            duration_ms: Time taken for prediction
        """
        
        service_map = {
            'yield': 'FARMSUITE_YIELD',
            'disease': 'FARMSUITE_DISEASE',
            'price': 'FARMSUITE_PRICE',
            'roi': 'FARMSUITE_ROI',
        }

        service_type = service_map.get(prediction_type, 'FARMSUITE_YIELD')
        
        return await self._deduct_and_log(
            farmiq_id=farmiq_id,
            user_id=user_id,
            hedera_wallet=hedera_wallet,
            service_type=service_type,
            operation=f'predict_{prediction_type}',
            tokens=1.0,
            metadata={
                'prediction_type': prediction_type,
                'confidence': confidence,
                'value': prediction_value,
            },
            response_summary=f"{prediction_type.title()}: {prediction_value}",
            duration_ms=duration_ms,
        )

    async def _deduct_and_log(
        self,
        farmiq_id: str,
        user_id: str,
        hedera_wallet: str,
        service_type: str,
        operation: str,
        tokens: float,
        metadata: Dict[str, Any] = None,
        response_summary: str = None,
        duration_ms: int = None,
    ) -> Dict[str, Any]:
        """
        Core token deduction and logging logic
        
        Flow:
        1. Validate user and wallet
        2. Check balance
        3. Check quota
        4. Execute smart contract (HSCS)
        5. Log to Supabase
        6. Log to HCS (immutable)
        7. Update balance
        
        Returns:
            {success, tokens_deducted, new_balance, errors}
        """
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"🔍 Tracking AI usage",
                farmiq_id=farmiq_id,
                service_type=service_type,
                operation=operation,
            )

            # ============ Step 1: Validate User ============
            user_wallet = await self.db.fetch_one("""
                SELECT * FROM user_wallets 
                WHERE farmiq_id = :farmiq_id AND user_id = :user_id
            """, {'farmiq_id': farmiq_id, 'user_id': user_id})

            if not user_wallet:
                error = f"User not found: {farmiq_id}"
                logger.error(error)
                return {
                    'success': False,
                    'error': error,
                    'tokens_deducted': 0,
                }

            if user_wallet['wallet_status'] != 'ACTIVE':
                error = f"Wallet suspended: {user_wallet['wallet_status']}"
                logger.warning(error, farmiq_id=farmiq_id)
                return {
                    'success': False,
                    'error': error,
                    'tokens_deducted': 0,
                }

            # ============ Step 2: Check Balance ============
            balance_before_fiq = float(user_wallet.get('fiq_token_balance', 0.0))

            if balance_before_fiq < tokens:
                error = f"Insufficient balance: {balance_before_fiq} < {tokens}"
                logger.warning(
                    error,
                    farmiq_id=farmiq_id,
                    balance=balance_before_fiq,
                    required=tokens,
                )
                
                # Log to compliance
                await self.db.execute("""
                    INSERT INTO compliance_logs (farmiq_id, event_type, severity, event_details)
                    VALUES (:farmiq_id, 'insufficient_balance', 'WARNING', :details)
                """, {
                    'farmiq_id': farmiq_id,
                    'details': json.dumps({
                        'service': service_type,
                        'required': tokens,
                        'available': balance_before_fiq,
                    }),
                })
                
                return {
                    'success': False,
                    'error': error,
                    'tokens_deducted': 0,
                    'balance': balance_before_fiq,
                }

            # ============ Step 3: Check Quota ============
            quota = await self.db.fetch_one("""
                SELECT * FROM service_quotas 
                WHERE farmiq_id = :farmiq_id AND quota_enabled = true
            """, {'farmiq_id': farmiq_id})

            if quota:
                daily_remaining = quota.get('daily_fiq_remaining', float('inf'))
                monthly_remaining = quota.get('monthly_fiq_remaining', float('inf'))
                
                if daily_remaining < tokens:
                    error = f"Daily quota exceeded"
                    logger.warning(error, farmiq_id=farmiq_id)
                    
                    await self.db.execute("""
                        INSERT INTO compliance_logs (farmiq_id, event_type, severity, event_details)
                        VALUES (:farmiq_id, 'quota_exceeded', 'WARNING', :details)
                    """, {
                        'farmiq_id': farmiq_id,
                        'details': json.dumps({
                            'quota_type': 'daily',
                            'remaining': daily_remaining,
                            'requested': tokens,
                        }),
                    })
                    
                    return {
                        'success': False,
                        'error': error,
                        'tokens_deducted': 0,
                    }

            # ============ Step 4: Deduct tokens locally ============
            hedera_tx_hash = None

            balance_before_fiq = float(user_wallet.get('fiq_token_balance', 0.0))
            balance_after_fiq = balance_before_fiq - tokens

            if balance_after_fiq < 0:
                error = f"Insufficient balance after deduction: {balance_before_fiq} < {tokens}"
                logger.warning(error, farmiq_id=farmiq_id)
                return {
                    'success': False,
                    'error': error,
                    'tokens_deducted': 0,
                }

            await self.db.execute("""
                UPDATE user_wallets
                SET fiq_token_balance = :new_balance,
                    updated_at = NOW()
                WHERE farmiq_id = :farmiq_id
            """, {
                'new_balance': balance_after_fiq,
                'farmiq_id': farmiq_id,
            })

            # Keep one local transaction identifier for audit
            local_tx_id = f"local-deduct-{farmiq_id}-{int(datetime.utcnow().timestamp())}"

            # ============ Step 5: Log deduction to AI usage log ============
            logger.info(f"📝 Logging internal usage record...")

            
            usage_log = await self.db.execute("""
                INSERT INTO ai_usage_log (
                    farmiq_id, user_id, role, service_type, operation,
                    tokens_deducted, user_balance_before, user_balance_after,
                    hedera_tx_hash, request_metadata, response_summary,
                    success, duration_ms
                )
                VALUES (
                    :farmiq_id, :user_id, :role, :service_type, :operation,
                    :tokens, :balance_before, :balance_after,
                    :tx_hash, :metadata::jsonb, :summary,
                    true, :duration
                )
                RETURNING id
            """, {
                'farmiq_id': farmiq_id,
                'user_id': user_id,
                'role': user_wallet.get('role'),
                'service_type': service_type,
                'operation': operation,
                'tokens': tokens,
                'balance_before': balance_before_fiq,
                'balance_after': balance_after_fiq,
                'tx_hash': hedera_tx_hash,
                'metadata': json.dumps(metadata or {}),
                'summary': response_summary,
                'duration': duration_ms,
            })

            # ============ Step 6: Record Token Transaction ============
            await self.db.execute("""
                INSERT INTO token_transactions (
                    farmiq_id, transaction_type,
                    amount_fiq, hedera_tx_id, status,
                    related_service, related_operation, metadata
                ) VALUES (
                    :farmiq_id, 'DEDUCTION',
                    :amount, :tx_id, 'CONFIRMED',
                    :service, :operation, :metadata::jsonb
                )
            """, {
                'farmiq_id': farmiq_id,
                'amount': tokens,
                'tx_id': local_tx_id,
                'service': service_type,
                'operation': operation,
                'metadata': json.dumps({'source': 'internal_deduction'}),
            })

            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            logger.info(
                f"✅ Usage tracked successfully",
                farmiq_id=farmiq_id,
                service_type=service_type,
                tokens_deducted=tokens,
                new_balance=balance_after_fiq,
                duration_ms=elapsed_ms,
            )

            return {
                'success': True,
                'tokens_deducted': tokens,
                'balance_before': balance_before_fiq,
                'balance_after': balance_after_fiq,
                'tx_id': local_tx_id,
                'duration_ms': elapsed_ms,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"❌ Usage tracking failed",
                farmiq_id=farmiq_id,
                service=service_type,
                error=error_msg,
            )

            # Log failed attempt to Supabase
            try:
                await self.db.execute("""
                    INSERT INTO ai_usage_log (
                        farmiq_id, user_id, service_type, operation,
                        tokens_deducted, error_message, success
                    )
                    VALUES (
                        :farmiq_id, :user_id, :service_type, :operation,
                        :tokens, :error, false
                    )
                """, {
                    'farmiq_id': farmiq_id,
                    'user_id': user_id,
                    'service_type': service_type,
                    'operation': operation,
                    'tokens': tokens,
                    'error': error_msg,
                })
            except Exception as log_e:
                logger.error(f"Failed to log error: {log_e}")

            return {
                'success': False,
                'error': error_msg,
                'tokens_deducted': 0,
            }

    async def check_user_balance(self, farmiq_id: str) -> Optional[float]:
        """Get current FIQ balance for user"""
        try:
            wallet = await self.db.fetch_one("""
                SELECT fiq_token_balance FROM user_wallets 
                WHERE farmiq_id = :farmiq_id
            """, {'farmiq_id': farmiq_id})
            
            if wallet:
                return wallet['fiq_token_balance']
            return None
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return None

    async def check_quota_status(self, farmiq_id: str) -> Optional[Dict[str, Any]]:
        """Get current quota usage and remaining"""
        try:
            quota = await self.db.fetch_one("""
                SELECT 
                    daily_fiq_budget,
                    daily_fiq_remaining,
                    monthly_fiq_budget,
                    monthly_fiq_remaining,
                    daily_fiq_used
                FROM service_quotas 
                WHERE farmiq_id = :farmiq_id AND quota_enabled = true
            """, {'farmiq_id': farmiq_id})
            
            if quota:
                return dict(quota)
            return None
        except Exception as e:
            logger.error(f"Failed to get quota: {e}")
            return None

    async def set_user_quota(
        self,
        farmiq_id: str,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
    ) -> bool:
        """Set or update user quota"""
        try:
            await self.db.execute("""
                INSERT INTO service_quotas (
                    farmiq_id, daily_fiq_budget, monthly_fiq_budget, quota_enabled
                )
                VALUES (:farmiq_id, :daily, :monthly, true)
                ON CONFLICT (farmiq_id) DO UPDATE SET
                    daily_fiq_budget = :daily,
                    monthly_fiq_budget = :monthly,
                    quota_enabled = true,
                    updated_at = NOW()
            """, {
                'farmiq_id': farmiq_id,
                'daily': daily_budget,
                'monthly': monthly_budget,
            })
            
            logger.info(
                f"✅ Quota set",
                farmiq_id=farmiq_id,
                daily=daily_budget,
                monthly=monthly_budget,
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to set quota: {e}")
            return False

    async def get_usage_history(
        self,
        farmiq_id: str,
        service_type: str = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user's AI usage history"""
        try:
            query = """
                SELECT * FROM ai_usage_log 
                WHERE farmiq_id = :farmiq_id
            """
            params = {'farmiq_id': farmiq_id}
            
            if service_type:
                query += " AND service_type = :service_type"
                params['service_type'] = service_type
            
            query += " ORDER BY created_at DESC LIMIT :limit"
            params['limit'] = limit
            
            logs = await self.db.fetch(query, params)
            return [dict(log) for log in logs] if logs else []
        except Exception as e:
            logger.error(f"Failed to get usage history: {e}")
            return []
