import uuid
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.ports.providers.storage_provider import StorageProvider, UploadResult
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("s3_storage")

class S3Storage(StorageProvider):
    """AWS S3 storage implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        self._s3_client = None
    
    def _get_s3_client(self):
        """Get S3 client"""
        if not self._s3_client:
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
            logger.info("Initialized S3 client")
        
        return self._s3_client
    
    def _generate_key(self, filename: str, folder: Optional[str] = None) -> str:
        """Generate S3 object key"""
        # Add UUID to prevent filename collisions
        file_uuid = str(uuid.uuid4())
        
        if folder:
            return f"{folder.strip('/')}/{file_uuid}_{filename}"
        
        return f"{file_uuid}_{filename}"
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: Optional[str] = None,
        public: bool = True
    ) -> UploadResult:
        """Upload file to S3"""
        try:
            s3_client = self._get_s3_client()
            key = self._generate_key(filename, folder)
            bucket = self.settings.s3_bucket_name
            
            # Read file content
            file.seek(0)
            file_content = file.read()
            file_size = len(file_content)
            
            # Prepare upload arguments
            upload_args = {
                'Bucket': bucket,
                'Key': key,
                'Body': file_content,
                'ContentType': content_type,
            }
            
            # Set ACL for public access if requested
            if public:
                upload_args['ACL'] = 'public-read'
            
            # Upload file
            s3_client.upload_fileobj(
                file,
                bucket,
                key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read' if public else 'private'
                }
            )
            
            # Generate URL
            if public:
                url = f"https://{bucket}.s3.{self.settings.aws_region}.amazonaws.com/{key}"
            else:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=3600  # 1 hour
                )
            
            logger.info(f"Uploaded file to S3: {key}")
            
            return UploadResult(
                url=url,
                public_id=key,
                file_size=file_size,
                content_type=content_type,
                metadata={
                    'bucket': bucket,
                    'region': self.settings.aws_region,
                    'public': public
                }
            )
        
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3 upload error: {e}")
            raise Exception(f"Failed to upload file to S3: {e}")
    
    async def delete_file(self, public_id: str) -> bool:
        """Delete file from S3"""
        try:
            s3_client = self._get_s3_client()
            bucket = self.settings.s3_bucket_name
            
            s3_client.delete_object(Bucket=bucket, Key=public_id)
            logger.info(f"Deleted file from S3: {public_id}")
            
            return True
        
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
    
    async def get_file_url(
        self,
        public_id: str,
        expires_in: Optional[int] = None
    ) -> str:
        """Get file URL"""
        try:
            s3_client = self._get_s3_client()
            bucket = self.settings.s3_bucket_name
            
            if expires_in:
                # Generate presigned URL
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': public_id},
                    ExpiresIn=expires_in
                )
            else:
                # Generate public URL (assumes object is public)
                url = f"https://{bucket}.s3.{self.settings.aws_region}.amazonaws.com/{public_id}"
            
            return url
        
        except ClientError as e:
            logger.error(f"S3 URL generation error: {e}")
            raise Exception(f"Failed to generate S3 URL: {e}")
    
    async def file_exists(self, public_id: str) -> bool:
        """Check if file exists in S3"""
        try:
            s3_client = self._get_s3_client()
            bucket = self.settings.s3_bucket_name
            
            s3_client.head_object(Bucket=bucket, Key=public_id)
            return True
        
        except ClientError:
            return False
    
    async def copy_file(
        self,
        source_public_id: str,
        destination_public_id: str
    ) -> UploadResult:
        """Copy file within S3"""
        try:
            s3_client = self._get_s3_client()
            bucket = self.settings.s3_bucket_name
            
            # Copy object
            copy_source = {'Bucket': bucket, 'Key': source_public_id}
            s3_client.copy_object(
                CopySource=copy_source,
                Bucket=bucket,
                Key=destination_public_id
            )
            
            # Get object metadata
            response = s3_client.head_object(Bucket=bucket, Key=destination_public_id)
            
            url = f"https://{bucket}.s3.{self.settings.aws_region}.amazonaws.com/{destination_public_id}"
            
            logger.info(f"Copied S3 file: {source_public_id} -> {destination_public_id}")
            
            return UploadResult(
                url=url,
                public_id=destination_public_id,
                file_size=response.get('ContentLength', 0),
                content_type=response.get('ContentType', 'application/octet-stream'),
                metadata={
                    'bucket': bucket,
                    'region': self.settings.aws_region,
                    'copied_from': source_public_id
                }
            )
        
        except ClientError as e:
            logger.error(f"S3 copy error: {e}")
            raise Exception(f"Failed to copy S3 file: {e}")
