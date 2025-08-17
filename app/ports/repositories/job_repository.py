# app/ports/repositories/job_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime

from app.models.core import Job
from app.schemas.job import JobCreate, JobUpdate, JobFilters
from .base_repository import BaseRepository

class JobRepository(BaseRepository[Job, JobCreate, JobUpdate], ABC):
    """Abstract job repository interface"""
    
    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID"""
        pass
    
    @abstractmethod
    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Job]:
        """Get jobs by organization ID with optional pagination and ordering"""
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Job]:
        """Get all jobs with optional pagination and ordering"""
        pass
    
    @abstractmethod
    async def filter_jobs(
        self,
        filters: JobFilters,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """Filter jobs based on various criteria"""
        pass

    @abstractmethod
    async def belongs_to_organization(
        self,
        job_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Check if job belongs to organization"""
        pass

    @abstractmethod
    async def add_skills(
        self,
        job_id: UUID,
        skills: List[str]
    ) -> Optional[Job]:
        """Add skills to job"""
        pass

    @abstractmethod
    async def update_picture(
        job_id: UUID,
        picture_url: str
    ) -> Optional[Job]:
        """Update job picture"""
        pass