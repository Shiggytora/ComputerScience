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
        st.error("Error")
    else:
        st.write("Current weather in Barcelona")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Temperature", "{weather['temperature']} °C")
            st.metric("Perceived", "{weather['apparent_temperature']} °C")
        with col2:
            st.metric("Humidity", "{weather['humidity']} %")
            st.metric("Wind Speed", "{weather['wind_speed]} km/h")
        st.caption("Data from {weather['time']}")