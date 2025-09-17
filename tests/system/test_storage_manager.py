"""
Unit tests for StorageManager and provider switching functionality.
Tests configuration loading, provider initialization, and seamless switching.
"""

import os
import tempfile
import shutil
import json
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add src to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage import StorageManager, StorageConfig, get_storage_manager
from storage.local_provider import LocalStorageProvider


class TestStorageManager:
    """Test suite for StorageManager functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            "provider_type": "local",
            "local": {
                "base_path": os.path.join(self.test_dir, "uploads"),
                "create_dirs": True,
                "preserve_structure": True
            }
        }
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_storage_manager_initialization(self):
        """Test StorageManager initialization with config"""
        manager = StorageManager(self.config)
        
        assert manager.config == self.config
        assert manager._current_provider is None
        assert manager._provider_type is None
    
    def test_get_available_providers(self):
        """Test getting list of available providers"""
        manager = StorageManager(self.config)
        providers = manager.get_available_providers()
        
        assert "local" in providers
        assert isinstance(providers, list)
    
    def test_get_local_provider(self):
        """Test getting local storage provider"""
        manager = StorageManager(self.config)
        provider = manager.get_provider("local")
        
        assert isinstance(provider, LocalStorageProvider)
        assert provider.base_path == self.config["local"]["base_path"]
    
    def test_provider_caching(self):
        """Test that providers are cached properly"""
        manager = StorageManager(self.config)
        
        provider1 = manager.get_provider("local")
        provider2 = manager.get_provider("local")
        
        assert provider1 is provider2  # Same instance
        assert manager._provider_type == "local"
    
    def test_provider_switching(self):
        """Test switching between providers"""
        # Setup config with multiple providers
        multi_config = {
            "provider_type": "local",
            "local": self.config["local"],
            "s3": {
                "bucket_name": "test-bucket",
                "region": "us-east-1"
            }
        }
        
        manager = StorageManager(multi_config)
        
        # Get local provider first
        local_provider = manager.get_provider("local")
        assert isinstance(local_provider, LocalStorageProvider)
        
        # Switch to different provider type (will fail without boto3, but tests switching logic)
        with pytest.raises((ValueError, ImportError)):  # S3 provider not available in test env
            manager.switch_provider("s3")
    
    def test_invalid_provider_type(self):
        """Test handling of invalid provider types"""
        manager = StorageManager(self.config)
        
        with pytest.raises(ValueError, match="Unknown provider type"):
            manager.get_provider("invalid_provider")
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test missing required config
        bad_config = {
            "provider_type": "local",
            "local": {}  # Missing base_path
        }
        
        manager = StorageManager(bad_config)
        with pytest.raises(ValueError, match="Invalid configuration"):
            manager.get_provider("local")
    
    def test_health_check_all(self):
        """Test health check across all providers"""
        manager = StorageManager(self.config)
        results = manager.health_check_all()
        
        assert "local" in results
        assert isinstance(results["local"], dict)
    
    def test_get_storage_info(self):
        """Test getting storage information"""
        manager = StorageManager(self.config)
        info = manager.get_storage_info()
        
        assert info["current_provider"] == "local"
        assert "available_providers" in info
        assert "config" in info
        assert "health" in info


class TestStorageManagerEnvironment:
    """Test StorageManager environment variable loading"""
    
    @patch.dict(os.environ, {
        'STORAGE_PROVIDER': 'local',
        'LOCAL_STORAGE_PATH': '/tmp/test_storage',
        'LOCAL_CREATE_DIRS': 'true'
    })
    def test_env_config_loading(self):
        """Test loading configuration from environment variables"""
        manager = StorageManager()  # No config provided, should load from env
        
        config = manager.config
        assert config["provider_type"] == "local"
        assert config["local"]["base_path"] == "/tmp/test_storage"
        assert config["local"]["create_dirs"] is True
    
    @patch.dict(os.environ, {
        'STORAGE_PROVIDER': 's3',
        'S3_BUCKET_NAME': 'test-bucket',
        'S3_REGION': 'us-west-2',
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    def test_s3_env_config_loading(self):
        """Test loading S3 configuration from environment"""
        manager = StorageManager()
        
        config = manager.config
        assert config["provider_type"] == "s3"
        assert config["s3"]["bucket_name"] == "test-bucket"
        assert config["s3"]["region"] == "us-west-2"
        assert config["s3"]["aws_access_key_id"] == "test-key"


class TestStorageConfig:
    """Test StorageConfig validation and defaults"""
    
    def test_get_default_config(self):
        """Test getting default configuration for providers"""
        local_config = StorageConfig.get_default_config(StorageConfig.LOCAL)
        
        assert "base_path" in local_config
        assert local_config["create_dirs"] is True
    
    def test_validate_local_config(self):
        """Test local storage configuration validation"""
        # Valid config
        valid_config = {"base_path": "/tmp/storage"}
        is_valid, errors = StorageConfig.validate_config(StorageConfig.LOCAL, valid_config)
        
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid config
        invalid_config = {}  # Missing base_path
        is_valid, errors = StorageConfig.validate_config(StorageConfig.LOCAL, invalid_config)
        
        assert is_valid is False
        assert "base_path is required" in errors[0]
    
    def test_validate_s3_config(self):
        """Test S3 configuration validation"""
        # Valid config
        valid_config = {"bucket_name": "test-bucket"}
        is_valid, errors = StorageConfig.validate_config(StorageConfig.S3, valid_config)
        
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid config
        invalid_config = {}  # Missing bucket_name
        is_valid, errors = StorageConfig.validate_config(StorageConfig.S3, invalid_config)
        
        assert is_valid is False
        assert "bucket_name is required" in errors[0]


class TestGlobalStorageManager:
    """Test global storage manager singleton"""
    
    def test_get_storage_manager_singleton(self):
        """Test that get_storage_manager returns singleton"""
        manager1 = get_storage_manager()
        manager2 = get_storage_manager()
        
        assert manager1 is manager2  # Same instance
    
    def test_get_storage_manager_with_config(self):
        """Test get_storage_manager with custom config"""
        config = {"provider_type": "local"}
        manager = get_storage_manager(config)
        
        assert manager.config == config


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])