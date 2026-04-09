"""
Payment Integration Layer
Coordinates M-Pesa, Afrika Talking, and Hedera services with retry logic and fallbacks

Author: FarmIQ Backend Team
Date: March 2026
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.payments.config import get_payment_config, TransactionStatus
from app.payments.exceptions import (
    ErrorCode,
    PaymentException,
    ErrorRecoveryHandler,
    ErrorRecoveryStrategy,
)

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_seconds: float = 1,
        max_delay_seconds: float = 30,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt with exponential backoff"""
        delay = self.initial_delay_seconds * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay_seconds)
        
        if self.jitter:
            # Add random jitter (±10%)
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class RetryHandler:
    """Handle retries with exponential backoff"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute_with_retry(
        self,
        func: Callable,
        error_code: ErrorCode,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            error_code: Error code to track
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        strategy = ErrorRecoveryHandler.get_strategy(error_code)
        
        if strategy != ErrorRecoveryStrategy.RETRY:
            raise PaymentException(
                error_code=error_code,
                message=f"Error not retriable: {error_code}",
            )
        
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                logger.info(f"Executing with retry (attempt {attempt + 1}/{self.config.max_attempts})")
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_attempts - 1:
                    delay = self.config.get_delay(attempt)
                    logger.info(f"Retrying after {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise PaymentException(
            error_code=error_code,
            message=f"All {self.config.max_attempts} retry attempts failed",
            details={"last_error": str(last_exception)},
        )


class FallbackHandler:
    """Handle provider fallbacks"""
    
    def __init__(self, gateway):
        self.gateway = gateway
        self.fallback_chain = {
            "mpesa": ["airtel"],
            "airtel": ["mobile_money"],
            "afritalk": ["twilio"],  # Could be extended
        }
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        primary_provider: str,
        fallback_provider: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute primary function, fallback to secondary on failure
        
        Args:
            primary_func: Primary provider's function
            fallback_func: Fallback provider's function
            primary_provider: Primary provider name
            fallback_provider: Fallback provider name
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        try:
            logger.info(f"Trying primary provider: {primary_provider}")
            result = await primary_func(*args, **kwargs)
            logger.info(f"✅ Primary provider succeeded: {primary_provider}")
            return result
            
        except PaymentException as e:
            strategy = ErrorRecoveryHandler.get_strategy(e.error_code)
            
            if strategy == ErrorRecoveryStrategy.FALLBACK:
                logger.warning(
                    f"Primary provider failed ({e.error_code}), falling back to {fallback_provider}"
                )
                try:
                    result = await fallback_func(*args, **kwargs)
                    logger.info(f"✅ Fallback provider succeeded: {fallback_provider}")
                    return result
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
                    raise
            else:
                raise


class TransactionOrchestrator:
    """
    Orchestrate complex multi-step payment transactions
    Coordinates M-Pesa, token minting, SMS notifications, etc.
    """
    
    def __init__(self, gateway):
        self.gateway = gateway
        self.retry_handler = RetryHandler()
        self.fallback_handler = FallbackHandler(gateway)
        self.config = get_payment_config()
    
    async def process_payment_flow(
        self,
        phone_number: str,
        amount_kes: Decimal,
        farmiq_id: str,
    ) -> Dict[str, Any]:
        """
        Complete payment flow: M-Pesa → Token Mint → SMS Notification → HCS Log
        
        Args:
            phone_number: Customer phone
            amount_kes: Payment amount
            farmiq_id: User FarmIQ ID
            
        Returns:
            Complete transaction result
        """
        logger.info(f"🚀 Starting payment flow for {farmiq_id}")
        
        transaction_state = {
            "phase": "initiated",
            "phases_completed": [],
            "errors": [],
            "results": {},
        }
        
        try:
            # Phase 1: Validate input
            transaction_state["phase"] = "validation"
            await self._validate_payment_input(phone_number, amount_kes)
            transaction_state["phases_completed"].append("validation")
            
            # Phase 2: Initiate M-Pesa STK Push
            transaction_state["phase"] = "mpesa_initiation"
            mpesa_result = await self.gateway.initiate_mpesa_payment(
                phone_number=phone_number,
                amount_kes=amount_kes,
                farmiq_id=farmiq_id,
            )
            transaction_state["results"]["mpesa"] = mpesa_result
            transaction_state["phases_completed"].append("mpesa_initiation")
            
            # Phase 3: Wait for M-Pesa callback (handled separately)
            # Return to user for payment entry
            logger.info(f"✅ M-Pesa STK Push initiated: {mpesa_result['checkout_id']}")
            
            return {
                "status": "awaiting_payment",
                "checkout_id": mpesa_result["checkout_id"],
                "transaction_state": transaction_state,
            }
            
        except Exception as e:
            logger.error(f"❌ Payment flow error: {e}")
            transaction_state["errors"].append({
                "phase": transaction_state["phase"],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            raise
    
    async def complete_payment_after_mpesa_callback(
        self,
        checkout_id: str,
        farmiq_id: str,
        amount_kes: Decimal,
        mpesa_receipt: str,
    ) -> Dict[str, Any]:
        """
        Complete payment after M-Pesa callback received
        Handles: Token minting, SMS notification, HCS logging
        
        Args:
            checkout_id: M-Pesa checkout ID
            farmiq_id: User FarmIQ ID
            amount_kes: Payment amount
            mpesa_receipt: M-Pesa receipt number
            
        Returns:
            Completion result
        """
        logger.info(f"💰 Completing payment after M-Pesa callback: {mpesa_receipt}")
        
        transaction_state = {
            "status": "completing",
            "phases_completed": [],
            "results": {},
        }
        
        try:
            # Phase 1: Calculate tokens
            tokens_to_mint = amount_kes * self.config.mpesa.KES_TO_FIQ_RATE
            transaction_state["results"]["tokens_to_mint"] = str(tokens_to_mint)
            
            # Phase 2: Mint tokens on Hedera
            if self.gateway.hedera_token:
                token_result = await self.gateway.mint_tokens(
                    farmiq_id=farmiq_id,
                    amount=tokens_to_mint,
                    transaction_reference=mpesa_receipt,
                    source="m_pesa_payment",
                )
                transaction_state["results"]["hedera_mint"] = token_result
                transaction_state["phases_completed"].append("hedera_mint")
                logger.info(f"✅ Tokens minted: {token_result.get('transaction_id')}")
            
            # Phase 3: Send SMS notification
            if self.gateway.afritalk:
                sms_result = await self.gateway.send_payment_notification_sms(
                    phone_number=farmiq_id,  # TODO: Get actual phone from user profile
                    farmiq_id=farmiq_id,
                    amount_kes=amount_kes,
                    tokens_received=tokens_to_mint,
                )
                transaction_state["results"]["sms_notification"] = sms_result
                transaction_state["phases_completed"].append("sms_notification")
                logger.info(f"✅ SMS notification sent")
            
            # Phase 4: Log to HCS (immutable audit)
            if self.gateway.hedera_hcs and self.config.ENABLE_HEDERA_LOGGING:
                hcs_result = await self.gateway.log_transaction_to_hedera(
                    farmiq_id=farmiq_id,
                    transaction_type="payment_completion",
                    amount=amount_kes,
                    provider="m_pesa",
                    transaction_id=mpesa_receipt,
                    status="success",
                    metadata={
                        "checkout_id": checkout_id,
                        "tokens_minted": str(tokens_to_mint),
                    },
                )
                transaction_state["results"]["hcs_audit"] = hcs_result
                transaction_state["phases_completed"].append("hcs_audit")
                logger.info(f"✅ Transaction logged to HCS")
            
            transaction_state["status"] = "completed"
            return transaction_state
            
        except Exception as e:
            logger.error(f"❌ Payment completion failed: {e}")
            transaction_state["status"] = "failed"
            transaction_state["error"] = str(e)
            raise
    
    # ==================== USSD PAYMENT FLOW ====================
    
    async def process_ussd_payment_flow(
        self,
        phone_number: str,
        amount_kes: Decimal,
        farmiq_id: str,
    ) -> Dict[str, Any]:
        """
        Process payment through USSD menu
        
        Args:
            phone_number: User phone
            amount_kes: Payment amount
            farmiq_id: User FarmIQ ID
            
        Returns:
            USSD flow result
        """
        logger.info(f"📱 Starting USSD payment flow for {farmiq_id}")
        
        try:
            # Initiate USSD session
            session_result = await self.gateway.initiate_ussd_session(phone_number)
            session_id = session_result["session_id"]
            
            # Send payment menu
            menu_text = (
                "FarmIQ - Buy Tokens\n"
                f"Amount: {amount_kes} KES\n"
                f"Tokens: {amount_kes * self.config.mpesa.KES_TO_FIQ_RATE} FIQ\n\n"
                "1. Confirm Payment\n"
                "2. Cancel\n"
                "3. Different Amount"
            )
            
            await self.gateway.send_ussd_menu(
                phone_number=phone_number,
                session_id=session_id,
                menu_text=menu_text,
            )
            
            return {
                "status": "menu_displayed",
                "session_id": session_id,
                "amount_kes": str(amount_kes),
                "tokens_available": str(amount_kes * self.config.mpesa.KES_TO_FIQ_RATE),
            }
            
        except Exception as e:
            logger.error(f"❌ USSD payment flow failed: {e}")
            raise
    
    # ==================== HELPER METHODS ====================
    
    async def _validate_payment_input(
        self,
        phone_number: str,
        amount_kes: Decimal,
    ):
        """Validate payment input"""
        from app.payments.validation import validate_phone_number, validate_payment_amount
        
        validate_phone_number(phone_number)
        validate_payment_amount(amount_kes, self.config.mpesa)


class PaymentTransactionLogger:
    """Log and track payment transactions for reconciliation"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def log_transaction(
        self,
        farmiq_id: str,
        transaction_id: str,
        transaction_type: str,
        amount: Decimal,
        provider: str,
        status: str,
        metadata: Dict[str, Any] = None,
    ):
        """Log transaction to database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO payment_transactions (
                    farmiq_id, transaction_id, transaction_type,
                    amount, provider, status, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                farmiq_id,
                transaction_id,
                transaction_type,
                str(amount),
                provider,
                status,
                metadata or {},
                datetime.utcnow(),
            )
    
    async def get_transaction(
        self,
        transaction_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve transaction from database"""
        async with self.db_pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM payment_transactions WHERE transaction_id = $1",
                transaction_id,
            )
    
    async def update_transaction_status(
        self,
        transaction_id: str,
        new_status: str,
        metadata_updates: Dict[str, Any] = None,
    ):
        """Update transaction status"""
        async with self.db_pool.acquire() as conn:
            metadata = await conn.fetchval(
                "SELECT metadata FROM payment_transactions WHERE transaction_id = $1",
                transaction_id,
            )
            
            if metadata_updates:
                metadata.update(metadata_updates)
            
            await conn.execute(
                """
                UPDATE payment_transactions
                SET status = $1, metadata = $2, updated_at = $3
                WHERE transaction_id = $4
                """,
                new_status,
                metadata or {},
                datetime.utcnow(),
                transaction_id,
            )
