from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import time
from collections import defaultdict

# Import core components
from app.core.config import get_settings
from app.core.container import get_container
from app.core.exceptions import UnauthorizedError, RateLimitError
from app.db.session import get_async_session
from app.utils.jwt import JWTManager
from app.utils.logger import get_logger
from app.utils.file_utils import FileUtils

# Import providers
from app.ports.providers.storage_provider import StorageProvider

#models
from app.models.auth import User, Organization

#services
from app.services.user import UserService
from app.services.organization import OrganizationService
from app.services.accommodation import AccommodationService
from app.services.job import JobService
from app.services.application import ApplicationService
from app.services.social import SocialService
from app.services.enum import EnumService

logger = get_logger("dependencies")

# Security
security = HTTPBearer()

# Rate limiting storage (in production, use Redis)
request_counts = defaultdict(list)

# Dependency injection functions
def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance"""
    return JWTManager()

def get_file_utils() -> FileUtils:
    """Get file utils instance"""
    return FileUtils()

# provider

async def get_storage_provider() -> StorageProvider:
    """Get storage provider instance"""
    container = await get_container()
    return container.get_storage_provider()

async def get_user_service(
    session: AsyncSession = Depends(get_async_session),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    file_utils: FileUtils = Depends(get_file_utils),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> UserService:
    """Get user service instance"""
    container = await get_container()
    user_repository = container.get_user_repository(session)
    return UserService(user_repository, jwt_manager, file_utils, storage_provider)

async def get_organization_service(
    session: AsyncSession = Depends(get_async_session),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    file_utils: FileUtils = Depends(get_file_utils),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> OrganizationService:
    """Get organization service instance"""
    container = await get_container()
    org_repository = container.get_organization_repository(session)
    return OrganizationService(org_repository, jwt_manager, file_utils, storage_provider)

async def get_accommodation_service(
    session: AsyncSession = Depends(get_async_session),
    file_utils: FileUtils = Depends(get_file_utils),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> AccommodationService:
    """Get accommodation service instance"""
    container = await get_container()
    accommodation_repository = container.get_accommodation_repository(session)
    return AccommodationService(accommodation_repository, storage_provider, file_utils)

async def get_job_service(
    session: AsyncSession = Depends(get_async_session),
    file_utils: FileUtils = Depends(get_file_utils),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> JobService:
    """Get job service instance"""
    container = await get_container()
    job_repository = container.get_job_repository(session)
    return JobService(job_repository, storage_provider, file_utils)

async def get_application_service(
    session: AsyncSession = Depends(get_async_session),
    file_utils: FileUtils = Depends(get_file_utils),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> ApplicationService:
    """Get application service instance"""
    container = await get_container()
    application_repository = container.get_application_repository(session)
    return ApplicationService(application_repository, file_utils, storage_provider)

async def get_social_service(
    session: AsyncSession = Depends(get_async_session),
    file_utils: FileUtils = Depends(get_file_utils),
    storage_provider: StorageProvider = Depends(get_storage_provider)
) -> SocialService:
    """Get social service instance"""
    container = await get_container()
    #social repository has 3 components: forum, post, comment
    forum_repository = container.get_forum_repository(session)
    post_repository = container.get_post_repository(session)
    comment_repository = container.get_comment_repository(session)
    return SocialService(forum_repository, post_repository, comment_repository, file_utils, storage_provider)

async def get_enum_service(
    session: AsyncSession = Depends(get_async_session)
) -> EnumService:
    """Get enum service instance"""
    container = await get_container()
    enum_repository = container.get_enum_repository(session)
    return EnumService(enum_repository)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
) -> User:
    """Get current authenticated user"""
    try:
        # Extract token
        token = credentials.credentials
        
        # Verify token
        payload = jwt_manager.verify_token(token, "access")
        if not payload:
            raise UnauthorizedError("Invalid or expired token")
        
        # Get user ID from payload
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Token missing user information")
        
        # Get user from database
        user_response = await user_service.get_user_by_id(user_id)
        if user_response.error or not user_response.id:
            raise UnauthorizedError("User not found")
        
        # Convert UserResponse back to User model for consistency
        # In a real app, you might want to adjust this based on your needs
        user = User(
            id=user_response.id,
            user_id=user_response.user_id,
            email=user_response.email,
            dob=user_response.dob,
            gender=user_response.gender,
            verified=user_response.verified,
            name=user_response.name,
            user_type=user_response.user_type,
            karma=user_response.karma,
            bio=user_response.bio,
            image=user_response.image,
            created_at=user_response.created_at
        )
        
        return user
    
    except UnauthorizedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_org(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    org_service: OrganizationService = Depends(get_organization_service),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
) -> Organization:
    """Get current authenticated organization"""
    try:
        # Extract token
        token = credentials.credentials

        # Verify token
        payload = jwt_manager.verify_token(token, "access")
        if not payload:
            raise UnauthorizedError("Invalid or expired token")

        # Get organization ID from payload
        org_id = payload.get("sub")
        if not org_id:
            raise UnauthorizedError("Token missing organization information")

        # Get organization from database
        org_response = await org_service.get_org_by_id(org_id)
        if org_response.error or not org_response.id:
            raise UnauthorizedError("Organization not found")

        # Convert OrganizationResponse back to Organization model for consistency
        org = Organization(
            id=org_response.id,
            name=org_response.name,
            created_at=org_response.created_at
        )

        return org

    except UnauthorizedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error getting current organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# versions of get_current_user and get_current_org that allow soft dependencies
async def get_current_user_soft(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_service: UserService = Depends(get_user_service),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token, "access")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user_response = await user_service.get_user_by_id(user_id)
        if user_response.error or not user_response.id:
            return None

        return User(
            id=user_response.id,
            user_id=user_response.user_id,
            email=user_response.email,
            dob=user_response.dob,
            gender=user_response.gender,
            verified=user_response.verified,
            name=user_response.name,
            user_type=user_response.user_type,
            karma=user_response.karma,
            bio=user_response.bio,
            image=user_response.image,
            created_at=user_response.created_at
        )

    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None

async def get_current_org_soft(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    org_service: OrganizationService = Depends(get_organization_service),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
) -> Optional[Organization]:
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token, "access")
        if not payload:
            return None

        org_id = payload.get("sub")
        if not org_id:
            return None

        org_response = await org_service.get_org_by_id(org_id)
        if org_response.error or not org_response.id:
            return None

        return Organization(
            id=org_response.id,
            name=org_response.name,
            created_at=org_response.created_at
        )

    except Exception as e:
        logger.error(f"Error getting current organization: {e}")
        return None

# Rate limiting
async def rate_limit_dependency(
    request: Request,
    settings = Depends(get_settings)
):
    """Rate limiting dependency"""
    if not getattr(settings, 'rate_limit_enabled', False):
        return
    
    # Get client IP
    client_ip = request.client.host
    current_time = time.time()
    
    # Get rate limit settings
    rate_limit_window = getattr(settings, 'rate_limit_window', 60)
    rate_limit_requests = getattr(settings, 'rate_limit_requests', 100)
    
    # Clean old requests
    cutoff_time = current_time - rate_limit_window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if req_time > cutoff_time
    ]
    
    # Check rate limit
    if len(request_counts[client_ip]) >= rate_limit_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {rate_limit_requests} requests per {rate_limit_window} seconds."
        )
    
    # Add current request
    request_counts[client_ip].append(current_time)

# Pagination
class PaginationParams:
    """Pagination parameters"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        self.skip = max(0, skip)
        self.limit = min(max(1, limit), 1000)  # Max 1000 items per page

def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> PaginationParams:
    """Get pagination parameters"""
    return PaginationParams(skip=skip, limit=limit)

# Query filters
class QueryFilters:
    """Base query filters"""
    
    def __init__(
        self,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
        **kwargs
    ):
        self.search = search
        self.order_by = order_by
        self.filters = {k: v for k, v in kwargs.items() if v is not None}

def get_query_filters(
    search: Optional[str] = None,
    order_by: Optional[str] = None,
    **kwargs
) -> QueryFilters:
    """Get query filters"""
    return QueryFilters(search=search, order_by=order_by, **kwargs)

# File upload validation
async def validate_upload_file(
    file: UploadFile = File(...),
    file_utils: FileUtils = Depends(get_file_utils)
) -> UploadFile:
    """Validate uploaded file"""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Read file content to get size
    content = await file.read()
    file_size = len(content)
    
    # Reset file position
    await file.seek(0)
    
    # Validate file
    is_valid, errors = file_utils.validate_file(
        filename=file.filename,
        content_type=file.content_type,
        file_size=file_size
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {', '.join(errors)}"
        )
    
    return file

# Permission checks
async def check_user_permission(
    target_user_id: str,
    current_user: User = Depends(get_current_user)
) -> bool:
    """Check if current user can access target user's data"""
    # Users can always access their own data
    if str(current_user.id) == target_user_id:
        return True
    
    return False

async def require_user_permission(
    target_user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Require user permission to access data"""
    has_permission = await check_user_permission(target_user_id, current_user)
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Insufficient permissions."
        )

# Database transaction helpers
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_transaction(session: AsyncSession = Depends(get_async_session)):
    """Database transaction context manager"""
    transaction = await session.begin()
    try:
        yield session
        await transaction.commit()
    except Exception as e:
        await transaction.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        await session.close()

# Health check dependencies
async def health_check_dependency():
    """Basic health check"""
    return {"status": "healthy", "timestamp": time.time()}
