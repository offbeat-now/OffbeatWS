# app/ports/repositories/booking_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

from app.models.core import Booking
from app.schemas.booking import BookingCreate, BookingUpdate, PaymentStatus

class BookingRepository(ABC):
    """Abstract booking repository interface"""
    
    @abstractmethod
    async def get_by_id(self, booking_id: UUID) -> Optional[Booking]:
        """Get booking by ID"""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Booking]:
        """Get bookings by a specific user"""
        pass
    
    @abstractmethod
    async def get_by_accommodation(self, accommodation_id: UUID, skip: int = 0, limit: int = 100) -> List[Booking]:
        """Get bookings for a specific accommodation"""
        pass
    
    @abstractmethod
    async def create(self, booking_data: Dict) -> Optional[Booking]:
        """Create a new booking"""
        pass
    
    @abstractmethod
    async def update(self, booking_id: UUID, update_data: BookingUpdate) -> Optional[Booking]:
        """Update booking details"""
        pass
    
    @abstractmethod
    async def update_by_payment_id(self, payment_id: UUID, update_data: Dict) -> Optional[Booking]:
        """Update booking by payment ID"""
        pass
    
    @abstractmethod
    async def delete(self, booking_id: UUID) -> bool:
        """Delete a booking"""
        pass
    
    @abstractmethod
    async def has_conflict(self, accommodation_id: UUID, from_date: datetime, to_date: datetime) -> bool:
        """Check if there's a booking conflict for given dates"""
        pass