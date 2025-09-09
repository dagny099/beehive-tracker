# Vision API

The Vision API module integrates with Google Cloud Vision API to provide computer vision analysis of beehive photos, enabling automated detection of bees, honeycomb patterns, and hive conditions.

## Module Overview

::: src.api_services.vision

## Key Features

### 🐝 Bee Detection
Automatically identifies and counts bees in uploaded photos using advanced object detection algorithms.

### 🍯 Honeycomb Analysis
Analyzes honeycomb patterns, cell structure, and honey presence to assess hive health and productivity.

### 📝 Text Recognition
Extracts text from hive labels, dates, and annotations visible in photos using OCR capabilities.

### 🛡️ Content Safety
Ensures uploaded images are appropriate for analysis through Google's SafeSearch detection.

## Configuration

### Environment Variables

The Vision API requires proper authentication configuration:

```bash
# Required: Path to Google Cloud service account key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Optional: Google Cloud Project ID
PROJECT_ID=your-gcp-project-id
```

### API Quotas

Be aware of Google Cloud Vision API quotas and limits:

| Feature | Quota | Notes |
|---------|-------|-------|
| **Object Localization** | 600 requests/minute | Bee and equipment detection |
| **Text Detection** | 600 requests/minute | Hive label recognition |
| **Safe Search** | 600 requests/minute | Content filtering |
| **Label Detection** | 600 requests/minute | General image classification |

## Usage Examples

### Basic Image Analysis

```python
from src.api_services.vision import analyze_image

# Analyze a beehive photo
with open("beehive_photo.jpg", "rb") as image_file:
    results = analyze_image(image_file.read())
    
print(f"Detected objects: {len(results['objects'])}")
print(f"Confidence scores: {[obj['confidence'] for obj in results['objects']]}")
```

### Bee Detection and Counting

```python
# Specific bee detection
bee_results = detect_bees(image_data)

for detection in bee_results:
    print(f"Bee detected at: {detection['location']}")
    print(f"Confidence: {detection['confidence']:.2%}")
```

### Text Extraction from Hive Labels

```python
# Extract text from hive markers and labels
text_results = extract_text(image_data)

for text in text_results:
    print(f"Found text: '{text['description']}'")
    print(f"Location: {text['bounding_box']}")
```

## Error Handling

The Vision API module implements robust error handling for common scenarios:

### API Errors
```python
try:
    results = analyze_image(image_data)
except VisionAPIError as e:
    logger.error(f"Vision API failed: {e}")
    # Fallback to basic image processing
    results = basic_image_analysis(image_data)
```

### Quota Exceeded
```python
except QuotaExceededError:
    logger.warning("Vision API quota exceeded")
    # Queue for later processing or use cached results
    return cached_analysis_results()
```

### Invalid Image Format
```python
except InvalidImageError as e:
    logger.error(f"Invalid image format: {e}")
    # Attempt format conversion or reject upload
    return {"error": "Unsupported image format"}
```

## Response Format

### Object Detection Response
```json
{
  "objects": [
    {
      "name": "bee",
      "confidence": 0.89,
      "bounding_box": {
        "x": 245,
        "y": 123,
        "width": 45,
        "height": 38
      }
    }
  ],
  "labels": [
    {
      "description": "honeycomb",
      "confidence": 0.94
    }
  ],
  "text_annotations": [
    {
      "description": "Hive #7",
      "confidence": 0.87,
      "bounding_box": {...}
    }
  ],
  "safe_search": {
    "adult": "VERY_UNLIKELY",
    "violence": "UNLIKELY"
  }
}
```

## Performance Optimization

### Image Preprocessing
```python
# Optimize image size before API call
def preprocess_image(image_data: bytes) -> bytes:
    """Optimize image for Vision API analysis."""
    # Resize large images to reduce processing time
    # Enhance contrast for better detection
    # Convert to optimal format
    return optimized_image_data
```

### Caching Results
```python
# Cache frequent analysis results
@lru_cache(maxsize=100)
def cached_vision_analysis(image_hash: str) -> Dict:
    """Cache vision analysis results by image hash."""
    return vision_api_call(image_hash)
```

### Batch Processing
```python
# Process multiple images efficiently
def batch_analyze_images(image_list: List[bytes]) -> List[Dict]:
    """Analyze multiple images in batches for efficiency."""
    # Implement batch processing logic
    pass
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Verify credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
gcloud auth application-default print-access-token
```

#### Quota Monitoring
```bash
# Check API usage in Google Cloud Console
gcloud logging read "resource.type=consumed_api" --limit=50
```

#### Image Quality Issues
- **Blurry images**: May result in lower confidence scores
- **Poor lighting**: Can affect bee detection accuracy  
- **Image size**: Very large images may timeout; resize before upload

### Best Practices

1. **Image Quality**: Use high-resolution, well-lit photos for best results
2. **API Limits**: Monitor usage to avoid quota exhaustion
3. **Error Recovery**: Always implement fallback mechanisms
4. **Caching**: Cache results for identical images to reduce API calls
5. **Preprocessing**: Optimize images before sending to API

---

*The Vision API integration enables powerful computer vision capabilities that transform simple photos into rich, analyzable data about hive health and bee activity.*