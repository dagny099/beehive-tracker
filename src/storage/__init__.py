# Storage abstraction layer for Beehive Tracker

from .base import StorageProvider, StorageConfig
from .local_provider import LocalStorageProvider
from .manager import StorageManager, get_storage_manager, get_storage_provider
from .config import StorageConfiguration, get_storage_config

# Import cloud providers if available
try:
    from .s3_provider import S3StorageProvider
    __all__ = [
        'StorageProvider',
        'StorageConfig', 
        'LocalStorageProvider',
        'S3StorageProvider',
        'StorageManager',
        'StorageConfiguration',
        'get_storage_manager',
        'get_storage_provider',
        'get_storage_config'
    ]
except ImportError:
    __all__ = [
        'StorageProvider',
        'StorageConfig', 
        'LocalStorageProvider',
        'StorageManager',
        'StorageConfiguration',
        'get_storage_manager',
        'get_storage_provider',
        'get_storage_config'
    ]