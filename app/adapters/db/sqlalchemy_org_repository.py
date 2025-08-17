from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.models.auth import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.ports.repositories.org_repository import OrganizationRepository
from app.adapters.db.sqlalchemy_base_repository import SQLAlchemyRepository
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SQLAlchemyOrganizationRepository(SQLAlchemyRepository[Organization, OrganizationCreate, OrganizationUpdate], OrganizationRepository):
    """SQLAlchemy implementation of the OrganizationRepository"""

    def __init__(self, session: AsyncSession):
        super().__init__(Organization, session)

    async def get_by_email(self, email: str) -> Optional[Organization]:
        result = await self.session.execute(
            select(Organization).where(Organization.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_cin(self, cin: str) -> Optional[Organization]:
        result = await self.session.execute(
            select(Organization).where(Organization.cin == cin)
        )
        return result.scalar_one_or_none()

    async def get_verified_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Organization]:
        query = select(Organization).where(Organization.is_verified == True)
        if order_by:
            query = query.order_by(text(order_by))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def search_organizations(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        result = await self.session.execute(
            select(Organization).where(Organization.name.ilike(f"%{query}%"))
        )
        return result.scalars().all()
    
    async def get_organization_count_in_db(self) -> int:
        # get total counts which are not soft deleted
        result = await self.session.execute(
            select(func.count(Organization.id)).where(Organization.deleted == 'False')
        )
        return result.scalar_one()
        