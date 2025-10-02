"""
Template Consistency Tests for Bulk Import System.

These tests enforce the core principle: IDENTICAL behavior across all import sources.
Any template that fails these tests violates the consistency contract and must be fixed.

Test Categories:
1. Metadata Extraction Consistency: Same photo → same metadata
2. Grouping Logic Consistency: Same photos → same inspection groups
3. Error Handling Consistency: Same errors → same error responses
4. Performance Baseline: All templates meet minimum performance standards

Following TDD principles, these tests define expected behavior BEFORE implementation.
"""

import pytest
import os
import tempfile
import io
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import Mock, patch

# Import the contract and test utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from bulk_import import (
    PhotoMetadata, BulkImportTemplate, InspectionGroup, GroupingStrategy,
    verify_template_consistency, TemplateConsistencyError
)


class MockBulkImporter(BulkImportTemplate):
    """Mock implementation for testing the base contract"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mock_metadata = None
        self.mock_groups = None
        self.validation_result = True

    def extract_photo_metadata(self, source_identifier) -> PhotoMetadata:
        if self.mock_metadata:
            return self.mock_metadata

        # Return consistent test metadata
        return PhotoMetadata(
            filename="test_image.jpg",
            original_path=source_identifier,
            file_size=1024000,
            created_at=datetime(2023, 6, 15, 10, 30, 0),
            exif_data={"Make": "TestCamera", "Model": "TestModel"},
            timestamp=datetime(2023, 6, 15, 10, 30, 0),
            gps_coordinates=(40.7128, -74.0060),  # NYC coordinates
            camera_make="TestCamera",
            camera_model="TestModel",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            vision_analysis={"labels": [{"description": "bee", "score": 0.95}]},
            source_type="mock",
            processed_at=datetime.now()
        )

    def group_into_inspections(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        if self.mock_groups:
            return self.mock_groups

        # Group by date (default strategy)
        groups = {}
        for photo in photos:
            date_key = photo.timestamp.date() if photo.timestamp else photo.created_at.date()
            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(photo)

        # Convert to InspectionGroup objects
        inspection_groups = []
        for date_key, group_photos in groups.items():
            group = InspectionGroup(
                inspection_date=datetime.combine(date_key, datetime.min.time()),
                location={"name": "Test Location", "lat": 40.7128, "lon": -74.0060},
                photos=group_photos,
                grouping_criteria=GroupingStrategy.BY_DATE,
                confidence_score=0.9
            )
            inspection_groups.append(group)

        return inspection_groups

    def validate_source(self) -> bool:
        return self.validation_result


@pytest.fixture
def sample_test_image():
    """Create a minimal valid JPEG for testing"""
    # Create a simple 1x1 pixel JPEG in memory
    from PIL import Image

    img = Image.new('RGB', (1, 1), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


@pytest.fixture
def mock_templates():
    """Create mock templates for consistency testing"""
    template1 = MockBulkImporter({"grouping_strategy": "date"})
    template2 = MockBulkImporter({"grouping_strategy": "date"})
    return template1, template2


class TestTemplateConsistency:
    """Core consistency tests that ALL templates must pass"""

    def test_identical_metadata_extraction(self, mock_templates, sample_test_image):
        """CRITICAL: Same photo from different sources produces identical metadata"""
        template1, template2 = mock_templates

        # Both templates should extract identical metadata
        metadata1 = template1.extract_photo_metadata("test_source_1")
        metadata2 = template2.extract_photo_metadata("test_source_2")

        # Compare critical fields (ignore source-specific fields)
        assert metadata1.filename == metadata2.filename
        assert metadata1.file_size == metadata2.file_size
        assert metadata1.timestamp == metadata2.timestamp
        assert metadata1.gps_coordinates == metadata2.gps_coordinates
        assert metadata1.camera_make == metadata2.camera_make
        assert metadata1.camera_model == metadata2.camera_model
        assert metadata1.colors == metadata2.colors

        # Vision analysis should be identical
        assert metadata1.vision_analysis == metadata2.vision_analysis

    def test_consistent_inspection_grouping(self, mock_templates):
        """CRITICAL: Same photo set produces identical inspection groups"""
        template1, template2 = mock_templates

        # Create identical photo metadata lists
        photos = [
            template1.extract_photo_metadata("photo1"),
            template1.extract_photo_metadata("photo2"),
            template1.extract_photo_metadata("photo3")
        ]

        # Both templates should group identically
        groups1 = template1.group_into_inspections(photos.copy())
        groups2 = template2.group_into_inspections(photos.copy())

        assert len(groups1) == len(groups2)

        for group1, group2 in zip(groups1, groups2):
            assert group1.inspection_date == group2.inspection_date
            assert len(group1.photos) == len(group2.photos)
            assert group1.grouping_criteria == group2.grouping_criteria

    def test_verify_template_consistency_function(self, mock_templates, sample_test_image):
        """Test the consistency verification utility function"""
        template1, template2 = mock_templates

        # Should pass for identical templates
        result = verify_template_consistency(
            template1, template2, sample_test_image, "test_identifier"
        )
        assert result is True

    def test_consistency_error_detection(self, mock_templates, sample_test_image):
        """Test that inconsistencies are properly detected"""
        template1, template2 = mock_templates

        # Make template2 return different metadata
        different_metadata = PhotoMetadata(
            filename="different_image.jpg",  # Different filename
            original_path="test_source",
            file_size=2048000,  # Different size
            created_at=datetime(2023, 6, 15, 10, 30, 0),
            exif_data={},
            timestamp=datetime(2023, 6, 15, 10, 30, 0),
            gps_coordinates=None,  # Different GPS
            camera_make="DifferentCamera",  # Different camera
            camera_model="DifferentModel",
            colors=["#000000"],  # Different colors
            vision_analysis={},
            source_type="mock",
            processed_at=datetime.now()
        )
        template2.mock_metadata = different_metadata

        # Should raise TemplateConsistencyError
        with pytest.raises(TemplateConsistencyError):
            verify_template_consistency(
                template1, template2, sample_test_image, "test_identifier"
            )


class TestGroupingStrategies:
    """Test consistency of different grouping strategies"""

    def test_date_grouping_consistency(self, mock_templates):
        """Test that date-based grouping is consistent across templates"""
        template1, template2 = mock_templates

        # Create photos from different dates
        photos = []
        for i, day in enumerate([15, 15, 16, 16, 17]):  # 3 different days
            metadata = PhotoMetadata(
                filename=f"photo_{i}.jpg",
                original_path=f"source_{i}",
                file_size=1024000,
                created_at=datetime(2023, 6, day, 10, 30, 0),
                exif_data={},
                timestamp=datetime(2023, 6, day, 10, 30, 0),
                gps_coordinates=(40.7128, -74.0060),
                camera_make="TestCamera",
                camera_model="TestModel",
                colors=["#FF0000"],
                vision_analysis={},
                source_type="test",
                processed_at=datetime.now()
            )
            photos.append(metadata)

        # Both templates should create same number of groups
        groups1 = template1.group_into_inspections(photos)
        groups2 = template2.group_into_inspections(photos)

        assert len(groups1) == len(groups2) == 3  # 3 different days

        # Groups should have same photo counts
        counts1 = sorted([len(g.photos) for g in groups1])
        counts2 = sorted([len(g.photos) for g in groups2])
        assert counts1 == counts2 == [1, 2, 2]  # 1+2+2 = 5 photos

    def test_location_grouping_consistency(self):
        """Test location-based grouping (when implemented)"""
        # TODO: Implement when location grouping is added
        pass


class TestErrorHandling:
    """Test consistent error handling across templates"""

    def test_invalid_source_handling(self, mock_templates):
        """Test that invalid sources are handled consistently"""
        template1, template2 = mock_templates

        # Both should raise ValueError for invalid sources
        with pytest.raises(ValueError):
            template1.extract_photo_metadata("")  # Empty string

        with pytest.raises(ValueError):
            template2.extract_photo_metadata("")  # Empty string

    def test_validation_failure_handling(self, mock_templates):
        """Test source validation failure handling"""
        template1, template2 = mock_templates

        # Make validation fail
        template1.validation_result = False
        template2.validation_result = False

        # Both should return unsuccessful results
        result1 = template1.process_bulk_import(["test_source"])
        result2 = template2.process_bulk_import(["test_source"])

        assert result1.success is False
        assert result2.success is False
        assert "validation failed" in result1.errors[0].lower()
        assert "validation failed" in result2.errors[0].lower()


class TestPerformanceBaseline:
    """Test that all templates meet minimum performance standards"""

    def test_metadata_extraction_performance(self, mock_templates):
        """Test that metadata extraction completes within reasonable time"""
        template1, template2 = mock_templates

        import time

        # Test single photo extraction speed
        start_time = time.time()
        template1.extract_photo_metadata("test_source")
        extraction_time = time.time() - start_time

        # Should complete within 1 second for mock implementation
        assert extraction_time < 1.0

    def test_bulk_processing_performance(self, mock_templates):
        """Test bulk processing performance with reasonable dataset"""
        template1, _ = mock_templates

        # Process 10 photos (reasonable test size)
        sources = [f"test_source_{i}" for i in range(10)]

        import time
        start_time = time.time()
        result = template1.process_bulk_import(sources)
        processing_time = time.time() - start_time

        # Should complete within 5 seconds for 10 photos
        assert processing_time < 5.0
        assert result.success is True
        assert result.valid_photos == 10


class TestDataValidation:
    """Test data validation and integrity checks"""

    def test_photo_metadata_validation(self):
        """Test PhotoMetadata validation in __post_init__"""
        # Valid metadata should not raise
        valid_metadata = PhotoMetadata(
            filename="test.jpg",
            original_path="/test/path",
            file_size=1024,
            created_at=datetime.now(),
            exif_data={},
            timestamp=None,
            gps_coordinates=None,
            camera_make=None,
            camera_model=None,
            colors=[],
            vision_analysis={},
            source_type="test",
            processed_at=datetime.now()
        )
        assert valid_metadata.filename == "test.jpg"

        # Invalid metadata should raise ValueError
        with pytest.raises(ValueError, match="filename cannot be empty"):
            PhotoMetadata(
                filename="",  # Invalid: empty filename
                original_path="/test/path",
                file_size=1024,
                created_at=datetime.now(),
                exif_data={},
                timestamp=None,
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="test",
                processed_at=datetime.now()
            )

        with pytest.raises(ValueError, match="file_size must be non-negative"):
            PhotoMetadata(
                filename="test.jpg",
                original_path="/test/path",
                file_size=-1,  # Invalid: negative size
                created_at=datetime.now(),
                exif_data={},
                timestamp=None,
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="test",
                processed_at=datetime.now()
            )

    def test_inspection_group_validation(self):
        """Test InspectionGroup calculation of derived properties"""
        photos = [
            PhotoMetadata(
                filename="test1.jpg",
                original_path="/test/path1",
                file_size=1024,
                created_at=datetime(2023, 6, 15, 10, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 10, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="test",
                processed_at=datetime.now()
            ),
            PhotoMetadata(
                filename="test2.jpg",
                original_path="/test/path2",
                file_size=2048,
                created_at=datetime(2023, 6, 15, 11, 0, 0),
                exif_data={},
                timestamp=datetime(2023, 6, 15, 11, 0, 0),
                gps_coordinates=None,
                camera_make=None,
                camera_model=None,
                colors=[],
                vision_analysis={},
                source_type="test",
                processed_at=datetime.now()
            )
        ]

        group = InspectionGroup(
            inspection_date=datetime(2023, 6, 15, 10, 30, 0),
            location=None,
            photos=photos,
            grouping_criteria=GroupingStrategy.BY_DATE,
            confidence_score=0.9
        )

        # Test derived properties
        assert group.photo_count == 2
        assert group.date_range == (
            datetime(2023, 6, 15, 10, 0, 0),
            datetime(2023, 6, 15, 11, 0, 0)
        )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])