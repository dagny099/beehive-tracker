"""
Tests for data migration between storage providers.
Tests migration functionality, EXIF preservation, and error handling.
"""

import os
import io
import tempfile
import shutil
import pytest
import time
from typing import Dict, Any, List

# Add src to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage import StorageManager, get_storage_manager
from storage.local_provider import LocalStorageProvider


def create_test_image_with_exif():
    """Create a test image with EXIF data"""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import piexif
        
        # Create test image
        img = Image.new('RGB', (200, 150), color='blue')
        
        # Create EXIF data
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: "TestCamera",
                piexif.ImageIFD.Model: "TestModel",
                piexif.ImageIFD.DateTime: "2025:01:01 12:00:00",
                piexif.ImageIFD.Software: "BeehiveTracker"
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2025:01:01 12:00:00",
                piexif.ExifIFD.FocalLength: (50, 1),
                piexif.ExifIFD.FNumber: (28, 10)
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitude: ((40, 1), (42, 1), (51, 1)),
                piexif.GPSIFD.GPSLatitudeRef: "N",
                piexif.GPSIFD.GPSLongitude: ((74, 1), (0, 1), (23, 1)), 
                piexif.GPSIFD.GPSLongitudeRef: "W"
            }
        }
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save image with EXIF
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', exif=exif_bytes)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: simple image without EXIF
        return create_simple_test_image()


def create_simple_test_image():
    """Create simple test image without EXIF dependencies"""
    try:
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='green')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        return buffer.getvalue()
    except ImportError:
        # Minimal JPEG-like data
        return b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100 + b'\xff\xd9'


class TestDataMigration:
    """Test data migration between storage providers"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.local_path1 = os.path.join(self.test_dir, "local1")
        self.local_path2 = os.path.join(self.test_dir, "local2")
        
        # Create two local storage configs for testing migration
        self.config1 = {
            "provider_type": "local",
            "local": {
                "base_path": self.local_path1,
                "create_dirs": True,
                "preserve_structure": True
            }
        }
        
        self.config2 = {
            "provider_type": "local", 
            "local": {
                "base_path": self.local_path2,
                "create_dirs": True,
                "preserve_structure": True
            }
        }
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_migration_between_local_providers(self):
        """Test migration between two local storage providers"""
        # Setup source provider with test data
        source_manager = StorageManager(self.config1)
        source_provider = source_manager.get_provider("local")
        
        # Upload test images to source
        test_images = [
            ("image1.jpg", create_simple_test_image()),
            ("image2.jpg", create_simple_test_image()),
            ("image3.jpg", create_simple_test_image())
        ]
        
        uploaded_images = []
        for filename, image_data in test_images:
            result = source_provider.upload_image(
                image_data=image_data,
                filename=filename,
                user_id="test_user",
                inspection_id="migration_test",
                metadata={"original_filename": filename, "test": "migration"}
            )
            assert result["success"] is True
            uploaded_images.append(result["storage_path"])
        
        # Verify images are in source
        source_images = source_provider.list_images(user_id="test_user")
        print(f"Source images found: {len(source_images)}")
        for img in source_images:
            print(f"  - {img}")
        assert len(source_images) >= 3  # Should have at least our 3 images
        
        # Setup destination manager
        dest_manager = StorageManager(self.config2) 
        
        # Perform migration
        migration_result = source_manager.migrate_data(
            from_provider="local",
            to_provider="local",
            user_id="test_user"
        )
        
        # Check migration results
        assert migration_result["success"] is True
        assert migration_result["migrated_files"] == 3
        assert migration_result["failed_files"] == 0
        assert len(migration_result["errors"]) == 0
        
        # Verify images are in destination
        dest_provider = dest_manager.get_provider("local")
        dest_images = dest_provider.list_images(user_id="test_user")
        assert len(dest_images) == 3
        
        # Verify image data integrity
        for orig_filename, orig_data in test_images:
            # Find corresponding image in destination
            dest_image = next(
                img for img in dest_images 
                if orig_filename in img["filename"]
            )
            
            # Download and compare
            downloaded_data = dest_provider.download_image(dest_image["storage_path"])
            assert downloaded_data == orig_data
    
    def test_migration_with_exif_preservation(self):
        """Test that EXIF data is preserved during migration"""
        # Create image with EXIF data
        image_with_exif = create_test_image_with_exif()
        
        # Upload to source
        source_manager = StorageManager(self.config1)
        source_provider = source_manager.get_provider("local")
        
        upload_result = source_provider.upload_image(
            image_data=image_with_exif,
            filename="exif_test.jpg",
            user_id="exif_user"
        )
        assert upload_result["success"] is True
        
        # Perform migration
        dest_manager = StorageManager(self.config2)
        migration_result = source_manager.migrate_data(
            from_provider="local",
            to_provider="local", 
            user_id="exif_user"
        )
        
        assert migration_result["success"] is True
        assert migration_result["migrated_files"] == 1
        
        # Download from destination and verify EXIF preservation
        dest_provider = dest_manager.get_provider("local")
        dest_images = dest_provider.list_images(user_id="exif_user")
        assert len(dest_images) == 1
        
        downloaded_data = dest_provider.download_image(dest_images[0]["storage_path"])
        assert downloaded_data == image_with_exif
        
        # Additional EXIF validation if PIL is available
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            # Load original and migrated images
            orig_img = Image.open(io.BytesIO(image_with_exif))
            migrated_img = Image.open(io.BytesIO(downloaded_data))
            
            # Compare EXIF data (if present)
            orig_exif = orig_img._getexif() or {}
            migrated_exif = migrated_img._getexif() or {}
            
            # Should have same EXIF data
            assert len(orig_exif) == len(migrated_exif)
            
        except ImportError:
            # Skip EXIF comparison if PIL not available
            pass
    
    def test_migration_error_handling(self):
        """Test migration error handling"""
        source_manager = StorageManager(self.config1)
        source_provider = source_manager.get_provider("local")
        
        # Upload a test image
        upload_result = source_provider.upload_image(
            image_data=create_simple_test_image(),
            filename="error_test.jpg",
            user_id="error_user"
        )
        assert upload_result["success"] is True
        
        # Try migration to invalid provider
        migration_result = source_manager.migrate_data(
            from_provider="local",
            to_provider="nonexistent_provider",
            user_id="error_user"
        )
        
        assert migration_result["success"] is False
        assert len(migration_result["errors"]) > 0
    
    def test_partial_migration_failure(self):
        """Test handling of partial migration failures"""
        # This is harder to test without mocking, but we can test the structure
        source_manager = StorageManager(self.config1)
        
        # Test with non-existent user (should succeed but migrate 0 files)
        migration_result = source_manager.migrate_data(
            from_provider="local",
            to_provider="local",
            user_id="nonexistent_user"
        )
        
        assert migration_result["success"] is True  # No failures because no files
        assert migration_result["migrated_files"] == 0
        assert migration_result["failed_files"] == 0
    
    def test_migration_preserves_metadata(self):
        """Test that metadata is preserved during migration"""
        source_manager = StorageManager(self.config1)
        source_provider = source_manager.get_provider("local")
        
        # Upload image with metadata
        test_metadata = {
            "camera": "Canon EOS R5",
            "location": "Beehive Alpha",
            "inspection_type": "routine",
            "weather": "sunny"
        }
        
        upload_result = source_provider.upload_image(
            image_data=create_simple_test_image(),
            filename="metadata_test.jpg",
            user_id="metadata_user",
            metadata=test_metadata
        )
        assert upload_result["success"] is True
        
        # Perform migration
        dest_manager = StorageManager(self.config2)
        migration_result = source_manager.migrate_data(
            from_provider="local",
            to_provider="local",
            user_id="metadata_user"
        )
        
        assert migration_result["success"] is True
        
        # Check metadata preservation
        dest_provider = dest_manager.get_provider("local")
        dest_images = dest_provider.list_images(user_id="metadata_user")
        assert len(dest_images) == 1
        
        migrated_metadata = dest_images[0].get("metadata", {})
        
        # Check that original metadata keys are preserved
        for key, value in test_metadata.items():
            assert key in migrated_metadata or str(value) in str(migrated_metadata)


class TestMigrationIntegration:
    """Integration tests for migration with different scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_bulk_migration_performance(self):
        """Test migration performance with multiple images"""
        # Setup source with multiple images
        local_path = os.path.join(self.test_dir, "bulk_source")
        config = {
            "provider_type": "local",
            "local": {
                "base_path": local_path,
                "create_dirs": True
            }
        }
        
        manager = StorageManager(config)
        provider = manager.get_provider("local")
        
        # Upload multiple images
        num_images = 10
        start_time = time.time()
        
        for i in range(num_images):
            provider.upload_image(
                image_data=create_simple_test_image(),
                filename=f"bulk_image_{i}.jpg",
                user_id="bulk_user"
            )
        
        upload_time = time.time() - start_time
        
        # Setup destination
        dest_path = os.path.join(self.test_dir, "bulk_dest") 
        dest_config = {
            "provider_type": "local",
            "local": {
                "base_path": dest_path,
                "create_dirs": True
            }
        }
        
        dest_manager = StorageManager(dest_config)
        
        # Perform migration
        migration_start = time.time()
        migration_result = manager.migrate_data(
            from_provider="local",
            to_provider="local",
            user_id="bulk_user"
        )
        migration_time = time.time() - migration_start
        
        assert migration_result["success"] is True
        assert migration_result["migrated_files"] == num_images
        
        # Performance should be reasonable (less than 1 second per image for local)
        assert migration_time < num_images * 1.0
        
        print(f"Upload time: {upload_time:.2f}s")
        print(f"Migration time: {migration_time:.2f}s") 
        print(f"Images per second: {num_images / migration_time:.1f}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])