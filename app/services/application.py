# app/services/application.py
from typing import List, Optional
from uuid import UUID

from app.ports.repositories.application_repository import ApplicationRepository
from app.utils.file_utils import FileUtils
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationStatus
)
from app.models.auth import User
from app.utils.logger import get_logger
from app.ports.providers.storage_provider import StorageProvider

logger = get_logger(__name__)

class ApplicationService:
    def __init__(self, repository: ApplicationRepository, file_utils: FileUtils, storage_provider: StorageProvider):
        self.repository = repository
        self.file_utils = file_utils
        self.storage_provider = storage_provider

    async def create_application(self, application_data: ApplicationCreate) -> ApplicationResponse:
        """Create a new job application"""
        try:
            # Check if user has already applied to this job (for solo applications)
            if application_data.application_type == "solo" and application_data.user_id:
                already_applied = await self.repository.exists(
                    application_data.job_id,
                    application_data.user_id
                )
                if already_applied:
                    return ApplicationResponse(
                        error=True,
                        message="You have already applied to this job",
                        data=None
                    )
            
            application = await self.repository.create(application_data)
            return ApplicationResponse.from_orm_model(application)
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}")
            return ApplicationResponse(
                error=True,
                message="Failed to create application",
                data=None
            )
    
    async def get_application(self, application_id: UUID) -> ApplicationResponse:
        """Get a specific application by ID"""
        try:
            application = await self.repository.get_by_id(application_id)
            return ApplicationResponse.from_orm_model(application)
        except Exception as e:
            logger.error(f"Error getting application {application_id}: {str(e)}")
            return ApplicationResponse(
                error=True,
                message="Application not found",
                data=None
            )
    
    async def get_user_applications(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> ApplicationListResponse:
        """Get all applications for a specific user"""
        try:
            applications = await self.repository.get_by_user(user_id, skip, limit)
            return ApplicationListResponse.from_orm_models(applications)
        except Exception as e:
            logger.error(f"Error getting applications for user {user_id}: {str(e)}")
            return ApplicationListResponse(
                error=True,
                message="Failed to get applications",
                data=[]
            )
    
    async def get_job_applications(
        self,
        job_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> ApplicationListResponse:
        """Get all applications for a specific job"""
        try:
            applications = await self.repository.get_by_job(job_id, skip, limit)
            return ApplicationListResponse.from_orm_models(applications)
        except Exception as e:
            logger.error(f"Error getting applications for job {job_id}: {str(e)}")
            return ApplicationListResponse(
                error=True,
                message="Failed to get applications",
                data=[]
            )
    
    
    async def update_application_status(
        self,
        application_id: UUID,
        new_status: ApplicationStatus
    ) -> ApplicationResponse:
        """Update application status (organization only)"""
        try:
            updated = await self.repository.change_status(application_id, new_status)
            if not updated:
                return ApplicationResponse(
                    error=True,
                    message="Application not found",
                    data=None
                )
            
            # if status is acce
            return ApplicationResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error updating status for application {application_id}: {str(e)}")
            return ApplicationResponse(
                error=True,
                message="Failed to update application status",
                data=None
            )
    
    async def delete_application(
        self,
        application_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete an application"""
        try:
            # Verify the application belongs to the user
            application = await self.repository.get_by_id(application_id)
            if not application:
                return False
            
            if application.user_id != user_id:
                return False
            
            return await self.repository.delete(application_id)
        except Exception as e:
            logger.error(f"Error deleting application {application_id}: {str(e)}")
            return False