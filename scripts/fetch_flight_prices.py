"""
Fetches flight prices from Zurich to all destinations. 
Run once, then merge into destinations.csv
"""

import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

# Configuration
ORIGIN = "ZRH"

# KORRIGIERT: Direkter Pfad zu deinem Ordner
BASE_DIR = Path("C:/Users/Jan Linsen/ComputerScience")
DESTINATIONS_FILE = Path("C:/Users/Jan Linsen/ComputerScience/data/destinations.csv")
OUTPUT_FILE = Path("C:/Users/Jan Linsen/ComputerScience/data/flight_prices.csv")


def get_amadeus_client():
    """Creates Amadeus API client."""
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERROR: AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET not found in .env")
        sys.exit(1)
    
    return Client(
        client_id=client_id,
        client_secret=client_secret,
        hostname="test"
    )


def get_cheapest_flight(amadeus, destination_iata: str, departure_date: str) -> dict:
    """Gets cheapest round-trip flight price."""
    try:
        return_date = (datetime.strptime(departure_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=ORIGIN,
            destinationLocationCode=destination_iata,
            departureDate=departure_date,
            returnDate=return_date,
            adults=1,
            currencyCode="CHF",
            max=3
        )
        
        if response.data:
            cheapest = min(response.data, key=lambda x: float(x['price']['total']))
            return {
                "success": True,
                "price": int(float(cheapest['price']['total'])),
            }
        return {"success": False, "error": "No flights"}
        
    except ResponseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("=" * 60)
    print("FLIGHT PRICE FETCHER")
    print(f"Origin: {ORIGIN} (Zurich)")
    print("=" * 60)
    
    # Check if file exists
    if not DESTINATIONS_FILE.exists():
        print(f"ERROR: File not found: {DESTINATIONS_FILE}")
        sys.exit(1)
    
    # Load destinations
    destinations = []
    with open(DESTINATIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        destinations = list(reader)
    
    print(f"Loaded {len(destinations)} destinations\n")
    
    # Setup
    amadeus = get_amadeus_client()
    departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"Search date: {departure_date} (30 days from now)\n")
    
    # Fetch prices
    results = []
    successful = 0
    failed = 0
    
    for i, dest in enumerate(destinations):
        city = dest["city"]
        iata = dest.get("iata_code", "")
        
        print(f"[{i+1:2d}/{len(destinations)}] {city:20s} ({iata})...  ", end="", flush=True)
        
        if not iata or len(iata) != 3:
            print("SKIP (no IATA)")
            results.append({"id": dest["id"], "flight_price_zrh": ""})
            failed += 1
            continue
        
        price_info = get_cheapest_flight(amadeus, iata, departure_date)
        
        if price_info["success"]:
            print(f"CHF {price_info['price']}")
            results.append({"id": dest["id"], "flight_price_zrh": price_info["price"]})
            successful += 1
        else:
            print(f"FAILED ({price_info['error'][:30]})")
            results.append({"id": dest["id"], "flight_price_zrh": ""})
            failed += 1
        
        time.sleep(0.3)  # Rate limiting
    
    # Save results
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "flight_price_zrh"], delimiter=';')
        writer.writeheader()
        writer.writerows(results)
    
    # Summary
    print("\n" + "=" * 60)
    print("DONE!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()