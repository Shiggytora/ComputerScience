"""
Matching algorithm for travel recommendations.
Learns user preferences and uses KNN for finding similar destinations.
"""

from typing import List, Dict, Optional
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from src.data import get_destinations_by_budget, get_all_destinations

# Features used for matching destinations to preferences
MATCHING_FEATURES = [
    "safety", "english_level", "crowds", "beach", "culture",
    "nature", "food", "nightlife", "adventure", "romance", "family",
]

# Default weights when no travel style selected
DEFAULT_WEIGHTS = {
    "safety": 2.0, "english_level": 1.0, "crowds": 1.0, "beach": 1.0,
    "culture": 1.0, "nature": 1.0, "food": 1.0, "nightlife": 1.0,
    "adventure": 1.0, "romance": 1.0, "family": 1.0,
}

# Different travel styles with custom feature weights
# Positive weight = prefer higher values
# Negative weight = prefer lower values (e.g. crowds)
TRAVEL_STYLES = {
    "beach_relaxation": {
        "name": "🏖️ Beach & Relaxation",
        "description": "Sun, sand, and relaxation",
        "weights": {
            "beach": 3.0, "safety": 2.0, "crowds": -1.5, "nature": 1.5,
            "romance": 1.0, "food": 1.0, "nightlife": 0.5, "culture": 0.5,
            "adventure": 0.5, "english_level": 1.0, "family": 1.0,
        }
    },
    "culture_history": {
        "name": "🏛️ Culture & History",
        "description": "Museums, architecture, and heritage",
        "weights": {
            "culture": 3.0, "food": 2.0, "safety": 1.5, "english_level": 1.5,
            "nature": 1.0, "romance": 1.0, "crowds": -0.5, "beach": 0.5,
            "nightlife": 0.5, "adventure": 0.5, "family": 1.0,
        }
    },
    "adventure_nature": {
        "name": "🏔️ Adventure & Nature",
        "description": "Hiking, wildlife, and outdoor activities",
        "weights": {
            "adventure": 3.0, "nature": 3.0, "crowds": -2.0, "safety": 2.0,
            "culture": 0.5, "beach": 0.5, "food": 1.0, "english_level": 1.0,
            "nightlife": 0.0, "romance": 1.0, "family": 1.0,
        }
    },
    "foodie": {
        "name": "🍽️ Food & Culinary",
        "description": "Local cuisine and gastronomic experiences",
        "weights": {
            "food": 3.0, "culture": 2.0, "safety": 1.5, "english_level": 1.0,
            "nightlife": 1.0, "crowds": -0.5, "beach": 0.5, "nature": 1.0,
            "adventure": 0.5, "romance": 1.5, "family": 1.0,
        }
    },
    "party_nightlife": {
        "name": "🎉 Party & Nightlife",
        "description": "Clubs, bars, and vibrant nightlife",
        "weights": {
            "nightlife": 3.0, "beach": 1.5, "safety": 1.5, "english_level": 2.0,
            "food": 1.5, "crowds": 0.5, "culture": 0.5, "nature": 0.5,
            "adventure": 1.0, "romance": 1.0, "family": -1.0,
        }
    },
    "romantic_getaway": {
        "name": "💕 Romantic Getaway",
        "description": "Perfect for couples and honeymoons",
        "weights": {
            "romance": 3.0, "safety": 2.5, "food": 2.0, "beach": 2.0,
            "crowds": -2.0, "nature": 2.0, "culture": 1.5, "nightlife": 1.0,
            "english_level": 1.0, "adventure": 1.0, "family": -1.0,
        }
    },
    "family_vacation": {
        "name": "👨‍👩‍👧‍👦 Family Vacation",
        "description": "Safe and fun for the whole family",
        "weights": {
            "family": 3.0, "safety": 3.0, "english_level": 2.0, "beach": 1.5,
            "nature": 1.5, "culture": 1.0, "food": 1.0, "adventure": 1.0,
            "nightlife": -1.5, "crowds": -0.5, "romance": 0.0,
        }
    },
    "budget_backpacker": {
        "name": "💰 Budget Travel",
        "description": "Maximum experience, minimum cost",
        "weights": {
            "avg_budget_per_day": -3.0, "safety": 2.0, "english_level": 1.5,
            "culture": 1.5, "food": 1.5, "adventure": 1.5, "nature": 1.0,
            "crowds": -0.5, "beach": 1.0, "nightlife": 1.0,
            "romance": 0.5, "family": 0.5,
        }
    },
    "hidden_gems": {
        "name": "🗺️ Hidden Gems",
        "description": "Off the beaten path destinations",
        "weights": {
            "crowds": -3.0, "nature": 2.0, "culture": 1.5, "adventure": 1.5,
            "safety": 1.5, "food": 1.0, "english_level": 0.5, "beach": 1.0,
            "nightlife": 0.0, "romance": 1.5, "family": 1.0,
        }
    },
    "balanced": {
        "name": "⚖️ Balanced",
        "description": "A bit of everything",
        "weights": {
            "safety": 2.0, "culture": 1.5, "nature": 1.5, "food": 1.5,
            "beach": 1.0, "english_level": 1.0, "adventure": 1.0,
            "nightlife": 0.5, "romance": 1.0, "family": 1.0, "crowds": -0.5,
        }
    },
}


def filter_by_budget(total_budget: float, trip_days: int, num_travelers: int = 1) -> List[Dict]:
    """Get destinations that fit within budget."""
    matches = get_destinations_by_budget(total_budget, trip_days, num_travelers)
    if not matches:
        return get_all_destinations()
    return matches


def get_travel_style_weights(style: str) -> Dict[str, float]:
    """Get weights for a travel style."""
    if style in TRAVEL_STYLES:
        return TRAVEL_STYLES[style]["weights"]
    return DEFAULT_WEIGHTS


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Scale value to 0-1 range for comparison."""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def calculate_feature_ranges(destinations: List[Dict]) -> Dict[str, tuple]:
    """Get min/max for each feature. Needed for normalization."""
    ranges = {}
    all_features = MATCHING_FEATURES + ["avg_budget_per_day"]
    
    for feature in all_features:
        values = [d.get(feature) for d in destinations if d.get(feature) is not None]
        if values:
            ranges[feature] = (min(values), max(values))
        else:
            ranges[feature] = (1, 5)
    
    return ranges


def preference_vector(chosen: List[Dict]) -> Dict[str, float]:
    """
    Learn user preferences from their choices.
    Simply averages each feature across chosen destinations.
    """
    if not chosen:
        return {}
    
    preference = {}
    all_features = MATCHING_FEATURES + ["avg_budget_per_day"]
    
    for feature in all_features:
        values = [d.get(feature) for d in chosen if d.get(feature) is not None]
        if values:
            preference[feature] = sum(values) / len(values)
    
    return preference


def calculate_match_score(destination: Dict, preference: Dict,
                          feature_ranges: Dict, weights: Optional[Dict] = None) -> float:
    """
    Calculate how well a destination matches user preferences.
    Returns score from 0-100.
    """
    if not preference:
        return 50.0
    
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    total_sim = 0.0
    total_weight = 0.0
    all_features = MATCHING_FEATURES + ["avg_budget_per_day"]
    
    for feature in all_features:
        if feature not in preference:
            continue
        
        dest_val = destination.get(feature)
        if dest_val is None:
            continue
        
        weight = weights.get(feature, 0)
        if weight == 0:
            continue
        
        min_val, max_val = feature_ranges.get(feature, (1, 5))
        
        # Normalize to 0-1
        norm_dest = normalize_value(dest_val, min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        # Similarity: 1 = same, 0 = opposite
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        # Negative weight means prefer lower values
        if weight < 0:
            similarity = 1.0 - similarity
        
        total_sim += similarity * abs(weight)
        total_weight += abs(weight)
    
    if total_weight == 0:
        return 50.0
    
    return round((total_sim / total_weight) * 100, 1)


def calculate_combined_score(destination: Dict, match_score: float,
                             weather_weight: float = 0.2) -> float:
    """Combine match score with weather score."""
    weather = destination.get('weather_score', 50.0) or 50.0
    combined = (match_score * (1 - weather_weight)) + (weather * weather_weight)
    return round(combined, 1)


def ranking_destinations(budget_matches: List[Dict], chosen: List[Dict],
                         travel_style: str = "balanced", use_weather: bool = True,
                         weather_weight: float = 0.2) -> List[Dict]:
    """
    Rank all destinations based on learned preferences.
    Returns sorted list with best matches first.
    """
    preference = preference_vector(chosen)
    feature_ranges = calculate_feature_ranges(budget_matches)
    weights = get_travel_style_weights(travel_style)
    
    scored = []
    
    for dest in budget_matches:
        d = dest.copy()
        
        match = calculate_match_score(d, preference, feature_ranges, weights)
        d['match_score'] = match
        
        weather = d.get('weather_score', 50.0) or 50.0
        d['weather_score'] = round(weather, 1)
        
        if use_weather:
            d['combined_score'] = calculate_combined_score(d, match, weather_weight)
        else:
            d['combined_score'] = match
        
        scored.append(d)
    
    scored.sort(key=lambda x: x['combined_score'], reverse=True)
    return scored


# KNN for finding similar destinations
# Uses scikit-learn's NearestNeighbors with cosine similarity

KNN_FEATURES = [
    "beach", "culture", "nature", "food", "nightlife",
    "adventure", "safety", "romance", "family", "crowds", "english_level"
]

# Cache for KNN model (avoid refitting every call)
_knn_model = None
_knn_scaler = None
_knn_destinations = []


def _build_feature_matrix(destinations: List[Dict]) -> np.ndarray:
    """Convert destinations to numpy matrix for KNN."""
    matrix = []
    for dest in destinations:
        row = [float(dest.get(f, 3.0) or 3.0) for f in KNN_FEATURES]
        matrix.append(row)
    return np.array(matrix)


def _fit_knn(destinations: List[Dict]):
    """Train KNN model on destinations."""
    global _knn_model, _knn_scaler, _knn_destinations
    
    if not destinations:
        return
    
    _knn_destinations = destinations
    features = _build_feature_matrix(destinations)
    
    # Normalize so all features contribute equally
    _knn_scaler = MinMaxScaler()
    normalized = _knn_scaler.fit_transform(features)
    
    # Use cosine similarity
    _knn_model = NearestNeighbors(
        n_neighbors=min(10, len(destinations)),
        metric='cosine',
        algorithm='brute'
    )
    _knn_model.fit(normalized)


def find_similar_destinations(target: Dict, all_destinations: List[Dict],
                              num_similar: int = 3) -> List[Dict]:
    """
    Find similar destinations using KNN algorithm.
    Uses scikit-learn NearestNeighbors with cosine similarity.
    """
    global _knn_model, _knn_scaler, _knn_destinations
    
    if not all_destinations or not target:
        return []
    
    # Rebuild model if needed
    if len(_knn_destinations) != len(all_destinations) or _knn_model is None:
        _fit_knn(all_destinations)
    
    if _knn_model is None or _knn_scaler is None:
        return []
    
    # Get target features
    target_features = [float(target.get(f, 3.0) or 3.0) for f in KNN_FEATURES]
    target_normalized = _knn_scaler.transform([target_features])
    
    # Find neighbors
    k = min(num_similar + 1, len(_knn_destinations))
    distances, indices = _knn_model.kneighbors(target_normalized, n_neighbors=k)
    
    results = []
    target_id = target.get('id')
    
    for idx, dist in zip(indices[0], distances[0]):
        dest = _knn_destinations[idx]
        
        # Skip target itself
        if dest.get('id') == target_id:
            continue
        
        # Convert distance to similarity percentage
        similarity = (1 - dist / 2) * 100
        
        results.append({**dest, 'similarity_score': round(similarity, 1)})
        
        if len(results) >= num_similar:
            break
    
    return results