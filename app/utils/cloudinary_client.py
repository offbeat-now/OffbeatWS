import cloudinary
import cloudinary.api
from core.config import get_settings
from utils.logger import get_logger

logger = get_logger("cloudinary_client")

class CloudinaryClient:
    """Cloudinary client utilities"""
    
    def __init__(self):
        self.settings = get_settings()
        self._configure()
    
    def _configure(self):
        """Configure Cloudinary"""
        cloudinary.config(
            cloud_name=self.settings.cloudinary_cloud_name,
            api_key=self.settings.cloudinary_api_key,
            api_secret=self.settings.cloudinary_api_secret
        )
    
    def get_usage_info(self) -> dict:
        """Get Cloudinary usage information"""
        try:
            usage = cloudinary.api.usage()
            return {
                'credits_used': usage.get('credits', {}).get('used', 0),
                'credits_limit': usage.get('credits', {}).get('limit', 0),
                'storage_used': usage.get('storage', {}).get('used', 0),
                'transformations_used': usage.get('transformations', {}).get('used', 0)
            }
        
        except Exception as e:
            logger.error(f"Error getting Cloudinary usage: {e}")
            return {}
