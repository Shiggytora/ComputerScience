import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "travel.db"

DESTINATIONS = [
    (
        1,  # Id of the destination
        "Singapore", # Name of the city
        "Singapore", # Name of the country
        "Asia", # Name of the continent the city & country is in
        "SIN", # IATA-Code of the city
        1.3521, # Latitude of the city
        103.8198, # Longitude of the city
        180, # The average Budget per day you need for this city 
        4.7, # City size (5 = insanely big city, 3 = midsize city, 1 = small city)
        4.7, # Tourist rating (5 = excellent rating given by tourists, 3 = mid rating given by tourists, 1 = bad rating given by tourists)
        4.5, # Tourist volume base (5 = high amount of tourism, 3 = moderate amount of tourism, 1 = nearly no tourism)
        1.0, # Coastel (1 = coast, 0.5 = near the coast, 0 = not coastel)
        4.1, # Climate (5 = hot/extreme, 3 = mild/normal, 1 = cold)
        0.9, # Cost index (1 = expensive, 0 = cheap)
    ),
    (
        2, 
        "Madrid",
        "Spain", 
        "Europe", 
        "MAD", 
        40.4168,
        -3.7039,
        110, 
        4.1, 
        4.5,
        3.3, 
        0.0, 
        3.8,
        0.6, 
    ), (
        3, 
        "Copenhagen",
        "Denmark", 
        "Europe", 
        "CPH", 
        55.6761,
        12.5683,
        150, 
        2.6, 
        4.6,
        3.1, 
        1.0, 
        2.4,
        0.8, 
    ),
]

def create_db():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("Drop table if exists destinations;")

    cur.execute(
        """
        Create table destinations (
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
        DESTINATIONS,
    )

    conn.commit()
    conn.close()
    print(f"created {DB_PATH} with {len(DESTINATIONS)} destinations")

if __name__ == "__main__":
    create_db()