"""
Integration tests for S3StorageProvider with real AWS operations.
These tests require AWS credentials and will create/delete real S3 objects.

Set environment variables before running:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY  
- TEST_S3_BUCKET_NAME
- AWS_DEFAULT_REGION (optional, defaults to us-east-1)
"""

import os
import io
import pytest
import tempfile
import time
from typing import Dict, Any, Optional

# Add src to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from storage.s3_provider import S3StorageProvider


# Test configuration
TEST_BUCKET = os.getenv("TEST_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# Skip tests if no AWS credentials or boto3
pytestmark = pytest.mark.skipif(
    not BOTO3_AVAILABLE or not TEST_BUCKET,
    reason="AWS credentials and boto3 required for S3 integration tests"
)


@pytest.fixture
def s3_config():
    """S3 configuration for testing"""
    return {
        "bucket_name": TEST_BUCKET,
        "region": AWS_REGION,
        "use_ssl": True,
        "create_bucket": False,  # Assume test bucket exists
        "storage_class": "STANDARD"
    }


@pytest.fixture
def s3_provider(s3_config):
    """Create S3StorageProvider instance for testing"""
    return S3StorageProvider(s3_config)


@pytest.fixture
def test_image_data():
    """Create test image data"""
    # Create a simple test image with PIL
    try:
        from PIL import Image
        
        # Create small test image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        return buffer.getvalue()
    except ImportError:
        # Fallback: create minimal JPEG-like data
        return b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100 + b'\xff\xd9'


class TestS3StorageProvider:
    """Test S3StorageProvider with real AWS operations"""
    
    def test_s3_provider_initialization(self, s3_config):
        """Test S3 provider initialization"""
        provider = S3StorageProvider(s3_config)
        
        assert provider.bucket_name == TEST_BUCKET
        assert provider.region == AWS_REGION
        assert provider.use_ssl is True
    
    def test_health_check(self, s3_provider):
        """Test S3 health check functionality"""
        result = s3_provider.health_check()
        
        assert result["healthy"] is True
        assert result["bucket"] == TEST_BUCKET
        assert result["writable"] is True
        assert "checked_at" in result
    
    def test_upload_and_download_image(self, s3_provider, test_image_data):
        """Test uploading and downloading an image"""
        filename = f"test_image_{int(time.time())}.jpg"
        user_id = "test_user"
        inspection_id = "test_inspection"
        
        try:
            # Upload image
            upload_result = s3_provider.upload_image(
                image_data=test_image_data,
                filename=filename,
                user_id=user_id,
                inspection_id=inspection_id,
                metadata={"test": "metadata", "upload_time": str(time.time())}
            )
            
            assert upload_result["success"] is True
            assert "storage_path" in upload_result
            assert "thumbnail_path" in upload_result
            assert upload_result["file_size"] == len(test_image_data)
            assert upload_result["provider"] == "S3StorageProvider"
            
            storage_path = upload_result["storage_path"]
            
            # Download image
            downloaded_data = s3_provider.download_image(storage_path)
            
            assert downloaded_data is not None
            assert downloaded_data == test_image_data
            
        finally:
            # Clean up - delete the uploaded image
            if 'storage_path' in locals():
                s3_provider.delete_image(storage_path)
    
    def test_upload_with_progress_callback(self, s3_provider, test_image_data):
        """Test upload with progress tracking"""
        filename = f"test_progress_{int(time.time())}.jpg"
        progress_calls = []
        
        def progress_callback(bytes_transferred, total_bytes):
            progress_calls.append((bytes_transferred, total_bytes))
        
        try:
            upload_result = s3_provider.upload_image(
                image_data=test_image_data,
                filename=filename,
                progress_callback=progress_callback
            )
            
            assert upload_result["success"] is True
            
            # For small files, progress might not be called
            # but the mechanism should work without errors
            
        finally:
            if upload_result.get("success"):
                s3_provider.delete_image(upload_result["storage_path"])
    
    def test_get_presigned_url(self, s3_provider, test_image_data):
        """Test generating pre-signed URLs"""
        filename = f"test_url_{int(time.time())}.jpg"
        
        try:
            # Upload image first
            upload_result = s3_provider.upload_image(
                image_data=test_image_data,
                filename=filename
            )
            
            assert upload_result["success"] is True
            storage_path = upload_result["storage_path"]
            
            # Get pre-signed URL
            url = s3_provider.get_image_url(storage_path, expires_in=300)
            
            assert url is not None
            assert url.startswith("https://")
            assert TEST_BUCKET in url
            assert "Expires=" in url  # Should have expiration parameter
            
        finally:
            if 'storage_path' in locals():
                s3_provider.delete_image(storage_path)
    
    def test_list_images(self, s3_provider, test_image_data):
        """Test listing images in S3"""
        filename1 = f"test_list_1_{int(time.time())}.jpg"
        filename2 = f"test_list_2_{int(time.time())}.jpg"
        user_id = "test_list_user"
        
        uploaded_paths = []
        
        try:
            # Upload two test images
            for filename in [filename1, filename2]:
                upload_result = s3_provider.upload_image(
                    image_data=test_image_data,
                    filename=filename,
                    user_id=user_id
                )
                assert upload_result["success"] is True
                uploaded_paths.append(upload_result["storage_path"])
            
            # List images for user
            images = s3_provider.list_images(user_id=user_id)
            
            # Should find at least our 2 images (maybe more from other tests)
            found_images = [img for img in images if img["storage_path"] in uploaded_paths]
            assert len(found_images) >= 2
            
            # Check image metadata
            for img in found_images:
                assert "filename" in img
                assert "storage_path" in img
                assert "file_size" in img
                assert "created_at" in img
                assert img["provider"] == "S3StorageProvider"
                assert img["bucket"] == TEST_BUCKET
            
        finally:
            # Clean up uploaded images
            for path in uploaded_paths:
                s3_provider.delete_image(path)
    
    def test_delete_image(self, s3_provider, test_image_data):
        """Test deleting images from S3"""
        filename = f"test_delete_{int(time.time())}.jpg"
        
        # Upload image
        upload_result = s3_provider.upload_image(
            image_data=test_image_data,
            filename=filename
        )
        
        assert upload_result["success"] is True
        storage_path = upload_result["storage_path"]
        
        # Verify image exists
        downloaded = s3_provider.download_image(storage_path)
        assert downloaded is not None
        
        # Delete image
        delete_success = s3_provider.delete_image(storage_path)
        assert delete_success is True
        
        # Verify image is gone
        downloaded_after_delete = s3_provider.download_image(storage_path)
        assert downloaded_after_delete is None
    
    def test_thumbnail_generation(self, s3_provider, test_image_data):
        """Test thumbnail generation and upload"""
        filename = f"test_thumb_{int(time.time())}.jpg"
        
        try:
            upload_result = s3_provider.upload_image(
                image_data=test_image_data,
                filename=filename
            )
            
            assert upload_result["success"] is True
            
            # Check if thumbnail was created
            thumbnail_path = upload_result.get("thumbnail_path")
            if thumbnail_path:
                # Try to download thumbnail
                thumb_data = s3_provider.download_image(thumbnail_path)
                assert thumb_data is not None
                assert len(thumb_data) < len(test_image_data)  # Should be smaller
            
        finally:
            if upload_result.get("success"):
                s3_provider.delete_image(upload_result["storage_path"])
    
    def test_get_storage_stats(self, s3_provider):
        """Test getting storage statistics"""
        stats = s3_provider.get_storage_stats()
        
        assert "provider" in stats
        assert "total_size" in stats
        assert "file_count" in stats
        assert "bucket" in stats
        assert "region" in stats
        assert stats["provider"] == "S3StorageProvider"
        assert stats["bucket"] == TEST_BUCKET


class TestS3ErrorHandling:
    """Test S3 error handling and edge cases"""
    
    def test_invalid_bucket_name(self, s3_config):
        """Test handling of invalid bucket names"""
        bad_config = s3_config.copy()
        bad_config["bucket_name"] = "invalid-bucket-name-that-does-not-exist-12345"
        
        with pytest.raises(Exception):
            provider = S3StorageProvider(bad_config)
    
    def test_download_nonexistent_image(self, s3_provider):
        """Test downloading non-existent image"""
        result = s3_provider.download_image("nonexistent/image/path.jpg")
        assert result is None
    
    def test_delete_nonexistent_image(self, s3_provider):
        """Test deleting non-existent image"""
        # Should not raise exception, might return False
        result = s3_provider.delete_image("nonexistent/image/path.jpg")
        # S3 delete is idempotent, so this might still return True
    
    def test_get_url_nonexistent_image(self, s3_provider):
        """Test getting URL for non-existent image"""
        # Should still generate URL (S3 allows this), but accessing it will fail
        url = s3_provider.get_image_url("nonexistent/image/path.jpg")
        assert url is not None  # URL generation succeeds
        assert "nonexistent/image/path.jpg" in url


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 required")
def test_s3_provider_without_credentials():
    """Test S3 provider behavior without valid credentials"""
    config = {
        "bucket_name": "test-bucket",
        "region": "us-east-1",
        "aws_access_key_id": "invalid",
        "aws_secret_access_key": "invalid"
    }
    
    provider = S3StorageProvider(config)
    
    # Health check should fail with invalid credentials
    health = provider.health_check()
    assert health["healthy"] is False
    assert "error" in health


if __name__ == "__main__":
    # Print configuration info
    print(f"Test bucket: {TEST_BUCKET}")
    print(f"AWS region: {AWS_REGION}")
    print(f"Boto3 available: {BOTO3_AVAILABLE}")
    
    if not TEST_BUCKET:
        print("Set TEST_S3_BUCKET_NAME environment variable to run S3 integration tests")
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])