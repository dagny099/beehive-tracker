# 🐝 Beehive Tracker API Documentation

## Overview
This directory contains comprehensive API documentation for all internal and external APIs used in the Beehive Photo Metadata Tracker application.

## API Components

### Internal APIs
- **[Vision API Integration](./vision_api.md)** - Google Cloud Vision API wrapper and analysis
- **[Weather API Integration](./weather_api.md)** - Weather data fetching and processing  
- **[Image Processing API](./image_processing_api.md)** - EXIF extraction and color analysis
- **[Data Pipeline API](./data_pipeline_api.md)** - Core data flow and processing

### External APIs
- **[Google Cloud Vision API](./external/google_vision.md)** - Computer vision analysis
- **[Open-Meteo Weather API](./external/weather_service.md)** - Environmental data

## Quick Reference

### Core Functions

#### Vision Analysis
```python
from src.api_services.vision import BeeVisionAnalyzer

analyzer = BeeVisionAnalyzer()
results = analyzer.analyze_image(image_data)
# Returns: Dict[str, Any] with analysis results
```

#### Image Processing
```python
from src.utils.image_processor import ImageProcessor

processor = ImageProcessor()
metadata = processor.extract_metadata(image_bytes)
colors = processor.analyze_colors(image_bytes)
```

#### Weather Data
```python
from src.api_services.weather import WeatherService

weather = WeatherService()
data = weather.get_weather_data(lat=40.7128, lon=-74.0060, date="2024-05-15")
```

## Error Handling Patterns

All APIs follow consistent error handling:

```python
{
    "status": "success" | "error",
    "data": {...},           # Present on success
    "error_message": str,    # Present on error  
    "error_code": str,       # Present on error
    "timestamp": str
}
```

## Rate Limiting & Quotas

| API | Rate Limit | Daily Quota | Notes |
|-----|------------|-------------|-------|
| Google Vision | 600 requests/min | 1,000,000/day | Per project |
| Weather API | 10,000 requests/day | N/A | Free tier |

## Authentication

### Google Cloud Vision
- Service Account Key authentication
- Environment variable: `GOOGLE_APPLICATION_CREDENTIALS`

### Weather API  
- No authentication required (Open-Meteo)
- Optional API key for increased limits

## Development Guidelines

1. **Always include comprehensive docstrings**
2. **Handle rate limits gracefully with exponential backoff**
3. **Log all API calls for monitoring**
4. **Cache responses when appropriate**
5. **Validate input data before API calls**

## Testing APIs

See [Testing Guide](../DOCUMENTATION_AND_TESTING_PLAN.md#22-critical-component-testing) for comprehensive testing strategies.

## Support

- **Issues**: Create GitHub issues for API-related bugs
- **Documentation**: Update this directory when adding new APIs
- **Monitoring**: Check Cloud Logging for API call metrics