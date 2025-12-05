"""
Weather Matching Module - Integrates weather data into recommendations. 

This module fetches real-time weather data from the Open-Meteo API
and calculates weather compatibility scores based on user temperature preferences. 

Part of Requirement #2: API Integration
"""

from typing import Dict, Any, List, Tuple
import requests
import streamlit as st

# Open-Meteo API configuration
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
API_TIMEOUT = 5  # seconds


# =============================================================================
# CURRENT WEATHER FUNCTIONS
# =============================================================================

def get_weather_for_destination(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetches current weather data for a destination from Open-Meteo API.
    
    This function makes an API call to retrieve real-time weather information
    for a specific geographic location.
    
    Args:
        latitude: Geographic latitude of the destination
        longitude: Geographic longitude of the destination
        
    Returns:
        Dictionary containing:
        - temperature: Current temperature in Celsius
        - windspeed: Current wind speed in km/h
        - weathercode: WMO weather code
        - success: Boolean indicating API success
        
    Example:
        >>> weather = get_weather_for_destination(41.3851, 2.1734)  # Barcelona
        >>> print(f"Temperature: {weather['temperature']}°C")
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
        }
        
        response = requests.get(
            OPEN_METEO_BASE_URL, 
            params=params, 
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            current = data.get("current_weather", {})
            return {
                "temperature": current.get("temperature"),
                "windspeed": current.get("windspeed"),
                "weathercode": current.get("weathercode"),
                "success": True,
            }
        else:
            return {"success": False, "error": f"API returned status {response.status_code}"}
            
    except requests.Timeout:
        return {"success": False, "error": "API request timed out"}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def calculate_weather_score(
    destination: Dict[str, Any], 
    preferred_temp_range: Tuple[int, int]
) -> float:
    """
    Calculates a weather compatibility score for a destination. 
    
    This function implements a scoring algorithm that compares the current
    temperature at a destination with the user's preferred temperature range. 
    Score decreases as temperature deviates from the preferred range.
    
    Algorithm:
    - Perfect score (100) if temperature is within preferred range
    - Score decreases by 15 points for every 5°C outside the range
    - Minimum score is 0
    
    Args:
        destination: Destination dictionary with latitude/longitude
        preferred_temp_range: Tuple of (min_temp, max_temp) in Celsius
        
    Returns:
        Float score between 0 and 100
        
    Example:
        >>> score = calculate_weather_score(dest, (20, 30))
        >>> print(f"Weather compatibility: {score}%")
    """
    lat = destination.get('latitude')
    lon = destination.get('longitude')
    
    # Return neutral score if coordinates are missing
    if lat is None or lon is None:
        return 50.0
    
    # Fetch current weather
    weather = get_weather_for_destination(lat, lon)
    
    # Return neutral score if API fails
    if not weather.get("success"):
        return 50.0
    
    temp = weather.get('temperature', 20)
    min_pref, max_pref = preferred_temp_range
    
    # Perfect score if temperature is within preferred range
    if min_pref <= temp <= max_pref:
        return 100.0
    
    # Calculate deviation from preferred range
    if temp < min_pref:
        diff = min_pref - temp
    else:
        diff = temp - max_pref
    
    # Scoring: -15 points per 5°C deviation
    penalty = (diff / 5) * 15
    return max(0.0, 100.0 - penalty)


def enrich_destinations_with_weather(
    destinations: List[Dict[str, Any]], 
    preferred_temp: Tuple[int, int],
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """
    Enriches destination list with weather data and scores. 
    
    This function iterates through all destinations, fetches weather data,
    and adds weather_score and current_temp fields to each destination. 
    Implements caching to avoid redundant API calls. 
    
    Args:
        destinations: List of destination dictionaries
        preferred_temp: User's preferred temperature range (min, max)
        show_progress: Whether to show a progress bar in Streamlit
        
    Returns:
        List of destinations enriched with weather data
        
    Note:
        Weather data is cached in session state to reduce API calls
    """
    enriched = []
    
    # Initialize weather cache in session state
    cache_key = "weather_cache"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}
    
    weather_cache = st.session_state[cache_key]
    
    # Show progress bar if enabled
    if show_progress:
        progress_bar = st.progress(0, text="Loading weather data...")
    
    for i, dest in enumerate(destinations):
        dest_copy = dest.copy()
        dest_id = dest.get("id")
        
        # Check cache first
        if dest_id in weather_cache:
            dest_copy['weather_score'] = weather_cache[dest_id]['score']
            dest_copy['current_temp'] = weather_cache[dest_id].get('temp')
        else:
            # Fetch weather data from API
            lat = dest.get('latitude')
            lon = dest.get('longitude')
            
            if lat and lon:
                weather = get_weather_for_destination(lat, lon)
                if weather.get("success"):
                    score = calculate_weather_score(dest, preferred_temp)
                    dest_copy['weather_score'] = score
                    dest_copy['current_temp'] = weather.get('temperature')
                    
                    # Cache the result
                    weather_cache[dest_id] = {
                        'score': score,
                        'temp': weather.get('temperature'),
                    }
                else:
                    dest_copy['weather_score'] = 50.0
            else:
                dest_copy['weather_score'] = 50.0
        
        enriched.append(dest_copy)
        
        # Update progress bar
        if show_progress:
            progress = (i + 1) / len(destinations)
            progress_bar.progress(progress, text=f"Loading weather data... {i+1}/{len(destinations)}")
    
    # Clear progress bar
    if show_progress:
        progress_bar.empty()
    
    return enriched


def get_weather_description(weathercode: int) -> str:
    """
    Converts WMO weather code to human-readable description. 
    
    Args:
        weathercode: WMO weather interpretation code
        
    Returns:
        String description of weather conditions
    """
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
    }
    return weather_codes.get(weathercode, "Unknown")


# =============================================================================
# FORECAST FUNCTIONS (NEW)
# =============================================================================

def get_forecast_for_destination(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Fetches weather forecast for a specific date range.
    
    Uses Open-Meteo's forecast API for dates within 16 days,
    returns current weather as fallback for dates further out.
    
    Args:
        latitude: Geographic latitude
        longitude: Geographic longitude
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Dictionary containing:
        - avg_temp: Average temperature for the period
        - max_temp: Maximum temperature
        - min_temp: Minimum temperature
        - precipitation_days: Days with rain expected
        - success: Boolean indicating API success
        
    Example:
        >>> forecast = get_forecast_for_destination(41.38, 2.17, "2025-12-20", "2025-12-27")
        >>> print(f"Average temp: {forecast['avg_temp']}°C")
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "weathercode"
            ],
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date,
        }
        
        response = requests.get(
            OPEN_METEO_BASE_URL,
            params=params,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            precipitation = daily.get("precipitation_sum", [])
            
            if temps_max and temps_min:
                avg_max = sum(temps_max) / len(temps_max)
                avg_min = sum(temps_min) / len(temps_min)
                avg_temp = (avg_max + avg_min) / 2
                
                # Count rainy days (precipitation > 1mm)
                rain_days = sum(1 for p in precipitation if p and p > 1)
                
                return {
                    "avg_temp": round(avg_temp, 1),
                    "max_temp": round(max(temps_max), 1),
                    "min_temp": round(min(temps_min), 1),
                    "precipitation_days": rain_days,
                    "total_days": len(temps_max),
                    "success": True,
                    "source": "forecast"
                }
        
        # Fallback to current weather
        current = get_weather_for_destination(latitude, longitude)
        if current.get("success"):
            return {
                "avg_temp": current.get("temperature"),
                "max_temp": current.get("temperature"),
                "min_temp": current.get("temperature"),
                "precipitation_days": 0,
                "total_days": 1,
                "success": True,
                "source": "current"
            }
        
        return {"success": False, "error": "Could not fetch forecast"}
        
    except requests.Timeout:
        return {"success": False, "error": "API request timed out"}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def calculate_forecast_weather_score(
    destination: Dict[str, Any],
    preferred_temp_range: Tuple[int, int],
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Calculates weather score based on forecast for travel dates.
    
    Args:
        destination: Destination dictionary with lat/lon
        preferred_temp_range: Tuple of (min_temp, max_temp)
        start_date: Travel start date (YYYY-MM-DD)
        end_date: Travel end date (YYYY-MM-DD)
        
    Returns:
        Dictionary with weather score and forecast details
    """
    lat = destination.get('latitude')
    lon = destination.get('longitude')
    
    if lat is None or lon is None:
        return {"score": 50.0, "source": "none"}
    
    # Try to get forecast
    forecast = get_forecast_for_destination(lat, lon, start_date, end_date)
    
    if not forecast.get("success"):
        # Fallback to current weather score
        score = calculate_weather_score(destination, preferred_temp_range)
        return {
            "score": score,
            "source": "current"
        }
    
    avg_temp = forecast.get("avg_temp", 20)
    min_pref, max_pref = preferred_temp_range
    
    # Calculate base score from temperature
    if min_pref <= avg_temp <= max_pref:
        temp_score = 100.0
    else:
        if avg_temp < min_pref:
            diff = min_pref - avg_temp
        else:
            diff = avg_temp - max_pref
        temp_score = max(0.0, 100.0 - (diff / 5) * 15)
    
    # Adjust for precipitation (reduce score for rainy days)
    total_days = forecast.get("total_days", 1)
    rain_days = forecast.get("precipitation_days", 0)
    rain_ratio = rain_days / total_days if total_days > 0 else 0
    
    # Reduce score by up to 20 points for rain
    rain_penalty = rain_ratio * 20
    final_score = max(0.0, temp_score - rain_penalty)
    
    return {
        "score": round(final_score, 1),
        "avg_temp": forecast.get("avg_temp"),
        "max_temp": forecast.get("max_temp"),
        "min_temp": forecast.get("min_temp"),
        "precipitation_days": rain_days,
        "total_days": total_days,
        "source": forecast.get("source", "forecast")
    }


def enrich_destinations_with_forecast(
    destinations: List[Dict[str, Any]],
    preferred_temp: Tuple[int, int],
    start_date: str,
    end_date: str,
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """
    Enriches destinations with weather forecast for specific travel dates.
    
    This function fetches weather forecasts for each destination based on
    the user's planned travel dates and calculates compatibility scores. 
    
    Args:
        destinations: List of destination dictionaries
        preferred_temp: User's preferred temperature range (min, max)
        start_date: Travel start date (YYYY-MM-DD)
        end_date: Travel end date (YYYY-MM-DD)
        show_progress: Whether to show progress bar
        
    Returns:
        List of destinations enriched with forecast data including:
        - weather_score: Compatibility score (0-100)
        - forecast_temp: Average forecasted temperature
        - forecast_min: Minimum temperature
        - forecast_max: Maximum temperature
        - rain_days: Expected rainy days
        - weather_source: "forecast" or "current"
    """
    enriched = []
    
    # Initialize cache
    cache_key = f"forecast_cache_{start_date}_{end_date}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}
    
    forecast_cache = st.session_state[cache_key]
    
    if show_progress:
        progress_bar = st.progress(0, text="Loading weather forecasts...")
    
    for i, dest in enumerate(destinations):
        dest_copy = dest.copy()
        dest_id = dest.get("id")
        
        # Check cache
        if dest_id in forecast_cache:
            cached = forecast_cache[dest_id]
            dest_copy['weather_score'] = cached['score']
            dest_copy['forecast_temp'] = cached.get('avg_temp')
            dest_copy['forecast_min'] = cached.get('min_temp')
            dest_copy['forecast_max'] = cached.get('max_temp')
            dest_copy['rain_days'] = cached.get('precipitation_days', 0)
            dest_copy['total_days'] = cached.get('total_days', 1)
            dest_copy['weather_source'] = cached.get('source', 'cached')
        else:
            # Fetch forecast
            forecast_data = calculate_forecast_weather_score(
                dest, preferred_temp, start_date, end_date
            )
            
            dest_copy['weather_score'] = forecast_data['score']
            dest_copy['forecast_temp'] = forecast_data.get('avg_temp')
            dest_copy['forecast_min'] = forecast_data.get('min_temp')
            dest_copy['forecast_max'] = forecast_data.get('max_temp')
            dest_copy['rain_days'] = forecast_data.get('precipitation_days', 0)
            dest_copy['total_days'] = forecast_data.get('total_days', 1)
            dest_copy['weather_source'] = forecast_data.get('source', 'unknown')
            
            # Cache result
            forecast_cache[dest_id] = forecast_data
        
        enriched.append(dest_copy)
        
        if show_progress:
            progress = (i + 1) / len(destinations)
            progress_bar.progress(progress, text=f"Loading forecasts... {i+1}/{len(destinations)}")
    
    if show_progress:
        progress_bar.empty()
    
    return enriched