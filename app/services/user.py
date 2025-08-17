from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status

from app.ports.providers.storage_provider import StorageProvider
from app.ports.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserUpdateResponse, 
    UserCreateResponse, UserLoginResponse, UserLogin
)
from app.models.auth import User
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.password import PasswordManager
from app.utils.jwt import JWTManager
from app.utils.logger import get_logger
from app.utils.file_utils import FileUtils

logger = get_logger("user_service")


class UserService:
    """User service layer containing business logic"""
    
    def __init__(
        self, 
        user_repository: UserRepository,
        jwt_manager: JWTManager,
        file_utils: FileUtils,
        storage_provider: StorageProvider
    ):
        self.user_repository = user_repository
        self.jwt_manager = jwt_manager
        self.file_utils = file_utils
        self.storage_provider = storage_provider

    async def create_user(self, user_create: UserCreate) -> UserCreateResponse:
        """Create a new user"""
        try:
            # Check if email already exists
            if await self.user_repository.email_exists(user_create.email):
                return UserCreateResponse(
                    error=True,
                    message="Email already registered",
                    created=False
                )
            
            # Check if user_id already exists
            if await self.user_repository.user_id_exists(user_create.user_id):
                return UserCreateResponse(
                    error=True,
                    message="User ID already taken",
                    created=False
                )
            
            # Hash password
            user_create.password = PasswordManager.hash_password(user_create.password)
            
            # Create user
            user = await self.user_repository.create(user_create)
            
            logger.info(f"Created user: {user.user_id} ({user.email})")
            
            return UserCreateResponse(
                error=False,
                message="User created successfully",
                created=True
            )
        
        except ConflictError as e:
            logger.warning(f"Conflict creating user: {e}")
            return UserCreateResponse(
                error=True,
                message="User already exists",
                created=False
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return UserCreateResponse(
                error=True,
                message="Failed to create user",
                created=False
            )
    
    async def authenticate_user(self, login_data: UserLogin) -> UserLoginResponse:
        """Authenticate user with email/password and return tokens"""
        try:
            # Get user by email
            user = await self.user_repository.get_by_email(login_data.email)
            if not user:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                return UserLoginResponse(
                    error=True,
                    message="Invalid email or password"
                )
            
            # Verify password
            if not PasswordManager.verify_password(login_data.password, user.password):
                logger.warning(f"Invalid password attempt for user: {login_data.email}")
                return UserLoginResponse(
                    error=True,
                    message="Invalid email or password"
                )
            
            # Check if user account is active (not soft deleted ie deleted_at is not null)
            if user.deleted_at is not None:
                logger.warning(f"Deleted user attempted login: {login_data.email}")
                return UserLoginResponse(
                    error=True,
                    message="Account not found"
                )
            
            # Generate tokens
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "user_id": user.user_id,
                "type": "access"
            }
            
            refresh_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "type": "refresh"
            }
            
            access_token = self.jwt_manager.create_access_token(data=access_token_data)
            refresh_token = self.jwt_manager.create_refresh_token(data=refresh_token_data)
            
            # Get token expiration time
            expires_in = self.jwt_manager.settings.access_token_expire_minutes * 60  # seconds
            
            logger.info(f"User authenticated successfully: {user.email}")
            
            return UserLoginResponse(
                error=False,
                message="Login successful",
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                email=user.email,
                name=user.name
            )
        
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return UserLoginResponse(
                error=True,
                message="Authentication failed"
            )

    async def refresh_access_token(self, refresh_token: str) -> UserLoginResponse:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            if not payload:
                logger.warning("Invalid refresh token used")
                return UserLoginResponse(
                    error=True,
                    message="Invalid or expired refresh token"
                )
            
            # Get user from token payload
            user_id = payload.get("sub")
            if not user_id:
                return UserLoginResponse(
                    error=True,
                    message="Invalid token payload"
                )
            
            # Get current user data
            user = await self.user_repository.get_by_id(UUID(user_id))
            if not user or user.deleted == 'True':
                logger.warning(f"Refresh token used for non-existent user: {user_id}")
                return UserLoginResponse(
                    error=True,
                    message="User not found"
                )
            
            # Generate new tokens
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "user_id": user.user_id,
                "type": "access"
            }
            
            new_refresh_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "type": "refresh"
            }
            
            new_access_token = self.jwt_manager.create_access_token(data=access_token_data)
            new_refresh_token = self.jwt_manager.create_refresh_token(data=new_refresh_token_data)

            expires_in = self.jwt_manager.settings.access_token_expire_minutes * 60

            logger.info(f"Tokens refreshed for user: {user.email}")
            
            return UserLoginResponse(
                error=False,
                message="Tokens refreshed successfully",
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in,
                email=user.email,
                name=user.name
            )

        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return UserLoginResponse(
                error=True,
                message="Failed to refresh token"
            )

    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by invalidating refresh token"""
        try:
            # Verify the refresh token
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            if not payload:
                logger.warning("Invalid refresh token provided for logout")
                return False
            
            user_id = payload.get("sub")
            if user_id:
                logger.info(f"User logged out: {user_id}")
            
            # In a production app, you'd want to:
            # 1. Add the token to a blacklist/revocation list
            # 2. Store blacklisted tokens in Redis with expiration
            # 3. Check blacklist in token verification
            
            # For now, we'll just log the logout
            # TODO: Implement token blacklisting
            
            return True
        
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False


    async def get_user_by_id(self, user_id: UUID) -> UserResponse:
        """Get user by ID"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return UserResponse(
                    error=True,
                    message="User not found"
                )
            
            return UserResponse(
                error=False,
                message="User found",
                id=user.id,
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                image=user.image,
                dob=user.dob,
                gender=user.gender,
                user_type=user.user_type,
                karma=user.karma,
                bio=user.bio,
                verified=str(user.verified),
                deleted=str(user.deleted),
                oauth_type=user.oauth_type,
                created_at=user.created_at,
                updated_at=user.updated_at,
                deleted_at=user.deleted_at
            )


        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return UserResponse(
                error=True,
                message="Failed to get user"
            )
        
    async def verify_email(self, token: str) -> UserResponse:
        """Verify user email using verification token"""
        try:
            # Verify email verification token
            payload = self.jwt_manager.verify_token(token, "email_verification")
            if not payload:
                return UserResponse(
                    id=UUID('00000000-0000-0000-0000-000000000000'),
                    user_id="",
                    email="",
                    dob=datetime.now().date(),
                    gender="",
                    error=True,
                    message="Invalid or expired verification token"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                return UserResponse(
                    id=UUID('00000000-0000-0000-0000-000000000000'),
                    user_id="",
                    email="",
                    dob=datetime.now().date(),
                    gender="",
                    error=True,
                    message="Invalid token payload"
                )
            
            # Verify the user
            verified_user = await self.user_repository.verify_user(UUID(user_id))
            if not verified_user:
                return UserResponse(
                    id=UUID(user_id),
                    user_id="",
                    email="",
                    dob=datetime.now().date(),
                    gender="",
                    error=True,
                    message="User not found or already verified"
                )
            
            logger.info(f"Email verified for user: {verified_user.email}")
            return UserResponse.from_orm(verified_user)
        
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return UserResponse(
                id=UUID('00000000-0000-0000-0000-000000000000'),
                user_id="",
                email="",
                dob=datetime.now().date(),
                gender="",
                error=True,
                message="Email verification failed"
            )

    
    async def get_user_by_email_or_user_id(self, email: str, user_id: Optional[str] = None) -> Optional[User]:
        """Get user by email or user_id - if any one exists return that user"""
        try:
            user = await self.user_repository.get_by_email(email)
            if user:
                return user
            user = await self.user_repository.get_by_user_id(user_id)
            if user:
                return user
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email} or user_id {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user"
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return await self.user_repository.get_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user"
            )
    
    async def get_user_by_user_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        try:
            return await self.user_repository.get_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user by user_id {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user"
            )
    
    async def update_user(
        self, 
        user: User, 
        user_update: UserUpdate
    ) -> UserUpdateResponse:
        """Update user information"""
        try:
            # Validate update data
            update_data = user_update.dict(exclude_unset=True)
            
            # Check if user_id is being changed and if it already exists
            if 'user_id' in update_data and update_data['user_id'] != user.user_id:
                if await self.user_repository.user_id_exists(update_data['user_id']):
                    return UserUpdateResponse(
                        error=True,
                        message="User ID already taken",
                        **user.__dict__
                    )
            
            # Update user
            updated_user = await self.user_repository.update(user.id, user_update)
            if not updated_user:
                return UserUpdateResponse(
                    error=True,
                    message="Failed to update user",
                    **user.__dict__
                )
            
            logger.info(f"Updated user: {updated_user.user_id}")
            
            return UserUpdateResponse(
                error=False,
                message="User updated successfully",
                **updated_user.__dict__
            )
        
        except ConflictError as e:
            logger.warning(f"Conflict updating user {user.id}: {e}")
            return UserUpdateResponse(
                error=True,
                message="Update violates constraints",
                **user.__dict__
            )
        except Exception as e:
            logger.error(f"Error updating user {user.id}: {e}")
            return UserUpdateResponse(
                error=True,
                message="Failed to update user",
                **user.__dict__
            )
    
    async def upload_user_picture(self, user: User, file_url: str) -> UserResponse:
        """Update user profile picture"""
        try:
            user_update = UserUpdate(image=file_url)
            updated_user = await self.user_repository.update(user.id, user_update)
            
            if not updated_user:
                return UserResponse(
                    **user.__dict__,
                    error=True,
                    message="Failed to update profile picture"
                )
            
            logger.info(f"Updated profile picture for user: {updated_user.user_id}")
            return UserResponse.from_orm(updated_user)
        
        except Exception as e:
            logger.error(f"Error updating profile picture for user {user.id}: {e}")
            return UserResponse(
                **user.__dict__,
                error=True,
                message="Failed to update profile picture"
            )
    
    async def update_user_karma(self, user_id: UUID, karma_delta: int) -> Optional[User]:
        """Update user karma"""
        try:
            updated_user = await self.user_repository.update_karma(user_id, karma_delta)
            if updated_user:
                logger.info(f"Updated karma for user {user_id}: {karma_delta}")
            return updated_user
        
        except NotFoundError:
            logger.warning(f"User not found for karma update: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating karma for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update karma"
            )
    
    async def soft_delete_user(self, user_id: UUID) -> bool:
        """Soft delete a user"""
        try:
            result = await self.user_repository.soft_delete(user_id)
            if result:
                logger.info(f"Soft deleted user: {user_id}")
            return result
        
        except Exception as e:
            logger.error(f"Error soft deleting user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
    
    async def restore_user(self, user_id: UUID) -> bool:
        """Restore a soft deleted user"""
        try:
            result = await self.user_repository.restore_user(user_id)
            if result:
                logger.info(f"Restored user: {user_id}")
            return result
        
        except Exception as e:
            logger.error(f"Error restoring user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore user"
            )
    
    async def search_users(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserResponse]:
        """Search users"""
        try:
            users = await self.user_repository.search_users(query, skip, limit)
            return [UserResponse.from_orm(user) for user in users]
        
        except Exception as e:
            logger.error(f"Error searching users with query '{query}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search users"
            )
    
    async def get_verified_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[UserResponse]:
        """Get verified users"""
        try:
            users = await self.user_repository.get_verified_users(skip, limit, order_by)
            return [UserResponse.from_orm(user) for user in users]
        
        except Exception as e:
            logger.error(f"Error getting verified users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get verified users"
            )
    
    async def get_users_by_type(
        self, 
        user_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserResponse]:
        """Get users by type"""
        try:
            users = await self.user_repository.get_users_by_type(user_type, skip, limit)
            return [UserResponse.from_orm(user) for user in users]
        
        except Exception as e:
            logger.error(f"Error getting users by type '{user_type}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get users by type"
            )
    
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:

        """Get user statistics"""
        try:
            return await self.user_repository.get_user_stats(user_id)
        
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user stats"
            )
        
    async def get_user_count_in_db(self) -> int:
        """Get total user count in the database"""
        try:
            return await self.user_repository.get_user_count_in_db()
        
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user count"
            )