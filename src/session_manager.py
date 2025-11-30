"""
Session Manager Module - Handles saving and exporting user sessions.

This module provides functionality to export the current session state
including user preferences, choices, and results to JSON format.
Users can download their results for future reference. 
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List


def export_session(
    ranked_results: Optional[List[Dict[str, Any]]] = None,
    session_state: Optional[Dict[str, Any]] = None
) -> str:
    """
    Exports the current session data to JSON format.
    
    Creates a comprehensive export of the user's travel matching session
    including their preferences, selections, and final recommendations.
    
    Args:
        ranked_results: List of ranked destination results
        session_state: Streamlit session state dictionary
        
    Returns:
        JSON string containing all session data
        
    Example:
        >>> json_data = export_session(ranked, st.session_state)
        >>> with open("results.json", "w") as f:
        ...     f. write(json_data)
    """
    import streamlit as st
    
    # Use provided session_state or get from streamlit
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
    
    # Add chosen destinations with details
    for i, dest in enumerate(state. get("chosen", []), 1):
        export_data["matching_process"]["chosen_destinations"].append({
            "round": i,
            "city": dest.get("city"),
            "country": dest.get("country"),
            "rating": dest.get("tourist_rating"),
            "daily_budget": dest. get("avg_budget_per_day"),
        })
    
    # Add top results if available
    if ranked_results:
        for i, dest in enumerate(ranked_results[:5]):
            export_data["results"]["top_recommendations"].append({
                "rank": i + 1,
                "city": dest.get("city"),
                "country": dest.get("country"),
                "combined_score": dest.get("combined_score"),
                "match_score": dest.get("match_score"),
                "weather_score": dest.get("weather_score"),
                "daily_budget": dest. get("avg_budget_per_day"),
            })
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def get_export_filename() -> str:
    """
    Generates a timestamped filename for the export.
    
    Returns:
        String filename in format: travel_match_YYYYMMDD_HHMM.json
    """
    timestamp = datetime.now(). strftime('%Y%m%d_%H%M')
    return f"travel_match_{timestamp}.json"


def format_session_summary(session_state: Dict[str, Any]) -> str:
    """
    Creates a human-readable summary of the session.
    
    Args:
        session_state: Streamlit session state dictionary
        
    Returns:
        Formatted string summary
    """
    budget = session_state. get("total_budget", 0)
    days = session_state.get("trip_days", 0)
    style = session_state.get("travel_style", "balanced")
    rounds = session_state.get("round", 0)
    
    summary = f"""
    Travel Matching Session Summary
    ================================
    Budget: CHF {budget}
    Duration: {days} days
    Travel Style: {style}
    Rounds Completed: {rounds}
    """
    
    return summary.strip()