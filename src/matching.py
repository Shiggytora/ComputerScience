"""
Matching Module - Core recommendation engine for travel destinations.

This module implements the matching algorithm that learns user preferences
from their choices and calculates compatibility scores for all destinations.
It uses weighted feature similarity to rank destinations. 

Part of Requirement #5: Machine Learning - Preference learning and similarity scoring.
Part of Requirement #4: User Interaction - Interactive matching process.
"""

import streamlit as st
import requests
import random
from amadeus import Client, ResponseError
from typing import List, Dict, Any, Optional
from src.data import get_destinations_by_budget, get_all_destinations
from src.config import get_secret

# API Configuration
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Features used for matching algorithm
NUMERIC_FEATURES = [
    "city_size",
    "tourist_rating",
    "tourist_volume_base",
    "is_coastal",
    "climate_category",
    "cost_index",
]

# Default feature weights for balanced matching
FEATURE_WEIGHTS = {
    "city_size": 1.0,
    "tourist_rating": 2.0,
    "tourist_volume_base": 1.0,
    "is_coastal": 1.5,
    "climate_category": 1.5,
    "cost_index": 1.0,
}

# Travel style configurations with custom weights
# Each style adjusts feature importance to match user preferences
# Negative weights indicate inverse preference (e.g., lower is better)
TRAVEL_STYLES = {
    "beach_lover": {
        "name": "🏖️ Beach Vacation",
        "description": "Sun, sea, and relaxation",
        "weights": {
            "is_coastal": 3.0,
            "climate_category": 2.5,
            "tourist_rating": 1.5,
            "city_size": 0.5,
            "tourist_volume_base": 1.0,
            "cost_index": 1.0,
        }
    },
    "city_explorer": {
        "name": "🏙️ City Trip",
        "description": "Culture, history, and urban life",
        "weights": {
            "city_size": 3.0,
            "tourist_rating": 2.5,
            "is_coastal": 0.5,
            "climate_category": 1.0,
            "tourist_volume_base": 1.5,
            "cost_index": 1.0,
        }
    },
    "budget_traveler": {
        "name": "💰 Budget Trip",
        "description": "Maximum experience, minimum cost",
        "weights": {
            "cost_index": -3.0,  # Negative = prefer lower costs
            "tourist_rating": 2.0,
            "city_size": 1.0,
            "is_coastal": 1.0,
            "climate_category": 1.5,
            "tourist_volume_base": 0.5,
        }
    },
    "off_the_beaten_path": {
        "name": "🗺️ Hidden Gem",
        "description": "Off the tourist trail",
        "weights": {
            "tourist_volume_base": -2.5,  # Prefer fewer tourists
            "tourist_rating": 1.5,
            "city_size": -1.0,  # Prefer smaller places
            "is_coastal": 1.0,
            "climate_category": 1.5,
            "cost_index": 1.0,
        }
    },
    "luxury": {
        "name": "💎 Luxury",
        "description": "Premium experiences and comfort",
        "weights": {
            "tourist_rating": 3.0,
            "cost_index": 2.0,  # Higher cost = higher quality
            "city_size": 1.5,
            "is_coastal": 1.5,
            "climate_category": 1.5,
            "tourist_volume_base": 1.0,
        }
    },
    "adventure": {
        "name": "🏔️ Adventure",
        "description": "Active and nature-focused",
        "weights": {
            "climate_category": 2.0,
            "is_coastal": 1.5,
            "tourist_volume_base": -1.0,
            "city_size": -0.5,
            "tourist_rating": 1.5,
            "cost_index": 1.0,
        }
    },
    "balanced": {
        "name": "⚖️ Balanced",
        "description": "A bit of everything",
        "weights": FEATURE_WEIGHTS. copy(),
    }
}


def filter_by_budget(total_budget: float, trip_days: int) -> List[Dict[str, Any]]:
    """
    Filters destinations based on user's budget. 
    
    Retrieves destinations from the database that match the user's
    daily budget (total_budget / trip_days). 
    
    Args:
        total_budget: Total trip budget in CHF
        trip_days: Number of days for the trip
        
    Returns:
        List of matching destination dictionaries
    """
    budget_matches = get_destinations_by_budget(total_budget, trip_days)
    if budget_matches:
        return budget_matches
    # Fallback to all destinations if no matches
    return get_all_destinations()


def test_locations(
    budget_matches: List[Dict[str, Any]], 
    id_used: List[int], 
    x: int = 3
) -> List[Dict[str, Any]]:
    """
    Selects random destinations for a matching round.
    
    Randomly samples x destinations from the available pool,
    excluding any that have already been shown to the user. 
    
    Args:
        budget_matches: List of all matching destinations
        id_used: List of destination IDs already shown
        x: Number of destinations to return (default: 3)
        
    Returns:
        List of x random destinations
    """
    remaining = [y for y in budget_matches if y["id"] not in id_used]
    if len(remaining) <= x:
        return remaining
    return random. sample(remaining, x)


def get_travel_style_weights(style: str) -> Dict[str, float]:
    """
    Returns the feature weights for a specific travel style.
    
    Args:
        style: Travel style key (e.g., "beach_lover", "city_explorer")
        
    Returns:
        Dictionary of feature weights
    """
    if style in TRAVEL_STYLES:
        return TRAVEL_STYLES[style]["weights"]
    return FEATURE_WEIGHTS


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    Normalizes a value to the range 0-1. 
    
    Uses min-max normalization to scale values for fair comparison
    between different features.
    
    Args:
        value: The value to normalize
        min_val: Minimum value in the dataset
        max_val: Maximum value in the dataset
        
    Returns:
        Normalized value between 0 and 1
    """
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def calculate_feature_ranges(destinations: List[Dict[str, Any]]) -> Dict[str, tuple]:
    """
    Calculates min/max ranges for each feature across all destinations.
    
    These ranges are used for normalization in the scoring algorithm.
    
    Args:
        destinations: List of destination dictionaries
        
    Returns:
        Dictionary mapping feature names to (min, max) tuples
    """
    ranges = {}
    for feature in NUMERIC_FEATURES:
        values = [d[feature] for d in destinations if feature in d]
        if values:
            ranges[feature] = (min(values), max(values))
        else:
            ranges[feature] = (0, 1)
    return ranges


def preference_vector(chosen: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates the user's preference vector from their choices.
    
    This is the core of the learning algorithm: it computes the average
    value for each feature across all destinations chosen by the user. 
    This represents what the user typically prefers.
    
    Args:
        chosen: List of destinations chosen by the user
        
    Returns:
        Dictionary mapping features to average preferred values
        
    Example:
        >>> prefs = preference_vector(user_choices)
        >>> print(prefs["is_coastal"])  # e.g., 0.8 if user prefers coastal
    """
    if not chosen:
        return {}
    
    preference = {}
    for feature in NUMERIC_FEATURES:
        values = [dest[feature] for dest in chosen if feature in dest]
        if values:
            preference[feature] = sum(values) / len(values)
    
    return preference


def calculate_match_score(
    destination: Dict[str, Any], 
    preference: Dict[str, float],
    feature_ranges: Dict[str, tuple],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculates match score between a destination and user preferences.
    
    This is the main ML algorithm: it computes a weighted similarity score
    between a destination's features and the learned user preferences.
    
    Algorithm:
    1.  Normalize both destination and preference values to 0-1
    2. Calculate similarity as 1 - |normalized_dest - normalized_pref|
    3. Apply weights (negative weights invert the similarity)
    4.  Return weighted average as percentage (0-100)
    
    Args:
        destination: Destination dictionary with features
        preference: User's preference vector
        feature_ranges: Min/max ranges for normalization
        weights: Feature weights (optional, uses travel style weights)
        
    Returns:
        Match score as percentage (0-100)
    """
    if not preference:
        return 50.0
    
    if weights is None:
        weights = FEATURE_WEIGHTS
    
    total_weighted_similarity = 0.0
    total_weight = 0.0
    
    for feature in NUMERIC_FEATURES:
        if feature not in preference or feature not in destination:
            continue
        
        min_val, max_val = feature_ranges. get(feature, (0, 1))
        
        # Normalize values for fair comparison
        norm_dest = normalize_value(destination[feature], min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        # Calculate similarity (1 = identical, 0 = opposite)
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        weight = weights.get(feature, 1.0)
        abs_weight = abs(weight)
        
        # Negative weight = inverse preference (e.g., lower cost is better)
        if weight < 0:
            similarity = 1.0 - similarity
        
        total_weighted_similarity += similarity * abs_weight
        total_weight += abs_weight
    
    if total_weight == 0:
        return 50.0
    
    # Convert to percentage
    score = (total_weighted_similarity / total_weight) * 100
    return round(score, 1)


def calculate_combined_score(
    destination: Dict[str, Any],
    match_score: float,
    weather_weight: float = 0.2
) -> float:
    """
    Combines match score with weather score for final ranking.
    
    Args:
        destination: Destination with weather_score field
        match_score: Calculated match score
        weather_weight: Weight for weather (0-1), rest goes to match
        
    Returns:
        Combined score as percentage (0-100)
    """
    weather_score = destination. get('weather_score', 50.0)
    combined = (match_score * (1 - weather_weight)) + (weather_score * weather_weight)
    return round(combined, 1)


def scoring_destinations(
    destination: Dict[str, Any], 
    preference: Dict[str, float]
) -> float:
    """
    Legacy scoring function using distance-based approach.
    
    Lower score = better match (inverse of similarity approach). 
    Kept for backward compatibility. 
    """
    if not preference:
        return 0
    
    score = 0
    for feature in NUMERIC_FEATURES:
        if feature in preference and feature in destination:
            weight = FEATURE_WEIGHTS. get(feature, 1.0)
            score += abs(destination[feature] - preference[feature]) * weight
    
    return score


def ranking_destinations(
    budget_matches: List[Dict[str, Any]], 
    chosen: List[Dict[str, Any]],
    travel_style: str = "balanced",
    use_weather: bool = True,
    weather_weight: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Ranks all destinations based on user preferences.
    
    This is the main recommendation function that:
    1.  Learns user preferences from their choices
    2.  Applies travel style weights
    3.  Calculates match scores for all destinations
    4.  Optionally incorporates weather data
    5. Returns sorted list with best matches first
    
    Args:
        budget_matches: All budget-matching destinations
        chosen: Destinations chosen by user in matching rounds
        travel_style: Selected travel style for weight adjustment
        use_weather: Whether to include weather in scoring
        weather_weight: How much weather affects final score (0-1)
        
    Returns:
        Sorted list of destinations with scores added
    """
    # Learn user preferences from their choices
    preference = preference_vector(chosen)
    feature_ranges = calculate_feature_ranges(budget_matches)
    weights = get_travel_style_weights(travel_style)
    
    scored_destinations = []
    for dest in budget_matches:
        dest_copy = dest.copy()
        
        # Calculate match score using ML algorithm
        match_score = calculate_match_score(
            dest_copy, preference, feature_ranges, weights
        )
        dest_copy['match_score'] = match_score
        
        # Get weather score (already enriched or default)
        weather_score = dest_copy.get('weather_score', 50.0)
        dest_copy['weather_score'] = round(weather_score, 1)
        
        # Calculate combined score
        if use_weather:
            dest_copy['combined_score'] = calculate_combined_score(
                dest_copy, match_score, weather_weight
            )
        else:
            dest_copy['combined_score'] = match_score
        
        # Legacy score for compatibility
        dest_copy['distance_score'] = scoring_destinations(dest_copy, preference)
        
        scored_destinations.append(dest_copy)
    
    # Sort by combined score (higher = better)
    scored_destinations.sort(key=lambda d: d['combined_score'], reverse=True)
    
    return scored_destinations


def get_match_breakdown(
    destination: Dict[str, Any],
    preference: Dict[str, float],
    feature_ranges: Dict[str, tuple],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Generates detailed breakdown of match score by feature.
    
    Useful for explaining to users why a destination was recommended.
    
    Args:
        destination: The destination to analyze
        preference: User's preference vector
        feature_ranges: Normalization ranges
        weights: Feature weights used
        
    Returns:
        Dictionary with per-feature similarity details
    """
    if weights is None:
        weights = FEATURE_WEIGHTS
    
    breakdown = {}
    
    for feature in NUMERIC_FEATURES:
        if feature not in preference or feature not in destination:
            continue
        
        min_val, max_val = feature_ranges.get(feature, (0, 1))
        
        norm_dest = normalize_value(destination[feature], min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        weight = weights.get(feature, 1.0)
        
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        # Invert display for negative weights
        if weight < 0:
            display_similarity = 1.0 - similarity
        else:
            display_similarity = similarity
        
        breakdown[feature] = {
            'destination_value': destination[feature],
            'preference_value': round(preference[feature], 2),
            'similarity': round(display_similarity * 100, 1),
            'weight': weight,
            'is_inverse': weight < 0,
        }
    
    return breakdown


def test_matching():
    """Test function to verify module is loaded correctly."""
    return "Test Matching successful"