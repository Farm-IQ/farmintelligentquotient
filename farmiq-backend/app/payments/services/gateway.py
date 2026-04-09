"""
Unified Payment Gateway Service
Orchestrates M-Pesa, Afrika Talking USSD/SMS, and Hedera Hashgraph integrations

Author: FarmIQ Backend Team
Date: March 2026
"""

import asyncio
import logging
import json
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import text

from core.db_pool import DatabasePool
from app.payments.config import (
    PaymentGatewayConfig,
    PaymentProvider,
    TransactionStatus,
    get_payment_config,
)
from app.payments.services.mpesa_service import MpesaPaymentService
from app.payments.services.afritalk_service import AfrikaTalkingService

logger = logging.getLogger(__name__)


class PaymentGateway:
    """
    Unified payment gateway supporting multiple providers
    - M-Pesa (primary: KES → Tokens)
    - Afrika Talking (USSD menu + SMS notifications)
    """
    
    def __init__(self):
        """Initialize gateway with all services (no Hedera backend)."""
        self.config = get_payment_config()
        
        # Initialize services
        self.mpesa = MpesaPaymentService() if self.config.mpesa else None
        self.afritalk = AfrikaTalkingService() if self.config.afritalk else None
        self.hedera_token = None
        self.hedera_hcs = None
        
        logger.info("✅ Payment Gateway initialized")
    
    # ==================== M-PESA INTEGRATION ====================
    
    async def initiate_mpesa_payment(
        self,
        phone_number: str,
        amount_kes: Decimal,
        farmiq_id: str,
        description: str = "FarmIQ Token Purchase",
    ) -> Dict[str, Any]:
        """
        Initiate M-Pesa STK Push payment
        
        Args:
            phone_number: Customer phone (2547xxxxxx)
            amount_kes: Amount in Kenya Shillings
            farmiq_id: User's FarmIQ identifier
            description: Payment description
            
        Returns:
            Payment initiation response with checkout ID
        """
        if not self.mpesa:
            raise ValueError("M-Pesa service not configured")
        
        logger.info(f"💳 Initiating M-Pesa payment: {phone_number}, {amount_kes} KES")
        
        try:
            result = await self.mpesa.initiate_stk_push(
                phone_number=phone_number,
                amount_kes=int(amount_kes),
                account_reference=farmiq_id,
                transaction_desc=description,
            )
            
            logger.info(f"✅ STK Push successful: {result['checkout_id']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ M-Pesa payment failed: {e}")
            raise
    
    async def handle_mpesa_callback(
        self,
        callback_data: Dict[str, Any],
        farmiq_id: str,
    ) -> Dict[str, Any]:
        """
        Process M-Pesa payment callback
        Mints FIQ tokens on successful payment
        
        Args:
            callback_data: M-Pesa callback payload
            farmiq_id: User's FarmIQ ID
            
        Returns:
            Processing result
        """
        if not self.mpesa:
            raise ValueError("M-Pesa service not configured")
        
        logger.info(f"📨 Processing M-Pesa callback for {farmiq_id}")
        
        try:
            # Parse callback
            result = await self.mpesa.process_payment_callback(callback_data)
            
            if result['status'] == TransactionStatus.SUCCESS:
                # Calculate tokens to mint
                tokens_to_mint = result['amount_kes'] * self.config.mpesa.KES_TO_FIQ_RATE
                
                # Mint tokens on Hedera
                if self.hedera_token:
                    token_result = await self.mint_tokens(
                        farmiq_id=farmiq_id,
                        amount=tokens_to_mint,
                        transaction_reference=result['checkout_id'],
                        source="m_pesa_payment",
                    )
                    result['token_mint'] = token_result
                
                # Send confirmation SMS
                if self.afritalk:
                    await self.afritalk.send_sms(
                        phone_number=result['phone_number'],
                        message=f"✅ Payment confirmed! {tokens_to_mint} FIQ tokens added to your account.",
                        priority="high"
                    )
            
            # HCS auditing is disabled; audit logs are maintained in local DB.
            return result
            
        except Exception as e:
            logger.error(f"❌ Callback processing failed: {e}")
            raise
    
    # ==================== HEDERA TOKEN INTEGRATION ====================
    
    async def mint_tokens(
        self,
        farmiq_id: str,
        amount: Decimal,
        transaction_reference: str,
        source: str = "payment",
    ) -> Dict[str, Any]:
        """
        Mint FIQ tokens in local ledger (no Hedera call).

        Args:
            farmiq_id: User's FarmIQ ID
            amount: Number of tokens to mint
            transaction_reference: Reference to payment transaction
            source: Source of minting (payment, referral, reward, etc)

        Returns:
            Mint transaction result
        """
        if not self.mpesa:
            raise ValueError("M-Pesa service not configured")

        logger.info(f"🪙 Minting {amount} FIQ tokens for {farmiq_id} (local ledger)")

        try:
            result = await self.mpesa.mint_fiq_tokens(
                checkout_id=transaction_reference,
                farmiq_id=farmiq_id,
            )

            return {
                'tokens_minted': amount,
                'transaction_id': result.get('transaction_id'),
                'balance_after': result.get('balance_after'),
                'source': source,
            }

        except Exception as e:
            logger.error(f"❌ Local token minting failed: {e}")
            raise
    
    async def get_token_balance(self, farmiq_id: str) -> Decimal:
        """Get user's FIQ token balance from local ledger."""
        try:
            # Query local user_wallets table (run in thread pool)
            def get_balance():
                session_factory = DatabasePool.get_session_factory()
                session = session_factory()
                try:
                    row = session.execute(
                        text("SELECT fiq_token_balance FROM user_wallets WHERE farmiq_id = :farmiq_id"),
                        {"farmiq_id": farmiq_id}
                    ).fetchone()
                    if row:
                        return Decimal(str(row[0] or 0))
                    return Decimal(0)
                finally:
                    session.close()
            
            balance = await asyncio.to_thread(get_balance)
            return balance
        except Exception as e:
            logger.error(f"Failed to get local token balance for {farmiq_id}: {e}")
            raise

    # ==================== USSD & SMS INTEGRATION ====================
    
    async def send_payment_notification_sms(
        self,
        phone_number: str,
        farmiq_id: str,
        amount_kes: Decimal,
        tokens_received: Decimal,
    ) -> Dict[str, Any]:
        """
        Send SMS notification about payment
        
        Args:
            phone_number: Recipient phone
            farmiq_id: User's FarmIQ ID
            amount_kes: Amount paid in KES
            tokens_received: Tokens received
            
        Returns:
            SMS delivery status
        """
        if not self.afritalk:
            raise ValueError("Afrika Talking service not configured")
        
        message = (
            f"✅ FarmIQ Payment Confirmed!\n"
            f"Amount: {amount_kes} KES\n"
            f"Tokens: {tokens_received} FIQ\n"
            f"Balance: Check in app or dial *384*46648#"
        )
        
        return await self.afritalk.send_sms(
            phone_number=phone_number,
            message=message,
            priority="high",
        )
    
    async def initiate_ussd_session(
        self,
        phone_number: str,
    ) -> Dict[str, Any]:
        """
        Initiate USSD session for menu navigation
        
        Args:
            phone_number: User's phone number
            
        Returns:
            USSD session details
        """
        if not self.afritalk:
            raise ValueError("Afrika Talking service not configured")
        
        return await self.afritalk.initiate_ussd_session(
            phone_number=phone_number,
        )
    
    async def send_ussd_menu(
        self,
        phone_number: str,
        session_id: str,
        menu_text: str,
        end_session: bool = False,
    ) -> Dict[str, Any]:
        """
        Send USSD menu to user
        
        Args:
            phone_number: User phone
            session_id: USSD session ID
            menu_text: Menu content
            end_session: Whether to end session
            
        Returns:
            USSD send result
        """
        if not self.afritalk:
            raise ValueError("Afrika Talking service not configured")
        
        return await self.afritalk.send_ussd_response(
            phone_number=phone_number,
            session_id=session_id,
            text=menu_text,
            end_session=end_session,
        )
    
    # ==================== BULK SMS CAMPAIGNS ====================
    
    async def send_bulk_sms_campaign(
        self,
        phone_numbers: List[str],
        message: str,
        campaign_name: str,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """
        Send bulk SMS campaign
        
        Args:
            phone_numbers: List of recipient phones
            message: Message content
            campaign_name: Campaign name
            campaign_id: Unique campaign ID
            
        Returns:
            Campaign result
        """
        if not self.afritalk:
            raise ValueError("Afrika Talking service not configured")
        
        logger.info(f"📨 Sending bulk SMS: {len(phone_numbers)} recipients")
        
        return await self.afritalk.send_bulk_sms(
            phone_list=phone_numbers,
            message=message,
            bulk_id=campaign_id,
        )
    
    async def get_bulk_sms_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get bulk SMS campaign status"""
        if not self.afritalk:
            raise ValueError("Afrika Talking service not configured")
        
        return await self.afritalk.get_bulk_status(bulk_id=campaign_id)
    
    # ==================== HEDERA AUDIT LOGGING ====================
    
    async def log_transaction_to_hedera(
        self,
        farmiq_id: str,
        transaction_type: str,
        amount: Decimal,
        provider: str,
        transaction_id: str,
        status: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Log transaction in local audit table (Hedera disabled).
        
        Args:
            farmiq_id: User's FarmIQ ID
            transaction_type: Type of transaction (payment, mint, transfer, etc)
            amount: Transaction amount
            provider: Provider (m_pesa, afritalk)
            transaction_id: Provider's transaction ID
            status: Transaction status
            metadata: Additional metadata
            
        Returns:
            Audit result record
        """
        logger.info(f"🔐 Logging transaction locally (Hedera disabled): {transaction_id}")

        # Log transaction audit (run in thread pool)
        def log_audit():
            session_factory = DatabasePool.get_session_factory()
            session = session_factory()
            try:
                session.execute(
                    text("""
                    INSERT INTO payment_audit_log (
                        farmiq_id, transaction_type, provider,
                        amount, transaction_id, status, metadata, created_at
                    ) VALUES (:farmiq_id, :transaction_type, :provider,
                              :amount, :transaction_id, :status, :metadata, NOW())
                    """),
                    {
                        "farmiq_id": farmiq_id,
                        "transaction_type": transaction_type,
                        "provider": provider,
                        "amount": str(amount),
                        "transaction_id": transaction_id,
                        "status": status,
                        "metadata": json.dumps(metadata or {}),
                    }
                )
                session.commit()
            finally:
                session.close()
        
        await asyncio.to_thread(log_audit)

        return {
            'farmiq_id': farmiq_id,
            'transaction_id': transaction_id,
            'status': status,
            'logged': True,
        }
    
    # ==================== RECONCILIATION & REPORTING ====================
    
    async def reconcile_payment_state(
        self,
        checkout_id: str,
    ) -> Dict[str, Any]:
        """
        Reconcile payment state across providers
        Check M-Pesa status, verify token mint on Hedera
        
        Args:
            checkout_id: Original checkout ID
            
        Returns:
            Reconciliation result
        """
        if not self.mpesa:
            raise ValueError("M-Pesa service not configured")
        
        logger.info(f"🔄 Reconciling payment: {checkout_id}")
        
        # Check M-Pesa status
        mpesa_status = await self.mpesa.query_payment_status(checkout_id)
        
        # Hedera status is not tracked in backend; frontend handles chain verification.
        return {
            "checkout_id": checkout_id,
            "mpesa_status": mpesa_status,
            "hedera_status": None,
            "reconciled_at": datetime.utcnow().isoformat(),
        }
    
    # ==================== HEALTH & STATUS ====================
    
    async def check_gateway_health(self) -> Dict[str, Any]:
        """Check health of all payment services"""
        health = {
            "gateway": "healthy",
            "services": {},
            "checked_at": datetime.utcnow().isoformat(),
        }
        
        # Check M-Pesa
        if self.mpesa:
            try:
                mpesa_health = await self.mpesa.health_check()
                health["services"]["mpesa"] = "healthy" if mpesa_health else "unhealthy"
            except Exception as e:
                logger.warning(f"M-Pesa health check failed: {e}")
                health["services"]["mpesa"] = "unhealthy"
        
        # Check Afrika Talking
        if self.afritalk:
            try:
                afritalk_health = await self.afritalk.health_check()
                health["services"]["afritalk"] = "healthy" if afritalk_health else "unhealthy"
            except Exception as e:
                logger.warning(f"Afrika Talking health check failed: {e}")
                health["services"]["afritalk"] = "unhealthy"
        
        # Determine overall health
        if any(v == "unhealthy" for v in health["services"].values()):
            health["gateway"] = "degraded"
        
        return health


# Global gateway instance
_gateway: Optional[PaymentGateway] = None


def get_payment_gateway() -> PaymentGateway:
    """Get singleton payment gateway instance"""
    global _gateway
    if _gateway is None:
        _gateway = PaymentGateway()
    return _gateway
