"""
Insights Module - Analyzes user preferences and generates insights. 

This module provides functionality to analyze the destinations chosen by users
during the matching process and extract meaningful patterns and preferences. 

Part of Requirement #5: Machine Learning - Pattern recognition from user choices.
"""

from typing import List, Dict, Any


def generate_preference_insights(chosen: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes user selections and generates insights about their preferences.
    
    Args:
        chosen: List of destination dictionaries selected by the user
        
    Returns:
        Dictionary containing patterns and preferences
    """
    if not chosen:
        return {}
    
    insights = {
        "total_selections": len(chosen),
        "preferences": {},
        "patterns": [],
    }
    
    # Features to analyze
    features = [
        "safety", "english_level", "crowds", "beach", "culture",
        "nature", "food", "nightlife", "adventure", "romance", "family"
    ]
    
    # Calculate averages for each feature
    for feature in features:
        values = []
        for d in chosen:
            val = d.get(feature)
            if val is not None:
                values.append(val)
        
        if values:
            avg = sum(values) / len(values)
            insights["preferences"][feature] = round(avg, 2)
    
    # Detect patterns
    prefs = insights["preferences"]
    
    # Beach lover
    if prefs.get("beach", 0) >= 4:
        insights["patterns"].append("🏖️ You love beaches and coastal destinations!")
    
    # Culture enthusiast
    if prefs.get("culture", 0) >= 4:
        insights["patterns"].append("🏛️ You're drawn to culture and history!")
    
    # Nature lover
    if prefs.get("nature", 0) >= 4:
        insights["patterns"].append("🌿 You appreciate natural beauty!")
    
    # Foodie
    if prefs.get("food", 0) >= 4:
        insights["patterns"].append("🍽️ You're a food enthusiast!")
    
    # Party person
    if prefs.get("nightlife", 0) >= 4:
        insights["patterns"].append("🎉 You enjoy vibrant nightlife!")
    
    # Adventure seeker
    if prefs.get("adventure", 0) >= 4:
        insights["patterns"].append("🏔️ You're an adventure seeker!")
    
    # Romantic
    if prefs.get("romance", 0) >= 4:
        insights["patterns"].append("💕 You prefer romantic destinations!")
    
    # Family oriented
    if prefs.get("family", 0) >= 4:
        insights["patterns"].append("👨‍👩‍👧‍👦 You prioritize family-friendly places!")
    
    # Safety conscious
    if prefs.get("safety", 0) >= 4.5:
        insights["patterns"].append("🛡️ Safety is very important to you!")
    
    # Crowd avoider
    if prefs.get("crowds", 0) <= 2.5:
        insights["patterns"].append("🗺️ You prefer less touristy places!")
    
    # Crowd seeker
    if prefs.get("crowds", 0) >= 4:
        insights["patterns"].append("🌟 You like popular, bustling destinations!")
    
    # Budget analysis
    budgets = []
    for d in chosen:
        val = d.get("avg_budget_per_day")
        if val is not None:
            budgets.append(val)
    
    if budgets:
        avg_budget = sum(budgets) / len(budgets)
        if avg_budget <= 70:
            insights["patterns"].append("💰 You're budget-conscious!")
        elif avg_budget >= 180:
            insights["patterns"].append("💎 You prefer premium experiences!")
    
    # Continent preference
    continents = [d.get("continent", "") for d in chosen if d.get("continent")]
    if continents:
        from collections import Counter
        continent_counts = Counter(continents)
        top_continent = continent_counts.most_common(1)[0]
        if top_continent[1] >= len(chosen) * 0.5:
            insights["patterns"].append(f"🌍 You seem to prefer {top_continent[0]}!")
    
    return insights


def calculate_preference_strength(insights: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates the strength of each preference. 
    
    Args:
        insights: The insights dictionary
        
    Returns:
        Dictionary mapping feature names to strength scores (0-1)
    """
    if not insights.get("preferences"):
        return {}
    
    strengths = {}
    neutral = 3.0
    
    for feature, value in insights["preferences"].items():
        strength = abs(value - neutral) / 2.0
        strengths[feature] = min(1.0, strength)
    
    return strengths