import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from core.config import get_settings
from utils.logger import get_logger

logger = get_logger("s3_client")

class S3Client:
    """S3 client utilities"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
    
    def get_client(self):
        """Get S3 client"""
        if not self._client:
            self._client = boto3.client(
                's3',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
        return self._client
    
    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            client = self.get_client()
            
            # Check if bucket exists
            try:
                client.head_bucket(Bucket=bucket_name)
                logger.info(f"Bucket {bucket_name} already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise
            
            # Create bucket
            if self.settings.aws_region == 'us-east-1':
                client.create_bucket(Bucket=bucket_name)
            else:
                client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.settings.aws_region}
                )
            
            logger.info(f"Created S3 bucket: {bucket_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating S3 bucket: {e}")
            return False
