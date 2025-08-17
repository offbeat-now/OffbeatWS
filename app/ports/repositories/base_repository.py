from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from sqlalchemy.ext.declarative import DeclarativeMeta

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Abstract base repository interface"""
    
    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get record by ID"""
        pass
    
    @abstractmethod
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering"""
        pass
    
    @abstractmethod
    async def update(
        self,
        id: Any,
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Update record by ID"""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        pass
    
    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """Check if record exists by ID"""
        pass