from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from app.models.base import BaseModel

class Forum(BaseModel):
    __tablename__ = "forums"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Creator information
    creator_type = Column(
        Enum('user', 'organization', name='forum_creator_type_enum'),
        nullable=False
    )
    creator_id = Column(UUID(as_uuid=True), nullable=False)  # FK to either users or organizations
    
    # Forum content
    name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)  # Display title of the forum
    description = Column(String)
    tags = Column(ARRAY(String))  # List of tags/categories
    
    # Visibility settings
    visibility = Column(
        Enum('public', 'private', name='forum_visibility_enum'),
        default='public',
        nullable=False
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships would be defined here
    # posts = relationship("ForumPost", back_populates="forum")
    # members = relationship("ForumMember", back_populates="forum")
    
    def __repr__(self):
        return f"<Forum {self.title} by {self.creator_type} {self.creator_id}>"
    
    @property
    def creator_relation(self):
        """Dynamic relationship property to get the creator object"""
        # This would be implemented based on your application's needs
        # Requires proper relationship setup in your application
        if self.creator_type == 'user':
            return f"User object with ID {self.creator_id}"
        return f"Organization object with ID {self.creator_id}"