# src/app_components.py
import streamlit as st
import io
import time
from PIL import Image
from datetime import datetime
import os
import json
from src.timeline_component import format_location_for_display
from src.utils.data_handler import add_photo_to_inspection
from src.api_services.weather import get_weather_open_meteo



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
    # Add honeycomb-themed header with warm colors
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #FFC300 0%, #FFE066 50%, #FFF2B3 100%);
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #D4A017;
        margin-bottom: 25px;
        box-shadow: 0 4px 8px rgba(255, 195, 0, 0.2);
        position: relative;
        overflow: hidden;
    ">
    <div style="
        position: absolute;
        top: -10px;
        right: -10px;
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
    "></div>
    <div style="
        position: absolute;
        bottom: -15px;
        left: -15px;
        width: 60px;
        height: 60px;
        background: rgba(255, 255, 255, 0.2);
        clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    "></div>
    <h3 style="color: #8B4513; margin-top: 0; text-shadow: 1px 1px 2px rgba(255,255,255,0.8); font-weight: 700;">🔍 Inspection Overview</h3>
    </div>
    """, unsafe_allow_html=True)

    # Add inspection dropdown selector
    if 'inspections' in st.session_state and st.session_state.inspections:
        inspection_options = []
        for idx, inspection in enumerate(st.session_state.inspections):
            # Get the inspection title using same logic as timeline
            from src.utils.data_handler import get_inspection_title
            title = get_inspection_title(idx)
            inspection_options.append((idx, title))

        # Sort by date (newest first)
        inspection_options.sort(key=lambda x: st.session_state.inspections[x[0]]['date'], reverse=True)

        # Create dropdown
        option_labels = [f"{title} ({st.session_state.inspections[idx]['photo_count']} photos)" for idx, title in inspection_options]
        option_indices = [idx for idx, _ in inspection_options]

        current_selection = st.session_state.get('selected_inspection', 0)
        if current_selection not in option_indices:
            current_selection = option_indices[0] if option_indices else 0

        selected_index = st.selectbox(
            "Select Inspection:",
            options=range(len(option_labels)),
            format_func=lambda x: option_labels[x],
            index=option_indices.index(current_selection) if current_selection in option_indices else 0,
            key="inspection_selector"
        )

        # Update selected inspection
        st.session_state.selected_inspection = option_indices[selected_index]

    # Display inspection date and weather in compact format
    if ('inspections' in st.session_state and
        'selected_inspection' in st.session_state and
        st.session_state.selected_inspection is not None and
        st.session_state.selected_inspection < len(st.session_state.inspections)):

        current_inspection = st.session_state.inspections[st.session_state.selected_inspection]

        # Compact date and location display
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**📅 Inspection Date:**")
            date_obj = current_inspection.get('date')
            if isinstance(date_obj, datetime):
                date_display = date_obj.strftime('%B %d, %Y')
            elif isinstance(date_obj, str):
                try:
                    parsed_date = datetime.strptime(date_obj.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                    date_display = parsed_date.strftime('%B %d, %Y')
                except:
                    date_display = date_obj
            else:
                date_display = "Not available"
            st.markdown(date_display)

        with col2:
            st.markdown("**📍 Location:**")
            location_with_icon = format_location_for_display(current_inspection)
            current_location = location_with_icon.replace("📍 ", "")  # Remove icon for consistency
            st.markdown(current_location)

        # Compact weather display with icons
        weather_data = current_inspection.get('weather_data')
        if weather_data and weather_data.get('weather_source') and 'Error' not in str(weather_data.get('weather_source', '')):
            st.markdown("**🌦️ Weather Conditions:**")
            # Create compact weather display with icons
            weather_parts = []
            if weather_data.get('weather_temperature_C') is not None:
                weather_parts.append(f"🌡️ {weather_data['weather_temperature_C']}°C")
            if weather_data.get('weather_precipitation_mm') is not None:
                weather_parts.append(f"💧 {weather_data['weather_precipitation_mm']}mm")
            if weather_data.get('weather_cloud_cover_percent') is not None:
                weather_parts.append(f"☁️ {weather_data['weather_cloud_cover_percent']}%")
            if weather_data.get('weather_wind_speed_kph') is not None:
                weather_parts.append(f"💨 {weather_data['weather_wind_speed_kph']}kph")

            if weather_parts:
                st.markdown(" • ".join(weather_parts))

            # Show data source in smaller text
            source = weather_data.get('weather_source', 'Open-Meteo API')
            st.markdown(f"*Source: {source}*")
        else:
            st.markdown("**🌦️ Weather:** Not available")

    # Add gallery functionality for current inspection
    display_inspection_gallery()


# Function to display photo analysis details
def display_photo_analysis():
    # Remove header since Photo Analysis is now spatially grouped with photo metadata
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
                        # Use the consistent image processing pipeline
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
        # Add main app header at top of sidebar
        st.markdown("# 🐝 Hive Photo Metadata Tracker")
        st.markdown("<hr>", unsafe_allow_html=True)

        # First add the image upload section
        display_image_upload_options(in_sidebar=True, expanded=True)

        # Add some space
        st.markdown("<hr>", unsafe_allow_html=True)

        # Then show inspection details
        st.header("Inspection Details")
        
        if st.session_state.inspections:
            st.write(f"Total Inspections: {len(st.session_state.inspections)}")
            st.write(f"Total Photos: {sum(insp['photo_count'] for insp in st.session_state.inspections)}")
            
            # Note: Inspection selection is now handled via dropdown on main dashboard
        else:
            st.info("No inspections recorded yet. Start by uploading a hive photo.")
        
        # Export data option with functional implementation
        st.subheader("Data Management")
        if st.button("Export Data (JSON)", key="export_button"):
            if st.session_state.inspections:
                # Export current data to JSON file
                import json
                from datetime import datetime
                import os

                export_data = {
                    "inspections": st.session_state.inspections,
                    "exported_at": datetime.now().isoformat()
                }

                # Ensure exports directory exists
                os.makedirs("data/exports", exist_ok=True)

                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/exports/inspections_export_{timestamp}.json"

                # Save to file
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)

                st.success(f"Data exported to {filename}")
            else:
                st.warning("No data to export")

        # Import data option
        uploaded_json = st.file_uploader("Import JSON Data", type=["json"], key="import_json")
        if uploaded_json is not None:
            try:
                import json
                import os
                import_data = json.load(uploaded_json)

                if 'inspections' in import_data:
                    # Validate file paths and report missing files
                    missing_files = []
                    total_photos = 0

                    for inspection in import_data['inspections']:
                        for photo in inspection.get('photos', []):
                            total_photos += 1
                            file_path = photo.get('file_path', '')
                            if file_path and not os.path.exists(file_path):
                                missing_files.append(file_path)

                    # Load inspections into session state
                    st.session_state.inspections = import_data['inspections']

                    # Save to main data file
                    from src.utils.data_handler import save_inspections_to_disk
                    save_inspections_to_disk()

                    # Report import status
                    if missing_files:
                        st.warning(f"Imported {len(import_data['inspections'])} inspections with {total_photos} photos. ⚠️ {len(missing_files)} image files not found at expected paths.")
                        with st.expander("Missing files"):
                            for missing in missing_files:
                                st.write(f"• {missing}")
                        # Clear file uploader and trigger rerun for missing files case too
                        st.session_state.pop('import_json', None)
                        st.rerun()
                    else:
                        st.success(f"✅ Imported {len(import_data['inspections'])} inspections with {total_photos} photos. All image files found!")

                    # Clear file uploader to prevent reprocessing and trigger rerun
                    st.session_state.pop('import_json', None)
                    st.rerun()
                else:
                    st.error("Invalid JSON format")
            except Exception as e:
                st.error(f"Import failed: {e}")
        
        # Display cache and file information
        st.subheader("Storage Status")
        if 'url_image_cache' in st.session_state:
            cache_count = len(st.session_state.url_image_cache)
            st.write(f"URL Image Cache: {cache_count} images")

            if cache_count > 0 and st.button("Clear Cache", key="clear_cache"):
                st.session_state.url_image_cache = {}
                st.success("Cache cleared!")
                st.rerun()

        # Show upload directory size
        import os
        upload_dir = "data/uploads/users/default_user"
        if os.path.exists(upload_dir):
            files = [f for f in os.listdir(upload_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            total_size = sum(os.path.getsize(os.path.join(upload_dir, f)) for f in files) / (1024*1024)
            st.write(f"Stored Images: {len(files)} files ({total_size:.1f} MB)")

def display_inspection_gallery():
    """Display photo gallery for the current inspection integrated into the overview"""
    if 'selected_inspection' not in st.session_state or st.session_state.selected_inspection is None:
        return

    if 'inspections' not in st.session_state or not st.session_state.inspections:
        return

    inspection_idx = st.session_state.selected_inspection
    if inspection_idx >= len(st.session_state.inspections):
        return

    inspection = st.session_state.inspections[inspection_idx]
    photos = inspection.get('photos', [])

    if not photos:
        st.info("No photos in this inspection.")
        return

    # Gallery header with bee styling - simplified without colored box
    st.markdown(f"**📷 Photos in this Inspection ({len(photos)})**")

    # Display photos in a grid
    import math
    cols_per_row = 3
    rows = math.ceil(len(photos) / cols_per_row)

    for row in range(rows):
        columns = st.columns(cols_per_row)
        for col in range(cols_per_row):
            photo_idx = row * cols_per_row + col
            if photo_idx < len(photos):
                photo = photos[photo_idx]
                with columns[col]:
                    # Display photo thumbnail
                    try:
                        if 'file_path' in photo and os.path.exists(photo['file_path']):
                            from PIL import Image
                            img = Image.open(photo['file_path'])
                            st.image(img, caption=photo.get('filename', f"Photo {photo_idx+1}"), use_container_width=True)
                        elif 'data' in photo:
                            if isinstance(photo['data'], bytes):
                                from PIL import Image
                                import io
                                img = Image.open(io.BytesIO(photo['data']))
                            else:
                                img = photo['data']
                            st.image(img, caption=photo.get('filename', f"Photo {photo_idx+1}"), use_container_width=True)
                        else:
                            st.error(f"Photo {photo_idx+1} data not available")
                    except Exception as e:
                        st.error(f"Could not load photo: {e}")

                    # Photo metadata below image
                    with st.expander(f"📋 Details", expanded=False):
                        st.markdown(f"**Filename:** {photo.get('filename', 'Unknown')}")
                        st.markdown(f"**Date Taken:** {photo.get('date_taken', 'Unknown')}")
                        st.markdown(f"**Camera:** {photo.get('camera_model', 'Unknown')}")
                        st.markdown(f"**Resolution:** {photo.get('resolution', 'Unknown')}")
                        if photo.get('file_size_mb'):
                            st.markdown(f"**Size:** {photo.get('file_size_mb'):.1f} MB")
                        if photo.get('lat') and photo.get('lon'):
                            st.markdown(f"**GPS:** {photo.get('lat'):.4f}, {photo.get('lon'):.4f}")

                        # Color palette if available
                        if 'color_palette' in photo:
                            st.markdown("**Color Palette:**")
                            palette_html = ""
                            for color in photo['color_palette']:
                                palette_html += f'<div style="display: inline-block; width: 25px; height: 25px; background-color: {color}; border: 1px solid #ccc; margin: 2px;"></div>'
                            st.markdown(palette_html, unsafe_allow_html=True)
