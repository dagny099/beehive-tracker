"""
Tests for URL Bulk Import Reference Template.

These tests verify that the URL template follows the consistency contract
and demonstrates proper implementation patterns for network operations.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import io
import requests

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from bulk_import.url_bulk_importer import URLBulkImporter, create_url_bulk_importer
from bulk_import import PhotoMetadata, GroupingStrategy


def create_test_image_bytes():
    """Create minimal JPEG bytes for testing"""
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


@pytest.fixture
def url_config():
    """Basic URL configuration for testing"""
    return {
        'urls': [
            'https://example.com/photo1.jpg',
            'https://example.com/photo2.jpg'
        ],
        'timeout': 10,
        'max_retries': 2,
        'grouping_strategy': 'date'
    }


@pytest.fixture
def mock_requests():
    """Mock requests for testing"""
    with patch('requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock successful HEAD response
        mock_head_response = MagicMock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': '1024000'
        }
        mock_head_response.raise_for_status.return_value = None
        mock_session.head.return_value = mock_head_response

        # Mock successful GET response for connectivity test
        mock_connectivity_response = MagicMock()
        mock_connectivity_response.status_code = 200
        mock_session.head.return_value = mock_connectivity_response

        # Mock successful GET response for download
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.headers = {'content-type': 'image/jpeg'}
        mock_get_response.raise_for_status.return_value = None

        # Mock iter_content for streaming download
        test_image_data = create_test_image_bytes()
        chunks = [test_image_data[i:i+1024] for i in range(0, len(test_image_data), 1024)]
        mock_get_response.iter_content.return_value = chunks
        mock_session.get.return_value = mock_get_response

        yield mock_session


class TestURLBulkImporter:
    """Test URL bulk importer implementation"""

    def test_initialization_success(self, url_config, mock_requests):
        """Test successful initialization with valid config"""
        importer = URLBulkImporter(url_config)

        assert importer.timeout == 10
        assert importer.max_retries == 2
        assert importer.grouping_strategy == GroupingStrategy.BY_DATE
        assert importer.verify_ssl is True

    def test_initialization_defaults(self, mock_requests):
        """Test initialization with default values"""
        config = {}
        importer = URLBulkImporter(config)

        assert importer.timeout == 30
        assert importer.max_retries == 3
        assert importer.user_agent.startswith('BeehiveTracker')

    def test_validate_source_success(self, url_config, mock_requests):
        """Test successful source validation"""
        importer = URLBulkImporter(url_config)

        result = importer.validate_source()
        assert result is True

    def test_validate_source_network_failure(self, url_config):
        """Test source validation with network failure"""
        with patch('requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_session.head.side_effect = requests.exceptions.ConnectionError("Network error")

            importer = URLBulkImporter(url_config)
            result = importer.validate_source()

            assert result is False

    def test_extract_photo_metadata_success(self, url_config, mock_requests):
        """Test successful metadata extraction"""
        importer = URLBulkImporter(url_config)

        metadata = importer.extract_photo_metadata('https://example.com/test-photo.jpg')

        # Verify metadata structure follows contract
        assert isinstance(metadata, PhotoMetadata)
        assert metadata.filename == 'test-photo.jpg'
        assert metadata.original_path == 'https://example.com/test-photo.jpg'
        assert metadata.source_type == 'url'
        assert metadata.file_size > 0
        assert isinstance(metadata.processed_at, datetime)

    def test_extract_photo_metadata_empty_url(self, url_config, mock_requests):
        """Test metadata extraction fails with empty URL"""
        importer = URLBulkImporter(url_config)

        with pytest.raises(ValueError, match="URL cannot be empty"):
            importer.extract_photo_metadata('')

    def test_extract_photo_metadata_invalid_url(self, url_config, mock_requests):
        """Test metadata extraction fails with invalid URL"""
        importer = URLBulkImporter(url_config)

        with pytest.raises(ValueError, match="Invalid URL format"):
            importer.extract_photo_metadata('not-a-url')

    def test_extract_photo_metadata_unsupported_scheme(self, url_config, mock_requests):
        """Test metadata extraction fails with unsupported scheme"""
        importer = URLBulkImporter(url_config)

        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            importer.extract_photo_metadata('ftp://example.com/photo.jpg')

    def test_extract_photo_metadata_unsupported_content_type(self, url_config):
        """Test metadata extraction fails with unsupported content type"""
        with patch('requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # Mock HEAD response with unsupported content type
            mock_head_response = MagicMock()
            mock_head_response.headers = {'content-type': 'text/html'}
            mock_head_response.raise_for_status.return_value = None
            mock_session.head.return_value = mock_head_response

            importer = URLBulkImporter(url_config)

            with pytest.raises(ValueError, match="Unsupported content type"):
                importer.extract_photo_metadata('https://example.com/document.html')

    def test_extract_filename_from_url(self, url_config, mock_requests):
        """Test filename extraction from various URL formats"""
        importer = URLBulkImporter(url_config)

        # Test normal filename
        filename = importer._extract_filename_from_url('https://example.com/photos/hive1.jpg')
        assert filename == 'hive1.jpg'

        # Test URL without extension - should generate fallback
        filename = importer._extract_filename_from_url('https://example.com/api/photo')
        assert 'example.com' in filename
        assert filename.endswith('.jpg')

    def test_group_into_inspections_by_date(self, url_config, mock_requests):
        """Test inspection grouping by date"""
        importer = URLBulkImporter(url_config)

        # Create test photos from different dates
        photos = [
            PhotoMetadata(
                filename="photo1.jpg",
                original_path="https://example.com/photo1.jpg",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="url",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="photo2.jpg",
                original_path="https://example.com/photo2.jpg",
                file_size=2048,
                created_at=datetime(2023, 6, 15, 11, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 11, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="url",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="photo3.jpg",
                original_path="https://example.com/photo3.jpg",
                file_size=1536,
                created_at=datetime(2023, 6, 16, 9, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 16, 9, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="url",
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

    def test_is_valid_url(self, url_config, mock_requests):
        """Test URL validation"""
        importer = URLBulkImporter(url_config)

        # Valid URLs
        assert importer._is_valid_url('https://example.com/photo.jpg') is True
        assert importer._is_valid_url('http://example.com/photo.jpg') is True

        # Invalid URLs
        assert importer._is_valid_url('not-a-url') is False
        assert importer._is_valid_url('') is False
        assert importer._is_valid_url('://missing-scheme') is False

    def test_factory_function(self, mock_requests):
        """Test factory function creates properly configured importer"""
        urls = ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg']

        importer = create_url_bulk_importer(
            urls=urls,
            max_workers=5,
            timeout=60
        )

        assert importer.config['urls'] == urls
        assert importer.max_workers == 5
        assert importer.timeout == 60
        assert importer.grouping_strategy == GroupingStrategy.BY_DATE


class TestURLTemplateConsistency:
    """Test that URL template follows consistency contract"""

    def test_metadata_extraction_consistency(self, url_config, mock_requests):
        """Test that URL metadata extraction is consistent"""
        importer1 = URLBulkImporter(url_config)
        importer2 = URLBulkImporter(url_config)

        test_url = 'https://example.com/test.jpg'

        # Extract metadata with both importers
        metadata1 = importer1.extract_photo_metadata(test_url)
        metadata2 = importer2.extract_photo_metadata(test_url)

        # Critical fields should be identical
        assert metadata1.filename == metadata2.filename
        assert metadata1.file_size == metadata2.file_size
        assert metadata1.source_type == metadata2.source_type
        assert metadata1.original_path == metadata2.original_path
        # Note: processed_at will differ, which is expected

    def test_grouping_consistency(self, url_config, mock_requests):
        """Test that grouping logic is consistent"""
        importer1 = URLBulkImporter(url_config)
        importer2 = URLBulkImporter(url_config)

        # Create identical photo sets
        photos = [
            PhotoMetadata(
                filename="photo1.jpg",
                original_path="https://example.com/photo1.jpg",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="url",
                processed_at=datetime.now()
            )
        ]

        groups1 = importer1.group_into_inspections(photos.copy())
        groups2 = importer2.group_into_inspections(photos.copy())

        # Should produce identical grouping
        assert len(groups1) == len(groups2)
        assert len(groups1[0].photos) == len(groups2[0].photos)
        assert groups1[0].grouping_criteria == groups2[0].grouping_criteria

    def test_cross_template_consistency_all_three(self, url_config, mock_requests):
        """Test consistency across all three templates (S3, Local, URL)"""
        from bulk_import.s3_bulk_importer import S3BulkImporter
        from bulk_import.local_bulk_importer import LocalBulkImporter
        import tempfile

        # Create URL importer
        url_importer = URLBulkImporter(url_config)

        # Create S3 importer with mocked client
        s3_config = {'bucket_name': 'test-bucket', 'grouping_strategy': 'date'}
        with patch('boto3.client') as mock_client:
            mock_s3 = mock_client.return_value
            mock_s3.head_bucket.return_value = {}
            s3_importer = S3BulkImporter(s3_config)

        # Create Local importer
        with tempfile.TemporaryDirectory() as temp_dir:
            local_config = {'base_path': temp_dir, 'grouping_strategy': 'date'}
            local_importer = LocalBulkImporter(local_config)

            # Test identical photos produce identical grouping across all templates
            photos = [
                PhotoMetadata(
                    filename="photo1.jpg",
                    original_path="test://photo1.jpg",  # Source-agnostic
                    file_size=1024,
                    created_at=datetime(2023, 6, 15, 10, 0, 0),
                    exif_data={},
                    timestamp=datetime(2023, 6, 15, 10, 0, 0),
                    gps_coordinates=None,
                    camera_make=None,
                    camera_model=None,
                    colors=[],
                    vision_analysis={},
                    source_type="test",  # Source-agnostic
                    processed_at=datetime.now()
                )
            ]

            url_groups = url_importer.group_into_inspections(photos.copy())
            s3_groups = s3_importer.group_into_inspections(photos.copy())
            local_groups = local_importer.group_into_inspections(photos.copy())

            # All templates should produce identical grouping
            assert len(url_groups) == len(s3_groups) == len(local_groups)
            assert url_groups[0].grouping_criteria == s3_groups[0].grouping_criteria == local_groups[0].grouping_criteria
            assert len(url_groups[0].photos) == len(s3_groups[0].photos) == len(local_groups[0].photos)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])