import os
import json
import pandas as pd
from datetime import datetime

class DataManager:
    """Manager class for handling data storage operations."""
    
    def __init__(self, csv_file="hive_color_log.csv", json_file="hive_color_log.json"):
        """Initialize the DataManager with file paths."""
        self.csv_file = csv_file
        self.json_file = json_file
        
    def save_entry(self, data):
        """Save or update a metadata entry to both CSV and JSON storage."""
        try:
            # Add timestamp for the edit
            data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save to CSV
            self._save_to_csv(data)
            
            # Save to JSON
            self._save_to_json(data)
            
            return True
        except Exception as e:
            print(f"Error saving entry: {e}")
            return False
    
    def _save_to_csv(self, data):
        """Save metadata to CSV file."""
        # Define expected columns
        columns = [
            "date", "date_source", "filename", "image_resolution", "camera_model",
            "dominant_color", "palette_1", "palette_2", "palette_3", "palette_4", "palette_5",
            "weather_datetime", "weather_temperature_C", "weather_precipitation_mm",
            "weather_cloud_cover_percent", "weather_wind_speed_kph", "weather_code",
            "weather_source", "hive_state", "notes", "gps_lat", "gps_long", "last_updated"
        ]
        
        # Convert missing data to empty strings for CSV compatibility
        for col in columns:
            if col not in data:
                data[col] = ""
        
        # Prepare data frame with single row
        df_new = pd.DataFrame([data])
        
        if os.path.exists(self.csv_file):
            # Load existing data
            df_existing = pd.read_csv(self.csv_file)
            
            # Remove any existing entry with the same filename
            df_existing = df_existing[df_existing['filename'] != data['filename']]
            
            # Check if df_existing is empty
            if len(df_existing) == 0:
                # If there's no existing data, just use the new data
                df_combined = df_new
            else:
                # Make sure both dataframes have the same columns
                # This addresses the deprecation warning
                for col in df_new.columns:
                    if col not in df_existing.columns:
                        df_existing[col] = ""
                for col in df_existing.columns:
                    if col not in df_new.columns:
                        df_new[col] = ""
                
                # Append new data
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            
            # Save combined data
            df_combined.to_csv(self.csv_file, index=False)
        else:
            # Create new file
            df_new.to_csv(self.csv_file, index=False)
                
    def _save_to_json(self, data):
        """Save metadata to JSON file with enhanced storage of nested data."""
        # Ensure we include all nested data structures as is
        # Ensures proper saving of complex structures like vision_analysis
        
        if os.path.exists(self.json_file):
            # Load existing data
            with open(self.json_file, 'r') as f:
                existing = json.load(f)
                
            # Remove any existing entry with the same filename
            existing = [entry for entry in existing if entry.get('filename') != data['filename']]
            
            # Append new data
            existing.append(data)
            
            # Save updated data
            with open(self.json_file, 'w') as f:
                json.dump(existing, f, indent=2)
        else:
            # Create new file with single entry
            with open(self.json_file, 'w') as f:
                json.dump([data], f, indent=2)
                
    def load_entry(self, filename):
        """Load a specific entry by filename."""
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                entries = json.load(f)
                
            # Find entry with matching filename
            for entry in entries:
                if entry.get('filename') == filename:
                    return entry
                    
        return None
    
    # The following methods should be indented to be part of the DataManager class
    def load_all_entries(self):
        """Load all entries from the JSON file."""
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                return json.load(f)
        return []

    def get_entry_summaries(self):
        """Return summaries of all entries for display in a browser/selector."""
        entries = self.load_all_entries()
        return [
            {
                'filename': entry.get('filename', 'Unknown'),
                'date_taken': entry.get('date', 'Unknown'),
                'hive_state': entry.get('hive_state', 'Unknown'),
                'last_updated': entry.get('last_updated', 'Unknown'),
                'thumbnail': entry.get('dominant_color', '#FFFFFF')
            }
            for entry in entries
        ]