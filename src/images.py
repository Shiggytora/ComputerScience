"""
Image Module - Handles destination images using Unsplash API with local caching.
"""

import os
import json
import requests
from pathlib import Path

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

# Cache configuration
CACHE_DIR = Path("data/image_cache")
CACHE_FILE = CACHE_DIR / "image_urls.json"

# Fallback image if API fails
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop"


def _load_cache() -> dict:
    """Loads the image URL cache from disk."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    """Saves the image URL cache to disk."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _get_cache_key(city: str, country: str, size: str) -> str:
    """Creates a unique cache key for a destination."""
    return f"{city}|{country}|{size}".lower()


def get_city_image_url(city: str, country: str = "", size: str = "800x500") -> str:
    """
    Returns an Unsplash image URL for a destination.
    Checks local cache first, then fetches from API if not cached.
    
    Args:
        city: City name
        country: Country name (optional)
        size: Image size in format "WIDTHxHEIGHT"
        
    Returns:
        URL string for the destination image
    """
    # Create cache key
    cache_key = _get_cache_key(city, country, size)
    
    # Check cache first
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key]
    
    # No cache hit - fetch from API
    if not UNSPLASH_ACCESS_KEY:
        return FALLBACK_IMAGE
    
    try:
        width, height = size.split("x")
    except ValueError:
        width, height = "800", "500"
    
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
                image_url = f"{raw_url}&w={width}&h={height}&fit=crop&q=80"
                
                # Save to cache
                cache[cache_key] = image_url
                _save_cache(cache)
                
                return image_url
        
        return FALLBACK_IMAGE
        
    except Exception:
        return FALLBACK_IMAGE


def get_destination_image(destination: dict, size: str = "800x500") -> str:
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


def get_cache_stats() -> dict:
    """Returns statistics about the image cache."""
    cache = _load_cache()
    return {
        "total_cached": len(cache),
        "cache_file": str(CACHE_FILE),
    }


def clear_cache() -> None:
    """Clears the entire image cache."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
    except Exception:
        pass