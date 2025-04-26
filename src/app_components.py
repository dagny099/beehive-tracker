# src/app_components.py
import streamlit as st
import io
import time
from PIL import Image
from datetime import datetime
import os
import json
from src.timeline_component import process_url_image
from src.utils.data_handler import add_photo_to_inspection



# Function to display the image and photo metadata
def display_image_and_photo_metadata():
    # Create columns for image and basic metadata
    img_col, meta_col = st.columns([3, 2])
    
    with img_col:
        # Display the image
        if st.session_state.current_image is not None:
            if hasattr(st.session_state.current_image, 'seek'):
                st.session_state.current_image.seek(0)
            
            # Handle different image types efficiently
            if isinstance(st.session_state.current_image, bytes):
                img = Image.open(io.BytesIO(st.session_state.current_image))
                st.image(img, caption=st.session_state.filename, use_container_width=True)
            else:
                st.image(st.session_state.current_image, caption=st.session_state.filename, use_container_width=True)
    
    with meta_col:
        # Display PHOTO metadata
        st.markdown("<h3>📷 Photo Metadata</h3>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        # Basic photo metadata
        st.markdown(f"**Filename:** {st.session_state.filename}")
        st.markdown(f"**Date Taken:** {st.session_state.date_taken}")
        st.markdown(f"**Resolution:** {st.session_state.image_resolution}")
        st.markdown(f"**Camera Model:** {st.session_state.camera_model}")
        st.markdown(f"**Source:** {st.session_state.date_source}")
        
        # Display Inspection association if available
        if hasattr(st.session_state, 'associated_inspection') and st.session_state.associated_inspection:
            inspection_id = st.session_state.associated_inspection
            st.markdown(f"**Part of Inspection:** {inspection_id}")
        else:
            st.markdown("**Part of Inspection:** Not assigned")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Function to display inspection metadata
def display_inspection_metadata():
    # Add a more prominent header with an icon and color
    st.markdown("""
    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #3366cc; margin-bottom: 20px;">
    <h3 style="color: #3366cc; margin-top: 0;">🔍 Inspection Overview</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create 2 columns for inspection metadata
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="metadata-container" style="border-left: 3px solid #3366cc;">', unsafe_allow_html=True)
        
        # Display inspection date with larger text
        if hasattr(st.session_state, 'inspection_date') and st.session_state.inspection_date:
            inspection_date = st.session_state.inspection_date
            st.markdown(f"<h4>📅 <span style='color:#3366cc;'>Inspection Date:</span></h4> {inspection_date.strftime('%B %d, %Y') if isinstance(inspection_date, datetime) else inspection_date}", unsafe_allow_html=True)
        else:
            # Use the photo date as a default
            date_str = st.session_state.date_taken
            if date_str and date_str != "Unknown":
                try:
                    # Try to parse the date if it's in a standard format
                    date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    st.markdown(f"<h4>📅 <span style='color:#3366cc;'>Inspection Date:</span></h4> {date_obj.strftime('%B %d, %Y')}", unsafe_allow_html=True)
                except:
                    st.markdown(f"<h4>📅 <span style='color:#3366cc;'>Inspection Date:</span></h4> {date_str}", unsafe_allow_html=True)
            else:
                st.markdown("<h4>📅 <span style='color:#3366cc;'>Inspection Date:</span></h4> Not available", unsafe_allow_html=True)
        
        # Location with icon and better formatting
        st.markdown("<h4>📍 <span style='color:#3366cc;'>Location:</span></h4>", unsafe_allow_html=True)
        if st.session_state.lat and st.session_state.lon:
            try:
                if isinstance(st.session_state.lat, (float, int)) and isinstance(st.session_state.lon, (float, int)):
                    st.markdown(f"{st.session_state.lat:.6f}, {st.session_state.lon:.6f}")
                else:
                    st.markdown(f"{st.session_state.lat}, {st.session_state.lon}")
            except:
                st.markdown(f"{st.session_state.lat}, {st.session_state.lon}")
        else:
            st.markdown("Not available")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metadata-container" style="border-left: 3px solid #3366cc;">', unsafe_allow_html=True)
        
        # Weather data section with icon and better formatting
        st.markdown("<h4>🌦️ <span style='color:#3366cc;'>Weather Conditions:</span></h4>", unsafe_allow_html=True)
        
        if st.session_state.weather_info["weather_source"] == "Not retrieved":
            st.markdown("Weather data not retrieved yet.")
            if st.button("Get Weather Data", key="weather_button"):
                with st.spinner("Fetching weather data..."):
                    # Simulate API call delay
                    time.sleep(0.5)
                    st.session_state.weather_info.update({
                        "weather_temperature_C": 23.5,
                        "weather_precipitation_mm": 0.0,
                        "weather_cloud_cover_percent": 25,
                        "weather_wind_speed_kph": 8.2,
                        "weather_code": 1,  # Clear sky
                        "weather_source": "Open-Meteo (Simulated)"
                    })
                    st.session_state.weather_fetched = True
                    st.rerun()
        else:
            st.markdown(f"**Temperature:** {st.session_state.weather_info['weather_temperature_C']}°C")
            st.markdown(f"**Precipitation:** {st.session_state.weather_info['weather_precipitation_mm']} mm")
            st.markdown(f"**Cloud Cover:** {st.session_state.weather_info['weather_cloud_cover_percent']}%")
            st.markdown(f"**Wind Speed:** {st.session_state.weather_info['weather_wind_speed_kph']} km/h")
        
        st.markdown('</div>', unsafe_allow_html=True)


# Function to display photo analysis details
def display_photo_analysis():
    st.markdown("<h3>📊 Photo Analysis</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    # Image Analysis column
    with col1:
        st.markdown("<h4>📷 Image Details</h4>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        # Add image-specific details
        if hasattr(st.session_state, 'image_size_mb'):
            st.markdown(f"**File Size:** {st.session_state.image_size_mb:.2f} MB")
        
        if hasattr(st.session_state, 'focal_length'):
            st.markdown(f"**Focal Length:** {st.session_state.focal_length}")
        
        if hasattr(st.session_state, 'exposure_time'):
            st.markdown(f"**Exposure:** {st.session_state.exposure_time}")
        
        if hasattr(st.session_state, 'f_number'):
            st.markdown(f"**Aperture:** f/{st.session_state.f_number}")
        
        # Add more technical details as needed
        st.markdown("Image technical details provide context about the photography conditions.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Annotations column
    with col2:
        st.markdown("<h4>🖊️ Beekeeper Annotations</h4>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        # Hive state dropdown
        hive_states = ["Select...", "Active Foraging", "Calm/Normal", "Defensive", "Swarming Preparation", "Queen Issues", "Honey Flow", "Dormant/Winter"]
        selected_state = st.selectbox("Hive State", hive_states, index=0, key="hive_state")
        
        # Notes text area
        notes = st.text_area("Beekeeper Notes", height=100, 
                           placeholder="Enter your observations about the hive condition, behavior, etc.", key="beekeeper_notes")
        
        if st.button("Save Annotations", key="save_annotations"):
            if selected_state != "Select...":
                st.success("Annotations saved!")
                # In a real app, you would save these to your data structure
            else:
                st.warning("Please select a hive state")
                
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Computer Vision column
    with col3:
        st.markdown("<h4>🤖 Computer Vision</h4>", unsafe_allow_html=True)
        st.markdown('<div class="metadata-container">', unsafe_allow_html=True)
        
        # Color palette section
        st.markdown("**Color Palette:**")
        palette_html = '<div style="display:flex; margin-bottom: 15px;">'
        for color in st.session_state.palette_hex:
            palette_html += f'<div class="color-swatch" style="background-color: {color};" title="{color}"></div>'
        palette_html += '</div>'
        st.markdown(palette_html, unsafe_allow_html=True)
        
        # Dominant color
        st.markdown(f"**Dominant Color:** {st.session_state.palette_hex[0]}")
        
        # Google Vision API button
        if st.button("🔍 Analyze with Vision API", key="vision_api_button"):
            with st.spinner("Analyzing image with Google Cloud Vision API..."):
                # Simulate API analysis for demo
                time.sleep(1)
                st.success("Image analysis complete! (Simulated)")
                # In a real implementation, you would call the Vision API here and store results
                
        # Vision API results (placeholder)
        if hasattr(st.session_state, 'vision_api_results') and st.session_state.vision_api_results:
            st.markdown("**API Results:**")
            # Display vision API results here
            st.markdown("Labels detected would appear here...")
        else:
            st.markdown("Click the button above to analyze this image.")
            
        st.markdown('</div>', unsafe_allow_html=True)

# Function to display the image upload options
def display_image_upload_options(in_sidebar=True, expanded=True):
    """Display image upload options either in sidebar or main content"""
    
    # Choose where to display based on the parameter
    container = st.sidebar if in_sidebar else st
    
    with container.expander("📤 Upload Image", expanded=expanded):
        # URL input option
        container.markdown("### Enter an Image URL")
        img_url = container.text_input(
            "Image URL", 
            value="https://drive.google.com/uc?export=view&id=1qbvRpDnseTcq1fd69wKkTUl5VDZMO4Vc",
            help="Enter the URL of a beehive photo",
            key="img_url_input"
        )
        
        if container.button("Process URL Image", key="url_button"):
            if img_url:
                # Only process if it's a new URL or previous processing failed
                if 'last_processed_url' not in st.session_state or st.session_state.last_processed_url != img_url:
                    with st.spinner("Processing image from URL..."):
                        # Import the function from the right module
                        from src.utils.image_processor import process_url_image
                        photo_data = process_url_image(img_url)
                        if photo_data:
                            # Add photo to appropriate inspection
                            from src.utils.data_handler import add_photo_to_inspection
                            add_photo_to_inspection(photo_data)
                            
                            st.session_state.last_processed_url = img_url
                            
                            # Force rerun to update UI
                            st.rerun()
                else:
                    st.info("Image already processed")
            else:
                st.warning("Please enter a valid image URL")

        # Add some space between the two options
        container.markdown("<hr style='margin: 10px 0'>", unsafe_allow_html=True)
        
        # File upload option
        container.markdown("### Upload an Image")
        uploaded_file = container.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"], key="file_uploader")
        
        if uploaded_file is not None:
            # Check if this is a new file upload
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != file_key:
                with st.spinner("Processing uploaded image..."):
                    # Import the function from the right module
                    from src.utils.image_processor import process_image_file
                    file_name = uploaded_file.name
                    success = process_image_file(uploaded_file, file_name)
                    if success:
                        st.session_state.last_uploaded_file = file_key
                        # Handle successful processing
                        handle_image_processing(success)
            # else:
            #     st.info("Image already processed")

# Function to handle successful image processing
def handle_image_processing(photo_data):
    """Callback to handle successful image processing"""
    if photo_data:
        st.session_state.processing_complete = True
        st.session_state.image_load_time = time.time()
        
        # Add photo to appropriate inspection if not already done
        from src.utils.data_handler import add_photo_to_inspection
        add_photo_to_inspection(photo_data)
        
        # Force rerun to update UI immediately
        st.rerun()

# Function to update timeline after processing new images
def update_timeline():
    """Update the timeline with new inspection data"""
    # This function would update any timeline-related data
    # For now it's a placeholder
    pass

# Function to render the sidebar with inspection list
def render_sidebar():
    with st.sidebar:
        # First add the image upload section at the top
        display_image_upload_options(in_sidebar=True, expanded=True)
        
        # Add some space
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Then show inspection details
        st.header("Inspection Details")
        
        if st.session_state.inspections:
            st.write(f"Total Inspections: {len(st.session_state.inspections)}")
            st.write(f"Total Photos: {sum(insp['photo_count'] for insp in st.session_state.inspections)}")
            
            # Display a list of inspections with letter identifiers
            st.subheader("Inspection History")
            
            # Sort inspections by date
            sorted_inspections = sorted(
                enumerate(st.session_state.inspections), 
                key=lambda x: x[1]['date'] if isinstance(x[1]['date'], datetime) else datetime.strptime(x[1]['date'], "%Y:%m:%d %H:%M:%S")
            )
            
            # Generate letter identifiers
            for idx, (i, inspection) in enumerate(sorted_inspections):
                letter = chr(65 + idx % 26)  # A, B, C, ... Z, then AA, AB, etc.
                date_str = inspection['date'].strftime("%b %d, %Y") if isinstance(inspection['date'], datetime) else inspection['date']
                if st.button(f"Inspection {letter}: {date_str} - {inspection['photo_count']} photos", key=f"insp_{i}"):
                    st.session_state.selected_inspection = i
                    st.info(f"Selected inspection {letter} from {date_str}")
                    
                    # Option to view in gallery
                    if st.button("📸 View in Gallery", key=f"gallery_{i}"):
                        st.session_state.page = 'gallery'
                        st.rerun()
        else:
            st.info("No inspections recorded yet. Start by uploading a hive photo.")
        
        # Export data option
        st.subheader("Data Management")
        if st.button("Export Data (JSON)", key="export_button"):
            if st.session_state.inspections:
                # In a real app, you would save to a file
                st.success("Data would be exported as JSON")
            else:
                st.warning("No data to export")
        
        # Display cache information
        st.subheader("Cache Status")
        if 'url_image_cache' in st.session_state:
            cache_count = len(st.session_state.url_image_cache)
            st.write(f"URL Image Cache: {cache_count} images")
            
            if cache_count > 0 and st.button("Clear Cache", key="clear_cache"):
                st.session_state.url_image_cache = {}
                st.success("Cache cleared!")
                st.rerun()
