# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

# user necessities
from app.services.user import UserService
from app.schemas.user import (
    UserCreate, UserCreateResponse, 
    UserLogin, UserLoginResponse, 
    RefreshTokenRequest
)
from app.api.dependencies import get_user_service


# org necessities
from app.services.organization import OrganizationService
from app.schemas.organization import (
    OrganizationCreate, OrganizationCreateResponse,
    OrganizationLogin, OrganizationLoginResponse
)
from app.api.dependencies import get_organization_service

router = APIRouter()


################################################################################

# USER

#################################################################################

@router.post("/register/user", response_model=UserCreateResponse, response_model_exclude_none=True)
async def register_user_route(
    user: UserCreate, 
    user_service: UserService = Depends(get_user_service)
) -> Any:
    """Register a new user"""
    try:
        return await user_service.create_user(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login/user", response_model=UserLoginResponse, response_model_exclude_none=True)
async def login_user_route(
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
) -> Any:
    """Login user and return tokens"""
    try:
        return await user_service.authenticate_user(login_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh/user", response_model=UserLoginResponse)
async def refresh_token_route(
    body: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
) -> Any:
    """Refresh access token using refresh token"""
    try:
        return await user_service.refresh_access_token(body.refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# @router.post("/logout/user")
# async def logout_user_route(
#     refresh_token: str,
#     user_service: UserService = Depends(get_user_service)
# ) -> dict:
#     """Logout user by invalidating refresh token"""
#     try:
#         await user_service.logout_user(refresh_token)
#         return {"message": "Successfully logged out"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Logout failed"
#         )

# @router.post("/verify-email/user")
# async def verify_email_route(
#     token: str,
#     user_service: UserService = Depends(get_user_service)
# ) -> dict:
#     """Verify user email with verification token"""
#     try:
#         result = await user_service.verify_email(token)
#         return {"message": "Email verified successfully", "user_id": result.user_id}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email verification failed"
#         )

# @router.post("/forgot-password/user")
# async def forgot_password_route(
#     email: str,
#     user_service: UserService = Depends(get_user_service)
# ) -> dict:
#     """Send password reset email"""
#     try:
#         await user_service.send_password_reset_email(email)
#         return {"message": "Password reset email sent"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Failed to send password reset email"
#         )

# @router.post("/reset-password/user")
# async def reset_password_route(
#     token: str,
#     new_password: str,
#     user_service: UserService = Depends(get_user_service)
# ) -> dict:
#     """Reset password using reset token"""
#     try:
#         await user_service.reset_password(token, new_password)
#         return {"message": "Password reset successfully"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Password reset failed"
#         )


######################################################################

# ORG

######################################################################

#register, login, logout


@router.post("/register/org", response_model=OrganizationCreateResponse, response_model_exclude_none=True)
async def register_org_route(
    org: OrganizationCreate, 
    organization_service: OrganizationService = Depends(get_organization_service)
) -> Any:
    """Register a new organization"""
    try:
        return await organization_service.create_organization(org)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    

@router.post("/login/org", response_model=OrganizationLoginResponse, response_model_exclude_none=True)
async def login_org_route(
    login_data: OrganizationLogin,
    organization_service: OrganizationService = Depends(get_organization_service)
) -> Any:
    """Login organization and return tokens"""
    try:
        return await organization_service.authenticate_organization(login_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


#logout
# @router.post("/logout/org")
# async def logout_org_route(
#     refresh_token: str,
#     organization_service: OrganizationService = Depends(get_organization_service)
# ) -> dict:
#     """Logout organization by invalidating refresh token"""
#     try:
#         await organization_service.logout_org(refresh_token)
#         return {"message": "Successfully logged out"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Logout failed"
#         )