from datetime import datetime, date
from sqlalchemy import Column, String, Enum, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from app.models.base import BaseModel

class Job(BaseModel):
    __tablename__ = "jobs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Organization reference
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    org_name = Column(String, nullable=False)
    
    # Job details
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String)
    compensation_range = Column(String)  # e.g., "5-10 LPA"
    image = Column(String)  # URL to job image or logo
    
    # Skills and requirements
    skills = Column(ARRAY(String))  # List of required skills
    skill_level = Column(
        Enum('Intern', 'Support', 'Pro', name='job_skill_level_enum'),
        nullable=False
    )
    
    # Duration information
    application_deadline = Column(Date)  # Deadline for applications
    mode = Column(
        Enum('Full-time', 'Part-time', 'Contract', name='job_mode_enum'),
        nullable=False
    )
    start_date = Column(Date)
    duration = Column(String)  # e.g., "6 months", "Full-time"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # organization = relationship("Organization", back_populates="jobs")
    # applications = relationship("Application", back_populates="job")
    
    def __repr__(self):
        return f"<Job {self.title} at {self.org_name}>"
    
    @property
    def is_active(self):
        """Check if job is still active based on start date"""
        if not self.start_date:
            return True
        return self.start_date >= date.today()