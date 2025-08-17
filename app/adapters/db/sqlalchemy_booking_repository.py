# app/adapters/db/sqlalchemy_booking_repository.py
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, not_
from sqlalchemy.exc import IntegrityError

from app.models.core import Booking
from app.schemas.booking import BookingCreate, BookingUpdate, PaymentStatus
from app.ports.repositories.booking_repository import BookingRepository
from app.core.exceptions import DatabaseError, ConflictError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SQLAlchemyBookingRepository(BookingRepository):
    """SQLAlchemy implementation of BookingRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, booking_id: UUID) -> Optional[Booking]:
        try:
            stmt = select(Booking).where(Booking.id == booking_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting booking {booking_id}: {e}")
            raise DatabaseError("Failed to get booking")
    
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Booking]:
        try:
            stmt = (
                select(Booking)
                .where(Booking.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(Booking.from_date.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting bookings for user {user_id}: {e}")
            raise DatabaseError("Failed to get bookings")
    
    async def get_by_accommodation(self, accommodation_id: UUID, skip: int = 0, limit: int = 100) -> List[Booking]:
        try:
            stmt = (
                select(Booking)
                .where(Booking.accommodation_id == accommodation_id)
                .offset(skip)
                .limit(limit)
                .order_by(Booking.from_date.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting bookings for accommodation {accommodation_id}: {e}")
            raise DatabaseError("Failed to get bookings")
    
    async def create(self, booking_data: Dict) -> Optional[Booking]:
        try:
            booking = Booking(**booking_data)
            self.session.add(booking)
            await self.session.commit()
            await self.session.refresh(booking)
            return booking
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating booking: {e}")
            raise ConflictError("Booking references invalid entities")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating booking: {e}")
            raise DatabaseError("Failed to create booking")
    
    async def update(self, booking_id: UUID, update_data: Dict) -> Optional[Booking]:
        try:
            stmt = (
                update(Booking)
                .where(Booking.id == booking_id)
                .values(**update_data)
                .returning(Booking)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating booking {booking_id}: {e}")
            raise DatabaseError("Failed to update booking")
    
    async def update_by_payment_id(self, payment_id: UUID, update_data: Dict) -> Optional[Booking]:
        try:
            stmt = (
                update(Booking)
                .where(Booking.payment_id == payment_id)
                .values(**update_data)
                .returning(Booking)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating booking by payment ID {payment_id}: {e}")
            raise DatabaseError("Failed to update booking")
    
    async def delete(self, booking_id: UUID) -> bool:
        try:
            stmt = delete(Booking).where(Booking.id == booking_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting booking {booking_id}: {e}")
            raise DatabaseError("Failed to delete booking")
    
    async def has_conflict(self, accommodation_id: UUID, from_date: datetime, to_date: datetime) -> bool:
        try:
            # Check for overlapping bookings with a 6-hour buffer
            buffer = timedelta(hours=6)
            check_from = from_date - buffer
            check_to = to_date + buffer
            
            stmt = select(Booking).where(
                and_(
                    Booking.accommodation_id == accommodation_id,
                    Booking.payment_status.in_([PaymentStatus.COMPLETED, PaymentStatus.PENDING]),
                    not_(or_(
                        Booking.to_date <= check_from,
                        Booking.from_date >= check_to
                    ))
                )
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().first() is not None
        except Exception as e:
            logger.error(f"Error checking booking conflict: {e}")
            raise DatabaseError("Failed to check booking conflicts")