# Vision API Integration Documentation

## Overview
The `BeeVisionAnalyzer` class provides a comprehensive interface to Google Cloud Vision API, specifically optimized for analyzing beehive inspection photographs.

## Class: BeeVisionAnalyzer

**Location**: `src/api_services/vision.py`

### Initialization

```python
from src.api_services.vision import BeeVisionAnalyzer

analyzer = BeeVisionAnalyzer()
```

**Requirements**:
- Google Cloud credentials set via `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Vision API enabled in Google Cloud Project

### Methods

#### `analyze_image(image_data: Union[bytes, str]) -> Dict[str, Any]`

Performs comprehensive image analysis using multiple Vision API features.

**Parameters**:
- `image_data`: Raw image bytes or file path to image
- `config` (optional): Analysis configuration dictionary

**Returns**:
```python
{
    "status": "success" | "error",
    "analysis_results": {
        "labels": List[Dict],          # Object/scene labels with confidence
        "objects": List[Dict],         # Object detection with bounding boxes
        "text": List[Dict],            # Detected text elements
        "colors": List[Dict],          # Dominant color analysis
        "crop_hints": List[Dict],      # Suggested crop regions
        "web_entities": List[Dict]     # Related web content
    },
    "bee_specific_insights": {
        "bee_confidence": float,       # Overall bee-related confidence (0-1)
        "honey_area_ratio": float,     # Estimated honey coverage (0-1)
        "brood_area_ratio": float,     # Estimated brood coverage (0-1)
        "geometric_patterns": List[Dict]  # Detected hexagonal patterns
    },
    "metadata": {
        "processing_time_ms": int,
        "api_calls_made": int,
        "image_dimensions": Tuple[int, int]
    },
    "error_message": Optional[str]     # Present only if status == "error"
}
```

**Example Usage**:
```python
# Analyze from file path
result = analyzer.analyze_image("/path/to/hive_photo.jpg")

# Analyze from bytes
with open("hive_photo.jpg", "rb") as f:
    result = analyzer.analyze_image(f.read())

# Check for bee-related content
if result["status"] == "success":
    bee_confidence = result["bee_specific_insights"]["bee_confidence"]
    if bee_confidence > 0.7:
        print("High confidence bee-related image detected!")
```

#### `get_beekeeping_insights(analysis_results: Dict) -> Dict[str, Any]`

Extracts beekeeping-specific insights from Vision API results.

**Parameters**:
- `analysis_results`: Raw Vision API analysis results

**Returns**:
```python
{
    "honey_indicators": {
        "color_matches": List[Dict],    # Colors matching honey spectrum
        "coverage_estimate": float,     # Percentage of image (0-1)
        "confidence": float            # Detection confidence (0-1)
    },
    "brood_indicators": {
        "color_matches": List[Dict],    # Colors matching brood cells
        "pattern_matches": List[Dict],  # Geometric patterns found
        "development_stage": str       # "eggs", "larvae", "capped", "unknown"
    },
    "health_indicators": {
        "normal_patterns": bool,        # Hexagonal cell structure detected
        "color_consistency": float,     # Color uniformity (0-1)
        "potential_issues": List[str]   # Detected anomalies
    },
    "bee_population": {
        "visible_bees": int,           # Number of individual bees detected
        "density_estimate": str,       # "low", "medium", "high"
        "activity_indicators": List[str]
    }
}
```

**Example Usage**:
```python
analysis = analyzer.analyze_image("hive_inspection.jpg")
if analysis["status"] == "success":
    insights = analyzer.get_beekeeping_insights(analysis["analysis_results"])
    
    print(f"Honey coverage: {insights['honey_indicators']['coverage_estimate']:.1%}")
    print(f"Visible bees: {insights['bee_population']['visible_bees']}")
    
    if insights["health_indicators"]["potential_issues"]:
        print("⚠️  Potential issues detected:")
        for issue in insights["health_indicators"]["potential_issues"]:
            print(f"  - {issue}")
```

## Configuration Options

### Analysis Configuration
```python
config = {
    "confidence_threshold": 0.5,        # Minimum confidence for results
    "max_results": 20,                  # Maximum results per feature
    "enable_web_detection": True,       # Include web entity detection
    "enable_crop_hints": True,          # Include crop suggestions
    "color_analysis_depth": "detailed"  # "basic", "detailed", "comprehensive"
}

result = analyzer.analyze_image(image_data, config=config)
```

### Beekeeping-Specific Settings
```python
beekeeping_config = {
    "honey_color_ranges": [             # RGB ranges for honey detection
        [(200, 150, 50), (255, 220, 100)],   # Light honey
        [(180, 120, 30), (220, 160, 70)]     # Dark honey
    ],
    "brood_color_ranges": [             # RGB ranges for brood detection
        [(240, 230, 220), (255, 255, 255)],  # White/pale brood
        [(200, 180, 160), (230, 210, 190)]   # Slightly darker brood
    ],
    "geometric_pattern_threshold": 0.3,  # Hexagon detection sensitivity
    "bee_detection_min_size": 50        # Minimum pixels for bee detection
}
```

## Error Handling

### Common Errors and Solutions

#### Authentication Errors
```python
try:
    result = analyzer.analyze_image(image_data)
except GoogleCloudError as e:
    if "permission denied" in str(e).lower():
        print("❌ Check Google Cloud credentials and Vision API access")
    elif "quota exceeded" in str(e).lower():
        print("❌ Vision API quota exceeded - implement rate limiting")
```

#### Image Format Errors
```python
def validate_image(image_data: bytes) -> bool:
    """
    Validate image format and size before Vision API call.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        bool: True if image is valid for Vision API
        
    Raises:
        ValueError: If image is invalid with specific reason
    """
    if len(image_data) > 20 * 1024 * 1024:  # 20MB limit
        raise ValueError("Image too large (max 20MB)")
    
    # Check for valid image headers
    if not (image_data.startswith(b'\xff\xd8\xff') or  # JPEG
            image_data.startswith(b'\x89PNG\r\n') or     # PNG
            image_data.startswith(b'GIF8')):             # GIF
        raise ValueError("Unsupported image format")
    
    return True
```

### Rate Limiting Strategy
```python
import time
from functools import wraps

def rate_limit_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for automatic retry with exponential backoff."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except GoogleCloudError as e:
                    if "quota exceeded" in str(e).lower() and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"Rate limited, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    raise
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Apply to methods
@rate_limit_retry(max_retries=3)
def analyze_with_retry(self, image_data):
    return self.analyze_image(image_data)
```

## Performance Optimization

### Batch Processing
```python
def analyze_multiple_images(self, image_paths: List[str], 
                          batch_size: int = 5) -> List[Dict]:
    """
    Analyze multiple images with rate limiting and batch processing.
    
    Args:
        image_paths: List of paths to images
        batch_size: Number of concurrent requests
        
    Returns:
        List of analysis results in same order as input
    """
    results = []
    
    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i:i + batch_size]
        batch_results = []
        
        for path in batch:
            try:
                result = self.analyze_image(path)
                batch_results.append(result)
                time.sleep(0.1)  # Prevent rate limiting
            except Exception as e:
                batch_results.append({
                    "status": "error",
                    "error_message": str(e),
                    "image_path": path
                })
        
        results.extend(batch_results)
        
        if i + batch_size < len(image_paths):
            time.sleep(1.0)  # Pause between batches
    
    return results
```

### Caching Results
```python
import json
from pathlib import Path
from typing import Optional

class CachedBeeVisionAnalyzer(BeeVisionAnalyzer):
    """Vision analyzer with result caching for development."""
    
    def __init__(self, cache_dir: str = "./cache/vision_results"):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, image_data: bytes) -> Path:
        """Generate cache file path based on image hash."""
        import hashlib
        image_hash = hashlib.md5(image_data).hexdigest()
        return self.cache_dir / f"{image_hash}.json"
    
    def analyze_image(self, image_data: Union[bytes, str]) -> Dict[str, Any]:
        """Analyze with caching support."""
        if isinstance(image_data, str):
            with open(image_data, 'rb') as f:
                image_bytes = f.read()
        else:
            image_bytes = image_data
        
        cache_path = self._get_cache_path(image_bytes)
        
        # Check cache first
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    cached_result = json.load(f)
                    cached_result["_from_cache"] = True
                    return cached_result
            except (json.JSONDecodeError, IOError):
                pass  # Fall through to API call
        
        # Make API call
        result = super().analyze_image(image_data)
        
        # Cache successful results
        if result.get("status") == "success":
            try:
                with open(cache_path, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            except IOError:
                pass  # Don't fail if caching fails
        
        return result
```

## Testing

See [Testing Documentation](../DOCUMENTATION_AND_TESTING_PLAN.md#221-vision-api-testing-test_vision_apipy) for comprehensive testing strategies including:

- Mock API response testing
- Error condition testing  
- Performance benchmarking
- Integration testing with real images

## Monitoring and Logging

### Usage Metrics
```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MonitoredBeeVisionAnalyzer(BeeVisionAnalyzer):
    """Vision analyzer with monitoring and usage tracking."""
    
    def __init__(self):
        super().__init__()
        self.api_calls_today = 0
        self.total_processing_time = 0
    
    def analyze_image(self, image_data: Union[bytes, str]) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        
        try:
            result = super().analyze_image(image_data)
            
            # Log successful analysis
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.total_processing_time += processing_time
            self.api_calls_today += 1
            
            logger.info(f"Vision API call successful", extra={
                "processing_time_s": processing_time,
                "api_calls_today": self.api_calls_today,
                "bee_confidence": result.get("bee_specific_insights", {}).get("bee_confidence", 0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Vision API call failed", extra={
                "error": str(e),
                "processing_time_s": (datetime.utcnow() - start_time).total_seconds()
            })
            raise
```

## API Quotas and Limits

### Google Cloud Vision API Limits
- **Rate Limit**: 600 requests per minute per project
- **Daily Quota**: 1,000,000 requests per day (default)
- **Image Size**: Maximum 20MB per image
- **Batch Size**: Up to 16 images per batch request

### Cost Optimization
- Use appropriate feature selection (don't request unused features)
- Implement client-side image compression
- Cache results for repeated analysis
- Consider using lower resolution for initial screening

## Integration Examples

### Streamlit Integration
```python
import streamlit as st
from src.api_services.vision import BeeVisionAnalyzer

@st.cache_data
def analyze_uploaded_image(image_bytes: bytes) -> Dict[str, Any]:
    """Cached image analysis for Streamlit."""
    analyzer = BeeVisionAnalyzer()
    return analyzer.analyze_image(image_bytes)

# In Streamlit app
uploaded_file = st.file_uploader("Choose a hive photo", type=['jpg', 'png'])
if uploaded_file is not None:
    with st.spinner("Analyzing image..."):
        result = analyze_uploaded_image(uploaded_file.read())
        
        if result["status"] == "success":
            st.success("Analysis complete!")
            
            # Display insights
            insights = result["bee_specific_insights"]
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Bee Confidence", f"{insights['bee_confidence']:.1%}")
            with col2:
                st.metric("Honey Coverage", f"{insights['honey_area_ratio']:.1%}")
            with col3:
                st.metric("Brood Coverage", f"{insights['brood_area_ratio']:.1%}")
```