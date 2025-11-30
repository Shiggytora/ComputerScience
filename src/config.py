import os
from dotenv import load_dotenv
import streamlit as st


# Returns a secret value. Works locally via .env and also online via Streamlit Secrets.

# 1. Streamlit Secrets
def get_secret(key: str):
    if key in st.secrets:
        return st.secrets[key]
    
    load_dotenv()
    return os.getenv(key)

# input1 = st.text_input("Test input")
    if input1:
        st.success(f"{input1} successful")



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