import streamlit as st
import io
import base64
from PIL import Image
from datetime import datetime
import os
import json
import pandas as pd
import plotly.graph_objects as go

# Import the timeline component module
from timeline_component import (
    initialize_session_state, 
    render_timeline, 
    process_url_image, 
    process_image
)

# Set page configuration
st.set_page_config(
    page_title="Hive Photo Metadata Tracker",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session_state()
if 'needs_rerun' not in st.session_state:
    st.session_state.needs_rerun = False
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None
if 'last_processed_url' not in st.session_state:
    st.session_state.last_processed_url = None

# Custom CSS for styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .honey-header {
        color: #FFC300;
        font-weight: 600;
    }
    .metadata-container {
        background-color: rgba(30, 30, 30, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        height: 100%;
    }
    .color-swatch {
        display: inline-block;
        width: 30px;
        height: 30px;
        margin-right: 5px;
        border-radius: 5px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    h3, h4 {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    .stMarkdown p {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.markdown("# 🐝 Hive Photo Metadata Tracker")
st.markdown("""
Track and organize your beehive photos with rich metadata, including weather conditions, 
color analysis, and computer vision insights.
""")

# Render the timeline
timeline = render_timeline()

# Add update timeline button and space after timeline
update_col, space_col = st.columns([1, 3])
with update_col:
    if st.button("🔄 Update Timeline", help="Click to refresh the timeline"):
        st.rerun()
        
st.markdown("<br><hr><br>", unsafe_allow_html=True)

# Create two columns for image input methods
col1, col2 = st.columns(2)

with col1:
    # URL input option
    st.markdown("### Enter an Image URL")
    img_url = st.text_input(
        "Image URL", 
        value="https://drive.google.com/uc?export=view&id=1aP-MjQ_wGG7RFyO0skn_cu7A2r7bh4iA",
        help="Enter the URL of a beehive photo"
    )
    
    if st.button("Process URL Image"):
        if img_url:
            # Check if this is a new URL
            if 'last_processed_url' not in st.session_state or st.session_state.last_processed_url != img_url:
                with st.spinner("Processing image from URL..."):
                    success = process_url_image(img_url)
                    if success:
                        st.success("Image processed successfully!")
                        # Record this URL as processed
                        st.session_state.last_processed_url = img_url
                        # No rerun - let Streamlit handle the flow
            else:
                st.info("Image already processed")
        else:
            st.warning("Please enter a valid image URL")

with col2:
    # File upload option
    st.markdown("### Upload an Image")
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Check if this is a new file upload
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != file_key:
            with st.spinner("Processing uploaded image..."):
                # Get the file name
                file_name = uploaded_file.name
                
                # Process the image
                success = process_image(uploaded_file, file_name)
                if success:
                    st.success("Image processed successfully!")
                    # Record this file as processed
                    st.session_state.last_uploaded_file = file_key
                    # No rerun - let Streamlit handle the flow


# Display the current image if available
if st.session_state.current_image:
    # Main container for image and metadata
    st.markdown("---")
    
    # Create columns for image and basic metadata
    img_col, meta_col = st.columns([3, 2])
    
    with img_col:
        # Display the image
        if hasattr(st.session_state.current_image, 'seek'):
            st.session_state.current_image.seek(0)
        
        if isinstance(st.session_state.current_image, bytes):
            img = Image.open(io.BytesIO(st.session_state.current_image))
            st.image(img, caption=st.session_state.filename, use_container_width=True)
        else:
            st.image(st.session_state.current_image, caption=st.session_state.filename, use_container_width=True)
    
    with meta_col:
        # Display core image metadata
        st.markdown("<h3>📷 Image Metadata</h3>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        # Basic metadata - note reorganized order
        st.markdown(f"**Date Taken:** {st.session_state.date_taken}")
        st.markdown(f"**Source:** {st.session_state.date_source}")
        st.markdown(f"**Filename:** {st.session_state.filename}")
        st.markdown(f"**Camera Model:** {st.session_state.camera_model}")
        st.markdown(f"**Resolution:** {st.session_state.image_resolution}")
        
        # Location
        if st.session_state.lat and st.session_state.lon:
            st.markdown(f"**Location:** {st.session_state.lat:.6f}, {st.session_state.lon:.6f}")
        else:
            st.markdown("**Location:** Not available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Three columns under the image for Color Palette, Weather Data, and Annotations
    st.markdown("### Inspection Details")
    col1, col2, col3 = st.columns(3)
    
    # Color palette column
    with col1:
        st.markdown("<h4>🎨 Color Palette</h4>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        palette_html = '<div style="display:flex; margin-bottom: 15px;">'
        for color in st.session_state.palette_hex:
            palette_html += f'<div class="color-swatch" style="background-color: {color};" title="{color}"></div>'
        palette_html += '</div>'
        st.markdown(palette_html, unsafe_allow_html=True)
        
        # Dominant color
        st.markdown(f"**Dominant Color:** {st.session_state.palette_hex[0]}")
        
        # Additional palette data could go here
        st.markdown("The dominant colors in your hive photo can reveal important information about hive health, pollen types, and seasonal changes.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Weather data column
    with col2:
        st.markdown("<h4>🌦️ Weather Data</h4>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        if st.session_state.weather_info["weather_source"] == "Not retrieved":
            st.markdown("Weather data not retrieved yet.")
            if st.button("Get Weather Data"):
                st.info("This would fetch weather data from Open-Meteo API in a real implementation.")
                # Simulate weather data for demo
                st.session_state.weather_info.update({
                    "weather_temperature_C": 23.5,
                    "weather_precipitation_mm": 0.0,
                    "weather_cloud_cover_percent": 25,
                    "weather_wind_speed_kph": 8.2,
                    "weather_code": 1,  # Clear sky
                    "weather_source": "Open-Meteo (Simulated)"
                })
                st.rerun()
        else:
            st.markdown(f"**Temperature:** {st.session_state.weather_info['weather_temperature_C']}°C")
            st.markdown(f"**Precipitation:** {st.session_state.weather_info['weather_precipitation_mm']} mm")
            st.markdown(f"**Cloud Cover:** {st.session_state.weather_info['weather_cloud_cover_percent']}%")
            st.markdown(f"**Wind Speed:** {st.session_state.weather_info['weather_wind_speed_kph']} km/h")
            st.markdown(f"**Source:** {st.session_state.weather_info['weather_source']}")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Annotations column
    with col3:
        st.markdown("<h4>🖊️ Annotations</h4>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        # Hive state dropdown
        hive_states = ["Select...", "Active Foraging", "Calm/Normal", "Defensive", "Swarming Preparation", "Queen Issues", "Honey Flow", "Dormant/Winter"]
        selected_state = st.selectbox("Hive State", hive_states, index=0)
        
        # Notes text area
        notes = st.text_area("Beekeeper Notes", height=100, 
                           placeholder="Enter your observations about the hive condition, behavior, etc.")
        
        if st.button("Save Annotations"):
            if selected_state != "Select...":
                st.success("Annotations saved!")
                # In a real app, you would save these to your data structure
            else:
                st.warning("Please select a hive state")
                
        st.markdown('</div>', unsafe_allow_html=True)

# Sidebar for additional controls and inspection details
with st.sidebar:
    st.header("Inspection Details")
    
    if st.session_state.inspections:
        st.write(f"Total Inspections: {len(st.session_state.inspections)}")
        st.write(f"Total Photos: {sum(insp['photo_count'] for insp in st.session_state.inspections)}")
        
        # Display a list of inspections
        st.subheader("Inspection History")
        for i, inspection in enumerate(st.session_state.inspections):
            date_str = inspection['date'].strftime("%b %d, %Y") if isinstance(inspection['date'], datetime) else inspection['date']
            if st.button(f"{date_str} - {inspection['photo_count']} photos", key=f"insp_{i}"):
                st.session_state.selected_inspection = i
                st.info(f"Selected inspection from {date_str}")
    else:
        st.info("No inspections recorded yet. Start by uploading a hive photo.")
    
    # Export data option
    st.subheader("Data Management")
    if st.button("Export Data (JSON)"):
        if st.session_state.inspections:
            # In a real app, this would save to a file
            st.success("Data would be exported as JSON")
        else:
            st.warning("No data to export")
    
    # Display cache information
    st.subheader("Cache Status")
    if 'url_image_cache' in st.session_state:
        cache_count = len(st.session_state.url_image_cache)
        st.write(f"URL Image Cache: {cache_count} images")
        
        if cache_count > 0 and st.button("Clear Cache"):
            st.session_state.url_image_cache = {}
            st.success("Cache cleared!")
            st.rerun()

# """
# # Test image URLs for development and testing:
# # 
# # "https://drive.google.com/uc?export=view&id=1aP-MjQ_wGG7RFyO0skn_cu7A2r7bh4iA",  #2024
# # "https://drive.google.com/uc?export=view&id=1iGytEfHMEXV2fNqI3z6aE49baoOt8W_B"  #2020
# # "https://drive.google.com/uc?export=view&id=1qbvRpDnseTcq1fd69wKkTUl5VDZMO4Vc"  #2023
# # "https://drive.google.com/uc?export=view&id=1ikdU2FT2L28hK9xH3Cy0R5BW-atAVd9l"  #2023, same day
# # "https://drive.google.com/uc?export=view&id=1KpMn4k3FRLeMzca8TJjblsq89sgQSSwN"  #2023, different day
# """