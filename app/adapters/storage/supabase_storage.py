import uuid
from typing import BinaryIO, Optional
from supabase import create_client, Client
from app.ports.providers.storage_provider import StorageProvider, UploadResult
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("supabase_storage")

class SupabaseStorage(StorageProvider):
    """Supabase storage implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Client] = None
        self.bucket_name = "uploads"  # Default bucket name
    
    def _get_client(self) -> Client:
        """Get Supabase client"""
        if not self._client:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_key
            )
            logger.info("Initialized Supabase client")
        
        return self._client
    
    def _generate_file_path(self, filename: str, folder: Optional[str] = None) -> str:
        """Generate file path"""
        file_uuid = str(uuid.uuid4())
        file_path = f"{file_uuid}_{filename}"
        
        if folder:
            file_path = f"{folder.strip('/')}/{file_path}"
        
        return file_path
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: Optional[str] = None,
        public: bool = True
    ) -> UploadResult:
        """Upload file to Supabase Storage"""
        try:
            client = self._get_client()
            file_path = self._generate_file_path(filename, folder)
            
            # Read file content
            await file.seek(0)
            file_content = await file.read()
            file_size = len(file_content)
            
            try:
                # Upload file
                result = client.storage.from_(self.bucket_name).upload(
                    file_path,
                    file_content,
                    file_options={
                        'content-type': content_type,
                        'cache-control': '3600'
                    }
                )
            except Exception as e:
                logger.error(f"Supabase upload error: {e}")
                raise Exception(f"Failed to upload file to Supabase: {e}")
            
            # Get public URL
            if public:
                url_result = client.storage.from_(self.bucket_name).get_public_url(file_path)
                url = url_result
            else:
                # Create signed URL (expires in 1 hour)
                url_result = client.storage.from_(self.bucket_name).create_signed_url(
                    file_path,
                    expires_in=3600
                )
                url = url_result.get('signedURL') if isinstance(url_result, dict) else getattr(url_result, "signedURL", None)
            
            if not url:
                raise Exception("Failed to generate file URL")
            
            logger.info(f"Uploaded file to Supabase: {file_path}")
            
            return UploadResult(
                url=url,
                public_id=file_path,
                file_size=file_size,
                content_type=content_type,
                metadata={
                    'bucket': self.bucket_name,
                    'public': public,
                    'supabase_result': result
                }
            )
        
        except Exception as e:
            logger.error(f"Supabase upload error: {e}")
            raise Exception(f"Failed to upload file to Supabase: {e}")
    
    async def delete_file(self, public_id: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            client = self._get_client()
            
            result = client.storage.from_(self.bucket_name).remove([public_id])
            
            if result and not result[0].get('error'):
                logger.info(f"Deleted file from Supabase: {public_id}")
                return True
            else:
                logger.warning(f"Could not delete file from Supabase: {public_id}")
                return False
        
        except Exception as e:
            logger.error(f"Supabase delete error: {e}")
            return False
    
    async def get_file_url(
        self,
        public_id: str,
        expires_in: Optional[int] = None
    ) -> str:
        """Get file URL from Supabase Storage"""
        try:
            client = self._get_client()
            
            if expires_in:
                # Create signed URL
                result = client.storage.from_(self.bucket_name).create_signed_url(
                    public_id,
                    expires_in=expires_in
                )
                
                if result and result.get('signedURL'):
                    return result['signedURL']
                else:
                    raise Exception("Failed to create signed URL")
            else:
                # Get public URL
                url = client.storage.from_(self.bucket_name).get_public_url(public_id)
                return url
        
        except Exception as e:
            logger.error(f"Supabase URL generation error: {e}")
            raise Exception(f"Failed to generate Supabase URL: {e}")
    
    async def file_exists(self, public_id: str) -> bool:
        """Check if file exists in Supabase Storage"""
        try:
            client = self._get_client()
            
            # Try to get file info
            result = client.storage.from_(self.bucket_name).list(
                path=public_id.rsplit('/', 1)[0] if '/' in public_id else "",
                search=public_id.split('/')[-1]
            )
            
            return len(result) > 0
        
        except Exception:
            return False
    
    async def copy_file(
        self,
        source_public_id: str,
        destination_public_id: str
    ) -> UploadResult:
        """Copy file within Supabase Storage"""
        try:
            client = self._get_client()
            
            # Supabase doesn't have direct copy, so we download and re-upload
            # First, get the file content
            result = client.storage.from_(self.bucket_name).download(source_public_id)
            
            if not result:
                raise Exception(f"Could not download source file: {source_public_id}")
            
            # Upload to new location
            upload_result = client.storage.from_(self.bucket_name).upload(
                destination_public_id,
                result
            )
            
            if upload_result.get('error'):
                raise Exception(f"Copy upload error: {upload_result['error']}")
            
            # Get public URL
            url = client.storage.from_(self.bucket_name).get_public_url(destination_public_id)
            
            logger.info(f"Copied Supabase file: {source_public_id} -> {destination_public_id}")
            
            return UploadResult(
                url=url,
                public_id=destination_public_id,
                file_size=len(result),
                content_type="application/octet-stream",  # Default, as we can't determine from copy
                metadata={
                    'bucket': self.bucket_name,
                    'copied_from': source_public_id,
                    'supabase_result': upload_result
                }
            )
        
        except Exception as e:
            logger.error(f"Supabase copy error: {e}")
            raise Exception(f"Failed to copy Supabase file: {e}")
