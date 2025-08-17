from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.services.user import UserService
from app.schemas.user import (
    UserResponse, 
    UserUpdate, 
    UserUpdateResponse,
    UserCountResponse
)
from app.api.dependencies import get_user_service, get_current_user
from app.models.auth import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) :
    """Get current user's profile"""
    try:
        return await user_service.get_user_by_id(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me", response_model=UserUpdateResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) :
    """Update current user's profile"""
    try:
        return await user_service.update_user(current_user, user_update)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/me/picture", response_model=UserUpdateResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) :
    """Upload profile picture for current user"""
    try:
        # Save file and get URL (implementation depends on your storage solution)
        upload_result = await user_service.storage_provider.upload_file(file, file.filename, file.content_type)
        return await user_service.upload_user_picture(current_user, upload_result.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/count", response_model=UserCountResponse)
async def get_user_count(
    user_service: UserService = Depends(get_user_service)
):
    """Get total user count"""
    try:
        count = await user_service.get_user_count_in_db()
        return UserCountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
) :
    """Get any user's public profile by ID"""
    try:
        return await user_service.get_user_by_id(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )