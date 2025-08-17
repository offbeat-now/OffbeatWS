# app/schemas/application.py
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator

class ApplicationType(str, Enum):
    SOLO = "solo"
    GROUP = "group"

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class ApplicationBase(BaseModel):
    id: UUID
    job_id: UUID
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    application_type: ApplicationType
    body: Optional[str] = None
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    job_id: UUID
    user_id: Optional[UUID] = None
    application_type: ApplicationType = ApplicationType.SOLO
    body: Optional[str] = Field(None, max_length=2000)
    status: ApplicationStatus = ApplicationStatus.APPLIED
    

class ApplicationUpdate(BaseModel):
    body: Optional[str] = Field(None, max_length=2000)
    status: Optional[ApplicationStatus] = None

class StatusUpdate(BaseModel):
    status: ApplicationStatus

class BaseResponse(BaseModel):
    error: bool = False
    message: str = "Success"
    data: Optional[dict] = None

class ApplicationResponse(BaseResponse):
    data: Optional[ApplicationBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        if orm_model is None:
            return cls(error=True, message="Application not found", data=None)
        
        if isinstance(orm_model, dict):
            base_data = ApplicationBase(**orm_model)
        else:
            base_data = ApplicationBase.model_validate(orm_model.__dict__)
        
        return cls(error=False, message="Success", data=base_data)

class ApplicationListResponse(BaseResponse):
    data: List[ApplicationBase] = []

    @classmethod
    def from_orm_models(cls, orm_models):
        applications = []
        for model in orm_models:
            if isinstance(model, dict):
                applications.append(ApplicationBase(**model))
            else:
                applications.append(ApplicationBase.model_validate(model.__dict__))
        
        return cls(error=False, message="Success", data=applications)