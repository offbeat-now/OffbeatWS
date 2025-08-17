import os
import re
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("file_utils")

class FileUtils:
    """File handling utilities"""
    
    def __init__(self):
        self.settings = get_settings()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        try:
            # Remove or replace unsafe characters
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # Remove leading/trailing spaces and dots
            filename = filename.strip('. ')
            
            # Ensure filename is not empty
            if not filename:
                filename = "unnamed_file"
            
            # Limit filename length
            name, ext = os.path.splitext(filename)
            if len(name) > 100:
                name = name[:100]
            
            return f"{name}{ext}".lower()
        
        except Exception as e:
            logger.error(f"Error sanitizing filename: {e}")
            return "unnamed_file"
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension from filename"""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type from filename"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    def is_allowed_file_type(self, content_type: str) -> bool:
        """Check if file type is allowed"""
        return content_type in self.settings.allowed_file_types
    
    def is_allowed_file_size(self, file_size: int) -> bool:
        """Check if file size is within limits"""
        return file_size <= self.settings.max_file_size
    
    def validate_file(
        self,
        filename: str,
        content_type: str,
        file_size: int
    ) -> Tuple[bool, List[str]]:
        """Validate file against all constraints"""
        errors = []
        
        # Check file type
        if not self.is_allowed_file_type(content_type):
            errors.append(f"File type '{content_type}' is not allowed")
        
        # Check file size
        if not self.is_allowed_file_size(file_size):
            max_size_mb = self.settings.max_file_size / (1024 * 1024)
            errors.append(f"File size exceeds maximum limit of {max_size_mb:.1f} MB")
        
        # Check filename
        if not filename or filename.isspace():
            errors.append("Filename cannot be empty")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        try:
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            
            return f"{size_bytes:.1f} {size_names[i]}"
        
        except Exception:
            return "Unknown size"
    
    @staticmethod
    def generate_unique_filename(original_filename: str, suffix: str = "") -> str:
        """Generate unique filename with timestamp"""
        try:
            import time
            
            name, ext = os.path.splitext(original_filename)
            timestamp = str(int(time.time()))
            
            if suffix:
                return f"{name}_{suffix}_{timestamp}{ext}"
            else:
                return f"{name}_{timestamp}{ext}"
        
        except Exception:
            return f"file_{int(time.time())}.bin"
        

    # save
