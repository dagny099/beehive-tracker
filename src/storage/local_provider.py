"""
Local filesystem storage provider for Beehive Tracker.
Maintains backward compatibility with existing local storage implementation.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import io
import logging

from .base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_path = config.get("base_path", "data/uploads")
        self.create_dirs = config.get("create_dirs", True)
        self.preserve_structure = config.get("preserve_structure", True)
        
        # Ensure base directory exists
        if self.create_dirs:
            os.makedirs(self.base_path, exist_ok=True)
            
        # Create metadata directory for storing additional info
        self.metadata_path = os.path.join(os.path.dirname(self.base_path), "metadata")
        if self.create_dirs:
            os.makedirs(self.metadata_path, exist_ok=True)
    
    def _get_storage_path(self, 
                         filename: str, 
                         user_id: Optional[str] = None,
                         inspection_id: Optional[str] = None) -> str:
        """Generate storage path for a file"""
        if self.preserve_structure and user_id:
            if inspection_id:
                # Structure: base_path/users/user_id/inspections/inspection_id/filename
                return os.path.join(
                    self.base_path, "users", user_id, "inspections", inspection_id, filename
                )
            else:
                # Structure: base_path/users/user_id/filename
                return os.path.join(self.base_path, "users", user_id, filename)
        else:
            # Flat structure: base_path/filename
            return os.path.join(self.base_path, filename)
    
    def _get_metadata_path(self, storage_path: str) -> str:
        """Get metadata file path for a given storage path"""
        rel_path = os.path.relpath(storage_path, self.base_path)
        metadata_file = f"{rel_path}.json"
        return os.path.join(self.metadata_path, metadata_file)
    
    def _save_metadata(self, storage_path: str, metadata: Dict[str, Any]) -> bool:
        """Save metadata for a file"""
        try:
            metadata_file = self._get_metadata_path(storage_path)
            metadata_dir = os.path.dirname(metadata_file)
            
            if self.create_dirs:
                os.makedirs(metadata_dir, exist_ok=True)
            
            # Add storage provider info
            metadata.update({
                "storage_provider": self.provider_name,
                "storage_path": storage_path,
                "created_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(storage_path) if os.path.exists(storage_path) else 0
            })
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save metadata: {e}")
            return False
    
    def _load_metadata(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a file"""
        try:
            metadata_file = self._get_metadata_path(storage_path)
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load metadata: {e}")
        return None
    
    def upload_image(self, 
                    image_data: bytes, 
                    filename: str, 
                    user_id: Optional[str] = None,
                    inspection_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload image to local storage"""
        try:
            # Generate unique filename to avoid collisions
            timestamp = int(datetime.now().timestamp())
            safe_filename = f"{timestamp}_{filename}"
            
            storage_path = self._get_storage_path(safe_filename, user_id, inspection_id)
            storage_dir = os.path.dirname(storage_path)
            
            # Create directory if needed
            if self.create_dirs:
                os.makedirs(storage_dir, exist_ok=True)
            
            # Write image data to file
            with open(storage_path, 'wb') as f:
                f.write(image_data)
            
            # Save metadata
            if metadata:
                metadata.update({
                    "original_filename": filename,
                    "safe_filename": safe_filename,
                    "user_id": user_id,
                    "inspection_id": inspection_id
                })
                self._save_metadata(storage_path, metadata)
            
            # Generate thumbnail
            thumbnail_data = self.generate_thumbnail(image_data)
            thumbnail_path = None
            if thumbnail_data:
                thumbnail_filename = f"thumb_{safe_filename}"
                thumbnail_path = self._get_storage_path(thumbnail_filename, user_id, inspection_id)
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(thumbnail_data)
            
            return {
                "success": True,
                "storage_path": storage_path,
                "thumbnail_path": thumbnail_path,
                "url": f"file://{os.path.abspath(storage_path)}",
                "file_size": len(image_data),
                "provider": self.provider_name
            }
            
        except Exception as e:
            logging.error(f"Failed to upload image: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider_name
            }
    
    def download_image(self, storage_path: str) -> Optional[bytes]:
        """Download image from local storage"""
        try:
            if os.path.exists(storage_path):
                with open(storage_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            logging.error(f"Failed to download image: {e}")
        return None
    
    def delete_image(self, storage_path: str) -> bool:
        """Delete image from local storage"""
        try:
            # Delete main file
            if os.path.exists(storage_path):
                os.remove(storage_path)
            
            # Delete metadata
            metadata_file = self._get_metadata_path(storage_path)
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            # Delete thumbnail if exists
            dir_name = os.path.dirname(storage_path)
            filename = os.path.basename(storage_path)
            thumbnail_path = os.path.join(dir_name, f"thumb_{filename}")
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            return True
        except Exception as e:
            logging.error(f"Failed to delete image: {e}")
            return False
    
    def list_images(self, 
                   user_id: Optional[str] = None,
                   inspection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List images in local storage"""
        images = []
        
        try:
            search_path = self.base_path
            if user_id and self.preserve_structure:
                if inspection_id:
                    search_path = os.path.join(self.base_path, "users", user_id, "inspections", inspection_id)
                else:
                    search_path = os.path.join(self.base_path, "users", user_id)
            
            if not os.path.exists(search_path):
                return images
            
            # Walk through directory structure
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    # Skip thumbnails and metadata files
                    if file.startswith("thumb_") or file.endswith(".json"):
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    # Try to load metadata
                    metadata = self._load_metadata(file_path) or {}
                    
                    # Basic file info
                    stat = os.stat(file_path)
                    
                    images.append({
                        "filename": file,
                        "storage_path": file_path,
                        "file_size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "metadata": metadata,
                        "provider": self.provider_name
                    })
        
        except Exception as e:
            logging.error(f"Failed to list images: {e}")
        
        return images
    
    def get_image_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """Get URL for accessing image (file:// URL for local storage)"""
        if os.path.exists(storage_path):
            return f"file://{os.path.abspath(storage_path)}"
        return None
    
    def generate_thumbnail(self, 
                          image_data: bytes, 
                          size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
        """Generate thumbnail for image"""
        try:
            # Open image with PIL
            img = Image.open(io.BytesIO(image_data))
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail to bytes
            thumb_buffer = io.BytesIO()
            img.save(thumb_buffer, format='JPEG', quality=85)
            thumb_buffer.seek(0)
            
            return thumb_buffer.getvalue()
            
        except Exception as e:
            logging.error(f"Failed to generate thumbnail: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check local storage health"""
        try:
            # Check if base directory exists and is writable
            if not os.path.exists(self.base_path):
                if self.create_dirs:
                    os.makedirs(self.base_path, exist_ok=True)
                else:
                    return {
                        "healthy": False,
                        "error": f"Base path does not exist: {self.base_path}",
                        "provider": self.provider_name
                    }
            
            # Test write access
            test_file = os.path.join(self.base_path, ".health_check")
            with open(test_file, 'w') as f:
                f.write("health_check")
            os.remove(test_file)
            
            return {
                "healthy": True,
                "base_path": os.path.abspath(self.base_path),
                "writable": True,
                "provider": self.provider_name,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": self.provider_name,
                "checked_at": datetime.now().isoformat()
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        stats = super().get_storage_stats()
        
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if not file.startswith("thumb_") and not file.endswith(".json"):
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            stats.update({
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "base_path": os.path.abspath(self.base_path)
            })
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats