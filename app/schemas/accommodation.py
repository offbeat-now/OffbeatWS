from datetime import datetime
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from uuid import UUID

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Standardized API response model"""
    error: bool = False
    message: str = "Success"
    data: Optional[T] = None

class AccommodationBase(BaseModel):
    """Base accommodation model for responses"""
    id: UUID
    org_id: UUID
    org_name: str
    title: str
    description: str
    location: str
    lat: Optional[float] = None
    long: Optional[float] = None
    address: str
    rate: float
    bedrooms: int
    capacity: int
    female_only: bool = False
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None
    rating: float = Field(1.0, ge=1.0, le=5.0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AccommodationCreate(BaseModel):
    """Schema for creating a new accommodation"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    location: str = Field(..., min_length=1, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    long: Optional[float] = Field(None, ge=-180, le=180)
    address: str = Field(..., min_length=1, max_length=300)
    rate: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=0)
    capacity: int = Field(..., ge=1)
    female_only: bool = False
    amenities: Optional[List[str]] = None
    rating: float = Field(1.0, ge=1.0, le=5.0)

    class Config:
        schema_extra = {
            "example": {
                "title": "Cozy Downtown Apartment",
                "description": "Beautiful 2-bedroom apartment in the heart of the city",
                "location": "Downtown",
                "lat": 40.7128,
                "long": -74.0060,
                "address": "123 Main St, New York, NY 10001",
                "rate": 150.0,
                "bedrooms": 2,
                "capacity": 4,
                "female_only": False,
                "amenities": ["WiFi", "Kitchen", "Parking"],
                "rating": 4.5
            }
        }

class AccommodationUpdate(BaseModel):
    """Schema for updating an existing accommodation"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    long: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, min_length=1, max_length=300)
    rate: Optional[float] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    capacity: Optional[int] = Field(None, ge=1)
    female_only: Optional[bool] = None
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)

class AccommodationResponse(BaseResponse):
    """Response model for accommodation operations"""
    data: Optional[AccommodationBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        """Create response from ORM model"""
        if isinstance(orm_model, dict):
            # Handle case where raw dict is passed
            base_data = AccommodationBase(**orm_model)
        else:
            # Handle SQLAlchemy model case
            base_data = AccommodationBase.model_validate(orm_model.__dict__)
        return cls(
            error=False,
            message="Success",
            data=base_data
        )

class AccommodationFilters(BaseModel):
    """Query parameters for filtering accommodations"""
    location: Optional[str] = None
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None
    min_bedrooms: Optional[int] = None
    min_capacity: Optional[int] = None
    female_only: Optional[bool] = None
    min_rating: Optional[float] = None
    amenities: Optional[List[str]] = None
    skip: int = 0
    limit: int = 100

    @classmethod
    def from_query_params(cls, **kwargs):
        """Create filters from query parameters"""
        valid_fields = cls.__fields__.keys()
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
        
        if 'amenities' in filtered_kwargs and isinstance(filtered_kwargs['amenities'], str):
            filtered_kwargs['amenities'] = filtered_kwargs['amenities'].split(',')
            
        return cls(**filtered_kwargs)

class AmenityList(BaseModel):
    amenities: List[str]

class AccommodationListResponse(BaseResponse):
    """Response model for accommodation lists"""
    data: List[AccommodationBase] = []

class AccommodationDetailResponse(BaseResponse):
    """Response model for single accommodation"""
    data: Optional[AccommodationBase] = None

class AccommodationCreateResponse(BaseResponse):
    """Response model for accommodation creation"""
    data: Optional[AccommodationBase] = None

class AccommodationUpdateResponse(BaseResponse):
    """Response model for accommodation updates"""
    data: Optional[AccommodationBase] = None

class AddAmenityRequest(BaseModel):
    """Request model for adding amenities"""
    amenity: str = Field(..., min_length=1, max_length=50)

    class Config:
        schema_extra = {
            "example": {
                "amenity": "Swimming Pool"
            }
        }