from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from dataclasses import dataclass

@dataclass
class UploadResult:
    """Result of file upload operation"""
    url: str
    public_id: str
    file_size: int
    content_type: str
    metadata: dict = None

class StorageProvider(ABC):
    """Abstract storage provider interface"""
    
    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: Optional[str] = None,
        public: bool = True
    ) -> UploadResult:
        """Upload file and return result"""
        pass
    
    @abstractmethod
    async def delete_file(self, public_id: str) -> bool:
        """Delete file by public ID"""
        pass
    
    @abstractmethod
    async def get_file_url(
        self,
        public_id: str,
        expires_in: Optional[int] = None
    ) -> str:
        """Get file URL, optionally with expiration"""
        pass
    
    @abstractmethod
    async def file_exists(self, public_id: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    async def copy_file(
        self,
        source_public_id: str,
        destination_public_id: str
    ) -> UploadResult:
        """Copy file to new location"""
        pass