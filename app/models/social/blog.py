from datetime import datetime
from sqlalchemy import Column, String, Enum, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from app.models.base import BaseModel

class Blog(BaseModel):
    __tablename__ = "blogs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Creator information
    creator_type = Column(
        Enum('user', 'organization', name='blog_creator_type_enum'),
        nullable=False
    )
    creator_id = Column(UUID(as_uuid=True), nullable=False)  # FK to users or organizations
    
    # Content
    title = Column(String(200), nullable=False)
    slug = Column(String(210), unique=True, nullable=False)  # URL-friendly version of title
    excerpt = Column(String(300))  # Short summary for previews
    content = Column(Text, nullable=False)  # Markdown content stored as text
    
    # Media references
    featured_image = Column(String)  # URL to featured image (stored in S3/Cloudinary)
    media_urls = Column(ARRAY(String))  # List of other media URLs
    
    # Metadata
    tags = Column(ARRAY(String))
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    # SEO fields
    meta_title = Column(String(200))
    meta_description = Column(String(300))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # creator = relationship("User/Organization", back_populates="blogs")
    # comments = relationship("BlogComment", back_populates="blog")
    
    def __repr__(self):
        return f"<Blog {self.title} by {self.creator_type} {self.creator_id}>"