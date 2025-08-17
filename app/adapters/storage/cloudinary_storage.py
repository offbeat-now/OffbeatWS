import uuid
from typing import BinaryIO, Optional
import cloudinary
import cloudinary.uploader
from app.ports.providers.storage_provider import StorageProvider, UploadResult
from app.core.config import get_settings
from app.utils.logger import get_logger
import time

logger = get_logger("cloudinary_storage")

class CloudinaryStorage(StorageProvider):
    """Cloudinary storage implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        self._configure_cloudinary()
    
    def _configure_cloudinary(self):
        """Configure Cloudinary"""
        cloudinary.config(
            cloud_name=self.settings.cloudinary_cloud_name,
            api_key=self.settings.cloudinary_api_key,
            api_secret=self.settings.cloudinary_api_secret
        )
        logger.info("Configured Cloudinary")
    
    def _generate_public_id(self, filename: str, folder: Optional[str] = None) -> str:
        """Generate Cloudinary public ID"""
        # Remove file extension for Cloudinary
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        file_uuid = str(uuid.uuid4())[:8]  # Short UUID
        
        public_id = f"{file_uuid}_{name_without_ext}"
        
        if folder:
            public_id = f"{folder.strip('/')}/{public_id}"
        
        return public_id
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: Optional[str] = None,
        public: bool = True
    ) -> UploadResult:
        """Upload file to Cloudinary"""
        try:
            public_id = self._generate_public_id(filename, folder)
            
            # Read file content
            file.seek(0)
            file_content = file.read()
            file_size = len(file_content)
            
            # Determine resource type
            resource_type = "auto"  # Let Cloudinary auto-detect
            if content_type.startswith('image/'):
                resource_type = "image"
            elif content_type.startswith('video/'):
                resource_type = "video"
            elif content_type.startswith('audio/'):
                resource_type = "video"  # Cloudinary treats audio as video
            else:
                resource_type = "raw"
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type=resource_type,
                type="upload" if public else "private"
            )
            
            logger.info(f"Uploaded file to Cloudinary: {public_id}")
            
            return UploadResult(
                url=result['secure_url'],
                public_id=result['public_id'],
                file_size=file_size,
                content_type=content_type,
                metadata={
                    'cloudinary_url': result['url'],
                    'version': result.get('version'),
                    'format': result.get('format'),
                    'resource_type': result.get('resource_type'),
                    'type': result.get('type')
                }
            )
        
        except Exception as e:
            logger.error(f"Cloudinary upload error: {e}")
            raise Exception(f"Failed to upload file to Cloudinary: {e}")
    
    async def delete_file(self, public_id: str) -> bool:
        """Delete file from Cloudinary"""
        try:
            # Try different resource types
            for resource_type in ['image', 'video', 'raw']:
                try:
                    result = cloudinary.uploader.destroy(
                        public_id,
                        resource_type=resource_type
                    )
                    
                    if result.get('result') == 'ok':
                        logger.info(f"Deleted file from Cloudinary: {public_id}")
                        return True
                
                except Exception:
                    continue
            
            logger.warning(f"Could not delete file from Cloudinary: {public_id}")
            return False
        
        except Exception as e:
            logger.error(f"Cloudinary delete error: {e}")
            return False
    
    async def get_file_url(
        self,
        public_id: str,
        expires_in: Optional[int] = None
    ) -> str:
        """Get file URL from Cloudinary"""
        try:
            if expires_in:
                # Generate signed URL with expiration
                timestamp = int(time.time()) + expires_in
                url = cloudinary.utils.cloudinary_url(
                    public_id,
                    sign_url=True,
                    auth_token={
                        'duration': expires_in
                    }
                )[0]
            else:
                # Generate regular URL
                url = cloudinary.utils.cloudinary_url(public_id)[0]
            
            return url
        
        except Exception as e:
            logger.error(f"Cloudinary URL generation error: {e}")
            raise Exception(f"Failed to generate Cloudinary URL: {e}")
    
    async def file_exists(self, public_id: str) -> bool:
        """Check if file exists in Cloudinary"""
        try:
            # Try different resource types
            for resource_type in ['image', 'video', 'raw']:
                try:
                    result = cloudinary.api.resource(
                        public_id,
                        resource_type=resource_type
                    )
                    
                    if result:
                        return True
                
                except cloudinary.exceptions.NotFound:
                    continue
                except Exception:
                    continue
            
            return False
        
        except Exception:
            return False
    
    async def copy_file(
        self,
        source_public_id: str,
        destination_public_id: str
    ) -> UploadResult:
        """Copy file within Cloudinary"""
        try:
            # Get source file info first
            source_info = None
            for resource_type in ['image', 'video', 'raw']:
                try:
                    source_info = cloudinary.api.resource(
                        source_public_id,
                        resource_type=resource_type
                    )
                    break
                except cloudinary.exceptions.NotFound:
                    continue
            
            if not source_info:
                raise Exception(f"Source file not found: {source_public_id}")
            
            # Copy file using upload with source URL
            result = cloudinary.uploader.upload(
                source_info['secure_url'],
                public_id=destination_public_id,
                resource_type=source_info['resource_type']
            )
            
            logger.info(f"Copied Cloudinary file: {source_public_id} -> {destination_public_id}")
            
            return UploadResult(
                url=result['secure_url'],
                public_id=result['public_id'],
                file_size=source_info.get('bytes', 0),
                content_type=f"{source_info.get('resource_type', 'image')}/{source_info.get('format', 'unknown')}",
                metadata={
                    'cloudinary_url': result['url'],
                    'version': result.get('version'),
                    'format': result.get('format'),
                    'resource_type': result.get('resource_type'),
                    'copied_from': source_public_id
                }
            )
        
        except Exception as e:
            logger.error(f"Cloudinary copy error: {e}")
            raise Exception(f"Failed to copy Cloudinary file: {e}")
