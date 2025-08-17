# app/adapters/db/sqlalchemy_application_repository.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.core import Application, Job
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.ports.repositories.application_repository import ApplicationRepository
from app.core.exceptions import DatabaseError, ConflictError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SQLAlchemyApplicationRepository(ApplicationRepository):
    """SQLAlchemy implementation of ApplicationRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, application_data: ApplicationCreate) -> Optional[Application]:
        try:
            application = Application(**application_data.dict())
            self.session.add(application)
            await self.session.commit()
            await self.session.refresh(application)
            return application
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating application: {e}")
            raise ConflictError("Application already exists or references invalid entities")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating application: {e}")
            raise DatabaseError("Failed to create application")
    
    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        try:
            stmt = select(Application).where(Application.id == application_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting application {application_id}: {e}")
            raise DatabaseError("Failed to get application")
    
    async def get_by_job(self, job_id: UUID, skip: int = 0, limit: int = 100) -> List[Application]:
        try:
            stmt = (
                select(Application)
                .where(Application.job_id == job_id)
                .offset(skip)
                .limit(limit)
                .order_by(Application.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting applications for job {job_id}: {e}")
            raise DatabaseError("Failed to get applications")
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Application]:
        try:
            stmt = (
                select(Application)
                .where(Application.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(Application.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting applications for user {user_id}: {e}")
            raise DatabaseError("Failed to get applications")
    
    async def update(self, application_id: UUID, update_data: ApplicationUpdate) -> Optional[Application]:
        try:
            stmt = (
                update(Application)
                .where(Application.id == application_id)
                .values(**update_data.dict(exclude_unset=True))
                .returning(Application)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating application {application_id}: {e}")
            raise DatabaseError("Failed to update application")
    
    async def delete(self, application_id: UUID) -> bool:
        try:
            stmt = delete(Application).where(Application.id == application_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting application {application_id}: {e}")
            raise DatabaseError("Failed to delete application")
    
    async def change_status(self, application_id: UUID, new_status: str) -> Optional[Application]:
        try:
            stmt = (
                update(Application)
                .where(Application.id == application_id)
                .values(status=new_status)
                .returning(Application)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error changing status for application {application_id}: {e}")
            raise DatabaseError("Failed to change application status")
    
    async def exists(self, job_id: UUID, user_id: UUID) -> bool:
        try:
            stmt = select(Application).where(
                and_(
                    Application.job_id == job_id,
                    Application.user_id == user_id
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking if application exists: {e}")
            raise DatabaseError("Failed to check application existence")
    
    async def belongs_to_org(self, application_id: UUID, org_id: UUID) -> bool:
        try:
            stmt = select(Application).join(Job).where(
                and_(
                    Application.id == application_id,
                    Job.org_id == org_id
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking application ownership: {e}")
            raise DatabaseError("Failed to verify application ownership")