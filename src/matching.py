"""
Matching Module - Core Recommendation Engine

This module implements the matching algorithm that learns user preferences
from their choices and calculates compatibility scores for all destinations. 

The algorithm uses:
1. Preference learning from user selections
2. Weighted feature similarity scoring
3. Travel style adjustments
4. Weather integration (optional)

Part of Requirement #5: Machine Learning Implementation
"""

import random
from typing import List, Dict, Any, Optional
from src.data import get_destinations_by_budget, get_all_destinations

# =============================================================================
# FEATURE CONFIGURATION
# =============================================================================

# All numeric features used in the matching algorithm
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

# Features where lower values are sometimes preferred
INVERTIBLE_FEATURES = ["crowds", "avg_budget_per_day"]

# Default weights for balanced matching
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

# Aliases for backward compatibility
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
    """
    Filters destinations based on user's budget for all travelers.
    
    This function wraps the data module's budget filtering and provides
    a fallback to all destinations if no matches are found.
    
    Args:
        total_budget: Total trip budget in CHF for ALL travelers combined
        trip_days: Number of days for the trip
        num_travelers: Number of people traveling (default: 1)
        
    Returns:
        List of matching destination dictionaries
        
    Example:
        >>> matches = filter_by_budget(6000, 10, 2)
        >>> # Returns destinations affordable for 2 people over 10 days
    """
    budget_matches = get_destinations_by_budget(total_budget, trip_days, num_travelers)
    
    # Fallback to all destinations if no budget matches
    if not budget_matches:
        return get_all_destinations()
    
    return budget_matches


def test_locations(
    budget_matches: List[Dict[str, Any]],
    id_used: List[int],
    x: int = 3
) -> List[Dict[str, Any]]:
    """
    Selects random destinations for a matching round.
    
    Args:
        budget_matches: List of all matching destinations
        id_used: List of destination IDs already shown
        x: Number of destinations to return
        
    Returns:
        List of x random destinations
    """
    remaining = [d for d in budget_matches if d["id"] not in id_used]
    
    if len(remaining) <= x:
        return remaining
    
    return random.sample(remaining, x)


def get_travel_style_weights(style: str) -> Dict[str, float]:
    """
    Returns the feature weights for a specific travel style.
    
    Args:
        style: Travel style key
        
    Returns:
        Dictionary of feature weights
    """
    if style in TRAVEL_STYLES:
        return TRAVEL_STYLES[style]["weights"]
    return DEFAULT_WEIGHTS


# =============================================================================
# SCORING ALGORITHM
# =============================================================================

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    Normalizes a value to the range 0-1. 
    
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
    
    Args:
        destinations: List of destination dictionaries
        
    Returns:
        Dictionary mapping feature names to (min, max) tuples
    """
    ranges = {}
    
    # Add budget to features for range calculation
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
            ranges[feature] = (1, 5)  # Default range for 1-5 scores
    
    return ranges


def preference_vector(chosen: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates the user's preference vector from their choices.
    
    This is the core of the learning algorithm: it computes the average
    value for each feature across all destinations chosen by the user. 
    
    Args:
        chosen: List of destinations chosen by the user
        
    Returns:
        Dictionary mapping features to average preferred values
    """
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
    """
    Calculates match score between a destination and user preferences.
    
    Algorithm:
    1. Normalize both destination and preference values to 0-1
    2. Calculate similarity as 1 - |normalized_dest - normalized_pref|
    3. Apply weights (negative weights invert the similarity)
    4. Return weighted average as percentage (0-100)
    
    Args:
        destination: Destination dictionary with features
        preference: User's preference vector
        feature_ranges: Min/max ranges for normalization
        weights: Feature weights
        
    Returns:
        Match score as percentage (0-100)
    """
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
        
        # Normalize values
        norm_dest = normalize_value(dest_value, min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        # Calculate similarity (1 = identical, 0 = opposite)
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        abs_weight = abs(weight)
        
        # Negative weight = inverse preference
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
    """
    Combines match score with weather score for final ranking.
    
    Args:
        destination: Destination with optional weather_score field
        match_score: Calculated match score
        weather_weight: Weight for weather (0-1)
        
    Returns:
        Combined score as percentage (0-100)
    """
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
    """
    Ranks all destinations based on user preferences.
    
    This is the main recommendation function that:
    1. Learns user preferences from their choices
    2. Applies travel style weights
    3. Calculates match scores for all destinations
    4. Optionally incorporates weather data
    5. Returns sorted list with best matches first
    
    Args:
        budget_matches: All budget-matching destinations
        chosen: Destinations chosen by user in matching rounds
        travel_style: Selected travel style for weight adjustment
        use_weather: Whether to include weather in scoring
        weather_weight: How much weather affects final score
        
    Returns:
        Sorted list of destinations with scores added
    """
    # Learn user preferences
    preference = preference_vector(chosen)
    feature_ranges = calculate_feature_ranges(budget_matches)
    weights = get_travel_style_weights(travel_style)
    
    scored_destinations = []
    
    for dest in budget_matches:
        dest_copy = dest.copy()
        
        # Calculate match score
        match_score = calculate_match_score(
            dest_copy, preference, feature_ranges, weights
        )
        dest_copy['match_score'] = match_score
        
        # Get weather score
        weather_score = dest_copy.get('weather_score', 50.0)
        if weather_score is None:
            weather_score = 50.0
        dest_copy['weather_score'] = round(weather_score, 1)
        
        # Calculate combined score
        if use_weather:
            dest_copy['combined_score'] = calculate_combined_score(
                dest_copy, match_score, weather_weight
            )
        else:
            dest_copy['combined_score'] = match_score
        
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
    
    Args:
        destination: The destination to analyze
        preference: User's preference vector
        feature_ranges: Normalization ranges
        weights: Feature weights used
        
    Returns:
        Dictionary with per-feature similarity details
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    breakdown = {}
    
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
        
        # Invert display for negative weights
        if weight < 0:
            display_similarity = 1.0 - similarity
        else:
            display_similarity = similarity
        
        breakdown[feature] = {
            'destination_value': dest_value,
            'preference_value': round(preference[feature], 2),
            'similarity': round(display_similarity * 100, 1),
            'weight': weight,
            'is_inverse': weight < 0,
        }
    
    return breakdown


# =============================================================================
# SIMILAR DESTINATIONS
# =============================================================================

def find_similar_destinations(
    target: Dict[str, Any],
    all_destinations: List[Dict[str, Any]],
    num_similar: int = 3
) -> List[Dict[str, Any]]:
    """
    Finds destinations similar to the target based on feature profiles.
    
    This function compares the target destination's features with all other
    destinations and returns the most similar ones.  Useful for suggesting
    alternatives to the user's top match.
    
    Algorithm:
    1. Compare each feature value between target and candidate
    2. Calculate similarity as 1 - (normalized difference)
    3. Average across all features
    4. Return top N most similar destinations
    
    Args:
        target: The destination to find similar ones for
        all_destinations: All available destinations to compare against
        num_similar: Number of similar destinations to return (default: 3)
        
    Returns:
        List of similar destinations sorted by similarity score,
        each with an added 'similarity_score' field (0-100)
        
    Example:
        >>> similar = find_similar_destinations(best_match, all_destinations, 3)
        >>> for dest in similar:
        ...     print(f"{dest['city']}: {dest['similarity_score']}% similar")
    """
    features = [
        "beach", "culture", "nature", "food", "nightlife",
        "adventure", "safety", "romance", "family", "crowds"
    ]
    
    similarities = []
    
    for dest in all_destinations:
        # Skip the target destination itself
        if dest.get('id') == target.get('id'):
            continue
        
        # Calculate feature similarity
        similarity_sum = 0
        feature_count = 0
        
        for feature in features:
            target_val = target.get(feature)
            dest_val = dest.get(feature)
            
            if target_val is not None and dest_val is not None:
                # Normalize difference (max diff is 4 on 1-5 scale)
                diff = abs(target_val - dest_val) / 4.0
                # Similarity = 1 - normalized difference
                similarity_sum += (1 - diff)
                feature_count += 1
        
        if feature_count > 0:
            avg_similarity = (similarity_sum / feature_count) * 100
            similarities.append({
                **dest,
                'similarity_score': round(avg_similarity, 1)
            })
    
    # Sort by similarity score (highest first)
    similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return similarities[:num_similar]


# =============================================================================
# RECOMMENDATION CONFIDENCE
# =============================================================================

def calculate_recommendation_confidence(
    ranked_destinations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculates how confident the recommendation is based on score distribution.
    
    High confidence means there's a clear winner with a significant gap
    between the top match and alternatives. Low confidence means many
    destinations have similar scores, so the user might want to explore options.
    
    Factors considered:
    1. Gap between #1 and #2 ranked destinations
    2. Score spread among top 5 destinations
    3. Absolute score of the top match
    
    Args:
        ranked_destinations: List of destinations sorted by combined_score
        
    Returns:
        Dictionary containing:
        - confidence: Percentage (0-100)
        - label: Human-readable confidence label
        - gap_to_second: Score difference between #1 and #2
        - top5_spread: Standard deviation of top 5 scores
        - recommendation: Advice based on confidence level
        
    Example:
        >>> confidence = calculate_recommendation_confidence(ranked)
        >>> print(f"Confidence: {confidence['label']} ({confidence['confidence']}%)")
    """
    if not ranked_destinations:
        return {
            "confidence": 0,
            "label": "No data",
            "emoji": "❓",
            "gap_to_second": 0,
            "top5_spread": 0,
            "top_score": 0,
            "recommendation": "No destinations to analyze"
        }
    
    if len(ranked_destinations) == 1:
        return {
            "confidence": 100,
            "label": "Only option",
            "emoji": "☝️",
            "gap_to_second": 0,
            "top5_spread": 0,
            "top_score": ranked_destinations[0].get('combined_score', 0),
            "recommendation": "This is the only destination matching your criteria"
        }
    
    # Get scores from top destinations
    scores = [d.get('combined_score', 0) for d in ranked_destinations[:5]]
    top_score = scores[0]
    
    # Calculate gap between #1 and #2
    gap = scores[0] - scores[1]
    
    # Calculate standard deviation of top 5
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5
    
    # Determine confidence level based on gap and top score
    if gap >= 10 and top_score >= 75:
        confidence = 95
        label = "Very High"
        emoji = "🎯"
        recommendation = "Clear winner!  This destination stands out for you."
    elif gap >= 7 and top_score >= 70:
        confidence = 85
        label = "High"
        emoji = "✅"
        recommendation = "Strong match! You can book with confidence."
    elif gap >= 4 and top_score >= 60:
        confidence = 70
        label = "Good"
        emoji = "👍"
        recommendation = "Good match. Consider checking the alternatives too."
    elif gap >= 2:
        confidence = 55
        label = "Medium"
        emoji = "🤔"
        recommendation = "Several good options. Compare the top 3 destinations."
    else:
        confidence = 40
        label = "Low"
        emoji = "⚖️"
        recommendation = "Many similar options. Explore alternatives below."
    
    # Adjust confidence if top score is low
    if top_score < 50:
        confidence = min(confidence, 50)
        recommendation = "Scores are low. Consider adjusting your preferences."
    
    return {
        "confidence": confidence,
        "label": label,
        "emoji": emoji,
        "gap_to_second": round(gap, 1),
        "top5_spread": round(std_dev, 1),
        "top_score": round(top_score, 1),
        "recommendation": recommendation
    }


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_matching():
    """Test function to verify module is loaded correctly."""
    return "Matching module loaded successfully"