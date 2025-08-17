from functools import lru_cache
from typing import Type, TypeVar, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client
from fastapi import Depends

# Import configurations
from app.core.config import get_settings

# Import ports
from app.ports.providers.cache_provider import CacheProvider
from app.ports.providers.storage_provider import StorageProvider
from app.ports.repositories.user_repository import UserRepository
from app.ports.repositories.org_repository import OrganizationRepository
from app.ports.repositories.accomodation_repository import AccommodationRepository
from app.ports.repositories.job_repository import JobRepository
from app.ports.repositories.application_repository import ApplicationRepository
from app.ports.repositories.social_repository import ForumRepository, PostRepository, CommentRepository
from app.ports.repositories.enum_repository import EnumRepository
# from ports.organization_repository import OrganizationRepository

# cache adapters
# from app.adapters.cache.redis_cache import RedisCache
# from app.adapters.cache.memory_cache import MemoryCache

# storage adapters
from app.adapters.storage.s3_storage import S3Storage
from app.adapters.storage.cloudinary_storage import CloudinaryStorage
from app.adapters.storage.supabase_storage import SupabaseStorage

# Import repositories
from app.adapters.db.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.adapters.db.sqlalchemy_org_repository import SQLAlchemyOrganizationRepository
from app.adapters.db.sqlalchemy_accomodation_repository import SQLAlchemyAccommodationRepository
from app.adapters.db.sqlalchemy_job_repository import SQLAlchemyJobRepository
from app.adapters.db.sqlalchemy_application_repository import SQLAlchemyApplicationRepository
from app.adapters.db.sqlalchemy_social_repository import SQLAlchemyForumRepository, SQLAlchemyPostRepository, SQLAlchemyCommentRepository
from app.adapters.db.sqlalchemy_enum_repository import SQLAlchemyEnumRepository

# session
from app.db.session import get_async_session


# Import database managers
# from app.db.session import get_async_session, get_prisma_client

# Import utils
from app.utils.logger import get_logger

logger = get_logger("container")

class Container:
    """Dependency injection container"""
    
    def __init__(self):
        self.settings = get_settings()
        self._cache_provider: CacheProvider = None
        self._storage_provider: StorageProvider = None
        self._repositories: Dict[str, Any] = {}
    
    # Cache Provider
    # @lru_cache()
    # def get_cache_provider(self) -> CacheProvider:
    #     """Get cache provider based on configuration"""
    #     if not self._cache_provider:
    #         if self.settings.cache_provider == "redis":
    #             self._cache_provider = RedisCache()
    #             logger.info("Initialized Redis cache provider")
    #         else:  # memory
    #             self._cache_provider = MemoryCache()
    #             logger.info("Initialized Memory cache provider")
        
    #     return self._cache_provider
    
    # Storage Provider
    @lru_cache()
    def get_storage_provider(self) -> StorageProvider:
        """Get storage provider based on configuration"""
        print(f"Initializing storage provider: {self.settings.storage_provider}")
        if not self._storage_provider:
            if self.settings.storage_provider == "s3":
                self._storage_provider = S3Storage()
                logger.info("Initialized S3 storage provider")
            elif self.settings.storage_provider == "cloudinary":
                self._storage_provider = CloudinaryStorage()
                logger.info("Initialized Cloudinary storage provider")
            else:  # supabase
                self._storage_provider = SupabaseStorage()
                logger.info("Initialized Supabase storage provider")
        
        return self._storage_provider
    
    # Repository Factories
    def get_user_repository(self, session: AsyncSession = None) -> UserRepository:
        """Get user repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyUserRepository(session)
        
        else:
            raise ValueError(f"Unsupported user repository provider: {self.settings.db_provider}")
    
    def get_organization_repository(self, session: AsyncSession = None) -> Type[OrganizationRepository]:
        """Get organization repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyOrganizationRepository(session)
        
        else:
            raise ValueError(f"Unsupported organization repository provider: {self.settings.db_provider}")

    def get_accommodation_repository(self, session: AsyncSession = None) -> AccommodationRepository:
        """Get accommodation repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyAccommodationRepository(session)

        else:
            raise ValueError(f"Unsupported accommodation repository provider: {self.settings.db_provider}")
        
    def get_job_repository(self, session: AsyncSession = None) -> Type[JobRepository]:
        """Get job repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyJobRepository(session)

        else:
            raise ValueError(f"Unsupported job repository provider: {self.settings.db_provider}")
        
    def get_application_repository(self, session: AsyncSession = None) -> ApplicationRepository:
        """Get application repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyApplicationRepository(session)

        else:
            raise ValueError(f"Unsupported application repository provider: {self.settings.db_provider}")
        
    def get_forum_repository(self, session: AsyncSession = None) -> ForumRepository:
        """Get forum repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyForumRepository(session)

        else:
            raise ValueError(f"Unsupported forum repository provider: {self.settings.db_provider}")
    
    def get_post_repository(self, session: AsyncSession = None) -> PostRepository:
        """Get post repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyPostRepository(session)

        else:
            raise ValueError(f"Unsupported post repository provider: {self.settings.db_provider}")
    
    def get_comment_repository(self, session: AsyncSession = None) -> CommentRepository:
        """Get comment repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            return SQLAlchemyCommentRepository(session)

        else:
            raise ValueError(f"Unsupported comment repository provider: {self.settings.db_provider}")
        
    def get_enum_repository(self, session: AsyncSession = None) -> EnumRepository:
        """Get enum repository based on database provider"""
        if self.settings.db_provider == "sqlalchemy":
            if not session:
                raise ValueError("SQLAlchemy session required")
            from app.adapters.db.sqlalchemy_enum_repository import SQLAlchemyEnumRepository
            return SQLAlchemyEnumRepository(session)

        else:
            raise ValueError(f"Unsupported enum repository provider: {self.settings.db_provider}")

    # Helper methods
    def _get_supabase_client(self) -> Client:
        """Get Supabase client"""
        from supabase import create_client
        return create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_key
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cleanup cache provider
            if self._cache_provider:
                if hasattr(self._cache_provider, 'close'):
                    await self._cache_provider.close()
                elif hasattr(self._cache_provider, 'shutdown'):
                    await self._cache_provider.shutdown()
            
            logger.info("Container cleanup completed")
        
        except Exception as e:
            logger.error(f"Error during container cleanup: {e}")

# Global container instance
container = Container()

# FastAPI Dependencies
async def get_container() -> Container:
    """FastAPI dependency to get container"""
    return container

# provider dependencies

async def get_cache_provider() -> CacheProvider:
    """FastAPI dependency to get cache provider"""
    return container.get_cache_provider()

async def get_storage_provider() -> StorageProvider:
    """FastAPI dependency to get storage provider"""
    return container.get_storage_provider()


# Repository dependencies
async def get_user_repository(session: AsyncSession = Depends(get_async_session)) -> UserRepository:
    """FastAPI dependency to get user repository"""
    return container.get_user_repository(session)