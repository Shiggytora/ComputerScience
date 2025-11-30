"""
Merges flight prices into destinations.csv
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DESTINATIONS_FILE = BASE_DIR / "data" / "destinations.csv"
FLIGHT_PRICES_FILE = BASE_DIR / "data" / "flight_prices.csv"
OUTPUT_FILE = BASE_DIR / "data" / "destinations_updated.csv"


def main():
    print("Merging flight prices into destinations...")
    
    # Load flight prices
    prices = {}
    with open(FLIGHT_PRICES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row["flight_price_zrh"]:
                prices[row["id"]] = row["flight_price_zrh"]
    
    print(f"Loaded {len(prices)} flight prices")
    
    # Read destinations and add flight prices
    with open(DESTINATIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        fieldnames = reader.fieldnames
        
        # Add flight_price_zrh if not exists
        if "flight_price_zrh" not in fieldnames:
            fieldnames = list(fieldnames) + ["flight_price_zrh"]
        
        rows = []
        for row in reader:
            row["flight_price_zrh"] = prices.get(row["id"], "")
            rows.append(row)
    
    # Write updated file
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    
    # Count
    with_prices = sum(1 for r in rows if r["flight_price_zrh"])
    
    print(f"Total destinations: {len(rows)}")
    print(f"With flight prices: {with_prices}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("\n⚠️  Rename destinations_updated.csv to destinations.csv to use it!")


if __name__ == "__main__":
    main()