"""
Afrika Talking USSD and SMS Gateway Service
Handles USSD menu interactions and bulk SMS delivery for farmers
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import aiohttp
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class USSDSessionStatus(str, Enum):
    """USSD session states"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


class SMSPriority(str, Enum):
    """SMS delivery priority"""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class USSDRequest:
    """USSD request from Afrika Talking"""
    phone_number: str
    text: str
    session_id: str
    network: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class SMSMessage:
    """SMS message to send via Afrika Talking"""
    phone_number: str
    message: str
    sender_id: str = "FarmIQ"
    priority: SMSPriority = SMSPriority.NORMAL
    scheduled_time: Optional[str] = None


class AfrikaTalkingService:
    """
    Handles all Afrika Talking operations:
    - USSD gateway integration
    - SMS sending (single and bulk)
    - Session management
    - Message acknowledgment
    """

    def __init__(self, api_key: str, username: str = "sandbox", base_url: str = "https://api.sandbox.africastalking.com"):
        self.api_key = api_key
        self.username = username
        self.base_url = base_url
        self.headers = {
            "Accept": "application/json",
            "Content-type": "application/x-www-form-urlencoded",
            "apiKey": api_key,
        }
        self.sms_url = f"{base_url}/version1/messaging"
        self.ussd_url = f"{base_url}/version1/ussd"
        self.session = None

    async def startup(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
        logger.info("Afrika Talking service initialized")

    async def shutdown(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
        logger.info("Afrika Talking service shutdown")

    async def send_sms(self, message: SMSMessage) -> Dict[str, Any]:
        """
        Send single SMS via Afrika Talking
        
        Args:
            message: SMSMessage with phone, text, sender_id
            
        Returns:
            {
                "success": bool,
                "message_id": str,
                "status": str,
                "timestamp": str
            }
        """
        try:
            payload = {
                "username": self.username,
                "to": message.phone_number,
                "message": message.message,
                "from": message.sender_id,
            }

            async with self.session.post(
                f"{self.sms_url}/send", headers=self.headers, data=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"SMS sent to {message.phone_number}: {result}")
                    return {
                        "success": True,
                        "message_id": result.get("SMSMessageData", [{}])[0].get("MessageId"),
                        "status": "sent",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    logger.error(f"SMS send failed: {result}")
                    return {
                        "success": False,
                        "error": result.get("error"),
                        "status": "failed",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
        except Exception as e:
            logger.error(f"Error sending SMS to {message.phone_number}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def send_bulk_sms(self, messages: List[SMSMessage]) -> Dict[str, Any]:
        """
        Send bulk SMS to multiple farmers
        
        Args:
            messages: List of SMSMessage objects
            
        Returns:
            {
                "total": int,
                "successful": int,
                "failed": int,
                "results": List[Dict]
            }
        """
        results = []
        successful = 0
        failed = 0

        # Process in batches of 100 (API limit)
        batch_size = 100
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            tasks = [self.send_sms(msg) for msg in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append(
                        {
                            "phone": batch[idx].phone_number,
                            "success": False,
                            "error": str(result),
                        }
                    )
                    failed += 1
                elif result.get("success"):
                    successful += 1
                else:
                    failed += 1
                results.append(result)

        logger.info(f"Bulk SMS sent: {successful}/{len(messages)} successful")
        return {
            "total": len(messages),
            "successful": successful,
            "failed": failed,
            "results": results,
        }

    async def send_ussd_response(self, phone_number: str, message: str, end_session: bool = False) -> Dict[str, Any]:
        """
        Send USSD response back to user
        
        Args:
            phone_number: User phone number
            message: USSD menu text to display
            end_session: Whether to end USSD session
            
        Returns:
            Response confirmation
        """
        try:
            payload = {
                "username": self.username,
                "sessionId": "",  # Set by Afrika Talking
                "phoneNumber": phone_number,
                "text": message,
                "endSession": "true" if end_session else "false",
            }

            async with self.session.post(
                f"{self.sms_url}/sendPrompt", headers=self.headers, data=payload, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                result = await response.json()

                if response.status == 200:
                    logger.info(f"USSD response sent to {phone_number}")
                    return {"success": True, "timestamp": datetime.utcnow().isoformat()}
                else:
                    logger.error(f"USSD response failed: {result}")
                    return {"success": False, "error": result}
        except Exception as e:
            logger.error(f"Error sending USSD response: {str(e)}")
            return {"success": False, "error": str(e)}

    async def parse_ussd_callback(self, request_data: Dict[str, Any]) -> USSDRequest:
        """
        Parse incoming USSD callback from Afrika Talking
        
        Request format from Afrika Talking:
        {
            'phoneNumber': '+254712345678',
            'text': '*500#',
            'sessionId': 'unique_session_id',
            'networkCode': '63902',
            ...
        }
        """
        phone = request_data.get("phoneNumber", "").lstrip("+")
        if not phone.startswith("254"):
            phone = f"254{phone.lstrip('0')}"

        return USSDRequest(
            phone_number=phone,
            text=request_data.get("text", ""),
            session_id=request_data.get("sessionId", ""),
            network=request_data.get("networkCode"),
            timestamp=request_data.get("timestamp"),
        )

    async def format_ussd_menu(
        self,
        options: List[tuple[str, str]],  # (number, option_text)
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> str:
        """
        Format USSD menu response
        
        Args:
            options: List of (number, text) tuples for menu items
            header: Menu title/header
            footer: Footer text or instruction
            
        Returns:
            Formatted USSD menu text
        """
        lines = []

        if header:
            lines.append(header)
            lines.append("-" * 30)

        for num, text in options:
            lines.append(f"{num}. {text}")

        if footer:
            lines.append("")
            lines.append(footer)

        # USSD text limit is typically 182 characters for single page
        menu_text = "\n".join(lines)
        return menu_text

    async def log_ussd_interaction(self, db: AsyncSession, phone_number: str, session_id: str, text: str, response: str, status: USSDSessionStatus):
        """
        Log USSD interaction for analytics and debugging
        """
        # Import here to avoid circular dependency
        from farmiq_backend.app.payments.models import USSDInteractionLog

        try:
            log_entry = USSDInteractionLog(
                phone_number=phone_number,
                session_id=session_id,
                user_input=text,
                system_response=response,
                status=status.value,
                timestamp=datetime.utcnow(),
            )
            db.add(log_entry)
            await db.commit()
        except Exception as e:
            logger.error(f"Error logging USSD interaction: {str(e)}")

    async def check_sms_balance(self) -> Dict[str, Any]:
        """
        Check SMS credit balance
        
        Returns:
            {
                "username": str,
                "balance": float,  # in KES
                "currency": str,
                "timestamp": str
            }
        """
        try:
            params = {"username": self.username}
            async with self.session.get(
                f"{self.sms_url}/querySMSDeliveryStatus",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                result = await response.json()

                if response.status == 200:
                    # Parse balance from response
                    balance_line = result.get("UserData")
                    return {
                        "username": self.username,
                        "balance": float(balance_line) if balance_line else 0,
                        "currency": "KES",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    logger.error(f"Balance check failed: {result}")
                    return {"success": False, "error": result}
        except Exception as e:
            logger.error(f"Error checking balance: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_sms_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get delivery status of sent SMS
        """
        try:
            params = {
                "username": self.username,
                "messageId": message_id,
            }
            async with self.session.get(
                f"{self.sms_url}/querySMSDeliveryStatus",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                result = await response.json()
                return result
        except Exception as e:
            logger.error(f"Error getting SMS status: {str(e)}")
            return {"success": False, "error": str(e)}


# Convenience functions
async def send_farmer_notification(
    service: AfrikaTalkingService, phone_number: str, message: str, priority: SMSPriority = SMSPriority.NORMAL
) -> Dict[str, Any]:
    """Send notification SMS to farmer"""
    msg = SMSMessage(phone_number=phone_number, message=message, priority=priority)
    return await service.send_sms(msg)


async def send_bulk_farmer_notifications(
    service: AfrikaTalkingService, phone_numbers: List[str], message: str, priority: SMSPriority = SMSPriority.NORMAL
) -> Dict[str, Any]:
    """Send bulk notification SMS to multiple farmers"""
    messages = [SMSMessage(phone_number=phone, message=message, priority=priority) for phone in phone_numbers]
    return await service.send_bulk_sms(messages)
