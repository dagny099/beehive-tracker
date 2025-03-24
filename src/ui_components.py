import streamlit as st
from PIL import Image

def display_color_palette(palette_hex):
    """Display a color palette with hex values."""
    st.markdown("**🎨 Color Palette**")
    for hex_color in palette_hex:
        st.markdown(f"<div style='width:100%;height:30px;background-color:{hex_color};border:1px solid #ccc;'></div>", unsafe_allow_html=True)
        st.markdown(f"<center>{hex_color}</center>", unsafe_allow_html=True)

def display_image_preview(img, img_name):
    """Display an image preview with its filename."""
    st.markdown("<hr class='custom-line'>", unsafe_allow_html=True)
    st.markdown(f"#### 📷 Preview: `{img_name}`")
    
    preview_col, sidebar_col = st.columns([2, 1])
    with preview_col:
        # Replace use_column_width with use_container_width
        st.image(img, use_container_width=True, output_format="JPEG")
    
    return sidebar_col


def display_exif_data(exif_data, date_taken, date_source, camera_model, image_resolution):
    """Display EXIF metadata in an expandable section."""
    with st.expander("📷 EXIF Metadata", expanded=False):
        st.markdown(f"**Date Taken:** {date_taken} ({date_source})")
        st.markdown(f"**Camera Model:** {camera_model}")
        st.markdown(f"**Image Resolution:** {image_resolution}")
        st.markdown("---")
        st.json({k: str(v) for k, v in exif_data.items()})

def display_annotation_form():
    """Display form for user annotations."""
    with st.expander("🖊️ Annotations", expanded=True):
        notes = st.text_area("Hive Notes")
        hive_state = st.selectbox("Hive Behavior Observed", 
                                 ["Calm", "Foraging", "Guarding", "Swarming", "Robbing"])
    
    return notes, hive_state

def display_location_input(default_lat=None, default_lon=None):
    """Display form for manual location input."""
    # Default values for San Francisco if none provided
    DEFAULT_LAT = 37.7749
    DEFAULT_LON = -97.7431
    
    # Convert values to float to ensure type consistency
    if default_lat is not None:
        try:
            default_lat = float(default_lat)
        except (TypeError, ValueError):
            default_lat = DEFAULT_LAT
    else:
        default_lat = DEFAULT_LAT
        
    if default_lon is not None:
        try:
            default_lon = float(default_lon)
        except (TypeError, ValueError):
            default_lon = DEFAULT_LON
    else:
        default_lon = DEFAULT_LON
    
    col1, col2 = st.columns(2)
    
    with col1:
        lat = st.number_input("Latitude", value=default_lat, format="%.6f")
    
    with col2:
        lon = st.number_input("Longitude", value=default_lon, format="%.6f")
        
    return lat, lon


def display_weather_data(weather_info):
    """
    Display weather data with option to fetch from API.
    
    Parameters:
        weather_info (dict): Weather information
        
    Returns:
        bool: True if the user requested to get weather data
    """
    # Create the main weather data container (not using an expander)
    st.markdown("### 🌦️ Weather Data")
    
    if not weather_info.get('weather_temperature_C'):
        st.info("Weather data has not been retrieved yet.")
        
        if st.button("Get Weather Data from Open-Meteo"):
            return True
            
        st.markdown("---")
        st.markdown("Weather data will be retrieved using coordinates and timestamp from the photo.")
    else:
        # Create a more user-friendly display for weather data
        weather_date = weather_info.get('weather_datetime', 'Unknown')
        temp = weather_info.get('weather_temperature_C', 'Unknown')
        precip = weather_info.get('weather_precipitation_mm', 'Unknown')
        cloud = weather_info.get('weather_cloud_cover_percent', 'Unknown')
        wind = weather_info.get('weather_wind_speed_kph', 'Unknown')
        weather_code = weather_info.get('weather_code', 'Unknown')
        weather_source = weather_info.get('weather_source', 'Unknown')
        
        # WMO Weather interpretation codes
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        # Weather description
        weather_desc = weather_codes.get(weather_code, "Unknown weather pattern")
        
        # Display the weather information
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Temperature", f"{temp} °C")
            st.metric("Precipitation", f"{precip} mm")
            st.metric("Cloud Cover", f"{cloud}%")
            
        with col2:
            st.metric("Wind Speed", f"{wind} km/h")
            st.markdown(f"**Weather Condition:** {weather_desc}")
            st.markdown(f"**Source:** {weather_source}")
            st.markdown(f"**Date/Time:** {weather_date}")
        
        if st.button("Refresh Weather Data"):
            return True
            
    # Now the Raw Weather Data expander is at the same level, not nested
    with st.expander("View Raw Weather Data", expanded=False):
        st.json(weather_info)
        
    return False

def display_vision_analysis(vision_analysis):
    """
    Display Vision API analysis results.
    
    Parameters:
        vision_analysis (dict): Vision API analysis results
        
    Returns:
        bool: True if the user requested a new analysis
    """
    # st.markdown("### 🤖 Vision API Analysis")
    
    if not vision_analysis or 'error' in vision_analysis:
        st.info("No vision analysis available. Click 'Analyze with Vision API' below.")
        
        if st.button("Analyze with Vision API"):
            return True
            
        st.markdown("---")
        st.markdown("The Google Cloud Vision API will analyze the image for labels, objects, and colors.")
        
    else:
        # Display analysis timestamp
        st.markdown(f"**Analysis performed:** {vision_analysis.get('timestamp', 'Unknown')}")
        st.markdown("---")
        
        # Display bee-related labels
        bee_labels = [label for label in vision_analysis.get('labels', []) 
                     if label.get('bee_related')]
        other_labels = [label for label in vision_analysis.get('labels', [])[:5] 
                       if not label.get('bee_related')]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Bee-Related Labels:**")
            if bee_labels:
                for label in bee_labels:
                    st.markdown(f"- {label['description']} ({label['score']:.2f})")
            else:
                st.markdown("*No bee-related labels detected*")
        
        with col2:
            st.markdown("**Other Top Labels:**")
            if other_labels:
                for label in other_labels:
                    st.markdown(f"- {label['description']} ({label['score']:.2f})")
            else:
                st.markdown("*No other labels detected*")
        
        # Display detected objects
        objects = vision_analysis.get('objects', [])
        if objects:
            st.markdown("**Detected Objects:**")
            for obj in objects[:5]:
                st.markdown(f"- {obj['name']} ({obj['score']:.2f})")
        
        # Display color analysis
        st.markdown("**Color Analysis:**")
        colors = vision_analysis.get('colors', [])
        if colors:
            color_cols = st.columns(min(5, len(colors)))
            
            for i, color in enumerate(colors[:5]):
                with color_cols[i]:
                    hex_color = color.get('hex', '#FFFFFF')
                    pixel_fraction = color.get('pixel_fraction', 0)
                    
                    st.markdown(
                        f"<div style='width:100%;height:30px;background-color:{hex_color};'></div>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{hex_color}**")
                    st.markdown(f"Pixel fraction: {pixel_fraction:.1%}")
        
        # Display bee summary
        bee_summary = vision_analysis.get('bee_summary', {})
        if bee_summary:
            st.markdown("**Hive Analysis Summary:**")
            st.markdown(f"- Suggested state: {bee_summary.get('suggested_hive_state', 'Unknown')}")
            st.markdown(f"- Honey colors detected: {'Yes' if bee_summary.get('honey_colors_detected') else 'No'}")
            st.markdown(f"- Brood colors detected: {'Yes' if bee_summary.get('brood_colors_detected') else 'No'}")
            
            # Show top bee terms
            st.markdown("**Top Bee Terms:**")
            top_terms = bee_summary.get('top_bee_terms', [])
            if top_terms:
                st.markdown(", ".join(top_terms))
            else:
                st.markdown("*No bee-specific terms detected*")
        
        # Button to refresh analysis
        if st.button("Refresh Vision Analysis"):
            return True
    
    return False

# Add to ui_components.py
def display_entry_browser(entries, current_filename=None):
    """
    Display a browsable list of saved entries.
    
    Parameters:
        entries (list): List of entry summaries to display
        current_filename (str): Currently loaded filename
        
    Returns:
        str: Selected filename or None if no selection made
    """
    st.markdown("### 📚 Saved Entries")
    
    if not entries:
        st.info("No saved entries found.")
        return None
    
    # Display count of entries
    st.markdown(f"**{len(entries)} entries found**")
    
    # Add search functionality
    search_term = st.text_input("🔍 Search entries by filename or notes", "")
    if search_term:
        entries = [entry for entry in entries if 
                  search_term.lower() in entry.get('filename', '').lower() or 
                  search_term.lower() in entry.get('hive_state', '').lower()]
        if not entries:
            st.warning(f"No entries found matching '{search_term}'")
            return None
        st.info(f"Found {len(entries)} entries matching '{search_term}'")
    
    # Create a container for the entry browser
    browser_container = st.container()
    
    # Display entries in a scrollable container
    with browser_container:
        selected_entry = None
        
        # Display entries as cards in a grid layout
        cols = st.columns(3)
        for i, entry in enumerate(entries):
            with cols[i % 3]:
                # Create a card-like container with better styling
                st.markdown(f"""
                <div style='
                    border: 1px solid #888; 
                    border-radius: 5px; 
                    padding: 10px; 
                    margin-bottom: 15px;
                    background-color: {'#e0f0ff' if entry['filename'] == current_filename else '#f5f5f5'};
                '>
                    <div style='width:100%; height:15px; background-color:{entry["thumbnail"]}; 
                         border-radius: 3px; margin-bottom: 8px;'></div>
                    <p style='font-weight: bold; color: #333; font-size: 14px; margin: 5px 0;'>
                        📄 {entry["filename"]}
                    </p>
                    <p style='color: #555; font-size: 12px; margin: 3px 0;'>
                        📅 Date: {entry["date_taken"]}
                    </p>
                    <p style='color: #555; font-size: 12px; margin: 3px 0;'>
                        🐝 Hive: {entry["hive_state"]}
                    </p>
                    <p style='color: #777; font-size: 11px; margin: 3px 0;'>
                        ⏱️ Updated: {entry["last_updated"]}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add a button to load this entry
                if st.button(f"Load", key=f"load_{i}"):
                    selected_entry = entry["filename"]
    
    return selected_entry