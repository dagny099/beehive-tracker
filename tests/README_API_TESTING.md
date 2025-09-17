# API Testing Best Practices and Patterns

This document outlines comprehensive testing strategies for external API integrations, specifically demonstrated through the Vision API and Weather API test suites. These patterns are essential for junior Data Scientists and Engineers learning how to build robust, testable applications that interact with external services.

## Table of Contents

1. [Why API Testing Matters](#why-api-testing-matters)
2. [Core Testing Principles](#core-testing-principles)
3. [Testing Patterns](#testing-patterns)
4. [Mock Strategies](#mock-strategies)
5. [Error Handling](#error-handling)
6. [Test Organization](#test-organization)
7. [Real-World Examples](#real-world-examples)

## Why API Testing Matters

### For Data Scientists & Engineers

External APIs are critical dependencies in modern applications, especially in data science and machine learning workflows:

- **Google Cloud Vision API**: Computer vision analysis for image processing pipelines
- **Weather APIs**: Environmental data for predictive modeling
- **Database APIs**: Data persistence and retrieval
- **ML Model APIs**: Inference and prediction services

### Risks of Poor API Testing

1. **Production Failures**: Untested error scenarios cause application crashes
2. **Data Quality Issues**: Malformed API responses corrupt downstream analysis
3. **Cost Overruns**: Uncontrolled API usage due to missing rate limiting tests
4. **Security Vulnerabilities**: Improper input validation exposes sensitive data
5. **Integration Brittleness**: API changes break applications without warning

## Core Testing Principles

### 1. Never Make Real API Calls in Tests

```python
# ❌ BAD: Makes real API calls
def test_weather_api():
    result = get_weather_open_meteo(40.7128, -74.0060, datetime.now())
    assert result["temperature"] > 0

# ✅ GOOD: Mocks API calls
@patch('src.api_services.weather.requests.get')
def test_weather_api(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = MOCK_WEATHER_RESPONSE
    mock_get.return_value = mock_response
    
    result = get_weather_open_meteo(40.7128, -74.0060, datetime.now())
    assert result["temperature"] == 25.5
```

**Why This Matters:**
- Tests run faster (no network latency)
- Tests are deterministic (same results every time)
- Tests don't consume API quota or cost money
- Tests work offline
- Tests don't break when external services are down

### 2. Test Multiple Response Scenarios

Every external API can return various responses:

```python
class TestWeatherAPIScenarios:
    def test_successful_response(self):
        """Test happy path with valid data"""
        
    def test_partial_data_response(self):
        """Test response with some null/missing values"""
        
    def test_empty_response(self):
        """Test response with no data"""
        
    def test_malformed_response(self):
        """Test invalid JSON or unexpected structure"""
        
    def test_error_response(self):
        """Test HTTP error codes (404, 500, etc.)"""
```

### 3. Validate Input Parameters

```python
def test_input_validation():
    """Test parameter validation and edge cases"""
    
    # Test missing required parameters
    result = get_weather_open_meteo(None, None, None)
    assert "Error:" in result["weather_source"]
    
    # Test invalid coordinate ranges
    result = get_weather_open_meteo(91.0, 181.0, datetime.now())
    assert "Error:" in result["weather_source"]
    
    # Test valid edge cases
    result = get_weather_open_meteo(0.0, 0.0, datetime.now())
    assert result is not None
```

## Testing Patterns

### Pattern 1: Response Structure Validation

Always verify that your code handles the expected API response structure:

```python
def test_vision_api_response_structure():
    """Ensure code handles all expected response fields"""
    
    with patch('vision_client.annotate_image') as mock_api:
        mock_api.return_value = MOCK_VISION_RESPONSE
        
        result = analyze_image(b"image_data")
        
        # Verify expected output structure
        assert 'labels' in result
        assert 'colors' in result
        assert 'objects' in result
        assert 'bee_summary' in result
        
        # Verify data types
        assert isinstance(result['labels'], list)
        assert isinstance(result['bee_summary'], dict)
```

### Pattern 2: Business Logic Testing

Test domain-specific processing of API responses:

```python
def test_bee_detection_logic():
    """Test bee-related classification logic"""
    
    analyzer = BeeVisionAnalyzer()
    
    # Test positive cases
    assert analyzer._is_bee_related("Honey bee") == True
    assert analyzer._is_bee_related("BEEHIVE") == True  # Case insensitive
    
    # Test negative cases
    assert analyzer._is_bee_related("Flower") == False
    assert analyzer._is_bee_related("Car") == False
    
    # Test edge cases
    assert analyzer._is_bee_related("") == False
    assert analyzer._is_bee_related("bee-like") == True  # Partial match
```

### Pattern 3: Data Transformation Testing

Verify that API data is correctly transformed for your application:

```python
def test_weather_data_transformation():
    """Test conversion from API format to application format"""
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2023-07-15T14:00"],
                "temperature_2m": [25.5],
                "precipitation": [0.1]
            }
        }
        mock_get.return_value = mock_response
        
        result = get_weather_open_meteo(40.7128, -74.0060, datetime(2023, 7, 15, 14, 30))
        
        # Verify data extraction
        assert result["weather_temperature_C"] == 25.5
        assert result["weather_precipitation_mm"] == 0.1
        assert "2023-07-15" in result["weather_datetime"]
```

## Mock Strategies

### Strategy 1: Fixture-Based Mocking

Create reusable mock responses in fixture files:

```python
# tests/fixtures/vision_api_responses.py
SUCCESSFUL_BEE_RESPONSE = MockVisionResponse(
    label_annotations=[
        MockLabel("Bee", 0.92),
        MockLabel("Honey bee", 0.88),
        # ... more labels
    ],
    # ... other response components
)

# tests/unit/test_vision_api.py
@patch('src.api_services.vision.vision.ImageAnnotatorClient')
def test_bee_image_analysis(mock_client):
    mock_client.return_value.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
    
    result = analyzer.analyze_image(b"image_data")
    assert result["bee_summary"]["bee_related_terms_count"] > 0
```

### Strategy 2: Parameterized Testing

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("coordinates,expected_error", [
    ((None, -74.0060), True),      # Missing latitude
    ((40.7128, None), True),       # Missing longitude  
    ((91.0, 0.0), True),          # Invalid latitude
    ((0.0, 181.0), True),         # Invalid longitude
    ((40.7128, -74.0060), False), # Valid coordinates
])
def test_coordinate_validation(coordinates, expected_error):
    lat, lon = coordinates
    result = get_weather_open_meteo(lat, lon, datetime.now())
    
    if expected_error:
        assert "Error:" in result["weather_source"]
    else:
        assert result["weather_source"] == "Open-Meteo API"
```

### Strategy 3: Error Simulation

Test various failure modes:

```python
@pytest.mark.parametrize("exception,expected_message", [
    (requests.exceptions.Timeout("Timeout"), "Timeout"),
    (requests.exceptions.ConnectionError("Connection failed"), "Connection failed"),
    (requests.exceptions.HTTPError("404 Not Found"), "404 Not Found"),
    (json.JSONDecodeError("Invalid JSON", "", 0), "Invalid JSON"),
])
def test_error_handling(exception, expected_message):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = exception
        
        result = get_weather_open_meteo(40.7128, -74.0060, datetime.now())
        
        assert "Error:" in result["weather_source"]
        assert expected_message in result["weather_source"]
```

## Error Handling

### HTTP Error Testing

Test all relevant HTTP status codes:

```python
HTTP_ERROR_SCENARIOS = [
    (400, "Bad Request - Invalid parameters"),
    (401, "Unauthorized - Invalid API key"), 
    (404, "Not Found - Resource not available"),
    (429, "Too Many Requests - Rate limit exceeded"),
    (500, "Internal Server Error - API unavailable"),
    (503, "Service Unavailable - Temporary outage")
]

@pytest.mark.parametrize("status_code,description", HTTP_ERROR_SCENARIOS)
def test_http_error_handling(status_code, description):
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} Client Error: {description}"
        )
        mock_get.return_value = mock_response
        
        result = get_weather_open_meteo(40.7128, -74.0060, datetime.now())
        
        assert "Error:" in result["weather_source"]
        assert str(status_code) in result["weather_source"]
```

### Network Error Testing

Test network-level failures:

```python
NETWORK_ERROR_SCENARIOS = [
    (requests.exceptions.Timeout, "Connection timeout"),
    (requests.exceptions.ConnectionError, "DNS resolution failed"),
    (requests.exceptions.TooManyRedirects, "Redirect loop detected"),
    (requests.exceptions.SSLError, "SSL certificate invalid")
]

@pytest.mark.parametrize("exception_class,description", NETWORK_ERROR_SCENARIOS)
def test_network_error_handling(exception_class, description):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = exception_class(description)
        
        result = get_weather_open_meteo(40.7128, -74.0060, datetime.now())
        
        assert "Error:" in result["weather_source"]
        assert description in result["weather_source"]
```

## Test Organization

### Directory Structure

```
tests/
├── conftest.py              # Shared test configuration
├── fixtures/                # Mock data and responses
│   ├── __init__.py
│   ├── vision_api_responses.py
│   └── weather_api_responses.py
├── unit/                    # Fast, isolated tests
│   ├── test_vision_api.py
│   ├── test_weather_api.py
│   └── test_data_processing.py
├── integration/             # Tests with multiple components
│   ├── test_api_integration.py
│   └── test_end_to_end.py
└── system/                  # Full system tests
    └── test_production_scenarios.py
```

### Test Class Organization

```python
class TestVisionAPISuccess:
    """Test successful API interactions"""
    
    def test_bee_image_analysis(self):
        """Test successful bee detection"""
        
    def test_non_bee_image_analysis(self):
        """Test non-bee image classification"""


class TestVisionAPIErrors:
    """Test error handling scenarios"""
    
    def test_api_quota_exceeded(self):
        """Test quota limit handling"""
        
    def test_invalid_image_format(self):
        """Test unsupported image handling"""


class TestVisionAPIEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_response(self):
        """Test handling of empty API response"""
        
    def test_malformed_response(self):
        """Test handling of unexpected response structure"""
```

## Real-World Examples

### Example 1: Vision API Integration

```python
# Source: tests/unit/test_vision_api.py
@patch('src.api_services.vision.vision.ImageAnnotatorClient')
def test_successful_bee_image_analysis(self, mock_client):
    """
    Demonstrates comprehensive Vision API testing:
    - Mock the Google Cloud client
    - Test bee detection logic
    - Validate data structure transformation
    - Check business logic (hive state classification)
    """
    # Arrange
    mock_instance = Mock()
    mock_client.return_value = mock_instance
    mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
    
    # Act
    result = self.analyzer.analyze_image(b"fake_image_data")
    
    # Assert
    assert 'error' not in result
    assert result['bee_summary']['bee_related_terms_count'] > 0
    assert result['bee_summary']['suggested_hive_state'] == 'Active'
    
    # Verify API call structure
    mock_instance.annotate_image.assert_called_once()
    call_args = mock_instance.annotate_image.call_args[0][0]
    assert len(call_args['features']) == 3  # Expected feature types
```

### Example 2: Weather API Integration

```python
# Source: tests/unit/test_weather_api.py
@patch('src.api_services.weather.requests.get')
def test_successful_weather_request_morning(self, mock_get):
    """
    Demonstrates comprehensive Weather API testing:
    - Mock HTTP requests
    - Test hour-matching logic
    - Validate parameter construction
    - Check data extraction accuracy
    """
    # Arrange
    mock_response = Mock()
    mock_response.json.return_value = SUCCESSFUL_WEATHER_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Act
    result = get_weather_open_meteo(40.7128, -74.0060, datetime(2023, 7, 15, 10, 30))
    
    # Assert
    assert result["weather_source"] == "Open-Meteo API"
    assert result["weather_temperature_C"] == 26.7  # Correct hour match
    
    # Verify API call parameters
    call_args = mock_get.call_args[1]["params"]
    assert call_args["latitude"] == 40.7128
    assert call_args["start_date"] == "2023-07-15"
```

### Example 3: Error Resilience Testing

```python
@patch('src.api_services.weather.requests.get')
def test_api_error_resilience(self, mock_get):
    """
    Demonstrates testing error resilience:
    - Simulate various failure modes
    - Verify graceful degradation
    - Ensure application continues functioning
    """
    # Test multiple error scenarios
    error_scenarios = [
        requests.exceptions.Timeout("Request timeout"),
        requests.exceptions.ConnectionError("Network unavailable"),
        requests.exceptions.HTTPError("429 Rate limit exceeded")
    ]
    
    for error in error_scenarios:
        mock_get.side_effect = error
        
        result = get_weather_open_meteo(40.7128, -74.0060, datetime.now())
        
        # Application should handle errors gracefully
        assert "Error:" in result["weather_source"]
        assert all(result[key] is None for key in [
            "weather_temperature_C", "weather_precipitation_mm"
        ])
```

## Key Takeaways for Junior Developers

1. **Always Mock External Dependencies**: Never make real API calls in tests
2. **Test Multiple Scenarios**: Success, failure, edge cases, and malformed data
3. **Validate Business Logic**: Test your data processing and classification logic
4. **Use Fixtures**: Create reusable mock data for consistent testing
5. **Test Error Handling**: Ensure your application degrades gracefully
6. **Organize Tests Well**: Group related tests and use clear naming
7. **Document Test Intent**: Explain what each test demonstrates
8. **Test Input Validation**: Verify parameter checking and sanitization
9. **Consider Performance**: Test with large responses and concurrent usage
10. **Keep Tests Fast**: Mocked tests should run in milliseconds

## Running the Tests

```bash
# Run all API tests
pytest tests/unit/test_vision_api.py tests/unit/test_weather_api.py -v

# Run specific test classes
pytest tests/unit/test_vision_api.py::TestBeeVisionAnalyzer -v

# Run with coverage reporting
pytest tests/unit/ --cov=src/api_services --cov-report=html

# Run tests matching pattern
pytest tests/ -k "test_error" -v
```

This comprehensive approach to API testing ensures your applications are robust, maintainable, and ready for production use.