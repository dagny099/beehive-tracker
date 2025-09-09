import pytest
from pathlib import Path
from PIL import Image
import logging

from src.utils.image_processor import (
    extract_exif_data,
    process_image_file
)

@pytest.mark.integration
@pytest.mark.device
class TestDeviceCoverage:
    """Test EXIF extraction across different device types"""
    
    def test_samsung_galaxy_s9_extraction(self, test_images):
        """Test EXIF extraction from Samsung Galaxy S9 images"""
        test_cases = [
            ("samsung_s9", "bees_pollen_visible.jpg"),
            ("samsung_s9_portrait", "queen_bee_closeup.jpg"), 
            ("samsung_s9_comb", "comb_queen_bee.jpg")
        ]
        
        for key, filename in test_cases:
            image_path = test_images[key]
            
            with Image.open(image_path) as img:
                exif_data = extract_exif_data(img, file_path=str(image_path))
                
                # Samsung-specific assertions
                assert isinstance(exif_data, dict)
                assert len(exif_data) > 0
                
                # Check for Samsung device markers
                make_fields = [field for field in exif_data.keys() 
                              if 'make' in field.lower() or 'Make' in field]
                model_fields = [field for field in exif_data.keys()
                               if 'model' in field.lower() or 'Model' in field]
                
                # Should have device identification
                assert len(make_fields) > 0 or len(model_fields) > 0
                
                # Check for GPS data (Samsung phones typically include this)
                gps_fields = [field for field in exif_data.keys()
                             if 'gps' in field.lower() or 'GPS' in field]
                
                if 'GPSLatitudeDecimal' in exif_data:
                    assert isinstance(exif_data['GPSLatitudeDecimal'], (int, float))
                    assert -90 <= exif_data['GPSLatitudeDecimal'] <= 90
                
                if 'GPSLongitudeDecimal' in exif_data:
                    assert isinstance(exif_data['GPSLongitudeDecimal'], (int, float))
                    assert -180 <= exif_data['GPSLongitudeDecimal'] <= 180
                    
                logging.info(f"Samsung S9 {filename}: extracted {len(exif_data)} EXIF fields")
    
    def test_google_pixel_7_extraction(self, test_images):
        """Test EXIF extraction from Google Pixel 7 images"""
        test_cases = [
            ("pixel_7_new", "capped_brood_top_bar.jpg"),
            ("pixel_7_old", "comb_new.jpg")
        ]
        
        for key, filename in test_cases:
            image_path = test_images[key]
            
            with Image.open(image_path) as img:
                exif_data = extract_exif_data(img, file_path=str(image_path))
                
                # Pixel-specific assertions
                assert isinstance(exif_data, dict)
                assert len(exif_data) > 0
                
                # Check for Google device markers
                make_fields = [field for field in exif_data.keys() 
                              if 'make' in field.lower() or 'Make' in field]
                model_fields = [field for field in exif_data.keys()
                               if 'model' in field.lower() or 'Model' in field]
                
                assert len(make_fields) > 0 or len(model_fields) > 0
                
                # Check for HDR+ software signature (Pixel-specific)
                software_fields = [field for field in exif_data.keys()
                                 if 'software' in field.lower() or 'Software' in field]
                
                # Pixel phones should have GPS data
                if 'GPSLatitudeDecimal' in exif_data:
                    assert isinstance(exif_data['GPSLatitudeDecimal'], (int, float))
                
                if 'GPSLongitudeDecimal' in exif_data:
                    assert isinstance(exif_data['GPSLongitudeDecimal'], (int, float))
                    
                logging.info(f"Pixel 7 {filename}: extracted {len(exif_data)} EXIF fields")
    
    def test_orientation_handling(self, test_images):
        """Test different image orientations are handled correctly"""
        # Samsung portrait mode image
        portrait_path = test_images["samsung_s9_portrait"]
        
        with Image.open(portrait_path) as img:
            exif_data = extract_exif_data(img, file_path=str(portrait_path))
            
            # Check for orientation data
            orientation_fields = [field for field in exif_data.keys()
                                if 'orientation' in field.lower() or 'Orientation' in field]
            
            # Should have orientation information
            if orientation_fields:
                orientation_field = orientation_fields[0]
                assert exif_data[orientation_field] is not None
                logging.info(f"Orientation: {exif_data[orientation_field]}")

@pytest.mark.integration
@pytest.mark.format 
class TestFileFormatCoverage:
    """Test EXIF extraction across different file formats"""
    
    def test_jpeg_format_extraction(self, test_images):
        """Test JPEG format EXIF extraction"""
        jpeg_images = [key for key in test_images.keys() if not key.endswith('png') and not 'png' in key]
        
        for key in jpeg_images:
            image_path = test_images[key]
            
            with Image.open(image_path) as img:
                assert img.format == 'JPEG', f"Expected JPEG format for {key}, got {img.format}"
                
                exif_data = extract_exif_data(img, file_path=str(image_path))
                
                # JPEG images should have EXIF data
                assert isinstance(exif_data, dict)
                # Most phone JPEGs will have some EXIF data
                if len(exif_data) == 0:
                    logging.warning(f"No EXIF data found in {image_path}")
    
    def test_png_format_handling(self, test_images):
        """Test PNG format (typically no EXIF)"""
        png_path = test_images["png_no_exif"]
        
        with Image.open(png_path) as img:
            assert img.format == 'PNG'
            
            exif_data = extract_exif_data(img, file_path=str(png_path))
            
            # PNG typically has no EXIF, should return empty dict
            assert isinstance(exif_data, dict)
            # It's OK if PNG has no EXIF data
            logging.info(f"PNG EXIF fields extracted: {len(exif_data)}")

@pytest.mark.integration
@pytest.mark.gps
class TestGPSExtraction:
    """Test GPS coordinate extraction and conversion"""
    
    def test_gps_extraction_all_devices(self, test_images):
        """Test GPS extraction across all test devices"""
        for key, image_path in test_images.items():
            if key == "png_no_exif":  # Skip PNG
                continue
                
            with Image.open(image_path) as img:
                exif_data = extract_exif_data(img, file_path=str(image_path))
                
                # Check if GPS data was extracted
                has_gps_lat = 'GPSLatitudeDecimal' in exif_data
                has_gps_lon = 'GPSLongitudeDecimal' in exif_data
                
                if has_gps_lat or has_gps_lon:
                    logging.info(f"{key}: GPS data found")
                    
                    if has_gps_lat:
                        lat = exif_data['GPSLatitudeDecimal']
                        assert isinstance(lat, (int, float))
                        assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
                        
                    if has_gps_lon:
                        lon = exif_data['GPSLongitudeDecimal']
                        assert isinstance(lon, (int, float))
                        assert -180 <= lon <= 180, f"Invalid longitude: {lon}"
                        
                    # If we have both, log the coordinates
                    if has_gps_lat and has_gps_lon:
                        logging.info(f"{key}: GPS coordinates: {lat:.6f}, {lon:.6f}")
                else:
                    logging.info(f"{key}: No GPS data found")

@pytest.mark.integration
class TestProcessImageFileIntegration:
    """Test the full process_image_file function with real images"""
    
    def test_process_image_file_samsung(self, test_images, temp_dir):
        """Test full image processing pipeline with Samsung image"""
        samsung_path = test_images["samsung_s9"]
        
        with open(samsung_path, 'rb') as f:
            file_content = f.read()
        
        # Mock file object
        class MockFile:
            def __init__(self, content):
                self.content = content
                self.position = 0
            
            def read(self):
                return self.content
            
            def seek(self, position):
                self.position = position
        
        mock_file = MockFile(file_content)
        
        # Note: process_image_file uses streamlit session state
        # We'll test the EXIF extraction parts directly
        with Image.open(samsung_path) as img:
            exif_data = extract_exif_data(img, file_path=str(samsung_path))
            
            # Should extract comprehensive data
            assert isinstance(exif_data, dict)
            assert len(exif_data) > 0
            
            # Verify specific fields that process_image_file relies on
            expected_date_fields = ['DateTimeOriginal', 'DateTime']
            date_field_found = any(field in exif_data for field in expected_date_fields)
            
            if not date_field_found:
                logging.warning("No date fields found in EXIF data")
            
            # Test GPS extraction
            if 'GPSLatitudeDecimal' in exif_data and 'GPSLongitudeDecimal' in exif_data:
                lat = exif_data['GPSLatitudeDecimal']
                lon = exif_data['GPSLongitudeDecimal'] 
                assert isinstance(lat, (int, float))
                assert isinstance(lon, (int, float))
                logging.info(f"Successfully extracted GPS: {lat:.6f}, {lon:.6f}")