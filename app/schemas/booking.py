# app/schemas/booking.py
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from datetime import timedelta

class BookingType(str, Enum):
    SOLO = "solo"
    GROUP = "group"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class BookingBase(BaseModel):
    id: UUID
    accommodation_id: UUID
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    booking_type: BookingType
    from_date: datetime
    to_date: datetime
    price: float
    payment_status: PaymentStatus
    payment_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    accommodation_id: UUID
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    booking_type: BookingType = BookingType.SOLO
    from_date: datetime
    to_date: datetime
    
    @validator('to_date')
    def validate_dates(cls, v, values):
        if 'from_date' in values and v <= values['from_date']:
            raise ValueError("End date must be after start date")
        if (v - values['from_date']).days > 30:
            raise ValueError("Booking duration cannot exceed 30 days")
        return v

class BookingUpdate(BaseModel):
    payment_status: Optional[PaymentStatus] = None
    payment_id: Optional[UUID] = None

class PaymentInitResponse(BaseModel):
    payment_url: str
    payment_id: UUID
    amount: float

class BaseResponse(BaseModel):
    error: bool = False
    message: str = "Success"
    data: Optional[dict] = None

class BookingResponse(BaseResponse):
    data: Optional[BookingBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        if orm_model is None:
            return cls(error=True, message="Booking not found", data=None)
        
        if isinstance(orm_model, dict):
            base_data = BookingBase(**orm_model)
        else:
            base_data = BookingBase.model_validate(orm_model.__dict__)
        
        return cls(error=False, message="Success", data=base_data)

class BookingListResponse(BaseResponse):
    data: List[BookingBase] = []

    @classmethod
    def from_orm_models(cls, orm_models):
        bookings = []
        for model in orm_models:
            if isinstance(model, dict):
                bookings.append(BookingBase(**model))
            else:
                bookings.append(BookingBase.model_validate(model.__dict__))
        
        return cls(error=False, message="Success", data=bookings)