# We use this for the main logic of our matching feature

import streamlit as st

#importing the data from the APIs to get the information in order to proceed the matching based on User inputs 

from api.amadeus_client import get_flight_price, get_hotel_price #takes the flight price and the hotel price from the API Amadeus 
from api.openmeteo_client import get_weather_forecast #takes the weather forecast over the next 14 days from the API Openmeteo 
from api.visualcrossing_client import get_typical_weather # ?
from api.currency_client import convert_currency #takes the exchange rate of the relevant currency from the API Currency 
from api.travelbuddy_client import check_visa #this API looks if there is a specific entry requirement in the selected country from the user 


# -------------------------------------------------------------------
# 1) COMPUTE FACTOR WEIGHTS BASED ON USER PRIORITIES
# -------------------------------------------------------------------
def compute_factor_weights(priorities: dict) -> dict:
    """
    priorities example:
    {
        "weather": 1,
        "budget": 2,
        "distance": 3
    }
    1 = most important.
    We convert this into normalized weights.
    """
    max_rank = max(priorities.values())
    raw = {k: max_rank + 1 - v for k, v in priorities.items()}
    total = sum(raw.values())
    return {k: raw[k] / total for k in raw}


# -------------------------------------------------------------------
# 2) WEATHER SUBSCORE FUNCTION
# -------------------------------------------------------------------
def calculate_weather_subscore(preference, temperature):
    """
    preference: warm | mild | cold
    temperature: actual destination temperature
    Returns a score between 0 and 1.
    """
    if preference == "warm":
        target = 25
    elif preference == "mild":
        target = 18
    else:
        target = 5

    return max(0, 1 - abs(temperature - target) / 20)


# -------------------------------------------------------------------
# 3) MAIN FUNCTION TO SCORE A DESTINATION
# -------------------------------------------------------------------
def score_destination(dest, user_prefs, weights):

    score = 0

    #  WEATHER 
    if "weather" in weights:
        weather = get_weather_forecast(dest["lat"], dest["lon"])
        current_temp = weather["temp"]
        sub = calculate_weather_subscore(user_prefs["weather_preference"], current_temp)
        score += weights["weather"] * sub

    #  BUDGET 
    if "budget" in weights:
        flight_price = get_flight_price(user_prefs["origin"], dest["airport"])
        hotel_price = get_hotel_price(dest["city"])

        total_cost_local = flight_price + hotel_price
        total_cost_eur = convert_currency(total_cost_local, dest["currency"], "EUR")

        if user_prefs["budget_min"] <= total_cost_eur <= user_prefs["budget_max"]:
            sub = 1
        else:
            sub = 0
        score += weights["budget"] * sub

    # DISTANCE / CONTINENT 
    if "distance" in weights:
        if user_prefs["continent"] == "any":
            sub = 1
        else:
            same = dest["continent"].lower() == user_prefs["continent"].lower()
            sub = 1 if same else 0.2
        score += weights["distance"] * sub

    # TOURISM LEVEL 
    if "tourism" in weights:
        sub = 1 if dest["tourist_level"] == user_prefs["tourism_level"] else 0.5
        score += weights["tourism"] * sub

    # CITY SIZE 
    if "city_size" in weights:
        sub = 1 if dest["city_size"] == user_prefs["city_size"] else 0.5
        score += weights["city_size"] * sub

    # VISA REQUIREMENT 
    if "visa" in weights:
        visa_info = check_visa(user_prefs["nationality"], dest["country"])
        sub = 1 if not visa_info["required"] else 0
        score += weights["visa"] * sub

    return score


# -------------------------------------------------------------------
# 4) RANK DESTINATIONS (SORT BY SCORE)
# -------------------------------------------------------------------
def rank_destinations(destinations, user_prefs, priorities):
    """
    destinations : list of destination dictionaries
    user_prefs : user preferences dictionary
    priorities : dictionary of prioritized factors (1 = most important)
    """
    weights = compute_factor_weights(priorities)
    results = []

    for d in destinations:
        s = score_destination(d, user_prefs, weights)
        results.append({"destination": d, "score": s})

    # Sort by score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)

    return results


def test_matching():

    return "Matching successful"
    


