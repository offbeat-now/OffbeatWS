from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.models.auth import User
from app.schemas.user import UserCreate, UserUpdate
from app.ports.repositories.user_repository import UserRepository
from app.adapters.db.sqlalchemy_base_repository import SQLAlchemyRepository
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.logger import get_logger

logger = get_logger("user_repository")


class SQLAlchemyUserRepository(SQLAlchemyRepository[User, UserCreate, UserUpdate], UserRepository):
    """SQLAlchemy implementation of user repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            stmt = select(User).where(
                and_(
                    User.email == email,
                    User.deleted == 'False'
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise DatabaseError(f"Failed to get user by email")
    
    async def get_by_user_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id (e.g., @sbk2k1)"""
        try:
            stmt = select(User).where(
                and_(
                    User.user_id == user_id,
                    User.deleted == 'False'
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by user_id {user_id}: {e}")
            raise DatabaseError(f"Failed to get user by user_id")
    
    async def get_verified_users(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[User]:
        """Get all verified users"""
        try:
            stmt = select(User).where(
                and_(
                    User.verified == 'True',
                    User.deleted == 'False'
                )
            )
            
            # Apply ordering
            if order_by:
                if order_by.startswith('-'):
                    order_field = order_by[1:]
                    if hasattr(User, order_field):
                        stmt = stmt.order_by(getattr(User, order_field).desc())
                else:
                    if hasattr(User, order_by):
                        stmt = stmt.order_by(getattr(User, order_by))
            else:
                stmt = stmt.order_by(User.created_at.desc())
            
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting verified users: {e}")
            raise DatabaseError(f"Failed to get verified users")
    
    async def get_users_by_type(
        self,
        user_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by type (Pro, Regular, Seasoned)"""
        try:
            stmt = select(User).where(
                and_(
                    User.user_type == user_type,
                    User.deleted == 'False'
                )
            ).offset(skip).limit(limit).order_by(User.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users by type {user_type}: {e}")
            raise DatabaseError(f"Failed to get users by type")
    
    async def get_users_by_karma_range(
        self,
        min_karma: int,
        max_karma: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by karma range"""
        try:
            conditions = [
                User.karma >= min_karma,
                User.deleted == 'False'
            ]
            
            if max_karma is not None:
                conditions.append(User.karma <= max_karma)
            
            stmt = select(User).where(
                and_(*conditions)
            ).offset(skip).limit(limit).order_by(User.karma.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users by karma range: {e}")
            raise DatabaseError(f"Failed to get users by karma range")
    
    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by name, user_id, or bio"""
        try:
            search_pattern = f"%{query}%"
            stmt = select(User).where(
                and_(
                    or_(
                        User.name.ilike(search_pattern),
                        User.user_id.ilike(search_pattern),
                        User.bio.ilike(search_pattern)
                    ),
                    User.deleted == 'False'
                )
            ).offset(skip).limit(limit).order_by(User.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users with query {query}: {e}")
            raise DatabaseError(f"Failed to search users")
    
    async def update_karma(self, user_id: UUID, karma_delta: int) -> Optional[User]:
        """Update user karma by delta amount"""
        try:
            # Get current user
            user = await self.get_by_id(user_id)
            if not user:
                raise NotFoundError("User", str(user_id))
            
            # Update karma
            new_karma = (user.karma or 0) + karma_delta
            stmt = update(User).where(User.id == user_id).values(
                karma=new_karma,
                updated_at=datetime.utcnow()
            ).returning(User)
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            updated_user = result.scalar_one_or_none()
            if updated_user:
                await self.session.refresh(updated_user)
            
            logger.debug(f"Updated karma for user {user_id}: {karma_delta}")
            return updated_user
        except NotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating karma for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update karma")
    
    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete user (set deleted=True, deleted_at=now)"""
        try:
            stmt = update(User).where(User.id == user_id).values(
                deleted='True',
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Soft deleted user {user_id}")
            
            return deleted
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error soft deleting user {user_id}: {e}")
            raise DatabaseError(f"Failed to soft delete user")
    
    async def restore_user(self, user_id: UUID) -> bool:
        """Restore soft deleted user"""
        try:
            stmt = update(User).where(User.id == user_id).values(
                deleted='False',
                deleted_at=None,
                updated_at=datetime.utcnow()
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            restored = result.rowcount > 0
            if restored:
                logger.debug(f"Restored user {user_id}")
            
            return restored
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error restoring user {user_id}: {e}")
            raise DatabaseError(f"Failed to restore user")
    
    async def verify_user(self, user_id: UUID) -> Optional[User]:
        """Mark user as verified"""
        try:
            stmt = update(User).where(User.id == user_id).values(
                verified='True',
                updated_at=datetime.utcnow()
            ).returning(User)
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            verified_user = result.scalar_one_or_none()
            if verified_user:
                await self.session.refresh(verified_user)
                logger.debug(f"Verified user {user_id}")
            
            return verified_user
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error verifying user {user_id}: {e}")
            raise DatabaseError(f"Failed to verify user")
    
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user statistics (posts count, comments count, etc.)"""
        try:
            # This is a placeholder - you'd need to join with posts, comments tables
            # For now, returning basic user info
            user = await self.get_by_id(user_id)
            if not user:
                raise NotFoundError("User", str(user_id))
            
            # Basic stats - extend this based on your other models
            stats = {
                "user_id": str(user.id),
                "karma": user.karma or 0,
                "verified": user.verified == 'True',
                "user_type": user.user_type,
                "created_at": user.created_at,
                "days_since_creation": (datetime.utcnow() - user.created_at).days if user.created_at else 0,
                # Add more stats as you implement other models
                "posts_count": 0,  # TODO: implement when Post model is available
                "comments_count": 0,  # TODO: implement when Comment model is available
            }
            
            return stats
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            raise DatabaseError(f"Failed to get user stats")
    
    async def get_users_created_between(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users created between dates"""
        try:
            stmt = select(User).where(
                and_(
                    User.created_at >= start_date,
                    User.created_at <= end_date,
                    User.deleted == 'False'
                )
            ).offset(skip).limit(limit).order_by(User.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users created between dates: {e}")
            raise DatabaseError(f"Failed to get users by date range")
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        try:
            stmt = select(func.count(User.id)).where(
                and_(
                    User.email == email,
                    User.deleted == 'False'
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one() > 0
        except Exception as e:
            logger.error(f"Error checking if email exists {email}: {e}")
            raise DatabaseError(f"Failed to check email existence")
    
    async def user_id_exists(self, user_id: str) -> bool:
        """Check if user_id already exists"""
        try:
            stmt = select(func.count(User.id)).where(
                and_(
                    User.user_id == user_id,
                    User.deleted == 'False'
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one() > 0
        except Exception as e:
            logger.error(f"Error checking if user_id exists {user_id}: {e}")
            raise DatabaseError(f"Failed to check user_id existence")
    
    async def get_users_by_oauth_type(
        self,
        oauth_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by OAuth type"""
        try:
            stmt = select(User).where(
                and_(
                    User.oauth_type == oauth_type,
                    User.deleted == 'False'
                )
            ).offset(skip).limit(limit).order_by(User.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users by oauth type {oauth_type}: {e}")
            raise DatabaseError(f"Failed to get users by oauth type")
    
    # Override base methods to include soft delete logic
    async def get_by_id(self, id: UUID) -> Optional[User]:
        """Get user by ID (excluding soft deleted)"""
        try:
            stmt = select(User).where(
                and_(
                    User.id == id,
                    User.deleted == 'False'
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {id}: {e}")
            raise DatabaseError(f"Failed to get user by ID")
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[User]:
        """Get multiple users (excluding soft deleted)"""
        # Add soft delete filter to existing filters
        if filters is None:
            filters = {}
        filters['deleted'] = 'False'
        
        return await super().get_multi(skip, limit, filters, order_by)
    
    async def get_user_count_in_db(self) -> int:
        """Get total user count (excluding soft deleted)"""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.deleted == 'False')
        )
        return result.scalar_one()