#We use this for the Amadeus Travel API

from amadeus import Client, ResponseError
from src.config import get_secret

def get_amadeus_client():
    client_id = get_secret("AMADEUS_CLIENT_ID")
    client_secret = get_secret("AMADEUS_CLIENT_SECRET")

    return Client(
        client_id=client_id,
        client_secret=client_secret,
        hostname="test"
    )

 

def test_amadeus():
    amadeus = get_amadeus_client()
    try:
        response = amadeus.reference_data.locations.get(keyword="Zurich", subType="AIRPORT")
        return response.data
    except ResponseError as error:
        return str(error)