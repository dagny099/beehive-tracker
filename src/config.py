# src/config.py
"""
Configuration settings for the Beehive Tracker application.

This module provides centralized configuration management for the app,
including default location settings and other app-wide constants.
"""

# Default location for new inspections when GPS data is not available
# Austin, Texas coordinates (you can change these to your preferred location)
DEFAULT_LOCATION = {
    "latitude": 30.4211179,
    "longitude": -97.6798296,
    "display_name": "Austin, TX"
}

def get_default_location():
    """
    Get the default location for inspections when GPS data is unavailable.

    Returns:
        dict: Dictionary with 'latitude', 'longitude', and 'display_name' keys

    Example:
        >>> location = get_default_location()
        >>> print(f"Default location: {location['display_name']}")
        Default location: Austin, TX
    """
    return DEFAULT_LOCATION.copy()

def format_location_display(lat, lon, display_name=None):
    """
    Format location information for consistent display across the app.

    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        display_name (str, optional): Human-readable location name

    Returns:
        str: Formatted location string for display

    Example:
        >>> format_location_display(30.42, -97.68, "Austin, TX")
        'Austin, TX (30.4211, -97.6800)'
    """
    if display_name:
        return f"{display_name} ({lat:.4f}, {lon:.4f})"
    else:
        return f"{lat:.4f}, {lon:.4f}"

def get_location_data(lat, lon, display_name=None):
    """
    Create a standardized location data structure.

    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        display_name (str, optional): Human-readable name

    Returns:
        dict: Standardized location data structure

    Example:
        >>> location = get_location_data(30.42, -97.68, "Austin, TX")
        >>> print(location)
        {'lat': 30.42, 'lon': -97.68, 'display': 'Austin, TX'}
    """
    return {
        "lat": float(lat),
        "lon": float(lon),
        "display": display_name or format_location_display(lat, lon)
    }