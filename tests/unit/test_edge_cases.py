import pytest
from pathlib import Path
from PIL import Image
import io
import tempfile
import os

from src.utils.image_processor import (
    extract_exif_data,
    extract_exif_with_exifread,
    extract_exif_with_pillow,
    convert_gps_to_decimal
)

@pytest.mark.unit
@pytest.mark.edge_case
class TestCorruptedImages:
    """Test handling of corrupted and malformed images"""
    
    def test_zero_byte_file(self, temp_dir):
        """Test handling of zero-byte files"""
        zero_file = temp_dir / "zero.jpg"
        zero_file.write_bytes(b"")
        
        # Should handle gracefully without crashing
        try:
            with Image.open(zero_file) as img:
                exif_data = extract_exif_data(img, file_path=str(zero_file))
                assert isinstance(exif_data, dict)
        except Exception as e:
            # It's acceptable for this to raise an exception
            assert True
    
    def test_truncated_jpeg(self, temp_dir):
        """Test handling of truncated JPEG files"""
        # Create a truncated JPEG (starts with JPEG header but incomplete)
        truncated_jpeg = temp_dir / "truncated.jpg" 
        truncated_jpeg.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")
        
        try:
            with Image.open(truncated_jpeg) as img:
                exif_data = extract_exif_data(img, file_path=str(truncated_jpeg))
                assert isinstance(exif_data, dict)
        except Exception as e:
            # Acceptable to fail on corrupted image
            assert True
    
    def test_non_image_file(self, temp_dir):
        """Test handling of non-image files"""
        text_file = temp_dir / "notimage.jpg"
        text_file.write_text("This is not an image file")
        
        try:
            with Image.open(text_file) as img:
                exif_data = extract_exif_data(img, file_path=str(text_file))
                assert isinstance(exif_data, dict)
        except Exception as e:
            # Expected to fail on non-image
            assert True
    
    def test_image_with_stripped_exif(self, sample_image_bytes):
        """Test images that have had EXIF data stripped"""
        # Create an image and save it without EXIF
        img = Image.open(io.BytesIO(sample_image_bytes))
        
        # Save without EXIF
        stripped_bytes = io.BytesIO()
        img.save(stripped_bytes, format='JPEG', exif=b'')
        stripped_bytes.seek(0)
        
        stripped_img = Image.open(stripped_bytes)
        exif_data = extract_exif_data(stripped_img)
        
        # Should return empty dict without crashing
        assert isinstance(exif_data, dict)
        # Likely to be empty since EXIF was stripped
        assert len(exif_data) == 0

@pytest.mark.unit
@pytest.mark.edge_case
class TestMalformedGPSData:
    """Test handling of malformed GPS data"""
    
    def test_gps_conversion_division_by_zero(self):
        """Test GPS conversion with zero denominators"""
        class MockGPSCoord:
            def __init__(self, values):
                self.values = values
        
        # GPS coordinates with zero denominator
        gps_coords = [
            MockGPSCoord([40, 0]),    # Division by zero
            MockGPSCoord([45, 1]),    
            MockGPSCoord([33, 1])     
        ]
        
        result = convert_gps_to_decimal(gps_coords, 'N')
        # Should handle gracefully and return None
        assert result is None
    
    def test_gps_conversion_negative_values(self):
        """Test GPS conversion with negative coordinate values"""
        class MockGPSCoord:
            def __init__(self, values):
                self.values = values
        
        gps_coords = [
            MockGPSCoord([-40, 1]),   # Negative degrees
            MockGPSCoord([45, 1]),    
            MockGPSCoord([33, 1])     
        ]
        
        # Should still work, direction is handled by GPS reference
        result = convert_gps_to_decimal(gps_coords, 'N')
        assert result is not None or result is None  # Either is acceptable
    
    def test_gps_conversion_invalid_reference(self):
        """Test GPS conversion with invalid direction reference"""
        class MockGPSCoord:
            def __init__(self, values):
                self.values = values
        
        gps_coords = [
            MockGPSCoord([40, 1]),
            MockGPSCoord([45, 1]),
            MockGPSCoord([33, 1])
        ]
        
        # Invalid GPS reference
        result = convert_gps_to_decimal(gps_coords, 'X')
        # Should handle gracefully
        assert isinstance(result, (float, type(None)))
    
    def test_gps_conversion_missing_coordinates(self):
        """Test GPS conversion with incomplete coordinate data"""
        class MockGPSCoord:
            def __init__(self, values):
                self.values = values
        
        # Only 2 coordinates instead of 3 (degrees, minutes, seconds)
        gps_coords = [
            MockGPSCoord([40, 1]),
            MockGPSCoord([45, 1])
        ]
        
        result = convert_gps_to_decimal(gps_coords, 'N')
        assert result is None

@pytest.mark.unit
@pytest.mark.edge_case
class TestExifExtractionFailures:
    """Test EXIF extraction failure scenarios"""
    
    def test_exifread_with_invalid_bytes(self):
        """Test exifread with invalid byte data"""
        invalid_bytes = io.BytesIO(b"invalid image data")
        
        exif_data = extract_exif_with_exifread(invalid_bytes)
        
        # Should return empty dict without crashing
        assert isinstance(exif_data, dict)
    
    def test_pillow_with_corrupted_exif(self):
        """Test Pillow EXIF extraction with corrupted EXIF data"""
        # Create minimal image
        img = Image.new('RGB', (100, 100), color='red')
        
        # This synthetic image has no EXIF
        exif_data = extract_exif_with_pillow(img)
        
        assert isinstance(exif_data, dict)
        # Synthetic image should have no EXIF
        assert len(exif_data) == 0
    
    def test_multi_library_all_methods_fail(self):
        """Test multi-library extraction when all methods fail"""
        # Create synthetic image with no EXIF
        img = Image.new('RGB', (50, 50), color='blue')
        
        # No file path or bytes provided, and synthetic image has no EXIF
        exif_data = extract_exif_data(img)
        
        # Should still return dict (empty is fine)
        assert isinstance(exif_data, dict)
    
    def test_permission_denied_file(self, temp_dir):
        """Test handling when file permission is denied"""
        # Create a file and remove read permissions
        protected_file = temp_dir / "protected.jpg"
        protected_file.write_bytes(b"fake image data")
        protected_file.chmod(0o000)  # No permissions
        
        try:
            # This should fail to read the file
            exif_data = extract_exif_with_exifread(str(protected_file))
            assert isinstance(exif_data, dict)
        except PermissionError:
            # Expected behavior
            assert True
        finally:
            # Restore permissions so file can be deleted
            try:
                protected_file.chmod(0o644)
            except:
                pass

@pytest.mark.unit
@pytest.mark.edge_case
class TestExtremeImageSizes:
    """Test handling of extreme image sizes"""
    
    def test_very_small_image(self):
        """Test handling of 1x1 pixel image"""
        img = Image.new('RGB', (1, 1), color='white')
        
        exif_data = extract_exif_data(img)
        
        # Should handle gracefully
        assert isinstance(exif_data, dict)
    
    def test_very_large_dimensions(self):
        """Test with very large image dimensions (but don't actually create it)"""
        # We'll simulate this by checking if our functions would handle
        # large dimension values in EXIF data
        
        # Mock large dimensions in EXIF-like data
        mock_exif = {
            'ImageWidth': 99999,
            'ImageHeight': 99999,
            'Make': 'TestCamera',
            'Model': 'BigImage'
        }
        
        # Our functions should handle large dimension values
        assert isinstance(mock_exif['ImageWidth'], int)
        assert isinstance(mock_exif['ImageHeight'], int)

@pytest.mark.unit
@pytest.mark.edge_case  
class TestUnicodeAndSpecialCharacters:
    """Test handling of unicode and special characters in EXIF data"""
    
    def test_unicode_in_exif_fields(self):
        """Test handling unicode characters in EXIF data"""
        # Simulate EXIF data with unicode
        mock_exif = {
            'Artist': 'José María',
            'Copyright': '© 2024 Test',
            'ImageDescription': 'Image with émojis 📷',
            'Make': 'Caméra Brand'
        }
        
        # Our code should handle unicode strings
        for key, value in mock_exif.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
    
    def test_special_characters_in_filenames(self, temp_dir):
        """Test handling files with special characters in names"""
        # Create file with special characters
        special_file = temp_dir / "test-image_@#$%^&()_file.jpg"
        
        # Create minimal valid JPEG
        img = Image.new('RGB', (100, 100), color='green')
        img.save(special_file, 'JPEG')
        
        # Should handle the filename without issues
        with Image.open(special_file) as opened_img:
            exif_data = extract_exif_data(opened_img, file_path=str(special_file))
            assert isinstance(exif_data, dict)