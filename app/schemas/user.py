from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class UserBase(BaseModel):
    user_id: str
    email: EmailStr
    name: Optional[str] = None
    image: Optional[str] = None
    dob: date
    gender: str  # Enum in DB, str in schema
    user_type: Optional[str] = "Regular"  # Enum in DB, str in schema
    karma: Optional[int] = 0
    bio: Optional[str] = None

class UserResponse(BaseModel):
    #all details of the user with error and message
    error: bool = False
    message: Optional[str] = None
    id: UUID
    name: str
    user_id: str
    email: EmailStr
    dob: date
    gender: str
    user_type: Optional[str] = "Regular"
    image: Optional[str] = None
    karma: Optional[int] = 0
    bio: Optional[str] = None
    verified: str
    created_at: Optional[datetime] = None
    error: bool = False
    message: Optional[str] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class UserUpdateResponse(UserBase):
    error: bool = False
    message: Optional[str] = None
    id: UUID
    verified: str
    deleted: Optional[str] = None
    oauth_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    error: bool = False
    message: Optional[str] = None

    
    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class UserCreate(UserBase):
    password: str
    
    class Config:
        from_attributes = True
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str
    
    class Config:
        from_attributes = True
        from_attributes = True

class UserLoginResponse(BaseModel):
    error: bool = False
    message: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    expires_in: Optional[int] = None  # seconds
    
    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class UserCreateResponse(BaseModel):
    error: bool = False
    message: str = None
    created: bool = None

    class Config:
        from_attributes = True
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    
    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
    class Config:
        from_attributes = True
        from_attributes = True

class UserCountResponse(BaseModel):
    error: bool = False
    message: Optional[str] = None
    count: Optional[int] = None

    class Config:
        from_attributes = True
        from_attributes = True
        exclude_none = True