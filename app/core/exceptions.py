# core/exceptions.py
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseAppException(Exception):
    """Base exception class for the application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(BaseAppException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class NotFoundError(BaseAppException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )

class UnauthorizedError(BaseAppException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class ForbiddenError(BaseAppException):
    """Raised when user lacks permission"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class ConflictError(BaseAppException):
    """Raised when there's a conflict with current state"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class DatabaseError(BaseAppException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class StorageError(BaseAppException):
    """Raised when file storage operations fail"""
    
    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class CacheError(BaseAppException):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class RateLimitError(BaseAppException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class FileUploadError(BaseAppException):
    """Raised when file upload fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class IntegrityError(BaseAppException):
    """Raised when data integrity constraints are violated"""
    
    def __init__(self, message: str = "Data integrity error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ExternalServiceError(BaseAppException):
    """Raised when external service calls fail"""
    
    def __init__(self, service: str, message: str = "External service error"):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY
        )

class PermissionError(BaseAppException):
    """Raised when user does not have permission to perform an action"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

def create_http_exception(exc: BaseAppException) -> HTTPException:
    """Convert BaseAppException to HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details
        }
    )