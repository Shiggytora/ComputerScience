"""
Attractions Module - Fetches points of interest from OpenTripMap API. 

This module provides functionality to fetch and display tourist attractions,
landmarks, and points of interest for any destination. 

API Documentation: https://dev.opentripmap.org/product

Part of Requirement #2: API Integration
"""

import requests
from typing import List, Dict, Any, Optional
import streamlit as st

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get your free API key at: https://dev.opentripmap.org/product
# After registration, replace this with your actual key
OPENTRIPMAP_API_KEY = "5ae2e3f221c38a28845f05b69fd0f5991a57222095b70343c72533ef"

OPENTRIPMAP_BASE_URL = "https://api.opentripmap.com/0.1/en/places"
API_TIMEOUT = 10

# Category mappings for display
CATEGORY_CONFIG = {
    "cultural": {"emoji": "🏛️", "name": "Cultural"},
    "historic": {"emoji": "🏰", "name": "Historic"},
    "natural": {"emoji": "🌿", "name": "Nature"},
    "religion": {"emoji": "⛪", "name": "Religious"},
    "architecture": {"emoji": "🏛️", "name": "Architecture"},
    "museums": {"emoji": "🖼️", "name": "Museums"},
    "theatres_and_entertainments": {"emoji": "🎭", "name": "Entertainment"},
    "amusements": {"emoji": "🎢", "name": "Amusements"},
    "sport": {"emoji": "⚽", "name": "Sports"},
    "beaches": {"emoji": "🏖️", "name": "Beaches"},
    "gardens_and_parks": {"emoji": "🌳", "name": "Parks & Gardens"},
    "water": {"emoji": "💧", "name": "Water"},
    "geological_formations": {"emoji": "🏔️", "name": "Geological"},
    "foods": {"emoji": "🍽️", "name": "Food & Drink"},
    "shops": {"emoji": "🛍️", "name": "Shopping"},
    "transport": {"emoji": "🚂", "name": "Transport"},
    "other": {"emoji": "📍", "name": "Other"},
}


# =============================================================================
# API FUNCTIONS
# =============================================================================

def get_attractions_by_radius(
    latitude: float,
    longitude: float,
    radius: int = 10000,
    limit: int = 15,
    min_rating: int = 2
) -> List[Dict[str, Any]]:
    """
    Fetches attractions within a radius of given coordinates. 
    
    Args:
        latitude: Geographic latitude
        longitude: Geographic longitude
        radius: Search radius in meters (default: 10km)
        limit: Maximum number of results
        min_rating: Minimum rating filter (1-3, where 3 is highest)
        
    Returns:
        List of attraction dictionaries with basic info
        
    Example:
        >>> attractions = get_attractions_by_radius(41.3851, 2.1734)  # Barcelona
        >>> for a in attractions:
        ...     print(a['name'])
    """
    try:
        response = requests.get(
            f"{OPENTRIPMAP_BASE_URL}/radius",
            params={
                "radius": radius,
                "lon": longitude,
                "lat": latitude,
                "rate": min_rating,
                "format": "json",
                "limit": limit,
                "apikey": OPENTRIPMAP_API_KEY,
            },
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            attractions = response.json()
            return attractions if isinstance(attractions, list) else []
        else:
            print(f"OpenTripMap API error: {response.status_code}")
            return []
            
    except requests.Timeout:
        print("OpenTripMap API timeout")
        return []
    except requests.RequestException as e:
        print(f"OpenTripMap API error: {e}")
        return []


def get_attraction_details(xid: str) -> Optional[Dict[str, Any]]:
    """
    Fetches detailed information for a specific attraction. 
    
    Args:
        xid: Unique identifier of the attraction
        
    Returns:
        Dictionary with detailed attraction info including:
        - name: Attraction name
        - kinds: Categories (comma-separated)
        - wikipedia_extracts: Description from Wikipedia
        - preview: Image preview info
        - point: Coordinates
        - address: Location details
    """
    if not xid:
        return None
    
    try:
        response = requests.get(
            f"{OPENTRIPMAP_BASE_URL}/xid/{xid}",
            params={"apikey": OPENTRIPMAP_API_KEY},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
            
    except Exception as e:
        print(f"Error fetching attraction details: {e}")
    
    return None


def get_attractions_for_destination(
    destination: Dict[str, Any],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetches and enriches attractions for a destination.
    
    This function combines radius search with detail fetching
    to provide complete attraction information.
    
    Args:
        destination: Destination dictionary with latitude/longitude
        limit: Maximum number of attractions to return
        
    Returns:
        List of enriched attraction dictionaries
    """
    lat = destination.get('latitude')
    lon = destination.get('longitude')
    city = destination.get('city', 'Unknown')
    
    if lat is None or lon is None:
        return []
    
    # Check cache first
    cache_key = f"attractions_{city}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # Fetch basic attraction list
    basic_attractions = get_attractions_by_radius(lat, lon, limit=limit * 2)
    
    if not basic_attractions:
        return []
    
    # Enrich with details (only for top results)
    enriched = []
    
    for attr in basic_attractions:
        if len(enriched) >= limit:
            break
        
        xid = attr.get('xid')
        name = attr.get('name', '').strip()
        
        # Skip unnamed attractions
        if not name or name == "":
            continue
        
        # Get detailed info
        details = get_attraction_details(xid)
        
        if details:
            # Parse categories
            kinds = details.get('kinds', '').split(',')
            primary_kind = kinds[0] if kinds else 'other'
            
            # Get category config
            category_info = CATEGORY_CONFIG.get(
                primary_kind, 
                CATEGORY_CONFIG.get('other')
            )
            
            # Extract Wikipedia description
            wiki_extracts = details.get('wikipedia_extracts', {})
            description = wiki_extracts.get('text', '') if isinstance(wiki_extracts, dict) else ''
            
            # Get image if available
            preview = details.get('preview', {})
            image_url = preview.get('source') if isinstance(preview, dict) else None
            
            enriched.append({
                'xid': xid,
                'name': details.get('name', name),
                'kinds': kinds,
                'primary_kind': primary_kind,
                'category_emoji': category_info['emoji'],
                'category_name': category_info['name'],
                'description': description[:300] + '...' if len(description) > 300 else description,
                'image_url': image_url,
                'rating': attr.get('rate', 0),
                'latitude': details.get('point', {}).get('lat'),
                'longitude': details.get('point', {}).get('lon'),
                'address': details.get('address', {}),
                'wikipedia': details.get('wikipedia'),
            })
    
    # Cache results
    st.session_state[cache_key] = enriched
    
    return enriched


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def render_attractions_section(destination: Dict[str, Any], num_attractions: int = 8):
    """
    Renders the attractions section in Streamlit.
    
    Args:
        destination: Destination dictionary
        num_attractions: Number of attractions to display
    """
    city = destination.get('city', 'Unknown')
    country = destination.get('country', '')
    
    st.subheader(f"🎯 Top Attractions in {city}")
    
    with st.spinner("Loading attractions..."):
        attractions = get_attractions_for_destination(destination, limit=num_attractions)
    
    if not attractions:
        st.info(f"No attraction data available for {city}. Try a larger city or check your internet connection.")
        return
    
    st.caption(f"Found {len(attractions)} top-rated attractions")
    
    # Display in a grid
    cols_per_row = 2
    
    for i in range(0, len(attractions), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(attractions):
                attr = attractions[i + j]
                
                with col:
                    render_attraction_card(attr)


def render_attraction_card(attraction: Dict[str, Any]):
    """
    Renders a single attraction card.
    
    Args:
        attraction: Enriched attraction dictionary
    """
    with st.container():
        # Image or placeholder
        if attraction.get('image_url'):
            try:
                st.image(attraction['image_url'], use_container_width=True)
            except:
                pass
        
        # Title with emoji
        emoji = attraction.get('category_emoji', '📍')
        name = attraction.get('name', 'Unknown')
        st.markdown(f"**{emoji} {name}**")
        
        # Category and rating
        category = attraction.get('category_name', 'Attraction')
        rating = attraction.get('rating', 0)
        rating_stars = "⭐" * rating if rating > 0 else ""
        
        st.caption(f"{category} {rating_stars}")
        
        # Description
        description = attraction.get('description', '')
        if description:
            st.write(description[:150] + "..." if len(description) > 150 else description)
        
        # Wikipedia link
        wiki_url = attraction.get('wikipedia')
        if wiki_url:
            st.markdown(f"[📖 Learn more]({wiki_url})")
        
        st.divider()


def render_attractions_compact(destination: Dict[str, Any], num_attractions: int = 5):
    """
    Renders a compact list of attractions (for use in smaller spaces).
    
    Args:
        destination: Destination dictionary
        num_attractions: Number to display
    """
    city = destination.get('city', 'Unknown')
    
    attractions = get_attractions_for_destination(destination, limit=num_attractions)
    
    if not attractions:
        st.caption("No attraction data available")
        return
    
    st.write(f"**🎯 Top {len(attractions)} things to do in {city}:**")
    
    for i, attr in enumerate(attractions, 1):
        emoji = attr.get('category_emoji', '📍')
        name = attr.get('name', 'Unknown')
        category = attr.get('category_name', '')
        
        st.write(f"{i}.{emoji} **{name}** ({category})")


def get_attractions_summary(destination: Dict[str, Any]) -> str:
    """
    Returns a text summary of top attractions for a destination.
    
    Useful for including in exports or text-based displays.
    
    Args:
        destination: Destination dictionary
        
    Returns:
        Formatted string with attraction names
    """
    attractions = get_attractions_for_destination(destination, limit=5)
    
    if not attractions:
        return "No attraction data available"
    
    names = [f"{a['category_emoji']} {a['name']}" for a in attractions]
    return ", ".join(names)