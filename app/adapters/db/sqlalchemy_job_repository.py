# app/adapters/db/sqlalchemy_job_repository.py
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.models.core import Job
from app.schemas.job import JobCreate, JobUpdate, JobFilters
from app.ports.repositories.job_repository import JobRepository
from app.adapters.db.sqlalchemy_base_repository import SQLAlchemyRepository
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SQLAlchemyJobRepository(SQLAlchemyRepository[Job, JobCreate, JobUpdate], JobRepository):
    """SQLAlchemy implementation of the JobRepository interface"""

    def __init__(self, session: AsyncSession):
        super().__init__(Job, session)

    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID"""
        try:
            stmt = select(Job).where(Job.id == job_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except NoResultFound:
            return None
        except Exception as e:
            logger.error(f"Error fetching job by ID {job_id}: {e}")
            raise DatabaseError("Error fetching job") from e
        
    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Job]:
        """Get jobs by organization ID with optional pagination and ordering"""
        try:
            stmt = select(Job).where(Job.org_id == organization_id)
            if order_by:
                stmt = stmt.order_by(text(order_by))
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching jobs for organization {organization_id}: {e}")
            raise DatabaseError("Error fetching jobs") from e
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Job]:
        """Get all jobs with optional pagination and ordering"""
        try:
            stmt = select(Job)
            if order_by:
                stmt = stmt.order_by(text(order_by))
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching all jobs: {e}")
            raise DatabaseError("Error fetching jobs") from e
        
    async def filter_jobs(
        self,
        filters: JobFilters,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """Filter jobs based on various criteria"""
        try:
            stmt = select(Job)
            
            if filters.title:
                stmt = stmt.where(Job.title.ilike(f"%{filters.title}%"))
            if filters.location:
                stmt = stmt.where(Job.location.ilike(f"%{filters.location}%"))
            if filters.skill_level:
                stmt = stmt.where(Job.skill_level == filters.skill_level)
            if filters.mode:
                stmt = stmt.where(Job.mode == filters.mode)
            if filters.start_date:
                stmt = stmt.where(Job.start_date >= filters.start_date)
            if filters.application_deadline:
                stmt = stmt.where(Job.application_deadline >= filters.application_deadline)
            if filters.compensation_range:
                stmt = stmt.where(Job.compensation_range.ilike(f"%{filters.compensation_range}%"))
            if filters.skills:
                for skill in filters.skills:
                    stmt = stmt.where(Job.skills.any(skill))
            
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error filtering jobs: {e}")
            raise DatabaseError("Error filtering jobs") from e

    async def belongs_to_organization(
        self,
        job_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Check if job belongs to organization"""
        try:
            stmt = select(Job).where(
                and_(
                    Job.id == job_id,
                    Job.org_id == organization_id
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking job ownership: {e}")
            raise DatabaseError("Error checking ownership") from e

    async def add_skills(
        self,
        job_id: UUID,
        skills: List[str]
    ) -> Optional[Job]:
        """Add skills to job"""
        try:
            stmt = select(Job).where(Job.id == job_id)
            result = await self.session.execute(stmt)
            job = result.scalar_one_or_none()
            
            if not job:
                return None
                
            # Merge new skills with existing ones, avoiding duplicates
            existing_skills = set(job.skills or [])
            new_skills = existing_skills.union(set(skills))
            
            update_stmt = (
                update(Job)
                .where(Job.id == job_id)
                .values(skills=list(new_skills))
            )

            await self.session.execute(update_stmt)
            await self.session.commit()
            
            # Refresh and return updated job
            await self.session.refresh(job)
            return job
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding skills: {e}")
            raise DatabaseError("Error adding skills") from e
        
    async def update_picture(
        self,
        job_id: UUID,
        picture_url: str
    ) -> Optional[Job]:
        """Update job picture"""
        try:
            update_stmt = (
                update(Job)
                .where(Job.id == job_id)
                .values(image=picture_url)
            )
            await self.session.execute(update_stmt)
            await self.session.commit()
            
            # Fetch and return updated job
            return await self.get_by_id(job_id)
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error updating picture: {e}")
            raise ConflictError("Job already exists") from e
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating job picture: {e}")
            raise DatabaseError("Error updating job picture") from e