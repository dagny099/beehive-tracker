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
import logging

logger = logging.getLogger(__name__)


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

        # Vision stage accounting. The UI reads this after a run so that a
        # stage which produced nothing says so out loud. See
        # _perform_vision_analysis for why this exists.
        self.vision_stats: Dict[str, Any] = {
            'attempted': 0,
            'succeeded': 0,
            'skipped': 0,
            'last_error': None,
        }

    def _perform_vision_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """
        Perform computer vision analysis, recording whether it actually ran.

        Shared by all templates. It used to be copy-pasted into each importer,
        where it swallowed failures at DEBUG level. That is how a Vision stage
        that had never worked stayed invisible for ~10 months: the function it
        imported did not exist, ImportError was caught, {} was returned, and
        the run still reported success. Failures are now logged at WARNING and
        counted, so "0 of 12 analyzed" is visible without reading DEBUG logs.

        Args:
            image_data: Raw image bytes

        Returns:
            Dict of vision results, or {} when analysis did not produce labels.
        """
        log = getattr(self, 'logger', logger)
        self.vision_stats['attempted'] += 1

        try:
            from api_services.vision import analyze_image_with_vision_api

            vision_results = analyze_image_with_vision_api(image_data)

            if vision_results and 'labels' in vision_results:
                self.vision_stats['succeeded'] += 1
                log.debug("Vision analysis found %d labels", len(vision_results['labels']))
                return vision_results

            reason = 'no labels returned'
            if isinstance(vision_results, dict) and vision_results.get('error'):
                reason = vision_results['error']

            self.vision_stats['skipped'] += 1
            self.vision_stats['last_error'] = reason
            log.warning("Vision analysis produced no results: %s", reason)
            return {}

        except ImportError as e:
            self.vision_stats['skipped'] += 1
            self.vision_stats['last_error'] = f"Vision API not importable: {e}"
            log.warning(
                "Vision API not importable, skipping analysis for this photo: %s", e
            )
            return {}
        except Exception as e:
            self.vision_stats['skipped'] += 1
            self.vision_stats['last_error'] = str(e)
            log.warning("Vision analysis failed: %s", e)
            return {}

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

            # Pixel dimensions, taken from the decoded image rather than EXIF.
            # Many phone photos omit the width/height tags, and a stripped or
            # rotated file can carry stale ones. PIL already has the real size
            # here, so record it when EXIF did not supply it. This is what lets
            # bulk import report a real resolution instead of "Unknown".
            try:
                width, height = image.size
                exif_data.setdefault('ImageWidth', width)
                exif_data.setdefault('ImageHeight', height)
            except Exception:
                pass

            return exif_data

        except Exception as e:
            # Return empty dict on error - don't fail the entire import
            return {}

    def _extract_gps_coordinates(self, exif_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Common GPS extraction logic used by all templates.

        Fixed 2026-08-23. This imported `get_image_gps_coordinates`, which has
        never existed on any branch, inside `except Exception: pass` — so every
        bulk-imported photo came back with gps_coordinates=None. That cascaded:
        no GPS meant get_inspection_location fell back to the configured
        default, and weather was then fetched for the default coordinates
        rather than where the photo was taken. Plausible wrong data is worse
        than none.

        The real helper is convert_gps_to_decimal(coords, ref). PIL leaves the
        nested GPSInfo dict keyed by integers, so GPSTAGS maps it back.
        """
        log = getattr(self, 'logger', logger)
        gps_info = (exif_data or {}).get('GPSInfo')
        if not gps_info or not isinstance(gps_info, dict):
            return None

        try:
            from PIL.ExifTags import GPSTAGS
            from utils.image_processor import convert_gps_to_decimal

            tags = {GPSTAGS.get(key, key): value for key, value in gps_info.items()}

            latitude = convert_gps_to_decimal(
                tags.get('GPSLatitude'), tags.get('GPSLatitudeRef')
            )
            longitude = convert_gps_to_decimal(
                tags.get('GPSLongitude'), tags.get('GPSLongitudeRef')
            )

            if latitude is None or longitude is None:
                return None

            # A bad conversion is easier to spot here than three screens later
            # on a map.
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                log.warning(
                    "Discarding out-of-range GPS coordinates: %s, %s", latitude, longitude
                )
                return None

            return (latitude, longitude)

        except Exception as e:
            log.warning("GPS extraction failed: %s", e)
            return None

    def _extract_color_palette(self, image_data: bytes) -> List[str]:
        """
        Common color extraction logic used by all templates.

        Fixed 2026-08-23. This passed raw bytes to extract_color_palette, which
        expects a PIL Image and calls img.save(). bytes has no .save, so it
        threw every time and the handler returned a hard-coded grey triple.
        Every bulk-imported photo therefore carried the same three fake
        colours, which look like real data in the gallery.

        Returns [] when extraction genuinely fails, so absent data is absent
        rather than disguised.
        """
        log = getattr(self, 'logger', logger)

        try:
            import io as _io
            from PIL import Image
            from utils.image_processor import extract_color_palette

            with Image.open(_io.BytesIO(image_data)) as image:
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                return extract_color_palette(image)

        except Exception as e:
            log.warning("Colour extraction failed: %s", e)
            return []


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