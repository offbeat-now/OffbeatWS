from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class Organization(BaseModel):
    __tablename__ = "organizations"
    
    # Required fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    cin = Column(String, nullable=False, unique=True)  # Company Identification Number
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    phone1 = Column(String, nullable=False)
    phone2 = Column(String, nullable=False)
    deleted = Column(Enum('True', 'False', name='deleted_enum'), default='False', nullable=False)
    verified = Column(Enum('True', 'False', name='verified_enum'), default='False', nullable=False)
    
    # Optional fields
    description = Column(String)  # Description
    url = Column(String)   # Website URL
    rating = Column(Float, default=1.0)  # Rating between 1.0-5.0
    image = Column(String)  # URL to organization logo
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships would go here if needed
    # Example:
    # members = relationship("OrganizationMember", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization {self.name} ({self.cin})>"