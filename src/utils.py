import os
from datetime import datetime
from PIL import Image, ExifTags
from colorthief import ColorThief

def extract_exif(image_file):
    """Extract EXIF metadata from an image file."""
    img = Image.open(image_file)
    exif_data = {}
    if hasattr(img, '_getexif') and img._getexif() is not None:
        exif = img._getexif()
        for tag, value in exif.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            exif_data[decoded] = value
    return exif_data

def extract_gps_coordinates(exif_data):
    """Extract GPS coordinates from EXIF data if available."""
    if 'GPSInfo' not in exif_data:
        return None, None
        
    gps_info = exif_data['GPSInfo']
    
    # Extract latitude
    if 2 in gps_info:
        lat_data = gps_info[2]
        lat_ref = gps_info.get(1, 'N')
        
        # Convert to float
        try:
            lat = float(lat_data[0]) + float(lat_data[1])/60 + float(lat_data[2])/3600
            if lat_ref == 'S':
                lat = -lat
        except (TypeError, ValueError):
            lat = None
    else:
        lat = None
        
    # Extract longitude
    if 4 in gps_info:
        lon_data = gps_info[4]
        lon_ref = gps_info.get(3, 'E')
        
        # Convert to float
        try:
            lon = float(lon_data[0]) + float(lon_data[1])/60 + float(lon_data[2])/3600
            if lon_ref == 'W':
                lon = -lon
        except (TypeError, ValueError):
            lon = None
    else:
        lon = None
        
    return lat, lon

def get_palette(image_file, color_count=5):
    """Extract a color palette from an image."""
    with open(image_file, 'rb') as f:
        color_thief = ColorThief(f)
        palette = color_thief.get_palette(color_count=color_count)
        return palette

def rgb_to_hex(rgb):
    """Convert RGB tuple to hexadecimal color code."""
    return '#%02x%02x%02x' % rgb

def get_file_creation_date(filepath):
    """Get the creation date of a file."""
    try:
        timestamp = os.path.getctime(filepath)
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown"

def parse_exif_date(date_string):
    """Parse EXIF date format into a datetime object."""
    try:
        return datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S")
    except (ValueError, TypeError):
        return None
    
    