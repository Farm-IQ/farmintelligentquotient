"""
USSD Menu System for FarmIQ Payment Testing
Provides text-based interface for users to test payment flow end-to-end
Can be integrated with actual USSD providers (Africa's Talking, Afrimax, etc.)

Author: FarmIQ Backend Team
Date: March 2026
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from fastapi import HTTPException

from core.logging_config import get_logger

logger = get_logger(__name__)


class USSDMenuService:
    """
    USSD (Unstructured Supplementary Service Data) menu system
    Simulates interactive SMS-based menu for testing payment flows
    """
    
    def __init__(self, db_pool: asyncpg.Pool, mpesa_service, escrow_service, reversal_service):
        self.db_pool = db_pool
        self.mpesa_service = mpesa_service
        self.escrow_service = escrow_service
        self.reversal_service = reversal_service
        
        # Session storage (in production, use Redis or database)
        self.sessions = {}
    
    # ===================== MAIN MENU FLOW =====================
    
    async def handle_ussd_request(
        self,
        phone_number: str,
        text: str,
        session_id: str
    ) -> str:
        """
        Handle incoming USSD request
        Routes to appropriate menu based on session state and user input
        
        Args:
            phone_number: User's M-Pesa phone (e.g., "254712345678")
            text: User's menu selection (e.g., "1", "1*1*100", etc.)
            session_id: Unique session identifier
        
        Returns:
            USSD menu text response
        """
        try:
            # Initialize or retrieve session
            session = await self._get_or_create_session(phone_number, session_id)
            
            # Parse text input (e.g., "1*2*100" means selections 1, 2, and input 100)
            menu_selections = text.strip("*").split("*") if text else []
            current_level = len(menu_selections)
            
            logger.info(f"📱 USSD Request: {phone_number} Level:{current_level} Input:{text}")
            
            # Route to appropriate menu level
            if current_level == 0 or text == "":
                return await self._show_main_menu(session)
            
            elif current_level == 1:
                return await self._handle_main_menu_selection(session, menu_selections[0])
            
            elif current_level == 2:
                return await self._handle_submenu_selection(session, menu_selections[0], menu_selections[1])
            
            elif current_level >= 3:
                return await self._handle_input(session, menu_selections)
            
            else:
                return "❌ Invalid input. Dial *500# to start over."
        
        except Exception as e:
            logger.error(f"❌ USSD handling failed: {str(e)}")
            return f"❌ Error: {str(e)}\nDial *500# to start over."
    
    # ===================== MENU LEVELS =====================
    
    async def _show_main_menu(self, session: Dict[str, Any]) -> str:
        """Display main menu"""
        session["menu_level"] = "MAIN"
        session["last_updated"] = datetime.now()
        
        menu_text = """
🌾 FARMIQ MENU 🌾
================
1. 💳 BUY TOKENS (M-Pesa)
2. 👁️ CHECK BALANCE
3. 📋 PAYMENT HISTORY
4. 🔒 ESCROW STATUS
5. ↩️ REQUEST REVERSAL
6. ℹ️ HELP
0. EXIT

Choose option (1-6):
"""
        return menu_text.strip()
    
    async def _handle_main_menu_selection(self, session: Dict[str, Any], choice: str) -> str:
        """Handle main menu selection"""
        if choice == "1":
            return await self._show_token_purchase_menu(session)
        
        elif choice == "2":
            return await self._show_balance(session)
        
        elif choice == "3":
            return await self._show_payment_history(session)
        
        elif choice == "4":
            return await self._show_escrow_status_menu(session)
        
        elif choice == "5":
            return await self._show_reversal_menu(session)
        
        elif choice == "6":
            return await self._show_help_menu(session)
        
        elif choice == "0":
            session["state"] = "CLOSED"
            return "👋 Thank you for using FarmIQ!\nDial *500# to start over."
        
        else:
            return "❌ Invalid choice. Enter 1-6:"
    
    # ===================== TOKEN PURCHASE FLOW =====================
    
    async def _show_token_purchase_menu(self, session: Dict[str, Any]) -> str:
        """Show token packages available"""
        session["menu_level"] = "BUY_TOKENS"
        session["state"] = "SELECTING_PACKAGE"
        
        menu_text = """
💳 CHOOSE TOKEN PACKAGE
=======================
1. 📦 STARTER: 100 FIQ = 1,000 KES (+10 Bonus)
2. 📦 SMALL: 500 FIQ = 5,000 KES (+50 Bonus)
3. 📦 MEDIUM: 1,000 FIQ = 10,000 KES (+100 Bonus)
4. 📦 LARGE: 2,000 FIQ = 20,000 KES (+200 Bonus)
0. BACK

Choose package (1-4):
"""
        return menu_text.strip()
    
    async def _handle_submenu_selection(
        self,
        session: Dict[str, Any],
        main_choice: str,
        sub_choice: str
    ) -> str:
        """Handle submenu selection"""
        
        # Token purchase flow
        if main_choice == "1":
            if sub_choice == "1":
                session["selected_package"] = "STARTER"
                session["package_amount"] = 1000
                session["state"] = "CONFIRMING_PURCHASE"
                return await self._confirm_token_purchase(session)
            
            elif sub_choice == "2":
                session["selected_package"] = "SMALL"
                session["package_amount"] = 5000
                session["state"] = "CONFIRMING_PURCHASE"
                return await self._confirm_token_purchase(session)
            
            elif sub_choice == "3":
                session["selected_package"] = "MEDIUM"
                session["package_amount"] = 10000
                session["state"] = "CONFIRMING_PURCHASE"
                return await self._confirm_token_purchase(session)
            
            elif sub_choice == "4":
                session["selected_package"] = "LARGE"
                session["package_amount"] = 20000
                session["state"] = "CONFIRMING_PURCHASE"
                return await self._confirm_token_purchase(session)
            
            elif sub_choice == "0":
                return await self._show_main_menu(session)
        
        # Escrow flow
        elif main_choice == "4":
            if sub_choice == "1":
                return await self._show_escrow_details(session)
            elif sub_choice == "0":
                return await self._show_main_menu(session)
        
        # Reversal flow
        elif main_choice == "5":
            if sub_choice == "1":
                session["state"] = "AWAITING_CHECKOUT_ID"
                return "Enter checkout ID to reverse:\n(e.g., FIQ1A2B3C4D5E6F7G)"
            elif sub_choice == "0":
                return await self._show_main_menu(session)
        
        return "❌ Invalid choice. Try again."
    
    async def _handle_input(
        self,
        session: Dict[str, Any],
        selections: list
    ) -> str:
        """Handle final user input (amounts, confirmations, etc.)"""
        
        state = session.get("state")
        
        # Token purchase confirmation
        if state == "CONFIRMING_PURCHASE":
            confirmation = selections[2] if len(selections) > 2 else None
            if confirmation == "1":
                return await self._process_token_purchase(session)
            elif confirmation == "2":
                return await self._show_main_menu(session)
        
        # Escrow farm ID
        elif state == "AWAITING_FARM_ID":
            farm_id = selections[2] if len(selections) > 2 else None
            return await self._get_escrow_for_farm(session, farm_id)
        
        # Reversal checkout ID
        elif state == "AWAITING_CHECKOUT_ID":
            checkout_id = selections[2] if len(selections) > 2 else None
            return await self._process_reversal_request(session, checkout_id)
        
        return "❌ Invalid input. Try again."
    
    # ===================== TOKEN PURCHASE LOGIC =====================
    
    async def _confirm_token_purchase(self, session: Dict[str, Any]) -> str:
        """Show purchase confirmation"""
        package = session.get("selected_package", "UNKNOWN")
        amount_kes = session.get("package_amount", 0)
        bonus_tokens = amount_kes // 100  # 10% bonus
        
        menu_text = f"""
✅ CONFIRM PURCHASE
====================
Package: {package}
Amount: {amount_kes:,} KES
Tokens: {amount_kes // 10} FIQ
Bonus: +{bonus_tokens} FIQ
Total: {(amount_kes // 10) + bonus_tokens} FIQ

1. ✅ CONFIRM
2. ❌ CANCEL

Choose (1-2):
"""
        return menu_text.strip()
    
    async def _process_token_purchase(self, session: Dict[str, Any]) -> str:
        """Process the token purchase"""
        try:
            phone_number = session["phone_number"]
            amount_kes = Decimal(session.get("package_amount", 1000))
            
            # Get user by phone number
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    SELECT farmiq_id, user_id, phone_number 
                    FROM user_wallets 
                    WHERE phone_number = $1 OR ((metadata->>'phone_number')::varchar = $1)
                    LIMIT 1
                    """,
                    phone_number
                )
            
            if not user:
                return f"""
❌ Account not linked to {phone_number}
Please contact support to create an account.

Dial *500# to start over.
"""
            
            farmiq_id = user["farmiq_id"]
            user_id = user["user_id"]
            
            # Initiate M-Pesa payment
            logger.info(f"💳 Initiating payment for {phone_number}: {amount_kes} KES")
            
            result = await self.mpesa_service.initiate_stk_push(
                phone_number=phone_number,
                amount_kes=amount_kes,
                farmiq_id=farmiq_id,
                user_id=user_id
            )
            
            tokens_to_buy = result["tokens_to_purchase"]
            checkout_id = result["checkout_id"]
            
            session["checkout_id"] = checkout_id
            session["state"] = "AWAITING_PAYMENT"
            session["initiated_at"] = datetime.now()
            
            return f"""
📱 M-PESA STK PUSH SENT!
========================
Amount: {amount_kes:,} KES
Tokens: {tokens_to_buy:.0f} FIQ
Checkout ID: {checkout_id}

✅ Enter your M-Pesa PIN on your phone
⏱️ This will timeout in 60 seconds

Check payment status:
Dial *500*1*3# to view history
"""
        
        except HTTPException as e:
            return f"❌ Error: {e.detail}\nDial *500# to try again."
        except Exception as e:
            logger.error(f"❌ Purchase processing failed: {str(e)}")
            return f"❌ Error: Failed to process payment\nDial *500# to try again."
    
    # ===================== BALANCE & HISTORY =====================
    
    async def _show_balance(self, session: Dict[str, Any]) -> str:
        """Show user's FIQ token balance"""
        try:
            phone_number = session["phone_number"]
            
            async with self.db_pool.acquire() as conn:
                wallet = await conn.fetchrow(
                    """
                    SELECT fiq_token_balance, fiq_balance_last_updated
                    FROM user_wallets
                    WHERE phone_number = $1 OR ((metadata->>'phone_number')::varchar = $1)
                    LIMIT 1
                    """,
                    phone_number
                )
            
            if not wallet:
                balance = 0
            else:
                balance = wallet["fiq_token_balance"]
            
            menu_text = f"""
💰 YOUR BALANCE
================
FIQ Tokens: {balance:.2f}
Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

1. 📊 USAGE STATS
2. 🔄 BACK TO MENU
0. EXIT

Choose (0-2):
"""
            return menu_text.strip()
        
        except Exception as e:
            logger.error(f"❌ Balance check failed: {str(e)}")
            return f"❌ Error checking balance\nDial *500# to try again."
    
    async def _show_payment_history(self, session: Dict[str, Any]) -> str:
        """Show last 5 payments"""
        try:
            # Get farmiq_id from phone
            phone_number = session["phone_number"]
            
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT farmiq_id FROM user_wallets WHERE phone_number = $1 LIMIT 1",
                    phone_number
                )
                
                if not user:
                    return "❌ Account not found. Dial *500# to start over."
                
                farmiq_id = user["farmiq_id"]
                
                # Get last 5 transactions
                transactions = await conn.fetch(
                    """
                    SELECT amount_kes, tokens_purchased, payment_status, created_at
                    FROM mpesa_transactions
                    WHERE farmiq_id = $1
                    ORDER BY created_at DESC
                    LIMIT 5
                    """,
                    farmiq_id
                )
            
            menu_text = "📋 RECENT PAYMENTS\n" + "="*20 + "\n"
            
            if not transactions:
                menu_text += "No payments yet.\n"
            else:
                for i, tx in enumerate(transactions, 1):
                    status_emoji = "✅" if tx["payment_status"] == "COMPLETED" else "⏳"
                    menu_text += f"\n{i}. {status_emoji} {tx['amount_kes']:.0f} KES\n   {tx['tokens_purchased']:.0f} FIQ\n   {tx['created_at'].strftime('%y-%m-%d %H:%M')}\n"
            
            menu_text += "\n1. 🔄 BACK\n0. EXIT"
            
            return menu_text.strip()
        
        except Exception as e:
            logger.error(f"❌ History query failed: {str(e)}")
            return f"❌ Error loading history\nDial *500# to try again."
    
    # ===================== ESCROW STATUS =====================
    
    async def _show_escrow_status_menu(self, session: Dict[str, Any]) -> str:
        """Show escrow options"""
        session["state"] = "SELECTING_ESCROW_ACTION"
        
        menu_text = """
🔒 ESCROW MANAGEMENT
====================
1. 👁️ CHECK ESCROW STATUS
2. 🔓 REQUEST RELEASE
0. BACK

Choose (0-2):
"""
        return menu_text.strip()
    
    async def _show_escrow_details(self, session: Dict[str, Any]) -> str:
        """Show escrow accounts for user"""
        try:
            phone_number = session["phone_number"]
            
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT farmiq_id FROM user_wallets WHERE phone_number = $1 LIMIT 1",
                    phone_number
                )
                
                if not user:
                    return "❌ Account not found. Dial *500# to start over."
                
                farmiq_id = user["farmiq_id"]
                
                # Get active escrows
                escrows = await conn.fetch(
                    """
                    SELECT loan_id, tokens_locked, escrow_status, 
                           expires_at, release_condition
                    FROM escrow_accounts
                    WHERE farmiq_id = $1 AND escrow_status = 'ACTIVE'
                    ORDER BY created_at DESC
                    LIMIT 3
                    """,
                    farmiq_id
                )
            
            menu_text = "🔒 YOUR ESCROWS\n" + "="*20 + "\n"
            
            if not escrows:
                menu_text += "No active escrows.\n"
            else:
                for i, escrow in enumerate(escrows, 1):
                    hours_left = max(0, (escrow["expires_at"] - datetime.now()).total_seconds() / 3600)
                    menu_text += f"\n{i}. Loan: {escrow['loan_id']}\n"
                    menu_text += f"   Locked: {escrow['tokens_locked']} FIQ\n"
                    menu_text += f"   Status: {escrow['escrow_status']}\n"
                    menu_text += f"   Expires: {hours_left:.0f}h\n"
            
            menu_text += "\n1. 🔄 BACK\n0. EXIT"
            
            return menu_text.strip()
        
        except Exception as e:
            logger.error(f"❌ Escrow query failed: {str(e)}")
            return f"❌ Error loading escrows\nDial *500# to try again."
    
    # ===================== REVERSAL FLOW =====================
    
    async def _show_reversal_menu(self, session: Dict[str, Any]) -> str:
        """Show reversal options"""
        session["state"] = "SELECTING_REVERSAL_ACTION"
        session["menu_level"] = "REVERSAL"
        
        menu_text = """
↩️ REQUEST REVERSAL
===================
(24-hour window only)

1. 📝 REQUEST REVERSAL
2. 👁️ CHECK REVERSAL STATUS
0. BACK

Choose (0-2):
"""
        return menu_text.strip()
    
    async def _process_reversal_request(self, session: Dict[str, Any], checkout_id: str) -> str:
        """Process reversal request"""
        try:
            phone_number = session["phone_number"]
            
            # Get user
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT farmiq_id FROM user_wallets WHERE phone_number = $1 LIMIT 1",
                    phone_number
                )
                
                if not user:
                    return "❌ Account not found. Dial *500# to start over."
                
                farmiq_id = user["farmiq_id"]
                
                # Get payment
                payment = await conn.fetchrow(
                    """
                    SELECT amount_kes, tokens_purchased, created_at, payment_status
                    FROM mpesa_transactions
                    WHERE checkout_id = $1 AND farmiq_id = $2
                    """,
                    checkout_id, farmiq_id
                )
            
            if not payment:
                return f"❌ Payment not found: {checkout_id}\nDial *500# to try again."
            
            # Request reversal
            result = await self.reversal_service.request_reversal(
                farmiq_id=farmiq_id,
                checkout_id=checkout_id,
                amount_kes=payment["amount_kes"]
            )
            
            return f"""
✅ REVERSAL REQUESTED
=====================
Reversal ID: {result['reversal_id']}
Tokens to refund: {result['tokens_to_refund']:.0f} FIQ
Amount to refund: {result['refund_amount_kes']:.0f} KES
Hours remaining: {result['hours_remaining']:.1f}h

Dial *500# to check status later.
"""
        
        except HTTPException as e:
            return f"❌ Error: {e.detail}\nDial *500# to try again."
        except Exception as e:
            logger.error(f"❌ Reversal request failed: {str(e)}")
            return f"❌ Error: {str(e)}\nDial *500# to try again."
    
    # ===================== HELP & INFO =====================
    
    async def _show_help_menu(self, session: Dict[str, Any]) -> str:
        """Show help information"""
        menu_text = """
ℹ️ HELP & INFORMATION
=====================
Commands:
*500# ......... Main menu
*500*1# ....... Buy tokens
*500*2# ....... Check balance
*500*3# ....... Payment history
*500*4# ....... Escrow status
*500*5# ....... Request reversal

Features:
💳 Instant token purchases via M-Pesa
🔒 Token escrow for loans
↩️ 24-hour refund window
📱 No data charges (USSD)

Support: support@farmiq.co.ke

Dial 1 to return to menu, 0 to exit.
"""
        return menu_text.strip()
    
    # ===================== SESSION MANAGEMENT =====================
    
    async def _get_or_create_session(
        self,
        phone_number: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get or create a session"""
        
        key = f"{phone_number}:{session_id}"
        
        if key not in self.sessions:
            self.sessions[key] = {
                "phone_number": phone_number,
                "session_id": session_id,
                "created_at": datetime.now(),
                "menu_level": "MAIN",
                "state": "INITIAL"
            }
        
        session = self.sessions[key]
        
        # Expire sessions after 10 minutes
        if (datetime.now() - session["created_at"]).total_seconds() > 600:
            del self.sessions[key]
            return await self._get_or_create_session(phone_number, session_id)
        
        return session
    
    async def cleanup_sessions(self) -> int:
        """Remove expired sessions (run periodically)"""
        expired = 0
        now = datetime.now()
        
        for key in list(self.sessions.keys()):
            session = self.sessions[key]
            if (now - session["created_at"]).total_seconds() > 600:
                del self.sessions[key]
                expired += 1
        
        logger.info(f"🧹 Cleaned up {expired} expired USSD sessions")
        return expired
