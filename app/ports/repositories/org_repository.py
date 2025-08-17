from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.auth import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from .base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate], ABC):
    """Abstract organization repository interface"""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Organization]:
        """Get organization by email"""
        pass

    @abstractmethod
    async def get_by_cin(self, cin: str) -> Optional[Organization]:
        """Get organization by CIN (Company Identification Number)"""
        pass
    
    @abstractmethod
    async def get_verified_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[Organization]:
        """Get all verified organizations"""
        pass
    
    @abstractmethod
    async def search_organizations(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """Search organizations by query"""
        pass

    @abstractmethod
    async def get_organization_count_in_db(self) -> int:
        """Get total organization count in the database"""
        pass