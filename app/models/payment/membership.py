from datetime import datetime, date
from sqlalchemy import Column, String, Enum, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class Membership(BaseModel):
    __tablename__ = "memberships"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Membership details
    tier = Column(
        Enum('Basic', 'Pro', 'Seasoned', name='membership_tier_enum'),
        nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Status and settings
    status = Column(
        Enum('active', 'expired', 'cancelled', name='membership_status_enum'),
        default='active',
        nullable=False
    )
    auto_renew = Column(Boolean, default=False)
    notes = Column(String)  # For admin notes or upgrade history
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="memberships")
    # payments = relationship("Payment", back_populates="membership")
    
    def __repr__(self):
        return f"<Membership {self.tier} for user {self.user_id}>"
    
    @property
    def is_active(self):
        """Check if membership is currently active"""
        today = date.today()
        return self.status == 'active' and self.start_date <= today <= self.end_date