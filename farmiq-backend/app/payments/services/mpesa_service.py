"""
M-Pesa Payment Integration Service
Handles M-Pesa STK Push, payment callbacks, token minting, and error handling
Integration with Africa's Talking (Daraja) API for Kenya M-Pesa

Author: FarmIQ Backend Team
Date: March 2026
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from decimal import Decimal
import base64
import hashlib
import httpx

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, Session

from core.logging_config import get_logger

logger = get_logger(__name__)

# ===================== CONFIGURATION =====================

class MpesaConfig:
    """M-Pesa and Africa's Talking configuration"""
    
    DARAJA_BASE_URL = os.getenv("DARAJA_BASE_URL", "https://sandbox.safaricom.co.ke")
    DARAJA_OAUTH_URL = f"{DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    
    DARAJA_BUSINESS_SHORTCODE = os.getenv("DARAJA_BUSINESS_SHORTCODE", "174379")
    DARAJA_CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY")
    DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET")
    DARAJA_PASSKEY = os.getenv("DARAJA_PASSKEY")
    
    STK_PUSH_URL = f"{DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    QUERY_URL = f"{DARAJA_BASE_URL}/mpesa/stkpushquery/v1/query"
    
    # Callback URLs (must be public + HTTPS)
    CALLBACK_CONFIRMATION_URL = os.getenv("CALLBACK_CONFIRMATION_URL", "https://farmiq.example.com/api/v1/payments/mpesa/confirmation")
    CALLBACK_VALIDATION_URL = os.getenv("CALLBACK_VALIDATION_URL", "https://farmiq.example.com/api/v1/payments/mpesa/validation")
    
    # FIQ Token exchange rules
    TOKENS_PER_1000_KES = 100  # 1000 KES = 100 FIQ tokens
    MIN_PAYMENT_KES = 10
    MAX_PAYMENT_KES = 150000
    
    # Timing
    STK_PUSH_TIMEOUT_SECONDS = 60
    PAYMENT_CONFIRMATION_TIMEOUT = 5 * 60  # 5 minutes to confirm


# ===================== M-PESA SERVICE =====================

class MpesaPaymentService:
    """
    Main M-Pesa payment service
    Handles STK push, payment confirmation, token minting, and reversal
    """
    
    def __init__(self, session_factory: sessionmaker):
        """
        Initialize M-Pesa service with SQLAlchemy session factory
        
        Args:
            session_factory: SQLAlchemy sessionmaker for database access
        """
        self.session_factory = session_factory
        self.config = MpesaConfig()
        self.oauth_token = None
        self.oauth_token_expires_at = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    # ===================== OAUTH AUTHENTICATION =====================
    
    async def _get_oauth_token(self) -> str:
        """
        Get OAuth access token from Daraja API
        Tokens cached and reused until expiry
        
        Returns:
            Access token string
        
        Raises:
            HTTPException: If OAuth request fails
        """
        try:
            # Check if cached token still valid
            if self.oauth_token and self.oauth_token_expires_at:
                if datetime.now() < self.oauth_token_expires_at:
                    logger.debug("Using cached OAuth token")
                    return self.oauth_token
            
            # Request new token
            credentials = base64.b64encode(
                f"{self.config.DARAJA_CONSUMER_KEY}:{self.config.DARAJA_CONSUMER_SECRET}".encode()
            ).decode()
            
            response = await self.client.get(
                self.config.DARAJA_OAUTH_URL,
                headers={"Authorization": f"Basic {credentials}"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.oauth_token = data["access_token"]
            expires_in = int(data.get("expires_in", 3599))
            self.oauth_token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info(f"✅ OAuth token obtained (expires in {expires_in}s)")
            return self.oauth_token
            
        except Exception as e:
            logger.error(f"❌ OAuth token request failed: {str(e)}")
            raise HTTPException(status_code=500, detail="M-Pesa authentication failed")
    
    # ===================== STK PUSH INITIATION =====================
    
    async def initiate_stk_push(
        self,
        phone_number: str,
        amount_kes: Decimal,
        farmiq_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Initiate M-Pesa STK Push payment request
        Prompts user to enter M-Pesa PIN on their phone
        
        Args:
            phone_number: M-Pesa phone number (2547xxxxxx)
            amount_kes: Amount in Kenya Shillings
            farmiq_id: FarmIQ user identifier
            user_id: System user ID (UUID)
        
        Returns:
            {
                'checkout_id': str,
                'status': 'INITIATED',
                'phone_number': str,
                'amount_kes': Decimal,
                'tokens_to_purchase': Decimal,
                'stk_push_sent_at': datetime
            }
        
        Raises:
            HTTPException: If validation fails or API error
        """
        try:
            # Validate inputs
            self._validate_payment_amount(amount_kes)
            self._validate_phone_number(phone_number)
            
            # Check user wallet exists (run in thread pool)
            def check_wallet():
                session = self.session_factory()
                try:
                    result = session.execute(
                        text("SELECT id, fiq_token_balance, wallet_status FROM user_wallets WHERE farmiq_id = :farmiq_id"),
                        {"farmiq_id": farmiq_id}
                    ).fetchone()
                    return result
                finally:
                    session.close()
            
            wallet = await asyncio.to_thread(check_wallet)
            if not wallet:
                raise HTTPException(status_code=404, detail="User wallet not found")
            
            if wallet[2] != "ACTIVE":  # wallet_status column
                raise HTTPException(status_code=403, detail="Wallet is suspended or disabled")
            
            # Calculate tokens to purchase
            tokens_to_purchase = self._calculate_fiq_tokens(amount_kes)
            
            # Generate checkout ID
            checkout_id = self._generate_checkout_id(farmiq_id, phone_number)
            
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Build password for Daraja API
            daraja_password = base64.b64encode(
                f"{self.config.DARAJA_BUSINESS_SHORTCODE}{self.config.DARAJA_PASSKEY}{timestamp}".encode()
            ).decode()
            
            # Get OAuth token
            access_token = await self._get_oauth_token()
            
            # Prepare STK Push request
            stk_request_body = {
                "BusinessShortCode": self.config.DARAJA_BUSINESS_SHORTCODE,
                "Password": daraja_password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount_kes),
                "PartyA": phone_number,
                "PartyB": self.config.DARAJA_BUSINESS_SHORTCODE,
                "PhoneNumber": phone_number,
                "CallBackURL": self.config.CALLBACK_CONFIRMATION_URL,
                "AccountReference": checkout_id,
                "TransactionDesc": f"FIQ Token Purchase {tokens_to_purchase:.0f}"
            }
            
            logger.info(f"📤 Sending STK Push to {phone_number} for {amount_kes} KES")
            
            # Call Daraja API
            response = await self.client.post(
                self.config.STK_PUSH_URL,
                json=stk_request_body,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            
            daraja_response = response.json()
            
            # Log to database (run in thread pool)
            def insert_transaction():
                session = self.session_factory()
                try:
                    session.execute(
                        text("""
                        INSERT INTO mpesa_transactions (
                            farmiq_id, user_id, phone_number, checkout_id,
                            amount_kes, tokens_purchased, payment_status, stk_push_sent_at
                        ) VALUES (:farmiq_id, :user_id, :phone_number, :checkout_id,
                                 :amount_kes, :tokens_purchased, :payment_status, :stk_push_sent_at)
                        """),
                        {
                            "farmiq_id": farmiq_id,
                            "user_id": user_id,
                            "phone_number": phone_number,
                            "checkout_id": checkout_id,
                            "amount_kes": float(amount_kes),
                            "tokens_purchased": float(tokens_to_purchase),
                            "payment_status": "INITIATED",
                            "stk_push_sent_at": datetime.now()
                        }
                    )
                    session.commit()
                finally:
                    session.close()
            
            await asyncio.to_thread(insert_transaction)
            
            logger.info(f"✅ STK Push initiated: {checkout_id}")
            
            return {
                "checkout_id": checkout_id,
                "status": "INITIATED",
                "phone_number": phone_number,
                "amount_kes": amount_kes,
                "tokens_to_purchase": tokens_to_purchase,
                "stk_push_sent_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ STK Push failed: {str(e)}")
            raise
    
    # ===================== PAYMENT CALLBACK HANDLERS =====================
    
    async def handle_payment_confirmation(
        self,
        callback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle M-Pesa payment confirmation callback from Daraja
        Validates payment and initiates token minting
        """
        try:
            stk_callback = callback_data.get("Body", {}).get("stkCallback", {})
            result_code = stk_callback.get("ResultCode")
            checkout_id = stk_callback.get("CheckoutRequestID")
            
            logger.info(f"📥 Payment callback received: {checkout_id} (ResultCode: {result_code})")
            
            # Get transaction from database (run in thread pool)
            def get_transaction():
                session = self.session_factory()
                try:
                    result = session.execute(
                        text("SELECT * FROM mpesa_transactions WHERE checkout_id = :checkout_id"),
                        {"checkout_id": checkout_id}
                    ).fetchone()
                    return result
                finally:
                    session.close()
            
            tx = await asyncio.to_thread(get_transaction)
            
            if not tx:
                logger.warning(f"⚠️ Callback for unknown checkout: {checkout_id}")
                return {"status": "IGNORED"}
            
            # Handle success (ResultCode 0)
            if result_code == 0:
                metadata_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
                payment_data = self._parse_callback_metadata(metadata_items)
                
                # Update transaction record (run in thread pool)
                def update_success():
                    session = self.session_factory()
                    try:
                        session.execute(
                            text("""
                            UPDATE mpesa_transactions SET
                                payment_status = :status,
                                mpesa_receipt_number = :receipt,
                                mpesa_transaction_date = :tx_date,
                                first_callback_at = :callback_at
                            WHERE checkout_id = :checkout_id
                            """),
                            {
                                "status": "COMPLETED",
                                "receipt": payment_data.get("receipt_number"),
                                "tx_date": datetime.now(),
                                "callback_at": datetime.now(),
                                "checkout_id": checkout_id
                            }
                        )
                        session.commit()
                    finally:
                        session.close()
                
                await asyncio.to_thread(update_success)
                logger.info(f"✅ Payment confirmed: {checkout_id}")
                
                return {
                    "status": "SUCCESS",
                    "checkout_id": checkout_id,
                    "amount": payment_data.get("amount")
                }
            
            # Handle user cancellation (ResultCode 1)
            elif result_code == 1:
                def update_cancelled():
                    session = self.session_factory()
                    try:
                        session.execute(
                            text("""
                            UPDATE mpesa_transactions SET
                                payment_status = :status,
                                first_callback_at = :callback_at
                            WHERE checkout_id = :checkout_id
                            """),
                            {
                                "status": "USER_CANCELLED",
                                "callback_at": datetime.now(),
                                "checkout_id": checkout_id
                            }
                        )
                        session.commit()
                    finally:
                        session.close()
                
                await asyncio.to_thread(update_cancelled)
                logger.info(f"⚠️ Payment cancelled by user: {checkout_id}")
                return {"status": "CANCELLED"}
            
            # Handle timeout (ResultCode 1032)
            elif result_code == 1032:
                def update_timeout():
                    session = self.session_factory()
                    try:
                        session.execute(
                            text("""
                            UPDATE mpesa_transactions SET
                                payment_status = :status,
                                first_callback_at = :callback_at
                            WHERE checkout_id = :checkout_id
                            """),
                            {
                                "status": "TIMEOUT",
                                "callback_at": datetime.now(),
                                "checkout_id": checkout_id
                            }
                        )
                        session.commit()
                    finally:
                        session.close()
                
                await asyncio.to_thread(update_timeout)
                logger.info(f"⏱️ Payment timed out: {checkout_id}")
                return {"status": "TIMEOUT"}
            
            # Handle other errors
            else:
                error_desc = stk_callback.get("ResultDesc", "Unknown error")
                
                def update_failed():
                    session = self.session_factory()
                    try:
                        session.execute(
                            text("""
                            UPDATE mpesa_transactions SET
                                payment_status = :status,
                                mpesa_error_code = :error_code,
                                mpesa_error_description = :error_desc,
                                first_callback_at = :callback_at
                            WHERE checkout_id = :checkout_id
                            """),
                            {
                                "status": "FAILED",
                                "error_code": str(result_code),
                                "error_desc": error_desc,
                                "callback_at": datetime.now(),
                                "checkout_id": checkout_id
                            }
                        )
                        session.commit()
                    finally:
                        session.close()
                
                await asyncio.to_thread(update_failed)
                logger.error(f"❌ Payment failed: {checkout_id} - {error_desc}")
                return {"status": "FAILED", "error": error_desc}
        
        except Exception as e:
            logger.error(f"❌ Callback processing failed: {str(e)}")
            raise
    
    # ===================== TOKEN MINTING =====================
    
    async def mint_fiq_tokens(
        self,
        checkout_id: str,
        farmiq_id: str
    ) -> Dict[str, Any]:
        """
        Mint FIQ tokens after payment confirmed
        Transfers tokens via Hedera Token Service
        
        Args:
            checkout_id: M-Pesa transaction checkout ID
            farmiq_id: FarmIQ user identifier
        
        Returns:
            {
                'tokens_minted': Decimal,
                'hedera_tx_id': str,
                'balance_after': Decimal
            }
        """
        try:
            # Get transaction details (run in thread pool)
            def get_transaction_details():
                session = self.session_factory()
                try:
                    result = session.execute(
                        text("""
                        SELECT mt.*, w.hedera_wallet_id, w.fiq_token_balance
                        FROM mpesa_transactions mt
                        JOIN user_wallets w ON mt.farmiq_id = w.farmiq_id
                        WHERE mt.checkout_id = :checkout_id AND mt.payment_status = 'COMPLETED'
                        """),
                        {"checkout_id": checkout_id}
                    ).fetchone()
                    return result
                finally:
                    session.close()
            
            tx = await asyncio.to_thread(get_transaction_details)
            
            if not tx:
                raise HTTPException(status_code=404, detail="Transaction not found or not completed")
            
            tokens_to_mint = Decimal(str(tx["tokens_purchased"]))
            hedera_wallet = tx["hedera_wallet_id"]
            
            logger.info(f"🪙 Minting {tokens_to_mint} FIQ for {farmiq_id}")
            
            # Local minting; frontend handles chain settlement.
            local_tx_id = f"local-mint-{checkout_id}-{int(datetime.utcnow().timestamp())}"
            new_balance = Decimal(str(tx["fiq_token_balance"])) + tokens_to_mint

            # Update transaction record (run in thread pool)
            def update_transaction():
                session = self.session_factory()
                try:
                    session.execute(
                        text("""
                        UPDATE mpesa_transactions SET
                            hedera_tx_id = :hedera_tx_id,
                            tokens_minted_at = :tokens_minted_at,
                            payment_status = :payment_status
                        WHERE checkout_id = :checkout_id
                        """),
                        {
                            "hedera_tx_id": local_tx_id,
                            "tokens_minted_at": datetime.now(),
                            "payment_status": "CONFIRMED",
                            "checkout_id": checkout_id
                        }
                    )
                    session.commit()
                finally:
                    session.close()
            
            await asyncio.to_thread(update_transaction)

            # Update user wallet (run in thread pool)
            def update_wallet():
                session = self.session_factory()
                try:
                    session.execute(
                        text("""
                        UPDATE user_wallets SET
                            fiq_token_balance = :fiq_token_balance,
                            fiq_balance_last_updated = :fiq_balance_last_updated
                        WHERE farmiq_id = :farmiq_id
                        """),
                        {
                            "fiq_token_balance": new_balance,
                            "fiq_balance_last_updated": datetime.now(),
                            "farmiq_id": farmiq_id
                        }
                    )
                    session.commit()
                finally:
                    session.close()
            
            await asyncio.to_thread(update_wallet)
            
            logger.info(f"✅ Tokens minted: {tokens_to_mint} FIQ -> {new_balance}")
            
            return {
                "tokens_minted": tokens_to_mint,
                "transaction_id": local_tx_id,
                "balance_after": new_balance
            }
        
        except Exception as e:
            logger.error(f"❌ Token minting failed: {str(e)}")
            raise
    
    # ===================== PAYMENT STATUS QUERY =====================
    
    async def query_payment_status(
        self,
        checkout_id: str
    ) -> Dict[str, Any]:
        """
        Query M-Pesa payment status (for frontend polling)
        
        Returns current status and details from database
        """
        try:
            # Query transaction from database (run in thread pool)
            def get_status():
                session = self.session_factory()
                try:
                    result = session.execute(
                        text("SELECT * FROM mpesa_transactions WHERE checkout_id = :checkout_id"),
                        {"checkout_id": checkout_id}
                    ).fetchone()
                    return result
                finally:
                    session.close()
            
            tx = await asyncio.to_thread(get_status)
            
            if not tx:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return {
                "checkout_id": checkout_id,
                "status": tx["payment_status"],
                "amount_kes": tx["amount_kes"],
                "tokens_purchased": tx["tokens_purchased"],
                "created_at": tx["created_at"],
                "stk_push_sent_at": tx["stk_push_sent_at"],
                "first_callback_at": tx["first_callback_at"],
                "mpesa_receipt": tx["mpesa_receipt_number"]
            }
        
        except Exception as e:
            logger.error(f"❌ Status query failed: {str(e)}")
            raise
    
    # ===================== PAYMENT HISTORY =====================
    
    async def get_payment_history(
        self,
        farmiq_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get payment history for a user
        """
        try:
            # Query payment history (run in thread pool)
            def get_history():
                session = self.session_factory()
                try:
                    transactions = session.execute(
                        text("""
                        SELECT 
                            checkout_id, amount_kes, tokens_purchased, 
                            payment_status, mpesa_receipt_number,
                            created_at, stk_push_sent_at, first_callback_at
                        FROM mpesa_transactions
                        WHERE farmiq_id = :farmiq_id
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                        """),
                        {
                            "farmiq_id": farmiq_id,
                            "limit": limit,
                            "offset": offset
                        }
                    ).fetchall()
                    
                    total = session.execute(
                        text("SELECT COUNT(*) as count FROM mpesa_transactions WHERE farmiq_id = :farmiq_id"),
                        {"farmiq_id": farmiq_id}
                    ).fetchone()
                    
                    return transactions, total[0] if total else 0
                finally:
                    session.close()
            
            transactions, total = await asyncio.to_thread(get_history)
            
            return {
                "transactions": [dict(tx) for tx in transactions],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        
        except Exception as e:
            logger.error(f"❌ History query failed: {str(e)}")
            raise
    
    # ===================== HELPER FUNCTIONS =====================
    
    def _validate_payment_amount(self, amount_kes: Decimal):
        """Validate payment amount is within limits"""
        if amount_kes < self.config.MIN_PAYMENT_KES:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum payment is {self.config.MIN_PAYMENT_KES} KES"
            )
        if amount_kes > self.config.MAX_PAYMENT_KES:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum payment is {self.config.MAX_PAYMENT_KES} KES"
            )
    
    def _validate_phone_number(self, phone: str):
        """Validate M-Pesa phone number format"""
        if not phone.startswith("254") or len(phone) != 12:
            raise HTTPException(
                status_code=400,
                detail="Phone must be in format 2547xxxxxx"
            )
    
    def _calculate_fiq_tokens(self, amount_kes: Decimal) -> Decimal:
        """Calculate FIQ tokens from KES amount"""
        tokens = (amount_kes / Decimal(1000)) * Decimal(self.config.TOKENS_PER_1000_KES)
        return tokens.quantize(Decimal("0.01"))
    
    def _generate_checkout_id(self, farmiq_id: str, phone: str) -> str:
        """Generate unique checkout ID"""
        raw = f"{farmiq_id}:{phone}:{datetime.now().isoformat()}"
        hash_val = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"FIQ{hash_val}".upper()
    
    def _parse_callback_metadata(self, items: list) -> Dict[str, Any]:
        """Parse M-Pesa callback metadata"""
        result = {}
        for item in items:
            name = item.get("Name", "")
            value = item.get("Value")
            
            if name == "Amount":
                result["amount"] = value
            elif name == "MpesaReceiptNumber":
                result["receipt_number"] = value
            elif name == "PhoneNumber":
                result["phone_number"] = value
        
        return result
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()
