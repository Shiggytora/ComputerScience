import streamlit as st
from typing import List, Dict, Any
from src.amadeus import test_amadeus
from src.weather import get_current_weather
from src.data import test_data
from src.matching import test_matching, filter_by_budget, test_locations, ranking_destinations
from src.machinelearning import test_ml
from src.visuals import test_visuals

ROUNDS = 3
MIN_BUDGET = 100
MAX_BUDGET = 10000
DEFAULT_BUDGET = 2000
MIN_DAYS = 1
MAX_DAYS = 60
DEFAULT_DAYS = 7
LOCATIONS_PER_ROUND = 3

st.set_page_config(
    page_title = "Travel Matching",
    page_icon = "⛱️",
    layout = "centered"
)

def initialize_sesion_state():
    if "state" not in st.session_state:
        st.session_state.state = "Start"
        st.session_state.budget_matches = []
        st.session_state.id_used = []
        st.session_state.chosen = []
        st.session_state.round = 0
        st.session_state.total_budget = DEFAULT_BUDGET
        st.session_state.trip_days = DEFAULT_DAYS

def main():
    initialize_sesion_state()
    st.title("Travel Matching")
    st.write("Welcome to our travel matching application")
    
    if st.session_state.state == "Start":
        st.subheader("Plan your trip")
        
        col1, col2 = st.columns(2)

        with col1:
            total_budget= st.number_input(
                "Total Budget (CHF)",
                min_value=MIN_BUDGET,
                max_value=MAX_BUDGET,
                value=DEFAULT_BUDGET,
                step=100,
                help="Enter your total travel budget in Swiss Francs"
            )

        with col2:
            trip_days = st.number_input(
                "Trip Length (days)",
                min_value=MIN_DAYS,
                max_value=MAX_DAYS,
                value=DEFAULT_DAYS,
                help="How many days will you be traveling?"
            )
        
        if trip_days > 0:
            budget_per_day = total_budget / trip_days
            st.info(f"Budget per day: **CHF {budget_per_day:.2f}**")
        
        st.divider()
        
        if st.button("Start Matching", type="primary", use_container_width=True):
            with st.spinner("Finding destinations within your budget..."):
                matches = filter_by_budget(total_budget, trip_days)
                
                if not matches:
                    st.error("No destinations found within your budget. Try adjusting your parameters.")
                else:
                    st.session_state.budget_matches = matches
                    st.session_state.total_budget = total_budget
                    st.session_state.trip_days = trip_days
                    st.session_state.id_used = []
                    st.session_state.chosen = []
                    st.session_state.round = 0
                    st.session_state.state = "Matching"
                    st.success(f"Found {len(matches)} destinations!")
                    st.rerun()
    
    elif st.session_state.state == "Matching":
        progress = st.session_state.round / ROUNDS
        st.progress(progress, text=f"Progress: {st.session_state.round}/{ROUNDS} rounds completed")
        st.subheader(f"Round {st.session_state.round + 1} of {ROUNDS}")
        st.write("Select the destination that appeals to you most:")
        
        locations = test_locations(
            st.session_state.budget_matches,
            st.session_state.id_used,
            x=LOCATIONS_PER_ROUND,
        )
        
        if not locations:
            st.warning("No more destinations available. Proceeding to results...")
            st.session_state.state = "Results"
            st.rerun()
        
        st.divider()
        
        for loc in locations:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"### {loc['city']}")
                    st.write(f"{loc['country']}")
                with col2:
                    st.metric("Rating", f"{loc.get('tourist_rating', 'N/A')}")
                with col3:
                    if 'avg_budget_per_day' in loc:
                        st.metric("Daily Budget", f"CHF {loc['avg_budget_per_day']}")
                st.divider()
        
        ids = [loc["id"] for loc in locations]
        
        choice = st.radio(
            "**Your choice:**",
            options=ids,
            index=None,
            key=f"round_{st.session_state.round}_choice",
            format_func=lambda _id: next(
                f"{loc['city']}, {loc['country']}" 
                for loc in locations if loc["id"] == _id
            ),
        )
        
        if choice is not None:
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Confirm Selection", type="primary", use_container_width=True):
                    picked = next(loc for loc in locations if loc["id"] == choice)
                    st.session_state.chosen.append(picked)
                    st.session_state.id_used.extend(ids)
                    st.session_state.round += 1
                    
                    if st.session_state.round >= ROUNDS:
                        st.session_state.state = "Results"
                    else:
                        st.session_state.state = "Matching"
                            
                    st.rerun()
        else:
            st.info("Please select a destination to continue")
    
    elif st.session_state.state == "Results":
        st.balloons()
        st.subheader("Your Perfect Destination!")
        
        with st.spinner("Calculating your best match..."):
            ranked = ranking_destinations(
                st.session_state.budget_matches,
                st.session_state.chosen,
            )
        
        if ranked:
            best = ranked [0]
            
            st.success(f"### {best['city']}, {best['country']}")
            st.write("Based on your preferences, this is your ideal destination!")
            
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tourist Rating", f"{best.get('tourist_rating', 'N/A')}")
            with col2:
                st.metric("Match Score", f"{best.get('match_score', 'N/A')}")
            with col3:
                if 'avg_budget_per_day' in best:
                    total_cost = best['avg_budget_per_day'] * st.session_state.trip_days
                    st.metric("Estimated Total", f"CHF {total_cost:.2f}")
            
            st.divider()
            
            with st.expander("See all destination details"):
                st.json(best)
            
            if len(ranked) > 1:
                st.subheader("Other Great Options:")
                for i, dest in enumerate(ranked[1:4], 2):
                    st.write(f"**{i}.** {dest['city']}, {dest['country']} - Rating: {dest.get('tourist_rating', 'N/A')}")
            
            st.divider()
        else:
            st.error("Unable to generate recommendations. Please try again.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Over", type="primary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("Save Results", use_container_width=True):
                st.info("In progress")

if __name__ == "__main__":
    main()