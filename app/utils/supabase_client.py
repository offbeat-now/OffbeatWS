from supabase import create_client, Client
from core.config import get_settings
from utils.logger import get_logger

logger = get_logger("supabase_client")

class SupabaseClient:
    """Supabase client utilities"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Client = None
    
    def get_client(self) -> Client:
        """Get Supabase client"""
        if not self._client:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_key
            )
        return self._client
    
    def create_storage_bucket_if_not_exists(self, bucket_name: str, public: bool = True) -> bool:
        """Create storage bucket if it doesn't exist"""
        try:
            client = self.get_client()
            
            # Check if bucket exists
            try:
                buckets = client.storage.list_buckets()
                bucket_names = [bucket['name'] for bucket in buckets]
                
                if bucket_name in bucket_names:
                    logger.info(f"Bucket {bucket_name} already exists")
                    return True
            
            except Exception:
                pass
            
            # Create bucket
            result = client.storage.create_bucket(bucket_name, {'public': public})
            
            if not result.get('error'):
                logger.info(f"Created Supabase storage bucket: {bucket_name}")
                return True
            else:
                logger.error(f"Error creating bucket: {result.get('error')}")
                return False
        
        except Exception as e:
            logger.error(f"Error creating Supabase bucket: {e}")
            return False
