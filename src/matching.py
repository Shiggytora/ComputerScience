"""
Matching Module - Core Recommendation Engine

This module implements the matching algorithm that learns user preferences
from their choices and calculates compatibility scores for all destinations.

The algorithm uses:
1. Preference learning from user selections
2. Weighted feature similarity scoring
3. Travel style adjustments
4. Weather integration (optional)
5. KNN-based similar destination finder (Machine Learning)

Part of Requirement #5: Machine Learning Implementation
"""

import random
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
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
        style: Travel style key (e.g., 'beach_relaxation', 'balanced')
        
    Returns:
        Dictionary of feature weights for the selected style
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
    
    This is used to normalize feature values for fair comparison.
    
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
    This represents what the user "prefers" based on their selections.
    
    Args:
        chosen: List of destinations chosen by the user
        
    Returns:
        Dictionary mapping features to average preferred values
        
    Example:
        >>> chosen = [dest1, dest2, dest3]  # User's selections
        >>> prefs = preference_vector(chosen)
        >>> print(prefs['beach'])  # Average beach score of chosen destinations
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
        weights: Feature weights (from travel style)
        
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
        
        # Normalize values to 0-1 range
        norm_dest = normalize_value(dest_value, min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        # Calculate similarity (1 = identical, 0 = opposite)
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        abs_weight = abs(weight)
        
        # Negative weight = inverse preference (e.g., prefer LOW crowds)
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
        weather_weight: Weight for weather (0-1), default 0.2 = 20%
        
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
        weather_weight: How much weather affects final score (0-1)
        
    Returns:
        Sorted list of destinations with scores added:
        - match_score: Score based on preference matching
        - weather_score: Score based on weather compatibility
        - combined_score: Final weighted score
    """
    # Learn user preferences from their choices
    preference = preference_vector(chosen)
    feature_ranges = calculate_feature_ranges(budget_matches)
    weights = get_travel_style_weights(travel_style)
    
    scored_destinations = []
    
    for dest in budget_matches:
        dest_copy = dest.copy()
        
        # Calculate match score based on learned preferences
        match_score = calculate_match_score(
            dest_copy, preference, feature_ranges, weights
        )
        dest_copy['match_score'] = match_score
        
        # Get weather score (already calculated during enrichment)
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
    
    # Sort by combined score (higher = better match)
    scored_destinations.sort(key=lambda d: d['combined_score'], reverse=True)
    
    return scored_destinations


# =============================================================================
# ML-POWERED SIMILAR DESTINATIONS (KNN)
# Part of Requirement #5: Machine Learning Implementation
#
# This section implements K-Nearest Neighbors (KNN) using scikit-learn
# to find destinations with similar feature profiles.
# =============================================================================

# Features used for KNN similarity calculation
KNN_FEATURES = [
    "beach", "culture", "nature", "food", "nightlife",
    "adventure", "safety", "romance", "family", "crowds",
    "english_level"
]

# Global KNN model cache (singleton pattern for efficiency)
_knn_model: Optional[NearestNeighbors] = None
_knn_scaler: Optional[MinMaxScaler] = None
_knn_destinations: List[Dict[str, Any]] = []


def _extract_feature_matrix(destinations: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extracts feature matrix from destinations for KNN algorithm.
    
    Converts destination dictionaries into a numerical matrix suitable
    for machine learning algorithms.
    
    Args:
        destinations: List of destination dictionaries
        
    Returns:
        NumPy array of shape (n_destinations, n_features)
    """
    matrix = []
    for dest in destinations:
        row = []
        for feature in KNN_FEATURES:
            value = dest.get(feature, 3.0)  # Default to middle value
            if value is None:
                value = 3.0
            row.append(float(value))
        matrix.append(row)
    return np.array(matrix)


def _fit_knn_model(destinations: List[Dict[str, Any]]) -> None:
    """
    Fits the KNN model with destination data.
    
    Uses scikit-learn's NearestNeighbors with cosine similarity
    to build an index for finding similar destinations.
    
    Args:
        destinations: List of all destinations to index
    """
    global _knn_model, _knn_scaler, _knn_destinations
    
    if not destinations:
        return
    
    _knn_destinations = destinations
    
    # Extract features into a matrix
    raw_features = _extract_feature_matrix(destinations)
    
    # Normalize features using MinMaxScaler (sklearn)
    # This ensures all features are on the same scale (0-1)
    _knn_scaler = MinMaxScaler()
    normalized_features = _knn_scaler.fit_transform(raw_features)
    
    # Fit KNN model with cosine similarity metric
    # Cosine similarity measures the angle between feature vectors,
    # making it ideal for comparing destination profiles
    _knn_model = NearestNeighbors(
        n_neighbors=min(10, len(destinations)),
        metric='cosine',
        algorithm='brute'
    )
    _knn_model.fit(normalized_features)


def find_similar_destinations(
    target: Dict[str, Any],
    all_destinations: List[Dict[str, Any]],
    num_similar: int = 3
) -> List[Dict[str, Any]]:
    """
    Finds destinations similar to the target using K-Nearest Neighbors.
    
    This is the main Machine Learning component of the application.
    It uses scikit-learn's KNN algorithm with cosine similarity to find
    destinations with similar feature profiles to the user's top match.
    
    Algorithm (KNN with Cosine Similarity):
    1. Extract numerical features from all destinations
    2. Normalize features using MinMaxScaler (sklearn.preprocessing)
    3. Use cosine distance to measure similarity in feature space
    4. Find K nearest neighbors using NearestNeighbors (sklearn.neighbors)
    5. Convert distances to similarity percentages
    6. Return top N most similar destinations
    
    Machine Learning Components Used:
    - sklearn.neighbors.NearestNeighbors: KNN implementation
    - sklearn.preprocessing.MinMaxScaler: Feature normalization
    - numpy: Numerical array operations
    
    Args:
        target: The destination to find similar ones for
        all_destinations: All available destinations to compare against
        num_similar: Number of similar destinations to return (default: 3)
        
    Returns:
        List of similar destinations sorted by similarity score,
        each with an added 'similarity_score' field (0-100%)
        
    Example:
        >>> similar = find_similar_destinations(best_match, all_destinations, 3)
        >>> for dest in similar:
        ...     print(f"{dest['city']}: {dest['similarity_score']}% similar")
    """
    global _knn_model, _knn_scaler, _knn_destinations
    
    if not all_destinations or not target:
        return []
    
    # Refit model if destinations changed or model not initialized
    if len(_knn_destinations) != len(all_destinations) or _knn_model is None:
        _fit_knn_model(all_destinations)
    
    if _knn_model is None or _knn_scaler is None:
        return []
    
    # Extract and normalize target features
    target_features = []
    for feature in KNN_FEATURES:
        value = target.get(feature, 3.0)
        if value is None:
            value = 3.0
        target_features.append(float(value))
    
    # Transform target using the fitted scaler
    target_normalized = _knn_scaler.transform([target_features])
    
    # Find nearest neighbors (get extra in case we need to exclude self)
    k = min(num_similar + 1, len(_knn_destinations))
    distances, indices = _knn_model.kneighbors(target_normalized, n_neighbors=k)
    
    results = []
    target_id = target.get('id')
    
    for idx, dist in zip(indices[0], distances[0]):
        dest = _knn_destinations[idx]
        
        # Skip the target destination itself
        if dest.get('id') == target_id:
            continue
        
        # Convert cosine distance to similarity percentage
        # Cosine distance ranges from 0 (identical) to 2 (opposite)
        # We convert to 0-100% scale where 100% = identical
        similarity = (1 - dist / 2) * 100
        
        results.append({
            **dest,
            'similarity_score': round(similarity, 1)
        })
        
        if len(results) >= num_similar:
            break
    
    return results


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_matching():
    """Test function to verify module is loaded correctly."""
    return "Matching module loaded successfully with KNN (Machine Learning) support"