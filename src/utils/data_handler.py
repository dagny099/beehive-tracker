# src/utils/data_handler.py
import streamlit as st
import os
import json
from datetime import datetime
import io
from PIL import Image

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
                            else:
                                # Log missing file
                                st.warning(f"Photo file not found: {photo.get('filename', 'unknown')}")
                        
                        # Update with only valid photos
                        inspection["photos"] = valid_photos
                        
                        # Update photo count
                        inspection["photo_count"] = len(valid_photos)
                    
                    loaded_inspections.append(inspection)
                
                # Set in session state
                st.session_state.inspections = loaded_inspections
                
                return True
            else:
                st.warning("No inspection data found in saved file.")
                return False
        else:
            st.info("No saved data found. Starting with empty inspections.")
            return False
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return False

def add_photo_to_inspection(photo_data):
    """Add a photo to an existing inspection or create a new one"""
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
            
            # Update this inspection in session state
            st.session_state.inspections[i] = inspection
            st.session_state.selected_inspection = i
            
            found_inspection = True
            break
    
    # If no matching inspection found, create a new one
    if not found_inspection:
        location = "Unknown"
        if 'lat' in photo_data and 'lon' in photo_data and photo_data['lat'] and photo_data['lon']:
            try:
                # Try to format as float if possible
                if isinstance(photo_data['lat'], (float, int)) and isinstance(photo_data['lon'], (float, int)):
                    location = f"{photo_data['lat']:.6f}, {photo_data['lon']:.6f}"
                else:
                    # Otherwise just convert to string
                    location = f"{photo_data['lat']}, {photo_data['lon']}"
            except:
                # Fallback to simple string conversion
                location = f"{photo_data['lat']}, {photo_data['lon']}"
        else:
            location = "Unknown"
            
        new_inspection = {
            'date': date_obj,
            'location': location,
            'photos': [photo_data],
            'photo_count': 1,
            'weather_summary': "Not recorded"
        }
        
        # Add the new inspection
        st.session_state.inspections.append(new_inspection)
        st.session_state.selected_inspection = len(st.session_state.inspections) - 1
    
    # Save changes to disk
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
            # This would need pandas to implement properly
            return None, "CSV export not implemented yet"
        
        else:
            return None, f"Unsupported export format: {format}"
    
    except Exception as e:
        return None, f"Error exporting data: {e}"