# We use this for the main logic of our matching feature

import streamlit as st #importing the data from the APIs to get the information in order to proceed the matching based on User inputs 
import requests
import random
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"#takes the weather forecast over the next 14 days from the API Openmeteo 
from amadeus import Client, ResponseError #takes the flight price and the hotel price from the API Amadeus 
from typing import List, Dict, Any
from src.data import get_destinations_by_budget, get_all_destinations
from src.config import get_secret

def filter_by_budget(total_budget: float, trip_days: int) -> List[Dict[str, Any]]:
    budget_matches = get_destinations_by_budget(total_budget, trip_days)
    if budget_matches:
        return budget_matches
    return get_all_destinations()

def test_locations(budget_matches: List[Dict[str, Any]], id_used: List[int], x: int = 3):
    remaining = [y for y in budget_matches if y ["id"] not in id_used]
    if len(remaining) <= x:
        return remaining
    return random.sample(remaining, x)

NUMERIC_FILTERS = [
    "city_size",
    "tourist_rating",
    "tourist_volume_base",
    "is_coastal",
    "climate_category",
    "cost_index",
]

def preference_vector(chosen: List[Dict[str, Any]]) -> Dict[str, float]:
    if not chosen:
        return {}
    
    preference = {}
    for feature in NUMERIC_FILTERS:
        preference[feature] = sum(y[feature] for y in chosen) / len(chosen)

    return preference

def scoring_destinations(destination: Dict[str, Any], preference: Dict[str, float]) -> float:
    if not preference:
        return 0
    
    score = 0
    for feature in NUMERIC_FILTERS:
        score += abs(destination[feature] - preference[feature])
    
    return score

def ranking_destinations(budget_matches: List[Dict[str, Any]], chosen: List[Dict[str, Any]]):
    preference = preference_vector(chosen)
    scored = [(scoring_destinations(y, preference), y) for y in budget_matches]
    scored.sort(key=lambda c: c[0])
    return [y for _, y in scored]


def test_matching():
    return "Test Matching successful"