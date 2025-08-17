from datetime import datetime
from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from app.models.base import BaseModel

class Post(BaseModel):
    __tablename__ = "posts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Forum reference
    forum_id = Column(UUID(as_uuid=True), ForeignKey('forums.id'), nullable=False)
    
    # Author information
    author_type = Column(
        Enum('user', 'organization', name='post_author_type_enum'),
        nullable=False
    )
    author_id = Column(UUID(as_uuid=True), nullable=False)  # FK to either users or organizations
    
    # Post content
    title = Column(String, nullable=False)
    body = Column(String)  # Main content (markdown supported)
    media_urls = Column(ARRAY(String))  # List of media URLs (images/videos)
    tags = Column(ARRAY(String))  # List of tags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # forum = relationship("Forum", back_populates="posts")
    # comments = relationship("Comment", back_populates="post")
    # likes = relationship("PostLike", back_populates="post")
    
    def __repr__(self):
        return f"<Post {self.title} in forum {self.forum_id}>"
    
    @property
    def has_media(self):
        """Check if post contains media"""
        return bool(self.media_urls)
    
    @property
    def is_popular(self):
        """Simple popularity check"""
        return self.like_count >= 10  # Threshold can be adjusted