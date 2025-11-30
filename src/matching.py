# We use this for the main logic of our matching feature

import streamlit as st
import requests
import random
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
from amadeus import Client, ResponseError
from typing import List, Dict, Any
from src.data import get_destinations_by_budget, get_all_destinations
from src.config import get_secret


def filter_by_budget(total_budget: float, trip_days: int) -> List[Dict[str, Any]]:
    budget_matches = get_destinations_by_budget(total_budget, trip_days)
    if budget_matches:
        return budget_matches
    return get_all_destinations()


def test_locations(budget_matches: List[Dict[str, Any]], id_used: List[int], x: int = 3):
    remaining = [y for y in budget_matches if y["id"] not in id_used]
    if len(remaining) <= x:
        return remaining
    return random.sample(remaining, x)


NUMERIC_FEATURES = [
    "city_size",
    "tourist_rating",
    "tourist_volume_base",
    "is_coastal",
    "climate_category",
    "cost_index",
]

# Gewichtung der Features (höher = wichtiger für den Match Score)
FEATURE_WEIGHTS = {
    "city_size": 1.0,
    "tourist_rating": 2.0,        # Rating ist wichtiger
    "tourist_volume_base": 1.0,
    "is_coastal": 1.5,            # Küstenlage ist mittel-wichtig
    "climate_category": 1.5,
    "cost_index": 1.0,
}


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Normalisiert einen Wert auf den Bereich 0-1."""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def calculate_feature_ranges(destinations: List[Dict[str, Any]]) -> Dict[str, tuple]:
    """Berechnet Min/Max für jedes Feature zur Normalisierung."""
    ranges = {}
    for feature in NUMERIC_FEATURES:
        values = [d[feature] for d in destinations if feature in d]
        if values:
            ranges[feature] = (min(values), max(values))
        else:
            ranges[feature] = (0, 1)
    return ranges


def preference_vector(chosen: List[Dict[str, Any]]) -> Dict[str, float]:
    """Berechnet den Präferenz-Vektor basierend auf den gewählten Destinationen."""
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
    feature_ranges: Dict[str, tuple]
) -> float:
    """
    Berechnet einen Match Score zwischen 0-100%. 
    
    Je höher der Score, desto besser passt die Destination zu den Präferenzen.
    """
    if not preference:
        return 50.0  # Neutraler Score wenn keine Präferenzen
    
    total_weighted_similarity = 0.0
    total_weight = 0.0
    
    for feature in NUMERIC_FEATURES:
        if feature not in preference or feature not in destination:
            continue
        
        min_val, max_val = feature_ranges. get(feature, (0, 1))
        
        # Normalisiere beide Werte
        norm_dest = normalize_value(destination[feature], min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        # Berechne Ähnlichkeit (1 - Differenz)
        similarity = 1. 0 - abs(norm_dest - norm_pref)
        
        # Gewichtung anwenden
        weight = FEATURE_WEIGHTS.get(feature, 1.0)
        total_weighted_similarity += similarity * weight
        total_weight += weight
    
    if total_weight == 0:
        return 50.0
    
    # Score als Prozent (0-100)
    score = (total_weighted_similarity / total_weight) * 100
    return round(score, 1)


def scoring_destinations(destination: Dict[str, Any], preference: Dict[str, float]) -> float:
    """Legacy-Funktion: Berechnet Distanz-Score (niedrig = besser)."""
    if not preference:
        return 0
    
    score = 0
    for feature in NUMERIC_FEATURES:
        if feature in preference and feature in destination:
            weight = FEATURE_WEIGHTS.get(feature, 1.0)
            score += abs(destination[feature] - preference[feature]) * weight
    
    return score


def ranking_destinations(
    budget_matches: List[Dict[str, Any]], 
    chosen: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rankt alle Destinationen basierend auf den Präferenzen.
    Fügt jedem Ergebnis einen match_score hinzu. 
    """
    preference = preference_vector(chosen)
    feature_ranges = calculate_feature_ranges(budget_matches)
    
    # Score berechnen und hinzufügen
    scored_destinations = []
    for dest in budget_matches:
        dest_copy = dest.copy()
        dest_copy['match_score'] = calculate_match_score(dest_copy, preference, feature_ranges)
        dest_copy['distance_score'] = scoring_destinations(dest_copy, preference)
        scored_destinations. append(dest_copy)
    
    # Nach Match Score sortieren (höher = besser)
    scored_destinations.sort(key=lambda d: d['match_score'], reverse=True)
    
    return scored_destinations


def get_match_breakdown(
    destination: Dict[str, Any],
    preference: Dict[str, float],
    feature_ranges: Dict[str, tuple]
) -> Dict[str, Dict[str, Any]]:
    """
    Gibt eine detaillierte Aufschlüsselung des Match Scores zurück. 
    Nützlich für die Anzeige, warum eine Destination gut/schlecht passt.
    """
    breakdown = {}
    
    for feature in NUMERIC_FEATURES:
        if feature not in preference or feature not in destination:
            continue
        
        min_val, max_val = feature_ranges.get(feature, (0, 1))
        
        norm_dest = normalize_value(destination[feature], min_val, max_val)
        norm_pref = normalize_value(preference[feature], min_val, max_val)
        
        similarity = 1.0 - abs(norm_dest - norm_pref)
        
        breakdown[feature] = {
            'destination_value': destination[feature],
            'preference_value': round(preference[feature], 2),
            'similarity': round(similarity * 100, 1),
            'weight': FEATURE_WEIGHTS.get(feature, 1.0),
        }
    
    return breakdown


def test_matching():
    return "Test Matching successful"