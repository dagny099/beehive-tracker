#!/usr/bin/env python3
"""
Open-Meteo Historical Weather API tool
Usage:
  python test_openmeteo.py --location "Austin, TX" --date 2024-09-21
  python test_openmeteo.py --coords 30.2672,-97.7431 --date 2024-09-21
  python test_openmeteo.py -l "New York" -d 2023-06-15
"""

import requests
import json
import argparse
import sys
from datetime import datetime, date

def get_coordinates_for_location(location_name):
    """
    Simple geocoding using Open-Meteo's geocoding API
    """
    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": location_name,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:
        response = requests.get(geocoding_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return result["latitude"], result["longitude"], result["name"], result.get("country", "")
        else:
            print(f"❌ Location '{location_name}' not found")
            return None
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return None

def validate_date(date_string):
    """
    Validate and parse date string in YYYY-MM-DD format
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()

        # Check if date is not in the future (Open-Meteo is historical only)
        if date_obj > date.today():
            print(f"⚠️  Warning: {date_string} is in the future. Open-Meteo only provides historical data.")
            print(f"   Using today's date instead: {date.today()}")
            return str(date.today())

        # Check if date is too far back (before 1940)
        if date_obj.year < 1940:
            print(f"❌ Date {date_string} is too far back. Open-Meteo data starts from 1940.")
            return None

        return date_string
    except ValueError:
        print(f"❌ Invalid date format: {date_string}")
        print("   Please use YYYY-MM-DD format (e.g., 2024-09-21)")
        return None

def test_openmeteo_historical_weather(latitude, longitude, test_date, location_display_name=""):

    # Open-Meteo Historical Weather API endpoint
    url = "https://archive-api.open-meteo.com/v1/archive"

    # API parameters
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": test_date,
        "end_date": test_date,  # Same date for single day
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode",
        "timezone": "auto"  # Let Open-Meteo determine timezone from coordinates
    }

    print(f"🌤️  Testing Open-Meteo Historical Weather API")
    print(f"📍 Location: {location_display_name} ({latitude}, {longitude})")
    print(f"📅 Date: {test_date}")
    print(f"🔗 URL: {url}")
    print()

    try:
        print("Making API request...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        print("✅ API call successful!")
        print(f"📊 Response status: {response.status_code}")
        print()

        # Display daily summary
        if "daily" in data:
            daily = data["daily"]
            print("📋 Daily Weather Summary:")
            print(f"  🌡️  Max Temperature: {daily['temperature_2m_max'][0]}°C")
            print(f"  🌡️  Min Temperature: {daily['temperature_2m_min'][0]}°C")
            print(f"  🌧️  Precipitation: {daily['precipitation_sum'][0]}mm")
            print(f"  💨 Max Wind Speed: {daily['windspeed_10m_max'][0]} km/h")
            print(f"  ☁️  Weather Code: {daily['weathercode'][0]}")

        # Display first few hourly readings
        if "hourly" in data and len(data["hourly"]["temperature_2m"]) > 0:
            print()
            print("⏰ First 6 Hourly Readings:")
            for i in range(min(6, len(data["hourly"]["time"]))):
                time = data["hourly"]["time"][i]
                temp = data["hourly"]["temperature_2m"][i]
                precip = data["hourly"]["precipitation"][i]
                wind = data["hourly"]["windspeed_10m"][i]
                print(f"  {time}: {temp}°C, {precip}mm rain, {wind} km/h wind")

        # Show raw JSON only if running standalone (not as imported function)
        if __name__ == "__main__":
            print()
            print("🎯 Raw JSON Response (first 500 chars):")
            print(json.dumps(data, indent=2)[:500] + "...")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing response: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Get historical weather data for any location and date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --location "Austin, TX" --date 2024-09-21
  %(prog)s --location "New York City" --date 2023-12-25
  %(prog)s --coords 30.2672,-97.7431 --date 2024-01-15
  %(prog)s -l "London, UK" -d 2023-06-01
  %(prog)s -c 51.5074,-0.1278 -d 2023-06-01  # London coordinates
        """)

    # Location options (mutually exclusive)
    location_group = parser.add_mutually_exclusive_group(required=True)
    location_group.add_argument("-l", "--location",
                               help="Location name (e.g., 'Austin, TX', 'London, UK')")
    location_group.add_argument("-c", "--coords",
                               help="Coordinates as 'latitude,longitude' (e.g., '30.2672,-97.7431')")

    # Date argument
    parser.add_argument("-d", "--date", required=True,
                       help="Date in YYYY-MM-DD format (e.g., '2024-09-21')")

    # Optional verbose output
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show detailed API response")

    args = parser.parse_args()

    # Validate date
    valid_date = validate_date(args.date)
    if not valid_date:
        sys.exit(1)

    # Get coordinates
    if args.location:
        print(f"🔍 Looking up coordinates for '{args.location}'...")
        coord_result = get_coordinates_for_location(args.location)
        if not coord_result:
            sys.exit(1)

        latitude, longitude, location_name, country = coord_result
        display_name = f"{location_name}, {country}" if country else location_name
        print(f"✅ Found: {display_name}")
        print()

    elif args.coords:
        try:
            coord_parts = args.coords.split(',')
            if len(coord_parts) != 2:
                raise ValueError("Invalid format")
            latitude = float(coord_parts[0].strip())
            longitude = float(coord_parts[1].strip())
            display_name = f"Custom coordinates"

            # Basic coordinate validation
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                raise ValueError("Coordinates out of range")

        except ValueError as e:
            print(f"❌ Invalid coordinates format: {args.coords}")
            print("   Please use 'latitude,longitude' format (e.g., '30.2672,-97.7431')")
            sys.exit(1)

    # Make the API call
    result = test_openmeteo_historical_weather(latitude, longitude, valid_date, display_name)

    if result:
        print("\n🚀 Weather data retrieved successfully!")
        if not args.verbose:
            print("💡 Use --verbose flag to see full API response")
        print("💡 This API can be integrated into your beehive tracker for historical weather context.")
        return True
    else:
        print("\n💥 Failed to get weather data - check your internet connection and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)