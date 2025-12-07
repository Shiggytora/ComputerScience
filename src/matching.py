"""
Matching Module - Core Recommendation Engine
"""

import random
from typing import List, Dict, Any, Optional
from src.data import get_destinations_by_budget, get_all_destinations

# =============================================================================
# FEATURE CONFIGURATION
# =============================================================================

MATCHING_FEATURES = [
    "safety",
    "english_level",
    "crowds",
    "beach",
    "culture",
    "nature",
    "food",
    "nightlife",
    "adventure",
    "romance",
    "family",
]

INVERTIBLE_FEATURES = ["crowds", "avg_budget_per_day"]

DEFAULT_WEIGHTS = {
    "safety": 2.0,
    "english_level": 1.0,
    "crowds": 1.0,
    "beach": 1.0,
    "culture": 1.0,
    "nature": 1.0,
    "food": 1.0,
    "nightlife": 1.0,
    "adventure": 1.0,
    "romance": 1.0,
    "family": 1.0,
}

NUMERIC_FEATURES = MATCHING_FEATURES
FEATURE_WEIGHTS = DEFAULT_WEIGHTS

# =============================================================================
# TRAVEL STYLES
# =============================================================================

TRAVEL_STYLES = {
    "beach_relaxation": {
        "name": "🏖️ Beach & Relaxation",
        "description": "Sun, sand, and relaxation",
        "weights": {
            "beach": 3.0,
            "safety": 2.0,
            "crowds": -1.5,
            "nature": 1.5,
            "romance": 1.0,
            "food": 1.0,
            "nightlife": 0.5,
            "culture": 0.5,
            "adventure": 0.5,
            "english_level": 1.0,
            "family": 1.0,
        }
    },
    "culture_history": {
        "name": "🏛️ Culture & History",
        "description": "Museums, architecture, and heritage",
        "weights": {
            "culture": 3.0,
            "food": 2.0,
            "safety": 1.5,
            "english_level": 1.5,
            "nature": 1.0,
            "romance": 1.0,
            "crowds": -0.5,
            "beach": 0.5,
            "nightlife": 0.5,
            "adventure": 0.5,
            "family": 1.0,
        }
    },
    "adventure_nature": {
        "name": "🏔️ Adventure & Nature",
        "description": "Hiking, wildlife, and outdoor activities",
        "weights": {
            "adventure": 3.0,
            "nature": 3.0,
            "crowds": -2.0,
            "safety": 2.0,
            "culture": 0.5,
            "beach": 0.5,
            "food": 1.0,
            "english_level": 1.0,
            "nightlife": 0.0,
            "romance": 1.0,
            "family": 1.0,
        }
    },
    "foodie": {
        "name": "🍽️ Food & Culinary",
        "description": "Local cuisine and gastronomic experiences",
        "weights": {
            "food": 3.0,
            "culture": 2.0,
            "safety": 1.5,
            "english_level": 1.0,
            "nightlife": 1.0,
            "crowds": -0.5,
            "beach": 0.5,
            "nature": 1.0,
            "adventure": 0.5,
            "romance": 1.5,
            "family": 1.0,
        }
    },
    "party_nightlife": {
        "name": "🎉 Party & Nightlife",
        "description": "Clubs, bars, and vibrant nightlife",
        "weights": {
            "nightlife": 3.0,
            "beach": 1.5,
            "safety": 1.5,
            "english_level": 2.0,
            "food": 1.5,
            "crowds": 0.5,
            "culture": 0.5,
            "nature": 0.5,
            "adventure": 1.0,
            "romance": 1.0,
            "family": -1.0,
        }
    },
    "romantic_getaway": {
        "name": "💕 Romantic Getaway",
        "description": "Perfect for couples and honeymoons",
        "weights": {
            "romance": 3.0,
            "safety": 2.5,
            "food": 2.0,
            "beach": 2.0,
            "crowds": -2.0,
            "nature": 2.0,
            "culture": 1.5,
            "nightlife": 1.0,
            "english_level": 1.0,
            "adventure": 1.0,
            "family": -1.0,
        }
    },
    "family_vacation": {
        "name": "👨‍👩‍👧‍👦 Family Vacation",
        "description": "Safe and fun for the whole family",
        "weights": {
            "family": 3.0,
            "safety": 3.0,
            "english_level": 2.0,
            "beach": 1.5,
            "nature": 1.5,
            "culture": 1.0,
            "food": 1.0,
            "adventure": 1.0,
            "nightlife": -1.5,
            "crowds": -0.5,
            "romance": 0.0,
        }
    },
    "budget_backpacker": {
        "name": "💰 Budget Travel",
        "description": "Maximum experience, minimum cost",
        "weights": {
            "avg_budget_per_day": -3.0,
            "safety": 2.0,
            "english_level": 1.5,
            "culture": 1.5,
            "food": 1.5,
            "adventure": 1.5,
            "nature": 1.0,
            "crowds": -0.5,
            "beach": 1.0,
            "nightlife": 1.0,
            "romance": 0.5,
            "family": 0.5,
        }
    },
    "hidden_gems": {
        "name": "🗺️ Hidden Gems",
        "description": "Off the beaten path destinations",
        "weights": {
            "crowds": -3.0,
            "nature": 2.0,
            "culture": 1.5,
            "adventure": 1.5,
            "safety": 1.5,
            "food": 1.0,
            "english_level": 0.5,
            "beach": 1.0,
            "nightlife": 0.0,
            "romance": 1.5,
            "family": 1.0,
        }
    },
    "balanced": {
        "name": "⚖️ Balanced",
        "description": "A bit of everything",
        "weights": {
            "safety": 2.0,
            "culture": 1.5,
            "nature": 1.5,
            "food": 1.5,
            "beach": 1.0,
            "english_level": 1.0,
            "adventure": 1.0,
            "nightlife": 0.5,
            "romance": 1.0,
            "family": 1.0,
            "crowds": -0.5,
        }
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def filter_by_budget(
    total_budget: float, 
    trip_days: int, 
    num_travelers: int = 1
) -> List[Dict[str, Any]]:
    """Filters destinations based on user's budget for all travelers."""
    budget_matches = get_destinations_by_budget(total_budget, trip_days, num_travelers)
    
    if not budget_matches:
        return get_all_destinations()
    
    return budget_matches


def test_locations(
    budget_matches: List[Dict[str, Any]],
    id_used: List[int],
    x: int = 3
) -> List[Dict[str, Any]]:
    """Selects random destinations for a matching round."""
    remaining = [d for d in budget_matches if d["id"] not in id_used]
    
    if len(remaining) <= x:
        return remaining
    
    return random.sample(remaining, x)


def get_travel_style_weights(style: str) -> Dict[str, float]:
    """Returns the feature weights for a specific travel style."""
    if style in TRAVEL_STYLES:
        return TRAVEL_STYLES[style]["weights"]
    return DEFAULT_WEIGHTS


# =============================================================================
# SCORING ALGORITHM
# =============================================================================

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Normalizes a value to the range 0-1."""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def calculate_feature_ranges(destinations: List[Dict[str, Any]]) -> Dict[str, tuple]:
    """Calculates min/max ranges for each feature across all destinations."""
    ranges = {}
    
    all_features = MATCHING_FEATURES + ["avg_budget_per_day"]
    
    for feature in all_features:
        values = []
        for d in destinations:
            val = d.get(feature)
            if val is not None:
                values.append(val)
        
        if values:
            ranges[feature] = (min(values), max(values))
        else:
            ranges[feature] = (1, 5)
    
    return ranges


def preference_vector(chosen: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculates the user's preference vector from their choices."""
    if not chosen:
        return {}
    
    preference = {}
    all_features = MATCHING_FEATURES + ["avg_budget_per_day"]
    
    for feature in all_features:
        values = []
        for d in chosen:
            val = d.get(feature)
            if val is not None:
                values.append(val)
        
        if values:
            preference[feature] = sum(values) / len(values)
    
    return preference


def calculate_match_score(
    destination: Dict[str, Any],
    preference: Dict[str, float],
    feature_ranges: Dict[str, tuple],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """Calculates match score between a destination and user preferences."""
    if not preference:
        return 50.0
    
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    total_weighted_similarity = 0.0
    total_weight = 0.0
    
    all_features = MATCHING_FEATURES + ["avg_budget_per_day"]
    
    for feature in all_features:
        if feature not in preference:
            continue
        
        dest_value = destination.get(feature)
        if dest_value is None:
            continue
        
        weight = weights.get(feature, 0)
        if weight == 0:
            continue
        
        min_val, max_val = feature_ranges.get(feature, (1, 5))
        
        norm_dest = normalize_value(dest_value, min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        abs_weight = abs(weight)
        
        if weight < 0:
            similarity = 1.0 - similarity
        
        total_weighted_similarity += similarity * abs_weight
        total_weight += abs_weight
    
    if total_weight == 0:
        return 50.0
    
    score = (total_weighted_similarity / total_weight) * 100
    return round(score, 1)


def calculate_combined_score(
    destination: Dict[str, Any],
    match_score: float,
    weather_weight: float = 0.2
) -> float:
    """Combines match score with weather score for final ranking."""
    weather_score = destination.get('weather_score', 50.0)
    if weather_score is None:
        weather_score = 50.0
    combined = (match_score * (1 - weather_weight)) + (weather_score * weather_weight)
    return round(combined, 1)


# =============================================================================
# MAIN RANKING FUNCTION
# =============================================================================

def ranking_destinations(
    budget_matches: List[Dict[str, Any]],
    chosen: List[Dict[str, Any]],
    travel_style: str = "balanced",
    use_weather: bool = True,
    weather_weight: float = 0.2
) -> List[Dict[str, Any]]:
    """Ranks all destinations based on user preferences."""
    preference = preference_vector(chosen)
    feature_ranges = calculate_feature_ranges(budget_matches)
    weights = get_travel_style_weights(travel_style)
    
    scored_destinations = []
    
    for dest in budget_matches:
        dest_copy = dest.copy()
        
        match_score = calculate_match_score(
            dest_copy, preference, feature_ranges, weights
        )
        dest_copy['match_score'] = match_score
        
        weather_score = dest_copy.get('weather_score', 50.0)
        if weather_score is None:
            weather_score = 50.0
        dest_copy['weather_score'] = round(weather_score, 1)
        
        if use_weather:
            dest_copy['combined_score'] = calculate_combined_score(
                dest_copy, match_score, weather_weight
            )
        else:
            dest_copy['combined_score'] = match_score
        
        scored_destinations.append(dest_copy)
    
    scored_destinations.sort(key=lambda d: d['combined_score'], reverse=True)
    
    return scored_destinations


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_matching():
    """Test function to verify module is loaded correctly."""
    return "Matching module loaded successfully"