import requests
from datetime import datetime

def get_weather_open_meteo(lat, lon, dt):
    """
    Retrieve historical weather data for a specific datetime and location using Open-Meteo API.

    Parameters:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        dt (datetime): Datetime object for which to retrieve weather info

    Returns:
        dict: Weather data for the hour closest to the given time
    """
    if not lat or not lon or not dt:
        return {
            "weather_datetime": str(datetime.now()) if dt is None else str(dt),
            "weather_temperature_C": None,
            "weather_precipitation_mm": None,
            "weather_cloud_cover_percent": None,
            "weather_wind_speed_kph": None,
            "weather_code": None,
            "weather_source": "Error: Missing location or date information"
        }
    
    # Format the date as required by the API
    date_str = dt.strftime("%Y-%m-%d")
    hour = dt.hour

    # Build request parameters
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": "temperature_2m,precipitation,cloudcover,windspeed_10m,weathercode",
        "timezone": "auto"
    }

    # Send the request
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()["hourly"]

        # Parse timestamps and find closest hour
        times = [datetime.fromisoformat(t) for t in data["time"]]
        closest_index = min(range(len(times)), key=lambda i: abs(times[i].hour - hour))

        # Extract weather details at closest hour
        weather_info = {
            "weather_datetime": str(times[closest_index]),
            "weather_temperature_C": data["temperature_2m"][closest_index],
            "weather_precipitation_mm": data["precipitation"][closest_index],
            "weather_cloud_cover_percent": data["cloudcover"][closest_index],
            "weather_wind_speed_kph": data["windspeed_10m"][closest_index],
            "weather_code": data["weathercode"][closest_index],
            "weather_source": "Open-Meteo API"
        }

        return weather_info
        
    except Exception as e:
        # Return error information in case of any exception
        return {
            "weather_datetime": str(dt),
            "weather_temperature_C": None,
            "weather_precipitation_mm": None,
            "weather_cloud_cover_percent": None,
            "weather_wind_speed_kph": None,
            "weather_code": None,
            "weather_source": f"Error: {str(e)}"
        }
    
    