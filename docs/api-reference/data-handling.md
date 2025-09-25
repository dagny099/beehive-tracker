# Data Handling API Reference

The data handling module manages data persistence, validation, export functionality, and inspection record management for the beehive tracker application.

!!! warning "🔴 Critical Gap - TODO"
    **This API reference needs complete documentation including:**
    - Complete data validation schemas and rules
    - Export format specifications and customization options
    - Database migration and upgrade patterns
    - Performance optimization for large datasets
    - Concurrent access and data integrity patterns

## Overview

The data handling system consists of multiple modules that work together to provide robust data management:

- `src/utils/data_handler.py`: Core data processing and validation
- `src/data_io.py`: Data persistence and export functionality
- `src/utils/session_manager.py`: Streamlit session state management

### Core Classes

**DataManager Class:**
```python
class DataManager:
    """Manager class for handling data storage operations."""

    def __init__(self, csv_file: str, json_file: str):
        """Initialize with storage file paths."""

    def save_entry(self, data: Dict[str, Any]) -> bool:
        """Save or update a metadata entry to both CSV and JSON storage."""

    def load_data(self) -> List[Dict[str, Any]]:
        """Load all inspection data from storage."""
```

### Primary Functions

**Inspection Data Management:**
```python
def add_photo_to_inspection(photo_data: Dict, inspection_id: str) -> bool:
    """Add photo data to existing inspection record.

    Args:
        photo_data: Complete photo metadata and analysis results
        inspection_id: Unique identifier for inspection session

    Returns:
        Boolean indicating success of operation
    """

def create_new_inspection(initial_photo: Dict) -> str:
    """Create new inspection record from first photo.

    Args:
        initial_photo: Photo data to initialize inspection

    Returns:
        Unique inspection ID for the new record
    """

def get_inspection_title(inspection_index: int) -> str:
    """Generate human-readable title for inspection."""
```

### Data Validation

**Input Validation Functions:**
```python
def validate_photo_metadata(metadata: Dict) -> Tuple[bool, List[str]]:
    """Validate photo metadata structure and content.

    Args:
        metadata: Photo metadata dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """

def sanitize_filename(filename: str) -> str:
    """Clean and sanitize uploaded filenames."""

def validate_gps_coordinates(lat: float, lng: float) -> bool:
    """Validate GPS coordinate values are within valid ranges."""
```

### Data Export Functions

**Export Capabilities:**
```python
def export_to_csv(data: List[Dict], output_path: str) -> bool:
    """Export inspection data to CSV format.

    Args:
        data: List of inspection records
        output_path: Path for CSV file

    Returns:
        Success status of export operation
    """

def export_to_json(data: List[Dict], output_path: str) -> bool:
    """Export inspection data to JSON format with full structure preservation."""

def export_filtered_data(
    data: List[Dict],
    filters: Dict[str, Any],
    format: str
) -> str:
    """Export data with applied filters."""
```

### Session Management

**Session State Functions:**
```python
def initialize_session_state() -> None:
    """Initialize all required session state variables."""

def clear_session_data() -> None:
    """Clear all session data safely."""

def backup_session_state() -> Dict[str, Any]:
    """Create backup of current session state."""

def restore_session_state(backup: Dict[str, Any]) -> bool:
    """Restore session state from backup."""
```

### Data Structures

**Inspection Record Structure:**
```python
{
    "inspection_id": "2024-03-15_001",
    "date": "2024-03-15T14:30:00Z",
    "location": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "address": "Approximate location string"
    },
    "photos": [
        {
            "filename": "hive1_inspection_001.jpg",
            "upload_timestamp": "2024-03-15T14:35:22Z",
            "exif_data": {...},
            "color_analysis": {...},
            "ai_analysis": {...},
            "weather_data": {...},
            "user_annotations": {...}
        }
    ],
    "summary": {
        "photo_count": 3,
        "average_temperature": 16.5,
        "dominant_colors": ["#D4A017", "#8B4513"],
        "overall_assessment": "Healthy hive condition"
    },
    "tags": ["spring", "inspection", "healthy"],
    "notes": "Strong population, good brood pattern observed"
}
```

### Storage Configuration

**File System Organization:**
```python
# Default storage paths
DEFAULT_PATHS = {
    "data_dir": "./data",
    "csv_file": "./data/hive_color_log.csv",
    "json_file": "./data/hive_color_log.json",
    "upload_dir": "./data/uploads",
    "thumbnail_dir": "./data/thumbnails",
    "export_dir": "./data/exports"
}
```

### Integration Examples

**Complete Data Processing Workflow:**
```python
def process_uploaded_photo(uploaded_file, user_annotations: Dict = None):
    """Complete workflow for processing uploaded inspection photo."""

    # Validate upload
    if not validate_uploaded_file(uploaded_file):
        return {"error": "Invalid file format"}

    # Extract and process metadata
    photo_data = {
        "filename": sanitize_filename(uploaded_file.name),
        "exif_data": extract_exif_data(uploaded_file),
        "color_analysis": analyze_colors(uploaded_file),
        "processing_timestamp": datetime.now().isoformat()
    }

    # Add user annotations if provided
    if user_annotations:
        photo_data["user_annotations"] = user_annotations

    # Save to inspection record
    inspection_id = get_or_create_inspection(photo_data)
    add_photo_to_inspection(photo_data, inspection_id)

    # Update session state
    update_session_with_photo(photo_data, inspection_id)

    return {
        "success": True,
        "inspection_id": inspection_id,
        "photo_data": photo_data
    }
```

### Error Handling and Recovery

**Data Integrity Functions:**
```python
def verify_data_integrity() -> Dict[str, Any]:
    """Check data consistency between JSON and CSV storage."""

def repair_corrupted_data(backup_path: str = None) -> bool:
    """Attempt to repair corrupted data files."""

def migrate_data_format(from_version: str, to_version: str) -> bool:
    """Migrate data between different schema versions."""
```

### Performance Optimization

**Large Dataset Handling:**
- **Lazy loading**: Load data incrementally for large collections
- **Indexing**: Create efficient lookup structures for quick access
- **Caching**: Store frequently accessed data in memory
- **Batch operations**: Process multiple records efficiently

**Memory Management:**
- **Data pagination**: Handle large datasets in chunks
- **Resource cleanup**: Proper file handle and memory management
- **Progress tracking**: Monitor progress for long-running operations

### Configuration Options

Data handling can be configured through environment variables:

```bash
# Storage configuration
DATA_DIRECTORY=./data
MAX_EXPORT_RECORDS=10000
BACKUP_RETENTION_DAYS=30

# Performance settings
BATCH_SIZE=100
CACHE_SIZE=1000
LAZY_LOADING=true
```

### Concurrent Access

**Thread Safety:**
- **File locking**: Prevent concurrent write operations
- **Session isolation**: Separate data for multiple user sessions
- **Atomic operations**: Ensure data consistency during updates

---

!!! info "🟡 Important Gap - TODO"
    **Missing documentation that needs to be added:**
    - Complete data validation schema reference
    - Export format customization and templating
    - Database migration procedures and version management
    - Performance tuning guidelines for large photo collections
    - Backup and recovery procedures
    - Data archiving and cleanup strategies
    - Integration patterns with cloud storage systems
    - Concurrent access patterns and locking mechanisms
    - Testing patterns for data integrity and validation