"""
Tests for EXIF data preservation through storage operations.
Validates that EXIF data survives upload, download, and cloud round-trips.
"""

import os
import io
import tempfile
import shutil
import pytest
from typing import Dict, Any, Optional

# Add src to path for imports  
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.local_provider import LocalStorageProvider
from utils.image_processor import extract_exif_data, process_image_file


def create_test_image_with_comprehensive_exif():
    """Create test image with comprehensive EXIF data"""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import piexif
        
        # Create test image
        img = Image.new('RGB', (300, 200), color=(255, 128, 64))
        
        # Comprehensive EXIF data
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: "BeehiveCamera",
                piexif.ImageIFD.Model: "HC-2025",
                piexif.ImageIFD.DateTime: "2025:09:09 14:30:15",
                piexif.ImageIFD.Software: "BeehiveTracker v2.0",
                piexif.ImageIFD.ImageWidth: 300,
                piexif.ImageIFD.ImageLength: 200,
                piexif.ImageIFD.XResolution: (72, 1),
                piexif.ImageIFD.YResolution: (72, 1),
                piexif.ImageIFD.ResolutionUnit: 2
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2025:09:09 14:30:15",
                piexif.ExifIFD.DateTimeDigitized: "2025:09:09 14:30:15", 
                piexif.ExifIFD.ExposureTime: (1, 125),
                piexif.ExifIFD.FNumber: (56, 10),  # f/5.6
                piexif.ExifIFD.ISOSpeedRatings: 200,
                piexif.ExifIFD.FocalLength: (85, 1),  # 85mm
                piexif.ExifIFD.Flash: 16,  # Flash did not fire
                piexif.ExifIFD.ExposureMode: 0,  # Auto exposure
                piexif.ExifIFD.WhiteBalance: 0,  # Auto white balance
                piexif.ExifIFD.SceneCaptureType: 0  # Standard
            },
            "GPS": {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitude: ((42, 1), (21, 1), (3060, 100)),  # 42°21'30.60"
                piexif.GPSIFD.GPSLatitudeRef: "N",
                piexif.GPSIFD.GPSLongitude: ((71, 1), (3, 1), (4520, 100)),  # 71°03'45.20"
                piexif.GPSIFD.GPSLongitudeRef: "W",
                piexif.GPSIFD.GPSAltitude: (12500, 100),  # 125m
                piexif.GPSIFD.GPSAltitudeRef: 0,
                piexif.GPSIFD.GPSTimeStamp: ((14, 1), (30, 1), (15, 1)),
                piexif.GPSIFD.GPSDateStamp: "2025:09:09"
            },
            "1st": {},  # Thumbnail IFD (empty for now)
            "thumbnail": None
        }
        
        # Convert to bytes and save
        exif_bytes = piexif.dump(exif_dict)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', exif=exif_bytes, quality=95)
        buffer.seek(0)
        
        return buffer.getvalue(), exif_dict
        
    except ImportError:
        # Fallback without EXIF
        return create_minimal_test_image(), {}


def create_minimal_test_image():
    """Create minimal test image for environments without piexif"""
    try:
        from PIL import Image
        
        img = Image.new('RGB', (200, 150), color='orange')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)
        
        return buffer.getvalue()
    except ImportError:
        # Absolute fallback
        return b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 200 + b'\xff\xd9'


def compare_exif_data(original_exif: Dict[str, Any], extracted_exif: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two EXIF datasets and return comparison results"""
    comparison = {
        "matches": {},
        "missing": {},
        "differences": {},
        "total_original": len(original_exif),
        "total_extracted": len(extracted_exif)
    }
    
    for key, orig_value in original_exif.items():
        if key in extracted_exif:
            extracted_value = extracted_exif[key]
            
            # Convert values to strings for comparison (handles different types)
            orig_str = str(orig_value)
            extracted_str = str(extracted_value)
            
            if orig_str == extracted_str:
                comparison["matches"][key] = orig_value
            else:
                comparison["differences"][key] = {
                    "original": orig_value,
                    "extracted": extracted_value
                }
        else:
            comparison["missing"][key] = orig_value
    
    return comparison


class TestEXIFPreservation:
    """Test EXIF data preservation through storage operations"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.storage_config = {
            "base_path": os.path.join(self.test_dir, "storage"),
            "create_dirs": True,
            "preserve_structure": True
        }
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_exif_extraction_basic(self):
        """Test basic EXIF extraction functionality"""
        image_data, original_exif = create_test_image_with_comprehensive_exif()
        
        # Save image to temp file for processing
        temp_file = os.path.join(self.test_dir, "test_exif.jpg")
        with open(temp_file, 'wb') as f:
            f.write(image_data)
        
        # Test EXIF extraction
        try:
            from PIL import Image
            
            img = Image.open(io.BytesIO(image_data))
            extracted_exif = extract_exif_data(img, file_path=temp_file, file_bytes=image_data)
            
            assert isinstance(extracted_exif, dict)
            assert len(extracted_exif) > 0
            
            # Check for key EXIF fields
            expected_fields = ['Make', 'Model', 'DateTime', 'DateTimeOriginal']
            found_fields = [field for field in expected_fields if field in extracted_exif]
            
            assert len(found_fields) > 0, f"No expected EXIF fields found. Available: {list(extracted_exif.keys())}"
            
        except ImportError:
            pytest.skip("PIL not available for EXIF testing")
    
    def test_local_storage_exif_preservation(self):
        """Test EXIF preservation through local storage operations"""
        provider = LocalStorageProvider(self.storage_config)
        image_data, original_exif = create_test_image_with_comprehensive_exif()
        
        # Upload image
        upload_result = provider.upload_image(
            image_data=image_data,
            filename="exif_preservation_test.jpg",
            user_id="exif_test_user",
            metadata={"test": "exif_preservation"}
        )
        
        assert upload_result["success"] is True
        storage_path = upload_result["storage_path"]
        
        # Download image
        downloaded_data = provider.download_image(storage_path)
        assert downloaded_data is not None
        assert len(downloaded_data) > 0
        
        # Compare original and downloaded data
        assert downloaded_data == image_data, "Image data should be identical after storage round-trip"
        
        # Extract EXIF from downloaded image
        try:
            from PIL import Image
            
            downloaded_img = Image.open(io.BytesIO(downloaded_data))
            downloaded_exif = extract_exif_data(downloaded_img, file_bytes=downloaded_data)
            
            # Compare EXIF data
            if original_exif and downloaded_exif:
                # Check that key fields are preserved
                key_fields = ['Make', 'Model', 'DateTime', 'DateTimeOriginal']
                
                for field in key_fields:
                    if field in downloaded_exif:
                        print(f"EXIF field '{field}' preserved: {downloaded_exif[field]}")
                
                # Should have some EXIF data
                assert len(downloaded_exif) > 0, "EXIF data should be preserved"
                
        except ImportError:
            print("PIL not available - skipping detailed EXIF comparison")
    
    def test_gps_data_preservation(self):
        """Test GPS data preservation specifically"""
        provider = LocalStorageProvider(self.storage_config)
        image_data, original_exif = create_test_image_with_comprehensive_exif()
        
        # Upload and download
        upload_result = provider.upload_image(
            image_data=image_data,
            filename="gps_test.jpg",
            user_id="gps_user"
        )
        
        assert upload_result["success"] is True
        
        downloaded_data = provider.download_image(upload_result["storage_path"])
        assert downloaded_data == image_data
        
        # Extract GPS data specifically
        try:
            from PIL import Image
            
            img = Image.open(io.BytesIO(downloaded_data))
            extracted_exif = extract_exif_data(img, file_bytes=downloaded_data)
            
            # Look for GPS coordinates
            gps_fields = [key for key in extracted_exif.keys() if 'GPS' in key.upper()]
            
            if gps_fields:
                print(f"GPS fields preserved: {gps_fields}")
                
                # Check for decimal GPS coordinates (our conversion)
                if 'GPSLatitudeDecimal' in extracted_exif and 'GPSLongitudeDecimal' in extracted_exif:
                    lat = extracted_exif['GPSLatitudeDecimal']
                    lon = extracted_exif['GPSLongitudeDecimal']
                    
                    assert isinstance(lat, (int, float))
                    assert isinstance(lon, (int, float))
                    assert -90 <= lat <= 90
                    assert -180 <= lon <= 180
                    
                    print(f"GPS coordinates: {lat}, {lon}")
            
        except ImportError:
            pytest.skip("PIL not available for GPS testing")
    
    def test_image_processor_integration(self):
        """Test EXIF preservation through image processor workflow"""
        image_data, original_exif = create_test_image_with_comprehensive_exif()
        
        # Create BytesIO object to simulate file upload
        image_file = io.BytesIO(image_data)
        image_file.name = "processor_test.jpg"  # Simulate filename attribute
        
        # Use existing image processor (which saves to local storage)
        try:
            # This requires mocking session state, but tests the full workflow
            import unittest.mock
            
            with unittest.mock.patch('streamlit.session_state', {}):
                photo_data = process_image_file(image_file, "processor_test.jpg")
                
                if photo_data:
                    # Check that photo data includes expected fields
                    assert 'filename' in photo_data
                    assert 'file_path' in photo_data
                    assert 'date_taken' in photo_data
                    
                    # Check if GPS data was extracted
                    if 'lat' in photo_data and photo_data['lat']:
                        assert isinstance(photo_data['lat'], (int, float))
                        print(f"Extracted latitude: {photo_data['lat']}")
                    
                    if 'lon' in photo_data and photo_data['lon']:
                        assert isinstance(photo_data['lon'], (int, float))
                        print(f"Extracted longitude: {photo_data['lon']}")
                        
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
    
    def test_thumbnail_exif_handling(self):
        """Test EXIF handling in thumbnails"""
        provider = LocalStorageProvider(self.storage_config)
        image_data, original_exif = create_test_image_with_comprehensive_exif()
        
        # Generate thumbnail
        thumbnail_data = provider.generate_thumbnail(image_data, size=(150, 150))
        
        if thumbnail_data:
            assert len(thumbnail_data) < len(image_data), "Thumbnail should be smaller"
            
            # Thumbnails typically don't preserve full EXIF data (by design)
            # But they should be valid images
            try:
                from PIL import Image
                
                thumb_img = Image.open(io.BytesIO(thumbnail_data))
                assert thumb_img.size[0] <= 150
                assert thumb_img.size[1] <= 150
                
                # Check if any EXIF survived (depends on thumbnail generation method)
                thumb_exif = extract_exif_data(thumb_img, file_bytes=thumbnail_data)
                print(f"Thumbnail EXIF fields: {len(thumb_exif) if thumb_exif else 0}")
                
            except ImportError:
                pytest.skip("PIL not available for thumbnail testing")
    
    def test_large_exif_data_handling(self):
        """Test handling of images with large amounts of EXIF data"""
        # This test simulates images with extensive metadata
        provider = LocalStorageProvider(self.storage_config)
        
        try:
            from PIL import Image
            import piexif
            
            # Create image with extensive metadata
            img = Image.new('RGB', (400, 300), color='purple')
            
            # Create large EXIF with many fields
            exif_dict = {
                "0th": {
                    piexif.ImageIFD.Make: "ExtensiveCamera",
                    piexif.ImageIFD.Model: "MetadataRich-3000",
                    piexif.ImageIFD.DateTime: "2025:09:09 16:45:30",
                    piexif.ImageIFD.Software: "BeehiveTracker Pro",
                    piexif.ImageIFD.Artist: "Beekeeper John Doe",
                    piexif.ImageIFD.Copyright: "Beehive Farm 2025",
                    piexif.ImageIFD.ImageDescription: "Hive inspection - extensive metadata test"
                },
                "Exif": {
                    piexif.ExifIFD.DateTimeOriginal: "2025:09:09 16:45:30",
                    piexif.ExifIFD.ExposureTime: (1, 60),
                    piexif.ExifIFD.FNumber: (80, 10),
                    piexif.ExifIFD.ISOSpeedRatings: 400,
                    piexif.ExifIFD.FocalLength: (105, 1),
                    piexif.ExifIFD.LensModel: "BeeLens 105mm f/8",
                    piexif.ExifIFD.LensMake: "BeeOptics"
                }
            }
            
            exif_bytes = piexif.dump(exif_dict)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', exif=exif_bytes)
            buffer.seek(0)
            
            large_exif_data = buffer.getvalue()
            
            # Test upload/download with large EXIF
            upload_result = provider.upload_image(
                image_data=large_exif_data,
                filename="large_exif_test.jpg",
                user_id="large_exif_user"
            )
            
            assert upload_result["success"] is True
            
            downloaded_data = provider.download_image(upload_result["storage_path"])
            assert downloaded_data == large_exif_data
            
            # Verify EXIF preservation
            downloaded_img = Image.open(io.BytesIO(downloaded_data))
            downloaded_exif = extract_exif_data(downloaded_img, file_bytes=downloaded_data)
            
            assert len(downloaded_exif) > 5, "Should preserve multiple EXIF fields"
            
        except ImportError:
            pytest.skip("PIL and piexif required for large EXIF testing")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])