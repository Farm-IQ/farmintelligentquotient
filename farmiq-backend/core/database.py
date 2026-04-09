"""
FarmSuite AI - Core Database Client & Dependency Injection
Handles Supabase initialization, connection pooling, and async operations
Follows repository pattern for clean architecture
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import os
import logging
import asyncio

# Optional Supabase import - graceful degradation if not installed
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    Client = None
    create_client = None

logger = logging.getLogger(__name__)


class SupabaseClientFactory:
    """
    Factory for creating and managing Supabase clients
    Implements singleton pattern with lazy initialization
    """
    
    _instance: Optional['SupabaseClientFactory'] = None
    _client: Optional[Client] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_client(self) -> Client:
        """Get or create Supabase client with async initialization"""
        if self._client is None:
            async with self._lock:
                if self._client is None:  # Double-check locking
                    await self._initialize_client()
        return self._client
    
    async def _initialize_client(self) -> None:
        """Initialize Supabase client from environment variables"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Missing SUPABASE_URL or SUPABASE_KEY environment variables"
                )
            
            # Use service role key if available (better for backend operations)
            key = service_role_key or supabase_key
            self._client = create_client(supabase_url, key)
            
            logger.info("✅ Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise


class DatabaseRepository:
    """
    Base repository class for database operations
    Implements async/await pattern and error handling
    """
    
    def __init__(self, client_factory: SupabaseClientFactory):
        self.factory = client_factory
        self._client: Optional[Client] = None
    
    async def _get_client(self) -> Client:
        """Get Supabase client"""
        if self._client is None:
            self._client = await self.factory.get_client()
        return self._client
    
    async def insert_one(
        self, 
        table: str, 
        data: Dict[str, Any],
        return_inserted: bool = True
    ) -> Dict[str, Any]:
        """
        Insert single row
        
        Args:
            table: Table name
            data: Data dict to insert
            return_inserted: Whether to return inserted row
            
        Returns:
            Inserted data or insert count
        """
        try:
            client = await self._get_client()
            response = client.table(table).insert(data)
            
            if return_inserted:
                result = response.execute()
                return result.data[0] if result.data else None
            return response.execute()
            
        except Exception as e:
            logger.error(f"❌ Insert failed on table '{table}': {e}")
            raise
    
    async def insert_many(
        self, 
        table: str, 
        data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Insert multiple rows
        
        Args:
            table: Table name
            data_list: List of data dicts
            
        Returns:
            List of inserted rows
        """
        try:
            client = await self._get_client()
            result = client.table(table).insert(data_list).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"❌ Batch insert failed on table '{table}': {e}")
            raise
    
    async def select_one(
        self, 
        table: str, 
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Select single row
        
        Args:
            table: Table name
            filters: Filter conditions (col=val)
            
        Returns:
            Single row or None
        """
        try:
            client = await self._get_client()
            query = client.table(table)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Select failed on table '{table}': {e}")
            raise
    
    async def select_many(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[Tuple[str, bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Select multiple rows
        
        Args:
            table: Table name
            filters: Filter conditions
            limit: Limit result count
            offset: Offset for pagination
            order_by: (column, is_ascending) tuple
            
        Returns:
            List of rows
        """
        try:
            client = await self._get_client()
            query = client.table(table)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply ordering
            if order_by:
                col, is_asc = order_by
                query = query.order(col, desc=not is_asc)
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"❌ Select many failed on table '{table}': {e}")
            raise
    
    async def update_one(
        self, 
        table: str, 
        filters: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update single row
        
        Args:
            table: Table name
            filters: Filter conditions
            data: Data to update
            
        Returns:
            Updated row
        """
        try:
            client = await self._get_client()
            query = client.table(table)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.update(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Update failed on table '{table}': {e}")
            raise
    
    async def delete_one(
        self, 
        table: str, 
        filters: Dict[str, Any]
    ) -> bool:
        """
        Delete single row (soft delete preferred)
        
        Args:
            table: Table name
            filters: Filter conditions
            
        Returns:
            Success boolean
        """
        try:
            client = await self._get_client()
            query = client.table(table)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.delete().execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ Delete failed on table '{table}': {e}")
            raise
    
    async def soft_delete(
        self, 
        table: str, 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Soft delete (set is_deleted=true, deleted_at=now)
        Recommended for audit trails and GDPR compliance
        
        Args:
            table: Table name
            filters: Filter conditions
            
        Returns:
            Updated row
        """
        data = {
            "is_deleted": True,
            "deleted_at": datetime.utcnow().isoformat()
        }
        return await self.update_one(table, filters, data)
    
    async def upsert_one(
        self, 
        table: str, 
        data: Dict[str, Any],
        on_conflict: str
    ) -> Dict[str, Any]:
        """
        Upsert (insert or update on conflict)
        
        Args:
            table: Table name
            data: Data to upsert
            on_conflict: Conflict column name
            
        Returns:
            Upserted row
        """
        try:
            client = await self._get_client()
            result = client.table(table).upsert(
                data, 
                ignore_duplicates=False
            ).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Upsert failed on table '{table}': {e}")
            raise
    
    async def count(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count rows
        
        Args:
            table: Table name
            filters: Filter conditions
            
        Returns:
            Count of rows
        """
        try:
            client = await self._get_client()
            query = client.table(table)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.select("id", count="exact").limit(1).execute()
            return result.count if hasattr(result, 'count') else 0
            
        except Exception as e:
            logger.error(f"❌ Count failed on table '{table}': {e}")
            raise
    
    async def raw_query(self, query_text: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute raw SQL query via Supabase RPC
        
        Args:
            query_text: SQL query text
            params: Query parameters
            
        Returns:
            Query results
        """
        try:
            client = await self._get_client()
            # This would use a Supabase RPC function
            logger.warning("Raw queries require RPC function setup")
            return []
            
        except Exception as e:
            logger.error(f"❌ Raw query failed: {e}")
            raise
    
    async def execute_query(self, query_text: str, params: Optional[List] = None) -> List[Tuple]:
        """
        Execute raw SQL query
        Note: Supabase SDK doesn't support arbitrary raw SQL directly.
        This method logs a warning and should be migrated to proper repository methods.
        
        Args:
            query_text: SQL query text  
            params: Query parameters
            
        Returns:
            Query results (empty list if not properly implemented)
        """
        logger.warning(f"⚠️ execute_query() called with: {query_text[:100]}... - This should use proper repository methods")
        logger.warning("Please migrate this to use select_many(), update_one(), delete_one(), or count() methods")
        
        # For now, return empty list to prevent crashes
        # This will need to be reimplemented using Supabase stored procedures/RPC
        return []


# Singleton instance
_client_factory = SupabaseClientFactory()


async def get_supabase_client() -> Client:
    """FastAPI dependency for getting Supabase client"""
    return await _client_factory.get_client()


async def get_database_repository() -> DatabaseRepository:
    """FastAPI dependency for getting database repository"""
    return DatabaseRepository(_client_factory)
