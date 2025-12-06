"""
Session Manager Module - Handles saving, exporting, and sharing user sessions.
"""

import json
import base64
import zlib
from datetime import datetime
from typing import Dict, Any, Optional, List


def export_session(
    ranked_results: Optional[List[Dict[str, Any]]] = None,
    session_state: Optional[Dict[str, Any]] = None
) -> str:
    """
    Exports the current session data to JSON format.
    """
    import streamlit as st
    
    state = session_state if session_state else st.session_state
    
    export_data = {
        "export_info": {
            "timestamp": datetime.now().isoformat(),
            "version": "2.0",
            "application": "Travel Matching Recommender",
        },
        "user_settings": {
            "total_budget": state.get("total_budget"),
            "trip_days": state.get("trip_days"),
            "num_travelers": state.get("num_travelers", 1),
            "travel_style": state.get("travel_style", "balanced"),
            "temperature_preference": state.get("temp_preference", (15, 28)),
            "weather_enabled": state.get("use_weather", True),
        },
        "matching_process": {
            "rounds_completed": state.get("round", 0),
            "chosen_destinations": [],
        },
        "results": {
            "top_recommendations": [],
        },
    }
    
    for i, dest in enumerate(state.get("chosen", []), 1):
        export_data["matching_process"]["chosen_destinations"].append({
            "round": i,
            "city": dest.get("city"),
            "country": dest.get("country"),
            "daily_budget": dest.get("avg_budget_per_day"),
        })
    
    if ranked_results:
        for i, dest in enumerate(ranked_results[:5]):
            export_data["results"]["top_recommendations"].append({
                "rank": i + 1,
                "city": dest.get("city"),
                "country": dest.get("country"),
                "combined_score": dest.get("combined_score"),
                "match_score": dest.get("match_score"),
                "weather_score": dest.get("weather_score"),
                "daily_budget": dest.get("avg_budget_per_day"),
                "flight_price": dest.get("flight_price"),
            })
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def get_export_filename() -> str:
    """Generates a timestamped filename for the export."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    return f"travel_match_{timestamp}.json"


# =============================================================================
# SHARE FUNCTIONALITY
# =============================================================================

def create_share_data(
    ranked_results: List[Dict[str, Any]],
    session_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates a minimal data structure for sharing.
    Only includes essential data to keep the URL short.
    """
    import streamlit as st
    
    state = session_state if session_state else st.session_state
    
    # Only include top 3 results with minimal data
    top_results = []
    for dest in ranked_results[:3]:
        top_results.append({
            "c": dest.get("city", ""),
            "co": dest.get("country", ""),
            "s": dest.get("combined_score", 0),
            "f": dest.get("flight_price", 0),
            "d": dest.get("avg_budget_per_day", 0),
        })
    
    share_data = {
        "v": 1,
        "b": state.get("total_budget", 0),
        "t": state.get("trip_days", 7),
        "n": state.get("num_travelers", 1),
        "st": state.get("travel_style", "balanced"),
        "r": top_results,
    }
    
    return share_data


def encode_share_data(share_data: Dict[str, Any]) -> str:
    """
    Encodes share data to a URL-safe string.
    Uses compression to keep URLs short.
    """
    try:
        json_str = json.dumps(share_data, separators=(',', ':'))
        compressed = zlib.compress(json_str.encode('utf-8'), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
        return encoded.rstrip('=')
    except Exception:
        return ""


def decode_share_data(encoded: str) -> Optional[Dict[str, Any]]:
    """
    Decodes a shared URL parameter back to data.
    """
    try:
        padding = 4 - (len(encoded) % 4)
        if padding != 4:
            encoded += '=' * padding
        
        compressed = base64.urlsafe_b64decode(encoded.encode('utf-8'))
        json_str = zlib.decompress(compressed).decode('utf-8')
        return json.loads(json_str)
    except Exception:
        return None


def generate_share_url(
    ranked_results: List[Dict[str, Any]],
    base_url: str = ""
) -> str:
    """
    Generates a shareable URL with encoded results.
    """
    share_data = create_share_data(ranked_results)
    encoded = encode_share_data(share_data)
    
    if not encoded:
        return ""
    
    if not base_url:
        base_url = "https://computerscience91.streamlit.app/"
    
    return f"{base_url}?share={encoded}"


def parse_shared_results(query_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parses shared results from URL query parameters.
    """
    share_param = query_params.get("share")
    
    if not share_param:
        return None
    
    if isinstance(share_param, list):
        share_param = share_param[0]
    
    return decode_share_data(share_param)


def format_session_summary(session_state: Dict[str, Any]) -> str:
    """Creates a human-readable summary of the session."""
    budget = session_state.get("total_budget", 0)
    days = session_state.get("trip_days", 0)
    travelers = session_state.get("num_travelers", 1)
    style = session_state.get("travel_style", "balanced")
    rounds = session_state.get("round", 0)
    
    summary = f"""
    Travel Matching Session Summary
    ================================
    Budget: CHF {budget}
    Travelers: {travelers}
    Duration: {days} days
    Travel Style: {style}
    Rounds Completed: {rounds}
    """
    
    return summary.strip()