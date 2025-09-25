# Image Processing API Reference

The image processing module handles EXIF metadata extraction, color analysis, and image utilities for beehive inspection photos.

!!! warning "🔴 Critical Gap - TODO"
    **This API reference needs complete documentation including:**
    - Complete function signatures for all image processing functions
    - Color analysis algorithm details and parameters
    - EXIF data structure specifications
    - Performance optimization guidelines
    - Error handling for corrupted or unsupported images

## Overview

The `src/utils/image_processor.py` module provides comprehensive image analysis capabilities using PIL (Python Imaging Library) and ColorThief for advanced color extraction.

### Primary Functions

**EXIF Metadata Extraction:**
```python
def extract_exif_data(image_path: str) -> Dict[str, Any]:
    """Extract comprehensive EXIF metadata from image.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary containing EXIF data including GPS coordinates,
        camera settings, timestamps, and technical metadata.
    """
```

**Color Analysis:**
```python
def analyze_colors(image_path: str, num_colors: int = 5) -> Dict[str, Any]:
    """Analyze dominant colors in beehive inspection image.

    Args:
        image_path: Path to the image file
        num_colors: Number of colors to extract in palette

    Returns:
        Dictionary with dominant color, color palette, and
        color distribution analysis.
    """
```

### Key Features

- **Comprehensive EXIF extraction** including GPS, camera settings, and timestamps
- **Advanced color analysis** using ColorThief for dominant color identification
- **Color palette generation** with 5-color schemes for visual analysis
- **Image format support** for JPEG, PNG, TIFF, and other common formats
- **Error handling** for corrupted or incomplete image data

### EXIF Data Structure

Extracted EXIF data includes:

```python
{
    "datetime": "2024:03:15 14:30:00",
    "camera_make": "Canon",
    "camera_model": "EOS R5",
    "gps_coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "altitude": 10.0
    },
    "technical_settings": {
        "iso": 400,
        "aperture": "f/5.6",
        "shutter_speed": "1/125",
        "focal_length": "85mm"
    },
    "image_properties": {
        "width": 6720,
        "height": 4480,
        "format": "JPEG",
        "file_size": 8456789
    }
}
```

### Color Analysis Structure

Color analysis returns structured data:

```python
{
    "dominant_color": {
        "hex": "#D4A017",
        "rgb": [212, 160, 23],
        "color_name": "golden_honey"
    },
    "color_palette": [
        {"hex": "#D4A017", "rgb": [212, 160, 23]},
        {"hex": "#8B4513", "rgb": [139, 69, 19]},
        {"hex": "#F5DEB3", "rgb": [245, 222, 179]},
        {"hex": "#2F4F2F", "rgb": [47, 79, 47]},
        {"hex": "#000000", "rgb": [0, 0, 0]}
    ],
    "color_distribution": {
        "#D4A017": 35.2,
        "#8B4513": 22.1,
        "#F5DEB3": 18.7,
        "#2F4F2F": 15.3,
        "#000000": 8.7
    }
}
```

### Integration Examples

**Complete Image Analysis Workflow:**
```python
from src.utils.image_processor import extract_exif_data, analyze_colors

def process_inspection_photo(image_path: str) -> Dict[str, Any]:
    """Complete processing pipeline for inspection photo."""

    # Extract EXIF metadata
    exif_data = extract_exif_data(image_path)

    # Analyze colors
    color_data = analyze_colors(image_path)

    # Combine results
    return {
        "file_path": image_path,
        "exif": exif_data,
        "color_analysis": color_data,
        "processing_timestamp": datetime.now().isoformat()
    }
```

### Utility Functions

**Image Validation:**
```python
def validate_image(image_path: str) -> bool:
    """Validate that file is a supported image format."""

def get_image_info(image_path: str) -> Dict[str, Any]:
    """Get basic image information without full processing."""

def generate_thumbnail(image_path: str, size: Tuple[int, int]) -> str:
    """Generate thumbnail image for gallery views."""
```

### Error Handling

The image processing module handles various error scenarios:

- **Corrupted image files**: Graceful degradation with partial data
- **Missing EXIF data**: Returns available data with clear indication of missing fields
- **Unsupported formats**: Clear error messages with supported format list
- **Permission errors**: File access and permission handling

### Performance Considerations

**Optimization Strategies:**
- **Lazy loading**: Only process data when specifically requested
- **Caching**: Store processed results to avoid recomputation
- **Thumbnail generation**: Create smaller images for gallery views
- **Batch processing**: Efficient handling of multiple images

**Memory Management:**
- **Image resizing**: Reduce memory footprint for large images
- **Resource cleanup**: Proper image file handle management
- **Progress tracking**: Monitor processing for large batches

### Configuration Options

Image processing can be configured through environment variables:

```bash
# Maximum image size for processing (in pixels)
MAX_IMAGE_SIZE=4000

# Thumbnail size for gallery views
THUMBNAIL_SIZE=300

# Color analysis precision (1-10, higher = more accurate but slower)
COLOR_ANALYSIS_PRECISION=5
```

---

!!! info "🟡 Important Gap - TODO"
    **Missing documentation that needs to be added:**
    - Complete function reference with all parameters and return types
    - Color analysis algorithm explanation and accuracy considerations
    - EXIF field mapping and standardization details
    - Performance benchmarks and optimization guidelines
    - Batch processing patterns and memory management
    - Testing patterns for image processing functions
    - Integration with computer vision analysis
    - Custom color palette interpretation for beehive health assessment