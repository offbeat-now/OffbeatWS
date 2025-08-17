from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.models.core import Accommodation
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate, AccommodationResponse, AccommodationListResponse, AccommodationFilters
from app.ports.repositories.accomodation_repository import AccommodationRepository
from app.adapters.db.sqlalchemy_base_repository import SQLAlchemyRepository
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.logger import get_logger

logger = get_logger("sqlalchemy_accommodation_repository")


class SQLAlchemyAccommodationRepository(SQLAlchemyRepository[Accommodation, AccommodationCreate, AccommodationUpdate], AccommodationRepository):
    """SQLAlchemy implementation of the AccommodationRepository interface"""

    def __init__(self, session: AsyncSession):
        super().__init__(Accommodation, session)

    async def get_by_id(self, accommodation_id: UUID) -> Optional[Accommodation]:
        """Get accommodation by ID"""
        try:
            stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except NoResultFound:
            return None
        except Exception as e:
            logger.error(f"Error fetching accommodation by ID {accommodation_id}: {e}")
            raise DatabaseError("Error fetching accommodation") from e
        
    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Accommodation]:
        """Get accommodations by organization ID with optional pagination and ordering"""
        try:
            stmt = select(Accommodation).where(Accommodation.org_id == organization_id)
            if order_by:
                stmt = stmt.order_by(text(order_by))
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching accommodations for organization {organization_id}: {e}")
            raise DatabaseError("Error fetching accommodations") from e
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Accommodation]:
        """Get all accommodations with optional pagination and ordering"""
        try:
            stmt = select(Accommodation)
            if order_by:
                stmt = stmt.order_by(text(order_by))
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching all accommodations: {e}")
            raise DatabaseError("Error fetching accommodations") from e
        
    async def belongs_to_organization(
        self,
        accommodation_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Check if accommodation belongs to organization"""
        try:
            stmt = select(Accommodation).where(
                and_(
                    Accommodation.id == accommodation_id,
                    Accommodation.org_id == organization_id
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking accommodation ownership: {e}")
            raise DatabaseError("Error checking ownership") from e

    async def search_accommodation_by_title(
        self,
        title: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Accommodation]:
        """Search accommodations by title"""
        try:
            stmt = select(Accommodation).where(
                or_(
                    Accommodation.title.ilike(f"%{title}%"),
                    Accommodation.description.ilike(f"%{title}%")
                )
            )
            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching accommodations with title '{title}': {e}")
            raise DatabaseError("Error searching accommodations") from e
        
    #filtered search based on location/amenities/rate/bedrooms/capacity/female_only/rating
    async def filter_accommodations(
        self,
        filters: AccommodationFilters,
        skip: int = 0,
        limit: int = 100
    ) -> List[Accommodation]:
        query = select(Accommodation)
        if filters.location:
            query = query.where(Accommodation.location == filters.location)
        if filters.min_rate is not None:
            query = query.where(Accommodation.rate >= filters.min_rate)
        if filters.max_rate is not None:
            query = query.where(Accommodation.rate <= filters.max_rate)
        if filters.min_bedrooms is not None:
            query = query.where(Accommodation.bedrooms >= filters.min_bedrooms)
        if filters.min_capacity is not None:
            query = query.where(Accommodation.capacity >= filters.min_capacity)
        if filters.female_only is not None:
            query = query.where(Accommodation.female_only == filters.female_only)
        if filters.min_rating is not None:
            query = query.where(Accommodation.rating >= filters.min_rating)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    

    async def belongs_to_organization(self, accommodation_id: UUID, organization_id: UUID) -> bool:
        """Check if accommodation belongs to organization"""
        try:
            stmt = select(Accommodation).where(
                and_(
                    Accommodation.id == accommodation_id,
                    Accommodation.org_id == organization_id
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking accommodation ownership: {e}")
            raise DatabaseError("Error checking ownership") from e

    async def add_amenities(self, accommodation_id: UUID, amenities: List[str]) -> Optional[Accommodation]:
        """Add amenities to accommodation"""
        try:
            stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
            result = await self.session.execute(stmt)
            accommodation = result.scalar_one_or_none()
            
            if not accommodation:
                return None
                
            # Merge new amenities with existing ones, avoiding duplicates
            existing_amenities = set(accommodation.amenities or [])
            new_amenities = existing_amenities.union(set(amenities))
            
            update_stmt = (
                update(Accommodation)
                .where(Accommodation.id == accommodation_id)
                .values(amenities=list(new_amenities))
            )

            await self.session.execute(update_stmt)
            await self.session.commit()
            
            # Refresh and return updated accommodation
            await self.session.refresh(accommodation)
            return accommodation
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding amenities: {e}")
            raise DatabaseError("Error adding amenities") from e

    async def search_accommodations(self, filters: AccommodationFilters) -> List[Accommodation]:
        """Search accommodations with advanced filters"""
        try:
            stmt = select(Accommodation)
            
            # Apply filters
            if filters.location:
                stmt = stmt.where(Accommodation.location.ilike(f"%{filters.location}%"))
            if filters.min_rate is not None:
                stmt = stmt.where(Accommodation.rate >= filters.min_rate)
            if filters.max_rate is not None:
                stmt = stmt.where(Accommodation.rate <= filters.max_rate)
            if filters.min_bedrooms is not None:
                stmt = stmt.where(Accommodation.bedrooms >= filters.min_bedrooms)
            if filters.min_capacity is not None:
                stmt = stmt.where(Accommodation.capacity >= filters.min_capacity)
            if filters.female_only is not None:
                stmt = stmt.where(Accommodation.female_only == filters.female_only)
            if filters.min_rating is not None:
                stmt = stmt.where(Accommodation.rating >= filters.min_rating)
            if filters.amenities:
                # Filter by amenities (all must be present)
                for amenity in filters.amenities:
                    stmt = stmt.where(Accommodation.amenities.any(amenity))
            
            # Apply pagination
            stmt = stmt.offset(filters.skip).limit(filters.limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching accommodations: {e}")
            raise DatabaseError("Error searching accommodations") from e
        

    async def update_picture(
        self,
        accommodation_id: UUID,
        image_url: str
    ) -> Optional[Accommodation]:
        """Update accommodation picture to already existing accommodation.images"""
        try:
            stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
            result = await self.session.execute(stmt)
            accommodation = result.scalar_one_or_none()
            
            if not accommodation:
                return None
            
            # Append new image URL to existing images
            if accommodation.images is None:
                accommodation.images = []
            accommodation.images.append(image_url)
            
            update_stmt = (
                update(Accommodation)
                .where(Accommodation.id == accommodation_id)
                .values(images=accommodation.images)
            )

            await self.session.execute(update_stmt)
            await self.session.commit()
            
            # Refresh and return updated accommodation
            await self.session.refresh(accommodation)
            return accommodation
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating picture: {e}")
            raise DatabaseError("Error updating picture") from e