"""
USSD Authentication and Registration Service
Handles farmer registration, role selection, and profile setup via USSD
Integrates with Supabase auth and FarmIQ ID system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

# Optional Supabase import - graceful degradation if not installed
try:
    from supabase import AsyncClient
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    AsyncClient = None

logger = logging.getLogger(__name__)


class FarmerRole(str, Enum):
    """Available farmer roles in FarmIQ"""
    FARMER = "farmer"
    FARM_MANAGER = "farm_manager"
    COOPERATIVE = "cooperative"
    EXTENSION_OFFICER = "extension_officer"
    WORKER = "worker"
    LENDER = "lender"


class USSDState(str, Enum):
    """USSD user state"""
    WELCOME = "welcome"
    VERIFY_FARMIQ_ID = "verify_farmiq_id"
    LOGIN = "login"
    ROLE_SELECTION = "role_selection"
    FARMING_PROFILE = "farming_profile"
    AI_SERVICES_MENU = "ai_services_menu"
    PAYMENT_MENU = "payment_menu"
    AUTHENTICATED = "authenticated"
    ERROR = "error"


@dataclass
class USSDSession:
    """USSD user session"""
    phone_number: str
    session_id: str
    state: USSDState
    farmiq_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[FarmerRole] = None
    created_at: datetime = None
    expires_at: datetime = None
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(minutes=10)
        if self.data is None:
            self.data = {}

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def refresh_expiry(self):
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)


class USSDAuthService:
    """
    Manages USSD authentication flow:
    1. Verify FarmIQ ID
    2. Check if registered in Supabase
    3. Handle registration if new user
    4. Role selection
    5. Farming profile setup
    """

    def __init__(self, db_pool: asyncpg.Pool, supabase_client: AsyncClient):
        self.db_pool = db_pool
        self.supabase = supabase_client
        self.sessions: Dict[str, USSDSession] = {}
        self.phone_to_session: Dict[str, str] = {}

    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired = [sid for sid, session in self.sessions.items() if session.is_expired()]
        for sid in expired:
            phone = self.phone_to_session.get(sid)
            del self.sessions[sid]
            if phone:
                del self.phone_to_session[phone]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired USSD sessions")

    async def get_or_create_session(self, phone_number: str, session_id: str) -> USSDSession:
        """Get existing session or create new one"""
        # Check if phone already has active session
        if phone_number in self.phone_to_session:
            existing_sid = self.phone_to_session[phone_number]
            if existing_sid in self.sessions:
                session = self.sessions[existing_sid]
                if not session.is_expired():
                    session.refresh_expiry()
                    return session

        # Create new session
        session = USSDSession(phone_number=phone_number, session_id=session_id, state=USSDState.WELCOME)
        self.sessions[session_id] = session
        self.phone_to_session[phone_number] = session_id
        return session

    async def verify_farmiq_id(self, farmiq_id: str, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify FarmIQ ID exists and matches phone number
        
        Returns:
            (is_valid, user_data)
        """
        try:
            # Check user exists in Supabase with this FarmIQ ID
            result = await self.supabase.table("user_profiles").select("*").eq("farmiq_id", farmiq_id).single().execute()

            user_data = result.data
            if user_data:
                # Verify phone matches
                if user_data.get("phone_number", "").endswith(phone_number[-9:]):
                    logger.info(f"FarmIQ ID {farmiq_id} verified for {phone_number}")
                    return True, user_data
                else:
                    logger.warning(f"Phone mismatch for FarmIQ ID {farmiq_id}")
                    return False, None

            return False, None
        except Exception as e:
            logger.error(f"Error verifying FarmIQ ID: {str(e)}")
            return False, None

    async def register_new_user(self, phone_number: str, farmiq_id: str, password: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Register new user via Supabase Auth
        
        If no password provided, use phone-based authentication
        """
        try:
            # Register in Supabase Auth
            if password:
                auth_response = await self.supabase.auth.sign_up(
                    {
                        "email": f"{farmiq_id}@farmiq.local",
                        "password": password,
                    }
                )
            else:
                # Phone-based sign up (requires passwordless flow)
                auth_response = await self.supabase.auth.sign_in_with_otp(
                    {
                        "phone": phone_number,
                    }
                )

            user_id = auth_response.user.id if auth_response.user else None

            if not user_id:
                logger.error("Failed to create auth user")
                return False, None

            # Create user profile
            profile_data = {
                "user_id": user_id,
                "farmiq_id": farmiq_id,
                "phone_number": phone_number,
                "created_at": datetime.utcnow().isoformat(),
                "role": None,  # Will be set later
                "registration_method": "ussd",
            }

            # Insert into user_profiles
            await self.supabase.table("user_profiles").insert(profile_data).execute()

            logger.info(f"New user registered: {farmiq_id} ({phone_number})")
            return True, profile_data
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False, None

    async def set_user_role(self, user_id: str, farmiq_id: str, role: FarmerRole) -> bool:
        """Set user's primary role and create access permissions"""
        try:
            # Update user profile
            await self.supabase.table("user_profiles").update({"role": role.value}).eq("user_id", user_id).execute()

            # Create role-specific record
            role_data = {
                "user_id": user_id,
                "farmiq_id": farmiq_id,
                "role": role.value,
                "assigned_at": datetime.utcnow().isoformat(),
            }

            if role == FarmerRole.FARMER:
                # Create farm record for new farmer
                farm_data = {
                    "farmiq_id": farmiq_id,
                    "farmer_id": user_id,
                    "status": "pending_setup",
                    "created_at": datetime.utcnow().isoformat(),
                }
                await self.supabase.table("farms").insert(farm_data).execute()

            elif role == FarmerRole.COOPERATIVE:
                # Create cooperative record
                coop_data = {
                    "farmiq_id": farmiq_id,
                    "operator_id": user_id,
                    "status": "pending_setup",
                    "created_at": datetime.utcnow().isoformat(),
                }
                await self.supabase.table("cooperatives").insert(coop_data).execute()

            logger.info(f"Role '{role.value}' assigned to {farmiq_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting user role: {str(e)}")
            return False

    async def get_farming_profile_fields(self, role: FarmerRole) -> List[Tuple[str, str, str]]:
        """
        Get fields to collect based on role
        Returns: List of (field_name, field_label, field_type)
        """
        base_fields = [
            ("farm_name", "Farm name", "text"),
            ("county", "County", "select"),
            ("subcounty", "Sub-county", "text"),
            ("land_size_acres", "Land size (acres)", "number"),
        ]

        role_fields = {
            FarmerRole.FARMER: [
                ("primary_crop", "Primary crop", "select"),
                ("secondary_crop", "Secondary crop (optional)", "select"),
                ("farming_method", "Farming method", "select"),
                ("experience_years", "Years of farming", "number"),
            ],
            FarmerRole.FARM_MANAGER: [
                ("farms_managed", "Number of farms managed", "number"),
                ("regions", "Regions managed", "text"),
                ("workers_count", "Number of workers", "number"),
            ],
            FarmerRole.COOPERATIVE: [
                ("members_count", "Number of members", "number"),
                ("focus_crop", "Focus crop", "select"),
                ("registration_number", "Registration number", "text"),
            ],
            FarmerRole.EXTENSION_OFFICER: [
                ("villages_covered", "Villages covered", "number"),
                ("experience_years", "Years of extension experience", "number"),
                ("specialization", "Specialization", "select"),
            ],
            FarmerRole.WORKER: [
                ("employer_farmiq_id", "Employer FarmIQ ID", "text"),
                ("position", "Position/Role", "text"),
            ],
        }

        return base_fields + role_fields.get(role, [])

    async def save_farming_profile(self, user_id: str, farmiq_id: str, role: FarmerRole, profile_data: Dict[str, Any]) -> bool:
        """Save farming profile data to Supabase"""
        try:
            profile_complete = {
                "user_id": user_id,
                "farmiq_id": farmiq_id,
                "role": role.value,
                **profile_data,
                "profile_completed_at": datetime.utcnow().isoformat(),
            }

            # Save to user_profiles
            await self.supabase.table("user_profiles").update(profile_complete).eq("user_id", user_id).execute()

            # If farmer, update farm record
            if role == FarmerRole.FARMER:
                await (
                    self.supabase.table("farms")
                    .update({**profile_data, "status": "active"})
                    .eq("farmer_id", user_id)
                    .execute()
                )

            logger.info(f"Farming profile saved for {farmiq_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving farming profile: {str(e)}")
            return False

    async def get_user_by_farmiq_id(self, farmiq_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by FarmIQ ID"""
        try:
            result = await self.supabase.table("user_profiles").select("*").eq("farmiq_id", farmiq_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None

    async def link_phone_to_user(self, phone_number: str, farmiq_id: str) -> bool:
        """Link phone number to existing FarmIQ user"""
        try:
            await (
                self.supabase.table("user_profiles")
                .update({"phone_number": phone_number, "phone_verified": True})
                .eq("farmiq_id", farmiq_id)
                .execute()
            )
            logger.info(f"Phone {phone_number} linked to {farmiq_id}")
            return True
        except Exception as e:
            logger.error(f"Error linking phone: {str(e)}")
            return False

    # USSD Flow Menus

    async def menu_welcome(self) -> str:
        """Display welcome menu"""
        menu = """
FarmIQ - Farming Made Smart
============================
1. Register New Account
2. Login with FarmIQ ID
3. Migrate from Web
0. Exit

Enter choice:
"""
        return menu

    async def menu_verify_farmiq_id(self) -> str:
        """Prompt for FarmIQ ID"""
        menu = """
Enter your FarmIQ ID:
(e.g., FARM001234)

Enter 0 to cancel
"""
        return menu

    async def menu_role_selection(self) -> str:
        """Display role selection menu"""
        menu = """
Select your role:
============================
1. Farmer (crop/livestock)
2. Farm Manager (oversee farms)
3. Cooperative (group farming)
4. Extension Officer (advisor)
5. Worker (farm worker)

Enter choice:
"""
        return menu

    async def menu_farming_profile_start(self, role: FarmerRole) -> str:
        """Start farming profile setup"""
        menu = f"""
Setting up {role.value.replace('_', ' ')} profile
============================
Ready to setup? Reply:
1. Continue
2. Skip for now
0. Exit

Enter choice:
"""
        return menu

    async def get_field_prompt(self, field_name: str, field_label: str, field_type: str, current_value: int = 1) -> str:
        """Get prompt for a specific profile field"""
        if field_type == "select":
            # Return select options
            select_options = {
                "county": [
                    "1. Nairobi",
                    "2. Kakamega",
                    "3. Kiambu",
                    "4. Nakuru",
                    "5. Uasin Gishu",
                    "6. Other counties type name",
                ],
                "primary_crop": [
                    "1. Maize",
                    "2. Wheat",
                    "3. Rice",
                    "4. Beans",
                    "5. Potatoes",
                    "6. Other",
                ],
                "farming_method": [
                    "1. Traditional",
                    "2. Organic",
                    "3. Conventional",
                    "4. Precision",
                ],
                "specialization": [
                    "1. Crop Production",
                    "2. Livestock",
                    "3. Horticulture",
                    "4. Aquaculture",
                ],
            }
            options = select_options.get(field_name, [])
            menu = f"\n{field_label}\n{'=' * 30}\n"
            menu += "\n".join(options)
            menu += "\n\nEnter choice:"
            return menu
        else:
            # Text/number input
            menu = f"\n{field_label}\n{'=' * 30}\n"
            menu += f"Enter {field_type}: "
            return menu


class USSDMenuManager:
    """Manages USSD menu state transitions and responses"""

    def __init__(self, auth_service: USSDAuthService, afritalk_service=None):
        self.auth_service = auth_service
        self.afritalk_service = afritalk_service

    async def handle_ussd_input(self, session: USSDSession, user_input: str) -> Tuple[str, USSDState]:
        """
        Process USSD input and return response + new state
        
        Returns:
            (response_text, new_state)
        """
        user_input = user_input.strip()

        # Welcome menu handling
        if session.state == USSDState.WELCOME:
            if user_input == "1":
                return (await self.auth_service.menu_verify_farmiq_id()), USSDState.VERIFY_FARMIQ_ID
            elif user_input == "2":
                return (await self.auth_service.menu_verify_farmiq_id()), USSDState.LOGIN
            elif user_input == "0":
                return "Goodbye! Dial again to continue.", USSDState.AUTHENTICATED
            else:
                menu = await self.auth_service.menu_welcome()
                return f"Invalid choice. {menu}", USSDState.WELCOME

        # Verify FarmIQ ID
        elif session.state == USSDState.VERIFY_FARMIQ_ID:
            if user_input == "0":
                return (await self.auth_service.menu_welcome()), USSDState.WELCOME

            session.farmiq_id = user_input.upper()

            # Check if user exists
            user = await self.auth_service.get_user_by_farmiq_id(session.farmiq_id)

            if user:
                # Existing user
                session.user_id = user.get("user_id")
                session.role = FarmerRole(user.get("role", FarmerRole.FARMER.value))
                response = f"Welcome back, {user.get('farmiq_id')}!\n\nEnter your PIN: "
                return response, USSDState.LOGIN
            else:
                # New user - confirm registration
                response = f"""Confirm new registration
==================
FarmIQ ID: {session.farmiq_id}
Phone: {session.phone_number}

1. Confirm & Register
2. Cancel

Enter choice:"""
                session.data["temp_farmiq_id"] = session.farmiq_id
                return response, USSDState.VERIFY_FARMIQ_ID

        # Login
        elif session.state == USSDState.LOGIN:
            # In real app, verify PIN against Supabase
            # For USSD, simplified auth with just FarmIQ ID
            if session.user_id:
                # Already verified
                session.state = USSDState.AUTHENTICATED
                menu = await self._get_authenticated_menu(session.role)
                return menu, USSDState.AUTHENTICATED
            else:
                # Confirm details and set role
                response = await self.auth_service.menu_role_selection()
                return response, USSDState.ROLE_SELECTION

        # Role selection
        elif session.state == USSDState.ROLE_SELECTION:
            role_map = {
                "1": FarmerRole.FARMER,
                "2": FarmerRole.FARM_MANAGER,
                "3": FarmerRole.COOPERATIVE,
                "4": FarmerRole.EXTENSION_OFFICER,
                "5": FarmerRole.WORKER,
            }
            if user_input in role_map:
                session.role = role_map[user_input]

                # Register user
                registered, user_data = await self.auth_service.register_new_user(
                    phone_number=session.phone_number, farmiq_id=session.data.get("temp_farmiq_id", session.farmiq_id)
                )

                if registered:
                    session.user_id = user_data.get("user_id")

                    # Set role
                    await self.auth_service.set_user_role(session.user_id, session.data.get("temp_farmiq_id", session.farmiq_id), session.role)

                    # Start profile setup
                    menu = await self.auth_service.menu_farming_profile_start(session.role)
                    return menu, USSDState.FARMING_PROFILE
                else:
                    return "Registration failed. Try again.\n0. Back", USSDState.ROLE_SELECTION
            else:
                menu = await self.auth_service.menu_role_selection()
                return f"Invalid choice.\n{menu}", USSDState.ROLE_SELECTION

        # Farming profile setup
        elif session.state == USSDState.FARMING_PROFILE:
            if user_input == "1":
                # Start collecting profile data
                fields = await self.auth_service.get_farming_profile_fields(session.role)
                session.data["profile_fields"] = fields
                session.data["current_field_idx"] = 0
                session.data["profile_answers"] = {}

                # Get first field prompt
                field_name, field_label, field_type = fields[0]
                prompt = await self.auth_service.get_field_prompt(field_name, field_label, field_type)
                return prompt, USSDState.FARMING_PROFILE

            elif user_input == "2":
                # Skip profile setup
                menu = await self._get_authenticated_menu(session.role)
                return f"Profile setup skipped.\n{menu}", USSDState.AUTHENTICATED

            elif user_input == "0":
                menu = await self.auth_service.menu_role_selection()
                return menu, USSDState.ROLE_SELECTION

            else:
                # Collecting profile data
                fields = session.data.get("profile_fields", [])
                current_idx = session.data.get("current_field_idx", 0)

                if current_idx < len(fields):
                    field_name, field_label, field_type = fields[current_idx]
                    session.data["profile_answers"][field_name] = user_input

                    # Move to next field
                    current_idx += 1
                    session.data["current_field_idx"] = current_idx

                    if current_idx < len(fields):
                        # Get next field prompt
                        next_field = fields[current_idx]
                        prompt = await self.auth_service.get_field_prompt(next_field[0], next_field[1], next_field[2], current_idx)
                        return prompt, USSDState.FARMING_PROFILE
                    else:
                        # All fields collected - save profile
                        saved = await self.auth_service.save_farming_profile(
                            session.user_id, session.farmiq_id, session.role, session.data["profile_answers"]
                        )

                        if saved:
                            response = """Profile saved! ✓

Your account is ready.
You can now use all FarmIQ services."""
                            menu = await self._get_authenticated_menu(session.role)
                            return f"{response}\n\n{menu}", USSDState.AUTHENTICATED
                        else:
                            return "Error saving profile.\n0. Retry", USSDState.FARMING_PROFILE

        return "Invalid state. Please try again.\n0. Exit", session.state

    async def _get_authenticated_menu(self, role: Optional[FarmerRole] = None) -> str:
        """Get main menu for authenticated user"""
        menu = """
FarmIQ Main Menu
============================
1. FarmGrow (AI Recommendations)
2. FarmScore (Credit Scoring)
3. FarmSuite (Farm Analytics)
4. Buy Tokens
5. Check Balance
6. My Farms
7. Settings
0. Exit

Enter choice:"""
        return menu
