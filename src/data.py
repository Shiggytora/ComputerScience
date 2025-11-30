# We use this to load data sources

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "travel.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_all_destinations() -> List[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM destinations;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_destinations_by_budget(total_budget: float, trip_days: int) -> List[Dict[str, Any]]:
    """
    Filters destinations by total trip cost (flight + daily budget). 
    """
    all_destinations = get_all_destinations()
    matches = []
    
    for dest in all_destinations:
        # Get flight price (0 if not available)
        flight_price = dest.get('flight_price') or 0
        daily_budget = dest.get('avg_budget_per_day') or 0
        
        # Calculate total trip cost
        total_cost = flight_price + (daily_budget * trip_days)
        
        # Allow destinations within budget (with 20% flexibility)
        if total_cost <= total_budget * 1.2:
            dest_copy = dest.copy()
            dest_copy['total_trip_cost'] = total_cost
            dest_copy['budget_remaining'] = total_budget - total_cost
            matches.append(dest_copy)
    
    # Sort by total cost (cheapest first)
    matches.sort(key=lambda d: d['total_trip_cost'])
    
    return matches


def test_data():
    return {"Status": "Data successful"}