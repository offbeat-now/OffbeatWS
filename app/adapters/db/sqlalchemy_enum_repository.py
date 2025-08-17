from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.models.enum import JobTitleEnum, CompRangeEnum, SkillEnum, LocationEnum
from app.ports.repositories.enum_repository import EnumRepository
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.logger import get_logger

logger = get_logger("sqlalchemy_enum_repository")


class SQLAlchemyEnumRepository(EnumRepository):
    """SQLAlchemy implementation of the EnumRepository interface"""

    def __init__(self, session: AsyncSession):
        # we want to initial a list of enums
        self.session = session

    async def get_enum_by_name(self, name: str) -> Optional[Any]:
        """Get enum by name"""
        try:
            print(f"Fetching enum by name: {name}")
            #switch case to handle different enum types
            if name == "jobtitle":
                enum_class = JobTitleEnum
            elif name == "comprange":
                enum_class = CompRangeEnum
            elif name == "skill":
                enum_class = SkillEnum
            elif name == "location":
                enum_class = LocationEnum
            else:
                logger.error(f"Unknown enum name: {name}")
                return None
            
            # get all values from the enum table
            query = select(enum_class.values)
            result = await self.session.execute(query)
            values = result.scalars().all()

            return values  # returns a list, can be empty
        except Exception as e:
            logger.error(f"Error fetching enum by name {name}: {e}")
            raise DatabaseError("Error fetching enum") from e