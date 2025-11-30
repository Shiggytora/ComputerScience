"""
Amadeus Flight Price Fetcher

Fetches flight prices from Zurich (ZRH) to all destinations. 
Saves results to data/flight_prices.csv
"""

from amadeus import Client, ResponseError
from datetime import datetime, timedelta
import csv
import time
import os
from dotenv import load_dotenv

load_dotenv()


def get_amadeus_client():
    """Creates Amadeus API client."""
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    return Client(
        client_id=client_id,
        client_secret=client_secret,
        hostname="test"
    )


def get_flight_price(amadeus, origin: str, destination: str) -> dict:
    """Gets cheapest round-trip flight price."""
    
    departure = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    try:
        response = amadeus.shopping.flight_offers_search. get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure,
            returnDate=return_date,
            adults=1,
            currencyCode="CHF",
            max=3
        )
        
        if response. data:
            cheapest = min(response.data, key=lambda x: float(x['price']['total']))
            return {
                "success": True,
                "price": int(float(cheapest['price']['total']))
            }
        return {"success": False, "price": None}
        
    except ResponseError as e:
        print(f"API Error: {e}")
        return {"success": False, "price": None}


def fetch_all_flight_prices():
    """Main function - fetches prices for all destinations."""
    
    # Alle 60 Destinationen mit IATA Codes (korrigiert)
    destinations = [
        {"id": 1, "city": "Barcelona", "iata": "BCN"},
        {"id": 2, "city": "Paris", "iata": "CDG"},
        {"id": 3, "city": "London", "iata": "LHR"},
        {"id": 4, "city": "Rome", "iata": "FCO"},
        {"id": 5, "city": "Amsterdam", "iata": "AMS"},
        {"id": 6, "city": "Prague", "iata": "PRG"},
        {"id": 7, "city": "Lisbon", "iata": "LIS"},
        {"id": 8, "city": "Berlin", "iata": "BER"},
        {"id": 9, "city": "Vienna", "iata": "VIE"},
        {"id": 10, "city": "Copenhagen", "iata": "CPH"},
        {"id": 11, "city": "Dublin", "iata": "DUB"},
        {"id": 12, "city": "Reykjavik", "iata": "KEF"},
        {"id": 13, "city": "Dubrovnik", "iata": "DBV"},
        {"id": 14, "city": "Santorini", "iata": "JTR"},
        {"id": 15, "city": "Budapest", "iata": "BUD"},
        {"id": 16, "city": "Edinburgh", "iata": "EDI"},
        {"id": 17, "city": "Stockholm", "iata": "ARN"},
        {"id": 18, "city": "Zurich", "iata": "ZRH"},
        {"id": 19, "city": "Nice", "iata": "NCE"},
        {"id": 20, "city": "Munich", "iata": "MUC"},
        {"id": 21, "city": "Tokyo", "iata": "NRT"},
        {"id": 22, "city": "Bangkok", "iata": "BKK"},
        {"id": 23, "city": "Singapore", "iata": "SIN"},
        {"id": 24, "city": "Bali", "iata": "DPS"},
        {"id": 25, "city": "Seoul", "iata": "ICN"},
        {"id": 26, "city": "Hong_Kong", "iata": "HKG"},
        {"id": 27, "city": "Kyoto", "iata": "KIX"},
        {"id": 28, "city": "Vietnam_Hanoi", "iata": "HAN"},
        {"id": 29, "city": "Phuket", "iata": "HKT"},
        {"id": 30, "city": "Dubai", "iata": "DXB"},
        {"id": 31, "city": "Maldives", "iata": "MLE"},
        {"id": 32, "city": "New_York", "iata": "JFK"},
        {"id": 33, "city": "Los_Angeles", "iata": "LAX"},
        {"id": 34, "city": "Miami", "iata": "MIA"},
        {"id": 35, "city": "Vancouver", "iata": "YVR"},
        {"id": 36, "city": "Mexico_City", "iata": "MEX"},
        {"id": 37, "city": "Cancun", "iata": "CUN"},
        {"id": 38, "city": "Havana", "iata": "HAV"},
        {"id": 39, "city": "Costa_Rica", "iata": "SJO"},
        {"id": 40, "city": "Toronto", "iata": "YYZ"},
        {"id": 41, "city": "Sydney", "iata": "SYD"},
        {"id": 42, "city": "Melbourne", "iata": "MEL"},
        {"id": 43, "city": "Auckland", "iata": "AKL"},
        {"id": 44, "city": "Queenstown", "iata": "ZQN"},
        {"id": 45, "city": "Fiji", "iata": "NAN"},
        {"id": 46, "city": "Cape_Town", "iata": "CPT"},
        {"id": 47, "city": "Marrakech", "iata": "RAK"},
        {"id": 48, "city": "Cairo", "iata": "CAI"},
        {"id": 49, "city": "Zanzibar", "iata": "ZNZ"},
        {"id": 50, "city": "Mauritius", "iata": "MRU"},
        {"id": 51, "city": "Rio_de_Janeiro", "iata": "GIG"},
        {"id": 52, "city": "Buenos_Aires", "iata": "EZE"},
        {"id": 53, "city": "Cusco", "iata": "CUZ"},
        {"id": 54, "city": "Cartagena", "iata": "CTG"},
        {"id": 55, "city": "Patagonia", "iata": "FTE"},
        {"id": 56, "city": "Galapagos", "iata": "GPS"},
        {"id": 57, "city": "Machu_Picchu", "iata": "CUZ"},
        {"id": 58, "city": "Petra", "iata": "AMM"},
        {"id": 59, "city": "Seychelles", "iata": "SEZ"},
        {"id": 60, "city": "Amalfi_Coast", "iata": "NAP"},
    ]
    
    print("=" * 60)
    print("FLIGHT PRICE FETCHER")
    print("From: Zurich (ZRH)")
    print("=" * 60 + "\n")
    
    amadeus = get_amadeus_client()
    results = []
    
    for dest in destinations:
        city = dest["city"]
        iata = dest["iata"]
        
        print(f"[{dest['id']:2d}/60] {city:20s} ({iata})...   ", end="", flush=True)
        
        if iata == "ZRH":
            print("SKIP (origin)")
            results.append({"id": dest["id"], "city": city, "iata": iata, "price": 0})
            continue
        
        price_info = get_flight_price(amadeus, "ZRH", iata)
        
        if price_info["success"]:
            print(f"CHF {price_info['price']}")
            results.append({"id": dest["id"], "city": city, "iata": iata, "price": price_info["price"]})
        else:
            print("FAILED")
            results. append({"id": dest["id"], "city": city, "iata": iata, "price": ""})
        
        time.sleep(0.5)
    
    # Save to CSV
    output_file = "data/flight_prices. csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv. DictWriter(f, fieldnames=["id", "city", "iata", "price"], delimiter=';')
        writer.writeheader()
        writer.writerows(results)
    
    # Summary
    successful = sum(1 for r in results if r["price"] and r["price"] != 0)
    print("\n" + "=" * 60)
    print(f"DONE!  Saved to {output_file}")
    print(f"Successful: {successful}/60")
    print("=" * 60)


if __name__ == "__main__":
    fetch_all_flight_prices()