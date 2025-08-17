import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import redis.asyncio as redis
from ports.cache_provider import CacheProvider
from core.config import get_settings
from utils.logger import get_logger

logger = get_logger("redis_cache")

class RedisCache(CacheProvider):
    """Redis cache implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        self._redis: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if not self._redis:
            if self.settings.redis_url:
                self._redis = redis.from_url(self.settings.redis_url)
            else:
                self._redis = redis.Redis(
                    host=self.settings.redis_host,
                    port=self.settings.redis_port,
                    db=self.settings.redis_db,
                    password=self.settings.redis_password,
                    decode_responses=False,  # We handle encoding ourselves
                )
            logger.info("Connected to Redis")
        
        return self._redis
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first for simple types
            return json.dumps(value).encode('utf-8')
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            redis_client = await self._get_redis()
            await redis_client.flushdb()
            return True
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values by keys"""
        try:
            redis_client = await self._get_redis()
            pipeline = redis_client.pipeline()
            
            for key in keys:
                pipeline.get(key)
            
            results = await pipeline.execute()
            
            output = {}
            for key, data in zip(keys, results):
                if data is not None:
                    try:
                        output[key] = self._deserialize(data)
                    except Exception as e:
                        logger.error(f"Error deserializing key {key}: {e}")
            
            return output
        
        except Exception as e:
            logger.error(f"Error getting multiple keys: {e}")
            return {}
    
    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple key-value pairs"""
        try:
            redis_client = await self._get_redis()
            pipeline = redis_client.pipeline()
            ttl_seconds = self._get_ttl_seconds(ttl)
            
            for key, value in mapping.items():
                serialized_value = self._serialize(value)
                if ttl_seconds:
                    pipeline.setex(key, ttl_seconds, serialized_value)
                else:
                    pipeline.set(key, serialized_value)
            
            await pipeline.execute()
            return True
        
        except Exception as e:
            logger.error(f"Error setting multiple keys: {e}")
            return False
    
    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys, return count of deleted keys"""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(*keys)
            return result
        
        except Exception as e:
            logger.error(f"Error deleting multiple keys: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
