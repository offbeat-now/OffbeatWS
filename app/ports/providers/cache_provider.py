from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from datetime import timedelta

class CacheProvider(ABC):
    """Abstract cache provider interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set key-value pair with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache"""
        pass
    
    @abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values by keys"""
        pass
    
    @abstractmethod
    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple key-value pairs"""
        pass
    
    @abstractmethod
    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys, return count of deleted keys"""
        pass