"""
In-Process Payment Caching Service
Replaces Redis with in-memory caching for faster performance and lower infrastructure

Features:
- OAuth token caching (M-Pesa)
- Session management (Afrika Talking USSD)
- Transaction state tracking (all providers)
- Automatic TTL expiration
- Cache statistics and monitoring
- Thread-safe operations

Author: FarmIQ Backend Team
Date: March 2026
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass
import logging
import threading
import time
from enum import Enum

logger = logging.getLogger(__name__)


class CacheKeyType(str, Enum):
    """Cache key namespacing"""
    MPESA_TOKEN = "mpesa:token"
    USSD_SESSION = "ussd:session"
    TRANSACTION = "transaction"
    USER = "user"
    PHONE = "phone"
    FARMIQ_ID = "farmiq_id"


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    errors: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'expirations': self.expirations,
            'errors': self.errors,
            'hit_rate': f"{self.hit_rate:.1f}%",
            'total_requests': self.hits + self.misses,
        }


class PaymentCache:
    """
    In-process cache for payment operations
    Thread-safe with automatic TTL expiration
    """
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize payment cache
        
        Args:
            max_size: Maximum number of cache entries (LRU eviction)
        """
        self.cache: OrderedDict[str, tuple[Any, datetime, int]] = OrderedDict()
        self.max_size = max_size
        self.lock = threading.RLock()
        self.stats = CacheStats()
        
        # Cache configuration by type
        self.ttl_config = {
            CacheKeyType.MPESA_TOKEN: 3500,  # M-Pesa token ~1 hour
            CacheKeyType.USSD_SESSION: 900,   # USSD session 15 minutes
            CacheKeyType.TRANSACTION: 3600,   # Transaction 1 hour
            CacheKeyType.USER: 1800,          # User data 30 minutes
            CacheKeyType.PHONE: 1800,         # Phone verification 30 minutes
            CacheKeyType.FARMIQ_ID: 1800,     # FarmIQ ID 30 minutes
        }
    
    def _generate_key(self, key_type: CacheKeyType, identifier: str) -> str:
        """Generate namespaced cache key"""
        return f"{key_type.value}:{identifier}"
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, (value, created_at, ttl) in self.cache.items():
            if now > created_at + timedelta(seconds=ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self.stats.expirations += 1
        
        return len(expired_keys)
    
    def _enforce_size_limit(self):
        """Enforce max cache size using LRU eviction"""
        while len(self.cache) > self.max_size:
            # Remove least recently used (first item)
            self.cache.popitem(last=False)
            self.stats.evictions += 1
    
    def set(
        self, 
        key_type: CacheKeyType, 
        identifier: str, 
        value: Any,
        ttl_seconds: Optional[int] = None
    ):
        """
        Set cache value with TTL
        
        Args:
            key_type: Type of cache key
            identifier: Unique identifier (e.g., phone number, transaction ID)
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses default per type if None)
        """
        try:
            with self.lock:
                key = self._generate_key(key_type, identifier)
                ttl = ttl_seconds or self.ttl_config.get(key_type, 300)
                
                self.cache[key] = (value, datetime.utcnow(), ttl)
                self.cache.move_to_end(key)  # Mark as recently used
                
                self._enforce_size_limit()
                
                logger.debug(f"Cache SET: {key} (ttl={ttl}s)")
        
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache SET error: {str(e)}")
    
    def get(self, key_type: CacheKeyType, identifier: str) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            key_type: Type of cache key
            identifier: Unique identifier
            
        Returns:
            Cached value or None if expired/missing
        """
        try:
            with self.lock:
                key = self._generate_key(key_type, identifier)
                
                if key not in self.cache:
                    self.stats.misses += 1
                    logger.debug(f"Cache MISS: {key}")
                    return None
                
                value, created_at, ttl = self.cache[key]
                now = datetime.utcnow()
                
                # Check expiration
                if now > created_at + timedelta(seconds=ttl):
                    del self.cache[key]
                    self.stats.expirations += 1
                    self.stats.misses += 1
                    logger.debug(f"Cache EXPIRED: {key}")
                    return None
                
                # Move to end (mark as recently used)
                self.cache.move_to_end(key)
                self.stats.hits += 1
                
                logger.debug(f"Cache HIT: {key}")
                return value
        
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache GET error: {str(e)}")
            return None
    
    def delete(self, key_type: CacheKeyType, identifier: str) -> bool:
        """Delete cache entry"""
        try:
            with self.lock:
                key = self._generate_key(key_type, identifier)
                
                if key in self.cache:
                    del self.cache[key]
                    logger.debug(f"Cache DELETE: {key}")
                    return True
                
                return False
        
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache DELETE error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete cache entries matching pattern (regex)"""
        try:
            import re
            with self.lock:
                regex = re.compile(pattern)
                keys_to_delete = [k for k in self.cache.keys() if regex.match(k)]
                
                for key in keys_to_delete:
                    del self.cache[key]
                
                logger.info(f"Cache DELETE PATTERN: {pattern} ({len(keys_to_delete)} entries)")
                return len(keys_to_delete)
        
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache DELETE PATTERN error: {str(e)}")
            return 0
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            logger.info("Cache CLEARED")
    
    def cleanup_expired(self) -> int:
        """Cleanup expired entries (should be called periodically)"""
        with self.lock:
            return self._cleanup_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                **self.stats.to_dict(),
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'memory_estimate_mb': len(self.cache) * 0.001,  # Rough estimate
            }
    
    def get_size(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.cache)
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for cache system"""
        stats = self.get_stats()
        
        return {
            'status': 'healthy' if stats['errors'] < 10 else 'degraded',
            'cache_size': stats['cache_size'],
            'max_size': stats['max_size'],
            'usage_percent': (stats['cache_size'] / stats['max_size']) * 100,
            'hit_rate': stats['hit_rate'],
            'errors': stats['errors'],
            'uptime_since_start': 'running',
        }


# Global cache instance
_payment_cache = PaymentCache(max_size=10000)


# ===================== CONVENIENCE FUNCTIONS =====================

def cache_mpesa_token(token: str, phone_number: str, ttl_seconds: int = 3500):
    """Cache M-Pesa OAuth token"""
    _payment_cache.set(CacheKeyType.MPESA_TOKEN, phone_number, token, ttl_seconds)


def get_mpesa_token(phone_number: str) -> Optional[str]:
    """Retrieve cached M-Pesa OAuth token"""
    return _payment_cache.get(CacheKeyType.MPESA_TOKEN, phone_number)


def cache_ussd_session(session_id: str, session_data: Dict[str, Any], ttl_seconds: int = 900):
    """Cache USSD session data"""
    _payment_cache.set(CacheKeyType.USSD_SESSION, session_id, session_data, ttl_seconds)


def get_ussd_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached USSD session"""
    return _payment_cache.get(CacheKeyType.USSD_SESSION, session_id)


def cache_transaction(transaction_id: str, transaction_data: Dict[str, Any], ttl_seconds: int = 3600):
    """Cache transaction state"""
    _payment_cache.set(CacheKeyType.TRANSACTION, transaction_id, transaction_data, ttl_seconds)


def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached transaction"""
    return _payment_cache.get(CacheKeyType.TRANSACTION, transaction_id)


def cache_user(farmiq_id: str, user_data: Dict[str, Any], ttl_seconds: int = 1800):
    """Cache user data"""
    _payment_cache.set(CacheKeyType.USER, farmiq_id, user_data, ttl_seconds)


def get_user(farmiq_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached user data"""
    return _payment_cache.get(CacheKeyType.USER, farmiq_id)


def get_cache_instance() -> PaymentCache:
    """Get global cache instance"""
    return _payment_cache
