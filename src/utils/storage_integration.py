"""
Storage integration layer for Streamlit app.
Bridges the gap between existing data_handler.py and new storage abstraction.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import storage abstraction
try:
    from storage import get_storage_provider, get_storage_config
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    logging.warning("Storage abstraction not available - falling back to original implementation")


def get_current_storage_provider():
    """Get the currently configured storage provider"""
    if not STORAGE_AVAILABLE:
        return None
    
    try:
        return get_storage_provider()
    except Exception as e:
        logging.error(f"Failed to get storage provider: {e}")
        return None


def upload_image_with_storage(image_data: bytes, 
                             filename: str,
                             user_id: Optional[str] = None,
                             inspection_id: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Upload image using storage abstraction layer
    
    Returns:
        Dict with upload results compatible with existing code
    """
    provider = get_current_storage_provider()
    
    if not provider:
        # Fallback to original local storage behavior
        return _fallback_local_upload(image_data, filename)
    
    try:
        # Use storage abstraction
        result = provider.upload_image(
            image_data=image_data,
            filename=filename,
            user_id=user_id,
            inspection_id=inspection_id,
            metadata=metadata
        )
        
        if result.get("success"):
            # Convert to format expected by existing code
            return {
                "success": True,
                "file_path": result.get("storage_path", ""),
                "storage_url": result.get("url", ""),
                "file_size": result.get("file_size", len(image_data)),
                "provider": result.get("provider", "unknown"),
                "thumbnail_path": result.get("thumbnail_path")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Upload failed"),
                "provider": result.get("provider", "unknown")
            }
    
    except Exception as e:
        logging.error(f"Storage upload failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": "error"
        }


def download_image_with_storage(storage_path: str) -> Optional[bytes]:
    """Download image using storage abstraction layer"""
    provider = get_current_storage_provider()
    
    if not provider:
        # Fallback to local file reading
        return _fallback_local_download(storage_path)
    
    try:
        return provider.download_image(storage_path)
    except Exception as e:
        logging.error(f"Storage download failed: {e}")
        return None


def delete_image_with_storage(storage_path: str) -> bool:
    """Delete image using storage abstraction layer"""
    provider = get_current_storage_provider()
    
    if not provider:
        # Fallback to local file deletion
        return _fallback_local_delete(storage_path)
    
    try:
        return provider.delete_image(storage_path)
    except Exception as e:
        logging.error(f"Storage delete failed: {e}")
        return False


def get_image_url_with_storage(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """Get image URL using storage abstraction layer"""
    provider = get_current_storage_provider()
    
    if not provider:
        # Fallback to local file URL
        return f"file://{storage_path}"
    
    try:
        return provider.get_image_url(storage_path, expires_in)
    except Exception as e:
        logging.error(f"Failed to get image URL: {e}")
        return None


def list_user_images(user_id: Optional[str] = None, 
                    inspection_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List images for a user using storage abstraction"""
    provider = get_current_storage_provider()
    
    if not provider:
        return []
    
    try:
        return provider.list_images(user_id=user_id, inspection_id=inspection_id)
    except Exception as e:
        logging.error(f"Failed to list images: {e}")
        return []


def get_storage_health_status() -> Dict[str, Any]:
    """Get current storage provider health status"""
    provider = get_current_storage_provider()
    
    if not provider:
        return {
            "healthy": False,
            "provider": "none",
            "error": "No storage provider available"
        }
    
    try:
        return provider.health_check()
    except Exception as e:
        return {
            "healthy": False,
            "provider": provider.__class__.__name__,
            "error": str(e)
        }


def get_storage_info() -> Dict[str, Any]:
    """Get storage configuration and status information"""
    if not STORAGE_AVAILABLE:
        return {
            "available": False,
            "provider": "fallback",
            "config": "local_only"
        }
    
    try:
        config = get_storage_config()
        provider = get_current_storage_provider()
        
        info = {
            "available": True,
            "provider_type": config.get_config().get("provider_type", "unknown"),
            "health": get_storage_health_status()
        }
        
        if provider:
            info["stats"] = provider.get_storage_stats()
            info["provider_class"] = provider.__class__.__name__
        
        return info
        
    except Exception as e:
        return {
            "available": True,
            "error": str(e),
            "provider": "error"
        }


# Fallback functions for when storage abstraction is not available
def _fallback_local_upload(image_data: bytes, filename: str) -> Dict[str, Any]:
    """Fallback local upload when storage abstraction unavailable"""
    import os
    from datetime import datetime
    
    try:
        # Create uploads directory
        upload_dir = os.path.join("data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = int(datetime.now().timestamp())
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return {
            "success": True,
            "file_path": file_path,
            "storage_url": f"file://{os.path.abspath(file_path)}",
            "file_size": len(image_data),
            "provider": "fallback_local"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": "fallback_local"
        }


def _fallback_local_download(file_path: str) -> Optional[bytes]:
    """Fallback local download"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
    except Exception as e:
        logging.error(f"Fallback download failed: {e}")
    return None


def _fallback_local_delete(file_path: str) -> bool:
    """Fallback local delete"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        logging.error(f"Fallback delete failed: {e}")
    return False


# Session state helpers for storage integration
def init_storage_session_state():
    """Initialize storage-related session state variables"""
    if 'storage_provider_type' not in st.session_state:
        info = get_storage_info()
        st.session_state.storage_provider_type = info.get("provider_type", "local")
    
    if 'storage_health' not in st.session_state:
        st.session_state.storage_health = get_storage_health_status()


def update_storage_session_state():
    """Update storage session state with current information"""
    st.session_state.storage_health = get_storage_health_status()
    
    info = get_storage_info()
    st.session_state.storage_provider_type = info.get("provider_type", "local")
    st.session_state.storage_stats = info.get("stats", {})


def display_storage_status():
    """Display storage status in Streamlit sidebar"""
    with st.sidebar:
        st.markdown("### Storage Status")
        
        info = get_storage_info()
        
        if info.get("available"):
            provider_type = info.get("provider_type", "unknown")
            health = info.get("health", {})
            
            if health.get("healthy"):
                st.success(f"✅ {provider_type.title()} storage active")
            else:
                st.error(f"❌ {provider_type.title()} storage unhealthy")
                if "error" in health:
                    st.error(f"Error: {health['error']}")
            
            # Show storage stats if available
            stats = info.get("stats", {})
            if stats:
                if "total_size_mb" in stats:
                    st.metric("Storage Used", f"{stats['total_size_mb']} MB")
                if "file_count" in stats:
                    st.metric("Files", stats['file_count'])
        else:
            st.warning("⚠️ Using fallback local storage")


# Migration helpers
def migrate_to_cloud_storage(target_provider: str = "s3", 
                           user_id: Optional[str] = None) -> Dict[str, Any]:
    """Helper function to migrate data to cloud storage"""
    if not STORAGE_AVAILABLE:
        return {"success": False, "error": "Storage abstraction not available"}
    
    try:
        from storage import get_storage_manager
        
        manager = get_storage_manager()
        
        # Migrate from current provider to target
        current_provider = get_storage_config().get_config().get("provider_type", "local")
        
        if current_provider == target_provider:
            return {"success": False, "error": f"Already using {target_provider}"}
        
        result = manager.migrate_data(
            from_provider=current_provider,
            to_provider=target_provider,
            user_id=user_id
        )
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def switch_storage_provider(provider_type: str) -> Dict[str, Any]:
    """Switch to a different storage provider"""
    if not STORAGE_AVAILABLE:
        return {"success": False, "error": "Storage abstraction not available"}
    
    try:
        config = get_storage_config()
        success = config.set_provider(provider_type, save=True)
        
        if success:
            # Update session state
            update_storage_session_state()
            return {"success": True, "provider": provider_type}
        else:
            return {"success": False, "error": f"Failed to switch to {provider_type}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}