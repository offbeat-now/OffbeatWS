# app/api/routes/booking.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from app.services.booking import BookingService
from app.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingListResponse,
    PaymentInitResponse,
    PaymentStatus
)
from app.api.dependencies import (
    get_booking_service,
    get_current_user,
    get_current_org
)
from app.models.auth import User, Organization
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/initiate", response_model=PaymentInitResponse, status_code=status.HTTP_201_CREATED)
async def initiate_booking(
    booking_data: BookingCreate,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    """Initiate a new booking and get payment URL"""
    try:
        # Ensure user_id is set for solo bookings
        if booking_data.booking_type == "solo":
            booking_data.user_id = user.id
        
        # Check for booking conflicts
        if await service.has_booking_conflict(
            booking_data.accommodation_id,
            booking_data.from_date,
            booking_data.to_date
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This accommodation is already booked for the selected dates"
            )
        
        # Calculate price and create payment intent
        payment_info = await service.initiate_booking(booking_data)
        return payment_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate booking"
        )

@router.post("/confirm/{payment_id}", response_model=BookingResponse)
async def confirm_booking(
    payment_id: UUID,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    """Confirm booking after successful payment"""
    try:
        response = await service.confirm_booking(payment_id)
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        return response
    except Exception as e:
        logger.error(f"Error confirming booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm booking"
        )

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    """Get a specific booking"""
    response = await service.get_booking(booking_id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    
    # Verify the booking belongs to the user
    if response.data and response.data.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )
    
    return response

@router.get("/user/me", response_model=BookingListResponse)
async def get_user_bookings(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    """Get all bookings for the current user"""
    try:
        response = await service.get_user_bookings(user.id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting user bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bookings"
        )

@router.get("/accommodation/{accommodation_id}", response_model=BookingListResponse)
async def get_accommodation_bookings(
    accommodation_id: UUID,
    skip: int = 0,
    limit: int = 100,
    org: Organization = Depends(get_current_org),
    service: BookingService = Depends(get_booking_service)
):
    """Get all bookings for a specific accommodation (Organization only)"""
    try:
        # Verify the accommodation belongs to the organization
        if not await service.accommodation_belongs_to_org(accommodation_id, org.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these bookings"
            )
        
        response = await service.get_accommodation_bookings(accommodation_id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting accommodation bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bookings"
        )

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    """Cancel a booking"""
    try:
        # Verify the booking belongs to the user
        booking = await service.get_booking(booking_id)
        if booking.error or booking.data.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or permission denied"
            )
        
        success = await service.cancel_booking(booking_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel booking"
            )
    except Exception as e:
        logger.error(f"Error canceling booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking"
        )