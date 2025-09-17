"""
Comprehensive test suite for Open-Meteo Weather API integration.

This test suite demonstrates best practices for testing external HTTP API integrations:
- Mocking HTTP requests to avoid real API calls
- Testing various response scenarios (success, error, timeouts)
- Validating data parsing and transformation logic
- Error handling and edge case management
- Parameter validation and input sanitization

Key learning points for junior developers:
1. Always mock HTTP requests in unit tests using responses or requests-mock
2. Test multiple response formats (success, error, malformed)
3. Validate input parameter handling and edge cases
4. Test network error scenarios (timeouts, connection errors)
5. Ensure proper data type conversion and null handling
6. Test coordinate and datetime validation
"""

import pytest
import requests
from unittest.mock import patch, Mock
from datetime import datetime
import json

from src.api_services.weather import get_weather_open_meteo
from tests.fixtures.weather_api_responses import (
    SUCCESSFUL_WEATHER_RESPONSE,
    PARTIAL_WEATHER_RESPONSE,
    EXPECTED_WEATHER_RESULT_MORNING,
    EXPECTED_WEATHER_RESULT_AFTERNOON,
    EXPECTED_WEATHER_RESULT_WITH_NULLS,
    EXPECTED_ERROR_RESULT,
    EXPECTED_MISSING_PARAMS_RESULT,
    HTTP_404_RESPONSE,
    HTTP_429_RESPONSE,
    HTTP_500_RESPONSE,
    VALID_COORDINATES,
    INVALID_COORDINATES,
    TEST_DATES
)


class TestWeatherAPISuccess:
    """Test successful weather API interactions."""

    @patch('src.api_services.weather.requests.get')
    def test_successful_weather_request_morning(self, mock_get):
        """
        Test successful weather data retrieval for morning hours.
        
        This test demonstrates:
        - Mocking successful HTTP responses
        - Testing hour-matching logic
        - Validating data extraction and transformation
        - Checking proper API parameter construction
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["new_york"]
        test_datetime = datetime(2023, 7, 15, 10, 30, 0)  # 10:30 AM
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert result["weather_source"] == "Open-Meteo API"
        assert result["weather_temperature_C"] == 26.7  # 10:00 AM value
        assert result["weather_precipitation_mm"] == 0.0
        assert result["weather_cloud_cover_percent"] == 65
        assert result["weather_wind_speed_kph"] == 11.2
        assert result["weather_code"] == 61
        assert "2023-07-15" in result["weather_datetime"]
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://archive-api.open-meteo.com/v1/archive"
        
        params = call_args[1]["params"]
        assert params["latitude"] == lat
        assert params["longitude"] == lon
        assert params["start_date"] == "2023-07-15"
        assert params["end_date"] == "2023-07-15"
        assert "temperature_2m" in params["hourly"]
        assert params["timezone"] == "auto"

    @patch('src.api_services.weather.requests.get')
    def test_successful_weather_request_afternoon(self, mock_get):
        """
        Test successful weather data retrieval for afternoon hours.
        
        This test demonstrates:
        - Testing different time periods within the same day
        - Validating closest hour matching algorithm
        - Ensuring consistent data structure across different times
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["london"]
        test_datetime = datetime(2023, 7, 15, 14, 45, 0)  # 2:45 PM
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert result["weather_source"] == "Open-Meteo API"
        assert result["weather_temperature_C"] == 29.8  # 14:00 (2 PM) value
        assert result["weather_precipitation_mm"] == 0.8
        assert result["weather_cloud_cover_percent"] == 80
        assert result["weather_wind_speed_kph"] == 15.3
        assert result["weather_code"] == 80

    @patch('src.api_services.weather.requests.get')
    def test_weather_with_null_values(self, mock_get):
        """
        Test handling of null/missing values in API response.
        
        This test demonstrates:
        - Handling incomplete data from external APIs
        - Proper null value preservation
        - Ensuring code doesn't crash on missing data
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = PARTIAL_WEATHER_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["sydney"]
        test_datetime = datetime(2023, 7, 15, 11, 0, 0)  # 11:00 AM
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert result["weather_source"] == "Open-Meteo API"
        assert result["weather_temperature_C"] is None  # Null in response
        assert result["weather_precipitation_mm"] == 0.1  # Valid value
        assert result["weather_cloud_cover_percent"] is None  # Null in response
        assert result["weather_wind_speed_kph"] == 12.8  # Valid value
        assert result["weather_code"] is None  # Null in response


class TestWeatherAPIErrors:
    """Test error handling for weather API interactions."""

    @patch('src.api_services.weather.requests.get')
    def test_http_404_error(self, mock_get):
        """
        Test handling of HTTP 404 Not Found errors.
        
        This test demonstrates:
        - Testing HTTP error responses
        - Ensuring graceful error handling
        - Validating error message propagation
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error: Not Found for url: https://archive-api.open-meteo.com/v1/archive"
        )
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["tokyo"]
        test_datetime = TEST_DATES["valid_recent"]
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert "Error:" in result["weather_source"]
        assert "404" in result["weather_source"]
        assert result["weather_temperature_C"] is None
        assert result["weather_precipitation_mm"] is None
        assert result["weather_cloud_cover_percent"] is None
        assert result["weather_wind_speed_kph"] is None
        assert result["weather_code"] is None

    @patch('src.api_services.weather.requests.get')
    def test_http_429_rate_limit_error(self, mock_get):
        """
        Test handling of HTTP 429 Too Many Requests errors.
        
        This test demonstrates:
        - Testing rate limiting scenarios
        - API quota/throttling error handling
        - Proper error categorization
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Client Error: Too Many Requests"
        )
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["new_york"]
        test_datetime = TEST_DATES["valid_recent"]
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert "Error:" in result["weather_source"]
        assert all(result[key] is None for key in [
            "weather_temperature_C", "weather_precipitation_mm",
            "weather_cloud_cover_percent", "weather_wind_speed_kph", "weather_code"
        ])

    @patch('src.api_services.weather.requests.get')
    def test_connection_timeout_error(self, mock_get):
        """
        Test handling of connection timeout errors.
        
        This test demonstrates:
        - Testing network connectivity issues
        - Timeout error handling
        - Ensuring application continues running despite network issues
        """
        # Arrange
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        lat, lon = VALID_COORDINATES["london"]
        test_datetime = TEST_DATES["valid_recent"]
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert "Error:" in result["weather_source"]
        assert "Connection timed out" in result["weather_source"]
        assert all(result[key] is None for key in [
            "weather_temperature_C", "weather_precipitation_mm",
            "weather_cloud_cover_percent", "weather_wind_speed_kph", "weather_code"
        ])

    @patch('src.api_services.weather.requests.get')
    def test_connection_error(self, mock_get):
        """
        Test handling of general connection errors.
        
        This test demonstrates:
        - Testing network connectivity failures
        - DNS resolution errors
        - General network exception handling
        """
        # Arrange
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to establish connection")
        
        lat, lon = VALID_COORDINATES["sydney"]
        test_datetime = TEST_DATES["valid_recent"]
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert "Error:" in result["weather_source"]
        assert "Failed to establish connection" in result["weather_source"]

    @patch('src.api_services.weather.requests.get')
    def test_invalid_json_response(self, mock_get):
        """
        Test handling of malformed JSON responses.
        
        This test demonstrates:
        - Testing malformed API responses
        - JSON parsing error handling
        - Ensuring robustness against API changes
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["tokyo"]
        test_datetime = TEST_DATES["valid_recent"]
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert "Error:" in result["weather_source"]
        assert "Invalid JSON" in result["weather_source"]

    @patch('src.api_services.weather.requests.get')
    def test_missing_hourly_data_in_response(self, mock_get):
        """
        Test handling of API response missing expected data structure.
        
        This test demonstrates:
        - Testing API response structure validation
        - Handling unexpected response formats
        - KeyError handling for missing data fields
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"latitude": 40.7128, "longitude": -74.0060}  # Missing hourly data
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["new_york"]
        test_datetime = TEST_DATES["valid_recent"]
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert "Error:" in result["weather_source"]


class TestWeatherAPIInputValidation:
    """Test input validation and edge cases."""

    def test_missing_latitude(self):
        """
        Test handling of missing latitude parameter.
        
        This test demonstrates:
        - Input parameter validation
        - Handling null/None values
        - Default error response structure
        """
        # Act
        result = get_weather_open_meteo(None, -74.0060, TEST_DATES["valid_recent"])
        
        # Assert
        assert result["weather_source"] == "Error: Missing location or date information"
        assert all(result[key] is None for key in [
            "weather_temperature_C", "weather_precipitation_mm",
            "weather_cloud_cover_percent", "weather_wind_speed_kph", "weather_code"
        ])

    def test_missing_longitude(self):
        """
        Test handling of missing longitude parameter.
        
        This test demonstrates:
        - Input parameter validation
        - Ensuring both coordinates are required
        """
        # Act
        result = get_weather_open_meteo(40.7128, None, TEST_DATES["valid_recent"])
        
        # Assert
        assert result["weather_source"] == "Error: Missing location or date information"

    def test_missing_datetime(self):
        """
        Test handling of missing datetime parameter.
        
        This test demonstrates:
        - Date/time parameter validation
        - Handling None datetime values
        """
        # Act
        result = get_weather_open_meteo(40.7128, -74.0060, None)
        
        # Assert
        assert result["weather_source"] == "Error: Missing location or date information"
        # Should still include current time in response
        assert result["weather_datetime"] is not None

    def test_all_missing_parameters(self):
        """
        Test handling when all parameters are missing.
        
        This test demonstrates:
        - Complete input validation failure
        - Comprehensive parameter checking
        """
        # Act
        result = get_weather_open_meteo(None, None, None)
        
        # Assert
        assert result["weather_source"] == "Error: Missing location or date information"

    def test_empty_string_coordinates(self):
        """
        Test handling of empty string coordinates.
        
        This test demonstrates:
        - Handling invalid coordinate types
        - Type validation for numeric parameters
        """
        # Act
        result = get_weather_open_meteo("", "", TEST_DATES["valid_recent"])
        
        # Assert
        assert result["weather_source"] == "Error: Missing location or date information"

    def test_zero_coordinates(self):
        """
        Test handling of zero coordinates (valid case).
        
        This test demonstrates:
        - Distinguishing between None and zero values
        - Handling edge case coordinates (0,0 is valid)
        """
        with patch('src.api_services.weather.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Act
            result = get_weather_open_meteo(0.0, 0.0, TEST_DATES["valid_recent"])
            
            # Assert
            assert result["weather_source"] == "Open-Meteo API"
            mock_get.assert_called_once()


class TestWeatherAPIDateHandling:
    """Test various date and time handling scenarios."""

    @patch('src.api_services.weather.requests.get')
    def test_past_date(self, mock_get):
        """
        Test weather request for past dates.
        
        This test demonstrates:
        - Historical weather data requests
        - Date formatting for API requests
        - Ensuring past dates are handled correctly
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["new_york"]
        past_date = TEST_DATES["valid_past"]  # 2020-01-01
        
        # Act
        result = get_weather_open_meteo(lat, lon, past_date)
        
        # Assert
        assert result["weather_source"] == "Open-Meteo API"
        
        # Verify API was called with correct date format
        call_args = mock_get.call_args[1]["params"]
        assert call_args["start_date"] == "2020-01-01"
        assert call_args["end_date"] == "2020-01-01"

    @patch('src.api_services.weather.requests.get')
    def test_future_date(self, mock_get):
        """
        Test weather request for future dates.
        
        This test demonstrates:
        - Handling future date requests
        - Testing edge cases for date ranges
        - API behavior with invalid date ranges
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "400 Client Error: Future dates not supported"
        )
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["tokyo"]
        future_date = TEST_DATES["future_date"]  # 2030-01-01
        
        # Act
        result = get_weather_open_meteo(lat, lon, future_date)
        
        # Assert
        assert "Error:" in result["weather_source"]

    @patch('src.api_services.weather.requests.get')
    def test_hour_matching_edge_cases(self, mock_get):
        """
        Test hour matching logic for edge cases.
        
        This test demonstrates:
        - Hour matching algorithm validation
        - Edge cases for time matching (e.g., minute precision)
        - Ensuring closest hour selection is correct
        """
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["london"]
        
        # Test exact hour match
        exact_hour = datetime(2023, 7, 15, 12, 0, 0)
        result = get_weather_open_meteo(lat, lon, exact_hour)
        assert result["weather_temperature_C"] == 29.1  # 12:00 value
        
        # Test 30 minutes past hour (should round to same hour)
        half_past = datetime(2023, 7, 15, 12, 30, 0)
        result = get_weather_open_meteo(lat, lon, half_past)
        assert result["weather_temperature_C"] == 29.1  # Still 12:00 value
        
        # Test 59 minutes past hour (should round to same hour)
        almost_next = datetime(2023, 7, 15, 12, 59, 0)
        result = get_weather_open_meteo(lat, lon, almost_next)
        assert result["weather_temperature_C"] == 29.1  # Still 12:00 value


class TestWeatherAPIPerformance:
    """Test performance and resource usage patterns."""

    @patch('src.api_services.weather.requests.get')
    def test_large_response_handling(self, mock_get):
        """
        Test handling of large API responses.
        
        This test demonstrates:
        - Memory usage patterns with large datasets
        - Performance considerations for data processing
        - Scalability testing approaches
        """
        # Arrange - Create large response with 24 hours * 30 days
        large_response = SUCCESSFUL_WEATHER_RESPONSE.copy()
        large_response["hourly"]["time"] = [
            f"2023-07-{day:02d}T{hour:02d}:00" 
            for day in range(1, 31) 
            for hour in range(24)
        ]
        
        # Extend all hourly data arrays to match
        hours_count = len(large_response["hourly"]["time"])
        for key in ["temperature_2m", "precipitation", "cloudcover", "windspeed_10m", "weathercode"]:
            large_response["hourly"][key] = [20.0] * hours_count
        
        mock_response = Mock()
        mock_response.json.return_value = large_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        lat, lon = VALID_COORDINATES["sydney"]
        test_datetime = datetime(2023, 7, 15, 12, 0, 0)
        
        # Act
        result = get_weather_open_meteo(lat, lon, test_datetime)
        
        # Assert
        assert result["weather_source"] == "Open-Meteo API"
        assert result["weather_temperature_C"] is not None

    def test_concurrent_requests(self):
        """
        Test concurrent weather API requests.
        
        This test demonstrates:
        - Thread safety of the weather function
        - Concurrent API usage patterns
        - Resource sharing considerations
        """
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(lat, lon, dt):
            try:
                with patch('src.api_services.weather.requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
                    mock_response.raise_for_status.return_value = None
                    mock_get.return_value = mock_response
                    
                    result = get_weather_open_meteo(lat, lon, dt)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads with different coordinates
        threads = []
        coordinates = list(VALID_COORDINATES.values())
        
        for i, (lat, lon) in enumerate(coordinates):
            thread = threading.Thread(
                target=make_request,
                args=(lat, lon, TEST_DATES["valid_recent"])
            )
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == len(coordinates)
        
        # Verify all results are valid
        for result in results:
            assert result["weather_source"] == "Open-Meteo API"
            assert result["weather_temperature_C"] is not None