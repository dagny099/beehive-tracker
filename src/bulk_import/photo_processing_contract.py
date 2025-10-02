"""
Photo Processing Contract for Bulk Import Templates.

This module defines the standardized interfaces and data structures that ALL
bulk import implementations must follow to ensure consistency across different
import sources (S3, Local, URL).

Following Test-Driven Development principles, these contracts ensure:
- Identical behavior regardless of photo source
- Consistent metadata extraction formats
- Uniform inspection grouping logic
- Predictable error handling patterns
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GroupingStrategy(Enum):
    """Strategies for grouping photos into inspections"""
    BY_DATE = "date"           # Group photos by date (same day = same inspection)
    BY_LOCATION = "location"   # Group photos by GPS coordinates
    BY_MANUAL = "manual"       # User-defined grouping rules
    BY_HYBRID = "hybrid"       # Combine date + location + user rules


@dataclass
class PhotoMetadata:
    """
    Standardized photo metadata format - IDENTICAL across all import sources.

    This structure MUST be returned by all import templates to ensure consistency.
    Any deviation will break the Template Consistency Tests.
    """
    # Basic file information
    filename: str
    original_path: str         # Source-specific path (S3 key, file path, URL)
    file_size: int             # Size in bytes
    created_at: datetime       # When photo was created

    # EXIF data (standardized extraction)
    exif_data: Dict[str, Any]           # Raw EXIF data
    timestamp: Optional[datetime]        # Photo timestamp from EXIF
    gps_coordinates: Optional[Tuple[float, float]]  # (latitude, longitude)

    # Camera information
    camera_make: Optional[str]
    camera_model: Optional[str]

    # Processing results
    colors: List[str]                   # Extracted color palette
    vision_analysis: Dict[str, Any]     # Computer vision results

    # Import metadata
    source_type: str                    # "s3", "local", or "url"
    processed_at: datetime              # When this metadata was extracted

    def __post_init__(self):
        """Validate metadata consistency after creation"""
        if not self.filename:
            raise ValueError("filename cannot be empty")
        if self.file_size < 0:
            raise ValueError("file_size must be non-negative")


@dataclass
class InspectionGroup:
    """
    Grouped photos that form a single inspection.

    All import templates MUST use identical grouping logic to ensure
    the same photos produce the same inspection groups.
    """
    inspection_date: datetime
    location: Optional[Dict[str, Any]]   # Location data if available
    photos: List[PhotoMetadata]
    grouping_criteria: GroupingStrategy  # How photos were grouped
    confidence_score: float              # Confidence in grouping (0.0-1.0)

    # Derived properties
    photo_count: int = None
    date_range: Tuple[datetime, datetime] = None

    def __post_init__(self):
        """Calculate derived properties"""
        self.photo_count = len(self.photos)
        if self.photos:
            timestamps = [p.timestamp for p in self.photos if p.timestamp]
            if timestamps:
                self.date_range = (min(timestamps), max(timestamps))


@dataclass
class ProcessingResult:
    """Result of bulk import processing"""
    success: bool
    processed_photos: List[PhotoMetadata]
    inspection_groups: List[InspectionGroup]
    errors: List[str]
    warnings: List[str]

    # Statistics
    total_files_found: int = 0
    valid_photos: int = 0
    invalid_photos: int = 0
    processing_time_seconds: float = 0.0


class BulkImportTemplate(ABC):
    """
    Abstract Base Class defining the minimal contract for all bulk import templates.

    This enforces IDENTICAL outputs across all import sources while allowing
    implementation flexibility for source-specific optimizations.

    Key Principle: Same photo from different sources MUST produce identical PhotoMetadata
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize import template with configuration.

        Args:
            config: Source-specific configuration (S3 credentials, local paths, etc.)
        """
        self.config = config
        self.grouping_strategy = GroupingStrategy(config.get('grouping_strategy', 'date'))

    @abstractmethod
    def extract_photo_metadata(self, source_identifier: Union[str, bytes]) -> PhotoMetadata:
        """
        Extract standardized metadata from a photo source.

        CRITICAL: This method MUST return identical PhotoMetadata format
        regardless of source type. Template Consistency Tests verify this.

        Args:
            source_identifier: Source-specific identifier (S3 key, file path, URL)

        Returns:
            PhotoMetadata: Standardized metadata structure

        Raises:
            ValueError: If photo is invalid or cannot be processed
            RuntimeError: If source is inaccessible
        """
        pass

    @abstractmethod
    def group_into_inspections(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """
        Group photos into logical inspections using consistent logic.

        CRITICAL: This method MUST use identical grouping algorithms across
        all import sources. Same photos = same groups.

        Args:
            photos: List of processed photo metadata

        Returns:
            List[InspectionGroup]: Grouped inspections
        """
        pass

    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate that the import source is accessible and valid.

        Returns:
            bool: True if source is valid and accessible
        """
        pass

    def process_bulk_import(self,
                          source_list: List[str],
                          progress_callback: Optional[callable] = None) -> ProcessingResult:
        """
        Process multiple photos in bulk using the template pattern.

        This method provides the common workflow that all templates follow:
        1. Validate sources
        2. Extract metadata for each photo
        3. Group photos into inspections
        4. Return standardized results

        Args:
            source_list: List of source identifiers to process
            progress_callback: Optional callback for progress updates

        Returns:
            ProcessingResult: Complete processing results
        """
        start_time = datetime.now()
        result = ProcessingResult(
            success=False,
            processed_photos=[],
            inspection_groups=[],
            errors=[],
            warnings=[],
            total_files_found=len(source_list)
        )

        try:
            # Step 1: Validate source
            if not self.validate_source():
                result.errors.append("Source validation failed")
                return result

            # Step 2: Process each photo
            for idx, source_id in enumerate(source_list):
                try:
                    if progress_callback:
                        progress_callback(idx, len(source_list), f"Processing {source_id}")

                    metadata = self.extract_photo_metadata(source_id)
                    result.processed_photos.append(metadata)
                    result.valid_photos += 1

                except Exception as e:
                    result.errors.append(f"Failed to process {source_id}: {str(e)}")
                    result.invalid_photos += 1

            # Step 3: Group into inspections
            if result.processed_photos:
                result.inspection_groups = self.group_into_inspections(result.processed_photos)

            # Step 4: Calculate final stats
            result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            result.success = result.valid_photos > 0

            return result

        except Exception as e:
            result.errors.append(f"Bulk processing failed: {str(e)}")
            result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            return result

    def _extract_exif_data(self, image_data: bytes) -> Dict[str, Any]:
        """
        Common EXIF extraction logic used by all templates.

        This ensures identical EXIF processing across all import sources.
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            import io

            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))

            # Extract EXIF data
            exif_data = {}
            if hasattr(image, '_getexif') and image._getexif():
                for tag_id, value in image._getexif().items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            return exif_data

        except Exception as e:
            # Return empty dict on error - don't fail the entire import
            return {}

    def _extract_gps_coordinates(self, exif_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Common GPS extraction logic used by all templates.

        Ensures identical GPS coordinate processing across all import sources.
        """
        try:
            from utils.image_processor import get_image_gps_coordinates

            # Use existing GPS extraction logic for consistency
            gps_info = exif_data.get('GPSInfo', {})
            if gps_info:
                # Convert GPS info to decimal coordinates
                # This would use the existing GPS processing logic
                return get_image_gps_coordinates(gps_info)

        except Exception:
            pass

        return None

    def _extract_color_palette(self, image_data: bytes) -> List[str]:
        """
        Common color extraction logic used by all templates.

        Ensures identical color analysis across all import sources.
        """
        try:
            from utils.image_processor import extract_color_palette

            # Use existing color extraction for consistency
            return extract_color_palette(image_data)

        except Exception:
            # Return default colors on error
            return ["#CCCCCC", "#DDDDDD", "#EEEEEE"]


class TemplateConsistencyError(Exception):
    """Raised when templates produce inconsistent results for the same data"""
    pass


def verify_template_consistency(template1: BulkImportTemplate,
                              template2: BulkImportTemplate,
                              test_data: bytes,
                              test_identifier: str) -> bool:
    """
    Verify that two templates produce identical results for the same photo.

    This function is used in Template Consistency Tests to ensure all
    import sources behave identically.

    Args:
        template1: First template to test
        template2: Second template to test
        test_data: Same photo data for both templates
        test_identifier: Source identifier for the photo

    Returns:
        bool: True if templates produce identical results

    Raises:
        TemplateConsistencyError: If templates produce different results
    """
    try:
        # Extract metadata using both templates
        metadata1 = template1.extract_photo_metadata(test_identifier)
        metadata2 = template2.extract_photo_metadata(test_identifier)

        # Compare critical fields (ignore source-specific fields)
        critical_fields = [
            'filename', 'file_size', 'timestamp', 'gps_coordinates',
            'camera_make', 'camera_model', 'colors'
        ]

        for field in critical_fields:
            val1 = getattr(metadata1, field, None)
            val2 = getattr(metadata2, field, None)

            if val1 != val2:
                raise TemplateConsistencyError(
                    f"Field '{field}' differs: {val1} != {val2}"
                )

        return True

    except Exception as e:
        raise TemplateConsistencyError(f"Consistency check failed: {str(e)}")