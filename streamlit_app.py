"""
Travel Matching Application - Main Streamlit Application

This is the main entry point for the Travel Matching Recommender application.
It provides an interactive interface for users to find their ideal travel destination
based on budget, preferences, and travel style.

University Course Project - Requirements Fulfilled:
1. Problem Statement: Travel destination recommendation
2. API/Database: SQLite DB + Open-Meteo Weather API
3. Data Visualization: Progress bars, metrics, charts
4.  User Interaction: Budget input, style selection, voting
5. Machine Learning: Preference learning, similarity scoring
6.  Code Documentation: Docstrings throughout
7. Contribution Matrix: See README.md
8. Video Demo: 4-minute presentation

Authors: [Team Members]
Date: 2024
"""

import streamlit as st
from typing import List, Dict, Any

# Import custom modules
from src.matching import (
    filter_by_budget,
    test_locations,
    ranking_destinations,
    preference_vector,
    calculate_feature_ranges,
    get_match_breakdown,
    get_travel_style_weights,
    NUMERIC_FEATURES,
    FEATURE_WEIGHTS,
    TRAVEL_STYLES,
)
from src.weather_matching import enrich_destinations_with_weather
from src.insights import generate_preference_insights
from src.session_manager import export_session, get_export_filename

# =============================================================================
# CONFIGURATION
# =============================================================================

ROUNDS = 7                    # Number of matching rounds
MIN_BUDGET = 100             # Minimum budget in CHF
MAX_BUDGET = 10000           # Maximum budget in CHF
DEFAULT_BUDGET = 2000        # Default budget value
MIN_DAYS = 1                 # Minimum trip length
MAX_DAYS = 60                # Maximum trip length
DEFAULT_DAYS = 7             # Default trip length
LOCATIONS_PER_ROUND = 3      # Destinations shown per round
WEATHER_WEIGHT = 0.2         # Weight of weather in final score (20%)

# Streamlit page configuration
st.set_page_config(
    page_title="Travel Matching",
    page_icon="✈️",
    layout="centered"
)


# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def initialize_session_state():
    """
    Initializes all session state variables with default values.
    
    This ensures the application has consistent state across reruns
    and prevents KeyError exceptions when accessing state variables.
    """
    defaults = {
        "state": "Start",           # Current app state: Start, Matching, Results
        "budget_matches": [],       # Destinations matching budget
        "id_used": [],              # IDs of shown destinations
        "chosen": [],               # User's chosen destinations
        "round": 0,                 # Current matching round
        "total_budget": DEFAULT_BUDGET,
        "trip_days": DEFAULT_DAYS,
        "travel_style": "balanced", # Selected travel style
        "temp_preference": (15, 28), # Temperature range preference
        "use_weather": True,        # Whether to use weather API
        "weather_cache": {},        # Cache for weather data
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session_state():
    """Resets all session state variables to start a new session."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# =============================================================================
# MATCHING LOGIC
# =============================================================================

def get_current_round_locations() -> List[Dict[str, Any]]:
    """
    Gets destinations for the current matching round.
    
    Retrieves or generates a set of destinations for the user to choose from.
    Results are cached in session state to ensure consistency during reruns.
    
    Returns:
        List of destination dictionaries for this round
    """
    round_key = f"locations_round_{st.session_state. round}"
    
    # Return cached locations if available
    if round_key not in st.session_state or not st.session_state[round_key]:
        locations = test_locations(
            st.session_state.budget_matches,
            st.session_state.id_used,
            x=LOCATIONS_PER_ROUND,
        )
        st.session_state[round_key] = locations
    
    return st.session_state[round_key]


def process_selection(choice_id: int, locations: List[Dict[str, Any]]) -> bool:
    """
    Processes the user's destination selection. 
    
    Updates session state with the user's choice and advances
    to the next round or results page.
    
    Args:
        choice_id: ID of the selected destination
        locations: List of destinations from this round
        
    Returns:
        True if selection was successful, False otherwise
    """
    # Find the selected destination
    picked = next((loc for loc in locations if loc["id"] == choice_id), None)
    
    if picked is None:
        st.error("Selected destination not found. Please try again.")
        return False
    
    # Save the choice
    st.session_state. chosen.append(picked)
    
    # Mark all shown destinations as used
    ids = [loc["id"] for loc in locations]
    st.session_state.id_used.extend(ids)
    
    # Advance to next round
    st.session_state.round += 1
    
    # Check if matching is complete
    if st.session_state.round >= ROUNDS:
        st. session_state.state = "Results"
    else:
        st.session_state. state = "Matching"
    
    return True


# =============================================================================
# UI HELPER FUNCTIONS
# =============================================================================

def get_score_color(score: float) -> str:
    """Returns an emoji color indicator based on score value."""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"


def get_score_label(score: float) -> str:
    """Returns a descriptive label for a score value."""
    if score >= 90:
        return "Perfect Match!"
    elif score >= 80:
        return "Excellent"
    elif score >= 70:
        return "Very Good"
    elif score >= 60:
        return "Good"
    elif score >= 50:
        return "Okay"
    else:
        return "Less Compatible"


def render_destination_card(loc: Dict[str, Any], index: int):
    """
    Renders a destination card with key information.
    
    Displays destination details in a formatted card layout
    including city, country, rating, and budget.
    
    Args:
        loc: Destination dictionary
        index: Card index for unique keys
    """
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {loc['city']}")
            st. caption(f"📍 {loc['country']}")
            
            # Show current temperature if available
            if 'current_temp' in loc and loc['current_temp'] is not None:
                temp = loc['current_temp']
                st. caption(f"🌡️ Currently: {temp}°C")
        
        with col2:
            rating = loc.get('tourist_rating', 'N/A')
            st.metric("Rating", f"⭐ {rating}")
        
        with col3:
            if 'avg_budget_per_day' in loc:
                budget_value = int(loc['avg_budget_per_day'])
                st. metric("Daily Budget", f"CHF {budget_value}")
        
        st.divider()


def render_progress_bar():
    """Renders the matching progress indicator."""
    current_round = st. session_state.round
    progress = current_round / ROUNDS
    
    st.progress(progress, text=f"Progress: {current_round}/{ROUNDS} rounds completed")
    
    remaining = ROUNDS - current_round
    if remaining > 0:
        st.info(f"🎯 {remaining} round{'s' if remaining > 1 else ''} remaining until your recommendation!")


def render_match_score_display(score: float, label: str = "Match Score"):
    """
    Renders a visual match score display. 
    
    Shows the score with color coding, label, and progress bar.
    """
    color = get_score_color(score)
    score_label = get_score_label(score)
    
    st.markdown(f"### {color} {label}: {score}%")
    st.caption(score_label)
    st.progress(score / 100)


def render_score_breakdown(breakdown: Dict[str, Dict[str, Any]]):
    """
    Renders detailed breakdown of match score by feature.
    
    Shows how each feature contributed to the final score. 
    """
    # Feature name translations
    feature_names = {
        "city_size": "🏙️ City Size",
        "tourist_rating": "⭐ Tourist Rating",
        "tourist_volume_base": "👥 Tourist Volume",
        "is_coastal": "🏖️ Coastal Location",
        "climate_category": "🌡️ Climate",
        "cost_index": "💰 Cost Index",
    }
    
    for feature, data in breakdown.items():
        name = feature_names. get(feature, feature)
        similarity = data['similarity']
        color = get_score_color(similarity)
        is_inverse = data. get('is_inverse', False)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            label = name
            if is_inverse:
                label += " (inverse)"
            st.write(f"{label}")
        with col2:
            st.write(f"{color} {similarity}%")
        with col3:
            weight = data['weight']
            if abs(weight) > 2.0:
                st.caption("⬆️ Very Important")
            elif abs(weight) > 1.5:
                st. caption("⬆️ Important")
            elif abs(weight) > 1.0:
                st.caption("➡️ Medium")
            else:
                st.caption("⬇️ Less Important")


def render_insights(insights: Dict[str, Any]):
    """
    Renders user preference insights.
    
    Shows patterns detected from user's choices. 
    """
    if not insights:
        return
    
    st.subheader("🔍 What We Learned About You")
    
    # Display detected patterns
    if insights.get("patterns"):
        for pattern in insights["patterns"]:
            st.write(pattern)
    else:
        st. write("Not enough data yet to detect patterns.")
    
    # Display preference metrics
    if insights. get("preferences"):
        st.write("**Your Average Preferences:**")
        
        prefs = insights["preferences"]
        labels = {
            "city_size": "🏙️ City Size",
            "tourist_rating": "⭐ Rating",
            "is_coastal": "🏖️ Coastal",
            "cost_index": "💰 Cost",
            "climate_category": "🌡️ Climate",
        }
        
        cols = st.columns(min(len(prefs), 5))
        for i, (key, value) in enumerate(list(prefs.items())[:5]):
            with cols[i]:
                label = labels.get(key, key)
                st.metric(label, f"{value:.2f}")


# =============================================================================
# PAGE RENDERERS
# =============================================================================

def render_start_page():
    """
    Renders the start/configuration page.
    
    Allows users to set their budget, trip length, travel style,
    and temperature preferences before starting the matching process. 
    """
    st.subheader("🌍 Plan Your Trip")
    
    # Budget and Days Input
    col1, col2 = st.columns(2)
    with col1:
        total_budget = st. number_input(
            "💰 Total Budget (CHF)",
            min_value=MIN_BUDGET,
            max_value=MAX_BUDGET,
            value=st.session_state. total_budget,
            step=100,
            help="Enter your total travel budget in Swiss Francs"
        )
    with col2:
        trip_days = st.number_input(
            "📅 Trip Length (days)",
            min_value=MIN_DAYS,
            max_value=MAX_DAYS,
            value=st. session_state.trip_days,
            help="How many days will you be traveling?"
        )
    
    # Display daily budget calculation
    if trip_days > 0:
        budget_per_day = total_budget / trip_days
        st. info(f"💵 Budget per day: **CHF {budget_per_day:.2f}**")
    
    st.divider()
    
    # Travel Style Selection
    st.subheader("🎨 What's Your Travel Style? ")
    
    style_options = list(TRAVEL_STYLES.keys())
    selected_style = st.session_state.get("travel_style", "balanced")
    
    # Create style selection buttons
    cols = st.columns(len(style_options))
    for i, style_key in enumerate(style_options):
        style = TRAVEL_STYLES[style_key]
        with cols[i]:
            if st.button(
                style["name"],
                key=f"style_{style_key}",
                use_container_width=True,
                type="primary" if selected_style == style_key else "secondary"
            ):
                st.session_state.travel_style = style_key
                st.rerun()
    
    # Show selected style description
    if selected_style in TRAVEL_STYLES:
        st.caption(f"_{TRAVEL_STYLES[selected_style]['description']}_")
    
    st. divider()
    
    # Temperature Preferences
    st.subheader("🌡️ Preferred Temperature")
    
    use_weather = st. checkbox(
        "Include weather in recommendations",
        value=st.session_state.get("use_weather", True),
        help="Uses real-time weather data from Open-Meteo API"
    )
    st.session_state. use_weather = use_weather
    
    if use_weather:
        temp_col1, temp_col2 = st.columns(2)
        with temp_col1:
            min_temp = st. slider(
                "Minimum °C",
                min_value=-10,
                max_value=30,
                value=st.session_state.temp_preference[0],
            )
        with temp_col2:
            max_temp = st.slider(
                "Maximum °C",
                min_value=10,
                max_value=45,
                value=st.session_state.temp_preference[1],
            )
        st.session_state. temp_preference = (min_temp, max_temp)
        st.caption(f"Preferred temperature range: {min_temp}°C - {max_temp}°C")
    
    st.divider()
    
    # Start Button
    if st. button("🚀 Start Matching", type="primary", use_container_width=True):
        with st.spinner("Finding destinations within your budget..."):
            matches = filter_by_budget(total_budget, trip_days)
            
            if not matches:
                st.error("❌ No destinations found within your budget.  Try adjusting your parameters.")
            else:
                # Enrich with weather data if enabled
                if use_weather:
                    matches = enrich_destinations_with_weather(
                        matches,
                        st.session_state. temp_preference,
                        show_progress=True
                    )
                
                # Initialize session for matching
                st.session_state. budget_matches = matches
                st.session_state.total_budget = total_budget
                st. session_state.trip_days = trip_days
                st. session_state.id_used = []
                st.session_state.chosen = []
                st.session_state.round = 0
                st.session_state. state = "Matching"
                st.success(f"✅ Found {len(matches)} destinations!")
                st.rerun()


def render_matching_page():
    """
    Renders the interactive matching page.
    
    Shows destinations for the current round and allows users
    to select their preferred destination.
    """
    render_progress_bar()
    
    # Show current travel style
    current_style = st. session_state.get("travel_style", "balanced")
    if current_style in TRAVEL_STYLES:
        st.caption(f"Travel Style: {TRAVEL_STYLES[current_style]['name']}")
    
    current_display_round = st.session_state.round + 1
    st.subheader(f"🎲 Round {current_display_round} of {ROUNDS}")
    st.write("Select the destination that appeals to you most:")
    
    # Get destinations for this round
    locations = get_current_round_locations()
    
    if not locations:
        st.warning("⚠️ No more destinations available.  Proceeding to results...")
        st.session_state.state = "Results"
        st.rerun()
        return
    
    st.divider()
    
    # Display destination cards
    for i, loc in enumerate(locations):
        render_destination_card(loc, i)
    
    # Selection radio buttons
    ids = [loc["id"] for loc in locations]
    
    choice = st.radio(
        "**🎯 Your Choice:**",
        options=ids,
        index=None,
        key=f"round_{st.session_state. round}_choice",
        format_func=lambda _id: next(
            f"{loc['city']}, {loc['country']}"
            for loc in locations if loc["id"] == _id
        ),
        horizontal=True,
    )
    
    st.divider()
    
    # Confirmation button
    if choice is not None:
        selected = next((loc for loc in locations if loc["id"] == choice), None)
        if selected:
            st.success(f"✅ Selected: **{selected['city']}, {selected['country']}**")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            btn_text = f"✓ Confirm & Go to Round {current_display_round + 1}"
            if current_display_round >= ROUNDS:
                btn_text = "✓ Confirm & See Results"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                if process_selection(choice, locations):
                    st.rerun()
    else:
        st.warning("👆 Please select a destination above to continue")
    
    # Start over button
    st.divider()
    if st.button("← Start Over", use_container_width=False):
        reset_session_state()
        st.rerun()


def render_results_page():
    """
    Renders the results page with recommendations. 
    
    Displays the top recommended destination along with detailed
    scores, insights, and alternative options.
    """
    st.balloons()
    st.subheader("🎉 Your Perfect Destination!")
    
    travel_style = st. session_state.get("travel_style", "balanced")
    use_weather = st. session_state.get("use_weather", True)
    
    # Calculate rankings
    with st.spinner("Calculating your best match..."):
        ranked = ranking_destinations(
            st.session_state. budget_matches,
            st.session_state.chosen,
            travel_style=travel_style,
            use_weather=use_weather,
            weather_weight=WEATHER_WEIGHT,
        )
    
    if ranked:
        best = ranked[0]
        
        # Display top recommendation
        st.success(f"### 🏆 {best['city']}, {best['country']}")
        st.write("Based on your preferences, this is your ideal destination!")
        
        # Show travel style used
        if travel_style in TRAVEL_STYLES:
            st.caption(f"Based on travel style: {TRAVEL_STYLES[travel_style]['name']}")
        
        st.divider()
        
        # Score Display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            combined_score = best. get('combined_score', 0)
            render_match_score_display(combined_score, "Overall Score")
        
        with col2:
            match_score = best. get('match_score', 0)
            color = get_score_color(match_score)
            st.metric("🎯 Match Score", f"{color} {match_score}%")
            
            if use_weather:
                weather_score = best. get('weather_score', 50)
                w_color = get_score_color(weather_score)
                st.metric("🌤️ Weather Score", f"{w_color} {weather_score}%")
        
        with col3:
            rating = best.get('tourist_rating', 'N/A')
            st.metric("Tourist Rating", f"⭐ {rating}")
            
            if 'avg_budget_per_day' in best:
                total_cost = best['avg_budget_per_day'] * st.session_state.trip_days
                total_cost_rounded = round(total_cost, 2)
                st.metric("Estimated Total", f"💰 CHF {total_cost_rounded}")
            
            if 'current_temp' in best and best['current_temp'] is not None:
                st.metric("Current Weather", f"🌡️ {best['current_temp']}°C")
        
        st. divider()
        
        # Expandable Details
        with st.expander("📊 Match Score Details"):
            st.write("How well this destination matches your preferences:")
            preference = preference_vector(st.session_state. chosen)
            feature_ranges = calculate_feature_ranges(st.session_state. budget_matches)
            weights = get_travel_style_weights(travel_style)
            breakdown = get_match_breakdown(best, preference, feature_ranges, weights)
            render_score_breakdown(breakdown)
        
        with st.expander("🔍 Your Travel Insights"):
            insights = generate_preference_insights(st.session_state.chosen)
            render_insights(insights)
        
        with st.expander("📋 Your Selections During Matching"):
            for i, chosen in enumerate(st. session_state.chosen, 1):
                st.write(f"**Round {i}:** {chosen['city']}, {chosen['country']}")
        
        with st.expander("🔍 Full Destination Details"):
            st. json(best)
        
        # Alternative Options
        if len(ranked) > 1:
            st.divider()
            st.subheader("🥈 Other Great Options")
            
            for i, dest in enumerate(ranked[1:6], 2):
                combined = dest.get('combined_score', 0)
                match = dest.get('match_score', 0)
                weather = dest.get('weather_score', 50)
                color = get_score_color(combined)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{i}. ** {dest['city']}, {dest['country']}")
                with col2:
                    st.write(f"{color} {combined}%")
                with col3:
                    st.caption(f"🎯 {match}%")
                with col4:
                    if use_weather:
                        st.caption(f"🌤️ {weather}%")
                    else:
                        dest_rating = dest.get('tourist_rating', 'N/A')
                        st. caption(f"⭐ {dest_rating}")
        
        st.divider()
        
        # Action Buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Start Over", type="primary", use_container_width=True):
                reset_session_state()
                st.rerun()
        
        with col2:
            json_data = export_session(ranked)
            st. download_button(
                label="📥 Download Results",
                data=json_data,
                file_name=get_export_filename(),
                mime="application/json",
                use_container_width=True,
            )
        
        with col3:
            if st.button("🔗 Share", use_container_width=True):
                st.info("🚧 Share feature coming soon!")
    
    else:
        st. error("❌ Unable to generate recommendations. Please try again.")
        if st.button("🔄 Start Over", type="primary"):
            reset_session_state()
            st.rerun()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application entry point.
    
    Initializes session state and routes to the appropriate page
    based on current application state.
    """
    # Initialize session state
    initialize_session_state()
    
    # Application header
    st.title("✈️ Travel Matching")
    st.write("Find your perfect travel destination based on your preferences!")
    
    # Sidebar with debug info and app info
    with st.sidebar:
        st.subheader("ℹ️ About")
        st. write("This app helps you find your ideal travel destination through an interactive matching process.")
        
        st.divider()
        
        st.subheader("🔧 Session Info")
        st. write(f"State: {st.session_state.state}")
        st.write(f"Round: {st.session_state.round}/{ROUNDS}")
        st.write(f"Selections: {len(st.session_state. chosen)}")
        st.write(f"Style: {st.session_state.get('travel_style', 'balanced')}")
        st.write(f"Weather: {'On' if st.session_state.get('use_weather', True) else 'Off'}")
        
        st.divider()
        st.caption("Travel Recommender v2.0")
        st.caption("University Project 2024")
    
    # Route to appropriate page based on state
    if st.session_state.state == "Start":
        render_start_page()
    elif st.session_state.state == "Matching":
        render_matching_page()
    elif st.session_state.state == "Results":
        render_results_page()


# Run the application
if __name__ == "__main__":
    main()