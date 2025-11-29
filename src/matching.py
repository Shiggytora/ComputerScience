# We use this for the main logic of our matching feature

import streamlit as st #importing the data from the APIs to get the information in order to proceed the matching based on User inputs 
import requests
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"#takes the weather forecast over the next 14 days from the API Openmeteo 
from amadeus import Client, ResponseError #takes the flight price and the hotel price from the API Amadeus 
from src.config import get_secret

def test_matching():
    return "Test Matching successful"