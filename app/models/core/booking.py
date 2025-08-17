from datetime import datetime, date
from sqlalchemy import Column, String, Enum, DateTime, Date, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class Booking(BaseModel):
    __tablename__ = "bookings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    accommodation_id = Column(UUID(as_uuid=True), ForeignKey('accommodations.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Optional (for solo bookings)
    group_id = Column(UUID(as_uuid=True)) #, ForeignKey('groups.id'))  # Optional (for group bookings)
    
    # Booking details
    booking_type = Column(Enum('solo', 'group', name='booking_type_enum'), nullable=False)
    from_date = Column(DateTime, nullable=False)
    to_date = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)  # Total price for the booking
    
    # Payment information
    payment_status = Column(
        Enum('pending', 'completed', 'failed', name='payment_status_enum'),
        default='pending',
        nullable=False
    )
    payment_id = Column(UUID(as_uuid=True))  # Reference to payment processor
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # accommodation = relationship("Accommodation", back_populates="bookings")
    # user = relationship("User", back_populates="bookings")
    # group = relationship("Group", back_populates="bookings")
    
    def __repr__(self):
        return f"<Booking {self.id} for {self.accommodation_id}>"
    
    @property
    def duration(self):
        """Calculate duration of booking in days"""
        return (self.to_date - self.from_date).days if self.from_date and self.to_date else 0