"""
Image handling using Unsplash API.
"""

import os
import requests

# Try Streamlit secrets first, then .env (for accessing the Unsplash API)
try:
    import streamlit as st
    UNSPLASH_ACCESS_KEY = st.secrets.get("UNSPLASH_ACCESS_KEY", None)
except Exception:
    UNSPLASH_ACCESS_KEY = None

# Fallback to .env for local dev if not found in Streamlit secrets
if not UNSPLASH_ACCESS_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# Fallback image if API fails
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop"


# Main function to get city image URL
def get_city_image_url(city: str, country: str = "", size: str = "800x500") -> str:
    
    # No API key = use fallback
    if not UNSPLASH_ACCESS_KEY:
        return FALLBACK_IMAGE
    
    try:
        width, height = size.split("x")
    except ValueError:
        width, height = "800", "500"
    
    # Search on Unsplash
    query = f"{city} {country} travel landmark".strip()
    
    # Make the API request
    try:
        response = requests.get(
            UNSPLASH_API_URL,
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=5
        )
        
        # Check for successful response
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                raw_url = data["results"][0]["urls"]["raw"]
                return f"{raw_url}&w={width}&h={height}&fit=crop&q=80"
        
        return FALLBACK_IMAGE
        
    except Exception:
        return FALLBACK_IMAGE


# Function to get small image of city
def get_thumbnail_url(city: str, country: str = "") -> str:
    return get_city_image_url(city, country, "800x500")

# Function to get large image of city
def get_hero_image_url(city: str, country: str = "") -> str:
    return get_city_image_url(city, country, "1600x900")