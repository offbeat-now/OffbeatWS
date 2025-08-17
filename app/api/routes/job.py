# app/api/routes/job.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from uuid import UUID
from datetime import date
from typing import Optional

from app.services.job import JobService
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobFilters,
    SkillList,
    JobResponse,
    JobListResponse
)
from app.api.dependencies import (
    get_job_service,
    get_current_org
)
from app.models.auth import Organization
from app.utils.logger import get_logger

logger = get_logger("job_router")

router = APIRouter()

@router.get("/", response_model=JobListResponse)
async def get_jobs(
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skill_level: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    application_deadline: Optional[date] = Query(None),
    compensation_range: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    service: JobService = Depends(get_job_service)
):
    """Get all jobs with optional filtering"""
    try:
        skills_list = skills.split(",") if skills else None
        
        filters = JobFilters(
            title=title,
            location=location,
            skill_level=skill_level,
            mode=mode,
            start_date=start_date,
            application_deadline=application_deadline,
            compensation_range=compensation_range,
            skills=skills_list,
            skip=skip,
            limit=limit
        )

        return await service.get_filtered_jobs(filters)
    except Exception as e:
        logger.error(f"Error in get_jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    organization: Organization = Depends(get_current_org),
    service: JobService = Depends(get_job_service)
):
    """Create a new job posting"""
    response = await service.create_job(job_data, organization)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "already exists" in response.message 
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.get("/me", response_model=JobListResponse)
async def get_my_jobs(
    organization: Organization = Depends(get_current_org),
    service: JobService = Depends(get_job_service)
):
    """Get all jobs for current organization"""
    response = await service.get_organization_jobs(organization.id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.post('/picture/{id}', response_model=JobResponse)
async def upload_job_picture(
    id: UUID,
    file: UploadFile = File(...),
    organization: Organization = Depends(get_current_org),
    service: JobService = Depends(get_job_service)
):
    """Upload a job picture"""
    #upload
    file_url = await service.storage_provider.upload_file(file, file.filename, file.content_type)
    #update with job url
    response = await service.update_picture(id, organization.id, file_url.url)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response

@router.get("/{id}", response_model=JobResponse)
async def get_job(
    id: UUID,
    service: JobService = Depends(get_job_service)
):
    """Get a specific job by ID"""
    response = await service.get_job(id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in response.message.lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.put("/{id}", response_model=JobResponse)
async def update_job(
    id: UUID,
    job_data: JobUpdate,
    organization: Organization = Depends(get_current_org),
    service: JobService = Depends(get_job_service)
):
    """Update an existing job"""
    response = await service.update_job(id, job_data, organization.id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permission" in response.message.lower()
            else status.HTTP_404_NOT_FOUND if "not found" in response.message.lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    id: UUID,
    organization: Organization = Depends(get_current_org),
    service: JobService = Depends(get_job_service)
):
    """Delete a job posting"""
    success = await service.delete_job(id, organization.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or permission denied"
        )

@router.post("/{id}/skills", response_model=JobResponse)
async def add_skill(
    id: UUID,
    skills: SkillList,
    organization: Organization = Depends(get_current_org),
    service: JobService = Depends(get_job_service)
):
    """Add skills to job"""
    response = await service.add_skills(id, organization.id, skills)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permission" in response.message.lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response