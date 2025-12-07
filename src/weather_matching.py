"""
Weather data from Open-Meteo API.
Calculates weather scores based on user temperature preferences and enriches destination data.
Structure as following (functions):
    - get_weather: Fetch current weather for a location.
    - get_forecast: Fetch weather forecast for date range.
    - calc_weather_score: Score 0-100 based on temperature match.
    - enrich_destinations_with_weather: Add current weather data to destinations.
    - enrich_destinations_with_forecast: Add forecast data to destinations for specific travel dates.
"""
# import necessary libraries and API
from typing import Dict, Any, List, Tuple
import requests
import streamlit as st

API_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10  # Increased timeout


# Get current weather data for a location
def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    try:
        # Make API request
        resp = requests.get(API_URL, params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=TIMEOUT)
        
        # Check for successful response
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current_weather", {})
            temp = current.get("temperature")
            
            # Return relevant weather data if available
            if temp is not None:
                return {"temperature": temp, "windspeed": current.get("windspeed"), "success": True}
    
    # If any error occurs, log it and return failure
    except requests.RequestException as e:
        print(f"Weather API error: {e}")
    
    return {"success": False}


# Fetch weather forecast for the specified date range and location
def get_forecast(lat: float, lon: float, start: str, end: str) -> Dict[str, Any]:
    try:
        # Make API request for daily forecast data
        resp = requests.get(API_URL, params={"latitude": lat, "longitude": lon, "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"], "timezone": "auto", "start_date": start, "end_date": end}, timeout=TIMEOUT)
        
        # Check for successful response
        if resp.status_code == 200:
            data = resp.json()
            daily = data.get("daily", {})
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            
            # Calculate average temperatures and rain days
            if temps_max and temps_min:
                avg = (sum(temps_max)/len(temps_max) + sum(temps_min)/len(temps_min)) / 2
                rain_days = sum(1 for p in precip if p and p > 1)
                
                # Return calculated forecast data
                return {"avg_temp": round(avg, 1), "max_temp": round(max(temps_max), 1), "min_temp": round(min(temps_min), 1), "rain_days": rain_days, "total_days": len(temps_max), "success": True}
            
    # If any error occurs, log it and return failure       
    except requests.RequestException as e:
        print(f"Forecast API error: {e}")
    return {"success": False}


# Calculate weather score based on temperature preference (0-100 scale, 100 = perfect match, 0 = very bad match and 50 as fallback if no data is available)
def calc_weather_score(temp: float, preferred: Tuple[int, int]) -> float:
    if temp is None:
        return 50.0
    
    # Unpack preferred temperature range
    min_pref, max_pref = preferred
    
    if min_pref <= temp <= max_pref:
        return 100.0
    
    # How far outside range
    if temp < min_pref:
        diff = min_pref - temp
    else:
        diff = temp - max_pref
    
    # -15 points per 5 degrees outside range
    penalty = (diff / 5) * 15
    return max(0.0, 100.0 - penalty)


# Enrich destinations with current weather data if forecast is not available
def enrich_destinations_with_weather(destinations: List[Dict], preferred: Tuple[int, int], show_progress: bool = True) -> List[Dict]:
    if "weather_cache" not in st.session_state:
        st.session_state["weather_cache"] = {}
    cache = st.session_state["weather_cache"]
    
    # Show progress bar if enabled
    if show_progress:
        progress = st.progress(0, text="Loading weather...")
    
    enriched = []
    success_count = 0
    
    # Iterate through destinations to fetch and calculate weather data
    for i, dest in enumerate(destinations):
        d = dest.copy()
        dest_id = dest.get("id")
        
        # Check cache first
        if dest_id in cache:
            d['weather_score'] = cache[dest_id]['score']
            d['current_temp'] = cache[dest_id].get('temp')
            if d['current_temp'] is not None:
                success_count += 1

        # If not cached, fetch from API
        else:
            lat = dest.get('latitude')
            lon = dest.get('longitude')
            
            # Only fetch if coordinates are available
            if lat is not None and lon is not None:
                weather = get_weather(lat, lon)
                
                # If successful, calculate score and cache it
                if weather.get("success"):
                    temp = weather.get('temperature')
                    score = calc_weather_score(temp, preferred)
                    d['weather_score'] = score
                    d['current_temp'] = temp
                    cache[dest_id] = {'score': score, 'temp': temp}
                    success_count += 1
                else:
                    d['weather_score'] = 50.0
                    d['current_temp'] = None
            else:
                d['weather_score'] = 50.0
                d['current_temp'] = None
        
        enriched.append(d)
        
        # Update progress bar if enabled
        if show_progress:
            progress.progress((i + 1) / len(destinations), text=f"Weather: {i+1}/{len(destinations)}")
    
    # Clear progress bar and show summary if enabled
    if show_progress:
        progress.empty()
        if success_count < len(destinations):
            st.caption(f"☁️ Weather loaded for {success_count}/{len(destinations)} destinations")
    
    return enriched


# Enrich destinations with forecast data for specific travel dates if forecast is available
def enrich_destinations_with_forecast(destinations: List[Dict], preferred: Tuple[int, int], start: str, end: str, show_progress: bool = True) -> List[Dict]:
    cache_key = f"forecast_{start}_{end}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}
    cache = st.session_state[cache_key]
    
    # Show progress bar if enabled
    if show_progress:
        progress = st.progress(0, text="Loading forecasts...")
    
    enriched = []
    success_count = 0
    
    # Iterate through destinations to fetch and calculate forecast data
    for i, dest in enumerate(destinations):
        d = dest.copy()
        dest_id = dest.get("id")
        
        # Check cache first
        if dest_id in cache:
            cached = cache[dest_id]
            d['weather_score'] = cached['score']
            d['forecast_temp'] = cached.get('avg_temp')
            d['rain_days'] = cached.get('rain_days', 0)
            if d['forecast_temp'] is not None:
                success_count += 1
        
        # If not cached, fetch from API
        else:
            lat = dest.get('latitude')
            lon = dest.get('longitude')
            
            # Only fetch if coordinates are available
            if lat is not None and lon is not None:
                forecast = get_forecast(lat, lon, start, end)
                
                # If successful, calculate score and cache it
                if forecast.get("success"):
                    avg_temp = forecast.get('avg_temp', 20)
                    temp_score = calc_weather_score(avg_temp, preferred)
                    
                    # Reduce score for rainy days
                    total_days = forecast.get('total_days', 1)
                    rain_days = forecast.get('rain_days', 0)
                    rain_penalty = (rain_days / total_days) * 20 if total_days > 0 else 0
                    final_score = max(0, temp_score - rain_penalty)
                    
                    d['weather_score'] = round(final_score, 1)
                    d['forecast_temp'] = avg_temp
                    d['rain_days'] = rain_days
                    
                    cache[dest_id] = {
                        'score': d['weather_score'],
                        'avg_temp': avg_temp,
                        'rain_days': rain_days
                    }
                    success_count += 1
                else:
                    d['weather_score'] = 50.0
                    d['forecast_temp'] = None
                    d['rain_days'] = 0
            else:
                d['weather_score'] = 50.0
                d['forecast_temp'] = None
                d['rain_days'] = 0
        
        enriched.append(d)
        
        # Update progress bar if enabled
        if show_progress:
            progress.progress((i + 1) / len(destinations), text=f"Forecast: {i+1}/{len(destinations)}")
    
    # Clear progress bar and show summary if enabled
    if show_progress:
        progress.empty()
        if success_count < len(destinations):
            st.caption(f"🌤️ Forecast loaded for {success_count}/{len(destinations)} destinations")
    
    return enriched