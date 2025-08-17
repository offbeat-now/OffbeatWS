from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.services.organization import OrganizationService
from app.schemas.organization import (
    OrganizationResponse, 
    OrganizationUpdate, 
    OrganizationUpdateResponse,
    OrganizationCountResponse
)
from app.api.dependencies import get_organization_service, get_current_org
from app.models.auth import Organization

router = APIRouter()

@router.get("/me", response_model=OrganizationResponse)
async def get_current_org_profile(
    current_org: Organization = Depends(get_current_org),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get current organization's profile"""
    print(current_org)
    try:
        return await org_service.get_org_by_id(current_org.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me", response_model=OrganizationUpdateResponse)
async def update_current_org_profile(
    org_update: OrganizationUpdate,
    current_org: Organization = Depends(get_current_org),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Update current organization's profile"""
    try:
        return await org_service.update_org(current_org.id, org_update)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/me/picture", response_model=OrganizationUpdateResponse)
async def upload_org_picture(
    file: UploadFile = File(...),
    current_org: Organization = Depends(get_current_org),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Upload profile picture for current organization"""
    try:
        # Save file and get URL
        file_url = await org_service.storage_provider.upload_file(file, file.filename, file.content_type)
        return await org_service.upload_org_picture(current_org, file_url.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/count", response_model=OrganizationCountResponse)
async def get_org_count(
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get total organization count"""
    try:
        count = await org_service.get_organization_count()
        return OrganizationCountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_org_profile(
    org_id: UUID,
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Get any organization's public profile by ID"""
    try:
        return await org_service.get_org_by_id(org_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )