"""
M-Pesa Service - High-level orchestration for M-Pesa operations
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from app.integrations.mpesa.daraja_client import DarajaClient, DarajaEnvironment
from app.integrations.mpesa.schemas import (
    StkPushRequest,
    ReversalRequest,
    TaxRemittanceRequest,
    TransactionStatusRequest,
    MpesaTransactionRecord,
    MpesaReversalRecord,
    MpesaTaxRecord,
)

logger = logging.getLogger(__name__)


class MpesaService:
    """
    High-level M-Pesa service for token purchases and transactions
    """
    
    def __init__(
        self,
        daraja_client: DarajaClient,
        db_pool
    ):
        """
        Initialize M-Pesa service
        
        Args:
            daraja_client: Initialized Daraja API client
            db_pool: Database connection pool
        """
        self.daraja = daraja_client
        self.db_pool = db_pool
    
    async def initiate_token_purchase(
        self,
        user_id: str,
        phone_number: str,
        fiq_amount: int,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Initiate FIQ token purchase via M-Pesa STK Push
        
        Args:
            user_id: FarmIQ user ID
            phone_number: User phone number
            fiq_amount: FIQ tokens to purchase
            callback_url: M-Pesa callback URL
            
        Returns:
            {
                "success": bool,
                "message": str,
                "request_id": str,
                "checkout_request_id": str,
                "merchant_request_id": str,
                "amount_kes": float
            }
        """
        
        try:
            # Calculate KES amount (1 FIQ = 1.5 KES by default)
            fiq_to_kes_rate = 1.5
            amount_kes = fiq_amount * fiq_to_kes_rate
            
            # Validate minimum and maximum amounts
            MIN_KES = 50
            MAX_KES = 150000
            
            if amount_kes < MIN_KES:
                return {
                    "success": False,
                    "error": f"Minimum amount is {MIN_KES} KES",
                }
            
            if amount_kes > MAX_KES:
                return {
                    "success": False,
                    "error": f"Maximum amount is {MAX_KES} KES",
                }
            
            # Generate request ID
            request_id = f"FIQ-{user_id[:8]}-{uuid.uuid4().hex[:12].upper()}"
            
            logger.info(f"Initiating token purchase: {request_id} - {fiq_amount} FIQ ({amount_kes} KES)")
            
            # Call M-Pesa STK Push
            stk_response = await self.daraja.initiate_stk_push(
                phone_number=phone_number,
                amount=amount_kes,
                account_reference=f"{fiq_amount}FIQ",
                transaction_desc="FarmIQ Tokens",
                callback_url=callback_url
            )
            
            if "error" in stk_response:
                logger.error(f"STK Push failed: {stk_response.get('error')}")
                return {
                    "success": False,
                    "error": stk_response.get("error"),
                }
            
            # Extract M-Pesa identifiers
            merchant_request_id = stk_response.get("MerchantRequestID")
            checkout_request_id = stk_response.get("CheckoutRequestID")
            response_code = stk_response.get("ResponseCode")
            
            # Log transaction to database
            await self._log_transaction(
                db_pool=self.db_pool,
                request_id=request_id,
                user_id=user_id,
                phone_number=phone_number,
                transaction_type="stk_push",
                amount_kes=amount_kes,
                fiq_amount=fiq_amount,
                merchant_request_id=merchant_request_id,
                checkout_request_id=checkout_request_id,
                response_code=response_code,
                raw_response=stk_response
            )
            
            if response_code == "0":
                return {
                    "success": True,
                    "message": stk_response.get("CustomerMessage", "STK Push sent successfully"),
                    "request_id": request_id,
                    "checkout_request_id": checkout_request_id,
                    "merchant_request_id": merchant_request_id,
                    "amount_kes": amount_kes,
                }
            else:
                return {
                    "success": False,
                    "error": stk_response.get("ResponseDescription", "STK Push failed"),
                }
        
        except Exception as e:
            logger.error(f"Token purchase error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def check_payment_status(
        self,
        checkout_request_id: str
    ) -> Dict[str, Any]:
        """
        Check payment status of STK Push request
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
            
        Returns:
            Status information
        """
        
        try:
            logger.info(f"Checking payment status: {checkout_request_id}")
            
            response = await self.daraja.query_stk_push_status(checkout_request_id)
            
            if "error" in response:
                logger.error(f"Status check failed: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                }
            
            result_code = response.get("ResultCode")
            result_desc = response.get("ResultDesc", "")
            
            # Map result code to status
            status = "unknown"
            if result_code == 0:
                status = "completed"
            elif result_code == 1032:
                status = "cancelled"
            else:
                status = "failed"
            
            return {
                "success": True,
                "checkout_request_id": checkout_request_id,
                "status": status,
                "result_code": result_code,
                "result_description": result_desc,
                "raw_response": response,
            }
        
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_account_balance(
        self,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str
    ) -> Dict[str, Any]:
        """
        Query M-Pesa account balance
        
        Args:
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            
        Returns:
            Balance information
        """
        
        try:
            logger.info("Querying account balance")
            
            response = await self.daraja.get_account_balance(
                initiator_name=initiator_name,
                initiator_password=initiator_password,
                queue_timeout_url=queue_timeout_url,
                result_url=result_url
            )
            
            if "error" in response:
                logger.error(f"Balance query failed: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                }
            
            return {
                "success": True,
                "response_code": response.get("ResponseCode"),
                "conversation_id": response.get("ConversationID"),
                "raw_response": response,
            }
        
        except Exception as e:
            logger.error(f"Balance query error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def query_transaction_status(
        self,
        transaction_id: str,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str
    ) -> Dict[str, Any]:
        """
        Query specific transaction status
        
        Args:
            transaction_id: M-Pesa receipt number
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            
        Returns:
            Transaction status
        """
        
        try:
            logger.info(f"Querying transaction status: {transaction_id}")
            
            response = await self.daraja.query_transaction_status(
                transaction_id=transaction_id,
                initiator_name=initiator_name,
                initiator_password=initiator_password,
                queue_timeout_url=queue_timeout_url,
                result_url=result_url
            )
            
            if "error" in response:
                logger.error(f"Transaction query failed: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                }
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "result_code": response.get("ResultCode"),
                "result_desc": response.get("ResultDesc"),
                "raw_response": response,
            }
        
        except Exception as e:
            logger.error(f"Transaction query error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def reverse_transaction(
        self,
        transaction_id: str,
        amount: float,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str,
        user_id: Optional[str] = None,
        reason: str = "Reversal"
    ) -> Dict[str, Any]:
        """
        Reverse M-Pesa transaction
        
        Args:
            transaction_id: M-Pesa receipt to reverse
            amount: Amount to reverse
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            user_id: FarmIQ user ID
            reason: Reversal reason
            
        Returns:
            Reversal response
        """
        
        try:
            # Generate request ID
            request_id = f"REV-{uuid.uuid4().hex[:16].upper()}"
            
            logger.info(f"Initiating reversal: {request_id} - {transaction_id} ({amount} KES)")
            
            response = await self.daraja.reverse_transaction(
                transaction_id=transaction_id,
                amount=amount,
                initiator_name=initiator_name,
                initiator_password=initiator_password,
                queue_timeout_url=queue_timeout_url,
                result_url=result_url,
                remarks=reason[:100]
            )
            
            if "error" in response:
                logger.error(f"Reversal failed: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                    "request_id": request_id,
                }
            
            # Log reversal request
            await self._log_reversal(
                db_pool=self.db_pool,
                request_id=request_id,
                original_transaction_id=transaction_id,
                amount=amount,
                user_id=user_id,
                response=response
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "transaction_id": transaction_id,
                "conversation_id": response.get("ConversationID"),
                "raw_response": response,
            }
        
        except Exception as e:
            logger.error(f"Reversal error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def remit_tax(
        self,
        prn: str,
        amount: float,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str,
        tax_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remit taxes to KRA
        
        Args:
            prn: Payment Registration Number from KRA
            amount: Tax amount in KES
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            tax_period: Tax reporting period
            
        Returns:
            Tax remittance response
        """
        
        try:
            request_id = f"TAX-{uuid.uuid4().hex[:16].upper()}"
            
            logger.info(f"Initiating tax remittance: {request_id} - {prn} ({amount} KES)")
            
            response = await self.daraja.remit_tax(
                sender_shortcode=self.daraja.business_shortcode,
                receiver_shortcode="572572",  # KRA shortcode
                amount=amount,
                prn=prn,
                initiator_name=initiator_name,
                initiator_password=initiator_password,
                queue_timeout_url=queue_timeout_url,
                result_url=result_url,
                remarks=f"Tax Remittance - PRN: {prn}"
            )
            
            if "error" in response:
                logger.error(f"Tax remittance failed: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                    "request_id": request_id,
                }
            
            # Log tax remittance
            await self._log_tax_remittance(
                db_pool=self.db_pool,
                request_id=request_id,
                prn=prn,
                amount=amount,
                tax_period=tax_period,
                response=response
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "prn": prn,
                "conversation_id": response.get("ConversationID"),
                "raw_response": response,
            }
        
        except Exception as e:
            logger.error(f"Tax remittance error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _log_transaction(
        self,
        db_pool,
        request_id: str,
        user_id: str,
        phone_number: str,
        transaction_type: str,
        amount_kes: float,
        fiq_amount: int,
        merchant_request_id: str,
        checkout_request_id: str,
        response_code: str,
        raw_response: Dict[str, Any]
    ) -> None:
        """Log transaction to database"""
        
        try:
            db = await db_pool.acquire()
            try:
                query = """
                INSERT INTO mpesa_transactions (
                    request_id, user_id, phone_number, transaction_type,
                    amount, fiq_amount_minted, merchant_request_id,
                    checkout_request_id, result_code, status, raw_response
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11);
                """
                
                status = "pending" if response_code == "0" else "failed"
                
                await db.execute(
                    query,
                    request_id,
                    user_id,
                    phone_number,
                    transaction_type,
                    amount_kes,
                    fiq_amount,
                    merchant_request_id,
                    checkout_request_id,
                    0 if response_code == "0" else 1,
                    status,
                    raw_response
                )
                
                logger.info(f"Transaction logged: {request_id}")
            
            finally:
                await db_pool.release(db)
        
        except Exception as e:
            logger.error(f"Error logging transaction: {str(e)}")
    
    async def _log_reversal(
        self,
        db_pool,
        request_id: str,
        original_transaction_id: str,
        amount: float,
        user_id: Optional[str],
        response: Dict[str, Any]
    ) -> None:
        """Log reversal to database"""
        
        try:
            db = await db_pool.acquire()
            try:
                query = """
                INSERT INTO mpesa_reversal_requests (
                    request_id, original_transaction_id, reversal_amount,
                    user_id, conversation_id, originator_conversation_id,
                    status, raw_response
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
                """
                
                await db.execute(
                    query,
                    request_id,
                    original_transaction_id,
                    amount,
                    user_id,
                    response.get("ConversationID"),
                    response.get("OriginatorConversationID"),
                    "pending",
                    response
                )
                
                logger.info(f"Reversal logged: {request_id}")
            
            finally:
                await db_pool.release(db)
        
        except Exception as e:
            logger.error(f"Error logging reversal: {str(e)}")
    
    async def _log_tax_remittance(
        self,
        db_pool,
        request_id: str,
        prn: str,
        amount: float,
        tax_period: Optional[str],
        response: Dict[str, Any]
    ) -> None:
        """Log tax remittance to database"""
        
        try:
            db = await db_pool.acquire()
            try:
                query = """
                INSERT INTO mpesa_tax_remittances (
                    request_id, prn, tax_amount, tax_period,
                    sender_shortcode, receiver_shortcode,
                    conversation_id, originator_conversation_id,
                    status, raw_response
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);
                """
                
                await db.execute(
                    query,
                    request_id,
                    prn,
                    amount,
                    tax_period,
                    self.daraja.business_shortcode,
                    "572572",  # KRA
                    response.get("ConversationID"),
                    response.get("OriginatorConversationID"),
                    "pending",
                    response
                )
                
                logger.info(f"Tax remittance logged: {request_id}")
            
            finally:
                await db_pool.release(db)
        
        except Exception as e:
            logger.error(f"Error logging tax remittance: {str(e)}")
