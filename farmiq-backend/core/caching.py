"""
FarmIQ Performance Optimization - Response Caching Layer
Phase 5.2 - Implements in-memory caching with TTL and automatic invalidation
"""
from typing import Optional, Any, Dict, Callable, TypeVar, Coroutine
from functools import wraps
from datetime import datetime, timedelta
from collections import OrderedDict
import logging
import asyncio
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for cached values


# ============================================================================
# IN-MEMORY CACHE IMPLEMENTATION
# ============================================================================

class CacheEntry:
    """Single cache entry with TTL and metadata"""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hit_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.created_at + self.ttl
    
    def access(self) -> Any:
        """Access value and update statistics"""
        self.hit_count += 1
        self.last_accessed = datetime.utcnow()
        return self.value


class InMemoryCache:
    """
    Simple in-memory cache with TTL support
    For distributed caching, use Redis (add redis-py integration)
    """
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expires': 0,
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache[key]
            self.stats['expires'] += 1
            self.stats['misses'] += 1
            return None
        
        # Update statistics and return value
        self.stats['hits'] += 1
        return entry.access()
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache"""
        # Remove oldest entry if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats['evictions'] += 1
        
        self.cache[key] = CacheEntry(value, ttl_seconds)
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
    
    def delete(self, key: str):
        """Delete specific cache entry"""
        if key in self.cache:
            del self.cache[key]
    
    def delete_pattern(self, pattern: str):
        """Delete cache entries matching pattern"""
        import re
        regex = re.compile(pattern)
        keys_to_delete = [k for k in self.cache.keys() if regex.match(k)]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return len(keys_to_delete)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expires': 0,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (
            self.stats['hits'] / total_requests
            if total_requests > 0 else 0
        )
        
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': f"{hit_rate * 100:.1f}%",
            'total_requests': total_requests,
        }


# Global cache instance
_cache = InMemoryCache(max_size=5000)


# ============================================================================
# CACHE KEY GENERATION
# ============================================================================

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    Used to cache function results based on parameters
    """
    # Create unique string from arguments
    key_parts = []
    
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif hasattr(arg, 'id'):  # ORM objects
            key_parts.append(str(arg.id))
        else:
            # For complex objects, use their string representation
            key_parts.append(str(arg)[:50])
    
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
    
    key_string = "|".join(key_parts)
    
    # Hash to shorter key
    hash_obj = hashlib.md5(key_string.encode())
    return f"cache_{hash_obj.hexdigest()}"


# ============================================================================
# CACHE DECORATORS
# ============================================================================

def cache(ttl_seconds: int = 300):
    """
    Decorator to cache function results
    
    Usage:
        @cache(ttl_seconds=600)
        def get_farm_health_score(farm_id: UUID) -> float:
            return expensive_calculation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(*args, **kwargs)
            
            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    
    return decorator


def async_cache(ttl_seconds: int = 300):
    """
    Decorator to cache async function results
    
    Usage:
        @async_cache(ttl_seconds=600)
        async def get_farm_data(farm_id: UUID) -> Dict:
            return await expensive_query()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(*args, **kwargs)
            
            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    
    return decorator


# ============================================================================
# CACHE INVALIDATION
# ============================================================================

class CacheInvalidator:
    """Helper for cache invalidation strategies"""
    
    @staticmethod
    def invalidate_by_farm(farm_id: str):
        """Invalidate all caches related to a farm"""
        keys_deleted = _cache.delete_pattern(f"cache_.*farm_id.*{farm_id}.*")
        logger.info(f"Invalidated {keys_deleted} cache entries for farm {farm_id}")
    
    @staticmethod
    def invalidate_by_user(user_id: str):
        """Invalidate all caches related to a user"""
        keys_deleted = _cache.delete_pattern(f"cache_.*user_id.*{user_id}.*")
        logger.info(f"Invalidated {keys_deleted} cache entries for user {user_id}")
    
    @staticmethod
    def invalidate_by_pattern(pattern: str):
        """Invalidate caches matching pattern"""
        keys_deleted = _cache.delete_pattern(pattern)
        logger.info(f"Invalidated {keys_deleted} cache entries matching {pattern}")
    
    @staticmethod
    def invalidate_all():
        """Clear entire cache"""
        _cache.clear()
        logger.info("Entire cache cleared")


# ============================================================================
# CACHE STATISTICS & MONITORING
# ============================================================================

class CacheMonitor:
    """Monitor cache performance"""
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get cache statistics"""
        return _cache.get_stats()
    
    @staticmethod
    def get_detailed_stats() -> Dict[str, Any]:
        """Get detailed cache entry statistics"""
        entries = []
        for key, entry in _cache.cache.items():
            entries.append({
                'key': key[:50],  # Truncate long keys
                'hit_count': entry.hit_count,
                'created_at': entry.created_at.isoformat(),
                'last_accessed': entry.last_accessed.isoformat(),
                'expired': entry.is_expired(),
            })
        
        # Sort by hit count (most popular first)
        entries.sort(key=lambda x: x['hit_count'], reverse=True)
        
        return {
            'total_entries': len(entries),
            'top_entries': entries[:10],
        }


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    return CacheMonitor.get_stats()


# ============================================================================
# HTTP RESPONSE CACHING (for GET endpoints)
# ============================================================================

class ResponseCache:
    """Manage HTTP response caching"""
    
    @staticmethod
    def get_cache_headers(ttl_seconds: int) -> Dict[str, str]:
        """Generate cache headers for HTTP responses"""
        return {
            'Cache-Control': f'public, max-age={ttl_seconds}',
            'Expires': (
                datetime.utcnow() + timedelta(seconds=ttl_seconds)
            ).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'Last-Modified': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
        }
    
    @staticmethod
    def get_no_cache_headers() -> Dict[str, str]:
        """Generate headers to prevent caching"""
        return {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Expires': '0',
            'Pragma': 'no-cache',
        }


# ============================================================================
# CACHE WARMING (Preload frequently accessed data)
# ============================================================================

class CacheWarmer:
    """Pre-load cache with frequently accessed data"""
    
    @staticmethod
    async def warm_cache(session, farm_id: str):
        """Warm cache for a specific farm"""
        logger.info(f"Warming cache for farm {farm_id}")
        
        # Pre-load frequently accessed farm data
        # This is a placeholder - implement based on your actual queries
        
        logger.info(f"Cache warmed for farm {farm_id}")
    
    @staticmethod
    async def warm_critical_data(session):
        """Warm cache with critical system data"""
        logger.info("Starting critical data cache warming")
        
        # Pre-load:
        # - All farms (if reasonable size)
        # - Reference data
        # - Configuration data
        
        logger.info("Critical data cache warming complete")
