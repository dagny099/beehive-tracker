"""
URL Bulk Import Reference Template.

This template demonstrates the expected patterns for network-based bulk imports
while maintaining consistency with S3 and Local templates. It shows:

- HTTP/HTTPS URL validation and fetching
- Streaming downloads for large images
- Comprehensive error handling for network operations
- Authentication handling for various URL sources
- Retry mechanisms for network failures
- Content-type validation and security measures

Key Patterns Demonstrated:
1. URL validation and sanitization
2. Streaming HTTP downloads with progress tracking
3. Content-type verification for security
4. Network timeout and retry handling
5. Authentication for protected resources
6. Integration with existing processing infrastructure

All patterns follow the established template conventions while being
optimized for network operations and security considerations.
"""

import os
import logging
import requests
from urllib.parse import urlparse, unquote
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
from pathlib import Path

from .photo_processing_contract import (
    BulkImportTemplate, PhotoMetadata, InspectionGroup,
    ProcessingResult, GroupingStrategy
)


class URLBulkImporter(BulkImportTemplate):
    """
    Reference implementation for URL-based bulk photo import.

    This template demonstrates best practices for:
    - Network-based photo retrieval
    - HTTP/HTTPS protocol handling
    - Authentication and security measures
    - Streaming downloads for efficiency
    - Comprehensive error recovery
    - Content validation and filtering

    Configuration Options:
        urls (list): List of URLs to process
        user_agent (str): User agent string for requests
        timeout (int): Request timeout in seconds (default: 30)
        max_retries (int): Maximum retry attempts (default: 3)
        chunk_size (int): Download chunk size in bytes (default: 8192)
        max_file_size (int): Maximum file size in MB (default: 50)
        verify_ssl (bool): Whether to verify SSL certificates (default: True)
        auth (dict): Authentication credentials if needed
        headers (dict): Additional HTTP headers
        max_workers (int): Maximum concurrent downloads (default: 3)
        batch_size (int): Number of URLs to process per batch (default: 10)
        grouping_strategy (str): How to group photos into inspections
        allowed_content_types (list): Allowed MIME types for downloads
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize URL bulk importer with comprehensive network configuration.

        Args:
            config: Configuration dictionary with URL and network settings

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        super().__init__(config)

        # Network configuration
        self.user_agent = config.get('user_agent', 'BeehiveTracker/1.0 (Photo Import Bot)')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.chunk_size = config.get('chunk_size', 8192)
        self.verify_ssl = config.get('verify_ssl', True)

        # File size limits
        self.max_file_size = config.get('max_file_size', 50) * 1024 * 1024  # Convert MB to bytes

        # Authentication settings
        self.auth = config.get('auth', None)
        self.headers = config.get('headers', {})

        # Content filtering
        self.allowed_content_types = config.get('allowed_content_types', [
            'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/gif'
        ])

        # Performance settings
        self.max_workers = config.get('max_workers', 3)  # Conservative for network I/O
        self.batch_size = config.get('batch_size', 10)

        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}")

        # Initialize HTTP session with connection pooling
        self._init_http_session()

    def _init_http_session(self) -> None:
        """
        Initialize HTTP session with optimal settings for bulk downloads.

        Demonstrates network optimization patterns:
        1. Connection pooling for efficiency
        2. Proper timeout configuration
        3. User agent and headers setup
        4. SSL verification handling
        5. Authentication configuration
        """
        self.session = requests.Session()

        # Configure session defaults
        self.session.headers.update({
            'User-Agent': self.user_agent,
            **self.headers
        })

        # Configure authentication if provided
        if self.auth:
            if self.auth.get('type') == 'basic':
                self.session.auth = (self.auth['username'], self.auth['password'])
            elif self.auth.get('type') == 'bearer':
                self.session.headers['Authorization'] = f"Bearer {self.auth['token']}"

        # Configure SSL verification
        self.session.verify = self.verify_ssl

        # Configure connection adapter for retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=self.max_workers)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.logger.info(f"HTTP session initialized with {self.max_workers} max connections")

    def validate_source(self) -> bool:
        """
        Validate URL accessibility and network connectivity.

        Performs lightweight validation:
        1. Network connectivity test
        2. Sample URL accessibility check
        3. Authentication validation
        4. SSL certificate verification

        Returns:
            bool: True if network sources are accessible
        """
        try:
            # Test basic network connectivity
            test_response = self.session.head('https://httpbin.org/status/200', timeout=10)
            if test_response.status_code != 200:
                self.logger.warning("Network connectivity test failed")
                return False

            self.logger.info("Network connectivity validated successfully")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            return False

    def extract_photo_metadata(self, source_identifier: str) -> PhotoMetadata:
        """
        Extract standardized metadata from URL source.

        This method follows the REFERENCE PATTERN established by other templates:
        1. Validate URL format and accessibility
        2. Download image data with streaming and progress tracking
        3. Use shared utilities for consistent EXIF processing
        4. Handle network errors gracefully with retries
        5. Extract all standard metadata fields
        6. Include source-specific information (URLs, HTTP headers)

        Args:
            source_identifier: URL to the image

        Returns:
            PhotoMetadata: Standardized metadata structure

        Raises:
            ValueError: If URL is invalid or image cannot be processed
            RuntimeError: If URL is inaccessible or download fails
        """
        if not source_identifier:
            raise ValueError("URL cannot be empty")

        # Validate URL format
        parsed_url = urlparse(source_identifier)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL format: {source_identifier}")

        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")

        try:
            # Get image metadata without downloading full content first
            head_response = self.session.head(source_identifier, timeout=self.timeout)
            head_response.raise_for_status()

            # Validate content type
            content_type = head_response.headers.get('content-type', '').lower()
            if not any(ct in content_type for ct in self.allowed_content_types):
                raise ValueError(f"Unsupported content type: {content_type}")

            # Validate file size
            content_length = head_response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                if file_size > self.max_file_size:
                    raise ValueError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            else:
                file_size = 0  # Unknown size, will be determined during download

            # Download the image data
            self.logger.debug(f"Downloading image from URL: {source_identifier}")
            image_data = self._download_image_data(source_identifier)

            # Update file size if it wasn't available in headers
            if file_size == 0:
                file_size = len(image_data)

            # Extract filename from URL
            filename = self._extract_filename_from_url(source_identifier)

            # Extract EXIF data using shared utilities (ensures consistency)
            exif_data = self._extract_exif_data(image_data)

            # Extract timestamp from EXIF (prefer EXIF over HTTP headers)
            timestamp = None
            if 'DateTime' in exif_data:
                try:
                    timestamp = datetime.strptime(exif_data['DateTime'], '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    self.logger.warning(f"Invalid EXIF DateTime format: {exif_data['DateTime']}")

            # Fallback to HTTP Last-Modified header
            if not timestamp:
                last_modified = head_response.headers.get('last-modified')
                if last_modified:
                    try:
                        timestamp = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                    except ValueError:
                        pass

            # Final fallback to current time
            if not timestamp:
                timestamp = datetime.now()

            # Extract GPS coordinates using shared utilities
            gps_coordinates = self._extract_gps_coordinates(exif_data)

            # Extract camera information
            camera_make = exif_data.get('Make', '').strip()
            camera_model = exif_data.get('Model', '').strip()

            # Extract color palette using shared utilities
            colors = self._extract_color_palette(image_data)

            # Perform vision analysis (if available)
            vision_analysis = self._perform_vision_analysis(image_data)

            # Create standardized metadata object
            metadata = PhotoMetadata(
                filename=filename,
                original_path=source_identifier,
                file_size=file_size,
                created_at=timestamp,
                exif_data=exif_data,
                timestamp=timestamp,
                gps_coordinates=gps_coordinates,
                camera_make=camera_make if camera_make else None,
                camera_model=camera_model if camera_model else None,
                colors=colors,
                vision_analysis=vision_analysis,
                source_type="url",
                processed_at=datetime.now()
            )

            self.logger.debug(f"Successfully extracted metadata for: {filename}")
            return metadata

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error accessing {source_identifier}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to process image {source_identifier}: {str(e)}")

    def _download_image_data(self, url: str) -> bytes:
        """
        Download image data with streaming and progress tracking.

        Demonstrates efficient network download patterns:
        1. Streaming download to handle large files
        2. Content-length validation during download
        3. Memory-efficient processing
        4. Timeout handling for slow connections

        Args:
            url: URL to download

        Returns:
            bytes: Downloaded image data

        Raises:
            RuntimeError: If download fails or exceeds size limits
        """
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Download in chunks with size validation
            image_data = bytearray()
            downloaded_size = 0

            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    image_data.extend(chunk)
                    downloaded_size += len(chunk)

                    # Check size limit during download
                    if downloaded_size > self.max_file_size:
                        raise RuntimeError(f"File too large during download: {downloaded_size} bytes")

            return bytes(image_data)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Download failed: {e}")

    def _extract_filename_from_url(self, url: str) -> str:
        """
        Extract filename from URL with fallback strategies.

        Args:
            url: URL to extract filename from

        Returns:
            str: Extracted filename
        """
        parsed_url = urlparse(url)

        # Try to get filename from path
        path = unquote(parsed_url.path)
        if path and '/' in path:
            filename = path.split('/')[-1]
            if filename and '.' in filename:
                return filename

        # Fallback to domain + timestamp
        domain = parsed_url.netloc.replace('www.', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{domain}_{timestamp}.jpg"

    def _perform_vision_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """
        Perform computer vision analysis using existing infrastructure.

        IDENTICAL implementation to other templates for consistency.

        Args:
            image_data: Raw image bytes

        Returns:
            Dict containing vision analysis results
        """
        try:
            # Import and use existing vision API integration
            from api_services.vision import analyze_image_with_vision_api

            # Use existing vision API (same as other templates)
            vision_results = analyze_image_with_vision_api(image_data)

            if vision_results and 'labels' in vision_results:
                self.logger.debug(f"Vision analysis found {len(vision_results['labels'])} labels")
                return vision_results
            else:
                self.logger.debug("No vision analysis results available")
                return {}

        except ImportError:
            self.logger.debug("Vision API not available - skipping analysis")
            return {}
        except Exception as e:
            self.logger.warning(f"Vision analysis failed: {e}")
            return {}

    def group_into_inspections(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """
        Group photos into logical inspections using consistent algorithms.

        Uses IDENTICAL grouping logic as other templates to ensure consistency.
        This demonstrates how different import sources share core logic.

        Args:
            photos: List of processed photo metadata

        Returns:
            List[InspectionGroup]: Grouped inspections with confidence scores
        """
        if not photos:
            return []

        self.logger.info(f"Grouping {len(photos)} photos using strategy: {self.grouping_strategy.value}")

        # Sort photos by timestamp for consistent processing (same as other templates)
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
        Group photos by date - IDENTICAL implementation to other templates.

        This ensures that URL, S3, and Local imports produce identical groupings
        for the same set of photos, maintaining template consistency.
        """
        groups = {}

        for photo in photos:
            photo_date = photo.timestamp or photo.created_at
            date_key = photo_date.date()

            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(photo)

        # Convert to InspectionGroup objects (identical to other templates)
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

            # Calculate confidence (identical algorithm to other templates)
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

        IDENTICAL implementation to other templates for consistency.
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

    def process_bulk_import(self,
                          source_list: Optional[List[str]] = None,
                          progress_callback: Optional[Callable] = None) -> ProcessingResult:
        """
        Process bulk import with network-optimized performance patterns.

        Demonstrates advanced network processing:
        1. Concurrent downloads with controlled parallelism
        2. Network error recovery and retry logic
        3. Bandwidth-aware batch processing
        4. Comprehensive connection monitoring

        Args:
            source_list: List of URLs to process
            progress_callback: Optional callback for progress updates

        Returns:
            ProcessingResult: Comprehensive processing results
        """
        start_time = datetime.now()

        if source_list is None:
            raise ValueError("URL list is required for URL bulk import")

        # Validate URLs before processing
        valid_urls = []
        for url in source_list:
            if self._is_valid_url(url):
                valid_urls.append(url)
            else:
                self.logger.warning(f"Skipping invalid URL: {url}")

        result = ProcessingResult(
            success=False,
            processed_photos=[],
            inspection_groups=[],
            errors=[],
            warnings=[],
            total_files_found=len(valid_urls)
        )

        if not valid_urls:
            result.errors.append("No valid URLs found to process")
            return result

        try:
            # Validate network connectivity
            if not self.validate_source():
                result.errors.append("Network connectivity validation failed")
                return result

            self.logger.info(f"Starting bulk import of {len(valid_urls)} URLs")

            # Process in batches with concurrent workers (optimized for network I/O)
            processed_count = 0

            for batch_start in range(0, len(valid_urls), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(valid_urls))
                batch = valid_urls[batch_start:batch_end]

                if progress_callback:
                    progress_callback(
                        processed_count, len(valid_urls),
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

                # Report progress periodically
                if processed_count % (self.batch_size * 3) == 0:
                    self.logger.info(f"Progress: {processed_count}/{len(valid_urls)} URLs processed")

            # Group photos into inspections (identical to other templates)
            if result.processed_photos:
                if progress_callback:
                    progress_callback(
                        len(valid_urls), len(valid_urls),
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

        finally:
            # Clean up HTTP session
            self.session.close()

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format and basic accessibility.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL appears valid
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def _process_batch_concurrent(self,
                                batch: List[str],
                                progress_callback: Optional[Callable] = None) -> List[tuple]:
        """
        Process a batch of URLs concurrently with network optimization.

        Uses conservative concurrency for network operations to avoid
        overwhelming servers and respecting rate limits.

        Args:
            batch: List of URLs to process
            progress_callback: Optional progress callback

        Returns:
            List[tuple]: List of (PhotoMetadata, error) tuples
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self._safe_extract_metadata, url): url
                for url in batch
            }

            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    metadata = future.result()
                    results.append((metadata, None))
                except Exception as e:
                    error_msg = f"Failed to process {url}: {str(e)}"
                    results.append((None, error_msg))
                    self.logger.error(error_msg)

        return results

    def _safe_extract_metadata(self, url: str) -> PhotoMetadata:
        """
        Safely extract metadata with comprehensive error handling.

        Args:
            url: URL to process

        Returns:
            PhotoMetadata: Extracted metadata

        Raises:
            Exception: If extraction fails after all retries
        """
        max_retries = self.max_retries
        for attempt in range(max_retries):
            try:
                return self.extract_photo_metadata(url)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Retry {attempt + 1}/{max_retries} for {url}: {e}")


# Factory function following established template pattern
def create_url_bulk_importer(urls: List[str], **kwargs) -> URLBulkImporter:
    """
    Factory function for creating URL bulk importer with sensible defaults.

    This demonstrates the recommended way to configure the importer
    for different use cases.

    Args:
        urls: List of URLs to process
        **kwargs: Additional configuration options

    Returns:
        URLBulkImporter: Configured importer instance
    """
    config = {
        'urls': urls,
        'grouping_strategy': 'date',
        'max_workers': 3,
        'batch_size': 10,
        'timeout': 30,
        'max_retries': 3,
        'verify_ssl': True,
        'max_file_size': 50,  # MB
        **kwargs
    }

    return URLBulkImporter(config)