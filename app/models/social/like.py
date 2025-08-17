from datetime import datetime
from sqlalchemy import Column, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class Like(BaseModel):
    __tablename__ = "likes"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Target reference (post or comment)
    target_type = Column(
        Enum('post', 'comment', name='like_target_type_enum'),
        nullable=False
    )
    target_id = Column(UUID(as_uuid=True), nullable=False)  # FK to posts or comments
    
    # Liker information
    liked_by_type = Column(
        Enum('user', 'organization', name='liker_type_enum'),
        nullable=False
    )
    liked_by_id = Column(UUID(as_uuid=True), nullable=False)  # FK to users or organizations
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite unique constraint to prevent duplicate likes
    __table_args__ = (
        UniqueConstraint('target_type', 'target_id', 'liked_by_type', 'liked_by_id',
                       name='uq_like_unique'),
    )
    
    def __repr__(self):
        return f"<Like by {self.liked_by_type} {self.liked_by_id} on {self.target_type} {self.target_id}>"