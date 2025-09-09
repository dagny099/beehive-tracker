"""
Tests for StorageConfiguration class.
Tests file-based config, environment variables, and configuration management.
"""

import os
import tempfile
import shutil
import json
import pytest
from unittest.mock import patch
from typing import Dict, Any

# Add src to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.config import StorageConfiguration, get_storage_config


class TestStorageConfiguration:
    """Test suite for StorageConfiguration functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "test_config.json")
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = StorageConfiguration(self.config_file)
        
        defaults = config.get_config()
        assert defaults["provider_type"] == "local"
        assert defaults["auto_migrate"] is False
        assert defaults["enable_thumbnails"] is True
        assert "providers" in defaults
        assert "local" in defaults["providers"]
        assert "s3" in defaults["providers"]
    
    def test_file_based_configuration(self):
        """Test loading configuration from file"""
        # Create test config file
        test_config = {
            "provider_type": "s3",
            "auto_migrate": True,
            "providers": {
                "s3": {
                    "bucket_name": "test-bucket",
                    "region": "us-west-2"
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Load configuration
        config = StorageConfiguration(self.config_file)
        loaded = config.get_config()
        
        assert loaded["provider_type"] == "s3"
        assert loaded["auto_migrate"] is True
        assert loaded["providers"]["s3"]["bucket_name"] == "test-bucket"
        assert loaded["providers"]["s3"]["region"] == "us-west-2"
    
    @patch.dict(os.environ, {
        'STORAGE_PROVIDER': 'local',
        'LOCAL_STORAGE_PATH': '/custom/path',
        'STORAGE_AUTO_MIGRATE': 'true',
        'S3_BUCKET_NAME': 'env-bucket'
    })
    def test_environment_override(self):
        """Test environment variables override file config"""
        # Create file config
        file_config = {
            "provider_type": "s3",
            "auto_migrate": False,
            "providers": {
                "local": {"base_path": "/file/path"},
                "s3": {"bucket_name": "file-bucket"}
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(file_config, f)
        
        # Load with environment override
        config = StorageConfiguration(self.config_file)
        loaded = config.get_config()
        
        # Environment should override file
        assert loaded["provider_type"] == "local"  # From env
        assert loaded["auto_migrate"] is True     # From env
        assert loaded["providers"]["local"]["base_path"] == "/custom/path"  # From env
        assert loaded["providers"]["s3"]["bucket_name"] == "env-bucket"     # From env
    
    def test_get_provider_config(self):
        """Test getting configuration for specific provider"""
        config = StorageConfiguration(self.config_file)
        
        local_config = config.get_config("local")
        assert "base_path" in local_config
        assert "create_dirs" in local_config
        
        s3_config = config.get_config("s3") 
        assert "bucket_name" in s3_config
        assert "region" in s3_config
    
    def test_set_provider(self):
        """Test setting current storage provider"""
        config = StorageConfiguration(self.config_file)
        
        # Set provider
        success = config.set_provider("s3", save=False)
        assert success is True
        
        # Verify it's set
        full_config = config.get_config()
        assert full_config["provider_type"] == "s3"
        
        # Test invalid provider
        success = config.set_provider("invalid", save=False)
        assert success is False
    
    def test_update_provider_config(self):
        """Test updating provider configuration"""
        config = StorageConfiguration(self.config_file)
        
        # Update S3 config
        s3_updates = {
            "bucket_name": "new-bucket",
            "region": "eu-west-1"
        }
        
        success = config.update_provider_config("s3", s3_updates, save=False)
        assert success is True
        
        # Verify updates
        s3_config = config.get_config("s3")
        assert s3_config["bucket_name"] == "new-bucket"
        assert s3_config["region"] == "eu-west-1"
    
    def test_validate_provider_config(self):
        """Test provider configuration validation"""
        config = StorageConfiguration(self.config_file)
        
        # Test valid local config
        is_valid, errors = config.validate_provider_config("local")
        assert is_valid is True
        assert len(errors) == 0
        
        # Update with invalid config
        config.update_provider_config("local", {"base_path": ""}, save=False)
        
        # Test now invalid config  
        is_valid, errors = config.validate_provider_config("local")
        assert is_valid is False
        assert len(errors) > 0
    
    def test_save_configuration(self):
        """Test saving configuration to file"""
        config = StorageConfiguration(self.config_file)
        
        # Make changes
        config.set_provider("s3", save=False)
        config.update_provider_config("s3", {"bucket_name": "saved-bucket"}, save=False)
        
        # Save
        success = config.save_configuration()
        assert success is True
        assert os.path.exists(self.config_file)
        
        # Verify saved content
        with open(self.config_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config["provider_type"] == "s3"
        assert saved_config["providers"]["s3"]["bucket_name"] == "saved-bucket"
        assert "_metadata" in saved_config
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults"""
        config = StorageConfiguration(self.config_file)
        
        # Make changes
        config.set_provider("s3", save=False)
        config.update_provider_config("local", {"base_path": "/custom"}, save=False)
        
        # Reset
        success = config.reset_to_defaults(save=False)
        assert success is True
        
        # Verify reset
        reset_config = config.get_config()
        assert reset_config["provider_type"] == "local"  # Default
        assert reset_config["providers"]["local"]["base_path"] == "data/uploads"  # Default
    
    def test_get_provider_status(self):
        """Test getting status for all providers"""
        config = StorageConfiguration(self.config_file)
        status = config.get_provider_status()
        
        assert "local" in status
        assert "s3" in status
        
        # Check local status
        local_status = status["local"]
        assert local_status["configured"] is True
        assert local_status["valid"] is True
        assert local_status["is_current"] is True  # Default provider
        
        # Check S3 status
        s3_status = status["s3"]
        assert s3_status["configured"] is True
        assert s3_status["is_current"] is False
    
    def test_get_migration_plan(self):
        """Test generating migration plans between providers"""
        config = StorageConfiguration(self.config_file)
        
        # Valid migration plan
        plan = config.get_migration_plan("local", "s3")
        assert plan["from_provider"] == "local"
        assert plan["to_provider"] == "s3"
        assert "feasible" in plan
        assert "requirements" in plan
        assert "warnings" in plan
        
        # Invalid migration (missing provider)
        plan = config.get_migration_plan("local", "nonexistent")
        assert plan["feasible"] is False
        assert len(plan["warnings"]) > 0


class TestConfigurationMerging:
    """Test configuration merging behavior"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "merge_test.json")
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_nested_config_merging(self):
        """Test that nested configurations merge properly"""
        # Create file with nested config
        file_config = {
            "providers": {
                "s3": {
                    "bucket_name": "file-bucket",
                    "region": "us-east-1"
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(file_config, f)
        
        with patch.dict(os.environ, {'S3_REGION': 'us-west-2'}):
            config = StorageConfiguration(self.config_file)
            s3_config = config.get_config("s3")
            
            # Should have bucket from file and region from env
            assert s3_config["bucket_name"] == "file-bucket"
            assert s3_config["region"] == "us-west-2"


class TestGlobalConfiguration:
    """Test global configuration singleton"""
    
    def test_get_storage_config_singleton(self):
        """Test that get_storage_config returns singleton"""
        config1 = get_storage_config()
        config2 = get_storage_config()
        
        assert config1 is config2  # Same instance
    
    def test_get_storage_config_with_file(self):
        """Test get_storage_config with custom file"""
        test_file = "/tmp/test_storage_config.json"
        config = get_storage_config(test_file)
        
        assert config.config_file == test_file


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])