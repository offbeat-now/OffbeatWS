# app/schemas/job.py
from datetime import date, datetime
from typing import List, Optional, Generic, TypeVar
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Standardized API response model"""
    error: bool = False
    message: str = "Success"
    data: Optional[T] = None

class JobSkillLevel(str, Enum):
    INTERN = "Intern"
    SUPPORT = "Support"
    PRO = "Pro"

class JobMode(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"

class JobBase(BaseModel):
    """Base job model for responses"""
    id: UUID
    org_id: UUID
    org_name: str
    title: str
    description: str
    location: Optional[str] = None
    compensation_range: Optional[str] = None
    image: Optional[str] = None  # URL to job image or logo
    skills: Optional[List[str]] = None
    skill_level: JobSkillLevel
    application_deadline: Optional[date] = None
    mode: JobMode
    start_date: Optional[date] = None
    duration: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    """Schema for creating a new job"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    compensation_range: Optional[str] = Field(None, min_length=1, max_length=50)
    skills: Optional[List[str]] = None
    skill_level: JobSkillLevel = JobSkillLevel.SUPPORT
    application_deadline: Optional[date] = None
    mode: JobMode = JobMode.FULL_TIME
    start_date: Optional[date] = None
    duration: Optional[str] = Field(None, min_length=1, max_length=50)

    class Config:
        schema_extra = {
            "example": {
                "title": "Software Engineer",
                "description": "Looking for a skilled software engineer...",
                "location": "Remote",
                "compensation_range": "10-15 LPA",
                "skills": ["Python", "Django", "React"],
                "skill_level": "Pro",
                "application_deadline": "2023-12-31",
                "mode": "Full-time",
                "start_date": "2024-01-15",
                "duration": "1 year"
            }
        }

class JobUpdate(BaseModel):
    """Schema for updating an existing job"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    compensation_range: Optional[str] = Field(None, min_length=1, max_length=50)
    skills: Optional[List[str]] = None
    skill_level: Optional[JobSkillLevel] = None
    application_deadline: Optional[date] = None
    mode: Optional[JobMode] = None
    start_date: Optional[date] = None
    duration: Optional[str] = Field(None, min_length=1, max_length=50)

class JobFilters(BaseModel):
    """Query parameters for filtering jobs"""
    title: Optional[str] = None
    location: Optional[str] = None
    skill_level: Optional[JobSkillLevel] = None
    mode: Optional[JobMode] = None
    start_date: Optional[date] = None
    application_deadline: Optional[date] = None
    compensation_range: Optional[str] = None
    skills: Optional[List[str]] = None
    skip: int = 0
    limit: int = 100

    @classmethod
    def from_query_params(cls, **kwargs):
        """Create filters from query parameters"""
        valid_fields = cls.__fields__.keys()
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
        
        if 'skills' in filtered_kwargs and isinstance(filtered_kwargs['skills'], str):
            filtered_kwargs['skills'] = filtered_kwargs['skills'].split(',')
            
        return cls(**filtered_kwargs)

class SkillList(BaseModel):
    skills: List[str]

class JobResponse(BaseResponse):
    """Response model for job operations"""
    data: Optional[JobBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        """Create response from ORM model"""
        if isinstance(orm_model, dict):
            base_data = JobBase(**orm_model)
        else:
            base_data = JobBase.model_validate(orm_model.__dict__)
        return cls(
            error=False,
            message="Success",
            data=base_data
        )

class JobListResponse(BaseResponse):
    """Response model for job lists"""
    data: List[JobBase] = []

class JobImage(BaseModel):
    """Model for job image upload"""
    image: str  # URL to the job image or logo

    class Config:
        schema_extra = {
            "example": {
                "image": "https://example.com/path/to/job-image.jpg"
            }
        }