"""
M-Pesa Token Purchase Service
Handles Safaricom Daraja API integration for token purchases
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from requests.auth import HTTPBasicAuth
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...config.settings import settings
from ...core.database import get_db
from ...core.structured_logging import log_event
from ...core.cache import get_cache, CacheKeyNamespace

logger = logging.getLogger(__name__)


class MpesaService:
    """Handle M-Pesa token purchase transactions"""

    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.business_shortcode = settings.MPESA_BUSINESS_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.api_url = settings.MPESA_API_URL
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.min_amount = settings.MPESA_MIN_AMOUNT
        self.max_amount = settings.MPESA_MAX_AMOUNT
        self.fiq_to_kes_rate = settings.MPESA_FIQ_TO_KES_RATE
        self.cache = get_cache()

    def get_access_token(self) -> str:
        """Get M-Pesa OAuth access token (cached for ~1 hour)"""
        try:
            # Check cache first
            cached_token = self.cache.get(CacheKeyNamespace.MPESA_TOKEN, "daraja_oauth")
            if cached_token:
                logger.debug("Using cached M-Pesa access token")
                return cached_token
            
            # Get new token from API
            url = f"{self.api_url}/oauth/v1/generate?grant_type=client_credentials"
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                timeout=10
            )
            response.raise_for_status()
            
            token_response = response.json()
            access_token = token_response.get('access_token')
            
            # Cache token for 3500 seconds (just under 1 hour before expiry)
            self.cache.set(
                CacheKeyNamespace.MPESA_TOKEN,
                "daraja_oauth",
                access_token,
                ttl_seconds=3500
            )
            
            log_event("mpesa_token_obtained", {
                "timestamp": datetime.now().isoformat(),
                "token_length": len(access_token) if access_token else 0,
                "cached": True
            })
            
            return access_token
            
        except requests.exceptions.RequestException as e:
            log_event("mpesa_token_error", {
                "error": str(e),
                "url": url
            })
            raise HTTPException(status_code=500, detail="Failed to obtain M-Pesa access token")

    def initiate_stk_push(
        self,
        phone_number: str,
        amount: int,
        account_reference: str,
        transaction_desc: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Initiate STK push for M-Pesa payment
        
        Args:
            phone_number: Customer phone number (254XXXXXXXXX format)
            amount: Amount in KES
            account_reference: Unique transaction reference
            transaction_desc: Transaction description
            user_id: FarmIQ user ID
            
        Returns:
            Dictionary with checkout request ID and response details
        """
        try:
            # Validate inputs
            if not self._validate_phone_number(phone_number):
                raise ValueError("Invalid phone number format")
            
            if not self._validate_amount(amount):
                raise ValueError(f"Amount must be between {self.min_amount} and {self.max_amount} KES")

            # Get access token
            access_token = self.get_access_token()
            
            # Prepare timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Generate password
            password = self._generate_password(timestamp)
            
            # Prepare request payload
            url = f"{self.api_url}/mpesa/stkpush/v1/processrequest"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallbackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            log_event("mpesa_stk_initiated", {
                "user_id": user_id,
                "phone_number": self._mask_phone(phone_number),
                "amount": amount,
                "checkout_request_id": response_data.get("CheckoutRequestID"),
                "response_code": response_data.get("ResponseCode")
            })
            
            return {
                "success": response_data.get("ResponseCode") == "0",
                "checkout_request_id": response_data.get("CheckoutRequestID"),
                "request_id": response_data.get("RequestId"),
                "response_code": response_data.get("ResponseCode"),
                "response_description": response_data.get("ResponseDescription")
            }
            
        except requests.exceptions.RequestException as e:
            log_event("mpesa_stk_error", {
                "user_id": user_id,
                "error": str(e),
                "phone_number": self._mask_phone(phone_number)
            })
            raise HTTPException(status_code=500, detail="Failed to initiate M-Pesa payment")

    def query_stk_status(
        self,
        checkout_request_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Query the status of an STK push request
        
        Args:
            checkout_request_id: The checkout request ID from initiate_stk_push
            user_id: FarmIQ user ID
            
        Returns:
            Dictionary with transaction status
        """
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self._generate_password(timestamp)
            
            url = f"{self.api_url}/mpesa/stkpushquery/v1/query"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            log_event("mpesa_query_status", {
                "user_id": user_id,
                "checkout_request_id": checkout_request_id,
                "result_code": response_data.get("ResultCode")
            })
            
            return {
                "result_code": response_data.get("ResultCode"),
                "result_desc": response_data.get("ResultDesc"),
                "merchant_request_id": response_data.get("MerchantRequestID"),
                "checkout_request_id": response_data.get("CheckoutRequestID")
            }
            
        except requests.exceptions.RequestException as e:
            log_event("mpesa_query_error", {
                "user_id": user_id,
                "checkout_request_id": checkout_request_id,
                "error": str(e)
            })
            raise HTTPException(status_code=500, detail="Failed to query M-Pesa status")

    def verify_callback_signature(
        self,
        callback_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """
        Verify M-Pesa callback signature
        
        Args:
            callback_data: The callback data from M-Pesa
            signature: Optional signature for verification
            
        Returns:
            True if signature is valid
        """
        # For now, we'll trust Safaricom's HTTPS connection
        # In production, implement full signature verification
        return True

    def process_callback(
        self,
        callback_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Process M-Pesa callback
        
        Args:
            callback_data: The callback data from M-Pesa
            db: Database session
            
        Returns:
            Processing result
        """
        try:
            # Extract key data
            body = callback_data.get("Body", {})
            stk_callback = body.get("stkCallback", {})
            
            merchant_request_id = stk_callback.get("MerchantRequestID")
            checkout_request_id = stk_callback.get("CheckoutRequestID")
            result_code = stk_callback.get("ResultCode")
            result_desc = stk_callback.get("ResultDesc")
            
            # Extract callback metadata
            callback_metadata = stk_callback.get("CallbackMetadata", {})
            items = callback_metadata.get("Item", [])
            
            transaction_details = {}
            for item in items:
                item_name = item.get("Name")
                item_value = item.get("Value")
                transaction_details[item_name] = item_value
            
            log_event("mpesa_callback_received", {
                "checkout_request_id": checkout_request_id,
                "result_code": result_code,
                "result_desc": result_desc
            })
            
            # Process based on result code
            if result_code == 0:
                # Payment successful
                return self._handle_successful_payment(
                    transaction_details,
                    checkout_request_id,
                    db
                )
            else:
                # Payment failed
                return self._handle_failed_payment(
                    result_code,
                    result_desc,
                    checkout_request_id,
                    db
                )
                
        except Exception as e:
            log_event("mpesa_callback_error", {
                "error": str(e)
            })
            raise HTTPException(status_code=500, detail="Failed to process M-Pesa callback")

    def _handle_successful_payment(
        self,
        transaction_details: Dict[str, Any],
        checkout_request_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle successful payment"""
        amount = transaction_details.get("Amount", 0)
        phone_number = transaction_details.get("PhoneNumber")
        mpesa_receipt = transaction_details.get("MpesaReceiptNumber")
        
        # Calculate FIQ tokens (convert KES to FIQ)
        fiq_amount = amount / self.fiq_to_kes_rate
        
        log_event("mpesa_payment_success", {
            "amount": amount,
            "fiq_amount": fiq_amount,
            "mpesa_receipt": mpesa_receipt,
            "phone_number": self._mask_phone(phone_number)
        })
        
        return {
            "status": "success",
            "checkout_request_id": checkout_request_id,
            "amount": amount,
            "fiq_amount": fiq_amount,
            "mpesa_receipt": mpesa_receipt
        }

    def _handle_failed_payment(
        self,
        result_code: int,
        result_desc: str,
        checkout_request_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle failed payment"""
        log_event("mpesa_payment_failed", {
            "result_code": result_code,
            "result_desc": result_desc,
            "checkout_request_id": checkout_request_id
        })
        
        return {
            "status": "failed",
            "checkout_request_id": checkout_request_id,
            "result_code": result_code,
            "result_desc": result_desc
        }

    @staticmethod
    def _validate_phone_number(phone_number: str) -> bool:
        """Validate phone number format (254XXXXXXXXX)"""
        if not phone_number.startswith("254"):
            return False
        if len(phone_number) != 12:
            return False
        return phone_number.isdigit()

    def _validate_amount(self, amount: int) -> bool:
        """Validate payment amount"""
        return self.min_amount <= amount <= self.max_amount

    def _generate_password(self, timestamp: str) -> str:
        """Generate M-Pesa password"""
        import base64
        data = f"{self.business_shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(data.encode()).decode()

    @staticmethod
    def _mask_phone(phone_number: str) -> str:
        """Mask phone number for logging"""
        if len(phone_number) >= 4:
            return f"***{phone_number[-4:]}"
        return "***MASKED"


# Create singleton instance
mpesa_service = MpesaService()
