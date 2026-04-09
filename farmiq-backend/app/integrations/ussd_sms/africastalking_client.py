"""
Africa's Talking API Client - Wrapper for USSD, SMS, and other services
"""

import hashlib
import hmac
import httpx
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class AfricasTalkingEnvironment(str, Enum):
    """Africa's Talking environments"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class AfricasTalkingClient:
    """
    Unified client for Africa's Talking API
    Handles authentication, signature validation, and API calls
    """
    
    def __init__(
        self,
        username: str,
        api_key: str,
        environment: AfricasTalkingEnvironment = AfricasTalkingEnvironment.SANDBOX
    ):
        """
        Initialize Africa's Talking client
        
        Args:
            username: Africa's Talking username (e.g., 'sandbox')
            api_key: Africa's Talking API key
            environment: Sandbox or production
        """
        self.username = username
        self.api_key = api_key
        self.environment = environment
        
        # Set base URLs
        if environment == AfricasTalkingEnvironment.SANDBOX:
            self.base_url = "https://api.sandbox.africastalking.com"
        else:
            self.base_url = "https://api.africastalking.com"
        
        logger.info(f"Africa's Talking client initialized: {username} ({environment})")
    
    async def send_sms(
        self,
        recipients: List[str],
        message: str,
        sender_id: str,
        enqueue: int = 1
    ) -> Dict[str, Any]:
        """
        Send SMS message
        
        Args:
            recipients: List of phone numbers (international format)
            message: SMS content
            sender_id: Sender ID or shortcode
            enqueue: Queue if busy (1=yes, 0=no)
            
        Returns:
            API response dictionary
        """
        
        try:
            endpoint = f"{self.base_url}/version1/messaging"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "username": self.username,
                "api_key": self.api_key,
                "recipients": ",".join(recipients),
                "message": message,
                "sender_id": sender_id,
                "enqueue": enqueue,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, headers=headers, data=data, timeout=30.0)
                
                logger.info(f"SMS API response: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"SMS API error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"SMS error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def fetch_sms(self, last_received_id: int = 0) -> Dict[str, Any]:
        """
        Fetch incoming SMS messages
        
        Args:
            last_received_id: Last message ID fetched
            
        Returns:
            API response with messages
        """
        
        try:
            endpoint = f"{self.base_url}/version1/messaging"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "username": self.username,
                "api_key": self.api_key,
                "lastReceivedId": last_received_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, headers=headers, data=data, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Fetch SMS error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Fetch SMS error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def send_ussd(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send USSD push (USSD Initiation Service)
        
        Args:
            phone_number: Recipient phone number
            message: USSD message content
            
        Returns:
            API response
        """
        
        try:
            endpoint = f"{self.base_url}/version1/ussd/send"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "username": self.username,
                "api_key": self.api_key,
                "phoneNumber": phone_number,
                "message": message,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, headers=headers, data=data, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"USSD send error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"USSD send error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def validate_webhook_signature(
        self,
        request_body: str,
        signature: str
    ) -> bool:
        """
        Validate webhook signature from Africa's Talking
        
        Args:
            request_body: Raw request body
            signature: Signature header value
            
        Returns:
            True if signature is valid
        """
        
        try:
            # Compute HMAC-SHA256
            computed_signature = hmac.new(
                self.api_key.encode(),
                request_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant-time comparison)
            is_valid = hmac.compare_digest(computed_signature, signature)
            
            if is_valid:
                logger.debug("Webhook signature valid")
            else:
                logger.warning("Webhook signature invalid")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Signature validation error: {str(e)}", exc_info=True)
            return False
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information
        
        Returns:
            Account info including balance, credits, etc.
        """
        
        try:
            endpoint = f"{self.base_url}/version1/user"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "username": self.username,
                "api_key": self.api_key,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=headers, params=data, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Account info error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Account info error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def get_airtime_topup_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Check airtime topup status
        
        Args:
            transaction_id: Topup transaction ID
            
        Returns:
            Status response
        """
        
        try:
            endpoint = f"{self.base_url}/version1/airtime/status"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "username": self.username,
                "api_key": self.api_key,
                "transactionId": transaction_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, headers=headers, data=data, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Airtime status error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Airtime status error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def topup_airtime(
        self,
        phone_number: str,
        amount: float,
        currency_code: str = "KES"
    ) -> Dict[str, Any]:
        """
        Send airtime topup to phone number
        
        Args:
            phone_number: Recipient phone number
            amount: Amount to topup
            currency_code: Currency code (e.g., KES, UGX, GHS)
            
        Returns:
            API response with transaction details
        """
        
        try:
            endpoint = f"{self.base_url}/version1/airtime/send"
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "username": self.username,
                "api_key": self.api_key,
                "recipients": f"{phone_number},{amount}",
                "currencyCode": currency_code,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, headers=headers, data=data, timeout=30.0)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Airtime topup error: {response.text}")
                    return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Airtime topup error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def get_balance(self) -> Optional[float]:
        """
        Get remaining SMS balance/credits
        
        Returns:
            Balance as float, or None on error
        """
        
        try:
            info = await self.get_account_info()
            
            if "error" in info:
                logger.error(f"Error fetching balance: {info['error']}")
                return None
            
            # Extract balance (format: "KES X.XXXX")
            if "UserData" in info:
                balance_str = info["UserData"].get("balance", "")
                try:
                    balance = float(balance_str.split()[-1])
                    return balance
                except (IndexError, ValueError):
                    pass
            
            return None
        
        except Exception as e:
            logger.error(f"Balance error: {str(e)}", exc_info=True)
            return None
