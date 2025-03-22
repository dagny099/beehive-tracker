import streamlit as st
import os
from PIL import Image
from datetime import datetime
import io

# Import modules
from api_services import get_weather_open_meteo, BeeVisionAnalyzer
from utils import (
    extract_exif, extract_gps_coordinates, get_palette, 
    rgb_to_hex, get_file_creation_date, parse_exif_date
)
from data_io import DataManager
from ui_components import (
    setup_page_config, display_color_palette, display_image_preview,
    display_exif_data, display_annotation_form, display_location_input,
    display_weather_data, display_vision_analysis  # Add this import
)
import os

# Constants
DEFAULT_IMAGE = "default_beepic.jpg"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/barbaraihidalgo-sotelo//PROJECTS/gen-lang-client-0846443908-27b15751bbd1.json"

print(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])

# Initialize data manager
data_manager = DataManager()

# Initialize session state variables
def init_session_state():
    if "exif_data" not in st.session_state:
        st.session_state.exif_data = {}
    if "palette_hex" not in st.session_state:
        st.session_state.palette_hex = []
    if "weather_info" not in st.session_state:
        st.session_state.weather_info = {}
    if "lat" not in st.session_state:
        st.session_state.lat = None
    if "lon" not in st.session_state:
        st.session_state.lon = None

def process_image(img_file, img_name):
    """
    Process an image to extract metadata.
    
    Parameters:
        img_file (str or file-like): Path to image or file-like object
        img_name (str): Name of the image file
        
    Returns:
        bool: True if processing was successful
    """
    try:
        # Extract EXIF data
        exif = extract_exif(img_file)
        
        # Get date taken
        date_taken = exif.get("DateTimeOriginal") or get_file_creation_date(img_file)
        date_source = "EXIF" if "DateTimeOriginal" in exif else "File Creation Date"
        
        # Extract GPS coordinates if available
        lat, lon = extract_gps_coordinates(exif)
        if lat and lon:
            st.session_state.lat = lat
            st.session_state.lon = lon
        
        # Get camera model
        camera_model = exif.get("Model", "Unknown")
        
        # Extract color palette
        palette_rgb = get_palette(img_file)
        palette_hex = [rgb_to_hex(c) for c in palette_rgb]
        
        # Get image resolution
        img = Image.open(img_file)
        image_resolution = f"{img.width} x {img.height}"
        
        # Update session state
        st.session_state.update({
            "filename": img_name,
            "exif_data": exif,
            "date_taken": date_taken,
            "date_source": date_source,
            "camera_model": camera_model,
            "palette_hex": palette_hex,
            "image_resolution": image_resolution,
            "weather_info": {
                "weather_datetime": date_taken,
                "weather_temperature_C": None,
                "weather_precipitation_mm": None,
                "weather_cloud_cover_percent": None,
                "weather_wind_speed_kph": None,
                "weather_code": None,
                "weather_source": "Not retrieved"
            }
        })
        
        return True
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return False

def get_weather_data():
    """
    Retrieve weather data based on location and date.
    
    Returns:
        dict: Weather information
    """
    try:
        # Parse the date from EXIF or file creation date
        date_str = st.session_state.date_taken
        
        # Handle EXIF date format (e.g., "2023:04:15 14:30:45")
        if ":" in date_str and date_str.count(":") >= 2:
            dt = parse_exif_date(date_str)
        else:
            # Try standard datetime parsing
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = None
                st.warning(f"Could not parse date: {date_str}")
        
        if dt and st.session_state.lat is not None and st.session_state.lon is not None:
            # Show status message
            with st.spinner("Retrieving weather data from Open-Meteo API..."):
                # Get weather data
                weather_info = get_weather_open_meteo(
                    float(st.session_state.lat), 
                    float(st.session_state.lon), 
                    dt
                )
                
                # Update session state
                st.session_state.weather_info = weather_info
                
                return weather_info
        else:
            st.warning("Could not retrieve weather data: Missing location or datetime information.")
            
            # Return empty weather info with error message
            return {
                "weather_datetime": date_str if date_str else str(datetime.now()),
                "weather_temperature_C": None,
                "weather_precipitation_mm": None,
                "weather_cloud_cover_percent": None,
                "weather_wind_speed_kph": None,
                "weather_code": None,
                "weather_source": "Error: Missing location or datetime information"
            }
    except Exception as e:
        st.error(f"Error retrieving weather data: {e}")
        return st.session_state.weather_info
    

def analyze_image_vision():
    """
    Analyze image using Google Cloud Vision API.
    
    Returns:
        dict: Vision analysis results
    """
    try:
        # Check if temp_filename exists
        if not st.session_state.get('temp_filename'):
            st.warning("No image available for analysis")
            return None
            
        # Check if file exists
        temp_filename = st.session_state.get('temp_filename')
        if not os.path.exists(temp_filename):
            st.error(f"File does not exist: {temp_filename}")
            return None
            
        # Check credentials
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            st.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return None
        if not os.path.exists(credentials_path):
            st.error(f"Credentials file not found: {credentials_path}")
            return None
            
        st.info(f"Using credentials from: {credentials_path}")
        
        with st.spinner("Analyzing image with Google Cloud Vision..."):
            # Create the vision analyzer if it doesn't exist
            if 'vision_analyzer' not in st.session_state:
                st.session_state.vision_analyzer = BeeVisionAnalyzer()
            
            # Log the file we're analyzing
            st.info(f"Analyzing file: {temp_filename}")
            
            # Analyze image
            analysis = st.session_state.vision_analyzer.analyze_image(temp_filename)
            
            # Check for errors in the analysis
            if 'error' in analysis:
                st.error(f"Vision API error: {analysis['error']}")
                return None
                
            # Update session state
            st.session_state.vision_analysis = analysis
            
            st.success("Image analysis complete!")
            return analysis
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        st.error(f"Error analyzing image with Vision API: {e}")
        st.code(error_details)
        return None
        

def main():
    # Setup page config
    setup_page_config()
    
    # Initialize session state
    init_session_state()
    
    # Debug mode in sidebar
    st.sidebar.header("🔍 Session State Viewer (Debug Mode)")
    with st.sidebar.expander("View session_state variables", expanded=False):
        st.json({k: str(v) for k, v in st.session_state.items()})
    
    # Main content
    st.title("🐝 Hive Photo Metadata Tracker")
    
    # File uploader
    img_file = DEFAULT_IMAGE
    img_name = os.path.basename(img_file)
    
    if os.path.exists(DEFAULT_IMAGE):
        uploaded_file = st.file_uploader("Choose a hive image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    else:
        uploaded_file = st.file_uploader("Choose a hive image", type=["jpg", "jpeg", "png"])
        
    if uploaded_file:
        img_file = uploaded_file
        img_name = uploaded_file.name
        temp_filename = f"temp_{uploaded_file.name}"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # Store temp filename in session state for vision API
        st.session_state.temp_filename = temp_filename
    else:
        temp_filename = img_file
        st.session_state.temp_filename = temp_filename
    
    # Process image if it's new or not processed yet
    if "filename" not in st.session_state or st.session_state.filename != img_name:
        process_image(temp_filename, img_name)
    
    # Display image preview
    img = Image.open(temp_filename)
    sidebar_col = display_image_preview(img, img_name)
    
    # Display color palette in sidebar
    with sidebar_col:
        display_color_palette(st.session_state.palette_hex)
        
        st.markdown("<hr class='custom-line'>", unsafe_allow_html=True)
        st.markdown("**🤖 Semantic Metadata**")
        st.text("Labels: ...")
        st.text("Objects: ...")
        st.text("Confidence: ...")
        st.text("Extracted Colors: ...")
    
    # Metadata section
    st.markdown("<hr class='custom-line'>", unsafe_allow_html=True)
    st.markdown("### 🧾 Photo Metadata")
    col1, col2, col3 = st.columns(3)
    
    st.markdown("<hr class='custom-line'>", unsafe_allow_html=True)
    
    # EXIF data
    with col1:
        display_exif_data(
            st.session_state.exif_data, 
            st.session_state.date_taken, 
            st.session_state.date_source, 
            st.session_state.camera_model, 
            st.session_state.image_resolution
        )
    
    # Annotations
    with col2:
        notes, hive_state = display_annotation_form()
    
    # Weather data
    with col3:
        # No longer wrapped in an expander since display_weather_data handles its own layout
        get_weather = display_weather_data(st.session_state.weather_info)
        if get_weather:
            st.session_state.weather_info = get_weather_data()
            st.rerun()
            # st.markdown("Weather data will be implemented in the next step.")
            # st.json(st.session_state.weather_info)
    
    # ---- 
    st.markdown("### 🤖 Computer Vision Analysis")
    run_vision = display_vision_analysis(st.session_state.get('vision_analysis', {}))
    if run_vision:
        analyze_image_vision()
        st.rerun()


    # Location input
    lat, lon = display_location_input(st.session_state.lat, st.session_state.lon)
    
    # If location changed, update session state
    if lat != st.session_state.lat or lon != st.session_state.lon:
        st.session_state.lat = lat
        st.session_state.lon = lon
    
    # Save button
    if st.button("Update Entry"):
        # Prepare metadata entry
        metadata_entry = {
            "date": st.session_state.date_taken,
            "date_source": st.session_state.date_source,
            "filename": img_name,
            "image_resolution": st.session_state.image_resolution,
            "camera_model": st.session_state.camera_model,
            "dominant_color": st.session_state.palette_hex[0],
            **{f"palette_{i+1}": color for i, color in enumerate(st.session_state.palette_hex)},
            **st.session_state.weather_info,
            "hive_state": hive_state,
            "notes": notes,
            "gps_lat": st.session_state.lat,
            "gps_long": st.session_state.lon,
            "vision_analysis": st.session_state.get('vision_analysis', {})  # Add vision analysis
        }
        
        # Save metadata
        if data_manager.save_entry(metadata_entry):
            st.success("Metadata saved to CSV and JSON!")
        else:
            st.error("Failed to save metadata!")
    
    # Clean up temporary file
    if uploaded_file and os.path.exists(temp_filename):
        os.remove(temp_filename)

if __name__ == "__main__":
    main()

