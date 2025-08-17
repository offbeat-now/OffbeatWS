# services/organization.py
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status

from app.ports.repositories.org_repository import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, 
    OrganizationResponse, OrganizationCreateResponse,
    OrganizationLoginResponse, OrganizationLogin
)
from app.models.auth import Organization
from app.core.exceptions import ConflictError, NotFoundError, DatabaseError
from app.utils.password import PasswordManager
from app.utils.jwt import JWTManager
from app.utils.logger import get_logger
from app.utils.file_utils import FileUtils
from app.ports.providers.storage_provider import StorageProvider


logger = get_logger("organization_service")

class OrganizationService:
    def __init__(
        self, 
        org_repository: OrganizationRepository,
        jwt_manager: JWTManager,
        file_utils: FileUtils,
        storage_provider: StorageProvider
    ):
        self.org_repository = org_repository
        self.jwt_manager = jwt_manager
        self.file_utils = file_utils
        self.storage_provider = storage_provider

    async def create_organization(self, org_data: OrganizationCreate) -> OrganizationCreateResponse:
        """Create a new organization"""
        try:
            #email exists check
            existing_org = await self.org_repository.get_by_email(org_data.email)
            if existing_org:
                logger.error(f"Organization with email {org_data.email} already exists")
                return OrganizationCreateResponse(
                    error=True,
                    message="Organization with this email already exists"
                )
            
            #cin exists check
            existing_cin = await self.org_repository.get_by_cin(org_data.cin)
            if existing_cin:
                logger.error(f"Organization with CIN {org_data.cin} already exists")
                return OrganizationCreateResponse(
                    error=True,
                    message="Organization with this CIN already exists"
                )
            
            # Hash password
            org_data.password = PasswordManager.hash_password(org_data.password)

            # Save organization to repository
            org = await self.org_repository.create(org_data)

            logger.info(f"Organization {org.id} created successfully")

            return OrganizationCreateResponse(
                error=False,
                message="Organization created successfully",
                created=True
            )
        
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise DatabaseError("Failed to create organization")

    async def authenticate_organization(self, login_data: OrganizationLogin) -> OrganizationLoginResponse:
        """Authenticate an organization and return tokens"""
        try:
            org = await self.org_repository.get_by_email(login_data.email)
            if not org:
                logger.error(f"Organization not found for email: {login_data.email}")
                return OrganizationLoginResponse(
                    error=False,
                    message="Invalid email or password"
                )

            if not PasswordManager.verify_password(login_data.password, org.password):
                logger.error(f"Password verification failed for org: {login_data.email}")
                return OrganizationLoginResponse(
                    error=False,
                    message="Invalid email or password"
                )

            if org.deleted_at is not None:
                logger.warning(f"Deleted organization attempted login: {login_data.email}")
                return OrganizationLoginResponse(
                    error=False,
                    message="Invalid email or password"
                )

            access_token = self.jwt_manager.create_access_token({"sub": str(org.id)})
            expires_in = self.jwt_manager.settings.access_token_expire_minutes * 60  # seconds

            logger.info(f"Organization {org.id} authenticated successfully")

            return OrganizationLoginResponse(
                error=False,
                message="Login successful",
                access_token=access_token,
                expires_in=expires_in,
                name=org.name,
                email=org.email,
            )
        except Exception as e:
            logger.error(f"Error authenticating organization: {e}")
            return OrganizationLoginResponse(
                error=True,
                message="Authentication failed",
            )

    async def get_org_by_id(self, org_id: UUID) -> OrganizationResponse:
        """Get organization details by ID"""
        try:
            org = await self.org_repository.get_by_id(org_id)
            if not org:
                logger.error(f"Organization not found for ID: {org_id}")
                raise OrganizationResponse(
                    error=True,
                    message="Organization not found",
                    id=org_id
                )

            return OrganizationResponse.from_orm(org)
        except NotFoundError as e:
            logger.warning(f"NotFoundError: {e}")
            raise OrganizationResponse(
                error=True,
                message="Organization not found",
                id=org_id
            )
        except Exception as e:
            logger.error(f"Error fetching organization: {e}")
            raise OrganizationResponse(
                error=True,
                message="Internal server error"
            )
        
    async def update_org(self, org_id: UUID, org_data: OrganizationUpdate) -> OrganizationResponse:
        """Update organization details"""
        try:
            org = await self.org_repository.get_by_id(org_id)
            if not org:
                logger.error(f"Organization not found for ID: {org_id}")
                return OrganizationResponse(
                    error=True,
                    message="Organization not found",
                    id=org_id
                )

            # Update fields
            for key, value in org_data.dict(exclude_unset=True).items():
                setattr(org, key, value)

            updated_org = await self.org_repository.update(org.id, org_data.dict(exclude_unset=True))

            if not updated_org:
                logger.error(f"Failed to update organization: {org_id}")
                return OrganizationResponse(
                    error=True,
                    message="Failed to update organization",
                    id=org_id
                )

            logger.info(f"Organization {org_id} updated successfully")

            print(updated_org)

            return OrganizationResponse(
                error=False,
                message="Organization updated successfully",
                id=updated_org.id,
                name=updated_org.name,
                email=updated_org.email,
                cin=updated_org.cin,
                phone1=updated_org.phone1,
                phone2=updated_org.phone2,
                description=updated_org.description,
                url=updated_org.url,
                rating=updated_org.rating,
                image=updated_org.image
            )
        
        except Exception as e:
            logger.error(f"Error updating organization: {e}")
            return OrganizationResponse(
                error=True,
                message="Internal server error",
                id=org_id
            )
        
    async def upload_org_picture(self, org: Organization, file_url: str) -> OrganizationResponse:
        """Upload organization profile picture"""
        try:
            if not org:
                logger.error("Organization not found for picture upload")
                return OrganizationResponse(
                    error=True,
                    message="Organization not found"
                )
            
            # use regular update method to set the image URL
            image_dict = {"image": file_url}

            updated_org = await self.org_repository.update(org.id, image_dict)

            if not updated_org:
                logger.error(f"Failed to update organization picture for ID: {org.id}")
                return OrganizationResponse(
                    error=True,
                    message="Failed to update organization picture",
                    id=org.id
                )

            logger.info(f"Organization picture updated successfully for ID: {org.id}")

            return OrganizationResponse(
                error=False,
                message="Organization picture updated successfully",
                id=updated_org.id,
                name=updated_org.name,
                email=updated_org.email,
                cin=updated_org.cin,
                phone1=updated_org.phone1,
                phone2=updated_org.phone2,
                description=updated_org.description,
                url=updated_org.url,
                rating=updated_org.rating,
                image=file_url
            )
        
        except Exception as e:
            logger.error(f"Error uploading organization picture: {e}")
            return OrganizationResponse(
                error=True,
                message="Internal server error"
            )
        
    async def get_organization_count(self) -> int:
        """Get total organization count"""
        try:
            return await self.org_repository.get_organization_count_in_db()
        except Exception as e:
            logger.error(f"Error fetching organization count: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch organization count"
            )
