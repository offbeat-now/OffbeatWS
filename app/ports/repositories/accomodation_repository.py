from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.core import Accommodation
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from .base_repository import BaseRepository

class AccommodationRepository(BaseRepository[Accommodation, AccommodationCreate, AccommodationUpdate], ABC):
    """Abstract accommodation repository interface"""
    
    @abstractmethod
    async def get_by_id(self, accommodation_id: UUID) -> Optional[Accommodation]:
        """Get accommodation by ID"""
        pass
    
    @abstractmethod
    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Accommodation]:
        """Get accommodations by organization ID with optional pagination and ordering"""
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Accommodation]:
        """Get all accommodations with optional pagination and ordering"""
        pass
    
    @abstractmethod
    async def search_accommodations(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Accommodation]:
        """Search accommodations by query string"""
        pass

    #filtered search based on location/amenities/rate/bedrooms/capacity/female_only/rating
    @abstractmethod
    async def filter_accommodations(
        self,
        location: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
        min_bedrooms: Optional[int] = None,
        min_capacity: Optional[int] = None,
        female_only: Optional[bool] = None,
        min_rating: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Accommodation]:
        """Filter accommodations based on various criteria"""
        pass


    @abstractmethod
    async def belongs_to_organization(
        self,
        accommodation_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Check if accommodation belongs to organization"""
        pass

    @abstractmethod
    async def update_picture(
        self,
        accommodation_id: UUID,
        image_url: str
    ) -> Optional[Accommodation]:
        """Update accommodation picture"""
        pass