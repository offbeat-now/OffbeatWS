from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.auth import User
from app.schemas.user import UserCreate, UserUpdate
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate], ABC):
    """Abstract user repository interface"""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id (e.g., @sbk2k1)"""
        pass
    
    @abstractmethod
    async def get_verified_users(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[User]:
        """Get all verified users"""
        pass
    
    @abstractmethod
    async def get_users_by_type(
        self,
        user_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by type (Pro, Regular, Seasoned)"""
        pass
    
    @abstractmethod
    async def get_users_by_karma_range(
        self,
        min_karma: int,
        max_karma: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by karma range"""
        pass
    
    @abstractmethod
    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by name, user_id, or bio"""
        pass
    
    @abstractmethod
    async def update_karma(self, user_id: UUID, karma_delta: int) -> Optional[User]:
        """Update user karma by delta amount"""
        pass
    
    @abstractmethod
    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete user (set deleted=True, deleted_at=now)"""
        pass
    
    @abstractmethod
    async def restore_user(self, user_id: UUID) -> bool:
        """Restore soft deleted user"""
        pass
    
    @abstractmethod
    async def verify_user(self, user_id: UUID) -> Optional[User]:
        """Mark user as verified"""
        pass
    
    @abstractmethod
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user statistics (posts count, comments count, etc.)"""
        pass
    
    @abstractmethod
    async def get_users_created_between(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users created between dates"""
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        pass
    
    @abstractmethod
    async def user_id_exists(self, user_id: str) -> bool:
        """Check if user_id already exists"""
        pass
    
    @abstractmethod
    async def get_users_by_oauth_type(
        self,
        oauth_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by OAuth type"""
        pass

    @abstractmethod
    async def get_user_count_in_db(self) -> int:
        """Get total user count in the database"""
        pass