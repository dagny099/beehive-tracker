# src/utils/image_processor.py
import streamlit as st
import io
from PIL import Image, ExifTags
from datetime import datetime
import os
import requests
from colorthief import ColorThief
import base64

def extract_exif_data(img):
    """Extract EXIF data from a PIL Image"""
    exif_data = {}
    
    try:
        # Get EXIF data
        exif = img._getexif()
        if exif:
            # Map EXIF tags to readable names
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_data[tag_name] = value
    except:
        pass
    
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
        
        # Extract EXIF data
        exif_data = extract_exif_data(img)
        
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
        
        # Extract GPS data
        lat, lon = None, None
        if "GPSInfo" in exif_data:
            gps_info = exif_data["GPSInfo"]
            # Process GPS data if available
            # This is a simplified approach - full implementation would be more complex
            if 2 in gps_info and 4 in gps_info:  # Latitude and Longitude
                lat = gps_info[2]
                lon = gps_info[4]
        
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