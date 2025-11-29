import streamlit as st
from src.amadeus import test_amadeus
from src.weather import get_current_weather
from typing import List, Dict, Any
from src.matching import filter_by_budget, test_locations, ranking_destinations

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


ROUNDS = 3

if "state" not in st.session_state:
    st.session_state.state = "Start"
    st.session_state.budget_matches = []
    st.session_state.id_used = []
    st.session_state.chosen = []
    st.session_state.round = 0

if st.session_state.state == "Start":

    st.subheader("Your Input")

    total_budget = st.number_input(
        "Total budget (CHF)",
        min_value=100,
        max_value=10000,
        value=2000,
    )

    trip_days = st.number_input(
        "Trip length (in days)",
        min_value=1,
        max_value=60,
        value=7
    )

    if st.button("Start Matching"):
        st.session_state.budget_matches = filter_by_budget(total_budget, trip_days)
        st.session_state.id_used = []
        st.session_state.chosen = []
        st.session_state.round = 0
        st.session_state.state = "Matching"
        st.rerun()

elif st.session_state.state == "Matching":

    st.subheader(f"Round {st.session_state.round + 1} of {ROUNDS}")

    locations = test_locations(
        st.session_state.budget_matches,
        st.session_state.id_used,
        x=3,
    )

    if not locations:
        st.error("No destinations left. Please restart")
        st.session_state.state = "Start"
        st.rerun()

    ids = [y["id"] for y in locations]

    with st.form("destination_choice_form"):
        choice = st.radio(
        "Choose one destination",
        options=ids,
        index=None,
        format_func=lambda _id: next(y["city"] for y in locations if y["id"] == _id),
        )

        for y in locations:
          st.write(f"**{y['city']}** ({y['country']}) - Rating: {y['tourist_rating']}")

        submitted = st.form_submit_button("Confirm choice")

    if submitted:
        if choice is not None:
            picked = next(y for y in locations if y["id"] == choice)
            st.session_state.chosen.append(picked)
            st.session_state.id_used.extend(ids)
            st.session_state.round += 1

            if st.session_state.round >= ROUNDS:
                st.session_state.state = "Results"
    
            else: 
                st.session_state.state = "Matching"
            
            st.rerun()
        
        else:
            st.warning("Please select a destination before confirming.")

elif st.session_state.state == "Results":
    st.subheader("Your final recommendation")

    ranked = ranking_destinations(
        st.session_state.budget_matches,
        st.session_state.chosen,
    )

    best = ranked[0]
    st.success(f"Your best match: **{best['city']}**, {best['country']}")

    st.write(best)

    if st.button("Restart"):
        st.session_state.state = "Start"
        st.rerun()
