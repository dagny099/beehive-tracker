# src/utils/image_processor.py
import streamlit as st
import io
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import os
import requests
from colorthief import ColorThief
import base64
import exifread
import logging
from typing import Dict, Any, Tuple, Optional, Union
import warnings

# Optional import for PyExifTool (fallback)
try:
    from exiftool import ExifToolHelper
    EXIFTOOL_AVAILABLE = True
except ImportError:
    EXIFTOOL_AVAILABLE = False
    warnings.warn("PyExifTool not available - will use Pillow and exifread only")

def convert_gps_to_decimal(gps_coords, gps_ref):
    """Convert GPS coordinates from DMS (Degrees, Minutes, Seconds) to decimal format"""
    if not gps_coords or not gps_ref:
        return None
    
    try:
        if isinstance(gps_coords, (list, tuple)) and len(gps_coords) == 3:
            # Handle exifread format (IfdTag objects)
            if hasattr(gps_coords[0], 'values'):
                degrees = float(gps_coords[0].values[0]) / gps_coords[0].values[1]
                minutes = float(gps_coords[1].values[0]) / gps_coords[1].values[1]
                seconds = float(gps_coords[2].values[0]) / gps_coords[2].values[1]
            else:
                # Handle direct numeric format (already processed by exifread)
                degrees = float(gps_coords[0])
                minutes = float(gps_coords[1])
                seconds = float(gps_coords[2])
            
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            # Apply direction
            gps_ref_str = str(gps_ref) if not isinstance(gps_ref, str) else gps_ref
            if gps_ref_str.upper() in ['S', 'W']:
                decimal = -decimal
                
            return decimal
                
        # Handle exifread IfdTag format directly
        elif hasattr(gps_coords, 'values') and len(gps_coords.values) >= 3:
            # This is an IfdTag with DMS values
            degrees = float(gps_coords.values[0])
            minutes = float(gps_coords.values[1])
            
            # Handle fractional seconds (like 9534/625)
            if len(gps_coords.values) >= 3:
                seconds = float(gps_coords.values[2])
                # If it's a fraction string, evaluate it
                if isinstance(gps_coords.values[2], str) and '/' in str(gps_coords.values[2]):
                    parts = str(gps_coords.values[2]).split('/')
                    if len(parts) == 2:
                        seconds = float(parts[0]) / float(parts[1])
            else:
                seconds = 0.0
            
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            gps_ref_str = str(gps_ref) if not isinstance(gps_ref, str) else gps_ref
            if gps_ref_str.upper() in ['S', 'W']:
                decimal = -decimal
                
            return decimal
            
    except (AttributeError, TypeError, ValueError, ZeroDivisionError) as e:
        logging.warning(f"GPS conversion error: {e}")
        return None
    
    return None

def extract_exif_with_exifread(file_path_or_bytes):
    """Extract EXIF data using exifread library (primary method)"""
    exif_data = {}
    
    try:
        if isinstance(file_path_or_bytes, (str, os.PathLike)):
            with open(file_path_or_bytes, 'rb') as f:
                tags = exifread.process_file(f, details=True)
        else:
            # Reset BytesIO position
            if hasattr(file_path_or_bytes, 'seek'):
                file_path_or_bytes.seek(0)
            tags = exifread.process_file(file_path_or_bytes, details=True)
        
        # Convert exifread tags to standard format
        for tag, value in tags.items():
            # Clean up tag names (remove EXIF prefix)
            clean_tag = tag.replace('EXIF ', '').replace('Image ', '').replace('GPS ', '')
            
            # Convert IfdTag values to appropriate types
            if hasattr(value, 'values'):
                if len(value.values) == 1:
                    exif_data[clean_tag] = value.values[0]
                else:
                    exif_data[clean_tag] = value.values
            else:
                exif_data[clean_tag] = str(value)
        
        # Special handling for GPS data
        if any(tag.startswith('GPS') for tag in tags.keys()):
            gps_info = {}
            for tag, value in tags.items():
                if tag.startswith('GPS'):
                    gps_tag = tag.replace('GPS ', '')
                    gps_info[gps_tag] = value
            
            # Extract latitude and longitude with better field handling
            lat_key = None
            lat_ref_key = None
            lon_key = None
            lon_ref_key = None
            
            # Find GPS coordinate fields (handle different tag formats)
            for tag, value in tags.items():
                if 'GPSLatitude' in tag and 'Ref' not in tag:
                    lat_key = tag
                elif 'GPSLatitudeRef' in tag:
                    lat_ref_key = tag
                elif 'GPSLongitude' in tag and 'Ref' not in tag:
                    lon_key = tag
                elif 'GPSLongitudeRef' in tag:
                    lon_ref_key = tag
            
            if lat_key and lat_ref_key and lat_key in tags and lat_ref_key in tags:
                lat = convert_gps_to_decimal(tags[lat_key], tags[lat_ref_key])
                if lat is not None:
                    exif_data['GPSLatitudeDecimal'] = lat
            
            if lon_key and lon_ref_key and lon_key in tags and lon_ref_key in tags:
                lon = convert_gps_to_decimal(tags[lon_key], tags[lon_ref_key])
                if lon is not None:
                    exif_data['GPSLongitudeDecimal'] = lon
                    
    except Exception as e:
        logging.warning(f"ExifRead extraction failed: {e}")
    
    return exif_data

def extract_exif_with_pillow(img):
    """Extract EXIF data using Pillow's getexif() method (modern images)"""
    exif_data = {}
    
    try:
        # Use modern getexif() method instead of deprecated _getexif()
        exif_dict = img.getexif()
        
        if exif_dict:
            # Convert to readable tags
            for tag_id, value in exif_dict.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
            
            # Handle GPS data specifically
            if 'GPSInfo' in exif_data:
                gps_info = exif_data['GPSInfo']
                gps_data = {}
                
                for gps_tag_id, value in gps_info.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_data[gps_tag] = value
                
                # Convert GPS coordinates to decimal
                if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                    lat = convert_gps_to_decimal(gps_data['GPSLatitude'], gps_data['GPSLatitudeRef'])
                    if lat is not None:
                        exif_data['GPSLatitudeDecimal'] = lat
                
                if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                    lon = convert_gps_to_decimal(gps_data['GPSLongitude'], gps_data['GPSLongitudeRef'])
                    if lon is not None:
                        exif_data['GPSLongitudeDecimal'] = lon
                        
    except Exception as e:
        logging.warning(f"Pillow EXIF extraction failed: {e}")
    
    return exif_data

def extract_exif_with_pyexiftool(file_path):
    """Extract EXIF data using PyExifTool (fallback for complex cases)"""
    exif_data = {}
    
    if not EXIFTOOL_AVAILABLE:
        return exif_data
    
    try:
        with ExifToolHelper() as et:
            metadata = et.get_metadata(file_path)
            
            if metadata:
                # Convert ExifTool format to our standard format
                for key, value in metadata[0].items():
                    # Clean up the key name
                    clean_key = key.replace('EXIF:', '').replace('GPS:', '').replace('File:', '')
                    exif_data[clean_key] = value
                    
    except Exception as e:
        logging.warning(f"PyExifTool extraction failed: {e}")
    
    return exif_data

def extract_exif_data(img, file_path=None, file_bytes=None):
    """
    Multi-library EXIF extraction with fallback hierarchy:
    1. Primary: exifread for compatibility
    2. Secondary: Pillow.getexif() for modern images  
    3. Fallback: PyExifTool for complex cases
    """
    exif_data = {}
    
    # Method 1: Try exifread (primary)
    try:
        if file_bytes:
            exif_data = extract_exif_with_exifread(io.BytesIO(file_bytes))
        elif file_path and os.path.exists(file_path):
            exif_data = extract_exif_with_exifread(file_path)
            
        if exif_data:
            logging.info("EXIF extracted successfully with exifread")
            return exif_data
    except Exception as e:
        logging.warning(f"ExifRead method failed: {e}")
    
    # Method 2: Try Pillow getexif() (secondary)
    try:
        pillow_data = extract_exif_with_pillow(img)
        if pillow_data:
            exif_data.update(pillow_data)
            logging.info("EXIF extracted successfully with Pillow")
            if exif_data:  # If we got some data, return it
                return exif_data
    except Exception as e:
        logging.warning(f"Pillow method failed: {e}")
    
    # Method 3: Try PyExifTool (fallback)
    if file_path and EXIFTOOL_AVAILABLE:
        try:
            pyexif_data = extract_exif_with_pyexiftool(file_path)
            if pyexif_data:
                exif_data.update(pyexif_data)
                logging.info("EXIF extracted successfully with PyExifTool")
        except Exception as e:
            logging.warning(f"PyExifTool method failed: {e}")
    
    return exif_data

def get_image_resolution(img):
    """Get image dimensions as a string"""
    try:
        width, height = img.size
        return f"{width} x {height}"
    except:
        return "Unknown"

def extract_color_palette(img, count=5):
    """Extract dominant colors from image"""
    try:
        # Convert PIL Image to BytesIO
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # Use ColorThief to extract palette
        color_thief = ColorThief(img_byte_arr)
        palette = color_thief.get_palette(color_count=count, quality=10)
        
        # Convert RGB tuples to hex
        hex_colors = ['#%02x%02x%02x' % rgb for rgb in palette]
        return hex_colors
    except Exception as e:
        # Return default palette on error
        return ["#CCCCCC", "#DDDDDD", "#EEEEEE", "#EFEFEF", "#F5F5F5"]

def process_image_file(image_file, filename):
    """Process an uploaded image file and save it locally"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate a unique filename to avoid collisions
        timestamp = int(datetime.now().timestamp())
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Read file content
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        if hasattr(image_file, 'read'):
            file_content = image_file.read()
        else:
            file_content = image_file
            
        # Save to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Reset file pointer for image processing
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        # Open with PIL for processing
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
            img = Image.open(image_file)
        else:
            img = Image.open(io.BytesIO(file_content))
        
        # Get image resolution
        resolution = get_image_resolution(img)
        
        # Extract EXIF data using multi-library approach
        exif_data = extract_exif_data(img, file_path=file_path, file_bytes=file_content)
        
        # Extract date taken
        date_taken = "Unknown"
        date_source = "File metadata"
        
        if "DateTimeOriginal" in exif_data:
            date_taken = exif_data["DateTimeOriginal"]
        elif "DateTime" in exif_data:
            date_taken = exif_data["DateTime"]
        else:
            # Use file creation time as fallback
            date_taken = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
            date_source = "Current time (no EXIF date found)"
        
        # Extract GPS data using new decimal coordinates
        lat, lon = None, None
        if "GPSLatitudeDecimal" in exif_data:
            lat = exif_data["GPSLatitudeDecimal"]
        if "GPSLongitudeDecimal" in exif_data:
            lon = exif_data["GPSLongitudeDecimal"]
        
        # Extract camera model
        camera_model = "Unknown"
        if "Make" in exif_data and "Model" in exif_data:
            camera_model = f"{exif_data['Make']} {exif_data['Model']}"
        elif "Model" in exif_data:
            camera_model = exif_data["Model"]
        
        # Extract color palette
        palette_hex = extract_color_palette(img)
        
        # Set session state variables
        st.session_state.current_image = file_content
        st.session_state.filename = filename
        st.session_state.date_taken = date_taken
        st.session_state.date_source = date_source
        st.session_state.image_resolution = resolution
        st.session_state.camera_model = camera_model
        st.session_state.lat = lat
        st.session_state.lon = lon
        st.session_state.palette_hex = palette_hex
        
        # Calculate file size in MB
        file_size_mb = len(file_content) / (1024 * 1024)
        st.session_state.image_size_mb = file_size_mb
        
        # Prepare photo data object
        photo_data = {
            'filename': filename,
            'file_path': file_path,
            'date_taken': date_taken,
            'camera_model': camera_model,
            'resolution': resolution,
            'color_palette': palette_hex,
            'file_size_mb': file_size_mb,
            'lat': lat,
            'lon': lon
        }
        
        # Add more EXIF data if available
        if "ExposureTime" in exif_data:
            exposure_time = exif_data["ExposureTime"]
            if isinstance(exposure_time, tuple) and exposure_time[0] and exposure_time[1]:
                st.session_state.exposure_time = f"{exposure_time[0]}/{exposure_time[1]} sec"
                photo_data['exposure_time'] = f"{exposure_time[0]}/{exposure_time[1]} sec"
        
        if "FNumber" in exif_data:
            f_number = exif_data["FNumber"]
            if isinstance(f_number, tuple) and f_number[0] and f_number[1]:
                st.session_state.f_number = f_number[0] / f_number[1]
                photo_data['f_number'] = f_number[0] / f_number[1]
        
        if "FocalLength" in exif_data:
            focal_length = exif_data["FocalLength"]
            if isinstance(focal_length, tuple) and focal_length[0] and focal_length[1]:
                st.session_state.focal_length = f"{focal_length[0] / focal_length[1]} mm"
                photo_data['focal_length'] = f"{focal_length[0] / focal_length[1]} mm"
        
        return photo_data
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def process_url_image(url):
    """Process an image from a URL"""
    try:
        # Check cache first
        if 'url_image_cache' in st.session_state and url in st.session_state.url_image_cache:
            # Use cached image data
            image_data = st.session_state.url_image_cache[url]
            img = Image.open(io.BytesIO(image_data))
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename:
                filename = "image_from_url.jpg"
                
            # Process the cached image
            return process_image_file(io.BytesIO(image_data), filename)
        else:
            # Download the image
            response = requests.get(url)
            if response.status_code == 200:
                # Get image data
                image_data = response.content
                
                # Cache the image data
                if 'url_image_cache' not in st.session_state:
                    st.session_state.url_image_cache = {}
                st.session_state.url_image_cache[url] = image_data
                
                # Extract filename from URL
                filename = url.split('/')[-1]
                if '?' in filename:
                    filename = filename.split('?')[0]
                if not filename:
                    filename = "image_from_url.jpg"
                
                # Process the downloaded image
                return process_image_file(io.BytesIO(image_data), filename)
            else:
                st.error(f"Failed to download image. Status code: {response.status_code}")
                return False
    except Exception as e:
        st.error(f"Error processing URL image: {e}")
        return False