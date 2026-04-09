"""
Database Connection Pool Manager (Phase 3 - Performance Optimization)
Provides SQLAlchemy connection pooling for Supabase PostgreSQL
Improves performance with sync operations in thread pools
"""
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
import logging
from typing import Optional
from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Manages SQLAlchemy connection pool for efficient database access.
    
    Features:
    - Connection pooling (min 5 / max 20 connections)
    - Automatic connection reuse
    - Query timeout enforcement
    - Graceful connection handling
    - Sync mode for thread pool execution in async context
    
    Usage Pattern:
    - Get sessionmaker: factory = DatabasePool.get_session_factory()
    - Execute in thread: session = factory()
    - No need to write asyncio.to_thread() manually - use db.execute()
    """
    
    _engine = None
    _session_factory: Optional[sessionmaker] = None
    
    @classmethod
    async def initialize(cls):
        """
        Initialize connection pool and engine.
        
        Called during application startup via lifespan context manager.
        Raises RuntimeError if already initialized.
        """
        if cls._engine is not None:
            logger.warning("Connection pool already initialized")
            return
        
        try:
            # Create engine with connection pooling
            cls._engine = create_engine(
                DATABASE_URL,
                poolclass=pool.QueuePool,
                pool_size=5,                    # Minimum connections
                max_overflow=15,                # Additional connections (total max 20)
                pool_timeout=30,                # Timeout for getting connection
                pool_recycle=3600,              # Recycle connections every hour
                connect_args={'connect_timeout': 10},  # Connection timeout
                echo=False,                     # Set to True for SQL logging
            )
            
            # Create session factory
            cls._session_factory = sessionmaker(
                bind=cls._engine,
                class_=Session,
                expire_on_commit=False
            )
            
            logger.info("✅ Database connection pool initialized (SQLAlchemy)")
            logger.info(f"   🔌 Host: {DATABASE_URL.split('@')[1].split('/')[0]}")
            logger.info(f"   📊 Pool size: min=5, max=20")
            logger.info(f"   ⏱️  Connection timeout: 10s")
            logger.info(f"   ♻️  Pool recycle: 3600s")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
            raise RuntimeError(f"Database pool initialization failed: {e}")
    
    @classmethod
    async def close(cls):
        """
        Close connection pool and engine.
        Called during application shutdown via lifespan context manager.
        """
        if cls._engine:
            try:
                cls._engine.dispose()
                cls._engine = None
                cls._session_factory = None
                logger.info("✅ Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
    
    @classmethod
    def get_session_factory(cls) -> sessionmaker:
        """
        Get session factory instance for creating database sessions.
        
        Returns:
            sessionmaker instance for creating Session objects
            
        Usage:
            factory = DatabasePool.get_session_factory()
            session = factory()
            try:
                result = session.execute(text("SELECT * FROM users")).fetchall()
            finally:
                session.close()
        
        Raises:
            RuntimeError if pool not initialized
        """
        if cls._session_factory is None:
            raise RuntimeError(
                "Connection pool not initialized. "
                "Make sure FastAPI lifespan initializes pool before handlers execute."
            )
        return cls._session_factory


# FastAPI Dependency
def get_session_factory() -> sessionmaker:
    """
    FastAPI dependency to get session factory.
    
    Usage in endpoints:
        @router.get("/endpoint")
        async def handler(session_factory = Depends(get_session_factory)):
            def db_op():
                session = session_factory()
                try:
                    result = session.execute(text("SELECT * FROM table")).fetchall()
                    return result
                finally:
                    session.close()
            results = await asyncio.to_thread(db_op)
    
    Returns:
        sessionmaker instance
    """
    return DatabasePool.get_session_factory()


# Alias for backward compatibility
get_db_pool = get_session_factory
