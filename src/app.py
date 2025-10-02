# src/app3.py
import streamlit as st
from datetime import datetime
import io
import time
from PIL import Image
import os

# Import components and utilities
from src.timeline_component import initialize_session_state, render_timeline
from src.app_components import (
    display_image_and_photo_metadata,
    display_inspection_metadata,
    display_photo_analysis,
    display_image_upload_options,
    render_sidebar,
    handle_image_processing
)

def main():
    """Main dashboard for the Hive Photo Metadata Tracker"""
    # Apply custom CSS
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
        .image-placeholder {
            background-color: rgba(30, 30, 30, 0.05);
            border-radius: 10px;
            height: 300px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-style: italic;
            color: rgba(100, 100, 100, 0.7);
        }
        .stButton>button {
            background-color: #FFC300;
            color: #333;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #FFD700;
            color: #333;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()

    # App content (header moved to sidebar)
    # Note: "Load Latest Backup" button moved to sidebar in app_components.py
    
    # Render the timeline with some margin
    st.markdown('<div style="margin: 15px 0;"></div>', unsafe_allow_html=True)
    timeline = render_timeline()
    st.markdown("""
    Track and organize your beehive photos with rich metadata, including weather conditions,
    color analysis, and computer vision insights.
    """)
    st.markdown('<div style="margin: 15px 0;"></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
        
    # Main app content
    if 'current_image' in st.session_state and st.session_state.current_image:
        # Display image and photo metadata
        display_image_and_photo_metadata()

        # Display photo analysis sections (moved to be adjacent to photo)
        display_photo_analysis()

        # Add horizontal line separator
        st.markdown('<hr style="border: 1px solid #FFC300; margin: 30px 0;">', unsafe_allow_html=True)

        # Display inspection overview (renamed from inspection metadata)
        display_inspection_metadata()

        # We no longer need this since upload is in sidebar
        # display_image_upload_options(expanded=False)
    else:
        # Placeholder for image when none is loaded
        st.markdown('<div class="image-placeholder"><p>Upload a hive photo using the options in the sidebar</p></div>', unsafe_allow_html=True)

    # Render the sidebar (with inspection list and upload options)
    render_sidebar()

if __name__ == "__main__":
    main()