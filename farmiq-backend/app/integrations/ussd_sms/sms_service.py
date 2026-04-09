"""
SMS Service - Handles sending and receiving SMS via Africa's Talking
"""

from typing import Optional, Dict, Any, List
import logging
import httpx
import json
from datetime import datetime
import asyncio
from sqlalchemy import text

from core.db_pool import DatabasePool

logger = logging.getLogger(__name__)


class SMSService:
    """Service to manage SMS operations via Africa's Talking"""
    
    def __init__(self, api_key: str, username: str, environment: str = "sandbox"):
        self.api_key = api_key
        self.username = username
        self.environment = environment
        
        # Set API endpoints based on environment
        if environment == "sandbox":
            self.api_url = "https://api.sandbox.africastalking.com/version1/messaging"
        else:
            self.api_url = "https://api.africastalking.com/version1/messaging"
    
    async def send_sms(
        self,
        recipients: List[str],
        message: str,
        sender_id: str
    ) -> Dict[str, Any]:
        """
        Send SMS to multiple recipients
        
        Args:
            recipients: List of phone numbers in international format (e.g., +254712345678)
            message: SMS message content
            sender_id: Sender ID or shortcode
            
        Returns:
            {
                "success": bool,
                "message": str,
                "recipients": List[Dict],
                "message_ids": List[str],
                "total_cost": float,
                "error": Optional[str]
            }
        """
        
        try:
            # Validate inputs
            if not recipients:
                raise ValueError("Recipients list cannot be empty")
            
            if len(message) == 0:
                raise ValueError("Message cannot be empty")
            
            if len(message) > 160:
                logger.warning(f"Message exceeds 160 characters, will be split into multiple SMS")
            
            logger.info(f"Sending SMS to {len(recipients)} recipients")
            
            # Prepare request
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            params = {
                "username": self.username,
                "api_key": self.api_key,
                "recipients": ",".join(recipients),
                "message": message,
                "sender_id": sender_id,
                "enqueue": 1,  # Queue if busy
            }
            
            # Make API call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    data=params,
                    timeout=30.0
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"SMS API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                    }
                
                # Parse response
                response_data = response.json()
                sms_data = response_data.get("SMSMessageData", {})
                
                recipients_list = sms_data.get("Recipients", [])
                message_ids = []
                total_cost = 0
                
                # Extract message IDs and costs
                for recipient in recipients_list:
                    if recipient.get("messageId"):
                        message_ids.append(recipient["messageId"])
                    
                    # Parse cost (format: "KES 0.8000")
                    cost_str = recipient.get("cost", "KES 0")
                    try:
                        cost_value = float(cost_str.split()[-1])
                        total_cost += cost_value
                    except (IndexError, ValueError):
                        pass
                
                # Log to database
                await self._log_sms_send(
                    recipients,
                    message,
                    sender_id,
                    message_ids,
                    total_cost
                )
                
                logger.info(f"SMS sent successfully: {len(recipients_list)} recipients")
                
                return {
                    "success": True,
                    "message": sms_data.get("Message", "SMS sent"),
                    "recipients": recipients_list,
                    "message_ids": message_ids,
                    "total_cost": total_cost,
                }
        
        except Exception as e:
            logger.error(f"SMS send error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def send_bulk_sms(
        self,
        user_ids: List[str],
        message: str,
        sender_id: str
    ) -> Dict[str, Any]:
        """
        Send bulk SMS to user base
        
        Args:
            user_ids: List of FarmIQ user IDs
            message: Message content
            sender_id: Sender ID
            
        Returns:
            Result dictionary
        """
        
        try:
            # Fetch phone numbers for users (run in thread pool)
            def get_phones():
                session_factory = DatabasePool.get_session_factory()
                session = session_factory()
                try:
                    results = session.execute(
                        text("""
                        SELECT DISTINCT phone_number FROM users
                        WHERE id = ANY(:user_ids)
                        AND phone_number IS NOT NULL
                        """),
                        {"user_ids": user_ids}
                    ).fetchall()
                    
                    if not results:
                        logger.warning("No valid phone numbers found")
                        return None
                    
                    return [row[0] for row in results]
                finally:
                    session.close()
            
            phone_numbers = await asyncio.to_thread(get_phones)
            
            if not phone_numbers:
                return {
                    "success": False,
                    "error": "No valid phone numbers",
                }
            
            # Send SMS
            return await self.send_sms(phone_numbers, message, sender_id)
        
        except Exception as e:
            logger.error(f"Bulk SMS error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def fetch_incoming_sms(
        self,
        last_received_id: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch incoming SMS messages
        
        Args:
            last_received_id: ID of last message fetched
            
        Returns:
            {
                "success": bool,
                "messages": List[Dict],
                "last_id": int,
                "error": Optional[str]
            }
        """
        
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            params = {
                "username": self.username,
                "api_key": self.api_key,
                "lastReceivedId": last_received_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    data=params,
                    timeout=30.0
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Fetch SMS error: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                    }
                
                response_data = response.json()
                sms_data = response_data.get("SMSMessageData", {})
                messages = sms_data.get("Messages", [])
                
                # Update last received ID
                last_id = last_received_id
                if messages:
                    last_id = max(int(msg["id"]) for msg in messages)
                
                # Log messages
                if messages:
                    await self._log_incoming_sms(messages)
                
                logger.info(f"Fetched {len(messages)} incoming messages")
                
                return {
                    "success": True,
                    "messages": messages,
                    "last_id": last_id,
                    "count": len(messages),
                }
        
        except Exception as e:
            logger.error(f"Fetch SMS error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def handle_delivery_report(
        self,
        delivery_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle SMS delivery report webhook
        
        Args:
            delivery_report: Delivery report from Africa's Talking webhook
            
        Returns:
            Processing result
        """
        
        try:
            logging_info = {
                "message_id": delivery_report.get("id"),
                "status": delivery_report.get("status"),
                "phone_number": delivery_report.get("phoneNumber"),
                "network_code": delivery_report.get("networkCode"),
                "failure_reason": delivery_report.get("failureReason"),
            }
            
            # Log delivery report to database (run in thread pool)
            def log_delivery():
                session_factory = DatabasePool.get_session_factory()
                session = session_factory()
                try:
                    session.execute(
                        text("""
                        INSERT INTO sms_delivery_track (
                            message_id, status, phone_number, attempted_at, failed_reason, network_code
                        )
                        VALUES (:message_id, :status, :phone_number, NOW(), :failed_reason, :network_code)
                        ON CONFLICT (message_id) 
                        DO UPDATE SET status = :status, failed_reason = :failed_reason
                        """),
                        {
                            "message_id": logging_info["message_id"],
                            "status": logging_info["status"],
                            "phone_number": logging_info["phone_number"],
                            "failed_reason": logging_info["failure_reason"],
                            "network_code": logging_info["network_code"],
                        }
                    )
                    session.commit()
                finally:
                    session.close()
            
            await asyncio.to_thread(log_delivery)
            
            logger.info(f"Delivery report logged: {logging_info['message_id']} - {logging_info['status']}")
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Error handling delivery report: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def handle_incoming_message(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle incoming SMS message webhook
        
        Args:
            message: Incoming message from Africa's Talking webhook
            
        Returns:
            Processing result
        """
        
        try:
            phone_number = message.get("from")
            text = message.get("text")
            shortcode = message.get("to")
            
            logger.info(f"Incoming SMS: {phone_number} -> {shortcode}: {text[:50]}")
            
            # Check if this is a USSD-like response and log to database (run in thread pool)
            def log_message():
                session_factory = DatabasePool.get_session_factory()
                session = session_factory()
                try:
                    session.execute(
                        text("""
                        INSERT INTO sms_delivery_track (
                            phone_number, message_content, message_type, status, recipient_count
                        )
                        VALUES (:phone_number, :message_content, 'incoming', 'received', 1)
                        """),
                        {
                            "phone_number": phone_number,
                            "message_content": text
                        }
                    )
                    session.commit()
                finally:
                    session.close()
            
            await asyncio.to_thread(log_message)
            
            # TODO: Process message based on content
            # Could trigger USSD-like flows or token purchases
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Error handling incoming message: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def handle_opt_out(
        self,
        opt_out_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle SMS opt-out notification
        
        Args:
            opt_out_data: Opt-out information
            
        Returns:
            Processing result
        """
        
        try:
            phone_number = opt_out_data.get("phoneNumber")
            sender_id = opt_out_data.get("senderId")
            
            logger.info(f"SMS opt-out: {phone_number} from {sender_id}")
            
            # Log opt-out to database (run in thread pool)
            def log_optout():
                session_factory = DatabasePool.get_session_factory()
                session = session_factory()
                try:
                    session.execute(
                        text("""
                        INSERT INTO sms_delivery_track (
                            phone_number, status, message_type, failed_reason
                        )
                        VALUES (:phone_number, 'optout', 'bulk_optout', :failed_reason)
                        """),
                        {
                            "phone_number": phone_number,
                            "failed_reason": f"Opted out from {sender_id}"
                        }
                    )
                    session.commit()
                finally:
                    session.close()
            
            await asyncio.to_thread(log_optout)
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Error handling opt-out: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _log_sms_send(
        self,
        recipients: List[str],
        message: str,
        sender_id: str,
        message_ids: List[str],
        total_cost: float
    ) -> None:
        """Log sent SMS to database"""
        
        def log_send():
            session_factory = DatabasePool.get_session_factory()
            session = session_factory()
            try:
                for i, recipient in enumerate(recipients):
                    message_id = message_ids[i] if i < len(message_ids) else None
                    
                    session.execute(
                        text("""
                        INSERT INTO sms_delivery_track (
                            message_id, phone_number, message_content, message_type,
                            provider, status, attempted_at, recipient_count
                        )
                        VALUES (:message_id, :phone_number, :message_content, 'bulk', 'afrikatalk', 'sent', NOW(), :recipient_count)
                        """),
                        {
                            "message_id": message_id,
                            "phone_number": recipient,
                            "message_content": message,
                            "recipient_count": len(recipients)
                        }
                    )
                session.commit()
            finally:
                session.close()
        
        try:
            await asyncio.to_thread(log_send)
        except Exception as e:
            logger.error(f"Error logging SMS: {str(e)}", exc_info=True)
    
    async def _log_incoming_sms(
        self,
        messages: List[Dict[str, Any]]
    ) -> None:
        """Log incoming SMS messages to database"""
        
        def log_incoming():
            session_factory = DatabasePool.get_session_factory()
            session = session_factory()
            try:
                for message in messages:
                    session.execute(
                        text("""
                        INSERT INTO sms_delivery_track (
                            message_id, phone_number, message_content, message_type, status
                        )
                        VALUES (:message_id, :phone_number, :message_content, 'incoming', 'received')
                        """),
                        {
                            "message_id": str(message.get("id")),
                            "phone_number": message.get("from"),
                            "message_content": message.get("text")
                        }
                    )
                session.commit()
            finally:
                session.close()
        
        try:
            await asyncio.to_thread(log_incoming)
        except Exception as e:
            logger.error(f"Error logging incoming SMS: {str(e)}", exc_info=True)
