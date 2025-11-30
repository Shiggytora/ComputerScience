"""
Insights Module - Analyzes user preferences and generates insights. 

This module provides functionality to analyze the destinations chosen by users
during the matching process and extract meaningful patterns and preferences.
These insights help explain the final recommendation to the user. 
"""

from typing import List, Dict, Any


def generate_preference_insights(chosen: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes user selections and generates insights about their preferences.
    
    This function examines the destinations chosen by the user during the
    matching rounds and identifies patterns in their preferences.
    
    Args:
        chosen: List of destination dictionaries selected by the user
        
    Returns:
        Dictionary containing:
        - total_selections: Number of destinations chosen
        - preferences: Average values for each feature
        - patterns: List of identified preference patterns
        
    Example:
        >>> insights = generate_preference_insights(user_choices)
        >>> print(insights["patterns"])
        ["🏖️ You prefer coastal destinations! "]
    """
    if not chosen:
        return {}
    
    insights = {
        "total_selections": len(chosen),
        "preferences": {},
        "patterns": [],
    }
    
    # Calculate average values for key features
    features = ["city_size", "tourist_rating", "is_coastal", "cost_index", "climate_category"]
    
    for feature in features:
        values = [d.get(feature, 0) for d in chosen if feature in d]
        if values:
            avg = sum(values) / len(values)
            insights["preferences"][feature] = round(avg, 2)
    
    # Pattern recognition based on averaged preferences
    # This is a simple form of ML: learning user preferences from their choices
    
    # Coastal preference detection
    coastal_count = sum(1 for d in chosen if d.get("is_coastal", 0) > 0.5)
    if coastal_count > len(chosen) / 2:
        insights["patterns"].append("🏖️ You prefer coastal destinations!")
    
    # City size preference detection
    avg_size = insights["preferences"].get("city_size", 0.5)
    if avg_size > 0.7:
        insights["patterns"].append("🏙️ You like big cities!")
    elif avg_size < 0.3:
        insights["patterns"].append("🏘️ You prefer smaller towns!")
    
    # Budget preference detection
    avg_cost = insights["preferences"]. get("cost_index", 0.5)
    if avg_cost < 0.4:
        insights["patterns"].append("💰 You're budget-conscious!")
    elif avg_cost > 0.7:
        insights["patterns"].append("💎 You prefer premium experiences!")
    
    # Rating preference detection
    avg_rating = insights["preferences"]. get("tourist_rating", 0)
    if avg_rating > 4:
        insights["patterns"].append("⭐ You choose top-rated destinations!")
    
    # Climate preference detection
    avg_climate = insights["preferences"].get("climate_category", 0.5)
    if avg_climate > 0.7:
        insights["patterns"].append("☀️ You love warm climates!")
    elif avg_climate < 0.3:
        insights["patterns"].append("❄️ You prefer cooler regions!")
    
    return insights


def calculate_preference_strength(insights: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates the strength of each preference based on variance from neutral.
    
    This helps identify which features the user cares most strongly about.
    
    Args:
        insights: The insights dictionary from generate_preference_insights
        
    Returns:
        Dictionary mapping feature names to strength scores (0-1)
    """
    if not insights. get("preferences"):
        return {}
    
    strengths = {}
    neutral = 0.5  # Neutral point for normalized features
    
    for feature, value in insights["preferences"]. items():
        # Strength is how far from neutral the preference is
        strength = abs(value - neutral) * 2  # Scale to 0-1
        strengths[feature] = min(1.0, strength)  # Cap at 1.0
    
    return strengths