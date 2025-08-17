from datetime import datetime
from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class Comment(BaseModel):
    __tablename__ = "comments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Polymorphic target reference
    target_type = Column(
        Enum('post', 'blog', 'job', 'accommodation', name='comment_target_type_enum'), # currently just post and comment
        nullable=False
    )
    target_id = Column(UUID(as_uuid=True), nullable=False)  # FK to any target table
    
    # Threading (for nested comments)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id'))  # Null for top-level
    
    # Author information
    author_type = Column(
        Enum('user', 'organization', name='comment_author_type_enum'),
        nullable=False
    )
    author_id = Column(UUID(as_uuid=True), nullable=False)  # FK to users or organizations
    
    # Content
    body = Column(String, nullable=False)  # Comment text
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # parent = relationship("Comment", remote_side=[id], back_populates="replies")
    # replies = relationship("Comment", back_populates="parent")
    # likes = relationship("CommentLike", back_populates="comment")
    
    def __repr__(self):
        return f"<Comment on {self.target_type} {self.target_id} by {self.author_type} {self.author_id}>"
    
    @property
    def is_reply(self):
        """Check if this is a reply to another comment"""
        return self.parent_comment_id is not None
    
    @property
    def target_relation(self):
        """Dynamic relationship property to get the target object"""
        # This would be implemented in your application logic
        return f"{self.target_type} object with ID {self.target_id}"