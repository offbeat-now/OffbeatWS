# app/services/booking.py
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.accomodation_repository import AccommodationRepository
from app.ports.providers.payment_provider import PaymentProvider
from app.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingListResponse,
    PaymentInitResponse,
    PaymentStatus
)
from app.models.auth import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BookingService:
    def __init__(
        self, 
        booking_repo: BookingRepository,
        accommodation_repo: AccommodationRepository,
        payment_provider: PaymentProvider
    ):
        self.booking_repo = booking_repo
        self.accommodation_repo = accommodation_repo
        self.payment_provider = payment_provider

    async def has_booking_conflict(
        self,
        accommodation_id: UUID,
        from_date: datetime,
        to_date: datetime
    ) -> bool:
        """Check if there are any existing bookings that conflict with the requested dates"""
        try:
            # Get all bookings for this accommodation
            existing_bookings = await self.booking_repo.get_by_accommodation(accommodation_id)
            
            # Add buffer time (6 hours before and after)
            buffer = timedelta(hours=6)
            check_from = from_date - buffer
            check_to = to_date + buffer
            
            for booking in existing_bookings:
                # Skip cancelled/failed bookings
                if booking.payment_status not in [PaymentStatus.COMPLETED, PaymentStatus.PENDING]:
                    continue
                
                # Check for overlap
                if (booking.from_date <= check_to) and (booking.to_date >= check_from):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking booking conflicts: {str(e)}")
            raise

    async def initiate_booking(self, booking_data: BookingCreate) -> PaymentInitResponse:
        """Create a booking and initiate payment"""
        try:
            # Get accommodation details to calculate price
            accommodation = await self.accommodation_repo.get_by_id(booking_data.accommodation_id)
            if not accommodation:
                raise ValueError("Accommodation not found")
            
            # Calculate duration and price
            duration = (booking_data.to_date - booking_data.from_date).days
            if duration <= 0:
                raise ValueError("Invalid booking duration")
            
            price = accommodation.rate * duration
            
            # Create payment intent with external provider
            payment_id = uuid4()
            payment_url = await self.payment_provider.create_payment_intent(
                amount=price,
                currency="USD",
                payment_id=str(payment_id),
                description=f"Booking for {accommodation.title}"
            )
            
            # Create booking record with pending status
            booking = await self.booking_repo.create({
                **booking_data.dict(),
                "price": price,
                "payment_status": PaymentStatus.PENDING,
                "payment_id": payment_id
            })
            
            return PaymentInitResponse(
                payment_url=payment_url,
                payment_id=payment_id,
                amount=price
            )
        except Exception as e:
            logger.error(f"Error initiating booking: {str(e)}")
            raise

    async def confirm_booking(self, payment_id: UUID) -> BookingResponse:
        """Confirm booking after successful payment"""
        try:
            # Verify payment with provider
            payment_status = await self.payment_provider.verify_payment(str(payment_id))
            if not payment_status:
                raise ValueError("Payment verification failed")
            
            # Update booking status
            updated_booking = await self.booking_repo.update(
                payment_id=payment_id,
                update_data={"payment_status": PaymentStatus.COMPLETED}
            )
            
            return BookingResponse.from_orm_model(updated_booking)
        except Exception as e:
            logger.error(f"Error confirming booking: {str(e)}")
            
            # Mark booking as failed if confirmation fails
            try:
                await self.booking_repo.update(
                    payment_id=payment_id,
                    update_data={"payment_status": PaymentStatus.FAILED}
                )
            except Exception as update_error:
                logger.error(f"Failed to mark booking as failed: {str(update_error)}")
            
            return BookingResponse(
                error=True,
                message="Failed to confirm booking",
                data=None
            )

    async def get_booking(self, booking_id: UUID) -> BookingResponse:
        """Get a specific booking by ID"""
        try:
            booking = await self.booking_repo.get_by_id(booking_id)
            return BookingResponse.from_orm_model(booking)
        except Exception as e:
            logger.error(f"Error getting booking {booking_id}: {str(e)}")
            return BookingResponse(
                error=True,
                message="Booking not found",
                data=None
            )

    async def get_user_bookings(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> BookingListResponse:
        """Get all bookings for a specific user"""
        try:
            bookings = await self.booking_repo.get_by_user(user_id, skip, limit)
            return BookingListResponse.from_orm_models(bookings)
        except Exception as e:
            logger.error(f"Error getting bookings for user {user_id}: {str(e)}")
            return BookingListResponse(
                error=True,
                message="Failed to get bookings",
                data=[]
            )

    async def get_accommodation_bookings(
        self,
        accommodation_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> BookingListResponse:
        """Get all bookings for a specific accommodation"""
        try:
            bookings = await self.booking_repo.get_by_accommodation(accommodation_id, skip, limit)
            return BookingListResponse.from_orm_models(bookings)
        except Exception as e:
            logger.error(f"Error getting bookings for accommodation {accommodation_id}: {str(e)}")
            return BookingListResponse(
                error=True,
                message="Failed to get bookings",
                data=[]
            )

    async def cancel_booking(self, booking_id: UUID) -> bool:
        """Cancel a booking"""
        try:
            # Get booking details
            booking = await self.booking_repo.get_by_id(booking_id)
            if not booking:
                return False
            
            # Initiate refund if payment was completed
            if booking.payment_status == PaymentStatus.COMPLETED:
                await self.payment_provider.initiate_refund(str(booking.payment_id))
            
            # Update booking status
            return await self.booking_repo.update(
                booking_id,
                {"payment_status": PaymentStatus.FAILED}
            )
        except Exception as e:
            logger.error(f"Error canceling booking {booking_id}: {str(e)}")
            return False

    async def accommodation_belongs_to_org(self, accommodation_id: UUID, org_id: UUID) -> bool:
        """Check if accommodation belongs to organization"""
        try:
            return await self.accommodation_repo.belongs_to_org(accommodation_id, org_id)
        except Exception as e:
            logger.error(f"Error checking accommodation ownership: {str(e)}")
            return False