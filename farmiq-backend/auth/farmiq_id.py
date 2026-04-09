"""
FarmIQ ID Service - Backend Validation and Storage
Handles FarmIQ ID validation, uniqueness checking, and database operations
"""

import re
from typing import Tuple, Optional, Dict
from datetime import datetime
import uuid


class FarmiqIdValidator:
    """
    Validates FarmIQ IDs and handles database operations
    Format: FQ + 4 alphanumeric characters (e.g., FQ7K9M2X)
    """
    
    PATTERN = re.compile(r'^FQ[A-Z0-9]{4}$')
    PREFIX = 'FQ'
    SUFFIX_LENGTH = 4
    VALID_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    @staticmethod
    def is_valid_format(farmiq_id: str) -> bool:
        """
        Validate FarmIQ ID format
        
        Args:
            farmiq_id: FarmIQ ID to validate
            
        Returns:
            True if format is valid (FQ + 4 alphanumeric), False otherwise
        """
        if not farmiq_id or not isinstance(farmiq_id, str):
            return False
        
        return bool(FarmiqIdValidator.PATTERN.match(farmiq_id.upper()))
    
    @staticmethod
    def parse_farmiq_id(farmiq_id: str) -> Optional[Dict[str, str]]:
        """
        Parse FarmIQ ID into components
        
        Args:
            farmiq_id: FarmIQ ID to parse
            
        Returns:
            Dictionary with 'prefix' and 'suffix' keys, or None if invalid
        """
        if not FarmiqIdValidator.is_valid_format(farmiq_id):
            return None
        
        farmiq_id = farmiq_id.upper()
        return {
            'prefix': farmiq_id[:2],
            'suffix': farmiq_id[2:],
            'full': farmiq_id
        }
    
    @staticmethod
    def generate_farmiq_id(user_id: Optional[str] = None) -> str:
        """
        Generate a new FarmIQ ID (non-cryptographic, for backend fallback only)
        For production, use the frontend FarmiqIdService which has database uniqueness checking
        
        Args:
            user_id: Optional user ID for deterministic generation
            
        Returns:
            Generated FarmIQ ID in format FQ + 4 random alphanumeric
        """
        import random
        import string
        
        # Generate 4 random alphanumeric characters
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{FarmiqIdValidator.PREFIX}{suffix}"


class FarmiqIdStorage:
    """
    Database operations for FarmIQ ID storage and validation
    (Actual implementation would use Supabase or other database)
    """
    
    @staticmethod
    async def check_if_exists(supabase_client, farmiq_id: str) -> bool:
        """
        Check if FarmIQ ID already exists in database
        
        Args:
            supabase_client: Supabase client instance
            farmiq_id: FarmIQ ID to check
            
        Returns:
            True if ID exists, False otherwise
        """
        if not FarmiqIdValidator.is_valid_format(farmiq_id):
            return False
        
        try:
            # Query user_profiles table for matching farmiq_id
            response = await supabase_client.table('user_profiles').select(
                'id', 'farmiq_id'
            ).eq('farmiq_id', farmiq_id.upper()).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking FarmIQ ID existence: {e}")
            # Return True (exists) on error to prevent creation (fail safe)
            return True
    
    @staticmethod
    async def store_farmiq_id(supabase_client, user_id: str, farmiq_id: str, role: str) -> Tuple[bool, Optional[str]]:
        """
        Store FarmIQ ID in database for user profile
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID
            farmiq_id: FarmIQ ID to store
            role: User role
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not FarmiqIdValidator.is_valid_format(farmiq_id):
            return False, f"Invalid FarmIQ ID format: {farmiq_id}"
        
        try:
            # Upsert into user_profiles (if exists, update; if not, insert)
            response = await supabase_client.table('user_profiles').upsert(
                {
                    'id': user_id,
                    'farmiq_id': farmiq_id.upper(),
                    'role': role,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
            ).execute()
            
            return True, None
        except Exception as e:
            error_msg = str(e)
            # Check for uniqueness constraint violation
            if '23505' in error_msg or 'unique' in error_msg.lower():
                return False, f"FarmIQ ID already exists: {farmiq_id}"
            return False, f"Failed to store FarmIQ ID: {error_msg}"
    
    @staticmethod
    async def get_user_by_farmiq_id(supabase_client, farmiq_id: str) -> Optional[Dict]:
        """
        Retrieve user information by FarmIQ ID
        
        Args:
            supabase_client: Supabase client instance
            farmiq_id: FarmIQ ID to search for
            
        Returns:
            User profile dict if found, None otherwise
        """
        if not FarmiqIdValidator.is_valid_format(farmiq_id):
            return None
        
        try:
            response = await supabase_client.table('user_profiles').select(
                '*'
            ).eq('farmiq_id', farmiq_id.upper()).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error retrieving user by FarmIQ ID: {e}")
            return None


class FarmiqIdAudit:
    """
    Audit logging for FarmIQ ID operations
    """
    
    @staticmethod
    def log_generation(farmiq_id: str, user_id: Optional[str] = None, retries: int = 0):
        """Log FarmIQ ID generation"""
        print(f"📱 FarmIQ ID Generated: {farmiq_id}, User: {user_id}, Retries: {retries}")
    
    @staticmethod
    def log_collision(farmiq_id: str, retry_attempt: int):
        """Log FarmIQ ID collision"""
        print(f"⚠️  FarmIQ ID Collision: {farmiq_id}, Retry: {retry_attempt}")
    
    @staticmethod
    def log_storage_error(farmiq_id: str, error: str):
        """Log FarmIQ ID storage error"""
        print(f"❌ FarmIQ ID Storage Error: {farmiq_id}, Error: {error}")
    
    @staticmethod
    def log_validation_success(user_id: str, farmiq_id: str):
        """Log successful FarmIQ ID validation"""
        print(f"✅ FarmIQ ID Validated: {farmiq_id} for user {user_id}")
