"""
Local Bulk Import Reference Template.

This template demonstrates the expected patterns for file system-based bulk imports
while maintaining consistency with the S3 template. It shows:

- Efficient directory traversal and file discovery
- Proper file validation and error handling
- Memory-efficient processing of large photo collections
- Integration with existing local storage infrastructure
- Consistent metadata extraction and grouping logic

Key Patterns Demonstrated:
1. Recursive directory scanning with configurable depth limits
2. File type filtering and validation
3. Progress tracking for long-running operations
4. Graceful handling of permissions and access issues
5. Symlink and junction handling for various file systems
6. Integration with existing local storage provider

All patterns follow the S3 template's established conventions while being
optimized for local file system operations.
"""

import os
import logging
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .photo_processing_contract import (
    BulkImportTemplate, PhotoMetadata, InspectionGroup,
    ProcessingResult, GroupingStrategy
)


class LocalBulkImporter(BulkImportTemplate):
    """
    Reference implementation for local file system-based bulk photo import.

    This template demonstrates best practices for:
    - File system traversal and discovery
    - Large directory handling with memory efficiency
    - Cross-platform file operations
    - Integration with existing storage infrastructure
    - Consistent error handling patterns

    Configuration Options:
        base_path (str): Root directory to scan for photos
        recursive (bool): Whether to scan subdirectories (default: True)
        max_depth (int): Maximum directory depth to scan (default: 10)
        follow_symlinks (bool): Whether to follow symbolic links (default: False)
        file_extensions (list): Allowed file extensions (default: common image types)
        exclude_patterns (list): Directory/file patterns to exclude (default: system dirs)
        max_workers (int): Maximum concurrent file processors (default: 4)
        batch_size (int): Number of files to process per batch (default: 20)
        grouping_strategy (str): How to group photos into inspections
        preserve_structure (bool): Maintain directory structure in metadata
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local bulk importer with comprehensive path validation.

        Args:
            config: Configuration dictionary with local file system settings

        Raises:
            ValueError: If required configuration is missing or invalid
            OSError: If base path is not accessible
        """
        super().__init__(config)

        # Extract and validate local configuration
        self.base_path = Path(config.get('base_path', '.'))
        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {self.base_path}")
        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {self.base_path}")

        # Directory traversal settings
        self.recursive = config.get('recursive', True)
        self.max_depth = config.get('max_depth', 10)
        self.follow_symlinks = config.get('follow_symlinks', False)

        # File filtering settings
        self.file_extensions = config.get('file_extensions', [
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif',
            '.JPG', '.JPEG', '.PNG', '.TIFF', '.TIF', '.BMP', '.GIF'
        ])
        self.exclude_patterns = config.get('exclude_patterns', [
            '.*',           # Hidden directories (Unix)
            '__pycache__',  # Python cache
            'node_modules', # Node.js modules
            '.git',         # Git repository
            '.svn',         # SVN repository
            'Thumbs.db',    # Windows thumbnails
            '.DS_Store'     # macOS metadata
        ])

        # Performance settings
        self.max_workers = config.get('max_workers', 4)  # Conservative for file I/O
        self.batch_size = config.get('batch_size', 20)

        # Structure preservation
        self.preserve_structure = config.get('preserve_structure', True)

        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}.{self.base_path.name}")

        # Cache for directory validation
        self._validated_dirs = set()

    def validate_source(self) -> bool:
        """
        Validate local file system access and permissions.

        Performs comprehensive validation:
        1. Base directory exists and is accessible
        2. Required read permissions
        3. Directory structure traversal capability
        4. Photo files availability in specified path

        Returns:
            bool: True if source is valid and accessible
        """
        try:
            # Test base directory access
            if not os.access(self.base_path, os.R_OK):
                self.logger.error(f"No read permission for base path: {self.base_path}")
                return False

            # Test directory traversal
            photo_count = 0
            sample_limit = 10  # Just test a few files for validation

            for photo_path in self._discover_photos_generator():
                if os.access(photo_path, os.R_OK):
                    photo_count += 1
                    if photo_count >= sample_limit:
                        break

            if photo_count == 0:
                self.logger.warning(f"No accessible photos found in: {self.base_path}")
                return False

            self.logger.info(f"Source validation successful: {photo_count}+ accessible photos found")
            return True

        except OSError as e:
            self.logger.error(f"File system error during validation: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            return False

    def extract_photo_metadata(self, source_identifier: Union[str, Path]) -> PhotoMetadata:
        """
        Extract standardized metadata from local file.

        This method follows the REFERENCE PATTERN established by S3 template:
        1. Validate file access and type
        2. Use shared utilities for consistent EXIF processing
        3. Handle errors gracefully with meaningful messages
        4. Extract all standard metadata fields
        5. Include source-specific information (file paths, timestamps)

        Args:
            source_identifier: Local file path (str or Path)

        Returns:
            PhotoMetadata: Standardized metadata structure

        Raises:
            ValueError: If file is not a valid image or cannot be processed
            RuntimeError: If file is inaccessible
        """
        if not source_identifier:
            raise ValueError("File path cannot be empty")

        file_path = Path(source_identifier)

        try:
            # Validate file existence and accessibility
            if not file_path.exists():
                raise RuntimeError(f"File does not exist: {file_path}")

            if not file_path.is_file():
                raise ValueError(f"Path is not a regular file: {file_path}")

            if not os.access(file_path, os.R_OK):
                raise RuntimeError(f"No read permission for file: {file_path}")

            # Validate file extension
            if not any(str(file_path).lower().endswith(ext.lower()) for ext in self.file_extensions):
                raise ValueError(f"Unsupported file type: {file_path.suffix}")

            # Get file statistics
            stat_info = file_path.stat()
            file_size = stat_info.st_size
            file_mtime = datetime.fromtimestamp(stat_info.st_mtime)

            # Validate file size (prevent processing huge files)
            max_file_size = 100 * 1024 * 1024  # 100MB limit for local files
            if file_size > max_file_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {max_file_size})")

            # Read file data for processing
            self.logger.debug(f"Reading local file: {file_path} ({file_size} bytes)")
            with open(file_path, 'rb') as f:
                image_data = f.read()

            # Extract EXIF data using shared utilities (ensures consistency)
            exif_data = self._extract_exif_data(image_data)

            # Extract timestamp from EXIF (prefer EXIF over file system timestamp)
            timestamp = None
            if 'DateTime' in exif_data:
                try:
                    timestamp = datetime.strptime(exif_data['DateTime'], '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    self.logger.warning(f"Invalid EXIF DateTime format: {exif_data['DateTime']}")

            # Fallback to file modification time if no EXIF timestamp
            if not timestamp:
                timestamp = file_mtime

            # Extract GPS coordinates using shared utilities
            gps_coordinates = self._extract_gps_coordinates(exif_data)

            # Extract camera information
            camera_make = exif_data.get('Make', '').strip()
            camera_model = exif_data.get('Model', '').strip()

            # Extract color palette using shared utilities
            colors = self._extract_color_palette(image_data)

            # Perform vision analysis (if available)
            vision_analysis = self._perform_vision_analysis(image_data)

            # Generate original path (preserve directory structure if configured)
            original_path = self._get_structured_path(file_path)

            # Create standardized metadata object
            metadata = PhotoMetadata(
                filename=file_path.name,
                original_path=original_path,
                file_size=file_size,
                created_at=timestamp,
                exif_data=exif_data,
                timestamp=timestamp,
                gps_coordinates=gps_coordinates,
                camera_make=camera_make if camera_make else None,
                camera_model=camera_model if camera_model else None,
                colors=colors,
                vision_analysis=vision_analysis,
                source_type="local",
                processed_at=datetime.now()
            )

            self.logger.debug(f"Successfully extracted metadata for: {file_path.name}")
            return metadata

        except (ValueError, RuntimeError):
            # Deliberate, specific failures raised in the block above (missing
            # file, unsupported type, no read permission). The generic handler
            # below used to re-wrap them, flattening every cause into a single
            # ValueError, so callers and the docstring's own contract could no
            # longer tell "file does not exist" from "not a valid image".
            raise
        except OSError as e:
            raise RuntimeError(f"File system error accessing {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to process image {file_path}: {str(e)}")

    def _get_structured_path(self, file_path: Path) -> str:
        """
        Generate structured path representation for original_path field.

        Args:
            file_path: Absolute file path

        Returns:
            str: Structured path for metadata
        """
        if self.preserve_structure:
            # Return relative path from base directory
            try:
                relative_path = file_path.relative_to(self.base_path.resolve())
                return f"file://{self.base_path.resolve()}/{relative_path}"
            except ValueError:
                # File is outside base path, use absolute path
                return f"file://{file_path.resolve()}"
        else:
            # Return just the filename
            return f"file://{file_path.resolve()}"

    # _perform_vision_analysis now lives on BulkImportTemplate so all three
    # importers share one implementation (and one set of vision counters).

    def group_into_inspections(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """
        Group photos into logical inspections using consistent algorithms.

        Uses IDENTICAL grouping logic as S3 template to ensure consistency.
        This demonstrates how different import sources can share core logic.

        Args:
            photos: List of processed photo metadata

        Returns:
            List[InspectionGroup]: Grouped inspections with confidence scores
        """
        if not photos:
            return []

        self.logger.info(f"Grouping {len(photos)} photos using strategy: {self.grouping_strategy.value}")

        # Sort photos by timestamp for consistent processing (same as S3)
        sorted_photos = sorted(photos, key=lambda p: p.timestamp or p.created_at)

        if self.grouping_strategy == GroupingStrategy.BY_DATE:
            return self._group_by_date(sorted_photos)
        elif self.grouping_strategy == GroupingStrategy.BY_LOCATION:
            return self._group_by_location(sorted_photos)
        elif self.grouping_strategy == GroupingStrategy.BY_HYBRID:
            return self._group_by_hybrid(sorted_photos)
        else:
            # Default to date-based grouping
            self.logger.warning(f"Unknown grouping strategy: {self.grouping_strategy}, using date-based")
            return self._group_by_date(sorted_photos)

    def _group_by_date(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """
        Group photos by date - IDENTICAL implementation to S3 template.

        This ensures that local and S3 imports produce identical groupings
        for the same set of photos, maintaining template consistency.
        """
        groups = {}

        for photo in photos:
            photo_date = photo.timestamp or photo.created_at
            date_key = photo_date.date()

            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(photo)

        # Convert to InspectionGroup objects (identical to S3 template)
        inspection_groups = []
        for date_key, group_photos in groups.items():
            # Calculate location if GPS data is available
            gps_coords = [p.gps_coordinates for p in group_photos if p.gps_coordinates]
            location = None
            if gps_coords:
                # Use average location for the group
                avg_lat = sum(coord[0] for coord in gps_coords) / len(gps_coords)
                avg_lon = sum(coord[1] for coord in gps_coords) / len(gps_coords)
                location = {
                    "lat": round(avg_lat, 6),
                    "lon": round(avg_lon, 6),
                    "name": f"Location ({avg_lat:.4f}, {avg_lon:.4f})"
                }

            # Calculate confidence (identical algorithm to S3 template)
            confidence = self._calculate_temporal_confidence(group_photos)

            group = InspectionGroup(
                inspection_date=datetime.combine(date_key, datetime.min.time()),
                location=location,
                photos=group_photos,
                grouping_criteria=GroupingStrategy.BY_DATE,
                confidence_score=confidence
            )
            inspection_groups.append(group)

        self.logger.info(f"Created {len(inspection_groups)} date-based inspection groups")
        return inspection_groups

    def _group_by_location(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """Group photos by GPS location - placeholder for future implementation."""
        self.logger.warning("Location-based grouping not yet implemented, using date-based")
        return self._group_by_date(photos)

    def _group_by_hybrid(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """Group photos using hybrid algorithm - placeholder for future implementation."""
        self.logger.warning("Hybrid grouping not yet implemented, using date-based")
        return self._group_by_date(photos)

    def _calculate_temporal_confidence(self, photos: List[PhotoMetadata]) -> float:
        """
        Calculate confidence score for temporal grouping.

        IDENTICAL implementation to S3 template for consistency.
        """
        if len(photos) <= 1:
            return 1.0

        # Calculate time span of the group
        timestamps = [p.timestamp or p.created_at for p in photos]
        time_span = max(timestamps) - min(timestamps)

        # High confidence for inspections under 4 hours
        if time_span.total_seconds() <= 4 * 3600:
            return 0.95
        # Medium confidence for inspections under 8 hours
        elif time_span.total_seconds() <= 8 * 3600:
            return 0.8
        # Lower confidence for longer periods
        else:
            return 0.6

    def discover_photos(self,
                      max_files: int = 10000,
                      progress_callback: Optional[Callable] = None) -> List[str]:
        """
        Discover all photo files in the directory tree efficiently.

        Demonstrates efficient local file system patterns:
        1. Memory-efficient directory traversal
        2. Configurable depth limiting
        3. Pattern-based exclusion filtering
        4. Progress reporting for large directories
        5. Cross-platform path handling

        Args:
            max_files: Maximum number of files to return
            progress_callback: Optional callback for progress updates

        Returns:
            List[str]: Paths to discovered photo files
        """
        photo_paths = []
        files_scanned = 0

        try:
            for file_path in self._discover_photos_generator():
                files_scanned += 1

                # Add to results
                photo_paths.append(str(file_path))

                # Check limits
                if len(photo_paths) >= max_files:
                    self.logger.info(f"Reached max_files limit: {max_files}")
                    break

                # Report progress periodically
                if progress_callback and files_scanned % 100 == 0:
                    progress_callback(files_scanned, None, f"Scanned {files_scanned} files")

            self.logger.info(f"Discovered {len(photo_paths)} photos from {files_scanned} files scanned")
            return photo_paths

        except Exception as e:
            self.logger.error(f"Error during photo discovery: {e}")
            raise RuntimeError(f"Failed to discover photos in {self.base_path}: {e}")

    def _discover_photos_generator(self):
        """
        Generator for memory-efficient photo discovery.

        Yields photo file paths one at a time to minimize memory usage
        when processing large directory trees.
        """
        if self.recursive:
            # Use os.walk for recursive traversal
            for root, dirs, files in os.walk(self.base_path, followlinks=self.follow_symlinks):
                # Calculate current depth
                depth = len(Path(root).relative_to(self.base_path).parts)
                if depth > self.max_depth:
                    continue

                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not self._should_exclude(d)]

                # Process files in current directory
                for filename in files:
                    if self._should_exclude(filename):
                        continue

                    file_path = Path(root) / filename

                    # Check file extension
                    if any(filename.lower().endswith(ext.lower()) for ext in self.file_extensions):
                        yield file_path

        else:
            # Non-recursive: only scan base directory
            try:
                for item in self.base_path.iterdir():
                    if item.is_file() and not self._should_exclude(item.name):
                        if any(item.name.lower().endswith(ext.lower()) for ext in self.file_extensions):
                            yield item
            except OSError as e:
                self.logger.error(f"Error scanning base directory: {e}")

    def _should_exclude(self, name: str) -> bool:
        """
        Check if a file or directory should be excluded based on patterns.

        Args:
            name: File or directory name

        Returns:
            bool: True if should be excluded
        """
        for pattern in self.exclude_patterns:
            if glob.fnmatch.fnmatch(name, pattern):
                return True
        return False

    def process_bulk_import(self,
                          source_list: Optional[List[str]] = None,
                          progress_callback: Optional[Callable] = None) -> ProcessingResult:
        """
        Process bulk import with local file system optimizations.

        Follows the same pattern as S3 template but optimized for file I/O:
        1. Auto-discovery of files if not provided
        2. Concurrent processing with file I/O optimized parallelism
        3. Batch processing for memory efficiency
        4. Comprehensive error recovery and reporting

        Args:
            source_list: Optional list of file paths (auto-discovered if None)
            progress_callback: Optional callback for progress updates

        Returns:
            ProcessingResult: Comprehensive processing results
        """
        start_time = datetime.now()

        # Auto-discover files if not provided
        if source_list is None:
            if progress_callback:
                progress_callback(0, None, "Discovering photos in directory tree...")

            source_list = self.discover_photos(
                max_files=10000,  # Reasonable limit for bulk import
                progress_callback=progress_callback
            )

        result = ProcessingResult(
            success=False,
            processed_photos=[],
            inspection_groups=[],
            errors=[],
            warnings=[],
            total_files_found=len(source_list)
        )

        if not source_list:
            result.errors.append("No photos found to process")
            return result

        try:
            # Validate source before processing
            if not self.validate_source():
                result.errors.append("Local source validation failed")
                return result

            self.logger.info(f"Starting bulk import of {len(source_list)} photos from local filesystem")

            # Process in batches with concurrent workers (optimized for file I/O)
            processed_count = 0

            for batch_start in range(0, len(source_list), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(source_list))
                batch = source_list[batch_start:batch_end]

                if progress_callback:
                    progress_callback(
                        processed_count, len(source_list),
                        f"Processing batch {batch_start//self.batch_size + 1}"
                    )

                # Process batch with concurrent workers
                batch_results = self._process_batch_concurrent(batch, progress_callback)

                # Collect results
                for photo_metadata, error in batch_results:
                    if photo_metadata:
                        result.processed_photos.append(photo_metadata)
                        result.valid_photos += 1
                    else:
                        result.errors.append(error)
                        result.invalid_photos += 1

                processed_count += len(batch)

                # Yield control periodically for long-running imports
                if processed_count % (self.batch_size * 5) == 0:
                    self.logger.info(f"Progress: {processed_count}/{len(source_list)} photos processed")

            # Group photos into inspections (identical to S3 template)
            if result.processed_photos:
                if progress_callback:
                    progress_callback(
                        len(source_list), len(source_list),
                        "Grouping photos into inspections..."
                    )

                result.inspection_groups = self.group_into_inspections(result.processed_photos)
                self.logger.info(f"Created {len(result.inspection_groups)} inspection groups")

            # Calculate final statistics
            result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            result.success = result.valid_photos > 0

            self.logger.info(
                f"Bulk import completed: {result.valid_photos} valid, "
                f"{result.invalid_photos} invalid, {len(result.inspection_groups)} groups, "
                f"{result.processing_time_seconds:.1f}s"
            )

            return result

        except Exception as e:
            result.errors.append(f"Bulk import failed: {str(e)}")
            result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Bulk import failed: {e}", exc_info=True)
            return result

    def _process_batch_concurrent(self,
                                batch: List[str],
                                progress_callback: Optional[Callable] = None) -> List[tuple]:
        """
        Process a batch of files concurrently with file I/O optimization.

        Uses fewer workers than S3 template since file I/O is less parallelizable
        and we want to avoid overwhelming the file system.

        Args:
            batch: List of file paths to process
            progress_callback: Optional progress callback

        Returns:
            List[tuple]: List of (PhotoMetadata, error) tuples
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self._safe_extract_metadata, path): path
                for path in batch
            }

            # Collect results as they complete
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    metadata = future.result()
                    results.append((metadata, None))
                except Exception as e:
                    error_msg = f"Failed to process {path}: {str(e)}"
                    results.append((None, error_msg))
                    self.logger.error(error_msg)

        return results

    def _safe_extract_metadata(self, file_path: str) -> PhotoMetadata:
        """
        Safely extract metadata with comprehensive error handling.

        Args:
            file_path: Local file path

        Returns:
            PhotoMetadata: Extracted metadata

        Raises:
            Exception: If extraction fails after all retries
        """
        max_retries = 2  # Fewer retries for local files (usually persistent errors)
        for attempt in range(max_retries):
            try:
                return self.extract_photo_metadata(file_path)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Retry {attempt + 1}/{max_retries} for {file_path}: {e}")


# Factory function following S3 template pattern
def create_local_bulk_importer(base_path: str, **kwargs) -> LocalBulkImporter:
    """
    Factory function for creating local bulk importer with sensible defaults.

    This demonstrates the recommended way to configure the importer
    for different use cases.

    Args:
        base_path: Base directory to scan for photos
        **kwargs: Additional configuration options

    Returns:
        LocalBulkImporter: Configured importer instance
    """
    config = {
        'base_path': base_path,
        'recursive': True,
        'max_depth': 10,
        'follow_symlinks': False,
        'grouping_strategy': 'date',
        'max_workers': 4,
        'batch_size': 20,
        'preserve_structure': True,
        'file_extensions': [
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif',
            '.JPG', '.JPEG', '.PNG', '.TIFF', '.TIF', '.BMP', '.GIF'
        ],
        **kwargs
    }

    return LocalBulkImporter(config)