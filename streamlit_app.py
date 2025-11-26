import streamlit as st
from src.amadeus import test_amadeus
from src.weather import get_current_weather

st.set_page_config(
    page_title = "Travel Matching",
    page_icon = "⛱️",
    layout = "centered"
)

st.title("Travel Matching")
st.write("Welcome to our travel matching application")
input1 = st.text_input("Test input")
if input1:
    st.success(f"{input1} successful")

from src.data import test_data
from src.matching import test_matching
from src.machinelearning import test_ml
from src.visuals import test_visuals

st.write("Data", test_data())
st.write("Matching", test_matching())
st.write("Maching Learning", test_ml())
st.write("Visuals", test_visuals())

st.subheader("API Test: Amadeus")
if st.button("Test connect"):
    data = test_amadeus()
    st.write(data)

st.subheader("API Test: Open-Meteo")
if st.button("Weather for Barcelona"):
    weather = get_current_weather()

    if "error" in weather:
        st.error(f"Error")
    else:
        st.write("Current weather in Barcelona")
        st.metric("Temperature", f"{weather['temperature']} °C")
        st.metric("Perceived", f"{weather['apparent_temperature']} °C")
        st.metric("Humidity", f"{weather['humidity']} %")

        st.caption(f"Data from {weather['time']}")

#Budget slider 
budget_min, budget_max = st.slider(
    "Total budget (€)",
    min_value=0,
    max_value=3000,
    value=(300, 1200)
)

#Creating user preferences 
user_prefs = {
    "origin": "CDG",
    "weather_preference": get_current_weather(),
    "budget_min": budget_min,
    "budget_max": budget_max,
    "continent": continent,
    "tourism_level": tourism,
    "city_size": city_size,
    "nationality": nationality,
}

#Run the matching 
from matching import rank_destinations
results = rank_destinations(destinations, user_prefs, priorities)




