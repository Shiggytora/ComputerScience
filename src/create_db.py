import sqlite3
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "travel.db"
CSV_PATH = BASE_DIR / "data" / "destinations.csv"

def create_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS destinations (
            id                  INTEGER PRIMARY KEY,
            city                TEXT,
            country             TEXT,
            continent           TEXT,
            iata_code           TEXT,
            latitude            REAL,
            longitude           REAL,
            avg_budget_per_day  REAL,
            city_size           REAL,
            tourist_rating      REAL,
            tourist_volume_base REAL,
            is_coastal          REAL,
            climate_category    REAL,
            cost_index          REAL
        );
        """
    )

def load_csv():
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [
            (
                int(r["id"]),
                r["city"],
                r["country"],
                r["continent"],
                r["iata_code"],
                float(r["latitude"]),
                float(r["longitude"]),
                float(r["avg_budget_per_day"]),
                float(r["city_size"]),
                float(r["tourist_rating"]),
                float(r["tourist_volume_base"]),
                float(r["is_coastal"]),
                float(r["climate_category"]),
                float(r["cost_index"]),
            )
            for r in reader
        ]
        print(f"Loaded {len(data)} destinations")
        return data

def create_db():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    create_table(cur)

    if not CSV_PATH.exists():
        print("Error, not found")
        return
    
    destinations = load_csv()

    if not destinations:
        print("CSV failed to be loaded")
        return
    
    cur.execute("DELETE FROM destinations;")

    cur.executemany(
        """
        INSERT INTO destinations (
            id, city, country, continent, iata_code,
            latitude, longitude,
            avg_budget_per_day, city_size,
            tourist_rating, tourist_volume_base,
            is_coastal, climate_category, cost_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        destinations,
    )

    conn.commit()
    conn.close()
    print(f"created {DB_PATH} with {len(destinations)} destinations")

if __name__ == "__main__":
    create_db()