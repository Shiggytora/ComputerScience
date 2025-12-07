"""
Weather data from Open-Meteo API.
Calculates weather scores based on user temperature preferences.
"""

from typing import Dict, Any, List, Tuple
import requests
import streamlit as st

API_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10  # Increased timeout


def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch current weather for a location."""
    try:
        resp = requests.get(API_URL, params={
            "latitude": lat, 
            "longitude": lon, 
            "current_weather": True
        }, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current_weather", {})
            temp = current.get("temperature")
            
            if temp is not None:
                return {
                    "temperature": temp,
                    "windspeed": current.get("windspeed"),
                    "success": True
                }
    except requests.RequestException as e:
        # Log error for debugging
        print(f"Weather API error: {e}")
    
    return {"success": False}


def get_forecast(lat: float, lon: float, start: str, end: str) -> Dict[str, Any]:
    """Fetch weather forecast for date range."""
    try:
        resp = requests.get(API_URL, params={
            "latitude": lat, 
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
            "timezone": "auto", 
            "start_date": start, 
            "end_date": end
        }, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            daily = data.get("daily", {})
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            
            if temps_max and temps_min:
                avg = (sum(temps_max)/len(temps_max) + sum(temps_min)/len(temps_min)) / 2
                rain_days = sum(1 for p in precip if p and p > 1)
                
                return {
                    "avg_temp": round(avg, 1),
                    "max_temp": round(max(temps_max), 1),
                    "min_temp": round(min(temps_min), 1),
                    "rain_days": rain_days,
                    "total_days": len(temps_max),
                    "success": True
                }
    except requests.RequestException as e:
        print(f"Forecast API error: {e}")
    
    return {"success": False}


def calc_weather_score(temp: float, preferred: Tuple[int, int]) -> float:
    """
    Score 0-100 based on temperature match.
    100 if within range, decreases as temp moves away from preferred range.
    """
    if temp is None:
        return 50.0
    
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


def enrich_destinations_with_weather(destinations: List[Dict], preferred: Tuple[int, int], show_progress: bool = True) -> List[Dict]:
    """Add current weather data to destinations."""
    if "weather_cache" not in st.session_state:
        st.session_state["weather_cache"] = {}
    cache = st.session_state["weather_cache"]
    
    if show_progress:
        progress = st.progress(0, text="Loading weather...")
    
    enriched = []
    success_count = 0
    
    for i, dest in enumerate(destinations):
        d = dest.copy()
        dest_id = dest.get("id")
        
        if dest_id in cache:
            d['weather_score'] = cache[dest_id]['score']
            d['current_temp'] = cache[dest_id].get('temp')
            if d['current_temp'] is not None:
                success_count += 1
        else:
            lat = dest.get('latitude')
            lon = dest.get('longitude')
            
            if lat is not None and lon is not None:
                weather = get_weather(lat, lon)
                
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
        
        if show_progress:
            progress.progress((i + 1) / len(destinations), text=f"Weather: {i+1}/{len(destinations)}")
    
    if show_progress:
        progress.empty()
        if success_count < len(destinations):
            st.caption(f"☁️ Weather loaded for {success_count}/{len(destinations)} destinations")
    
    return enriched


def enrich_destinations_with_forecast(destinations: List[Dict], preferred: Tuple[int, int], start: str, end: str, show_progress: bool = True) -> List[Dict]:
    """Add forecast data to destinations for specific travel dates."""
    cache_key = f"forecast_{start}_{end}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}
    cache = st.session_state[cache_key]
    
    if show_progress:
        progress = st.progress(0, text="Loading forecasts...")
    
    enriched = []
    success_count = 0
    
    for i, dest in enumerate(destinations):
        d = dest.copy()
        dest_id = dest.get("id")
        
        if dest_id in cache:
            cached = cache[dest_id]
            d['weather_score'] = cached['score']
            d['forecast_temp'] = cached.get('avg_temp')
            d['rain_days'] = cached.get('rain_days', 0)
            if d['forecast_temp'] is not None:
                success_count += 1
        else:
            lat = dest.get('latitude')
            lon = dest.get('longitude')
            
            if lat is not None and lon is not None:
                forecast = get_forecast(lat, lon, start, end)
                
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
        
        if show_progress:
            progress.progress((i + 1) / len(destinations), text=f"Forecast: {i+1}/{len(destinations)}")
    
    if show_progress:
        progress.empty()
        if success_count < len(destinations):
            st.caption(f"🌤️ Forecast loaded for {success_count}/{len(destinations)} destinations")
    
    return enriched