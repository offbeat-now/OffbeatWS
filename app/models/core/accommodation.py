from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from app.models.base import BaseModel

class Accommodation(BaseModel):
    __tablename__ = "accommodations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Organization reference
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    org_name = Column(String, nullable=False)
    
    # Property details
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String, nullable=False)  # city/area
    lat = Column(Float)  # latitude
    long = Column(Float)  # longitude
    address = Column(String, nullable=False)
    
    # Pricing and capacity
    rate = Column(Float, nullable=False)  # per night
    bedrooms = Column(Integer, nullable=False)
    capacity = Column(Integer)  # number of persons
    female_only = Column(Boolean, default=False)
    
    # Arrays for amenities and images
    amenities = Column(ARRAY(String))  # List of amenities
    images = Column(ARRAY(String))  # List of image URLs
    rating = Column(Float, default=1.0)  # Rating between 1.0-5.0
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # organization = relationship("Organization", back_populates="accommodations")
    
    def __repr__(self):
        return f"<Accommodation {self.title} in {self.location}>"