"""
Amazon S3 storage provider for Beehive Tracker.
Implements scalable cloud storage with security, progress tracking, and performance optimizations.
"""

import os
import io
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Callable
from PIL import Image

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from boto3.s3.transfer import TransferConfig
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .base import StorageProvider


class S3StorageProvider(StorageProvider):
    """Amazon S3 cloud storage implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        # S3 configuration
        self.bucket_name = config.get("bucket_name")
        self.region = config.get("region", "us-east-1")
        self.use_ssl = config.get("use_ssl", True)
        self.create_bucket = config.get("create_bucket", False)
        self.storage_class = config.get("storage_class", "STANDARD")
        self.server_side_encryption = config.get("server_side_encryption", "AES256")
        
        # Performance settings
        self.multipart_threshold = config.get("multipart_threshold_mb", 8) * 1024 * 1024
        self.max_concurrency = config.get("max_concurrency", 10)
        self.chunk_size = config.get("chunk_size_mb", 8) * 1024 * 1024
        
        # Initialize S3 client
        self._init_s3_client(config)
        
        # Validate and setup bucket
        if self.bucket_name:
            self._setup_bucket()
    
    def _init_s3_client(self, config: Dict[str, Any]):
        """Initialize S3 client with credentials"""
        session_config = {
            "region_name": self.region,
            "use_ssl": self.use_ssl
        }
        
        # Handle credentials
        if config.get("aws_access_key_id") and config.get("aws_secret_access_key"):
            session_config.update({
                "aws_access_key_id": config["aws_access_key_id"],
                "aws_secret_access_key": config["aws_secret_access_key"]
            })
            if config.get("aws_session_token"):
                session_config["aws_session_token"] = config["aws_session_token"]
        
        self.s3_client = boto3.client('s3', **session_config)
        self.s3_resource = boto3.resource('s3', **session_config)
    
    def _setup_bucket(self):
        """Setup and validate S3 bucket"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logging.info(f"S3 bucket '{self.bucket_name}' is accessible")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404' and self.create_bucket:
                # Create bucket
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    # Configure bucket for security
                    self._configure_bucket_security()
                    
                    logging.info(f"Created S3 bucket: {self.bucket_name}")
                    
                except ClientError as create_error:
                    logging.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logging.error(f"S3 bucket access failed: {e}")
                raise
    
    def _configure_bucket_security(self):
        """Configure bucket security settings"""
        try:
            # Block public access
            self.s3_client.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            # Enable versioning for data protection
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Set default encryption
            self.s3_client.put_bucket_encryption(
                Bucket=self.bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': self.server_side_encryption
                        }
                    }]
                }
            )
            
            logging.info(f"Configured security for bucket: {self.bucket_name}")
            
        except ClientError as e:
            logging.warning(f"Failed to configure bucket security: {e}")
    
    def _get_s3_key(self, filename: str, user_id: Optional[str] = None, inspection_id: Optional[str] = None) -> str:
        """Generate S3 key for file organization"""
        # Create structured path: users/{user_id}/inspections/{inspection_id}/filename
        if user_id:
            if inspection_id:
                return f"users/{user_id}/inspections/{inspection_id}/{filename}"
            else:
                return f"users/{user_id}/{filename}"
        else:
            return f"shared/{filename}"
    
    def _upload_with_progress(self, 
                             image_data: bytes, 
                             s3_key: str,
                             progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Upload with progress tracking and error recovery"""
        try:
            # Configure transfer settings
            transfer_config = TransferConfig(
                multipart_threshold=self.multipart_threshold,
                max_concurrency=self.max_concurrency,
                multipart_chunksize=self.chunk_size,
                use_threads=True
            )
            
            # Prepare upload parameters
            extra_args = {
                'StorageClass': self.storage_class,
                'ServerSideEncryption': self.server_side_encryption,
                'ContentType': 'image/jpeg'  # Default, could be dynamic
            }
            
            # Upload with progress callback
            file_obj = io.BytesIO(image_data)
            
            if progress_callback:
                # Wrap with progress tracking
                def progress_wrapper(bytes_transferred):
                    progress_callback(bytes_transferred, len(image_data))
                
                self.s3_client.upload_fileobj(
                    file_obj, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs=extra_args,
                    Config=transfer_config,
                    Callback=progress_wrapper
                )
            else:
                self.s3_client.upload_fileobj(
                    file_obj, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs=extra_args,
                    Config=transfer_config
                )
            
            # Get object metadata
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                "success": True,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "size": response['ContentLength'],
                "etag": response['ETag'],
                "last_modified": response['LastModified'].isoformat(),
                "storage_class": response.get('StorageClass', self.storage_class)
            }
            
        except ClientError as e:
            logging.error(f"S3 upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_image(self, 
                    image_data: bytes, 
                    filename: str, 
                    user_id: Optional[str] = None,
                    inspection_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None,
                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Upload image to S3 with progress tracking"""
        try:
            # Generate unique filename
            timestamp = int(datetime.now().timestamp())
            safe_filename = f"{timestamp}_{filename}"
            s3_key = self._get_s3_key(safe_filename, user_id, inspection_id)
            
            # Upload main image
            upload_result = self._upload_with_progress(image_data, s3_key, progress_callback)
            
            if not upload_result.get("success"):
                return {
                    "success": False,
                    "error": upload_result.get("error", "Upload failed"),
                    "provider": self.provider_name
                }
            
            # Generate and upload thumbnail
            thumbnail_data = self.generate_thumbnail(image_data)
            thumbnail_key = None
            
            if thumbnail_data:
                thumbnail_filename = f"thumb_{safe_filename}"
                thumbnail_key = self._get_s3_key(thumbnail_filename, user_id, inspection_id)
                
                thumb_result = self._upload_with_progress(thumbnail_data, thumbnail_key)
                if not thumb_result.get("success"):
                    logging.warning(f"Thumbnail upload failed: {thumb_result.get('error')}")
            
            # Store metadata as S3 object tags if provided
            if metadata:
                try:
                    # Convert metadata to S3 tags (limited to 50 chars per key/value)
                    tags = []
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float)):
                            tag_key = str(key)[:50]
                            tag_value = str(value)[:50]
                            tags.append({'Key': tag_key, 'Value': tag_value})
                    
                    if tags:
                        self.s3_client.put_object_tagging(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            Tagging={'TagSet': tags}
                        )
                        
                except ClientError as e:
                    logging.warning(f"Failed to set S3 tags: {e}")
            
            return {
                "success": True,
                "storage_path": s3_key,
                "thumbnail_path": thumbnail_key,
                "url": f"s3://{self.bucket_name}/{s3_key}",
                "file_size": len(image_data),
                "provider": self.provider_name,
                "bucket": self.bucket_name,
                "region": self.region,
                "s3_metadata": upload_result
            }
            
        except Exception as e:
            logging.error(f"S3 upload error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider_name
            }
    
    def download_image(self, storage_path: str) -> Optional[bytes]:
        """Download image from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_path)
            return response['Body'].read()
            
        except ClientError as e:
            logging.error(f"S3 download failed: {e}")
            return None
    
    def delete_image(self, storage_path: str) -> bool:
        """Delete image from S3"""
        try:
            # Delete main image
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_path)
            
            # Try to delete thumbnail
            if not storage_path.startswith('thumb_'):
                parts = storage_path.split('/')
                parts[-1] = f"thumb_{parts[-1]}"
                thumbnail_key = '/'.join(parts)
                
                try:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=thumbnail_key)
                except ClientError:
                    pass  # Thumbnail might not exist
            
            return True
            
        except ClientError as e:
            logging.error(f"S3 delete failed: {e}")
            return False
    
    def list_images(self, 
                   user_id: Optional[str] = None,
                   inspection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List images in S3"""
        images = []
        
        try:
            # Determine prefix for filtering
            if user_id:
                if inspection_id:
                    prefix = f"users/{user_id}/inspections/{inspection_id}/"
                else:
                    prefix = f"users/{user_id}/"
            else:
                prefix = ""
            
            # Paginate through objects
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get('Contents', []):
                    # Skip thumbnails and directories
                    if obj['Key'].endswith('/') or '/thumb_' in obj['Key']:
                        continue
                    
                    # Try to get object tags (metadata)
                    tags = {}
                    try:
                        tag_response = self.s3_client.get_object_tagging(
                            Bucket=self.bucket_name, Key=obj['Key']
                        )
                        tags = {tag['Key']: tag['Value'] for tag in tag_response['TagSet']}
                    except ClientError:
                        pass
                    
                    images.append({
                        "filename": obj['Key'].split('/')[-1],
                        "storage_path": obj['Key'],
                        "file_size": obj['Size'],
                        "created_at": obj['LastModified'].isoformat(),
                        "modified_at": obj['LastModified'].isoformat(),
                        "metadata": tags,
                        "provider": self.provider_name,
                        "bucket": self.bucket_name,
                        "storage_class": obj.get('StorageClass', 'STANDARD'),
                        "etag": obj['ETag']
                    })
        
        except ClientError as e:
            logging.error(f"S3 list failed: {e}")
        
        return images
    
    def get_image_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """Get pre-signed URL for S3 object"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': storage_path},
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logging.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def generate_thumbnail(self, 
                          image_data: bytes, 
                          size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
        """Generate thumbnail (same as local provider)"""
        try:
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumb_buffer = io.BytesIO()
            img.save(thumb_buffer, format='JPEG', quality=85)
            thumb_buffer.seek(0)
            
            return thumb_buffer.getvalue()
            
        except Exception as e:
            logging.error(f"Thumbnail generation failed: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check S3 connectivity and permissions"""
        try:
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Test write permission with small object
            test_key = "_health_check_" + str(int(datetime.now().timestamp()))
            test_data = b"health_check"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=test_data
            )
            
            # Clean up test object
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            
            return {
                "healthy": True,
                "bucket": self.bucket_name,
                "region": self.region,
                "writable": True,
                "provider": self.provider_name,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": self.provider_name,
                "bucket": self.bucket_name,
                "checked_at": datetime.now().isoformat()
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get S3 storage usage statistics"""
        stats = super().get_storage_stats()
        
        try:
            total_size = 0
            file_count = 0
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name):
                for obj in page.get('Contents', []):
                    if not obj['Key'].endswith('/'):
                        total_size += obj['Size']
                        file_count += 1
            
            # Get bucket region for cost estimation
            bucket_location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            region = bucket_location.get('LocationConstraint', 'us-east-1')
            
            # Rough cost estimation (varies by region)
            monthly_storage_cost = (total_size / (1024**3)) * 0.023  # ~$0.023/GB/month
            
            stats.update({
                "total_size": total_size,
                "total_size_gb": round(total_size / (1024**3), 3),
                "file_count": file_count,
                "bucket": self.bucket_name,
                "region": region,
                "estimated_monthly_cost_usd": round(monthly_storage_cost, 2),
                "storage_class": self.storage_class
            })
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats