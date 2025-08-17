from datetime import datetime
from sqlalchemy import Column, String, Enum, Integer, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    # Required fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # e.g., @sbk2k1
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String)  # Hashed password, nullable for OAuth users
    dob = Column(Date, nullable=False)
    gender = Column(Enum('Male', 'Female', 'Other', name='gender_enum'), nullable=False)
    verified = Column(Enum('True', 'False', name='verified_enum'), default='False', nullable=False)
    deleted = Column(Enum('True', 'False', name='deleted_enum'), default='False', nullable=False)

    # Optional fields
    name = Column(String)
    oauth_type = Column(Enum('Google', 'GitHub', 'Apple', name='oauth_type_enum'))
    user_type = Column(Enum('Pro', 'Regular', 'Seasoned', name='user_type_enum'), default='Regular')
    karma = Column(Integer, default=0)
    bio = Column(String)
    image = Column(String)  # URL to profile image
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships would go here if needed
    # Example:
    # posts = relationship("Post", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.user_id} ({self.email})>"