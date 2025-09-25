# Weather API Reference

The weather API module provides integration with external weather services to correlate environmental data with beehive inspection records.

!!! warning "🔴 Critical Gap - TODO"
    **This API reference needs complete documentation including:**
    - Complete function signatures and parameters
    - Usage examples with real code
    - Error handling patterns and exception types
    - Integration examples with inspection data
    - Rate limiting and API key management details

## Overview

The `src/api_services/weather.py` module integrates with Open-Meteo weather services to provide historical weather data correlation with inspection photos.

### Primary Functions

**Core Weather Data Retrieval:**
```python
def get_weather_open_meteo(lat: float, lng: float, date: str) -> Dict[str, Any]:
    """Retrieve historical weather data for a specific location and date.

    Args:
        lat: Latitude coordinate
        lng: Longitude coordinate
        date: Date in YYYY-MM-DD format

    Returns:
        Dictionary containing weather data including temperature,
        precipitation, humidity, and other environmental factors.
    """
```

### Key Features

- **Historical weather data** retrieval for any GPS location
- **Multiple weather metrics** including temperature, precipitation, humidity
- **API rate limiting** and error handling
- **Caching mechanisms** to reduce API calls
- **Integration with EXIF GPS data** from photos

### Data Structure

Weather data returned in standardized format:

```python
{
    "date": "2024-03-15",
    "temperature_max": 18.5,
    "temperature_min": 8.2,
    "precipitation": 0.0,
    "humidity": 65,
    "wind_speed": 12.5,
    "cloud_cover": 25,
    "weather_code": 0  # Clear sky
}
```

### Integration Examples

**Basic Usage:**
```python
# Get weather for inspection location
weather_data = get_weather_open_meteo(
    lat=40.7128,
    lng=-74.0060,
    date="2024-03-15"
)

# Add to inspection record
inspection["weather"] = weather_data
```

### Error Handling

The weather API implements robust error handling for:
- Network connectivity issues
- API rate limiting
- Invalid coordinates or dates
- Service unavailability

### Configuration

Weather API configuration through environment variables:
```bash
# Optional premium weather service API key
WEATHER_API_KEY=your-api-key-here

# API timeout settings
WEATHER_API_TIMEOUT=30
```

---

!!! info "🟡 Important Gap - TODO"
    **Missing documentation that needs to be added:**
    - Complete API function reference with all parameters
    - Weather code interpretation guide
    - Caching implementation details
    - Rate limiting and quota management
    - Integration patterns with inspection workflow
    - Error recovery strategies
    - Testing and mocking patterns