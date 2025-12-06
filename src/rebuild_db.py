"""
Script to rebuild the travel database with new schema.
Run this locally, then upload the new travel.db to GitHub.
"""

import sqlite3
import csv
from pathlib import Path

# Paths - relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "travel.db"
CSV_PATH = BASE_DIR / "data" / "destinations.csv"


def rebuild_database():
    print(f"Database path: {DB_PATH}")
    print(f"CSV path: {CSV_PATH}")
    print("=" * 60)
    
    # Check if CSV exists
    if not CSV_PATH.exists():
        print(f"ERROR: destinations.csv not found at {CSV_PATH}")
        return
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Drop old table
    print("Dropping old table...")
    cur.execute("DROP TABLE IF EXISTS destinations;")
    
    # Create new table (flight_price, NOT flight_price_zrh!)
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
            flight_price        INTEGER,
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
    
    # Load CSV with semicolon delimiter
    print("\nLoading CSV (delimiter: semicolon)...")
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        
        print(f"Columns found: {reader.fieldnames}")
        
        destinations = []
        for row in reader:
            try:
                # Get flight price from flight_price_zrh column
                fp = row.get("flight_price_zrh", "0")
                if fp == "" or fp is None:
                    flight_price = 0
                else:
                    flight_price = int(float(fp))
                
                dest = (
                    int(row["id"]),
                    row["city"],
                    row["country"],
                    row["continent"],
                    row.get("iata_code", "") or "",
                    float(row.get("latitude", 0) or 0),
                    float(row.get("longitude", 0) or 0),
                    int(row.get("avg_budget_per_day", 100) or 100),
                    flight_price,  # flight_price_zrh -> flight_price in DB
                    row.get("population", "medium") or "medium",
                    int(row.get("safety", 3) or 3),
                    int(row.get("visa_easy", 1) or 1),
                    int(row.get("english_level", 3) or 3),
                    row.get("climate", "temperate") or "temperate",
                    row.get("best_months", "") or "",
                    int(row.get("crowds", 3) or 3),
                    int(row.get("is_coastal", 0) or 0),
                    int(row.get("beach", 3) or 3),
                    int(row.get("culture", 3) or 3),
                    int(row.get("nature", 3) or 3),
                    int(row.get("food", 3) or 3),
                    int(row.get("nightlife", 3) or 3),
                    int(row.get("adventure", 3) or 3),
                    int(row.get("romance", 3) or 3),
                    int(row.get("family", 3) or 3),
                )
                destinations.append(dest)
                
                # Show first 5 rows
                if len(destinations) <= 5:
                    print(f"  ✓ {row['city']}: Flight={flight_price} CHF, Daily={row.get('avg_budget_per_day')} CHF")
                    
            except (ValueError, KeyError) as e:
                print(f"  ⚠ Skipping row {row.get('id', '?')}: {e}")
    
    print(f"\nLoaded {len(destinations)} destinations")
    
    # Insert data
    print("Inserting data...")
    cur.executemany("""
        INSERT INTO destinations (
            id, city, country, continent, iata_code,
            latitude, longitude, avg_budget_per_day, flight_price, population,
            safety, visa_easy, english_level, climate, best_months,
            crowds, is_coastal, beach, culture, nature, food,
            nightlife, adventure, romance, family
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? );
    """, destinations)
    
    conn.commit()
    
    # Verify
    print("\n" + "=" * 60)
    cur.execute("SELECT COUNT(*) FROM destinations")
    count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM destinations WHERE flight_price > 0")
    with_prices = cur.fetchone()[0]
    
    print("✈️ Sample data:")
    cur.execute("SELECT id, city, flight_price, avg_budget_per_day FROM destinations LIMIT 5")
    for row in cur.fetchall():
        print(f"  {row[1]}: Flight={row[2]} CHF, Daily={row[3]} CHF")
    
    print(f"\n📊 Total: {count} destinations")
    print(f"📊 With flight prices: {with_prices}/{count}")
    
    # Show destinations with 0 price
    cur.execute("SELECT city FROM destinations WHERE flight_price = 0")
    zero_prices = cur.fetchall()
    if zero_prices:
        print(f"\n⚠️ Destinations with 0 CHF flight price:")
        for row in zero_prices:
            print(f"  - {row[0]}")
    
    print(f"\n✅ Done! Database saved to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    rebuild_database()