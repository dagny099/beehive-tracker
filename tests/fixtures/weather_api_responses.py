"""
Mock response fixtures for Open-Meteo Weather API testing.

This module provides comprehensive mock responses that mirror the actual Weather API
structure, enabling reliable testing without making real API calls.
"""

from datetime import datetime


# Sample successful API response data
SUCCESSFUL_WEATHER_RESPONSE = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "generationtime_ms": 0.123,
    "utc_offset_seconds": -14400,
    "timezone": "America/New_York",
    "timezone_abbreviation": "EDT",
    "elevation": 7.0,
    "hourly_units": {
        "time": "iso8601",
        "temperature_2m": "°C",
        "precipitation": "mm",
        "cloudcover": "%",
        "windspeed_10m": "km/h",
        "weathercode": "wmo code"
    },
    "hourly": {
        "time": [
            "2023-07-15T00:00",
            "2023-07-15T01:00",
            "2023-07-15T02:00",
            "2023-07-15T03:00",
            "2023-07-15T04:00",
            "2023-07-15T05:00",
            "2023-07-15T06:00",
            "2023-07-15T07:00",
            "2023-07-15T08:00",
            "2023-07-15T09:00",
            "2023-07-15T10:00",
            "2023-07-15T11:00",
            "2023-07-15T12:00",
            "2023-07-15T13:00",
            "2023-07-15T14:00",
            "2023-07-15T15:00",
            "2023-07-15T16:00",
            "2023-07-15T17:00",
            "2023-07-15T18:00",
            "2023-07-15T19:00",
            "2023-07-15T20:00",
            "2023-07-15T21:00",
            "2023-07-15T22:00",
            "2023-07-15T23:00"
        ],
        "temperature_2m": [
            18.2, 17.8, 17.5, 17.2, 16.9, 17.1, 18.3, 20.1, 22.4, 24.8,
            26.7, 28.2, 29.1, 29.8, 30.2, 29.9, 29.1, 28.3, 26.8, 25.2,
            23.7, 22.1, 20.8, 19.6
        ],
        "precipitation": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.1, 0.3, 0.8, 1.2, 0.9, 0.4, 0.1, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0
        ],
        "cloudcover": [
            15, 20, 25, 30, 35, 40, 45, 50, 55, 60,
            65, 70, 75, 80, 85, 80, 75, 70, 65, 60,
            55, 50, 45, 40
        ],
        "windspeed_10m": [
            5.2, 4.8, 4.5, 4.2, 3.9, 4.1, 4.8, 6.2, 7.8, 9.4,
            11.2, 12.8, 14.1, 15.3, 16.2, 15.8, 14.9, 13.7, 12.1, 10.4,
            8.7, 7.2, 6.1, 5.6
        ],
        "weathercode": [
            1, 1, 1, 2, 2, 2, 3, 3, 51, 61,
            61, 63, 63, 80, 80, 61, 51, 3, 2, 2,
            1, 1, 1, 1
        ]
    }
}

# Weather response with missing data (nulls)
PARTIAL_WEATHER_RESPONSE = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "hourly": {
        "time": [
            "2023-07-15T10:00",
            "2023-07-15T11:00",
            "2023-07-15T12:00"
        ],
        "temperature_2m": [24.8, None, 29.1],
        "precipitation": [0.0, 0.1, None],
        "cloudcover": [60, None, 75],
        "windspeed_10m": [9.4, 12.8, None],
        "weathercode": [61, None, 63]
    }
}

# Expected processed results for different scenarios

EXPECTED_WEATHER_RESULT_MORNING = {
    "weather_datetime": "2023-07-15 10:00:00",
    "weather_temperature_C": 26.7,
    "weather_precipitation_mm": 0.0,
    "weather_cloud_cover_percent": 65,
    "weather_wind_speed_kph": 11.2,
    "weather_code": 61,
    "weather_source": "Open-Meteo API"
}

EXPECTED_WEATHER_RESULT_AFTERNOON = {
    "weather_datetime": "2023-07-15 14:00:00",
    "weather_temperature_C": 29.8,
    "weather_precipitation_mm": 0.8,
    "weather_cloud_cover_percent": 80,
    "weather_wind_speed_kph": 15.3,
    "weather_code": 80,
    "weather_source": "Open-Meteo API"
}

EXPECTED_WEATHER_RESULT_WITH_NULLS = {
    "weather_datetime": "2023-07-15 11:00:00",
    "weather_temperature_C": None,
    "weather_precipitation_mm": 0.1,
    "weather_cloud_cover_percent": None,
    "weather_wind_speed_kph": 12.8,
    "weather_code": None,
    "weather_source": "Open-Meteo API"
}

EXPECTED_ERROR_RESULT = {
    "weather_datetime": "2023-07-15 14:00:00",
    "weather_temperature_C": None,
    "weather_precipitation_mm": None,
    "weather_cloud_cover_percent": None,
    "weather_wind_speed_kph": None,
    "weather_code": None,
    "weather_source": "Error: 404 Client Error: Not Found for url: https://archive-api.open-meteo.com/v1/archive"
}

EXPECTED_MISSING_PARAMS_RESULT = {
    "weather_datetime": "2023-07-15 14:00:00",
    "weather_temperature_C": None,
    "weather_precipitation_mm": None,
    "weather_cloud_cover_percent": None,
    "weather_wind_speed_kph": None,
    "weather_code": None,
    "weather_source": "Error: Missing location or date information"
}

# HTTP error responses for testing error handling
HTTP_404_RESPONSE = {
    "error": True,
    "reason": "Location not found"
}

HTTP_429_RESPONSE = {
    "error": True,
    "reason": "Too many requests"
}

HTTP_500_RESPONSE = {
    "error": True,
    "reason": "Internal server error"
}

# Test coordinates for different scenarios
VALID_COORDINATES = {
    "new_york": (40.7128, -74.0060),
    "london": (51.5074, -0.1278),
    "sydney": (-33.8688, 151.2093),
    "tokyo": (35.6762, 139.6503)
}

INVALID_COORDINATES = {
    "out_of_range_lat": (91.0, 0.0),
    "out_of_range_lon": (0.0, 181.0),
    "null_values": (None, None),
    "string_values": ("invalid", "coordinates")
}

# Test dates for different scenarios
TEST_DATES = {
    "valid_recent": datetime(2023, 7, 15, 14, 30, 0),
    "valid_past": datetime(2020, 1, 1, 12, 0, 0),
    "future_date": datetime(2030, 1, 1, 12, 0, 0),
    "null_date": None
}