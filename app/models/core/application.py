from datetime import datetime, date
from sqlalchemy import Column, String, Enum, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from app.models.base import BaseModel

class Application(BaseModel):
    __tablename__ = "applications"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Optional (for solo applications)
    group_id = Column(UUID(as_uuid=True))#, ForeignKey('groups.id'))  # Optional (for group applications)
    
    # Application details
    application_type = Column(Enum('solo', 'group', name='application_type_enum'), nullable=False)
    body = Column(String)  # Cover letter or application message
    
    # Status tracking
    status = Column(
        Enum('applied', 'reviewed', 'accepted', 'rejected', name='application_status_enum'),
        default='applied',
        nullable=False
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # job = relationship("Job", back_populates="applications")
    # user = relationship("User", back_populates="job_applications")
    # group = relationship("Group", back_populates="job_applications")
    
    def __repr__(self):
        return f"<Application {self.id} for job {self.job_id}>"

    @property
    def is_active(self):
        """Check if application is still active/under consideration"""
        return self.status in ['applied', 'reviewed']