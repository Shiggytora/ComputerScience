"""
Image Module - Handles destination images using Unsplash API.
"""

import os
import requests
from functools import lru_cache

# Try to load from Streamlit secrets first, then .env
try:
    import streamlit as st
    UNSPLASH_ACCESS_KEY = st.secrets.get("UNSPLASH_ACCESS_KEY")
except Exception:
    UNSPLASH_ACCESS_KEY = None

# Fallback to .env file for local development
if not UNSPLASH_ACCESS_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# Fallback image if API fails
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop"


@lru_cache(maxsize=200)
def get_city_image_url(city: str, country: str = "", size: str = "800x400") -> str:
    """
    Returns an Unsplash image URL for a destination.
    
    Args:
        city: City name
        country: Country name (optional, improves search results)
        size: Image size in format "WIDTHxHEIGHT"
        
    Returns:
        URL string for the destination image
    """
    if not UNSPLASH_ACCESS_KEY:
        return FALLBACK_IMAGE
    
    try:
        width, height = size.split("x")
    except ValueError:
        width, height = "800", "400"
    
    # Build search query
    query = f"{city} {country} travel landmark".strip()
    
    try:
        response = requests.get(
            UNSPLASH_API_URL,
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
            },
            headers={
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                raw_url = data["results"][0]["urls"]["raw"]
                return f"{raw_url}&w={width}&h={height}&fit=crop&q=80"
        
        return FALLBACK_IMAGE
        
    except Exception:
        return FALLBACK_IMAGE


def get_destination_image(destination: dict, size: str = "800x400") -> str:
    """Returns an image URL for a destination dictionary."""
    city = destination.get("city", "travel")
    country = destination.get("country", "")
    return get_city_image_url(city, country, size)


def get_thumbnail_url(city: str, country: str = "") -> str:
    """Returns a small thumbnail image (800x500)."""
    return get_city_image_url(city, country, "800x500")


def get_hero_image_url(city: str, country: str = "") -> str:
    """Returns a large hero image (1600x900)."""
    return get_city_image_url(city, country, "1600x900")