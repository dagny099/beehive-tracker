import pytest
import os
from pathlib import Path
from PIL import Image
import tempfile
import shutil

# Test data paths
ASSETS_DIR = Path(__file__).parent.parent / "assets"

@pytest.fixture(scope="session") 
def assets_dir():
    """Path to test assets directory"""
    return ASSETS_DIR

@pytest.fixture(scope="session")
def test_images():
    """Dictionary of test images by device type"""
    return {
        "samsung_s9": ASSETS_DIR / "bees_pollen_visible.jpg",
        "samsung_s9_portrait": ASSETS_DIR / "queen_bee_closeup.jpg", 
        "samsung_s9_comb": ASSETS_DIR / "comb_queen_bee.jpg",
        "pixel_7_new": ASSETS_DIR / "capped_brood_top_bar.jpg",
        "pixel_7_old": ASSETS_DIR / "comb_new.jpg",
        "png_no_exif": ASSETS_DIR / "comb_queen_bee.png"
    }

@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_image_bytes():
    """Sample image as bytes for testing"""
    # Create a minimal valid JPEG image
    img = Image.new('RGB', (100, 100), color='red')
    import io
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

@pytest.fixture
def expected_gps_coordinates():
    """Known GPS coordinates for test images"""
    return {
        "samsung_s9": {"lat": 40.75895, "lon": -73.9861111},  # Approximate NYC
        "pixel_7_new": {"lat": 37.7749, "lon": -122.4194},    # Approximate SF
        # Add more as we discover actual coordinates in test images
    }

@pytest.fixture
def expected_device_info():
    """Expected device information for test images"""
    return {
        "samsung_s9": {
            "make": "samsung",
            "model": "SM-G960U1",
            "orientation": "upper-right"  # From file command output
        },
        "pixel_7": {
            "make": "Google", 
            "model": "Pixel 7",
            "orientation": "upper-left"
        }
    }

@pytest.fixture
def corrupted_image_data():
    """Corrupted image data for edge case testing"""
    return b'\x00\x01\x02\x03'  # Invalid image data

@pytest.fixture
def empty_image_data():
    """Empty image data for edge case testing"""
    return b''