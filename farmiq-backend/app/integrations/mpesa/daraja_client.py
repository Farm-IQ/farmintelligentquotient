"""
M-Pesa Daraja API Client - Core authentication and API interactions
"""

import base64
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DarajaEnvironment(str, Enum):
    """M-Pesa Daraja environments"""
    SANDBOX = "https://sandbox.safaricom.co.ke"
    PRODUCTION = "https://api.safaricom.co.ke"


class DarajaClient:
    """
    Unified M-Pesa Daraja API client
    Handles authentication, STK Push, payments, reversals, tax remittance, etc.
    """
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        business_shortcode: str,
        passkey: str,
        environment: DarajaEnvironment = DarajaEnvironment.SANDBOX
    ):
        """
        Initialize Daraja client
        
        Args:
            consumer_key: M-Pesa Daraja consumer key
            consumer_secret: M-Pesa Daraja consumer secret
            business_shortcode: Business shortcode (5-7 digits)
            passkey: M-Pesa passkey for STK Push
            environment: Sandbox or production
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.business_shortcode = business_shortcode
        self.passkey = passkey
        self.base_url = environment
        
        # Token caching
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        logger.info(f"Daraja client initialized: {business_shortcode} ({environment})")
    
    async def get_access_token(self) -> str:
        """
        Get OAuth access token
        
        Returns:
            Access token valid for 3599 seconds
            
        Raises:
            Exception if authentication fails
        """
        
        try:
            # Check if token is still valid
            if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
                logger.debug("Using cached access token")
                return self.access_token
            
            # Get new token
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create Basic auth header
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                
                if response.status_code != 200:
                    logger.error(f"Auth error: {response.status_code} - {response.text}")
                    raise Exception(f"Authentication failed: {response.text}")
                
                data = response.json()
                
                self.access_token = data["access_token"]
                expires_in = int(data.get("expires_in", 3599))
                
                # Store expiry with 60-second buffer
                self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                
                logger.info(f"Token obtained, expires in {expires_in}s")
                
                return self.access_token
        
        except Exception as e:
            logger.error(f"Token fetch error: {str(e)}", exc_info=True)
            raise
    
    async def initiate_stk_push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Initiate STK Push (M-Pesa Express)
        
        Args:
            phone_number: Customer phone in format 254712345678
            amount: Transaction amount in KES
            account_reference: Account reference (max 12 chars)
            transaction_desc: Transaction description (max 13 chars)
            callback_url: Callback URL for results
            
        Returns:
            Response with CheckoutRequestID and MerchantRequestID
        """
        
        try:
            # Get token
            token = await self.get_access_token()
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Generate password
            password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_string.encode()).decode()
            
            # Prepare request
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": account_reference[:12],  # Max 12 chars
                "TransactionDesc": transaction_desc[:13],     # Max 13 chars
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                logger.info(f"STK Push response: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"STK Push error: {response.text}")
                    return {"error": response.text, "status_code": response.status_code}
        
        except Exception as e:
            logger.error(f"STK Push error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def query_stk_push_status(
        self,
        checkout_request_id: str
    ) -> Dict[str, Any]:
        """
        Query STK Push request status
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
            
        Returns:
            Status response with ResultCode and ResultDesc
        """
        
        try:
            token = await self.get_access_token()
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_string.encode()).decode()
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"STK Query error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"STK Query error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def get_account_balance(
        self,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str
    ) -> Dict[str, Any]:
        """
        Query account balance
        
        Args:
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password (plain text - encrypted by this method)
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            
        Returns:
            Balance response
        """
        
        try:
            token = await self.get_access_token()
            
            # Encrypt password
            security_credential = self._encrypt_credential(initiator_password)
            
            url = f"{self.base_url}/mpesa/accountbalance/v1/query"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "CommandID": "AccountBalance",
                "PartyA": self.business_shortcode,
                "IdentifierType": 4,  # Organization shortcode
                "Remarks": "Account Balance Query",
                "Initiator": initiator_name,
                "SecurityCredential": security_credential,
                "QueueTimeOutURL": queue_timeout_url,
                "ResultURL": result_url,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Balance query error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Balance query error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def query_transaction_status(
        self,
        transaction_id: str,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str,
        original_conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query transaction status
        
        Args:
            transaction_id: M-Pesa receipt number
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password (plain text)
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            original_conversation_id: Optional original conversation ID
            
        Returns:
            Transaction status response
        """
        
        try:
            token = await self.get_access_token()
            
            security_credential = self._encrypt_credential(initiator_password)
            
            url = f"{self.base_url}/mpesa/transactionstatus/v1/query"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "CommandID": "TransactionStatusQuery",
                "PartyA": self.business_shortcode,
                "IdentifierType": 4,  # Organization shortcode
                "Remarks": "Transaction Status Query",
                "Initiator": initiator_name,
                "SecurityCredential": security_credential,
                "TransactionID": transaction_id,
                "QueueTimeOutURL": queue_timeout_url,
                "ResultURL": result_url,
            }
            
            if original_conversation_id:
                payload["OriginalConversationID"] = original_conversation_id
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Transaction status error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Transaction status error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def reverse_transaction(
        self,
        transaction_id: str,
        amount: float,
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str,
        remarks: str = "Transaction Reversal"
    ) -> Dict[str, Any]:
        """
        Reverse M-Pesa transaction
        
        Args:
            transaction_id: M-Pesa receipt number to reverse
            amount: Amount to reverse
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password (plain text)
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            remarks: Reversal remarks
            
        Returns:
            Reversal response with TransactionID
        """
        
        try:
            token = await self.get_access_token()
            
            security_credential = self._encrypt_credential(initiator_password)
            
            url = f"{self.base_url}/mpesa/reversal/v1/request"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "CommandID": "TransactionReversal",
                "PartyA": self.business_shortcode,
                "RecieverParty": self.business_shortcode,
                "ReceiverIdentifierType": 11,  # Organization
                "Initiator": initiator_name,
                "SecurityCredential": security_credential,
                "Amount": int(amount),
                "Remarks": remarks[:100],
                "QueueTimeOutURL": queue_timeout_url,
                "ResultURL": result_url,
                "TransactionID": transaction_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Reversal error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Reversal error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def remit_tax(
        self,
        sender_shortcode: str,
        receiver_shortcode: str,
        amount: float,
        prn: str,  # Payment Registration Number
        initiator_name: str,
        initiator_password: str,
        queue_timeout_url: str,
        result_url: str,
        remarks: str = "Tax Remittance to KRA"
    ) -> Dict[str, Any]:
        """
        Remit taxes to KRA
        
        Args:
            sender_shortcode: Your shortcode
            receiver_shortcode: KRA shortcode (usually 572572)
            amount: Tax amount in KES
            prn: KRA Payment Registration Number
            initiator_name: M-Pesa initiator username
            initiator_password: M-Pesa initiator password (plain text)
            queue_timeout_url: URL for timeout notifications
            result_url: URL for result notifications
            remarks: Tax remittance description
            
        Returns:
            Tax remittance response
        """
        
        try:
            token = await self.get_access_token()
            
            security_credential = self._encrypt_credential(initiator_password)
            
            url = f"{self.base_url}/mpesa/b2b/v1/remittax"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "CommandID": "PayTaxToKRA",
                "SenderIdentifierType": 4,  # Organization shortcode
                "PartyA": sender_shortcode,
                "PartyB": receiver_shortcode,  # KRA shortcode
                "ReceiverIdentifierType": 4,
                "Amount": int(amount),
                "AccountReference": prn,
                "Remarks": remarks[:100],
                "Initiator": initiator_name,
                "SecurityCredential": security_credential,
                "QueueTimeOutURL": queue_timeout_url,
                "ResultURL": result_url,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Tax remittance error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Tax remittance error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _encrypt_credential(self, password: str) -> str:
        """
        Encrypt credential using base64 (M-Pesa requirement)
        
        Args:
            password: Plain text password
            
        Returns:
            Base64 encoded password
        """
        try:
            return base64.b64encode(password.encode()).decode()
        except Exception as e:
            logger.error(f"Credential encryption error: {str(e)}")
            raise
