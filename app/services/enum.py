# app/services/job.py
from typing import Any, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.ports.repositories.enum_repository import EnumRepository
from app.utils.logger import get_logger

logger = get_logger("enum_service")

class EnumService:
    def __init__(self, enum_repository: EnumRepository):
        self.repository = enum_repository

    async def get_enum_by_name(self, name: str) -> Optional[Any]:
        """Get enum by name"""
        try:
            enum = await self.repository.get_enum_by_name(name)
            if not enum:
                logger.error(f"Empty set of enum values for name: {name}")
                return None
            
            # return as list of strings 
            return enum
        except Exception as e:
            logger.error(f"Error fetching enum by name {name}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching enum") from e
