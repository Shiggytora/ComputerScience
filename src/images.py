"""
Image Module - Handles destination images using Unsplash.
"""


def get_city_image_url(city: str, country: str = "", size: str = "800x400") -> str:
    """
    Returns an Unsplash image URL for a destination.
    
    Args:
        city: City name
        country: Country name (optional, improves search results)
        size: Image size in format "WIDTHxHEIGHT" (default: 800x400)
        
    Returns:
        URL string for the destination image
    """
    # Parse size
    try:
        width, height = size.split("x")
    except ValueError:
        width, height = "800", "400"
    
    # Build search query
    query_parts = [city]
    if country:
        query_parts.append(country)
    query_parts.append("travel")
    
    query = ",".join(query_parts).replace(" ", "-")
    
    return f"https://source.unsplash.com/{width}x{height}/?{query}"


def get_destination_image(destination: dict, size: str = "800x400") -> str:
    """
    Returns an image URL for a destination dictionary.
    
    Args:
        destination: Destination dict with 'city' and 'country' keys
        size: Image size
        
    Returns:
        URL string for the destination image
    """
    city = destination.get("city", "travel")
    country = destination.get("country", "")
    
    return get_city_image_url(city, country, size)


def get_thumbnail_url(city: str, country: str = "") -> str:
    """Returns a small thumbnail image (400x250)."""
    return get_city_image_url(city, country, "400x250")


def get_hero_image_url(city: str, country: str = "") -> str:
    """Returns a large hero image (1200x600)."""
    return get_city_image_url(city, country, "1200x600")