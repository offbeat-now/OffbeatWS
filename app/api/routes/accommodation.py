from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional, List
from uuid import UUID

from app.services.accommodation import AccommodationService
from app.schemas.accommodation import (
    AccommodationCreate,
    AccommodationUpdate,
    AccommodationFilters,
    AmenityList,
    AccommodationResponse,
    AccommodationListResponse
)
from app.api.dependencies import (
    get_accommodation_service,
    get_current_org
)
from app.models.auth import Organization
from app.utils.logger import get_logger

logger = get_logger("accommodation_router")

router = APIRouter()

@router.get("/", response_model=AccommodationListResponse)
async def get_accommodations(
    location: Optional[str] = None,
    min_rate: Optional[float] = None,
    max_rate: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    min_capacity: Optional[int] = None,
    female_only: Optional[bool] = None,
    min_rating: Optional[float] = None,
    amenities: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    service: AccommodationService = Depends(get_accommodation_service)
):
    try:
        amenities_list = amenities.split(",") if amenities else None
        
        filters = AccommodationFilters(
            location=location,
            min_rate=min_rate,
            max_rate=max_rate,
            min_bedrooms=min_bedrooms,
            min_capacity=min_capacity,
            female_only=female_only,
            min_rating=min_rating,
            amenities=amenities_list,
            skip=skip,
            limit=limit
        )

        return await service.get_filtered_acc_ommodations(filters)
    except Exception as e:
        logger.error(f"Error in get_accommodations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED)
async def create_accommodation(
    accommodation_data: AccommodationCreate,
    organization: Organization = Depends(get_current_org),
    service: AccommodationService = Depends(get_accommodation_service)
):
    response = await service.create_accommodation(accommodation_data, organization)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "already exists" in response.message 
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.get("/me", response_model=List[AccommodationResponse])
async def get_my_accommodations(
    organization: Organization = Depends(get_current_org),
    service: AccommodationService = Depends(get_accommodation_service)
):
    accommodations = await service.get_organization_accommodations(organization.id)
    if any(acc.error for acc in accommodations):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get accommodations"
        )
    return accommodations

@router.get("/{id}", response_model=AccommodationResponse)
async def get_accommodation(
    id: UUID,
    service: AccommodationService = Depends(get_accommodation_service)
):
    response = await service.get_accommodation(id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in response.message.lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.put("/{id}", response_model=AccommodationResponse)
async def update_accommodation(
    id: UUID,
    accommodation_data: AccommodationUpdate,
    organization: Organization = Depends(get_current_org),
    service: AccommodationService = Depends(get_accommodation_service)
):
    response = await service.update_accommodation(id, accommodation_data, organization.id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permission" in response.message.lower()
            else status.HTTP_404_NOT_FOUND if "not found" in response.message.lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message
        )
    return response

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accommodation(
    id: UUID,
    organization: Organization = Depends(get_current_org),
    service: AccommodationService = Depends(get_accommodation_service)
):
    success = await service.delete_accommodation(id, organization.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accommodation not found or permission denied"
        )

@router.post("/{id}/picture", response_model=AccommodationResponse)
async def upload_accommodation_picture(
    id: UUID,
    file: UploadFile = File(...),
    organization: Organization = Depends(get_current_org),
    service: AccommodationService = Depends(get_accommodation_service)
):
    try:
        upload_result = await service.storage_provider.upload_file(file, file.filename, file.content_type)
        print(f"File uploaded successfully: {upload_result.url}")
        response = await service.update_accommodation_picture(id, organization.id, upload_result.url)
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{id}/amenities", response_model=AccommodationResponse)
async def add_amenity(
    id: UUID,
    amenities: AmenityList,
    organization: Organization = Depends(get_current_org),
    service: AccommodationService = Depends(get_accommodation_service)
):
    response = await service.add_amenities(id, organization.id, amenities)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permission" in response.message.lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response