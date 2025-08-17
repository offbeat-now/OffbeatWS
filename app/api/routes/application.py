# app/api/routes/application.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.services.application import ApplicationService
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    StatusUpdate,
    ApplicationResponse,
    ApplicationListResponse
)
from app.api.dependencies import (
    get_application_service,
    get_current_user,
    get_current_org
)
from app.models.auth import User, Organization
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service)
):
    """Create a new job application"""
    try:
        # Ensure user_id is set for solo applications
        if application_data.application_type == "solo":
            application_data.user_id = user.id
        
        response = await service.create_application(application_data)
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        return response
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service)
):
    """Get a specific application"""
    response = await service.get_application(application_id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response


@router.get("/applied/me", response_model=ApplicationListResponse)
async def get_user_applications(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service)
):
    """Get all applications for the current user"""
    try:
        print(f"Fetching applications for user: {user.id}, skip: {skip}, limit: {limit}")
        response = await service.get_user_applications(user.id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting user applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        )

@router.get("/job/{job_id}", response_model=ApplicationListResponse)
async def get_job_applications(
    job_id: UUID,
    skip: int = 0,
    limit: int = 100,
    org: Organization = Depends(get_current_org),
    service: ApplicationService = Depends(get_application_service)
):
    """Get all applications for a specific job (Organization only)"""
    try:
        response = await service.get_job_applications(job_id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting job applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get applications"
        )


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: UUID,
    status_update: StatusUpdate,
    org: Organization = Depends(get_current_org),
    service: ApplicationService = Depends(get_application_service)
):
    """Update application status (Organization only)"""
    response = await service.update_application_status(application_id, status_update.status)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: UUID,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service)
):
    """Delete an application"""
    success = await service.delete_application(application_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or permission denied"
        )