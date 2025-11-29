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
    budget_per_day = total_budget / trip_days
    lower = budget_per_day * 0.6
    upper = budget_per_day * 1.15

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM destinations
        WHERE avg_budget_per_day BETWEEN ? AND ?
        """,
        (lower, upper),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def test_data():
    return {"Status": "Data successful"}