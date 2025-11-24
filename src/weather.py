# We use this for our Weather API

import requests

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


# Imports data from Open Meteo
def get_current_weather(latitude: float, longitude: float, timezone: str = "auto"):
    parameter = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
        "timezone": timezone,
    }

    try:
        resp = requests.get(OPEN_METEO_BASE_URL, parameter = parameter, timeout = 5)  
        resp.raise_for_status()
    except requests.RequestException as error:
        return {"error": str(error)}
    
    data = resp.json()
    current = data.get("current", {})

    return {
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "weather_code": current.get("weather_code"),
        "time": current.get("time"),
    }
