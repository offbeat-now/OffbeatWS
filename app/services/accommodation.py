from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.ports.repositories.accomodation_repository import AccommodationRepository
from app.ports.providers.storage_provider import StorageProvider
from app.schemas.accommodation import (
    AccommodationCreate,
    AccommodationUpdate,
    AccommodationResponse,
    AccommodationFilters,
    AmenityList,
    AccommodationListResponse,
    AccommodationBase,
)
from app.models.auth import Organization
from app.utils.logger import get_logger
from app.utils.file_utils import FileUtils

logger = get_logger("accommodation_service")

class AccommodationService:
    def __init__(
        self,
        accommodation_repository: AccommodationRepository,
        storage_provider: StorageProvider,
        file_utils: FileUtils
    ):
        self.repository = accommodation_repository
        self.storage_provider = storage_provider
        self.file_utils = file_utils

    async def create_accommodation(
        self,
        accommodation_data: AccommodationCreate,
        organization: Organization
    ) -> AccommodationResponse:
        try:
            existing = await self.repository.search_accommodation_by_title(accommodation_data.title)
            if existing:
                return AccommodationResponse(
                    error=True,
                    message="Accommodation with this title already exists",
                    data=None
                )

            create_data = accommodation_data.dict()
            create_data.update({
                "org_id": organization.id,
                "org_name": organization.name
            })
            
            accommodation = await self.repository.create(create_data)
            if not accommodation:
                return AccommodationResponse(
                    error=True,
                    message="Failed to create accommodation",
                    data=None
                )
                
            return AccommodationResponse.from_orm_model(accommodation)
            
        except Exception as e:
            logger.error(f"Error creating accommodation: {str(e)}", exc_info=True)
            return AccommodationResponse(
                error=True,
                message="Failed to create accommodation",
                data=None
            )

    async def get_accommodation(self, id: UUID) -> AccommodationResponse:
        try:
            accommodation = await self.repository.get_by_id(id)
            if not accommodation:
                return AccommodationResponse(
                    error=True,
                    message="Accommodation not found",
                    data=None
                )
            return AccommodationResponse.from_orm_model(accommodation)
        except Exception as e:
            logger.error(f"Error getting accommodation {id}: {e}")
            return AccommodationResponse(
                error=True,
                message="Failed to get accommodation",
                data=None
            )

    async def get_organization_accommodations(
        self,
        organization_id: UUID
    ) -> List[AccommodationResponse]:
        try:
            accommodations = await self.repository.get_by_organization(organization_id)
            return [AccommodationResponse.from_orm_model(acc) for acc in accommodations]
        except Exception as e:
            logger.error(f"Error getting org accommodations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get accommodations"
            )

    async def get_filtered_accommodations(
        self,
        filters: AccommodationFilters
    ) -> AccommodationListResponse:
        try:
            accommodations = await self.repository.filter_accommodations(filters)
            
            # Convert each accommodation to the response format
            response_data = []
            for acc in accommodations:
                if isinstance(acc, dict):
                    # If repository returns raw dicts
                    response_data.append(AccommodationBase(**acc))
                else:
                    # If repository returns ORM models
                    response_data.append(AccommodationBase.model_validate(acc.__dict__))
            
            return AccommodationListResponse(
                error=False,
                message="Accommodations found",
                data=response_data
            )
        except Exception as e:
            logger.error(f"Error filtering accommodations: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to filter accommodations"
            )

    async def update_accommodation(
        self,
        id: UUID,
        update_data: AccommodationUpdate,
        organization_id: UUID
    ) -> AccommodationResponse:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return AccommodationResponse(
                    error=True,
                    message="Permission denied",
                    data=None
                )
                
            updated = await self.repository.update(id, update_data.dict(exclude_unset=True))
            if not updated:
                return AccommodationResponse(
                    error=True,
                    message="Accommodation not found",
                    data=None
                )
                
            return AccommodationResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error updating accommodation {id}: {e}")
            return AccommodationResponse(
                error=True,
                message="Failed to update accommodation",
                data=None
            )

    async def delete_accommodation(self, id: UUID, organization_id: UUID) -> bool:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return False
            return await self.repository.delete(id)
        except Exception as e:
            logger.error(f"Error deleting accommodation {id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete accommodation"
            )

    async def update_accommodation_picture(
        self,
        id: UUID,
        organization_id: UUID,
        image_url: str
    ) -> AccommodationResponse:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return AccommodationResponse(
                    error=True,
                    message="Permission denied",
                    data=None
                )

            print(" accommodation belongs to organization")
            
            # append to images list already present
            updated = await self.repository.update_picture(id, image_url)

            if not updated:
                return AccommodationResponse(
                    error=True,
                    message="Accommodation not found",
                    data=None
                )
                
            return AccommodationResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error updating picture for {id}: {e}")
            return AccommodationResponse(
                error=True,
                message="Failed to update picture",
                data=None
            )

    async def add_amenities(
        self,
        id: UUID,
        organization_id: UUID,
        amenities: AmenityList
    ) -> AccommodationResponse:
        try:
            if not await self.repository.belongs_to_organization(id, organization_id):
                return AccommodationResponse(
                    error=True,
                    message="Permission denied",
                    data=None
                )
                
            updated = await self.repository.add_amenities(id, amenities.amenities)
            if not updated:
                return AccommodationResponse(
                    error=True,
                    message="Failed to add amenities",
                    data=None
                )
                
            return AccommodationResponse.from_orm_model(updated)
        except Exception as e:
            logger.error(f"Error adding amenities to {id}: {e}")
            return AccommodationResponse(
                error=True,
                message="Failed to add amenities",
                data=None
            )