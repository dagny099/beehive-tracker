# src/gallery_view.py
import streamlit as st
import io
from PIL import Image
import os
import math
from datetime import datetime
from src.timeline_component import initialize_session_state

def main():
    """Render the photo gallery page"""
    st.markdown("## 📸 Hive Photo Gallery")
    
    # Initialize session state if needed
    initialize_session_state()
    
    # Check if there are any inspections to display
    if 'inspections' not in st.session_state or not st.session_state.inspections:
        st.info("No inspections available. Start by uploading hive photos.")
        return
    
    # Sort inspections by date
    sorted_inspections = sorted(
        enumerate(st.session_state.inspections), 
        key=lambda x: x[1]['date'] if isinstance(x[1]['date'], datetime) else datetime.strptime(x[1]['date'], "%Y:%m:%d %H:%M:%S")
    )
    
    # Create a dropdown to select inspection
    inspection_options = []
    for idx, (i, inspection) in enumerate(sorted_inspections):
        letter = chr(65 + idx % 26)
        date_str = inspection['date'].strftime("%b %d, %Y") if isinstance(inspection['date'], datetime) else inspection['date']
        inspection_options.append(f"Inspection {letter}: {date_str} - {inspection['photo_count']} photos")
    
    # If we have a selected inspection, set it as default
    default_index = 0
    if 'selected_inspection' in st.session_state:
        for idx, (i, _) in enumerate(sorted_inspections):
            if i == st.session_state.selected_inspection:
                default_index = idx
                break
    
    selected_option = st.selectbox(
        "Select Inspection:", 
        inspection_options,
        index=default_index,
        key="gallery_inspection_selector"
    )
    
    # Get the selected inspection index
    selected_idx = inspection_options.index(selected_option)
    inspection_idx = sorted_inspections[selected_idx][0]
    
    # Update selected inspection in session state
    st.session_state.selected_inspection = inspection_idx
    
    # Get photos associated with this inspection
    inspection = st.session_state.inspections[inspection_idx]
    photos = inspection.get('photos', [])
    
    if not photos:
        st.warning("No photos found for this inspection.")
        return
    
    # Display inspection metadata
    with st.expander("Inspection Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date_str = inspection['date'].strftime("%B %d, %Y") if isinstance(inspection['date'], datetime) else inspection['date']
            st.markdown(f"**Date:** {date_str}")
            st.markdown(f"**Location:** {inspection.get('location', 'Not recorded')}")
            
        with col2:
            st.markdown(f"**Weather:** {inspection.get('weather_summary', 'Not recorded')}")
            st.markdown(f"**Photos:** {len(photos)}")
    
    # Display photo gallery
    st.markdown("### Photo Gallery")
    
    # Calculate grid layout based on number of photos
    cols_per_row = 3
    rows = math.ceil(len(photos) / cols_per_row)
    
    # Create grid for photos
    for row in range(rows):
        columns = st.columns(cols_per_row)
        for col in range(cols_per_row):
            photo_idx = row * cols_per_row + col
            if photo_idx < len(photos):
                photo = photos[photo_idx]
                with columns[col]:
                    # Display photo thumbnail
                    if 'file_path' in photo and os.path.exists(photo['file_path']):
                        # Load from file path if available
                        img = Image.open(photo['file_path'])
                        st.image(img, caption=photo.get('filename', f"Photo {photo_idx+1}"), use_container_width=True)
                    elif 'data' in photo:
                        # Load from stored data
                        if isinstance(photo['data'], bytes):
                            img = Image.open(io.BytesIO(photo['data']))
                        else:
                            img = photo['data']
                        st.image(img, caption=photo.get('filename', f"Photo {photo_idx+1}"), use_container_width=True)
                    else:
                        st.error(f"Photo {photo_idx+1} data not available")
                    
                    # Add a "View Details" button for each photo
                    if st.button(f"View Details", key=f"view_photo_{photo_idx}"):
                        st.session_state.selected_photo = photo_idx
                        st.session_state.view_photo_details = True
                        st.rerun()
    
    # Photo detail view
    if 'view_photo_details' in st.session_state and st.session_state.view_photo_details and 'selected_photo' in st.session_state:
        photo_idx = st.session_state.selected_photo
        if photo_idx < len(photos):
            photo = photos[photo_idx]
            
            st.markdown("---")
            st.markdown(f"### Photo Details: {photo.get('filename', f'Photo {photo_idx+1}')}")
            
            # Display photo and metadata
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Display full-size image
                if 'file_path' in photo and os.path.exists(photo['file_path']):
                    img = Image.open(photo['file_path'])
                    st.image(img, use_container_width=True)
                elif 'data' in photo:
                    if isinstance(photo['data'], bytes):
                        img = Image.open(io.BytesIO(photo['data']))
                    else:
                        img = photo['data']
                    st.image(img, use_container_width=True)
            
            with col2:
                # Display photo metadata
                st.markdown("#### Metadata")
                for key, value in photo.items():
                    if key not in ['data', 'file_path'] and not callable(value) and not key.startswith('_'):
                        st.markdown(f"**{key.capitalize()}:** {value}")
                
                # Close detail view button
                if st.button("Close Detail View"):
                    st.session_state.view_photo_details = False
                    st.rerun()

if __name__ == "__main__":
    main()