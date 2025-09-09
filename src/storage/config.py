"""
Configuration management for storage providers.
Handles environment-based configuration, validation, and user preferences.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime


class StorageConfiguration:
    """Manages storage configuration across the application"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize storage configuration
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file or os.path.join("data", "storage_config.json")
        self._config: Dict[str, Any] = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file and environment"""
        # Start with defaults
        self._config = self._get_default_configuration()
        
        # Load from file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(self._config, file_config)
            except Exception as e:
                logging.warning(f"Failed to load config file: {e}")
        
        # Override with environment variables
        env_config = self._load_from_environment()
        self._merge_config(self._config, env_config)
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "provider_type": "local",
            "auto_migrate": False,
            "enable_thumbnails": True,
            "thumbnail_size": [200, 200],
            "metadata_storage": True,
            "providers": {
                "local": {
                    "base_path": "data/uploads",
                    "create_dirs": True,
                    "preserve_structure": True,
                    "max_file_size_mb": 50
                },
                "s3": {
                    "bucket_name": None,
                    "region": "us-east-1",
                    "use_ssl": True,
                    "create_bucket": False,
                    "storage_class": "STANDARD",
                    "server_side_encryption": "AES256"
                },
                "gcs": {
                    "bucket_name": None,
                    "project_id": None,
                    "credentials_path": None,
                    "create_bucket": False,
                    "storage_class": "STANDARD"
                }
            },
            "security": {
                "signed_url_expiry": 3600,
                "require_authentication": True,
                "encrypt_metadata": False
            },
            "performance": {
                "concurrent_uploads": 3,
                "chunk_size_mb": 5,
                "retry_attempts": 3,
                "timeout_seconds": 30
            }
        }
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        
        # General settings
        if os.getenv("STORAGE_PROVIDER"):
            env_config["provider_type"] = os.getenv("STORAGE_PROVIDER").lower()
        
        if os.getenv("STORAGE_AUTO_MIGRATE"):
            env_config["auto_migrate"] = os.getenv("STORAGE_AUTO_MIGRATE").lower() == "true"
        
        # Provider-specific settings
        providers = {}
        
        # Local storage
        local_config = {}
        if os.getenv("LOCAL_STORAGE_PATH"):
            local_config["base_path"] = os.getenv("LOCAL_STORAGE_PATH")
        if os.getenv("LOCAL_CREATE_DIRS"):
            local_config["create_dirs"] = os.getenv("LOCAL_CREATE_DIRS").lower() == "true"
        if os.getenv("LOCAL_MAX_FILE_SIZE_MB"):
            local_config["max_file_size_mb"] = int(os.getenv("LOCAL_MAX_FILE_SIZE_MB"))
        if local_config:
            providers["local"] = local_config
        
        # S3 storage
        s3_config = {}
        if os.getenv("S3_BUCKET_NAME"):
            s3_config["bucket_name"] = os.getenv("S3_BUCKET_NAME")
        if os.getenv("S3_REGION"):
            s3_config["region"] = os.getenv("S3_REGION")
        if os.getenv("AWS_ACCESS_KEY_ID"):
            s3_config["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
        if os.getenv("AWS_SECRET_ACCESS_KEY"):
            s3_config["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        if os.getenv("S3_USE_SSL"):
            s3_config["use_ssl"] = os.getenv("S3_USE_SSL").lower() == "true"
        if os.getenv("S3_STORAGE_CLASS"):
            s3_config["storage_class"] = os.getenv("S3_STORAGE_CLASS")
        if s3_config:
            providers["s3"] = s3_config
        
        # GCS storage
        gcs_config = {}
        if os.getenv("GCS_BUCKET_NAME"):
            gcs_config["bucket_name"] = os.getenv("GCS_BUCKET_NAME")
        if os.getenv("GCS_PROJECT_ID"):
            gcs_config["project_id"] = os.getenv("GCS_PROJECT_ID")
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            gcs_config["credentials_path"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if gcs_config:
            providers["gcs"] = gcs_config
        
        if providers:
            env_config["providers"] = providers
        
        # Security settings
        security = {}
        if os.getenv("STORAGE_SIGNED_URL_EXPIRY"):
            security["signed_url_expiry"] = int(os.getenv("STORAGE_SIGNED_URL_EXPIRY"))
        if os.getenv("STORAGE_REQUIRE_AUTH"):
            security["require_authentication"] = os.getenv("STORAGE_REQUIRE_AUTH").lower() == "true"
        if security:
            env_config["security"] = security
        
        return env_config
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_config(self, provider_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific provider or full config
        
        Args:
            provider_type: Provider type to get config for (None for full config)
            
        Returns:
            Configuration dictionary
        """
        if provider_type:
            return self._config.get("providers", {}).get(provider_type, {})
        return self._config.copy()
    
    def set_provider(self, provider_type: str, save: bool = True) -> bool:
        """
        Set the current storage provider
        
        Args:
            provider_type: Provider type to set as current
            save: Whether to save configuration to file
            
        Returns:
            True if successful, False otherwise
        """
        if provider_type not in self._config.get("providers", {}):
            logging.error(f"Unknown provider type: {provider_type}")
            return False
        
        self._config["provider_type"] = provider_type
        
        if save:
            return self.save_configuration()
        
        return True
    
    def update_provider_config(self, 
                              provider_type: str, 
                              config: Dict[str, Any], 
                              save: bool = True) -> bool:
        """
        Update configuration for a specific provider
        
        Args:
            provider_type: Provider type to update
            config: Configuration updates
            save: Whether to save configuration to file
            
        Returns:
            True if successful, False otherwise
        """
        if "providers" not in self._config:
            self._config["providers"] = {}
        
        if provider_type not in self._config["providers"]:
            self._config["providers"][provider_type] = {}
        
        self._merge_config(self._config["providers"][provider_type], config)
        
        if save:
            return self.save_configuration()
        
        return True
    
    def validate_provider_config(self, provider_type: str) -> Tuple[bool, List[str]]:
        """
        Validate configuration for a provider
        
        Args:
            provider_type: Provider type to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        from .base import StorageConfig
        
        config = self.get_config(provider_type)
        return StorageConfig.validate_config(provider_type, config)
    
    def save_configuration(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create directory if needed
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            # Add metadata
            config_to_save = self._config.copy()
            config_to_save["_metadata"] = {
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            
            logging.info(f"Configuration saved to: {self.config_file}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False
    
    def reset_to_defaults(self, save: bool = True) -> bool:
        """
        Reset configuration to defaults
        
        Args:
            save: Whether to save after reset
            
        Returns:
            True if successful, False otherwise
        """
        self._config = self._get_default_configuration()
        
        if save:
            return self.save_configuration()
        
        return True
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all configured providers"""
        status = {}
        
        for provider_type in self._config.get("providers", {}):
            config = self.get_config(provider_type)
            is_valid, errors = self.validate_provider_config(provider_type)
            
            status[provider_type] = {
                "configured": bool(config),
                "valid": is_valid,
                "errors": errors,
                "is_current": self._config.get("provider_type") == provider_type
            }
        
        return status
    
    def get_migration_plan(self, from_provider: str, to_provider: str) -> Dict[str, Any]:
        """
        Generate a migration plan between providers
        
        Args:
            from_provider: Source provider
            to_provider: Destination provider
            
        Returns:
            Migration plan dictionary
        """
        plan = {
            "from_provider": from_provider,
            "to_provider": to_provider,
            "feasible": False,
            "estimated_time": "unknown",
            "requirements": [],
            "warnings": []
        }
        
        # Check if both providers are configured
        from_config = self.get_config(from_provider)
        to_config = self.get_config(to_provider)
        
        if not from_config:
            plan["warnings"].append(f"Source provider '{from_provider}' is not configured")
            return plan
        
        if not to_config:
            plan["warnings"].append(f"Destination provider '{to_provider}' is not configured")
            return plan
        
        # Validate configurations
        from_valid, from_errors = self.validate_provider_config(from_provider)
        to_valid, to_errors = self.validate_provider_config(to_provider)
        
        if not from_valid:
            plan["warnings"].extend([f"Source config error: {e}" for e in from_errors])
        
        if not to_valid:
            plan["warnings"].extend([f"Destination config error: {e}" for e in to_errors])
        
        plan["feasible"] = from_valid and to_valid
        
        if plan["feasible"]:
            plan["requirements"] = [
                "Backup existing data before migration",
                "Ensure sufficient storage space in destination",
                "Verify network connectivity to destination",
                "Plan for potential downtime during migration"
            ]
            
            if from_provider == "local":
                plan["estimated_time"] = "Fast (local read, network upload)"
            elif to_provider == "local":
                plan["estimated_time"] = "Medium (network download, local write)"
            else:
                plan["estimated_time"] = "Slow (network download + upload)"
        
        return plan


# Global configuration instance
_storage_config: Optional[StorageConfiguration] = None


def get_storage_config(config_file: Optional[str] = None) -> StorageConfiguration:
    """Get global storage configuration instance"""
    global _storage_config
    
    if _storage_config is None or config_file is not None:
        _storage_config = StorageConfiguration(config_file)
    
    return _storage_config