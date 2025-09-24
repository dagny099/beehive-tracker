import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from PIL import Image
import io
import base64
import requests
from urllib.parse import urlparse

# Updated initialize_session_state function
def initialize_session_state():
    # Core UI state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
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
    
    # Vision API results
    if 'vision_api_results' not in st.session_state:
        st.session_state.vision_api_results = None
    
    # Collection of inspections
    if 'inspections' not in st.session_state:
        st.session_state.inspections = []
    
    # Image caching
    if 'url_image_cache' not in st.session_state:
        st.session_state.url_image_cache = {}



def create_empty_timeline():
    """
    Create an empty timeline with placeholder visualization.
    This ensures the timeline is always visible even when no inspections exist.
    
    Returns:
        go.Figure: A Plotly figure object with the empty timeline
    """
    # Create placeholder dates spanning a year for visual context
    today = datetime.now()
    dates = [today - timedelta(days=30*i) for i in range(6)]
    
    # Create the figure
    fig = go.Figure()
    
    # Add a trace that's visible but subtle to ensure the timeline is drawn
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[1] * len(dates),
            mode='markers',
            marker=dict(
                size=18,
                symbol='hexagon',  # Hexagon shape like a honeycomb cell
                color='rgba(180, 180, 180, 0.1)',  # Almost transparent
                line=dict(width=1, color='rgba(150, 150, 150, 0.3)')
            ),
            hoverinfo='skip',
            showlegend=False
        )
    )
    
    # Add an annotation explaining the empty state
    fig.add_annotation(
        x=dates[len(dates)//2],
        y=1,
        text="Start by uploading a hive photo",
        showarrow=False,
        font=dict(size=14, color='rgba(180, 180, 180, 0.8)'),
        align="center"
    )
    
    # Set layout options for consistent appearance
    fig.update_layout(
        height=150,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=True,
            tickformat="%b %Y"  # Month Year format
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[0.5, 1.5]  # Fix the y-axis range for consistent layout
        )
    )
    
    return fig

def update_timeline_with_inspections():
    """
    Update the timeline with actual inspection data from session state.
    Called when inspections are available to display on the timeline.
    
    Returns:
        go.Figure: A Plotly figure with inspection points
    """
    # Guard clause - use empty timeline if no inspections
    if not st.session_state.inspections:
        return create_empty_timeline()
    
    # Extract dates and create dataframe for the timeline
    inspections_df = pd.DataFrame(st.session_state.inspections)
    
    # Convert string dates to datetime if needed
    if isinstance(inspections_df['date'].iloc[0], str):
        inspections_df['date'] = pd.to_datetime(inspections_df['date'])
    
    # Sort by date
    inspections_df = inspections_df.sort_values('date')
    
    # Create bee icon labels for timeline nodes
    text_labels = ["🐝"] * len(inspections_df)  # Bee icons for all nodes
    
    # Create the figure
    fig = go.Figure()
    
    # Add connecting line for timeline continuity
    fig.add_trace(
        go.Scatter(
            x=inspections_df['date'],
            y=[1] * len(inspections_df),
            mode='lines',
            line=dict(
                color='rgba(212, 160, 23, 0.6)',  # Honey color with transparency
                width=3,
                dash='solid'
            ),
            hoverinfo='skip',
            showlegend=False
        )
    )

    # Add inspection points with text labels on top of the line
    fig.add_trace(
        go.Scatter(
            x=inspections_df['date'],
            y=[1] * len(inspections_df),
            mode='markers+text',  # Show both markers and text
            text=text_labels,
            textposition='middle center',  # Center text on markers
            textfont=dict(
                family='Arial, sans-serif',
                size=11,
                color='rgba(139, 69, 19, 0.9)',  # Darker brown for better contrast
                weight='bold'
            ),
            marker=dict(
                size=28,  # Larger to accommodate text and stand out
                symbol='hexagon',  # Hexagon for honeycomb theme
                color='#FFC300',  # Honey color
                line=dict(width=3, color='#D4A017')  # Stronger border
            ),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Photos: %{customdata}<br><i>Click to view details</i><extra></extra>',
            customdata=inspections_df['photo_count'],
            showlegend=False
        )
    )
    
    # Ensure consistent layout with padding on either side
    min_date = inspections_df['date'].min() - timedelta(days=30)
    max_date = inspections_df['date'].max() + timedelta(days=30)
    
    # Set layout options for consistent appearance
    fig.update_layout(
        height=150,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=True,
            tickformat="%b %Y",
            range=[min_date, max_date]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[0.5, 1.5]  # Fix the y-axis range for consistent layout
        )
    )
    
    # Add date range selector for timeline navigation with honey theme
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]),
                bgcolor='rgba(255, 195, 0, 0.15)',  # Honey-colored background
                bordercolor='#D4A017',
                borderwidth=1,
                font=dict(color='#8B4513', size=11),  # Brown text
                activecolor='#FFC300'  # Active button color
            )
        )
    )
    
    return fig

def render_inspection_summary():
    """
    Render a summary of all inspections with key metrics.
    """
    if not st.session_state.inspections:
        return

    inspections = st.session_state.inspections
    total_photos = sum(inspection.get('photo_count', 0) for inspection in inspections)

    # Get date range
    dates = []
    for inspection in inspections:
        if isinstance(inspection['date'], datetime):
            dates.append(inspection['date'])
        else:
            try:
                dates.append(datetime.strptime(inspection['date'], "%Y:%m:%d %H:%M:%S"))
            except ValueError:
                continue

    if dates:
        latest_date = max(dates)
        first_date = min(dates)

        # Get location info from latest inspection
        latest_inspection = None
        for inspection in inspections:
            inspection_date = inspection['date']
            if isinstance(inspection_date, str):
                try:
                    inspection_date = datetime.strptime(inspection_date, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    continue
            if inspection_date == latest_date:
                latest_inspection = inspection
                break

        # Format location using new helper function
        if latest_inspection:
            location_text = format_location_for_display(latest_inspection).replace("📍 ", "")
        else:
            location_text = "Location not available"

        st.markdown(f"""
        <div style="
            background: rgba(255, 195, 0, 0.1);
            border: 1px solid #D4A017;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        ">
            <div style="
                background: #FFC300;
                color: #8B4513;
                font-weight: bold;
                font-size: 24px;
                padding: 10px 15px;
                border-radius: 50%;
                min-width: 50px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            ">{len(inspections)}</div>
            <div style="flex: 1;">
                <h4 style="margin: 0 0 8px 0; color: #FFC300; font-size: 18px;">Total Inspections</h4>
                <p style="margin: 4px 0; color: #ccc; font-size: 14px;">Latest: {latest_date.strftime('%B %d, %Y')} at {location_text}</p>
                <p style="margin: 4px 0; color: #ccc; font-size: 14px;">First: {first_date.strftime('%B %d, %Y')}</p>
                <p style="margin: 4px 0; color: #ccc; font-size: 14px;">Photo coverage: {total_photos} photos across {len(inspections)} inspection sessions</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_inspection_cards():
    """
    Render individual cards for each inspection with detailed metadata.
    """
    if not st.session_state.inspections:
        return

    # Create columns for card layout - only create as many columns as needed
    num_inspections = len(st.session_state.inspections)
    num_cols = min(3, num_inspections)  # Don't create more columns than inspections
    cols = st.columns(num_cols)

    for i, inspection in enumerate(st.session_state.inspections):
        col = cols[i % num_cols]

        # Skip if inspection data is invalid
        if not inspection or not isinstance(inspection, dict):
            continue

        # Get inspection title using the new function
        from src.utils.data_handler import get_inspection_title
        inspection_title = get_inspection_title(i) or "Untitled Inspection"

        # Ensure we have a valid photo count
        photo_count = inspection.get('photo_count', 0)
        if not isinstance(photo_count, int) or photo_count < 0:
            photo_count = 0

        # Format location using helper function
        try:
            location_text = format_location_for_display(inspection)
        except:
            location_text = "📍 Location not available"

        # Format weather data compactly for card display
        weather_data = inspection.get('weather_data')
        if weather_data and isinstance(weather_data, dict):
            temp = weather_data.get('weather_temperature_C', 'N/A')
            precip = weather_data.get('weather_precipitation_mm', 'N/A')
            cloud = weather_data.get('weather_cloud_cover_percent', 'N/A')
            wind = weather_data.get('weather_wind_speed_kph', 'N/A')
            weather_text = f"🌡️{temp}°C • 💧{precip}mm • ☁️{cloud}% • 💨{wind}kph"
        else:
            weather_text = "Weather data not available"

        with col:
            st.markdown(f"""
            <div style="
                background: rgba(255, 195, 0, 0.05);
                border: 1px solid rgba(255, 195, 0, 0.3);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 15px;
                transition: all 0.3s ease;
                cursor: pointer;
            " onclick="st.rerun()">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 12px;
                ">
                    <div style="
                        background: #FFC300;
                        color: #8B4513;
                        font-weight: bold;
                        padding: 8px 12px;
                        border-radius: 6px;
                        font-size: 18px;
                    ">🐝</div>
                    <div style="
                        color: #FFC300;
                        font-weight: 600;
                        font-size: 14px;
                        line-height: 1.3;
                    ">{inspection_title}</div>
                </div>
                <div style="
                    color: #ccc;
                    font-size: 13px;
                    line-height: 1.4;
                ">
                    <div style="margin-bottom: 4px;">📸 {photo_count} photos</div>
                    <div style="margin-bottom: 4px; font-size: 12px;">{weather_text}</div>
                    <div style="color: #FFE066;">{location_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_timeline():
    """
    Render the timeline in the Streamlit app.
    This is the main function to call from app.py to display the timeline.

    Returns:
        object: The Streamlit plot chart object
    """
    # Timeline header with honeycomb styling
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #FFC300 0%, #FFE066 50%, #FFC300 100%);
        padding: 12px 20px;
        border-radius: 25px;
        border: 2px solid #D4A017;
        margin-bottom: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(255, 195, 0, 0.3);
    ">
    <h3 style="color: #8B4513; margin: 0; text-shadow: 1px 1px 2px rgba(255,255,255,0.8);">📅 Hive Inspection Timeline</h3>
    </div>
    """, unsafe_allow_html=True)

    # Render inspection summary if inspections exist
    if st.session_state.inspections:
        render_inspection_summary()

    # Use the appropriate timeline based on whether inspections exist
    if st.session_state.inspections:
        fig = update_timeline_with_inspections()
    else:
        fig = create_empty_timeline()

    # Display the Plotly figure using Streamlit
    timeline = st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Render inspection cards if inspections exist
    if st.session_state.inspections:
        st.markdown("### Inspection Details")
        render_inspection_cards()
    else:
        # Enhanced empty state
        st.markdown("""
        <div style="
            text-align: center;
            color: #999;
            padding: 40px;
            font-style: italic;
            background: rgba(255, 195, 0, 0.05);
            border-radius: 10px;
            border-left: 4px solid #FFC300;
            margin-top: 20px;
        ">
            <div style="font-size: 48px; margin-bottom: 10px;">🐝</div>
            <p style="font-size: 16px; margin-bottom: 8px;">No inspections yet</p>
            <p style="font-size: 14px; color: #777;">Start by uploading a hive photo to create your first inspection record</p>
        </div>
        """, unsafe_allow_html=True)

    return timeline

def format_location_for_display(inspection):
    """
    Extract and format location from inspection data for consistent display.

    Handles both old string format and new structured format.

    Args:
        inspection (dict): Inspection data

    Returns:
        str: Formatted location string for UI display
    """
    location = inspection.get('location')

    # Handle new structured format (preferred)
    if isinstance(location, dict):
        display_name = location.get('display', '')
        if display_name:
            return f"📍 {display_name}"
        # Fallback to coordinates
        lat = location.get('lat')
        lon = location.get('lon')
        if lat is not None and lon is not None:
            return f"📍 ({lat:.4f}, {lon:.4f})"

    # Handle old string format - upgrade to default if "Unknown"
    elif isinstance(location, str):
        if location in ["Unknown", "Default location"]:
            # Use default Austin location for display
            from src.config import get_default_location
            default = get_default_location()
            return f"📍 {default['display_name']}"
        elif location != "Unknown":
            return f"📍 {location}"

    # If no location data, show default
    from src.config import get_default_location
    default = get_default_location()
    return f"📍 {default['display_name']}"


def extract_exif(img_file):
    """
    Extract EXIF metadata from an image file.
    
    Parameters:
        img_file: File-like object or path to image
        
    Returns:
        dict: Dictionary of EXIF metadata tags
    """
    try:
        img = Image.open(img_file)
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif() is not None:
            exif = img._getexif()
            from PIL.ExifTags import TAGS
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
        return exif_data
    except Exception as e:
        st.warning(f"Could not extract EXIF data: {e}")
        return {}

def get_file_creation_date(img_file):
    """
    Get the file creation date when EXIF data is not available.
    For file-like objects, this returns the current time.
    
    Parameters:
        img_file: File-like object or path to image
        
    Returns:
        str: Date string in format "YYYY:MM:DD HH:MM:SS"
    """
    try:
        # For file-like objects, we can't get creation date directly
        # Return current time as fallback
        return datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    except Exception as e:
        st.warning(f"Could not determine file creation date: {e}")
        return datetime.now().strftime("%Y:%m:%d %H:%M:%S")

def extract_gps_coordinates(exif_data):
    """
    Extract GPS coordinates from EXIF data.
    Currently returns placeholder values to avoid parsing errors.
    
    Parameters:
        exif_data (dict): Dictionary of EXIF metadata
        
    Returns:
        tuple: (latitude, longitude) as floats, or (None, None) if not found
    """
    try:
        if 'GPSInfo' in exif_data:
            # For now, just return placeholder values to avoid parsing errors
            # This can be enhanced in the future as needed
            return 37.7749, -122.4194
        return None, None
    except Exception as e:
        st.warning(f"Could not extract GPS coordinates: {e}")
        return None, None

def rgb_to_hex(rgb):
    """
    Convert RGB tuple to hex color code.
    
    Parameters:
        rgb (tuple): RGB color values as (r, g, b)
        
    Returns:
        str: Hex color code like '#RRGGBB'
    """
    return f'#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}'

def get_palette(img_file):
    """
    Extract dominant color palette from image using ColorThief.
    
    Parameters:
        img_file: File-like object or path to image
        
    Returns:
        list: List of RGB tuples representing the dominant colors
    """
    try:
        from colorthief import ColorThief
        
        # If img_file is a BytesIO object, we need to seek to the beginning
        if hasattr(img_file, 'seek'):
            img_file.seek(0)
            
        color_thief = ColorThief(img_file)
        palette = color_thief.get_palette(color_count=5, quality=1)
        return palette
    except Exception as e:
        st.warning(f"Could not extract color palette: {e}")
        # Return fallback colors that look like honey/hive colors
        return [(255, 223, 0), (246, 174, 45), (242, 100, 25), (206, 18, 18), (0, 0, 0)]

def process_image(img_file, img_name):
    """
    Process an image to extract metadata in a single efficient pass.
    
    Parameters:
        img_file (str or file-like): Path to image or file-like object
        img_name (str): Name of the image file
        
    Returns:
        bool: True if processing was successful
    """
    try:
        # Reset file position if needed
        if hasattr(img_file, 'seek'):
            img_file.seek(0)
            
        # Open the image once and keep it in memory
        img = Image.open(img_file)
        
        # Extract EXIF data
        exif = {}
        if hasattr(img, '_getexif') and img._getexif() is not None:
            raw_exif = img._getexif()
            from PIL.ExifTags import TAGS
            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif[tag] = value
        
        # Get date taken
        date_taken = exif.get("DateTimeOriginal")
        if not date_taken:
            # Use file creation date as fallback
            date_taken = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
            date_source = "File Creation Date"
        else:
            date_source = "EXIF"
        
        # Convert date string to datetime
        if isinstance(date_taken, str):
            try:
                date_taken_dt = datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                # Fallback to current date if parsing fails
                date_taken_dt = datetime.now()
                date_taken = date_taken_dt.strftime("%Y:%m:%d %H:%M:%S")
        else:
            date_taken_dt = date_taken
        
        # Extract GPS coordinates if available (simplified)
        lat, lon = extract_gps_coordinates(exif)
        
        # Get camera model
        camera_model = exif.get("Model", "Unknown")
        
        # Get image resolution
        image_resolution = f"{img.width} x {img.height}"
        
        # Reset file position for color thief
        if hasattr(img_file, 'seek'):
            img_file.seek(0)
            
        # Extract color palette
        palette_rgb = get_palette(img_file)
        palette_hex = [rgb_to_hex(c) for c in palette_rgb]
        
        # Store the image data in session state
        if hasattr(img_file, 'seek'):
            img_file.seek(0)
            img_data = img_file.read()
            st.session_state.current_image = img_data
        else:
            # For PIL Image objects without file backing
            img_buffer = io.BytesIO()
            img.save(img_buffer, format=img.format or 'JPEG')
            img_buffer.seek(0)
            st.session_state.current_image = img_buffer.read()
        
        # Update metadata in session state
        metadata = {
            "filename": img_name,
            "exif_data": exif,
            "date_taken": date_taken,
            "date_taken_dt": date_taken_dt,
            "date_source": date_source,
            "camera_model": camera_model,
            "palette_hex": palette_hex,
            "image_resolution": image_resolution,
            "lat": lat,
            "lon": lon,
            "weather_info": {
                "weather_datetime": date_taken,
                "weather_temperature_C": None,
                "weather_precipitation_mm": None,
                "weather_cloud_cover_percent": None,
                "weather_wind_speed_kph": None,
                "weather_code": None,
                "weather_source": "Not retrieved"
            }
        }
        
        # Update session state
        for key, value in metadata.items():
            st.session_state[key] = value
        
        # Update inspections data
        update_inspections(date_taken_dt, lat, lon)
        
        return True
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return False

def update_inspections(date_taken_dt, lat, lon):
    """
    Update the inspections data structure with a new or existing inspection.
    Groups photos by date into inspection entries.
    
    Parameters:
        date_taken_dt: datetime object of when the photo was taken
        lat: latitude coordinate
        lon: longitude coordinate
    """
    # Format date for comparison (just keep the date part)
    inspection_date = date_taken_dt.date()
    
    # Check if this inspection date already exists
    existing_inspection = None
    existing_index = None
    
    for i, inspection in enumerate(st.session_state.inspections):
        # Handle both datetime and string date formats
        if isinstance(inspection['date'], datetime):
            existing_date = inspection['date'].date()
        else:
            try:
                existing_date = datetime.strptime(inspection['date'], "%Y:%m:%d %H:%M:%S").date()
            except ValueError:
                # If parsing fails, try another format or skip
                continue
        
        if existing_date == inspection_date:
            existing_inspection = inspection
            existing_index = i
            break
    
    # Update existing inspection or create a new one
    if existing_inspection:
        # Increment photo count for existing inspection
        st.session_state.inspections[existing_index]['photo_count'] += 1
        
        # Update GPS if previously None
        if st.session_state.inspections[existing_index]['gps'][0] is None and lat is not None:
            st.session_state.inspections[existing_index]['gps'] = (lat, lon)
            
        # Set as selected inspection
        st.session_state.selected_inspection = existing_index
    else:
        # Create new inspection
        new_inspection = {
            'date': date_taken_dt,
            'gps': (lat, lon),
            'weather': {},
            'photo_count': 1
        }
        st.session_state.inspections.append(new_inspection)
        st.session_state.selected_inspection = len(st.session_state.inspections) - 1