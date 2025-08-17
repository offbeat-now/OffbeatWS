import asyncio
import time
from typing import Any, Optional, Union, Dict
from datetime import timedelta
from dataclasses import dataclass
from ports.cache_provider import CacheProvider
from utils.logger import get_logger

logger = get_logger("memory_cache")

@dataclass
class CacheItem:
    """Cache item with expiration"""
    value: Any
    expires_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if item is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

class MemoryCache(CacheProvider):
    """In-memory cache implementation"""
    
    def __init__(self):
        self._cache: Dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_items())
    
    async def _cleanup_expired_items(self):
        """Background task to clean up expired items"""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                async with self._lock:
                    expired_keys = [
                        key for key, item in self._cache.items() 
                        if item.is_expired()
                    ]
                    for key in expired_keys:
                        del self._cache[key]
                    
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def _get_expiration_time(self, ttl: Optional[Union[int, timedelta]]) -> Optional[float]:
        """Calculate expiration timestamp"""
        if ttl is None:
            return None
        
        if isinstance(ttl, timedelta):
            seconds = ttl.total_seconds()
        else:
            seconds = ttl
        
        return time.time() + seconds
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        async with self._lock:
            item = self._cache.get(key)
            
            if item is None:
                return None
            
            if item.is_expired():
                del self._cache[key]
                return None
            
            return item.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set key-value pair with optional TTL"""
        try:
            expires_at = self._get_expiration_time(ttl)
            
            async with self._lock:
                self._cache[key] = CacheItem(value=value, expires_at=expires_at)
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self._lock:
            item = self._cache.get(key)
            
            if item is None:
                return False
            
            if item.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            async with self._lock:
                self._cache.clear()
            return True
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values by keys"""
        result = {}
        
        async with self._lock:
            expired_keys = []
            
            for key in keys:
                item = self._cache.get(key)
                
                if item is None:
                    continue
                
                if item.is_expired():
                    expired_keys.append(key)
                    continue
                
                result[key] = item.value
            
            # Clean up expired keys
            for key in expired_keys:
                del self._cache[key]
        
        return result
    
    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple key-value pairs"""
        try:
            expires_at = self._get_expiration_time(ttl)
            
            async with self._lock:
                for key, value in mapping.items():
                    self._cache[key] = CacheItem(value=value, expires_at=expires_at)
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting multiple keys: {e}")
            return False
    
    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys, return count of deleted keys"""
        deleted_count = 0
        
        async with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    deleted_count += 1
        
        return deleted_count
    
    def get_cache_info(self) -> dict:
        """Get cache statistics"""
        return {
            "total_items": len(self._cache),
            "expired_items": sum(1 for item in self._cache.values() if item.is_expired())
        }
    
    async def shutdown(self):
        """Shutdown cache and cleanup resources"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            self._cache.clear()
