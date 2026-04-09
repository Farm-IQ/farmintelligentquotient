"""
Centralized In-Process Caching Module
Provides application-wide caching with TTL, LRU eviction, and decorators
Replaces Redis with efficient in-memory caching

Features:
- Thread-safe operations
- Automatic TTL expiration
- LRU eviction policy
- Cache statistics and monitoring
- Decorator-based caching for functions
- Namespaced keys
- Pattern-based deletion

Author: FarmIQ Backend Team
Date: March 2026
"""

from typing import Optional, Dict, Any, Callable, TypeVar, List
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import hashlib
import inspect

logger = logging.getLogger(__name__)

# Type variable for generic function caching
T = TypeVar('T')


class CacheKeyNamespace(str, Enum):
    """Cache key namespaces for organization"""
    # Core namespaces
    MPESA_TOKEN = "mpesa:token"
    MPESA_STATUS = "mpesa:status"
    USSD_SESSION = "ussd:session"
    TRANSACTION = "transaction"
    USER = "user"
    PHONE = "phone"
    FARMIQ_ID = "farmiq_id"
    
    # AI/ML namespaces
    EMBEDDING = "embedding"
    EMBEDDING_CACHE = "embedding:cache"
    MODEL = "model"
    TOKENIZER = "tokenizer"
    
    # Service-specific namespaces
    FARMGROW = "farmgrow"
    FARMSCORE = "farmscore"
    FARMSUITE = "farmsuite"
    RAG = "rag"
    
    # Credit scoring namespaces
    CREDIT_PROFILE = "credit:profile"
    CREDIT_SCORE = "credit:score"
    FEATURE = "feature"
    
    # Temporary/Session namespaces
    TEMP = "temp"
    SESSION = "session"
    VALIDATION = "validation"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def touch(self):
        """Update last access time"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expirations: int = 0
    errors: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def total_requests(self) -> int:
        """Total cache requests"""
        return self.hits + self.misses
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'evictions': self.evictions,
            'expirations': self.expirations,
            'errors': self.errors,
            'hit_rate_percent': f"{self.hit_rate:.1f}%",
            'total_requests': self.total_requests,
        }


class ApplicationCache:
    """
    Thread-safe in-process cache for the entire FarmIQ application
    Provides TTL expiration, LRU eviction, and comprehensive statistics
    """
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 300):
        """
        Initialize application cache
        
        Args:
            max_size: Maximum number of cache entries (LRU eviction)
            default_ttl: Default time-to-live in seconds for entries
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        logger.info(f"🚀 Cache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _generate_key(self, namespace: CacheKeyNamespace, identifier: str) -> str:
        """Generate namespaced cache key"""
        return f"{namespace.value}:{identifier}"
    
    def _cleanup_expired(self) -> int:
        """Remove all expired entries"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats.expirations += 1
        
        if expired_keys:
            logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def _enforce_size_limit(self):
        """Enforce max cache size using LRU eviction"""
        while len(self._cache) > self._max_size:
            # Remove least recently used (first item)
            lru_key, lru_entry = self._cache.popitem(last=False)
            self._stats.evictions += 1
            logger.debug(f"Cache LRU eviction: {lru_key}")
    
    def set(
        self,
        namespace: CacheKeyNamespace,
        identifier: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set cache value with TTL
        
        Args:
            namespace: Cache key namespace
            identifier: Unique identifier within namespace
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses default if None)
        """
        try:
            with self._lock:
                key = self._generate_key(namespace, identifier)
                ttl = ttl_seconds or self._default_ttl
                
                # Create cache entry
                entry = CacheEntry(
                    value=value,
                    created_at=datetime.utcnow(),
                    ttl_seconds=ttl
                )
                
                self._cache[key] = entry
                self._cache.move_to_end(key)  # Mark as recently used
                self._stats.sets += 1
                
                # Cleanup if getting full
                if len(self._cache) > self._max_size:
                    self._cleanup_expired()
                    self._enforce_size_limit()
                
                logger.debug(f"✓ Cache SET: {key} (ttl={ttl}s, size={len(self._cache)})")
        
        except Exception as e:
            self._stats.errors += 1
            logger.error(f"❌ Cache SET error: {str(e)}", exc_info=True)
    
    def get(
        self,
        namespace: CacheKeyNamespace,
        identifier: str
    ) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            namespace: Cache key namespace
            identifier: Unique identifier within namespace
            
        Returns:
            Cached value or None if expired/missing
        """
        try:
            with self._lock:
                key = self._generate_key(namespace, identifier)
                
                if key not in self._cache:
                    self._stats.misses += 1
                    logger.debug(f"✗ Cache MISS: {key}")
                    return None
                
                entry = self._cache[key]
                
                # Check expiration
                if entry.is_expired():
                    del self._cache[key]
                    self._stats.expirations += 1
                    self._stats.misses += 1
                    logger.debug(f"✗ Cache EXPIRED: {key}")
                    return None
                
                # Update access info and move to end
                entry.touch()
                self._cache.move_to_end(key)
                self._stats.hits += 1
                
                logger.debug(f"✓ Cache HIT: {key} (accessed {entry.access_count}x)")
                return entry.value
        
        except Exception as e:
            self._stats.errors += 1
            logger.error(f"❌ Cache GET error: {str(e)}", exc_info=True)
            return None
    
    def delete(self, namespace: CacheKeyNamespace, identifier: str) -> bool:
        """
        Delete cache entry
        
        Args:
            namespace: Cache key namespace
            identifier: Unique identifier within namespace
            
        Returns:
            True if deleted, False if not found
        """
        try:
            with self._lock:
                key = self._generate_key(namespace, identifier)
                
                if key in self._cache:
                    del self._cache[key]
                    self._stats.deletes += 1
                    logger.debug(f"✓ Cache DELETE: {key}")
                    return True
                
                return False
        
        except Exception as e:
            self._stats.errors += 1
            logger.error(f"❌ Cache DELETE error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete cache entries matching regex pattern
        
        Args:
            pattern: Regex pattern to match keys
            
        Returns:
            Number of entries deleted
        """
        try:
            import re
            with self._lock:
                regex = re.compile(pattern)
                keys_to_delete = [k for k in self._cache.keys() if regex.match(k)]
                
                for key in keys_to_delete:
                    del self._cache[key]
                
                logger.info(f"Cache DELETE PATTERN: {pattern} ({len(keys_to_delete)} entries)")
                return len(keys_to_delete)
        
        except Exception as e:
            self._stats.errors += 1
            logger.error(f"❌ Cache DELETE PATTERN error: {str(e)}")
            return 0
    
    def delete_namespace(self, namespace: CacheKeyNamespace) -> int:
        """
        Delete all entries in a namespace
        
        Args:
            namespace: Cache namespace to clear
            
        Returns:
            Number of entries deleted
        """
        return self.delete_pattern(f"^{namespace.value}:")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED ({count} entries removed)")
    
    def cleanup_expired(self) -> int:
        """
        Cleanup expired entries (call periodically)
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            return self._cleanup_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            return {
                'statistics': self._stats.to_dict(),
                'cache': {
                    'size': len(self._cache),
                    'max_size': self._max_size,
                    'utilization_percent': f"{(len(self._cache) / self._max_size * 100):.1f}%",
                    'memory_estimate_mb': len(self._cache) * 0.001,  # Rough estimate
                },
                'timestamp': datetime.utcnow().isoformat(),
            }
    
    def get_entry_info(self, namespace: CacheKeyNamespace, identifier: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a cache entry"""
        with self._lock:
            key = self._generate_key(namespace, identifier)
            
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            return {
                'key': key,
                'value_type': type(entry.value).__name__,
                'created_at': entry.created_at.isoformat(),
                'expires_at': (entry.created_at + timedelta(seconds=entry.ttl_seconds)).isoformat(),
                'ttl_seconds': entry.ttl_seconds,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed.isoformat(),
                'is_expired': entry.is_expired(),
                'age_seconds': (datetime.utcnow() - entry.created_at).total_seconds(),
            }


# Global cache instance
_cache_instance: Optional[ApplicationCache] = None


def get_cache() -> ApplicationCache:
    """Get or create the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        from config.settings import settings
        _cache_instance = ApplicationCache(
            max_size=settings.cache_max_size,
            default_ttl=settings.cache_default_ttl
        )
    return _cache_instance


def cache_decorator(
    namespace: CacheKeyNamespace,
    ttl_seconds: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Args:
        namespace: Cache namespace for this function
        ttl_seconds: Time-to-live for cached values
        key_builder: Custom function to build cache key from args/kwargs
                    Default: uses function name + args hash
    
    Example:
        @cache_decorator(CacheKeyNamespace.FARMGROW, ttl_seconds=3600)
        def expensive_function(user_id: str):
            return some_expensive_computation(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache()
            
            # Build cache key
            if key_builder:
                identifier = key_builder(*args, **kwargs)
            else:
                # Default: hash function signature and arguments
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                arg_str = str(bound.arguments)
                identifier = hashlib.md5(arg_str.encode()).hexdigest()
            
            # Try to get from cache
            cached_value = cache.get(namespace, identifier)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}({identifier})")
                return cached_value
            
            # Cache miss - call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(namespace, identifier, result, ttl_seconds)
            
            return result
        
        return wrapper
    
    return decorator


def invalidate_cache(namespace: CacheKeyNamespace, identifier: str) -> bool:
    """
    Invalidate a specific cache entry
    
    Args:
        namespace: Cache namespace
        identifier: Entry identifier
        
    Returns:
        True if deleted, False if not found
    """
    cache = get_cache()
    return cache.delete(namespace, identifier)


def invalidate_namespace(namespace: CacheKeyNamespace) -> int:
    """
    Invalidate all entries in a namespace
    
    Args:
        namespace: Cache namespace to clear
        
    Returns:
        Number of entries removed
    """
    cache = get_cache()
    return cache.delete_namespace(namespace)
