# app/services/job.py
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.ports.repositories.job_repository import JobRepository
from app.ports.providers.storage_provider import StorageProvider

from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobFilters,
    SkillList,
    JobListResponse,
    JobBase,
)
from app.models.auth import Organization
from app.utils.logger import get_logger
from app.utils.file_utils import FileUtils

logger = get_logger("job_service")

class JobService:
    def __init__(self, job_repository: JobRepository, storage_provider: StorageProvider, file_utils: FileUtils):
        self.repository = job_repository
        self.storage_provider = storage_provider
        self.file_utils = file_utils

    async def create_job(
        self,
        job_data: JobCreate,
        organization: Organization
    ) -> JobResponse:
        try:
            create_data = job_data.dict()
            create_data.update({
                "org_id": organization.id,
                "org_name": organization.name
            })
            
            job = await self.repository.create(create_data)
            if not job:
                return JobResponse(
                    error=True,
                    message="Failed to create job",
                    data=None
                )
                
            return JobResponse.from_orm_model(job)
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}", exc_info=True)
            return JobResponse(
                error=True,
                message="Failed to create job",
                data=None
            )

    async def get_job(self, id: UUID) -> JobResponse:
        try:
            job = await self.repository.get_by_id(id)
            if not job:
                return JobResponse(
                    error=True,
                    message="Job not found",
                    data=None
                )
            return JobResponse.from_orm_model(job)
        except Exception as e:
            logger.error(f"Error getting job {id}: {e}")
            return JobResponse(
                error=True,
                message="Failed to get job",
                data=None
            )

    async def get_organization_jobs(
        self,
        organization_id: UUID
    ) -> JobListResponse:  # Changed return type
        try:
            jobs = await self.repository.get_by_organization(organization_id)
            
            # Convert jobs to JobBase objects
            job_list = []
            for job in jobs:
                if isinstance(job, dict):
                    job_list.append(JobBase(**job))
                else:
                    job_list.append(JobBase.model_validate(job.__dict__))
            
            return JobListResponse(
                error=False,
                message="Success",
                data=job_list
            )
        except Exception as e:
            logger.error(f"Error getting org jobs: {e}")
            return JobListResponse(
                error=True,
                message="Failed to get jobs",
                data=[]
            )

    async def get_filtered_jobs(
        self,
        filters: JobFilters
    ) -> JobListResponse:
        try:
            jobs = await self.repository.filter_jobs(filters)
            
            response_data = []
            for job in jobs:
                if isinstance(job, dict):
                    response_data.append(JobBase(**job))
                else:
                    response_data.append(JobBase.model_validate(job.__dict__))
            
            return JobListResponse(
                error=False,
                message="Jobs found",
                data=response_data
            )
        except Exception as e:
            logger.error(f"Error filtering jobs: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to filter jobs"
            )

    async def update_job(
        self,
        id: UUID,
        update_data: JobUpdate,
        organization_id: UUID
    ) -> JobResponse:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return JobResponse(
                    error=True,
                    message="Permission denied",
                    data=None
                )
                
            updated = await self.repository.update(id, update_data.dict(exclude_unset=True))
            if not updated:
                return JobResponse(
                    error=True,
                    message="Job not found",
                    data=None
                )
                
            return JobResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error updating job {id}: {e}")
            return JobResponse(
                error=True,
                message="Failed to update job",
                data=None
            )

    async def delete_job(self, id: UUID, organization_id: UUID) -> bool:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return False
            return await self.repository.delete(id)
        except Exception as e:
            logger.error(f"Error deleting job {id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete job"
            )

    async def add_skills(
        self,
        id: UUID,
        organization_id: UUID,
        skills: SkillList
    ) -> JobResponse:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return JobResponse(
                    error=True,
                    message="Permission denied",
                    data=None
                )
                
            updated = await self.repository.add_skills(id, skills.skills)
            if not updated:
                return JobResponse(
                    error=True,
                    message="Failed to add skills",
                    data=None
                )
                
            return JobResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error adding skills to {id}: {e}")
            return JobResponse(
                error=True,
                message="Failed to add skills",
                data=None
            )
        
    async def update_picture(
        self,
        id: UUID,
        organization_id: UUID,
        file_url: str
    ) -> JobResponse:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return JobResponse(
                    error=True,
                    message="Permission denied",
                    data=None
                )
                
            updated = await self.repository.update_picture(id, file_url)
            if not updated:
                return JobResponse(
                    error=True,
                    message="Failed to update job picture",
                    data=None
                )
                
            return JobResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error updating job picture for {id}: {e}")
            return JobResponse(
                error=True,
                message="Failed to update job picture",
                data=None
            )