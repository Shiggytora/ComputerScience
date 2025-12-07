"""
Image handling using Unsplash API with local caching.
"""

import os
import json
import requests
from pathlib import Path

# Try Streamlit secrets first, then .env
try:
    import streamlit as st
    UNSPLASH_ACCESS_KEY = st.secrets.get("UNSPLASH_ACCESS_KEY", None)
except Exception:
    UNSPLASH_ACCESS_KEY = None

# Fallback to .env for local dev
if not UNSPLASH_ACCESS_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# Cache config
CACHE_DIR = Path("data/image_cache")
CACHE_FILE = CACHE_DIR / "image_urls.json"

# Fallback if API fails
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop"


def _load_cache() -> dict:
    """Load cached image URLs from disk."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    """Save image URLs to disk cache."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _get_cache_key(city: str, country: str, size: str) -> str:
    """Create unique cache key."""
    return f"{city}|{country}|{size}".lower()


def get_city_image_url(city: str, country: str = "", size: str = "800x500") -> str:
    """
    Get Unsplash image URL for a destination.
    Checks cache first, fetches from API if not cached.
    """
    cache_key = _get_cache_key(city, country, size)
    
    # Check cache
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key]
    
    # No API key = use fallback
    if not UNSPLASH_ACCESS_KEY:
        return FALLBACK_IMAGE
    
    try:
        width, height = size.split("x")
    except ValueError:
        width, height = "800", "500"
    
    # Search Unsplash
    query = f"{city} {country} travel landmark".strip()
    
    try:
        response = requests.get(
            UNSPLASH_API_URL,
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                raw_url = data["results"][0]["urls"]["raw"]
                image_url = f"{raw_url}&w={width}&h={height}&fit=crop&q=80"
                
                # Cache it
                cache[cache_key] = image_url
                _save_cache(cache)
                
                return image_url
        
        return FALLBACK_IMAGE
        
    except Exception:
        return FALLBACK_IMAGE


def get_thumbnail_url(city: str, country: str = "") -> str:
    """Get small thumbnail (800x500)."""
    return get_city_image_url(city, country, "800x500")


def get_hero_image_url(city: str, country: str = "") -> str:
    """Get large hero image (1600x900)."""
    return get_city_image_url(city, country, "1600x900")