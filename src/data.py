"""
Database access for destination data.
Uses SQLite database with destination information.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

# Path to database file
DB_PATH = Path(__file__).parent.parent / "data" / "travel.db"


def get_connection():
    """Create database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def get_all_destinations() -> List[Dict[str, Any]]:
    """Load all destinations from database."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM destinations;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_destinations_by_budget(total_budget: float, trip_days: int, num_travelers: int = 1) -> List[Dict]:
    """
    Filter destinations that fit within budget.
    Calculates total cost: flights + daily expenses for all travelers.
    """
    all_dests = get_all_destinations()
    matches = []
    
    for dest in all_dests:
        flight = dest.get('flight_price') or 0
        daily = dest.get('avg_budget_per_day') or 0
        
        # Total for all travelers
        flight_total = flight * num_travelers
        daily_total = daily * trip_days * num_travelers
        total = flight_total + daily_total
        
        # Allow 20% over budget for flexibility
        if total <= total_budget * 1.2:
            d = dest.copy()
            d['total_trip_cost'] = total
            d['budget_remaining'] = total_budget - total
            matches.append(d)
    
    # Sort cheapest first
    matches.sort(key=lambda x: x['total_trip_cost'])
    return matches