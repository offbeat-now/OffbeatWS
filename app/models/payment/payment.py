from datetime import datetime, date
from sqlalchemy import Column, String, Enum, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import BaseModel

class Payment(BaseModel):
    __tablename__ = "payments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Payment details
    purpose = Column(
        Enum('booking', 'membership', name='payment_purpose_enum'),
        nullable=False
    )
    reference_id = Column(UUID(as_uuid=True), nullable=False)  # FK to either Booking or Membership
    amount = Column(Float, nullable=False)
    currency = Column(String, default='INR')
    method = Column(
        Enum('upi', 'card', 'wallet', 'netbanking', 'paypal', 'unknown', name='payment_method_enum'),
        default='unknown'
    )
    
    # Status and gateway info
    status = Column(
        Enum('initiated', 'success', 'failed', 'refunded', name='payment_status_enum'),
        default='initiated',
        nullable=False
    )
    payment_gateway_id = Column(String)  # External transaction ID (e.g., RazorPay ID)
    receipt_url = Column(String)  # Payment receipt URL
    notes = Column(String)  # Additional notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.amount}{self.currency} for {self.purpose}>"
    
    @property
    def gateway_provider(self):
        """Determine payment gateway from gateway ID format"""
        if not self.payment_gateway_id:
            return None
        if self.payment_gateway_id.startswith('pay_'):
            return 'razorpay'
        if self.payment_gateway_id.startswith('pi_'):
            return 'stripe'
        return 'unknown'