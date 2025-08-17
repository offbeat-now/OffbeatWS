from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError, NoResultFound
from app.ports.repositories.base_repository import BaseRepository
from app.core.exceptions import DatabaseError, NotFoundError, ConflictError
from app.utils.logger import get_logger

logger = get_logger("sqlalchemy_repository")

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class SQLAlchemyRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """SQLAlchemy implementation of base repository"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new record"""
        try:
            # Convert Pydantic model to dict
            if hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict(exclude_unset=True)
            elif hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_data = obj_in
            
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            logger.debug(f"Created {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
        
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise ConflictError(f"Record already exists or violates constraints")
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to create record")
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get record by ID"""
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {id}: {e}")
            raise DatabaseError(f"Failed to get record by ID")
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering"""
        try:
            stmt = select(self.model)
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        attr = getattr(self.model, key)
                        if isinstance(value, list):
                            conditions.append(attr.in_(value))
                        elif isinstance(value, dict):
                            # Support for range queries, like {"gte": 10, "lte": 20}
                            if "gte" in value:
                                conditions.append(attr >= value["gte"])
                            if "lte" in value:
                                conditions.append(attr <= value["lte"])
                            if "gt" in value:
                                conditions.append(attr > value["gt"])
                            if "lt" in value:
                                conditions.append(attr < value["lt"])
                            if "eq" in value:
                                conditions.append(attr == value["eq"])
                            if "ne" in value:
                                conditions.append(attr != value["ne"])
                            if "like" in value:
                                conditions.append(attr.like(f"%{value['like']}%"))
                            if "ilike" in value:
                                conditions.append(attr.ilike(f"%{value['ilike']}%"))
                        else:
                            conditions.append(attr == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            # Apply ordering
            if order_by:
                if order_by.startswith('-'):
                    # Descending order
                    order_field = order_by[1:]
                    if hasattr(self.model, order_field):
                        stmt = stmt.order_by(getattr(self.model, order_field).desc())
                else:
                    # Ascending order
                    if hasattr(self.model, order_by):
                        stmt = stmt.order_by(getattr(self.model, order_by))
            
            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to get records")
    
    async def update(
        self,
        id: Any,
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Update record by ID"""
        try:
            # Get existing record
            db_obj = await self.get_by_id(id)
            if not db_obj:
                raise NotFoundError(self.model.__name__, str(id))
            
            # Convert update data to dict
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            elif hasattr(obj_in, 'model_dump'):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            logger.debug(f"Updated {self.model.__name__} with ID: {id}")
            return db_obj
        
        except NotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error updating {self.model.__name__}: {e}")
            raise ConflictError(f"Update violates constraints")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating {self.model.__name__} with ID {id}: {e}")
            raise DatabaseError(f"Failed to update record")
    
    async def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Deleted {self.model.__name__} with ID: {id}")
            
            return deleted
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting {self.model.__name__} with ID {id}: {e}")
            raise DatabaseError(f"Failed to delete record")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        try:
            stmt = select(func.count(self.model.id))
            
            # Apply filters (same logic as get_multi)
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        attr = getattr(self.model, key)
                        if isinstance(value, list):
                            conditions.append(attr.in_(value))
                        elif isinstance(value, dict):
                            if "gte" in value:
                                conditions.append(attr >= value["gte"])
                            if "lte" in value:
                                conditions.append(attr <= value["lte"])
                            if "gt" in value:
                                conditions.append(attr > value["gt"])
                            if "lt" in value:
                                conditions.append(attr < value["lt"])
                            if "eq" in value:
                                conditions.append(attr == value["eq"])
                            if "ne" in value:
                                conditions.append(attr != value["ne"])
                            if "like" in value:
                                conditions.append(attr.like(f"%{value['like']}%"))
                            if "ilike" in value:
                                conditions.append(attr.ilike(f"%{value['ilike']}%"))
                        else:
                            conditions.append(attr == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return result.scalar_one()
        
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to count records")
    
    async def exists(self, id: Any) -> bool:
        """Check if record exists by ID"""
        try:
            stmt = select(func.count(self.model.id)).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one() > 0
        
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} with ID {id}: {e}")
            raise DatabaseError(f"Failed to check record existence")