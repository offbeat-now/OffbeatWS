from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import jwt
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("jwt")

class JWTManager:
    """JWT token management utilities"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(
                    minutes=self.settings.access_token_expire_minutes
                )
            
            to_encode.update({"exp": expire, "type": "access"})
            
            encoded_jwt = jwt.encode(
                to_encode,
                self.settings.secret_key,
                algorithm=self.settings.algorithm
            )
            
            return encoded_jwt
        
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise Exception("Failed to create access token")
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(
                    days=self.settings.refresh_token_expire_days
                )
            
            to_encode.update({"exp": expire, "type": "refresh"})
            
            encoded_jwt = jwt.encode(
                to_encode,
                self.settings.secret_key,
                algorithm=self.settings.algorithm
            )
            
            return encoded_jwt
        
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise Exception("Failed to create refresh token")
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
                return None
            
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiry datetime"""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )
            
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            
            return None
        
        except Exception:
            return None

    