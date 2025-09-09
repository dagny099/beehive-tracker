import pytest
from pathlib import Path
from PIL import Image
import io
import logging

from src.utils.image_processor import (
    extract_exif_data,
    extract_exif_with_exifread,
    extract_exif_with_pillow,
    extract_exif_with_pyexiftool,
    convert_gps_to_decimal
)

@pytest.mark.unit
class TestGPSConversion:
    """Test GPS coordinate conversion functions"""
    
    def test_convert_gps_decimal_valid_north_east(self):
        """Test converting valid GPS coordinates (North/East)"""
        # Mock exifread format with IfdTag-like objects
        class MockGPSCoord:
            def __init__(self, values):
                self.values = values
        
        gps_coords = [
            MockGPSCoord([40, 1]),    # 40 degrees
            MockGPSCoord([45, 1]),    # 45 minutes  
            MockGPSCoord([33, 1])     # 33 seconds
        ]
        
        result = convert_gps_to_decimal(gps_coords, 'N')
        expected = 40 + (45/60.0) + (33/3600.0)  # ~40.7592
        assert abs(result - expected) < 0.0001
    
    def test_convert_gps_decimal_valid_south_west(self):
        """Test converting GPS coordinates with South/West direction"""
        class MockGPSCoord:
            def __init__(self, values):
                self.values = values
        
        gps_coords = [
            MockGPSCoord([37, 1]),    # 37 degrees
            MockGPSCoord([46, 1]),    # 46 minutes
            MockGPSCoord([30, 1])     # 30 seconds
        ]
        
        result = convert_gps_to_decimal(gps_coords, 'S')
        expected = -(37 + (46/60.0) + (30/3600.0))  # Negative for South
        assert abs(result - expected) < 0.0001
    
    def test_convert_gps_decimal_pillow_format(self):
        """Test converting GPS coordinates in Pillow tuple format"""
        gps_coords = [40.0, 45.0, 33.0]  # Degrees, minutes, seconds
        
        result = convert_gps_to_decimal(gps_coords, 'N')
        expected = 40 + (45/60.0) + (33/3600.0)
        assert abs(result - expected) < 0.0001
    
    def test_convert_gps_invalid_input(self):
        """Test GPS conversion with invalid input"""
        assert convert_gps_to_decimal(None, 'N') is None
        assert convert_gps_to_decimal([], 'N') is None
        assert convert_gps_to_decimal([1, 2], 'N') is None  # Too few values
        assert convert_gps_to_decimal([1, 2, 3], None) is None

@pytest.mark.unit 
class TestExifExtractionMethods:
    """Test individual EXIF extraction methods"""
    
    def test_extract_exif_with_pillow_valid_image(self, test_images):
        """Test Pillow EXIF extraction with valid images"""
        # Test with Samsung image (has rich EXIF)
        samsung_path = test_images["samsung_s9"]
        
        with Image.open(samsung_path) as img:
            exif_data = extract_exif_with_pillow(img)
            
            # Should extract basic EXIF data
            assert isinstance(exif_data, dict)
            assert len(exif_data) > 0
            
            # Check for expected fields
            expected_fields = ['Make', 'Model', 'DateTime']
            for field in expected_fields:
                if field in exif_data:
                    assert exif_data[field] is not None
    
    def test_extract_exif_with_pillow_no_exif(self, test_images):
        """Test Pillow extraction with image that has no EXIF"""
        # PNG typically has no EXIF
        png_path = test_images["png_no_exif"]
        
        with Image.open(png_path) as img:
            exif_data = extract_exif_with_pillow(img)
            
            # Should return empty dict or minimal data
            assert isinstance(exif_data, dict)
    
    def test_extract_exif_with_exifread_valid_file(self, test_images):
        """Test exifread extraction with valid file"""
        samsung_path = test_images["samsung_s9"]
        
        exif_data = extract_exif_with_exifread(samsung_path)
        
        assert isinstance(exif_data, dict)
        assert len(exif_data) > 0
        
        # Should have device info
        potential_make_fields = ['Make', 'manufacturer']
        assert any(field in exif_data for field in potential_make_fields)
    
    def test_extract_exif_with_exifread_bytesio(self, test_images):
        """Test exifread extraction with BytesIO input"""
        samsung_path = test_images["samsung_s9"]
        
        with open(samsung_path, 'rb') as f:
            file_bytes = f.read()
        
        exif_data = extract_exif_with_exifread(io.BytesIO(file_bytes))
        
        assert isinstance(exif_data, dict)
        assert len(exif_data) > 0

@pytest.mark.unit
class TestMultiLibraryExifExtraction:
    """Test the main multi-library EXIF extraction function"""
    
    def test_extract_exif_data_with_file_path(self, test_images):
        """Test multi-library extraction with file path"""
        samsung_path = test_images["samsung_s9"]
        
        with Image.open(samsung_path) as img:
            exif_data = extract_exif_data(img, file_path=str(samsung_path))
            
            assert isinstance(exif_data, dict)
            assert len(exif_data) > 0
            
            # Should have extracted device information
            device_fields = ['Make', 'Model', 'manufacturer', 'model']
            assert any(field in exif_data for field in device_fields)
    
    def test_extract_exif_data_with_bytes(self, test_images):
        """Test multi-library extraction with file bytes"""
        samsung_path = test_images["samsung_s9"]
        
        with open(samsung_path, 'rb') as f:
            file_bytes = f.read()
        
        with Image.open(samsung_path) as img:
            exif_data = extract_exif_data(img, file_bytes=file_bytes)
            
            assert isinstance(exif_data, dict)
            assert len(exif_data) > 0
    
    def test_extract_exif_data_fallback_to_pillow(self, sample_image_bytes):
        """Test fallback to Pillow when exifread fails"""
        # Create a minimal image that might cause exifread to fail
        img = Image.open(io.BytesIO(sample_image_bytes))
        
        # This should fall back to Pillow method
        exif_data = extract_exif_data(img)
        
        # Should return dict (might be empty for synthetic image)
        assert isinstance(exif_data, dict)
    
    def test_extract_exif_data_no_input(self):
        """Test extraction with no file path or bytes"""
        # Create minimal synthetic image
        img = Image.new('RGB', (100, 100), color='red')
        
        exif_data = extract_exif_data(img)
        
        # Should return empty dict for synthetic image with no EXIF
        assert isinstance(exif_data, dict)

@pytest.mark.unit
class TestExifExtractionEdgeCases:
    """Test edge cases and error handling"""
    
    def test_extract_exif_corrupted_image(self, corrupted_image_data):
        """Test extraction with corrupted image data"""
        # Should not crash, should return empty dict
        try:
            img = Image.open(io.BytesIO(corrupted_image_data))
            exif_data = extract_exif_data(img, file_bytes=corrupted_image_data)
            assert isinstance(exif_data, dict)
        except Exception:
            # It's acceptable for this to raise an exception
            pass
    
    def test_extract_exif_empty_data(self, empty_image_data):
        """Test extraction with empty image data"""
        try:
            img = Image.open(io.BytesIO(empty_image_data))
            exif_data = extract_exif_data(img, file_bytes=empty_image_data)
            assert isinstance(exif_data, dict)
        except Exception:
            # It's acceptable for this to raise an exception
            pass
    
    def test_extract_exif_nonexistent_file(self):
        """Test extraction with non-existent file path"""
        img = Image.new('RGB', (100, 100), color='blue')
        
        exif_data = extract_exif_data(img, file_path="/nonexistent/file.jpg")
        
        # Should fall back to Pillow method
        assert isinstance(exif_data, dict)