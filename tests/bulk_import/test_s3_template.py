"""
Tests for S3 Bulk Import Reference Template.

These tests verify that the S3 template follows the consistency contract
and demonstrates proper implementation patterns.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import io

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from bulk_import.s3_bulk_importer import S3BulkImporter, create_s3_bulk_importer
from bulk_import import PhotoMetadata, GroupingStrategy


@pytest.fixture
def s3_config():
    """Basic S3 configuration for testing"""
    return {
        'bucket_name': 'test-beehive-bucket',
        'region': 'us-east-1',
        'prefix_filter': 'hive-photos/',
        'grouping_strategy': 'date'
    }


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing"""
    with patch('boto3.client') as mock_boto3_client:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock successful bucket access
        mock_client.head_bucket.return_value = {}

        # Mock object listing
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'hive-photos/photo1.jpg', 'LastModified': datetime.now(), 'Size': 1024000},
                {'Key': 'hive-photos/photo2.jpg', 'LastModified': datetime.now(), 'Size': 2048000}
            ]
        }

        # Mock object head
        mock_client.head_object.return_value = {
            'ContentLength': 1024000,
            'LastModified': datetime.now()
        }

        # Mock object get
        mock_image_data = create_test_image_bytes()
        mock_client.get_object.return_value = {
            'Body': Mock(read=Mock(return_value=mock_image_data))
        }

        yield mock_client


def create_test_image_bytes():
    """Create minimal JPEG bytes for testing"""
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


class TestS3BulkImporter:
    """Test S3 bulk importer implementation"""

    def test_initialization_success(self, s3_config, mock_s3_client):
        """Test successful initialization with valid config"""
        importer = S3BulkImporter(s3_config)

        assert importer.bucket_name == 'test-beehive-bucket'
        assert importer.region == 'us-east-1'
        assert importer.prefix_filter == 'hive-photos/'
        assert importer.grouping_strategy == GroupingStrategy.BY_DATE

    def test_initialization_missing_bucket(self):
        """Test initialization fails with missing bucket name"""
        config = {'region': 'us-east-1'}

        with pytest.raises(ValueError, match="bucket_name is required"):
            S3BulkImporter(config)

    @patch('bulk_import.s3_bulk_importer.BOTO3_AVAILABLE', False)
    def test_initialization_no_boto3(self, s3_config):
        """Test initialization fails when boto3 not available"""
        with pytest.raises(ImportError, match="boto3 is required"):
            S3BulkImporter(s3_config)

    def test_validate_source_success(self, s3_config, mock_s3_client):
        """Test successful source validation"""
        importer = S3BulkImporter(s3_config)

        result = importer.validate_source()
        assert result is True

        # Verify S3 calls were made
        mock_s3_client.head_bucket.assert_called_with(Bucket='test-beehive-bucket')
        mock_s3_client.list_objects_v2.assert_called()

    def test_validate_source_no_objects(self, s3_config, mock_s3_client):
        """Test source validation with no objects"""
        mock_s3_client.list_objects_v2.return_value = {}  # No Contents

        importer = S3BulkImporter(s3_config)
        result = importer.validate_source()

        assert result is False

    def test_extract_photo_metadata_success(self, s3_config, mock_s3_client):
        """Test successful metadata extraction"""
        importer = S3BulkImporter(s3_config)

        metadata = importer.extract_photo_metadata('hive-photos/test-photo.jpg')

        # Verify metadata structure follows contract
        assert isinstance(metadata, PhotoMetadata)
        assert metadata.filename == 'test-photo.jpg'
        assert metadata.original_path == 's3://test-beehive-bucket/hive-photos/test-photo.jpg'
        assert metadata.source_type == 's3'
        assert metadata.file_size > 0
        assert isinstance(metadata.processed_at, datetime)

    def test_extract_photo_metadata_empty_key(self, s3_config, mock_s3_client):
        """Test metadata extraction fails with empty key"""
        importer = S3BulkImporter(s3_config)

        with pytest.raises(ValueError, match="S3 object key cannot be empty"):
            importer.extract_photo_metadata('')

    def test_extract_photo_metadata_unsupported_type(self, s3_config, mock_s3_client):
        """Test metadata extraction fails with unsupported file type"""
        importer = S3BulkImporter(s3_config)

        with pytest.raises(ValueError, match="Unsupported file type"):
            importer.extract_photo_metadata('hive-photos/document.pdf')

    def test_group_into_inspections_by_date(self, s3_config, mock_s3_client):
        """Test inspection grouping by date"""
        importer = S3BulkImporter(s3_config)

        # Create test photos from different dates
        photos = [
            PhotoMetadata(
                filename="photo1.jpg",
                original_path="s3://bucket/photo1.jpg",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="s3",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="photo2.jpg",
                original_path="s3://bucket/photo2.jpg",
                file_size=2048,
                created_at=datetime(2023, 6, 15, 11, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 11, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="s3",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="photo3.jpg",
                original_path="s3://bucket/photo3.jpg",
                file_size=1536,
                created_at=datetime(2023, 6, 16, 9, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 16, 9, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="s3",
                processed_at=datetime.now()
            )
        ]

        groups = importer.group_into_inspections(photos)

        # Should create 2 groups (2 different dates)
        assert len(groups) == 2

        # First group should have 2 photos (same date)
        assert len(groups[0].photos) == 2
        assert groups[0].grouping_criteria == GroupingStrategy.BY_DATE

        # Second group should have 1 photo
        assert len(groups[1].photos) == 1

    def test_list_available_photos(self, s3_config, mock_s3_client):
        """Test listing available photos with filtering"""
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'hive-photos/photo1.jpg'},
                {'Key': 'hive-photos/document.pdf'},  # Should be filtered out
                {'Key': 'hive-photos/photo2.JPG'},
                {'Key': 'hive-photos/photo3.png'},
            ]
        }

        importer = S3BulkImporter(s3_config)
        photo_keys = importer.list_available_photos()

        # Should only return image files
        assert len(photo_keys) == 3
        assert 'hive-photos/photo1.jpg' in photo_keys
        assert 'hive-photos/photo2.JPG' in photo_keys
        assert 'hive-photos/photo3.png' in photo_keys
        assert 'hive-photos/document.pdf' not in photo_keys

    def test_factory_function(self):
        """Test factory function creates properly configured importer"""
        with patch('boto3.client'):
            importer = create_s3_bulk_importer(
                bucket_name='test-bucket',
                aws_access_key_id='test-key',
                aws_secret_access_key='test-secret',
                max_workers=10
            )

            assert importer.bucket_name == 'test-bucket'
            assert importer.max_workers == 10
            assert importer.config['aws_access_key_id'] == 'test-key'


class TestS3TemplateConsistency:
    """Test that S3 template follows consistency contract"""

    def test_metadata_extraction_consistency(self, s3_config, mock_s3_client):
        """Test that S3 metadata extraction is consistent"""
        importer1 = S3BulkImporter(s3_config)
        importer2 = S3BulkImporter(s3_config)

        # Extract metadata for same object
        metadata1 = importer1.extract_photo_metadata('hive-photos/test.jpg')
        metadata2 = importer2.extract_photo_metadata('hive-photos/test.jpg')

        # Critical fields should be identical
        assert metadata1.filename == metadata2.filename
        assert metadata1.file_size == metadata2.file_size
        assert metadata1.source_type == metadata2.source_type
        # Note: processed_at will differ, which is expected

    def test_grouping_consistency(self, s3_config, mock_s3_client):
        """Test that grouping logic is consistent"""
        importer1 = S3BulkImporter(s3_config)
        importer2 = S3BulkImporter(s3_config)

        # Create identical photo sets
        photos = [
            PhotoMetadata(
                filename="photo1.jpg",
                original_path="s3://bucket/photo1.jpg",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="s3",
                processed_at=datetime.now()
            )
        ]

        groups1 = importer1.group_into_inspections(photos.copy())
        groups2 = importer2.group_into_inspections(photos.copy())

        # Should produce identical grouping
        assert len(groups1) == len(groups2)
        assert len(groups1[0].photos) == len(groups2[0].photos)
        assert groups1[0].grouping_criteria == groups2[0].grouping_criteria


if __name__ == "__main__":
    pytest.main([__file__, "-v"])