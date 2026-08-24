# src/utils/data_handler.py
import streamlit as st
import os
import json
from datetime import datetime
import io
from PIL import Image
from src.config import get_default_location, get_location_data
from src.api_services.weather import get_weather_open_meteo

def get_inspection_title(inspection_index):
    """Get a descriptive title for an inspection based on its date and time"""
    if 'inspections' not in st.session_state or not st.session_state.inspections:
        return "Inspection"

    if inspection_index >= len(st.session_state.inspections):
        return "Inspection"

    inspection = st.session_state.inspections[inspection_index]
    inspection_date = inspection.get('date')

    if not inspection_date:
        return "Inspection"

    try:
        # Handle different date formats
        if isinstance(inspection_date, datetime):
            dt = inspection_date
        elif isinstance(inspection_date, str):
            # Try ISO format first
            if 'T' in inspection_date:
                dt = datetime.fromisoformat(inspection_date.replace('Z', '+00:00'))
            elif '-' in inspection_date and ':' in inspection_date:
                # Handle format like "2023-03-03 00:00:00"
                dt = datetime.strptime(inspection_date, "%Y-%m-%d %H:%M:%S")
            else:
                # Try other formats
                dt = datetime.strptime(inspection_date, "%Y:%m:%d %H:%M:%S")
        else:
            return "Inspection"

        # If we have photos, use the first photo's timestamp for more precise time
        if 'photos' in inspection and inspection['photos']:
            first_photo = inspection['photos'][0]
            photo_date = first_photo.get('date_taken')
            if photo_date:
                try:
                    # Parse photo timestamp format: "2021:05:21 14:47:43"
                    photo_dt = datetime.strptime(photo_date, "%Y:%m:%d %H:%M:%S")
                    # Use photo's date but keep inspection's date if no time info
                    dt = photo_dt
                except:
                    pass  # Keep using inspection date

        # Format as "Inspection on Mar 21, 2021 at 2:47pm"
        return dt.strftime("Inspection on %b %d, %Y at %I:%M%p").replace('AM', 'am').replace('PM', 'pm')

    except:
        return "Inspection"

def get_inspection_letter(inspection_index):
    """Legacy function for backward compatibility - now returns bee emoji"""
    return "🐝"

def get_inspection_location(photo_data):
    """
    Determine location for inspection using priority system:
    1. Photo GPS data (if available)
    2. Default location from config
    3. "Unknown" as fallback

    Args:
        photo_data (dict): Photo data containing potential lat/lon

    Returns:
        dict: Location data structure with lat, lon, display keys
    """
    # Priority 1: Photo GPS data
    if ('lat' in photo_data and 'lon' in photo_data and
        photo_data['lat'] is not None and photo_data['lon'] is not None):
        try:
            lat = float(photo_data['lat'])
            lon = float(photo_data['lon'])
            # Don't provide display name, let it default to coordinates
            return get_location_data(lat, lon)
        except (ValueError, TypeError):
            pass  # Fall through to default

    # Priority 2: Default location from config
    default_loc = get_default_location()
    return get_location_data(
        default_loc['latitude'],
        default_loc['longitude'],
        default_loc['display_name']
    )

def fetch_weather_for_inspection(inspection):
    """
    Automatically fetch weather data for an inspection if conditions are met.

    Args:
        inspection (dict): Inspection data with location and date

    Returns:
        dict or None: Weather data if successfully fetched, None otherwise
    """
    # Only fetch if we don't already have weather data
    if inspection.get('weather_data'):
        return inspection.get('weather_data')  # Return existing data

    # Need location and date to fetch weather
    location = inspection.get('location')
    inspection_date = inspection.get('date')

    if not location or not inspection_date:
        return None

    # Extract coordinates
    if isinstance(location, dict):
        lat = location.get('lat')
        lon = location.get('lon')
    else:
        return None  # Old format, can't extract coordinates

    if not (lat and lon):
        return None

    # Convert date to datetime if needed
    if isinstance(inspection_date, datetime):
        dt = inspection_date
    else:
        try:
            dt = datetime.fromisoformat(inspection_date) if isinstance(inspection_date, str) else inspection_date
        except:
            return None  # Can't parse date

    # Fetch weather data
    try:
        weather_data = get_weather_open_meteo(lat, lon, dt)
        if weather_data and weather_data.get('weather_source') != 'Error':
            return weather_data
    except Exception as e:
        # Log error but don't fail the inspection creation
        print(f"Weather fetch failed: {e}")

    return None

def save_inspections_to_disk():
    """Save inspection data to disk"""
    try:
        data_dir = os.path.join("data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Prepare data for serialization
        save_data = {
            "inspections": [],
            "last_save": datetime.now().isoformat()
        }
        
        # Process inspections for saving
        if 'inspections' in st.session_state and st.session_state.inspections:
            for inspection in st.session_state.inspections:
                # Create a serializable copy
                insp_copy = inspection.copy()
                
                # Process photos to remove non-serializable data
                if "photos" in insp_copy:
                    processed_photos = []
                    for photo in insp_copy["photos"]:
                        # Make a copy without the image data
                        photo_copy = {k: v for k, v in photo.items() if k != 'data'}
                        processed_photos.append(photo_copy)
                    
                    insp_copy["photos"] = processed_photos
                
                # Handle datetime objects
                if "date" in insp_copy:
                    if isinstance(insp_copy["date"], datetime):
                        insp_copy["date"] = insp_copy["date"].isoformat()
                    
                save_data["inspections"].append(insp_copy)
        
        # Save to JSON file
        with open(os.path.join(data_dir, "inspections.json"), "w") as f:
            json.dump(save_data, f, indent=2)
            
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def load_inspections_from_disk():
    """Load inspection data from disk"""
    try:
        data_file = os.path.join("data", "inspections.json")
        
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)
                
            # Process loaded inspections
            if "inspections" in data:
                loaded_inspections = []
                
                for inspection in data["inspections"]:
                    # Convert date strings back to datetime objects
                    if "date" in inspection and isinstance(inspection["date"], str):
                        try:
                            inspection["date"] = datetime.fromisoformat(inspection["date"])
                        except:
                            # Keep as string if parsing fails
                            pass
                    
                    # Process photos to verify file paths
                    if "photos" in inspection:
                        valid_photos = []
                        
                        for photo in inspection["photos"]:
                            if "file_path" in photo and os.path.exists(photo["file_path"]):
                                # Photo file exists, keep it
                                valid_photos.append(photo)
                            # Silently skip missing files during load
                        
                        # Update with only valid photos
                        inspection["photos"] = valid_photos
                        
                        # Update photo count
                        inspection["photo_count"] = len(valid_photos)
                    
                    loaded_inspections.append(inspection)
                
                # Migrate old inspections to new format and fetch weather
                migrated_inspections = []
                migration_needed = False

                for inspection in loaded_inspections:
                    # Migrate location format - convert all string locations to structured format
                    if isinstance(inspection.get('location'), str):
                        migration_needed = True
                        old_location = inspection['location']

                        if old_location in ["Unknown", "Default location"]:
                            # Use default location for unknown locations
                            inspection['location'] = get_inspection_location({})
                        else:
                            # Try to parse coordinate string (e.g., "30.420881, -97.679250")
                            try:
                                coords = old_location.split(', ')
                                if len(coords) == 2:
                                    lat = float(coords[0])
                                    lon = float(coords[1])
                                    inspection['location'] = get_location_data(lat, lon, "GPS coordinates")
                                else:
                                    # Keep as display name and use default coordinates
                                    inspection['location'] = get_inspection_location({})
                            except (ValueError, AttributeError):
                                # If parsing fails, use default location
                                inspection['location'] = get_inspection_location({})

                    # Ensure location is in new structured format
                    elif not isinstance(inspection.get('location'), dict):
                        migration_needed = True
                        inspection['location'] = get_inspection_location({})

                    # Add weather data if missing
                    if not inspection.get('weather_data'):
                        migration_needed = True
                        weather_data = fetch_weather_for_inspection(inspection)
                        if weather_data:
                            inspection['weather_data'] = weather_data

                    # Remove old weather_summary field if present
                    if 'weather_summary' in inspection:
                        migration_needed = True
                        del inspection['weather_summary']

                    migrated_inspections.append(inspection)

                # Save migrated data if any changes were made
                if migration_needed:
                    st.session_state.inspections = migrated_inspections
                    save_inspections_to_disk()
                    # Migration happened silently - no UI message needed

                # Set in session state
                st.session_state.inspections = migrated_inspections

                return True
            else:
                # No inspection data in file
                return False
        else:
            # No saved data file exists yet
            return False
    except Exception as e:
        # Log error but don't show UI message during initialization
        import sys
        print(f"Error loading data: {e}", file=sys.stderr)
        return False

def add_photo_to_inspection(photo_data, defer_save=False):
    """Add a photo to an existing inspection or create a new one

    Args:
        photo_data (dict): The photo record to file into an inspection.
        defer_save (bool): Skip the write to disk. Bulk import passes True and
            calls save_inspections_to_disk() once at the end. Saving inside the
            loop re-serializes every inspection for every photo, which is
            quadratic and makes a large import look hung. Single-photo callers
            leave this False so their behaviour is unchanged.
    """
    # Extract date from photo data
    if "date_taken" in photo_data and photo_data["date_taken"] != "Unknown":
        try:
            # Try to parse the date
            date_obj = datetime.strptime(photo_data["date_taken"], "%Y:%m:%d %H:%M:%S")
            
            # Truncate to date only (no time) for grouping
            date_str = date_obj.strftime("%Y-%m-%d")
        except:
            date_str = None
    else:
        date_str = None
    
    # If no valid date, use today
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Initialize inspections list if needed
    if 'inspections' not in st.session_state:
        st.session_state.inspections = []
    
    # Look for an existing inspection on the same date
    found_inspection = False
    for i, inspection in enumerate(st.session_state.inspections):
        insp_date = inspection['date']
        
        # Convert to date string for comparison
        if isinstance(insp_date, datetime):
            insp_date_str = insp_date.strftime("%Y-%m-%d")
        elif isinstance(insp_date, str):
            try:
                insp_date_obj = datetime.strptime(insp_date, "%Y:%m:%d %H:%M:%S")
                insp_date_str = insp_date_obj.strftime("%Y-%m-%d")
            except:
                try:
                    # Try ISO format
                    insp_date_obj = datetime.fromisoformat(insp_date)
                    insp_date_str = insp_date_obj.strftime("%Y-%m-%d")
                except:
                    # Keep as is if parsing fails
                    insp_date_str = insp_date
        else:
            continue
        
        # If the dates match, add to this inspection
        if insp_date_str == date_str:
            if 'photos' not in inspection:
                inspection['photos'] = []

            inspection['photos'].append(photo_data)
            inspection['photo_count'] = len(inspection['photos'])

            # Update location if this photo has GPS data and inspection doesn't have proper location yet
            if ('lat' in photo_data and 'lon' in photo_data and
                photo_data['lat'] is not None and photo_data['lon'] is not None):
                # Only update if inspection has old string-based location or no location
                current_location = inspection.get('location')
                if (not current_location or
                    isinstance(current_location, str) or
                    current_location.get('display') == 'Austin, TX'):  # Upgrade from default to GPS
                    inspection['location'] = get_inspection_location(photo_data)
            elif not inspection.get('location'):
                # If no GPS and no existing location, use default
                inspection['location'] = get_inspection_location(photo_data)

            # Automatically fetch weather data if not present.
            # The attempted flag stops a failed lookup from being retried once
            # per photo. During a bulk import of one day's photos that meant a
            # fresh blocking HTTP call, and its timeout, for every photo in the
            # inspection.
            if not inspection.get('weather_data') and not inspection.get('weather_fetch_attempted'):
                weather_data = fetch_weather_for_inspection(inspection)
                inspection['weather_fetch_attempted'] = True
                if weather_data:
                    inspection['weather_data'] = weather_data

            # Update this inspection in session state
            st.session_state.inspections[i] = inspection
            st.session_state.selected_inspection = i

            # Set the associated inspection for display purposes
            inspection_title = get_inspection_title(i)
            st.session_state.associated_inspection = inspection_title

            found_inspection = True
            break
    
    # If no matching inspection found, create a new one
    if not found_inspection:
        # Get location using priority system: GPS -> Default -> Unknown
        location_data = get_inspection_location(photo_data)

        new_inspection = {
            'date': date_obj,
            'location': location_data,  # Now stores structured location data
            'photos': [photo_data],
            'photo_count': 1,
            'weather_data': None,  # Will be populated automatically if location available
        }

        # Automatically fetch weather data for new inspection
        weather_data = fetch_weather_for_inspection(new_inspection)
        new_inspection['weather_fetch_attempted'] = True
        if weather_data:
            new_inspection['weather_data'] = weather_data

        # Add the new inspection
        st.session_state.inspections.append(new_inspection)
        st.session_state.selected_inspection = len(st.session_state.inspections) - 1

        # Set the associated inspection for display purposes
        inspection_index = len(st.session_state.inspections) - 1
        inspection_title = get_inspection_title(inspection_index)
        st.session_state.associated_inspection = inspection_title
    
    # Save changes to disk (unless the caller is batching, see defer_save)
    if not defer_save:
        save_inspections_to_disk()

    return True

def get_inspection_by_id(inspection_id):
    """Get inspection data by ID"""
    if 'inspections' in st.session_state and inspection_id < len(st.session_state.inspections):
        return st.session_state.inspections[inspection_id]
    return None

def update_inspection_data(inspection_id, field, value):
    """Update a field in an inspection"""
    if 'inspections' in st.session_state and inspection_id < len(st.session_state.inspections):
        st.session_state.inspections[inspection_id][field] = value
        save_inspections_to_disk()
        return True
    return False

def delete_inspection(inspection_id):
    """Delete an inspection and its photos"""
    if 'inspections' in st.session_state and inspection_id < len(st.session_state.inspections):
        inspection = st.session_state.inspections[inspection_id]
        
        # Delete photo files
        if 'photos' in inspection:
            for photo in inspection['photos']:
                if 'file_path' in photo and os.path.exists(photo['file_path']):
                    try:
                        os.remove(photo['file_path'])
                    except:
                        pass
        
        # Remove from session state
        del st.session_state.inspections[inspection_id]
        
        # Reset selected inspection if needed
        if 'selected_inspection' in st.session_state and st.session_state.selected_inspection == inspection_id:
            st.session_state.selected_inspection = None
        
        # Save changes
        save_inspections_to_disk()
        return True
    return False

def export_inspection_data(format="json"):
    """Export inspection data to a file"""
    if 'inspections' not in st.session_state or not st.session_state.inspections:
        return None, "No inspection data to export"
    
    try:
        if format == "json":
            # Prepare data for export
            export_data = {"inspections": []}
            
            for inspection in st.session_state.inspections:
                # Create a serializable copy
                insp_copy = inspection.copy()
                
                # Process photos to remove non-serializable data
                if "photos" in insp_copy:
                    processed_photos = []
                    for photo in insp_copy["photos"]:
                        # Make a copy without the image data
                        photo_copy = {k: v for k, v in photo.items() if k != 'data'}
                        processed_photos.append(photo_copy)
                    
                    insp_copy["photos"] = processed_photos
                
                # Handle datetime objects
                if "date" in insp_copy and isinstance(insp_copy["date"], datetime):
                    insp_copy["date"] = insp_copy["date"].isoformat()
                    
                export_data["inspections"].append(insp_copy)
            
            # Convert to JSON string
            json_data = json.dumps(export_data, indent=2)
            return json_data, None
        
        elif format == "csv":
            # Flatten inspection data for CSV export using pandas
            import pandas as pd

            # Prepare flattened data for CSV
            flattened_data = []

            for inspection in st.session_state.inspections:
                # Base inspection data
                base_data = {
                    'inspection_id': inspection.get('id', ''),
                    'inspection_date': inspection.get('date', ''),
                    'inspection_notes': inspection.get('notes', ''),
                    'location_name': inspection.get('location', {}).get('name', ''),
                    'location_lat': inspection.get('location', {}).get('lat', ''),
                    'location_lon': inspection.get('location', {}).get('lon', ''),
                    'weather_temperature_c': inspection.get('weather_data', {}).get('temperature_c', ''),
                    'weather_humidity_percent': inspection.get('weather_data', {}).get('humidity_percent', ''),
                    'weather_wind_speed_kmh': inspection.get('weather_data', {}).get('wind_speed_kmh', ''),
                    'weather_precipitation_mm': inspection.get('weather_data', {}).get('precipitation_mm', ''),
                    'weather_description': inspection.get('weather_data', {}).get('description', ''),
                    'photo_count': len(inspection.get('photos', []))
                }

                # If there are photos, create a row for each photo
                if inspection.get('photos'):
                    for idx, photo in enumerate(inspection['photos']):
                        photo_data = base_data.copy()
                        photo_data.update({
                            'photo_index': idx + 1,
                            'photo_filename': photo.get('filename', ''),
                            'photo_file_size': photo.get('file_size', ''),
                            'photo_timestamp': photo.get('timestamp', ''),
                            'photo_camera_make': photo.get('camera_make', ''),
                            'photo_camera_model': photo.get('camera_model', ''),
                            'photo_gps_lat': photo.get('gps_coordinates', {}).get('lat', ''),
                            'photo_gps_lon': photo.get('gps_coordinates', {}).get('lon', ''),
                            'photo_colors': ', '.join(photo.get('colors', [])),
                            'vision_labels': ', '.join([label.get('description', '') for label in photo.get('vision_analysis', {}).get('labels', [])]),
                            'vision_confidence': ', '.join([str(label.get('score', '')) for label in photo.get('vision_analysis', {}).get('labels', [])])
                        })
                        flattened_data.append(photo_data)
                else:
                    # If no photos, still include the inspection data
                    photo_data = base_data.copy()
                    photo_data.update({
                        'photo_index': 0,
                        'photo_filename': '',
                        'photo_file_size': '',
                        'photo_timestamp': '',
                        'photo_camera_make': '',
                        'photo_camera_model': '',
                        'photo_gps_lat': '',
                        'photo_gps_lon': '',
                        'photo_colors': '',
                        'vision_labels': '',
                        'vision_confidence': ''
                    })
                    flattened_data.append(photo_data)

            # Create DataFrame and convert to CSV
            if flattened_data:
                df = pd.DataFrame(flattened_data)
                csv_data = df.to_csv(index=False)
                return csv_data, None
            else:
                return None, "No data to export"
        
        else:
            return None, f"Unsupported export format: {format}"
    
    except Exception as e:
        return None, f"Error exporting data: {e}"