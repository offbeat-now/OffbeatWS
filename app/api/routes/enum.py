# app/api/routes/booking.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Optional
from pydantic import BaseModel

from app.services.enum import EnumService
from app.api.dependencies import get_enum_service
from app.utils.logger import get_logger


logger = get_logger("enum_router")

router = APIRouter()

class EnumResponse(BaseModel):
    error: bool
    message: str
    data: Optional[Any] = None

@router.get("/get/{name}", response_model=EnumResponse, status_code=status.HTTP_200_OK)
async def get_enum_by_name(
    name: str,
    enum_service: EnumService = Depends(get_enum_service)
):
    """Get enum by name"""
    try:
        enum = await enum_service.get_enum_by_name(name)
        if not enum:
            return EnumResponse(
                error=False,
                message=f"Enum '{name}' is empty or not found",
                data=[]  # Return an empty list if no enum found or empty
            )
        return EnumResponse(
            error=False,
            message=f"Enum '{name}' fetched successfully",
            data=enum
        )
    except Exception as e:
        logger.error(f"Error fetching enum by name {name}: {e}")
        return EnumResponse(
            error=True,
            message=str(e),
            data=None
        )
        
