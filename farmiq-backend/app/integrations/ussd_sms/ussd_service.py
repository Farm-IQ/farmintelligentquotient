"""
USSD Service - Manages USSD sessions and menu navigation
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy import text

from core.db_pool import DatabasePool

logger = logging.getLogger(__name__)


class USSDMenuTree:
    """USSD Menu tree structure"""
    
    MENUS = {
        "welcome": {
            "id": "welcome",
            "title": "Welcome to FarmIQ",
            "options": [
                {"key": "1", "text": "Check Balance", "action": "navigate", "next": "balance"},
                {"key": "2", "text": "Buy Tokens", "action": "navigate", "next": "buy_tokens"},
                {"key": "3", "text": "Subscribe to Tools", "action": "navigate", "next": "tools"},
                {"key": "4", "text": "Get Help", "action": "navigate", "next": "help"},
            ]
        },
        "balance": {
            "id": "balance",
            "title": "Token Balance",
            "options": [],
            "action": "show_balance"
        },
        "buy_tokens": {
            "id": "buy_tokens",
            "title": "Buy FIQ Tokens",
            "options": [
                {"key": "1", "text": "100 tokens = KES 50", "action": "purchase", "amount_fiq": 100, "amount_kes": 50},
                {"key": "2", "text": "500 tokens = KES 250", "action": "purchase", "amount_fiq": 500, "amount_kes": 250},
                {"key": "3", "text": "1000 tokens = KES 500", "action": "purchase", "amount_fiq": 1000, "amount_kes": 500},
                {"key": "4", "text": "5000 tokens = KES 2500", "action": "purchase", "amount_fiq": 5000, "amount_kes": 2500},
                {"key": "0", "text": "Back to Menu", "action": "navigate", "next": "welcome"},
            ]
        },
        "tools": {
            "id": "tools",
            "title": "Available Tools",
            "options": [
                {"key": "1", "text": "Disease Detection (500 FIQ/month)", "action": "subscribe", "tool_id": "disease-detection"},
                {"key": "2", "text": "Weather Forecast (300 FIQ/month)", "action": "subscribe", "tool_id": "weather-forecast"},
                {"key": "3", "text": "Yield Prediction (800 FIQ/month)", "action": "subscribe", "tool_id": "yield-prediction"},
                {"key": "4", "text": "Market Prices (200 FIQ/month)", "action": "subscribe", "tool_id": "market-prices"},
                {"key": "0", "text": "Back to Menu", "action": "navigate", "next": "welcome"},
            ]
        },
        "help": {
            "id": "help",
            "title": "Help Menu",
            "options": [
                {"key": "1", "text": "How to buy tokens?", "action": "show_help", "topic": "buy_tokens"},
                {"key": "2", "text": "FAQ", "action": "show_help", "topic": "faq"},
                {"key": "3", "text": "Contact Support", "action": "show_help", "topic": "contact"},
                {"key": "0", "text": "Back to Menu", "action": "navigate", "next": "welcome"},
            ]
        },
    }


class USSDService:
    """Service to manage USSD sessions and menu navigation"""
    
    def __init__(self):
        self.session_factory = DatabasePool.get_session_factory()
        self.menu_tree = USSDMenuTree()
        self.session_timeout_minutes = 10
    
    async def handle_ussd_request(
        self,
        session_id: str,
        phone_number: str,
        user_input: str,
        service_code: str
    ) -> Dict[str, Any]:
        """
        Handle incoming USSD request
        
        Args:
            session_id: Unique session ID from Africa's Talking
            phone_number: Phone number of user
            user_input: User's menu selection (empty for first request)
            service_code: USSD service code
            
        Returns:
            {"response_type": "CON" or "END", "menu_text": str}
        """
        
        try:
            # First request (user_input is empty)
            if not user_input:
                logger.info(f"USSD session started: {session_id} | Phone: {phone_number}")
                
                # Create new session
                session_data = await self._create_session(session_id, phone_number)
                
                # Return welcome menu
                menu = self.menu_tree.MENUS["welcome"]
                menu_text = await self._format_menu(menu)
                
                return {
                    "response_type": "CON",
                    "menu_text": menu_text,
                    "session_id": session_id,
                }
            
            # Subsequent requests - user has made selections
            else:
                logger.debug(f"USSD input received: {session_id} | Input: {user_input}")
                
                # Retrieve session
                session_data = await self._get_session(session_id)
                
                if not session_data:
                    logger.warning(f"Session not found: {session_id}")
                    menu_text = "END Session expired. Please dial again."
                    return {
                        "response_type": "END",
                        "menu_text": menu_text,
                    }
                
                # Update session with user input
                await self._update_session_input(session_id, user_input)
                
                # Parse user input (e.g., "1*2*3")
                selections = user_input.split("*")
                current_selection = selections[-1]
                
                # Get current menu based on navigation history
                current_menu_id = await self._get_current_menu(session_id, selections)
                current_menu = self.menu_tree.MENUS.get(current_menu_id, self.menu_tree.MENUS["welcome"])
                
                # Find selected option
                selected_option = None
                for option in current_menu.get("options", []):
                    if option["key"] == current_selection:
                        selected_option = option
                        break
                
                if not selected_option:
                    logger.warning(f"Invalid selection: {current_selection}")
                    menu_text = f"END Invalid selection. Please try again."
                    return {
                        "response_type": "END",
                        "menu_text": menu_text,
                    }
                
                # Handle action
                action = selected_option.get("action")
                
                if action == "navigate":
                    next_menu_id = selected_option.get("next", "welcome")
                    await self._update_current_menu(session_id, next_menu_id)
                    next_menu = self.menu_tree.MENUS.get(next_menu_id)
                    menu_text = await self._format_menu(next_menu)
                    
                    return {
                        "response_type": "CON",
                        "menu_text": menu_text,
                    }
                
                elif action == "show_balance":
                    balance = await self._get_user_balance(phone_number)
                    menu_text = f"END Your FIQ Balance: {balance} tokens"
                    return {
                        "response_type": "END",
                        "menu_text": menu_text,
                    }
                
                elif action == "purchase":
                    amount_fiq = selected_option.get("amount_fiq")
                    amount_kes = selected_option.get("amount_kes")
                    
                    # Trigger M-Pesa payment
                    mpesa_prompt = await self._initiate_token_purchase(
                        phone_number,
                        amount_fiq,
                        amount_kes
                    )
                    
                    menu_text = f"CON {mpesa_prompt}\n\nEnter M-Pesa PIN to complete payment"
                    return {
                        "response_type": "CON",
                        "menu_text": menu_text,
                    }
                
                elif action == "subscribe":
                    tool_id = selected_option.get("tool_id")
                    subscription_result = await self._subscribe_to_tool(phone_number, tool_id)
                    
                    if subscription_result["success"]:
                        menu_text = f"END Successfully subscribed to {selected_option['text']}"
                    else:
                        menu_text = f"END Subscription failed: {subscription_result.get('error')}"
                    
                    return {
                        "response_type": "END",
                        "menu_text": menu_text,
                    }
                
                elif action == "show_help":
                    topic = selected_option.get("topic")
                    help_text = await self._get_help_text(topic)
                    return {
                        "response_type": "END",
                        "menu_text": f"END {help_text}",
                    }
                
                else:
                    logger.warning(f"Unknown action: {action}")
                    return {
                        "response_type": "END",
                        "menu_text": "END Unknown action. Please try again.",
                    }
        
        except Exception as e:
            logger.error(f"USSD error: {str(e)}", exc_info=True)
            return {
                "response_type": "END",
                "menu_text": "END An error occurred. Please try again later.",
            }
    
    async def _create_session(self, session_id: str, phone_number: str) -> Dict[str, Any]:
        """Create new USSD session in database"""
        
        def create_sess():
            session = self.session_factory()
            try:
                result = session.execute(
                    text("""
                    INSERT INTO ussd_sessions (
                        session_id, phone_number, current_state, session_data, 
                        started_at, expires_at, status
                    )
                    VALUES (:session_id, :phone_number, 'welcome', :session_data, NOW(), NOW() + INTERVAL '10 minutes', 'active')
                    RETURNING *
                    """),
                    {
                        "session_id": session_id,
                        "phone_number": phone_number,
                        "session_data": json.dumps({"menu_history": ["welcome"], "inputs": []})
                    }
                )
                session.commit()
                row = result.fetchone()
                return dict(row) if row else None
            finally:
                session.close()
        
        return await asyncio.to_thread(create_sess)
    
    async def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from database"""
        
        def get_sess():
            session = self.session_factory()
            try:
                result = session.execute(
                    text("""
                    SELECT * FROM ussd_sessions
                    WHERE session_id = :session_id AND status = 'active'
                    AND expires_at > NOW()
                    LIMIT 1
                    """),
                    {"session_id": session_id}
                )
                row = result.fetchone()
                return dict(row) if row else None
            finally:
                session.close()
        
        return await asyncio.to_thread(get_sess)
    
    async def _update_session_input(self, session_id: str, user_input: str) -> None:
        """Update session with new user input"""
        
        def update_sess():
            session = self.session_factory()
            try:
                # Get current session data
                result = session.execute(
                    text("SELECT session_data FROM ussd_sessions WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                row = result.fetchone()
                if not row:
                    return
                
                session_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                session_data.setdefault("inputs", []).append(user_input)
                
                # Update session
                session.execute(
                    text("""
                    UPDATE ussd_sessions SET
                        session_data = :session_data,
                        updated_at = NOW()
                    WHERE session_id = :session_id
                    """),
                    {
                        "session_id": session_id,
                        "session_data": json.dumps(session_data)
                    }
                )
                session.commit()
            finally:
                session.close()
        
        await asyncio.to_thread(update_sess)
    
    async def _update_current_menu(self, session_id: str, menu_id: str) -> None:
        """Update current menu in session"""
        
        def update_menu():
            session = self.session_factory()
            try:
                session.execute(
                    text("""
                    UPDATE ussd_sessions
                    SET current_state = :menu_id
                    WHERE session_id = :session_id
                    """),
                    {
                        "menu_id": menu_id,
                        "session_id": session_id
                    }
                )
                session.commit()
            finally:
                session.close()
        
        await asyncio.to_thread(update_menu)
    
    async def _get_current_menu(self, session_id: str, selections: List[str]) -> str:
        """Get current menu based on navigation history"""
        
        # For now, use the first selection to determine menu
        # This can be enhanced for more complex menu trees
        
        if len(selections) == 1:
            return "welcome"
        
        first_selection = selections[0]
        menu_mapping = {
            "1": "balance",
            "2": "buy_tokens",
            "3": "tools",
            "4": "help",
        }
        
        return menu_mapping.get(first_selection, "welcome")
    
    async def _format_menu(self, menu: Dict[str, Any]) -> str:
        """Format menu for USSD display"""
        
        text = f"CON {menu.get('title', '')}\n"
        
        for option in menu.get("options", []):
            text += f"{option['key']}. {option['text']}\n"
        
        return text.strip()
    
    async def _get_user_balance(self, phone_number: str) -> int:
        """Get user's FIQ token balance"""
        
        def get_balance():
            session = self.session_factory()
            try:
                # Find user by phone number
                user_result = session.execute(
                    text("""
                    SELECT u.id FROM users u
                    WHERE u.phone_number = :phone_number
                    LIMIT 1
                    """),
                    {"phone_number": phone_number}
                ).fetchone()
                
                if not user_result:
                    return 0
                
                user_id = user_result[0]
                
                # Get token balance
                balance_result = session.execute(
                    text("""
                    SELECT fiq_balance FROM user_tokens
                    WHERE user_id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()
                
                return balance_result[0] if balance_result else 0
            finally:
                session.close()
        
        return await asyncio.to_thread(get_balance)
    
    async def _initiate_token_purchase(
        self,
        phone_number: str,
        amount_fiq: int,
        amount_kes: int
    ) -> str:
        """Initiate M-Pesa token purchase via USSD"""
        
        logger.info(f"Token purchase initiated via USSD: {phone_number} | {amount_fiq} FIQ")
        
        # This would call M-Pesa API to start payment
        # For now, return prompt
        return f"Please enter M-Pesa PIN to pay KES {amount_kes} for {amount_fiq} FIQ tokens"
    
    async def _subscribe_to_tool(self, phone_number: str, tool_id: str) -> Dict[str, Any]:
        """Subscribe user to tool via USSD"""
        
        logger.info(f"Tool subscription initiated via USSD: {phone_number} | {tool_id}")
        
        # TODO: Integrate with subscription service
        return {
            "success": True,
            "message": f"Subscribed to {tool_id}",
        }
    
    async def _get_help_text(self, topic: str) -> str:
        """Get help text for given topic"""
        
        help_topics = {
            "buy_tokens": "To buy tokens: 1. Select 'Buy Tokens' 2. Choose amount 3. Complete M-Pesa payment",
            "faq": "Q: How much do tokens cost? A: Prices vary by quantity. Q: Can I get a refund? A: Yes within 24 hours.",
            "contact": "For support, call +254 708 123 456 or email support@farmiq.app",
        }
        
        return help_topics.get(topic, "Help topic not found")
    
    async def end_session(self, session_id: str) -> None:
        """End USSD session"""
        
        def end_sess():
            session = self.session_factory()
            try:
                session.execute(
                    text("""
                    UPDATE ussd_sessions
                    SET status = 'completed'
                    WHERE session_id = :session_id
                    """),
                    {"session_id": session_id}
                )
                session.commit()
            finally:
                session.close()
        
        await asyncio.to_thread(end_sess)
        logger.info(f"USSD session ended: {session_id}")
