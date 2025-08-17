import hashlib
import hmac
import secrets
from typing import Optional
from utils.logger import get_logger

logger = get_logger("hashing")

class HashUtils:
    """General hashing utilities"""
    
    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Generate cryptographically secure random salt"""
        return secrets.token_hex(length)
    
    @staticmethod
    def hash_string(data: str, salt: Optional[str] = None) -> str:
        """Hash string with optional salt using SHA-256"""
        try:
            if salt:
                data = f"{data}{salt}"
            
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        
        except Exception as e:
            logger.error(f"Error hashing string: {e}")
            raise Exception("Failed to hash string")
    
    @staticmethod
    def hash_file_content(content: bytes) -> str:
        """Hash file content using SHA-256"""
        try:
            return hashlib.sha256(content).hexdigest()
        
        except Exception as e:
            logger.error(f"Error hashing file content: {e}")
            raise Exception("Failed to hash file content")
    
    @staticmethod
    def create_hmac(data: str, secret_key: str) -> str:
        """Create HMAC-SHA256 signature"""
        try:
            return hmac.new(
                secret_key.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        
        except Exception as e:
            logger.error(f"Error creating HMAC: {e}")
            raise Exception("Failed to create HMAC")
    
    @staticmethod
    def verify_hmac(data: str, signature: str, secret_key: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        try:
            expected_signature = HashUtils.create_hmac(data, secret_key)
            return hmac.compare_digest(signature, expected_signature)
        
        except Exception as e:
            logger.error(f"Error verifying HMAC: {e}")
            return False
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID4"""
        import uuid
        return str(uuid.uuid4())
