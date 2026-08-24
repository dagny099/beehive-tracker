"""
S3 Bulk Import Reference Template.

This is the REFERENCE IMPLEMENTATION that demonstrates the expected patterns
for all bulk import templates. It shows:

- Proper integration with existing storage infrastructure
- Comprehensive error handling and recovery strategies
- Performance optimizations for cloud operations
- Detailed logging and progress tracking
- Security best practices for AWS operations

Key Patterns Demonstrated:
1. Source validation with detailed error reporting
2. Batch processing with configurable concurrency
3. Progress tracking with meaningful status updates
4. Graceful degradation when services are unavailable
5. Consistent metadata extraction using shared utilities
6. Standard inspection grouping logic

All other import templates should follow these established patterns.
"""

import logging
import io
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logging.warning("boto3 not available - S3BulkImporter will not function")

from .photo_processing_contract import (
    BulkImportTemplate, PhotoMetadata, InspectionGroup,
    ProcessingResult, GroupingStrategy
)


class S3BulkImporter(BulkImportTemplate):
    """
    Reference implementation for S3-based bulk photo import.

    This template demonstrates best practices for:
    - Cloud storage integration
    - Batch processing optimization
    - Error handling and recovery
    - Progress tracking and user feedback
    - Security and authentication patterns

    Configuration Options:
        bucket_name (str): S3 bucket containing photos
        region (str): AWS region (default: us-east-1)
        aws_access_key_id (str): AWS access key (optional, uses default auth)
        aws_secret_access_key (str): AWS secret (optional, uses default auth)
        prefix_filter (str): Only process objects with this prefix
        file_extensions (list): Allowed file extensions (default: ['.jpg', '.jpeg', '.png'])
        max_workers (int): Maximum concurrent downloads (default: 5)
        batch_size (int): Number of files to process per batch (default: 10)
        grouping_strategy (str): How to group photos into inspections
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 bulk importer with comprehensive configuration validation.

        Args:
            config: Configuration dictionary with S3 settings

        Raises:
            ImportError: If boto3 is not available
            ValueError: If required configuration is missing
        """
        super().__init__(config)

        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 bulk import. Install with: pip install boto3")

        # Extract and validate S3 configuration
        self.bucket_name = config.get('bucket_name')
        if not self.bucket_name:
            raise ValueError("bucket_name is required in configuration")

        self.region = config.get('region', 'us-east-1')
        self.prefix_filter = config.get('prefix_filter', '')
        self.file_extensions = config.get('file_extensions', ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'])

        # Performance settings
        self.max_workers = config.get('max_workers', 5)
        self.batch_size = config.get('batch_size', 10)

        # Initialize logging first
        self.logger = logging.getLogger(f"{__name__}.{self.bucket_name}")

        # Initialize S3 client with proper error handling
        self._init_s3_client(config)

    def _init_s3_client(self, config: Dict[str, Any]) -> None:
        """
        Initialize S3 client with comprehensive authentication handling.

        Demonstrates proper AWS authentication patterns:
        1. Explicit credentials from config
        2. Environment variables (AWS_ACCESS_KEY_ID, etc.)
        3. IAM roles (for EC2/Lambda)
        4. AWS credentials file (~/.aws/credentials)

        Args:
            config: Configuration dictionary

        Raises:
            NoCredentialsError: If no valid credentials found
        """
        try:
            session_config = {
                'region_name': self.region,
                'service_name': 's3'
            }

            # Use explicit credentials if provided
            if config.get('aws_access_key_id') and config.get('aws_secret_access_key'):
                session_config.update({
                    'aws_access_key_id': config['aws_access_key_id'],
                    'aws_secret_access_key': config['aws_secret_access_key']
                })

                if config.get('aws_session_token'):
                    session_config['aws_session_token'] = config['aws_session_token']

                self.logger.info("Using explicit AWS credentials from configuration")
            else:
                self.logger.info("Using default AWS credential chain")

            # Create S3 client
            self.s3_client = boto3.client('s3', **session_config)

            # Test credentials by attempting to list the bucket
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")

        except NoCredentialsError:
            self.logger.error("No AWS credentials found. Configure credentials using one of:")
            self.logger.error("1. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            self.logger.error("2. ~/.aws/credentials file")
            self.logger.error("3. IAM role (if running on EC2)")
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'. Check permissions.")
            else:
                raise ValueError(f"Failed to access S3 bucket: {e}")

    def validate_source(self) -> bool:
        """
        Validate S3 bucket access and permissions.

        Performs comprehensive validation:
        1. Bucket exists and is accessible
        2. Required permissions (ListBucket, GetObject)
        3. Network connectivity
        4. Object availability in specified prefix

        Returns:
            bool: True if source is valid and accessible
        """
        try:
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)

            # Test object listing permissions
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix_filter,
                MaxKeys=1  # Just test permission, don't load everything
            )

            # Check if any objects exist
            if 'Contents' not in response:
                self.logger.warning(f"No objects found in bucket '{self.bucket_name}' with prefix '{self.prefix_filter}'")
                return False

            # Test object download permission
            first_object_key = response['Contents'][0]['Key']
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=first_object_key)
                self.logger.info(f"Source validation successful: {len(response.get('Contents', []))} objects accessible")
                return True
            except ClientError as e:
                self.logger.error(f"Cannot access objects in bucket: {e}")
                return False

        except ClientError as e:
            self.logger.error(f"Source validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            return False

    def extract_photo_metadata(self, source_identifier: str) -> PhotoMetadata:
        """
        Extract standardized metadata from S3 object.

        This method demonstrates the REFERENCE PATTERN for metadata extraction:
        1. Download object efficiently (streaming when possible)
        2. Use shared utilities for consistent EXIF processing
        3. Handle errors gracefully with meaningful messages
        4. Extract all standard metadata fields
        5. Include source-specific information

        Args:
            source_identifier: S3 object key

        Returns:
            PhotoMetadata: Standardized metadata structure

        Raises:
            ValueError: If object is not a valid image or cannot be processed
            RuntimeError: If S3 object is inaccessible
        """
        if not source_identifier:
            raise ValueError("S3 object key cannot be empty")

        try:
            # Get object metadata first (efficient, no data transfer)
            head_response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=source_identifier
            )

            file_size = head_response['ContentLength']
            s3_last_modified = head_response['LastModified']

            # Validate file size (prevent downloading huge files)
            max_file_size = 50 * 1024 * 1024  # 50MB limit
            if file_size > max_file_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {max_file_size})")

            # Check file extension
            filename = source_identifier.split('/')[-1]
            if not any(filename.lower().endswith(ext.lower()) for ext in self.file_extensions):
                raise ValueError(f"Unsupported file type: {filename}")

            # Download object data for processing
            self.logger.debug(f"Downloading S3 object: {source_identifier} ({file_size} bytes)")
            get_response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=source_identifier
            )
            image_data = get_response['Body'].read()

            # Extract EXIF data using shared utilities (ensures consistency)
            exif_data = self._extract_exif_data(image_data)

            # Extract timestamp from EXIF (prefer EXIF over S3 metadata)
            timestamp = None
            if 'DateTime' in exif_data:
                try:
                    timestamp = datetime.strptime(exif_data['DateTime'], '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    self.logger.warning(f"Invalid EXIF DateTime format: {exif_data['DateTime']}")

            # Fallback to S3 last modified if no EXIF timestamp
            if not timestamp:
                timestamp = s3_last_modified.replace(tzinfo=None)

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
                original_path=f"s3://{self.bucket_name}/{source_identifier}",
                file_size=file_size,
                created_at=timestamp,
                exif_data=exif_data,
                timestamp=timestamp,
                gps_coordinates=gps_coordinates,
                camera_make=camera_make if camera_make else None,
                camera_model=camera_model if camera_model else None,
                colors=colors,
                vision_analysis=vision_analysis,
                source_type="s3",
                processed_at=datetime.now()
            )

            self.logger.debug(f"Successfully extracted metadata for: {filename}")
            return metadata

        except (ValueError, RuntimeError):
            # Deliberate failures raised above (file too large, unsupported
            # type) pass through unchanged. See the note in
            # local_bulk_importer: the generic handler was flattening them.
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise RuntimeError(f"S3 object not found: {source_identifier}")
            elif error_code == 'AccessDenied':
                raise RuntimeError(f"Access denied to S3 object: {source_identifier}")
            else:
                raise RuntimeError(f"S3 error accessing {source_identifier}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to process image {source_identifier}: {str(e)}")

    # _perform_vision_analysis now lives on BulkImportTemplate so all three
    # importers share one implementation (and one set of vision counters).

    def group_into_inspections(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """
        Group photos into logical inspections using consistent algorithms.

        This method demonstrates the REFERENCE PATTERN for inspection grouping:
        1. Support multiple grouping strategies
        2. Use consistent date/location/manual logic
        3. Calculate confidence scores for groups
        4. Handle edge cases gracefully
        5. Provide detailed logging of grouping decisions

        Args:
            photos: List of processed photo metadata

        Returns:
            List[InspectionGroup]: Grouped inspections with confidence scores
        """
        if not photos:
            return []

        self.logger.info(f"Grouping {len(photos)} photos using strategy: {self.grouping_strategy.value}")

        # Sort photos by timestamp for consistent processing
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
        Group photos by date with intelligent same-day detection.

        Algorithm:
        1. Group photos taken on the same calendar day
        2. For multiple groups on same day, consider time gaps
        3. Calculate confidence based on temporal clustering

        Args:
            photos: Sorted list of photo metadata

        Returns:
            List[InspectionGroup]: Date-based inspection groups
        """
        groups = {}

        for photo in photos:
            photo_date = photo.timestamp or photo.created_at
            date_key = photo_date.date()

            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(photo)

        # Convert to InspectionGroup objects
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

            # Calculate confidence based on temporal clustering
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
        """
        Group photos by GPS location with clustering algorithm.

        Args:
            photos: Sorted list of photo metadata

        Returns:
            List[InspectionGroup]: Location-based inspection groups
        """
        # TODO: Implement location-based clustering
        # For now, fall back to date-based grouping
        self.logger.warning("Location-based grouping not yet implemented, using date-based")
        return self._group_by_date(photos)

    def _group_by_hybrid(self, photos: List[PhotoMetadata]) -> List[InspectionGroup]:
        """
        Group photos using hybrid date + location + time gap analysis.

        Args:
            photos: Sorted list of photo metadata

        Returns:
            List[InspectionGroup]: Hybrid inspection groups
        """
        # TODO: Implement hybrid grouping algorithm
        # For now, fall back to date-based grouping
        self.logger.warning("Hybrid grouping not yet implemented, using date-based")
        return self._group_by_date(photos)

    def _calculate_temporal_confidence(self, photos: List[PhotoMetadata]) -> float:
        """
        Calculate confidence score for temporal grouping.

        Higher confidence for:
        - Photos taken within a short time window
        - Consistent time intervals between photos
        - Reasonable inspection duration (not too long/short)

        Args:
            photos: Photos in the potential group

        Returns:
            float: Confidence score between 0.0 and 1.0
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

    def list_available_photos(self,
                            max_keys: int = 1000,
                            progress_callback: Optional[Callable] = None) -> List[str]:
        """
        List all available photos in the S3 bucket with filtering.

        Demonstrates efficient S3 listing patterns:
        1. Paginated listing to handle large buckets
        2. Client-side filtering by file extension
        3. Progress reporting for long operations
        4. Memory-efficient processing

        Args:
            max_keys: Maximum number of objects to return
            progress_callback: Optional callback for progress updates

        Returns:
            List[str]: S3 object keys for valid photo files
        """
        photo_keys = []
        continuation_token = None
        total_processed = 0

        try:
            while len(photo_keys) < max_keys:
                # Prepare list request
                list_kwargs = {
                    'Bucket': self.bucket_name,
                    'Prefix': self.prefix_filter,
                    'MaxKeys': min(1000, max_keys - len(photo_keys))  # S3 max per request
                }

                if continuation_token:
                    list_kwargs['ContinuationToken'] = continuation_token

                # List objects
                response = self.s3_client.list_objects_v2(**list_kwargs)

                if 'Contents' not in response:
                    break

                # Filter for image files
                for obj in response['Contents']:
                    key = obj['Key']
                    total_processed += 1

                    # Filter by file extension
                    if any(key.lower().endswith(ext.lower()) for ext in self.file_extensions):
                        photo_keys.append(key)

                        if len(photo_keys) >= max_keys:
                            break

                    # Report progress
                    if progress_callback and total_processed % 100 == 0:
                        progress_callback(total_processed, None, f"Scanned {total_processed} objects")

                # Check if there are more objects
                if not response.get('IsTruncated', False):
                    break

                continuation_token = response.get('NextContinuationToken')

            self.logger.info(f"Found {len(photo_keys)} photos out of {total_processed} objects scanned")
            return photo_keys

        except ClientError as e:
            self.logger.error(f"Failed to list S3 objects: {e}")
            raise RuntimeError(f"Cannot list objects in bucket {self.bucket_name}: {e}")

    def process_bulk_import(self,
                          source_list: Optional[List[str]] = None,
                          progress_callback: Optional[Callable] = None) -> ProcessingResult:
        """
        Process bulk import with S3-optimized performance patterns.

        Demonstrates advanced bulk processing:
        1. Automatic source discovery if not provided
        2. Concurrent processing with controlled parallelism
        3. Batch processing to manage memory usage
        4. Comprehensive error recovery and retry logic
        5. Detailed progress reporting and statistics

        Args:
            source_list: Optional list of S3 keys (auto-discovered if None)
            progress_callback: Optional callback for progress updates

        Returns:
            ProcessingResult: Comprehensive processing results
        """
        start_time = datetime.now()

        # Auto-discover sources if not provided
        if source_list is None:
            if progress_callback:
                progress_callback(0, None, "Discovering photos in S3 bucket...")

            source_list = self.list_available_photos(
                max_keys=10000,  # Reasonable limit for bulk import
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
                result.errors.append("S3 source validation failed")
                return result

            self.logger.info(f"Starting bulk import of {len(source_list)} photos from S3")

            # Process in batches with concurrent workers
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

            # Group photos into inspections
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
        Process a batch of photos concurrently with proper error handling.

        Args:
            batch: List of S3 object keys to process
            progress_callback: Optional progress callback

        Returns:
            List[tuple]: List of (PhotoMetadata, error) tuples
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(self._safe_extract_metadata, key): key
                for key in batch
            }

            # Collect results as they complete
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    metadata = future.result()
                    results.append((metadata, None))
                except Exception as e:
                    error_msg = f"Failed to process {key}: {str(e)}"
                    results.append((None, error_msg))
                    self.logger.error(error_msg)

        return results

    def _safe_extract_metadata(self, s3_key: str) -> PhotoMetadata:
        """
        Safely extract metadata with comprehensive error handling.

        Args:
            s3_key: S3 object key

        Returns:
            PhotoMetadata: Extracted metadata

        Raises:
            Exception: If extraction fails after all retries
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.extract_photo_metadata(s3_key)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Retry {attempt + 1}/{max_retries} for {s3_key}: {e}")


# Example usage and configuration patterns
def create_s3_bulk_importer(bucket_name: str,
                          aws_access_key_id: str = None,
                          aws_secret_access_key: str = None,
                          **kwargs) -> S3BulkImporter:
    """
    Factory function for creating S3 bulk importer with sensible defaults.

    This demonstrates the recommended way to configure the importer
    for different use cases.

    Args:
        bucket_name: S3 bucket name
        aws_access_key_id: Optional AWS access key
        aws_secret_access_key: Optional AWS secret key
        **kwargs: Additional configuration options

    Returns:
        S3BulkImporter: Configured importer instance
    """
    config = {
        'bucket_name': bucket_name,
        'grouping_strategy': 'date',
        'max_workers': 5,
        'batch_size': 10,
        'file_extensions': ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'],
        **kwargs
    }

    if aws_access_key_id and aws_secret_access_key:
        config.update({
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key
        })

    return S3BulkImporter(config)