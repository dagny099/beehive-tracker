# src/utils/session_manager.py
import streamlit as st
from datetime import datetime
import os
import json

def initialize_full_session_state():
    """Initialize all session state variables for the application"""
    # Core UI state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Image processing state
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = False
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None
    if 'last_processed_url' not in st.session_state:
        st.session_state.last_processed_url = None
    
    # Currently selected items
    if 'selected_inspection' not in st.session_state:
        st.session_state.selected_inspection = None
    if 'selected_photo' not in st.session_state:
        st.session_state.selected_photo = None
    if 'view_photo_details' not in st.session_state:
        st.session_state.view_photo_details = False
    
    # Current image state
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'filename' not in st.session_state:
        st.session_state.filename = ""
    if 'date_taken' not in st.session_state:
        st.session_state.date_taken = "Unknown"
    if 'date_source' not in st.session_state:
        st.session_state.date_source = "Unknown"
    if 'camera_model' not in st.session_state:
        st.session_state.camera_model = "Unknown"
    if 'image_resolution' not in st.session_state:
        st.session_state.image_resolution = "Unknown"
    if 'lat' not in st.session_state:
        st.session_state.lat = None
    if 'lon' not in st.session_state:
        st.session_state.lon = None
    if 'palette_hex' not in st.session_state:
        st.session_state.palette_hex = ["#CCCCCC", "#DDDDDD", "#EEEEEE"]
    
    # Weather info
    if 'weather_info' not in st.session_state:
        st.session_state.weather_info = {
            "weather_temperature_C": None,
            "weather_precipitation_mm": None,
            "weather_cloud_cover_percent": None,
            "weather_wind_speed_kph": None,
            "weather_code": None,
            "weather_source": "Not retrieved"
        }
    if 'weather_fetched' not in st.session_state:
        st.session_state.weather_fetched = False
    
    # Vision API results
    if 'vision_api_results' not in st.session_state:
        st.session_state.vision_api_results = None
    
    # Collection of inspections
    if 'inspections' not in st.session_state:
        st.session_state.inspections = []
    
    # Image caching
    if 'url_image_cache' not in st.session_state:
        st.session_state.url_image_cache = {}
    
    # Load saved data if available
    load_data_from_disk()

def save_data_to_disk():
    """Save inspection data to disk"""
    try:
        data_dir = os.path.join("data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Prepare data for serialization
        save_data = {
            "inspections": []
        }
        
        # Process inspections for saving
        for inspection in st.session_state.inspections:
            # Create a serializable copy
            insp_copy = inspection.copy()
            
            # Process photos to remove non-serializable data
            if "photos" in insp_copy:
                for photo in insp_copy["photos"]:
                    # Remove image data, keeping only the file path
                    if "data" in photo:
                        del photo["data"]
            
            # Handle datetime objects
            if "date" in insp_copy and isinstance(insp_copy["date"], datetime):
                insp_copy["date"] = insp_copy["date"].isoformat()
                
            save_data["inspections"].append(insp_copy)
        
        # Save to JSON file
        with open(os.path.join(data_dir, "inspections.json"), "w") as f:
            json.dump(save_data, f, indent=2)
            
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def load_data_from_disk():
    """Load inspection data from disk"""
    try:
        data_file = os.path.join("data", "inspections.json")
        
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)
                
            # Process loaded inspections
            if "inspections" in data:
                for i, inspection in enumerate(data["inspections"]):
                    # Convert date strings back to datetime objects
                    if "date" in inspection and isinstance(inspection["date"], str):
                        try:
                            inspection["date"] = datetime.fromisoformat(inspection["date"])
                        except:
                            # Keep as string if parsing fails
                            pass
                    
                    # Load any photo files
                    if "photos" in inspection:
                        for photo in inspection["photos"]:
                            if "file_path" in photo and os.path.exists(photo["file_path"]):
                                # Don't load the actual image data here to save memory
                                # It will be loaded when needed
                                pass
                
                # Set in session state
                st.session_state.inspections = data["inspections"]
                
            return True
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return False