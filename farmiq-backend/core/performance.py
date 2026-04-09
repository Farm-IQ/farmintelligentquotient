"""
FarmIQ Performance Optimization - Database Connection Pooling & Query Optimization
Phase 5.2 - Implements connection pooling, query caching, and optimization statistics
"""
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE CONNECTION POOLING CONFIGURATION
# ============================================================================

class DatabasePoolConfig:
    """Configuration for database connection pooling"""
    
    # Connection pool settings
    POOL_SIZE = 10  # Number of connections to maintain in pool
    MAX_OVERFLOW = 20  # Maximum overflow connections beyond pool size
    POOL_TIMEOUT = 30  # Seconds to wait for connection from pool
    POOL_RECYCLE = 3600  # Recycle connections after 1 hour
    POOL_PRE_PING = True  # Test connections before using (detects dead connections)
    
    # Performance tuning
    ECHO_SQL = False  # Log all SQL statements (enable for debugging)
    CONNECT_ARGS = {
        'connect_timeout': 10,  # Connection timeout in seconds
        'application_name': 'farmiq-api',
    }
    
    @classmethod
    def create_engine(cls, database_url: str, **kwargs):
        """Create SQLAlchemy engine with optimized settings"""
        
        # Merge default config with kwargs
        engine_config = {
            'poolclass': pool.QueuePool,
            'pool_size': cls.POOL_SIZE,
            'max_overflow': cls.MAX_OVERFLOW,
            'pool_timeout': cls.POOL_TIMEOUT,
            'pool_recycle': cls.POOL_RECYCLE,
            'pool_pre_ping': cls.POOL_PRE_PING,
            'echo': cls.ECHO_SQL,
            'connect_args': cls.CONNECT_ARGS,
        }
        engine_config.update(kwargs)
        
        # Create engine with optimized settings
        engine = create_engine(database_url, **engine_config)
        
        # Add query execution profiler
        SimpleQueryProfiler.attach_to_engine(engine)
        
        logger.info(
            "Database engine created with connection pooling",
            extra={
                "pool_size": cls.POOL_SIZE,
                "max_overflow": cls.MAX_OVERFLOW,
                "pool_timeout": cls.POOL_TIMEOUT,
            }
        )
        
        return engine


# ============================================================================
# QUERY EXECUTION PROFILER
# ============================================================================

class SimpleQueryProfiler:
    """
    Profile SQL query execution times
    Identifies slow queries and N+1 issues
    """
    
    # Track query stats: {query_hash: {count, total_time, avg_time, last_time, ...}}
    query_stats = defaultdict(lambda: {
        'count': 0,
        'total_time_ms': 0,
        'min_time_ms': float('inf'),
        'max_time_ms': 0,
        'avg_time_ms': 0,
        'last_executed': None,
        'query_text': None,
    })
    
    # Thresholds
    SLOW_QUERY_THRESHOLD_MS = 100  # Queries taking > 100ms are slow
    N_PLUS_ONE_THRESHOLD = 10  # More than 10 similar queries in request
    
    @classmethod
    def attach_to_engine(cls, engine):
        """Attach profiler to SQLAlchemy engine"""
        
        @event.listens_for(engine, 'before_cursor_execute')
        def before_execute(conn, cursor, statement, parameters, context, executemany):
            # Store start time in connection
            conn.info.setdefault('query_start_time', time.time())
        
        @event.listens_for(engine, 'after_cursor_execute')
        def after_execute(conn, cursor, statement, parameters, context, executemany):
            # Calculate duration
            start_time = conn.info.pop('query_start_time', None)
            if start_time:
                duration_ms = (time.time() - start_time) * 1000
                
                # Normalize query for grouping (remove parameter values)
                query_hash = cls._hash_query(statement)
                
                # Update stats
                stats = cls.query_stats[query_hash]
                stats['count'] += 1
                stats['total_time_ms'] += duration_ms
                stats['min_time_ms'] = min(stats['min_time_ms'], duration_ms)
                stats['max_time_ms'] = max(stats['max_time_ms'], duration_ms)
                stats['avg_time_ms'] = stats['total_time_ms'] / stats['count']
                stats['last_executed'] = datetime.utcnow()
                if not stats['query_text']:
                    stats['query_text'] = statement[:200]  # Store first 200 chars
                
                # Log slow queries
                if duration_ms > cls.SLOW_QUERY_THRESHOLD_MS:
                    logger.warning(
                        f"Slow query detected: {duration_ms:.2f}ms",
                        extra={
                            'duration_ms': duration_ms,
                            'query_hash': query_hash,
                            'query_preview': statement[:100],
                        }
                    )
    
    @classmethod
    def _hash_query(cls, query_text: str) -> str:
        """Hash query to group identical queries"""
        import hashlib
        # Normalize query (remove parameters, extra whitespace)
        normalized = ' '.join(query_text.split()[:10])  # First 10 words
        return hashlib.md5(normalized.encode()).hexdigest()
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get query profiling statistics"""
        slow_queries = {
            k: v for k, v in cls.query_stats.items()
            if v['avg_time_ms'] > cls.SLOW_QUERY_THRESHOLD_MS
        }
        
        return {
            'total_queries': sum(q['count'] for q in cls.query_stats.values()),
            'total_time_ms': sum(q['total_time_ms'] for q in cls.query_stats.values()),
            'unique_queries': len(cls.query_stats),
            'slow_queries': len(slow_queries),
            'slowest_queries': sorted(
                slow_queries.items(),
                key=lambda x: x[1]['avg_time_ms'],
                reverse=True
            )[:5],
        }
    
    @classmethod
    def reset_stats(cls):
        """Clear all statistics"""
        cls.query_stats.clear()


# ============================================================================
# LAZY LOADED RELATIONSHIPS HELPER
# ============================================================================

class LazyLoadHelper:
    """Helper functions to prevent N+1 query problems"""
    
    @staticmethod
    def eager_load_relationships(query, *relationships):
        """
        Eager load relationships to prevent N+1 queries
        
        Usage:
            query = session.query(Farm)
            query = LazyLoadHelper.eager_load_relationships(
                query, 
                'crops', 
                'productionRecords'
            )
            farms = query.all()  # Now only 3 queries: 1 for farms + 2 for relationships
        """
        from sqlalchemy.orm import joinedload
        
        for rel in relationships:
            query = query.options(joinedload(rel))
        
        return query
    
    @staticmethod
    def count_efficient(query) -> int:
        """Count rows without loading all data"""
        from sqlalchemy import func
        return query.with_entities(func.count()).scalar()


# ============================================================================
# BATCH OPERATIONS HELPER
# ============================================================================

class BatchOperations:
    """Helper for efficient batch database operations"""
    
    @staticmethod
    def batch_insert(session: Session, records: List[Any], batch_size: int = 1000):
        """
        Efficiently insert many records using batching
        
        Usage:
            farms = [Farm(...) for _ in range(10000)]
            BatchOperations.batch_insert(session, farms)
        """
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            session.add_all(batch)
            session.commit()
            logger.info(f"Inserted batch {i // batch_size + 1}")
    
    @staticmethod
    def batch_update(
        session: Session,
        query_func: Callable,
        update_func: Callable,
        batch_size: int = 1000
    ):
        """
        Efficiently update many records using batching
        
        Usage:
            def get_farms():
                return session.query(Farm).filter(Farm.health_score < 50)
            
            def update_farm(farm):
                farm.health_score += 10
            
            BatchOperations.batch_update(
                session,
                get_farms,
                update_farm,
                batch_size=500
            )
        """
        offset = 0
        while True:
            records = query_func().offset(offset).limit(batch_size).all()
            if not records:
                break
            
            for record in records:
                update_func(record)
            
            session.commit()
            logger.info(f"Updated batch starting at offset {offset}")
            offset += batch_size


# ============================================================================
# PAGINATION HELPER
# ============================================================================

class PaginationHelper:
    """Helper for efficient pagination without loading all data"""
    
    @staticmethod
    def paginate(
        query,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Paginate query results efficiently
        
        Returns:
            {
                'items': [...],
                'page': 1,
                'per_page': 20,
                'total': 1000,
                'pages': 50,
                'has_next': True,
                'has_prev': False,
            }
        """
        # Enforce max per_page
        per_page = min(per_page, max_per_page)
        
        # Get total count efficiently
        from sqlalchemy import func
        total = query.with_entities(func.count()).scalar()
        
        # Get page items
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate pages
        pages = (total + per_page - 1) // per_page
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_next': page < pages,
            'has_prev': page > 1,
        }


# ============================================================================
# TRANSACTION MANAGEMENT
# ============================================================================

@contextmanager
def transaction_scope(session: Session):
    """
    Context manager for transaction handling with proper error handling
    
    Usage:
        with transaction_scope(session) as trans:
            farm = session.query(Farm).get(farm_id)
            farm.health_score += 5
            # Automatically commits on success, rolls back on error
    """
    try:
        yield session
        session.commit()
        logger.info("Transaction committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise
    finally:
        session.close()


# ============================================================================
# CONNECTION POOL MONITORING
# ============================================================================

class PoolMonitor:
    """Monitor database connection pool health"""
    
    @staticmethod
    def get_pool_status(engine) -> Dict[str, Any]:
        """Get connection pool statistics"""
        pool = engine.pool
        
        return {
            'pool_type': pool.__class__.__name__,
            'pool_size': getattr(pool, 'pool_size', None),
            'current_connections': getattr(pool, 'checkedout', None),
            'available_connections': getattr(pool, 'size', None),
            'overflow_connections': getattr(pool, 'overflow', None),
            'total_connections': (
                getattr(pool, 'size', 0) + getattr(pool, 'overflow', 0)
            ),
            'queue_size': (
                pool.pool.qsize() if hasattr(pool, 'pool') else None
            ),
        }
    
    @staticmethod
    def log_pool_status(engine):
        """Log pool statistics"""
        status = PoolMonitor.get_pool_status(engine)
        logger.info(
            "Connection pool status",
            extra=status
        )


# ============================================================================
# DATABASE STATISTICS & OPTIMIZATION
# ============================================================================

class DatabaseStats:
    """Collect and report database statistics"""
    
    _stats = {
        'queries_executed': 0,
        'total_query_time_ms': 0,
        'slow_queries_detected': 0,
        'n_plus_one_issues': 0,
        'last_stat_reset': datetime.utcnow(),
    }
    
    @classmethod
    def increment_query_count(cls, query_time_ms: float):
        """Record query execution"""
        cls._stats['queries_executed'] += 1
        cls._stats['total_query_time_ms'] += query_time_ms
        
        if query_time_ms > SimpleQueryProfiler.SLOW_QUERY_THRESHOLD_MS:
            cls._stats['slow_queries_detected'] += 1
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get database statistics since last reset"""
        uptime = datetime.utcnow() - cls._stats['last_stat_reset']
        
        return {
            **cls._stats,
            'queries_per_second': (
                cls._stats['queries_executed'] / uptime.total_seconds()
                if uptime.total_seconds() > 0 else 0
            ),
            'avg_query_time_ms': (
                cls._stats['total_query_time_ms'] / cls._stats['queries_executed']
                if cls._stats['queries_executed'] > 0 else 0
            ),
        }
    
    @classmethod
    def reset_stats(cls):
        """Reset statistics"""
        cls._stats = {
            'queries_executed': 0,
            'total_query_time_ms': 0,
            'slow_queries_detected': 0,
            'n_plus_one_issues': 0,
            'last_stat_reset': datetime.utcnow(),
        }
