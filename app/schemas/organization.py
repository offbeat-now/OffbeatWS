from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str
    cin: str
    email: EmailStr
    phone1: str
    phone2: str
    description: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[float] = 1.0
    image: Optional[str] = None

class OrganizationResponse(BaseModel):
    # All details of the organization with error and message
    error: bool = False
    message: Optional[str] = None
    id: Optional[UUID] = None
    name: Optional[str] = None
    cin: Optional[str] = None
    email: Optional[EmailStr] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[float] = 1.0
    image: Optional[str] = None
    deleted_at: Optional[datetime] = None
    verified: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class OrganizationCreate(BaseModel):
    name: str
    cin: str
    email: EmailStr
    password: str
    phone1: str
    phone2: str
    description: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True
        from_attributes = True

class OrganizationCreateResponse(BaseModel):
    error: bool = False
    message: Optional[str] = None
    created: Optional[bool] = None

    class Config:
        from_attributes = True
        from_attributes = True

class OrganizationLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True
        from_attributes = True

class OrganizationLoginResponse(BaseModel):
    error: bool = False
    message: Optional[str] = None
    access_token: Optional[str] = None
    id: Optional[UUID] = None
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class OrganizationUpdateResponse(BaseModel):
    error: bool = False
    message: Optional[str] = None

    # all else
    id: Optional[UUID] = None
    name: Optional[str] = None
    cin: Optional[str] = None
    email: Optional[EmailStr] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[float] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class OrganizationCountResponse(BaseModel):
    error: bool = False
    message: Optional[str] = None
    count: Optional[int] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True