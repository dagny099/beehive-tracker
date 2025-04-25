import streamlit as st
import os
import time
from PIL import Image
from datetime import datetime
import io
# ------
from src.api_services.weather import get_weather_open_meteo
from src.api_services.vision import BeeVisionAnalyzer
from src.utils import (
    extract_exif, extract_gps_coordinates, get_palette, 
    rgb_to_hex, get_file_creation_date, parse_exif_date
)
from src.data_io import DataManager
from src.ui_components import (
    display_color_palette, display_image_preview,
    display_exif_data, display_annotation_form, display_location_input,
    display_weather_data, display_vision_analysis, display_entry_browser
)

# Setup page config
st.set_page_config(
    page_title="Hive Tracker",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Get PORT from environment variable for Cloud Run compatibility
PORT = int(os.environ.get("PORT", 8501))  # Default to 8501 for local development
# print(f"Application configured to use PORT: {PORT}")


# Constants
DEFAULT_IMAGE = "default_beepic.jpg"

# Set Google Cloud credentials - you should store this in an environment variable
# or use a .env file in production
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] =   ".streamlit/key.json"

# Initialize data manager
data_manager = DataManager()

# Initialize session state variables
def init_session_state():
    """Initialize all required session state variables."""
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
    if "vision_analysis" not in st.session_state:
        st.session_state.vision_analysis = {}
    if "active_image_source" not in st.session_state:
        st.session_state.active_image_source = "default"

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

    # Initialize session state
    init_session_state()
    
    # Add custom CSS
    st.markdown("""
        <style>
        .card-container {
            border: 2px solid white;
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 2em;
        }
        hr.custom-line {
            border: none;
            height: 1px;
            background-color: #ddd;
            margin: 1em 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Debug mode in sidebar
    st.sidebar.header("🔍 Session State Viewer (Debug Mode)")
    with st.sidebar.expander("View session_state variables", expanded=False):
        st.json({k: str(v) for k, v in st.session_state.items()})
    
    # Main content
    st.title("🐝 Hive Photo Metadata Tracker")
    
    # Add a toggle button for the entry browser
    show_browser = st.checkbox("📚 Browse Saved Entries", value=False)

    if show_browser:
        # Get all entries
        entries = data_manager.get_entry_summaries()
        
        # Display the entry browser
        selected_entry = display_entry_browser(entries, 
                                            current_filename=st.session_state.get('filename'))
        
        # If an entry was selected, load it
        if selected_entry:
            st.info(f"Loading entry: {selected_entry}")
            
            # Load the selected entry
            entry_data = data_manager.load_entry(selected_entry)
            
            if entry_data:
                # Update session state with loaded data
                st.session_state.update({
                    "filename": entry_data.get("filename"),
                    "exif_data": entry_data.get("exif_data", {}),
                    "date_taken": entry_data.get("date"),
                    "date_source": entry_data.get("date_source"),
                    "camera_model": entry_data.get("camera_model"),
                    "image_resolution": entry_data.get("image_resolution"),
                    "palette_hex": [
                        entry_data.get("palette_1", "#FFFFFF"),
                        entry_data.get("palette_2", "#FFFFFF"),
                        entry_data.get("palette_3", "#FFFFFF"),
                        entry_data.get("palette_4", "#FFFFFF"),
                        entry_data.get("palette_5", "#FFFFFF")
                    ],
                    "lat": entry_data.get("gps_lat"),
                    "lon": entry_data.get("gps_long"),
                    "weather_info": {
                        "weather_datetime": entry_data.get("weather_datetime"),
                        "weather_temperature_C": entry_data.get("weather_temperature_C"),
                        "weather_precipitation_mm": entry_data.get("weather_precipitation_mm"),
                        "weather_cloud_cover_percent": entry_data.get("weather_cloud_cover_percent"),
                        "weather_wind_speed_kph": entry_data.get("weather_wind_speed_kph"),
                        "weather_code": entry_data.get("weather_code"),
                        "weather_source": entry_data.get("weather_source", "Unknown")
                    },
                    "vision_analysis": entry_data.get("vision_analysis", {})
                })
                
                # Need to load the image from file
                image_found = False
                # Check current directory
                if os.path.exists(selected_entry):
                    image_found = True
                    temp_filename = selected_entry
                # Check other common locations
                elif os.path.exists(os.path.join("uploads", selected_entry)):
                    image_found = True
                    temp_filename = os.path.join("uploads", selected_entry)
                # Check if it's in the temp directory
                elif os.path.exists(f"temp_{selected_entry}"):
                    image_found = True
                    temp_filename = f"temp_{selected_entry}"

                if image_found:
                    st.session_state.temp_filename = temp_filename
                    st.session_state.active_image_source = "loaded"  # Mark as loaded entry
                    st.success(f"Image file found at: {temp_filename}. Loading preview...")
                    st.rerun()
                else:
                    st.warning(f"Image file not found: {selected_entry}. Metadata loaded without image.")
                    # Still keep the loaded data without an image
                    st.session_state.active_image_source = "loaded"
                    st.session_state.temp_filename = None
            else:
                st.error(f"Could not load entry data for: {selected_entry}")

    # Show current image source status
    if st.session_state.active_image_source == "default":
        st.info("📷 Viewing default example image")
    elif st.session_state.active_image_source == "uploaded":
        st.success(f"📷 Viewing your uploaded image: {st.session_state.get('filename', '')}")
    elif st.session_state.active_image_source == "loaded":
        st.success(f"📷 Viewing saved entry: {st.session_state.get('filename', 'Unknown')}")
    
    # File uploader with reset option
    col1, col2 = st.columns([4, 1])
    with col1:
        uploaded_file = st.file_uploader("Choose a hive image", type=["jpg", "jpeg", "png"], 
                                       label_visibility="collapsed")
    with col2:
        if st.button("Reset View", key="reset_btn"):
            # Clear the relevant session state
            for key in ["filename", "exif_data", "date_taken", "camera_model", 
                        "palette_hex", "vision_analysis"]:
                if key in st.session_state:
                    if key == "exif_data" or key == "vision_analysis":
                        st.session_state[key] = {}
                    elif key == "palette_hex":
                        st.session_state[key] = []
                    else:
                        st.session_state[key] = None
            # Reset to default image
            st.session_state.active_image_source = "default"
            st.session_state.temp_filename = DEFAULT_IMAGE
            st.rerun()
            
    # Handle file selection based on active image source
    if uploaded_file:
        # Process uploaded file
        img_name = uploaded_file.name
        temp_filename = f"temp_{uploaded_file.name}"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # Store temp filename in session state for vision API
        st.session_state.temp_filename = temp_filename
        st.session_state.active_image_source = "uploaded"
        # Process the new image
        process_image(temp_filename, img_name)
    elif st.session_state.active_image_source == "loaded" and st.session_state.get("temp_filename"):
        # Use the loaded entry's image
        temp_filename = st.session_state.temp_filename
        img_name = st.session_state.get("filename", os.path.basename(temp_filename) if temp_filename else "Unknown")
    else:
        # Use default image
        temp_filename = DEFAULT_IMAGE
        img_name = os.path.basename(DEFAULT_IMAGE)
        st.session_state.temp_filename = temp_filename
        st.session_state.active_image_source = "default"
        # Make sure we process the default image if needed
        if "filename" not in st.session_state or st.session_state.filename != img_name:
            process_image(temp_filename, img_name)
    
    # Only show the image and metadata if we have a valid file
    if temp_filename and os.path.exists(temp_filename):
        # Display image preview
        img = Image.open(temp_filename)
        sidebar_col = display_image_preview(img, img_name)
        
        # Display color palette in sidebar
        with sidebar_col:
            display_color_palette(st.session_state.palette_hex)
            
            st.markdown("<hr class='custom-line'>", unsafe_allow_html=True)
            st.markdown("**🤖 Semantic Metadata**")
            if st.session_state.get('vision_analysis') and st.session_state['vision_analysis'].get('labels'):
                labels = st.session_state['vision_analysis'].get('labels', [])
                bee_labels = [l for l in labels if l.get('bee_related', False)]
                
                if bee_labels:
                    st.markdown("**Bee-Related Labels:**")
                    for label in bee_labels[:3]:
                        st.text(f"• {label.get('description', 'Unknown')}")
                else:
                    st.text("No bee-related labels detected")
            else:
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
                "dominant_color": st.session_state.palette_hex[0] if st.session_state.palette_hex else "#FFFFFF",
                **{f"palette_{i+1}": color for i, color in enumerate(st.session_state.palette_hex[:5])},
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
    else:
        st.warning("No image available to display. Please upload an image or select a saved entry.")
    
    # Clean up temporary file
    if uploaded_file and os.path.exists(f"temp_{uploaded_file.name}"):
        os.remove(f"temp_{uploaded_file.name}")

    if st.sidebar.checkbox("Show Environment Info", False):
        st.sidebar.write(f"Server port: {PORT}")
        st.sidebar.write(f"Server IP: {socket.gethostbyname(socket.gethostname())}")
        
        # Show all environment variables
        st.sidebar.write("Environment Variables:")
        env_vars = {k: v for k, v in os.environ.items()}
        st.sidebar.json(env_vars)


if __name__ == "__main__":
    main()