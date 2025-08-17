# app/ports/repositories/application_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import date

from app.models.core import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate

class ApplicationRepository(ABC):
    """Abstract application repository interface"""
    
    @abstractmethod
    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        """Get application by ID"""
        pass
    
    @abstractmethod
    async def get_by_job(self, job_id: UUID, skip: int = 0, limit: int = 100) -> List[Application]:
        """Get applications for a specific job"""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Application]:
        """Get applications by a specific user"""
        pass
    
    @abstractmethod
    async def change_status(
        self,
        application_id: UUID,
        new_status: str
    ) -> Optional[Application]:
        """Change application status"""
        pass
    
    @abstractmethod
    async def exists(self, job_id: UUID, user_id: UUID) -> bool:
        """Check if user has already applied to this job"""
        pass
    
    @abstractmethod
    async def belongs_to_org(self, application_id: UUID, org_id: UUID) -> bool:
        """Check if application belongs to organization through job"""
        pass