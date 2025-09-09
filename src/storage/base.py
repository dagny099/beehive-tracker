"""
Base storage interface for the Beehive Tracker application.
Provides abstract interface that all storage providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
import io


class StorageProvider(ABC):
    """Abstract base class for all storage providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize storage provider with configuration"""
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    def upload_image(self, 
                    image_data: bytes, 
                    filename: str, 
                    user_id: Optional[str] = None,
                    inspection_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload an image to storage
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            user_id: User identifier for organizing storage
            inspection_id: Inspection identifier for organizing storage
            metadata: Additional metadata to store with image
            
        Returns:
            Dict containing storage info (path, url, etc.)
        """
        pass
    
    @abstractmethod
    def download_image(self, storage_path: str) -> Optional[bytes]:
        """
        Download an image from storage
        
        Args:
            storage_path: Path/identifier where image is stored
            
        Returns:
            Image bytes or None if not found
        """
        pass
    
    @abstractmethod
    def delete_image(self, storage_path: str) -> bool:
        """
        Delete an image from storage
        
        Args:
            storage_path: Path/identifier where image is stored
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_images(self, 
                   user_id: Optional[str] = None,
                   inspection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List images in storage
        
        Args:
            user_id: Filter by user ID
            inspection_id: Filter by inspection ID
            
        Returns:
            List of image metadata dictionaries
        """
        pass
    
    @abstractmethod
    def get_image_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get a URL for accessing an image (may be temporary/signed)
        
        Args:
            storage_path: Path/identifier where image is stored
            expires_in: URL expiration time in seconds
            
        Returns:
            URL string or None if not available
        """
        pass
    
    @abstractmethod
    def generate_thumbnail(self, 
                          image_data: bytes, 
                          size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
        """
        Generate thumbnail for an image
        
        Args:
            image_data: Original image bytes
            size: Thumbnail dimensions (width, height)
            
        Returns:
            Thumbnail bytes or None if generation failed
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check if storage provider is healthy and accessible
        
        Returns:
            Dict with health status information
        """
        pass
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics (optional, provider-specific)
        
        Returns:
            Dict with storage statistics
        """
        return {
            "provider": self.provider_name,
            "total_size": "unknown",
            "file_count": "unknown",
            "last_accessed": datetime.now().isoformat()
        }


class StorageConfig:
    """Configuration management for storage providers"""
    
    # Storage provider types
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    
    # Default configurations
    DEFAULT_CONFIGS = {
        LOCAL: {
            "base_path": "data/uploads",
            "create_dirs": True,
            "preserve_structure": True
        },
        S3: {
            "bucket_name": None,
            "region": "us-east-1", 
            "use_ssl": True,
            "create_bucket": False
        },
        GCS: {
            "bucket_name": None,
            "project_id": None,
            "credentials_path": None
        },
        AZURE: {
            "account_name": None,
            "account_key": None,
            "container_name": None
        }
    }
    
    @classmethod
    def get_default_config(cls, provider_type: str) -> Dict[str, Any]:
        """Get default configuration for a provider type"""
        return cls.DEFAULT_CONFIGS.get(provider_type, {}).copy()
    
    @classmethod
    def validate_config(cls, provider_type: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration for a provider type
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if provider_type == cls.LOCAL:
            if not config.get("base_path"):
                errors.append("base_path is required for local storage")
                
        elif provider_type == cls.S3:
            if not config.get("bucket_name"):
                errors.append("bucket_name is required for S3 storage")
                
        elif provider_type == cls.GCS:
            if not config.get("bucket_name"):
                errors.append("bucket_name is required for GCS storage")
            if not config.get("project_id"):
                errors.append("project_id is required for GCS storage")
                
        elif provider_type == cls.AZURE:
            if not config.get("account_name"):
                errors.append("account_name is required for Azure storage")
            if not config.get("container_name"):
                errors.append("container_name is required for Azure storage")
        
        return len(errors) == 0, errors