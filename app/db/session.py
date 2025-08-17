from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("database")

class DatabaseManager:
    """Database session manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None
        
    def get_async_engine(self):
        """Get async SQLAlchemy engine"""
        if not self._async_engine:
            # Convert sync URL to async URL
            database_url = self.settings.database_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("mysql://"):
                database_url = database_url.replace("mysql://", "mysql+aiomysql://", 1)
            elif database_url.startswith("sqlite://"):
                database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            
            self._async_engine = create_async_engine(
                database_url,
                echo=self.settings.debug if isinstance(self.settings.debug, bool) else self.settings.debug == "True",
                pool_pre_ping=True,
                pool_recycle=300,
            )
            logger.info(f"Created async database engine")
        
        return self._async_engine
    
    def get_sync_engine(self):
        """Get sync SQLAlchemy engine"""
        if not self._sync_engine:
            self._sync_engine = create_engine(
                self.settings.database_url,
                echo=self.settings.debug if isinstance(self.settings.debug, bool) else self.settings.debug == "True",
                pool_pre_ping=True,
                pool_recycle=300,
            )
            logger.info(f"Created sync database engine: {self.settings.database_url}")

        return self._sync_engine
    
    def get_async_session_factory(self):
        """Get async session factory"""
        if not self._async_session_factory:
            self._async_session_factory = async_sessionmaker(
                bind=self.get_async_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return self._async_session_factory
    
    def get_sync_session_factory(self):
        """Get sync session factory"""
        if not self._sync_session_factory:
            self._sync_session_factory = sessionmaker(
                bind=self.get_sync_engine(),
                autoflush=False,
                autocommit=False,
            )
        return self._sync_session_factory

# Global database manager
db_manager = DatabaseManager()

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database session"""
    async_session_factory = db_manager.get_async_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

def get_sync_session() -> Generator[Session, None, None]:
    """Sync database session generator"""
    sync_session_factory = db_manager.get_sync_session_factory()
    session = sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()