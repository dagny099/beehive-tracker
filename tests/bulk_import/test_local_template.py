"""
Tests for Local Bulk Import Reference Template.

These tests verify that the Local template follows the consistency contract
and demonstrates proper implementation patterns for file system operations.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
import io

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from bulk_import.local_bulk_importer import LocalBulkImporter, create_local_bulk_importer
from bulk_import import PhotoMetadata, GroupingStrategy


def create_test_image_file(path: Path) -> None:
    """Create a minimal test image file"""
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(path, format='JPEG')


@pytest.fixture
def temp_photo_dir():
    """Create temporary directory with test photos"""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create test directory structure
        (temp_dir / "subdir1").mkdir()
        (temp_dir / "subdir2").mkdir()
        (temp_dir / ".hidden_dir").mkdir()

        # Create test image files
        create_test_image_file(temp_dir / "photo1.jpg")
        create_test_image_file(temp_dir / "photo2.JPG")
        create_test_image_file(temp_dir / "subdir1" / "photo3.png")
        create_test_image_file(temp_dir / "subdir2" / "photo4.jpeg")

        # Create non-image files (should be filtered out)
        (temp_dir / "document.pdf").write_text("not an image")
        (temp_dir / "readme.txt").write_text("text file")
        (temp_dir / ".hidden_dir" / "hidden_photo.jpg").write_text("hidden")

        yield temp_dir

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


@pytest.fixture
def local_config(temp_photo_dir):
    """Basic local configuration for testing"""
    return {
        'base_path': str(temp_photo_dir),
        'recursive': True,
        'max_depth': 10,
        'grouping_strategy': 'date'
    }


class TestLocalBulkImporter:
    """Test local bulk importer implementation"""

    def test_initialization_success(self, local_config):
        """Test successful initialization with valid config"""
        importer = LocalBulkImporter(local_config)

        assert importer.base_path == Path(local_config['base_path'])
        assert importer.recursive is True
        assert importer.max_depth == 10
        assert importer.grouping_strategy == GroupingStrategy.BY_DATE

    def test_initialization_nonexistent_path(self):
        """Test initialization fails with nonexistent path"""
        config = {'base_path': '/nonexistent/path'}

        with pytest.raises(ValueError, match="Base path does not exist"):
            LocalBulkImporter(config)

    def test_initialization_file_not_directory(self, temp_photo_dir):
        """Test initialization fails when base_path is a file"""
        test_file = temp_photo_dir / "test.txt"
        test_file.write_text("test")

        config = {'base_path': str(test_file)}

        with pytest.raises(ValueError, match="Base path is not a directory"):
            LocalBulkImporter(config)

    def test_validate_source_success(self, local_config):
        """Test successful source validation"""
        importer = LocalBulkImporter(local_config)

        result = importer.validate_source()
        assert result is True

    def test_validate_source_empty_directory(self):
        """Test source validation with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'base_path': temp_dir}
            importer = LocalBulkImporter(config)

            result = importer.validate_source()
            assert result is False

    def test_discover_photos_recursive(self, local_config):
        """Test photo discovery with recursive scanning"""
        importer = LocalBulkImporter(local_config)

        photos = importer.discover_photos()

        # Should find 4 image files (excluding hidden and non-image files)
        assert len(photos) == 4

        # Check that all found files are image files
        for photo_path in photos:
            path = Path(photo_path)
            assert path.suffix.lower() in ['.jpg', '.png', '.jpeg']
            assert path.exists()

    def test_discover_photos_non_recursive(self, local_config):
        """Test photo discovery without recursive scanning"""
        local_config['recursive'] = False
        importer = LocalBulkImporter(local_config)

        photos = importer.discover_photos()

        # Should only find 2 images in root directory
        assert len(photos) == 2

        # All photos should be in the base directory
        for photo_path in photos:
            path = Path(photo_path)
            assert path.parent == importer.base_path

    def test_extract_photo_metadata_success(self, local_config):
        """Test successful metadata extraction"""
        importer = LocalBulkImporter(local_config)

        # Get a photo file to test
        photos = importer.discover_photos()
        assert len(photos) > 0

        test_photo = photos[0]
        metadata = importer.extract_photo_metadata(test_photo)

        # Verify metadata structure follows contract
        assert isinstance(metadata, PhotoMetadata)
        assert metadata.filename == Path(test_photo).name
        assert metadata.source_type == "local"
        assert metadata.file_size > 0
        assert isinstance(metadata.processed_at, datetime)
        assert metadata.original_path.startswith("file://")

    def test_extract_photo_metadata_empty_path(self, local_config):
        """Test metadata extraction fails with empty path"""
        importer = LocalBulkImporter(local_config)

        with pytest.raises(ValueError, match="File path cannot be empty"):
            importer.extract_photo_metadata("")

    def test_extract_photo_metadata_nonexistent_file(self, local_config):
        """Test metadata extraction fails with nonexistent file"""
        importer = LocalBulkImporter(local_config)

        with pytest.raises(RuntimeError, match="File does not exist"):
            importer.extract_photo_metadata("/nonexistent/file.jpg")

    def test_exclude_patterns(self, local_config):
        """Test that exclude patterns work correctly"""
        importer = LocalBulkImporter(local_config)

        # Hidden directories should be excluded
        assert importer._should_exclude(".hidden_dir") is True
        assert importer._should_exclude("__pycache__") is True
        assert importer._should_exclude(".DS_Store") is True

        # Normal files should not be excluded
        assert importer._should_exclude("photo.jpg") is False
        assert importer._should_exclude("normal_dir") is False

    def test_group_into_inspections_by_date(self, local_config):
        """Test inspection grouping by date"""
        importer = LocalBulkImporter(local_config)

        # Create test photos from different dates
        photos = [
            PhotoMetadata(
                filename="photo1.jpg",
                original_path="file:///test/photo1.jpg",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="local",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="photo2.jpg",
                original_path="file:///test/photo2.jpg",
                file_size=2048,
                created_at=datetime(2023, 6, 15, 11, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 11, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="local",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="photo3.jpg",
                original_path="file:///test/photo3.jpg",
                file_size=1536,
                created_at=datetime(2023, 6, 16, 9, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 16, 9, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="local",
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

    def test_factory_function(self):
        """Test factory function creates properly configured importer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            importer = create_local_bulk_importer(
                base_path=temp_dir,
                max_workers=8,
                batch_size=50
            )

            assert str(importer.base_path) == temp_dir
            assert importer.max_workers == 8
            assert importer.batch_size == 50
            assert importer.recursive is True  # Default


class TestLocalTemplateConsistency:
    """Test that Local template follows consistency contract"""

    def test_metadata_extraction_consistency(self, local_config):
        """Test that Local metadata extraction is consistent"""
        importer1 = LocalBulkImporter(local_config)
        importer2 = LocalBulkImporter(local_config)

        # Get a test photo
        photos = importer1.discover_photos()
        if not photos:
            pytest.skip("No photos found for consistency test")

        test_photo = photos[0]

        # Extract metadata with both importers
        metadata1 = importer1.extract_photo_metadata(test_photo)
        metadata2 = importer2.extract_photo_metadata(test_photo)

        # Critical fields should be identical
        assert metadata1.filename == metadata2.filename
        assert metadata1.file_size == metadata2.file_size
        assert metadata1.source_type == metadata2.source_type
        assert metadata1.original_path == metadata2.original_path
        # Note: processed_at will differ, which is expected

    def test_grouping_consistency(self, local_config):
        """Test that grouping logic is consistent"""
        importer1 = LocalBulkImporter(local_config)
        importer2 = LocalBulkImporter(local_config)

        # Create identical photo sets
        photos = [
            PhotoMetadata(
                filename="photo1.jpg",
                original_path="file:///test/photo1.jpg",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="local",
                processed_at=datetime.now()
            )
        ]

        groups1 = importer1.group_into_inspections(photos.copy())
        groups2 = importer2.group_into_inspections(photos.copy())

        # Should produce identical grouping
        assert len(groups1) == len(groups2)
        assert len(groups1[0].photos) == len(groups2[0].photos)
        assert groups1[0].grouping_criteria == groups2[0].grouping_criteria

    def test_cross_template_consistency(self, local_config):
        """Test consistency between Local and S3 templates"""
        from bulk_import.s3_bulk_importer import S3BulkImporter
        from unittest.mock import MagicMock

        # Create local importer
        local_importer = LocalBulkImporter(local_config)

        # Create S3 importer with mocked client
        s3_config = {
            'bucket_name': 'test-bucket',
            'grouping_strategy': 'date'
        }

        with patch('boto3.client') as mock_client:
            mock_s3 = mock_client.return_value
            mock_s3.head_bucket.return_value = {}

            s3_importer = S3BulkImporter(s3_config)

            # Test identical photos produce identical grouping
            photos = [
                PhotoMetadata(
                    filename="photo1.jpg",
                    original_path="test://photo1.jpg",  # Source-specific
                    file_size=1024,
                    created_at=datetime(2023, 6, 15, 10, 0, 0),
                    exif_data={},
                    timestamp=datetime(2023, 6, 15, 10, 0, 0),
                    gps_coordinates=None,
                    camera_make=None,
                    camera_model=None,
                    colors=[],
                    vision_analysis={},
                    source_type="test",  # Source-specific
                    processed_at=datetime.now()
                )
            ]

            local_groups = local_importer.group_into_inspections(photos.copy())
            s3_groups = s3_importer.group_into_inspections(photos.copy())

            # Grouping logic should be identical
            assert len(local_groups) == len(s3_groups)
            assert local_groups[0].grouping_criteria == s3_groups[0].grouping_criteria
            assert len(local_groups[0].photos) == len(s3_groups[0].photos)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])