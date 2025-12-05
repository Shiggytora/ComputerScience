"""
Data Module - Database Access and Budget Filtering

This module handles loading destination data from the SQLite database
and provides filtering functions based on user budget constraints. 

Part of Requirement #2: API/Database Implementation
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "travel.db"


def get_connection():
    """
    Creates a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    return sqlite3.connect(DB_PATH)


def get_all_destinations() -> List[Dict[str, Any]]:
    """
    Retrieves all destinations from the database.
    
    Returns:
        List of destination dictionaries with all fields
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM destinations;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_destinations_by_budget(
    total_budget: float, 
    trip_days: int, 
    num_travelers: int = 1
) -> List[Dict[str, Any]]:
    """
    Filters destinations by total trip cost for all travelers.
    
    This function calculates the total cost for a group of travelers
    including flights and daily expenses, and returns only destinations
    that fit within the specified budget.
    
    Args:
        total_budget: Total trip budget in CHF for ALL travelers combined
        trip_days: Number of days for the trip
        num_travelers: Number of people traveling (default: 1)
        
    Returns:
        List of matching destination dictionaries with added cost calculations:
        - total_trip_cost: Total cost for all travelers
        - flight_total: Total flight cost for all travelers
        - daily_total: Total daily expenses for all travelers
        - num_travelers: Number of travelers (for reference)
        - budget_remaining: Remaining budget after trip costs
        
    Example:
        >>> destinations = get_destinations_by_budget(5000, 7, 2)
        >>> # Returns destinations where 2 people can travel for 7 days
        >>> # with a combined budget of 5000 CHF
    """
    all_destinations = get_all_destinations()
    matches = []
    
    for dest in all_destinations:
        # Get base prices (per person)
        flight_price = dest.get('flight_price') or 0
        daily_budget = dest.get('avg_budget_per_day') or 0
        
        # Calculate total trip cost for ALL travelers
        flight_total = flight_price * num_travelers
        daily_total = daily_budget * trip_days * num_travelers
        total_cost = flight_total + daily_total
        
        # Allow destinations within budget (with 20% flexibility)
        if total_cost <= total_budget * 1.2:
            dest_copy = dest.copy()
            dest_copy['total_trip_cost'] = total_cost
            dest_copy['flight_total'] = flight_total
            dest_copy['daily_total'] = daily_total
            dest_copy['num_travelers'] = num_travelers
            dest_copy['budget_remaining'] = total_budget - total_cost
            matches.append(dest_copy)
    
    # Sort by total cost (cheapest first)
    matches.sort(key=lambda d: d['total_trip_cost'])
    
    return matches


def test_data():
    """Test function to verify module is loaded correctly."""
    return {"Status": "Data successful"}