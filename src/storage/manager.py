"""
Storage Manager for Beehive Tracker.
Handles storage provider initialization, configuration, and runtime switching.
"""

import os
import logging
from typing import Dict, Any, Optional, Type, List
from .base import StorageProvider, StorageConfig
from .local_provider import LocalStorageProvider

# Import cloud providers when available
try:
    from .s3_provider import S3StorageProvider
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logging.warning("S3StorageProvider not available - install boto3 for S3 support")

try:
    from .gcs_provider import GCSStorageProvider  
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class StorageManager:
    """Manages storage providers and configuration"""
    
    # Registry of available providers
    _providers: Dict[str, Type[StorageProvider]] = {
        StorageConfig.LOCAL: LocalStorageProvider,
    }
    
    # Add cloud providers if available
    if S3_AVAILABLE:
        _providers[StorageConfig.S3] = S3StorageProvider
    if GCS_AVAILABLE:
        _providers[StorageConfig.GCS] = GCSStorageProvider
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize storage manager"""
        self.config = config or {}
        self._current_provider: Optional[StorageProvider] = None
        self._provider_type: Optional[str] = None
        
        # Load configuration from environment if not provided
        if not self.config:
            self.config = self._load_config_from_env()
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load storage configuration from environment variables"""
        config = {}
        
        # Determine provider type from environment
        provider_type = os.getenv("STORAGE_PROVIDER", StorageConfig.LOCAL).lower()
        config["provider_type"] = provider_type
        
        # Load provider-specific configuration
        if provider_type == StorageConfig.LOCAL:
            config["local"] = {
                "base_path": os.getenv("LOCAL_STORAGE_PATH", "data/uploads"),
                "create_dirs": os.getenv("LOCAL_CREATE_DIRS", "true").lower() == "true",
                "preserve_structure": os.getenv("LOCAL_PRESERVE_STRUCTURE", "true").lower() == "true"
            }
        
        elif provider_type == StorageConfig.S3:
            config["s3"] = {
                "bucket_name": os.getenv("S3_BUCKET_NAME"),
                "region": os.getenv("S3_REGION", "us-east-1"),
                "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "use_ssl": os.getenv("S3_USE_SSL", "true").lower() == "true",
                "create_bucket": os.getenv("S3_CREATE_BUCKET", "false").lower() == "true"
            }
        
        elif provider_type == StorageConfig.GCS:
            config["gcs"] = {
                "bucket_name": os.getenv("GCS_BUCKET_NAME"),
                "project_id": os.getenv("GCS_PROJECT_ID"),
                "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                "create_bucket": os.getenv("GCS_CREATE_BUCKET", "false").lower() == "true"
            }
        
        return config
    
    def get_available_providers(self) -> List[str]:
        """Get list of available storage providers"""
        return list(self._providers.keys())
    
    def get_provider(self, provider_type: Optional[str] = None) -> StorageProvider:
        """
        Get storage provider instance
        
        Args:
            provider_type: Type of provider to get (None for current/default)
            
        Returns:
            StorageProvider instance
        """
        if provider_type is None:
            provider_type = self.config.get("provider_type", StorageConfig.LOCAL)
        
        # Return cached provider if same type
        if self._current_provider and self._provider_type == provider_type:
            return self._current_provider
        
        # Validate provider type
        if provider_type not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ValueError(f"Unknown provider type: {provider_type}. Available: {available}")
        
        # Get provider configuration
        provider_config = self.config.get(provider_type, {})
        
        # Merge with defaults
        default_config = StorageConfig.get_default_config(provider_type)
        provider_config = {**default_config, **provider_config}
        
        # Validate configuration
        is_valid, errors = StorageConfig.validate_config(provider_type, provider_config)
        if not is_valid:
            raise ValueError(f"Invalid configuration for {provider_type}: {', '.join(errors)}")
        
        # Create provider instance
        provider_class = self._providers[provider_type]
        provider_instance = provider_class(provider_config)
        
        # Cache provider
        self._current_provider = provider_instance
        self._provider_type = provider_type
        
        logging.info(f"Initialized storage provider: {provider_type}")
        return provider_instance
    
    def switch_provider(self, provider_type: str, config: Optional[Dict[str, Any]] = None) -> StorageProvider:
        """
        Switch to a different storage provider
        
        Args:
            provider_type: Type of provider to switch to
            config: Optional provider-specific configuration
            
        Returns:
            New StorageProvider instance
        """
        if config:
            self.config[provider_type] = config
        
        # Clear cached provider to force new instance
        self._current_provider = None
        self._provider_type = None
        
        return self.get_provider(provider_type)
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all configured providers"""
        results = {}
        
        for provider_type in self._providers.keys():
            try:
                provider = self.get_provider(provider_type)
                results[provider_type] = provider.health_check()
            except Exception as e:
                results[provider_type] = {
                    "healthy": False,
                    "error": str(e),
                    "provider": provider_type
                }
        
        return results
    
    def migrate_data(self, 
                    from_provider: str, 
                    to_provider: str, 
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Migrate data between storage providers
        
        Args:
            from_provider: Source provider type
            to_provider: Destination provider type  
            user_id: Optional user ID to filter migration
            
        Returns:
            Migration results
        """
        results = {
            "success": False,
            "migrated_files": 0,
            "failed_files": 0,
            "errors": []
        }
        
        try:
            source = self.get_provider(from_provider)
            destination = self.get_provider(to_provider)
            
            # List images from source
            images = source.list_images(user_id=user_id)
            
            for image_info in images:
                try:
                    # Download from source
                    image_data = source.download_image(image_info["storage_path"])
                    if not image_data:
                        results["errors"].append(f"Failed to download: {image_info['filename']}")
                        results["failed_files"] += 1
                        continue
                    
                    # Upload to destination
                    upload_result = destination.upload_image(
                        image_data=image_data,
                        filename=image_info["filename"],
                        user_id=user_id,
                        metadata=image_info.get("metadata", {})
                    )
                    
                    if upload_result.get("success"):
                        results["migrated_files"] += 1
                        logging.info(f"Migrated: {image_info['filename']}")
                    else:
                        results["errors"].append(f"Failed to upload: {image_info['filename']}")
                        results["failed_files"] += 1
                        
                except Exception as e:
                    results["errors"].append(f"Error migrating {image_info['filename']}: {str(e)}")
                    results["failed_files"] += 1
            
            results["success"] = results["failed_files"] == 0
            
        except Exception as e:
            results["errors"].append(f"Migration failed: {str(e)}")
        
        return results
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about current storage configuration"""
        provider_type = self.config.get("provider_type", StorageConfig.LOCAL)
        
        info = {
            "current_provider": provider_type,
            "available_providers": self.get_available_providers(),
            "config": self.config.get(provider_type, {})
        }
        
        # Add health check for current provider
        try:
            provider = self.get_provider()
            info["health"] = provider.health_check()
            info["stats"] = provider.get_storage_stats()
        except Exception as e:
            info["health"] = {"healthy": False, "error": str(e)}
            info["stats"] = {}
        
        return info


# Global storage manager instance
_storage_manager: Optional[StorageManager] = None


def get_storage_manager(config: Optional[Dict[str, Any]] = None) -> StorageManager:
    """Get global storage manager instance"""
    global _storage_manager
    
    if _storage_manager is None or config is not None:
        _storage_manager = StorageManager(config)
    
    return _storage_manager


def get_storage_provider(provider_type: Optional[str] = None) -> StorageProvider:
    """Convenience function to get storage provider"""
    manager = get_storage_manager()
    return manager.get_provider(provider_type)