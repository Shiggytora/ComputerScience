"""
Script to rebuild the travel database with new schema. 
Run this locally, then upload the new travel.db to GitHub.
"""

import sqlite3
import csv
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "travel.db"
CSV_PATH = BASE_DIR / "data" / "destinations.csv"

def rebuild_database():
    print(f"Database path: {DB_PATH}")
    print(f"CSV path: {CSV_PATH}")
    
    # Check if CSV exists
    if not CSV_PATH.exists():
        print("ERROR: destinations.csv not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Drop old table
    print("Dropping old table...")
    cur. execute("DROP TABLE IF EXISTS destinations;")
    
    # Create new table with correct schema
    print("Creating new table...")
    cur.execute("""
        CREATE TABLE destinations (
            id                  INTEGER PRIMARY KEY,
            city                TEXT NOT NULL,
            country             TEXT NOT NULL,
            continent           TEXT NOT NULL,
            iata_code           TEXT,
            latitude            REAL,
            longitude           REAL,
            avg_budget_per_day  INTEGER,
            population          TEXT,
            safety              INTEGER,
            visa_easy           INTEGER,
            english_level       INTEGER,
            climate             TEXT,
            best_months         TEXT,
            crowds              INTEGER,
            is_coastal          INTEGER,
            beach               INTEGER,
            culture             INTEGER,
            nature              INTEGER,
            food                INTEGER,
            nightlife           INTEGER,
            adventure           INTEGER,
            romance             INTEGER,
            family              INTEGER
        );
    """)
    
    # Load CSV
    print("Loading CSV...")
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        
        destinations = []
        for row in reader:
            try:
                dest = (
                    int(row["id"]),
                    row["city"],
                    row["country"],
                    row["continent"],
                    row. get("iata_code", ""),
                    float(row. get("latitude", 0)),
                    float(row.get("longitude", 0)),
                    int(row. get("avg_budget_per_day", 100)),
                    row.get("population", "medium"),
                    int(row.get("safety", 3)),
                    int(row.get("visa_easy", 1)),
                    int(row.get("english_level", 3)),
                    row.get("climate", "temperate"),
                    row.get("best_months", ""),
                    int(row.get("crowds", 3)),
                    int(row.get("is_coastal", 0)),
                    int(row.get("beach", 3)),
                    int(row.get("culture", 3)),
                    int(row.get("nature", 3)),
                    int(row.get("food", 3)),
                    int(row. get("nightlife", 3)),
                    int(row. get("adventure", 3)),
                    int(row.get("romance", 3)),
                    int(row.get("family", 3)),
                )
                destinations.append(dest)
            except (ValueError, KeyError) as e:
                print(f"  Warning: Skipping row {row. get('id', '?')}: {e}")
    
    print(f"Loaded {len(destinations)} destinations")
    
    # Insert data
    print("Inserting data...")
    cur.executemany("""
        INSERT INTO destinations (
            id, city, country, continent, iata_code,
            latitude, longitude, avg_budget_per_day, population,
            safety, visa_easy, english_level, climate, best_months,
            crowds, is_coastal, beach, culture, nature, food,
            nightlife, adventure, romance, family
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? );
    """, destinations)
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM destinations")
    count = cur.fetchone()[0]
    print(f"Total records in database: {count}")
    
    # Show sample
    cur.execute("SELECT id, city, safety, beach, culture FROM destinations LIMIT 3")
    print("\nSample data:")
    for row in cur.fetchall():
        print(f"  {row}")
    
    conn.close()
    print(f"\n✅ Done! Database saved to {DB_PATH}")
    print("Now upload travel.db to GitHub!")

if __name__ == "__main__":
    rebuild_database()