"""
Comprehensive test suite for Google Cloud Vision API integration.

This test suite demonstrates best practices for testing external API integrations:
- Mocking external services to avoid real API calls
- Testing various response scenarios (success, error, edge cases)
- Validating data processing and transformation logic
- Error handling and resilience testing

Key learning points for junior developers:
1. Always mock external API calls in unit tests
2. Test both happy path and error scenarios
3. Validate that your code handles API response variations
4. Test data transformation logic thoroughly
5. Ensure proper error propagation and logging
"""

import pytest
import io
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from src.api_services.vision import BeeVisionAnalyzer
from tests.fixtures.vision_api_responses import (
    SUCCESSFUL_BEE_RESPONSE,
    NON_BEE_RESPONSE,
    EMPTY_RESPONSE,
    LOW_CONFIDENCE_RESPONSE,
    EXPECTED_BEE_ANALYSIS,
    EXPECTED_NON_BEE_ANALYSIS
)


class TestBeeVisionAnalyzer:
    """Test class for BeeVisionAnalyzer with comprehensive coverage."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.analyzer = BeeVisionAnalyzer()

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_successful_bee_image_analysis(self, mock_client):
        """
        Test successful analysis of bee-related image.
        
        This test demonstrates:
        - Mocking the Vision API client
        - Testing successful API response processing
        - Validating bee-related content detection
        - Checking data structure transformation
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        image_data = b"fake_image_data"
        
        # Act
        result = self.analyzer.analyze_image(image_data)
        
        # Assert
        assert 'error' not in result
        assert 'timestamp' in result
        assert 'labels' in result
        assert 'colors' in result
        assert 'objects' in result
        assert 'bee_summary' in result
        
        # Verify bee-related detection
        bee_labels = [label for label in result['labels'] if label['bee_related']]
        assert len(bee_labels) > 0
        
        # Verify bee summary contains expected fields
        summary = result['bee_summary']
        assert 'bee_related_terms_count' in summary
        assert 'bee_objects_detected_count' in summary
        assert 'honey_colors_detected' in summary
        assert 'suggested_hive_state' in summary
        
        # Verify API was called correctly
        mock_instance.annotate_image.assert_called_once()
        call_args = mock_instance.annotate_image.call_args[0][0]
        assert 'image' in call_args
        assert 'features' in call_args
        assert len(call_args['features']) == 3  # label, properties, objects

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_non_bee_image_analysis(self, mock_client):
        """
        Test analysis of non-bee-related image.
        
        This test demonstrates:
        - Handling images that don't contain bee-related content
        - Ensuring the analyzer doesn't false-positive on flowers/plants
        - Validating proper classification of non-bee content
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = NON_BEE_RESPONSE
        
        image_data = b"fake_flower_image_data"
        
        # Act
        result = self.analyzer.analyze_image(image_data)
        
        # Assert
        assert 'error' not in result
        
        # Verify no bee-related detection
        bee_labels = [label for label in result['labels'] if label['bee_related']]
        assert len(bee_labels) == 0
        
        # Verify bee summary reflects no bee content
        summary = result['bee_summary']
        assert summary['bee_related_terms_count'] == 0
        assert summary['bee_objects_detected_count'] == 0
        assert summary['suggested_hive_state'] == 'Unknown'

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_empty_api_response(self, mock_client):
        """
        Test handling of empty API response.
        
        This test demonstrates:
        - Handling edge case where API returns no labels/objects
        - Ensuring code doesn't crash on empty responses
        - Proper default value handling
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = EMPTY_RESPONSE
        
        image_data = b"empty_image_data"
        
        # Act
        result = self.analyzer.analyze_image(image_data)
        
        # Assert
        assert 'error' not in result
        assert result['labels'] == []
        assert result['colors'] == []
        assert result['objects'] == []
        
        # Verify summary handles empty data gracefully
        summary = result['bee_summary']
        assert summary['bee_related_terms_count'] == 0
        assert summary['suggested_hive_state'] == 'Unknown'

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_api_error_handling(self, mock_client):
        """
        Test handling of Vision API errors.
        
        This test demonstrates:
        - Proper exception handling for API failures
        - Error information preservation
        - Graceful degradation when API is unavailable
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.side_effect = Exception("API quota exceeded")
        
        image_data = b"image_data"
        
        # Act
        result = self.analyzer.analyze_image(image_data)
        
        # Assert
        assert 'error' in result
        assert 'API quota exceeded' in result['error']
        assert 'error_details' in result
        assert 'timestamp' in result

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_file_path_input(self, mock_client):
        """
        Test analysis with file path input.
        
        This test demonstrates:
        - Handling different input types (file path vs bytes)
        - File reading error handling
        - Input validation
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        test_file_path = "/path/to/test/image.jpg"
        mock_file_content = b"fake_image_content"
        
        # Act & Assert
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = self.analyzer.analyze_image(test_file_path)
            
        assert 'error' not in result
        mock_instance.annotate_image.assert_called_once()

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_bytesio_input(self, mock_client):
        """
        Test analysis with BytesIO input.
        
        This test demonstrates:
        - Handling BytesIO stream objects
        - Proper data extraction from streams
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        image_data = io.BytesIO(b"fake_image_content")
        
        # Act
        result = self.analyzer.analyze_image(image_data)
        
        # Assert
        assert 'error' not in result
        mock_instance.annotate_image.assert_called_once()

    def test_invalid_input_type(self):
        """
        Test error handling for invalid input types.
        
        This test demonstrates:
        - Input validation and type checking
        - Proper error messaging for invalid inputs
        """
        # Act
        result = self.analyzer.analyze_image(123)  # Invalid type
        
        # Assert
        assert 'error' in result
        assert 'Unsupported image data type' in result['error']

    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_file_not_found_error(self, mock_client, mock_open):
        """
        Test handling of file not found errors.
        
        This test demonstrates:
        - File system error handling
        - Proper error propagation for file operations
        """
        # Act
        result = self.analyzer.analyze_image("/nonexistent/file.jpg")
        
        # Assert
        assert 'error' in result
        assert 'File not found' in result['error']

    def test_bee_term_detection(self):
        """
        Test bee-related term detection logic.
        
        This test demonstrates:
        - Testing internal helper methods
        - Validating business logic for bee classification
        - Edge case handling for term matching
        """
        # Test bee-related terms
        assert self.analyzer._is_bee_related("Bee") == True
        assert self.analyzer._is_bee_related("Honey bee") == True
        assert self.analyzer._is_bee_related("BEEHIVE") == True  # Case insensitive
        assert self.analyzer._is_bee_related("Worker bee colony") == True
        assert self.analyzer._is_bee_related("Varroa mite") == True
        
        # Test non-bee terms
        assert self.analyzer._is_bee_related("Flower") == False
        assert self.analyzer._is_bee_related("Car") == False
        assert self.analyzer._is_bee_related("") == False

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_color_processing(self, mock_client):
        """
        Test color data processing and conversion.
        
        This test demonstrates:
        - Testing data transformation logic
        - RGB to hex conversion validation
        - Color classification for beekeeping context
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        # Act
        result = self.analyzer.analyze_image(b"image_data")
        
        # Assert
        colors = result['colors']
        assert len(colors) > 0
        
        for color in colors:
            assert 'color' in color
            assert 'hex' in color
            assert 'score' in color
            assert 'pixel_fraction' in color
            
            # Verify RGB format
            assert color['color'].startswith('rgb(')
            assert color['color'].endswith(')')
            
            # Verify hex format
            assert color['hex'].startswith('#')
            assert len(color['hex']) == 7

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_hive_state_classification(self, mock_client):
        """
        Test hive state classification logic.
        
        This test demonstrates:
        - Testing business logic for hive state determination
        - Confidence score processing
        - State classification validation
        """
        # Test high activity scenario
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        result = self.analyzer.analyze_image(b"active_hive_image")
        assert result['bee_summary']['suggested_hive_state'] in ['Active', 'Moderate Activity']
        
        # Test low confidence scenario
        mock_instance.annotate_image.return_value = LOW_CONFIDENCE_RESPONSE
        result = self.analyzer.analyze_image(b"unclear_image")
        assert result['bee_summary']['suggested_hive_state'] in ['Unknown', 'Low Activity']

    @patch('src.api_services.vision.vision.vision.Image')
    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_vision_api_request_structure(self, mock_client, mock_image):
        """
        Test that Vision API requests are structured correctly.
        
        This test demonstrates:
        - Validating API request parameters
        - Ensuring correct feature types are requested
        - Testing API integration patterns
        """
        # Arrange
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        # Act
        self.analyzer.analyze_image(b"image_data")
        
        # Assert
        mock_instance.annotate_image.assert_called_once()
        call_args = mock_instance.annotate_image.call_args[0][0]
        
        # Verify request structure
        assert 'image' in call_args
        assert 'features' in call_args
        
        # Verify feature types
        features = call_args['features']
        feature_types = [f['type_'] for f in features]
        
        from google.cloud import vision
        expected_types = [
            vision.Feature.Type.LABEL_DETECTION,
            vision.Feature.Type.IMAGE_PROPERTIES,
            vision.Feature.Type.OBJECT_LOCALIZATION
        ]
        
        for expected_type in expected_types:
            assert expected_type in feature_types


class TestVisionAPIIntegrationPatterns:
    """
    Additional tests focused on integration patterns and best practices.
    
    These tests demonstrate advanced testing techniques for external APIs.
    """

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_api_retry_behavior(self, mock_client):
        """
        Test API retry behavior for transient failures.
        
        Note: This test assumes retry logic would be implemented.
        Currently the analyzer doesn't have retry logic, but this shows
        how you would test it if implemented.
        """
        # This is a placeholder for when retry logic is implemented
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Simulate transient failure then success
        mock_instance.annotate_image.side_effect = [
            Exception("Temporary network error"),
            SUCCESSFUL_BEE_RESPONSE
        ]
        
        analyzer = BeeVisionAnalyzer()
        result = analyzer.analyze_image(b"image_data")
        
        # Currently will fail - this shows where retry logic could be added
        assert 'error' in result

    @patch('src.api_services.vision.vision.ImageAnnotatorClient')
    def test_large_image_handling(self, mock_client):
        """
        Test handling of large image files.
        
        This test demonstrates:
        - Performance considerations for large files
        - Memory usage patterns
        - Potential optimization points
        """
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
        
        # Simulate large image (5MB)
        large_image_data = b"x" * (5 * 1024 * 1024)
        
        analyzer = BeeVisionAnalyzer()
        result = analyzer.analyze_image(large_image_data)
        
        assert 'error' not in result
        mock_instance.annotate_image.assert_called_once()

    def test_concurrent_analysis_safety(self):
        """
        Test thread safety of analyzer instance.
        
        This test demonstrates:
        - Concurrent usage patterns
        - State management in multi-threaded environments
        - Resource sharing considerations
        """
        import threading
        import time
        
        analyzer = BeeVisionAnalyzer()
        results = []
        errors = []
        
        def analyze_image(image_data):
            try:
                # Mock the client to avoid real API calls
                with patch('src.api_services.vision.vision.ImageAnnotatorClient') as mock_client:
                    mock_instance = Mock()
                    mock_client.return_value = mock_instance
                    mock_instance.annotate_image.return_value = SUCCESSFUL_BEE_RESPONSE
                    
                    result = analyzer.analyze_image(image_data)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=analyze_image, 
                args=(f"image_data_{i}".encode(),)
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
        assert len(results) == 5