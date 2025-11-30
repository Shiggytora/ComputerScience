"""
Travel Matching Application - Main Streamlit Application
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
    MATCHING_FEATURES,
    DEFAULT_WEIGHTS,
    TRAVEL_STYLES,
)
from src.weather_matching import enrich_destinations_with_weather
from src.insights import generate_preference_insights
from src.session_manager import export_session, get_export_filename

# =============================================================================
# CONFIGURATION
# =============================================================================

ROUNDS = 7
MIN_BUDGET = 100
MAX_BUDGET = 15000  # Erhöht für Flugkosten
DEFAULT_BUDGET = 3000  # Erhöht für Flugkosten
MIN_DAYS = 1
MAX_DAYS = 60
DEFAULT_DAYS = 7
LOCATIONS_PER_ROUND = 3
WEATHER_WEIGHT = 0.2

st.set_page_config(
    page_title="Travel Matching",
    page_icon="✈️",
    layout="centered"
)


# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def initialize_session_state():
    """Initializes all session state variables with default values."""
    defaults = {
        "state": "Start",
        "budget_matches": [],
        "id_used": [],
        "chosen": [],
        "round": 0,
        "total_budget": DEFAULT_BUDGET,
        "trip_days": DEFAULT_DAYS,
        "travel_style": "balanced",
        "temp_preference": (15, 28),
        "use_weather": True,
        "weather_cache": {},
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
    """Gets destinations for the current matching round."""
    round_key = f"locations_round_{st.session_state.round}"
    
    if round_key not in st.session_state or not st.session_state[round_key]:
        locations = test_locations(
            st.session_state.budget_matches,
            st.session_state.id_used,
            x=LOCATIONS_PER_ROUND,
        )
        st.session_state[round_key] = locations
    
    return st.session_state[round_key]


def process_selection(choice_id: int, locations: List[Dict[str, Any]]) -> bool:
    """Processes the user's destination selection."""
    picked = next((loc for loc in locations if loc["id"] == choice_id), None)
    
    if picked is None:
        st.error("Selected destination not found.  Please try again.")
        return False
    
    st.session_state.chosen.append(picked)
    
    ids = [loc["id"] for loc in locations]
    st.session_state.id_used.extend(ids)
    
    st.session_state.round += 1
    
    if st.session_state.round >= ROUNDS:
        st.session_state.state = "Results"
    else:
        st.session_state.state = "Matching"
    
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
    """Renders a destination card with flight price."""
    with st.container():
        # Breitere Spalten für die Zahlen
        col1, col2, col3, col4 = st.columns([2.5, 1, 1.8, 1.2])
        
        with col1:
            st.markdown(f"### {loc['city']}")
            st.caption(f"📍 {loc['country']}")
            
            if 'current_temp' in loc and loc['current_temp'] is not None:
                st.caption(f"🌡️ {loc['current_temp']}°C")
        
        with col2:
            safety = loc.get('safety', 'N/A')
            st.metric("Safety", f"{safety}/5")
        
        with col3:
            # Flugpreis anzeigen
            flight = loc. get('flight_price')
            if flight:
                st.metric("✈️ Flight (Two-way in CHF)", f"{flight}")
            else:
                st.metric("✈️ Flight", "N/A")
        
        with col4:
            # Tagesbudget anzeigen
            daily = loc.get('avg_budget_per_day', 0)
            st.metric("📅 /Day (CHF)", f"{int(daily)}")
        
        st.divider()


def render_progress_bar():
    """Renders the matching progress indicator."""
    current_round = st.session_state.round
    progress = current_round / ROUNDS
    
    st.progress(progress, text=f"Progress: {current_round}/{ROUNDS} rounds completed")
    
    remaining = ROUNDS - current_round
    if remaining > 0:
        plural = "s" if remaining > 1 else ""
        st.info(f"🎯 {remaining} round{plural} remaining until your recommendation!")


def render_match_score_display(score: float, label: str = "Match Score"):
    """Renders a visual match score display."""
    color = get_score_color(score)
    score_label = get_score_label(score)
    
    st.markdown(f"### {color} {label}: {score}%")
    st.caption(score_label)
    st.progress(score / 100)


def render_score_breakdown(breakdown: Dict[str, Dict[str, Any]]):
    """Renders detailed breakdown of match score by feature."""
    feature_names = {
        "safety": "🛡️ Safety",
        "english_level": "🗣️ English Friendly",
        "crowds": "👥 Crowd Level",
        "beach": "🏖️ Beach",
        "culture": "🏛️ Culture & History",
        "nature": "🌿 Nature",
        "food": "🍽️ Food & Cuisine",
        "nightlife": "🌙 Nightlife",
        "adventure": "🏔️ Adventure",
        "romance": "💕 Romance",
        "family": "👨‍👩‍👧‍👦 Family Friendly",
        "avg_budget_per_day": "💰 Budget",
    }
    
    if not breakdown:
        st.write("No breakdown data available.")
        return
    
    for feature, data in breakdown.items():
        name = feature_names.get(feature, feature)
        similarity = data['similarity']
        color = get_score_color(similarity)
        is_inverse = data.get('is_inverse', False)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            label = name
            if is_inverse:
                label += " ↓"
            st.write(f"{label}")
        
        with col2:
            st.write(f"{color} {similarity}%")
        
        with col3:
            weight = abs(data['weight'])
            if weight >= 2.5:
                st.caption("⬆️ Very Important")
            elif weight >= 1.5:
                st.caption("⬆️ Important")
            elif weight >= 1.0:
                st.caption("➡️ Medium")
            else:
                st.caption("⬇️ Less Important")


def render_insights(insights: Dict[str, Any]):
    """Renders user preference insights."""
    if not insights:
        return
    
    st.subheader("🔍 What We Learned About You")
    
    if insights.get("patterns"):
        for pattern in insights["patterns"]:
            st.write(pattern)
    else:
        st.write("Complete more rounds to discover your travel preferences!")
    
    if insights.get("preferences"):
        st.write("**Your Average Preferences:**")
        
        prefs = insights["preferences"]
        
        labels = {
            "safety": "🛡️ Safety",
            "beach": "🏖️ Beach",
            "culture": "🏛️ Culture",
            "nature": "🌿 Nature",
            "food": "🍽️ Food",
            "nightlife": "🌙 Nightlife",
            "adventure": "🏔️ Adventure",
            "romance": "💕 Romance",
            "family": "👨‍👩‍👧‍👦 Family",
        }
        
        display_prefs = {k: v for k, v in prefs.items() if k in labels}
        
        if display_prefs:
            num_cols = min(len(display_prefs), 5)
            cols = st.columns(num_cols)
            
            for i, (key, value) in enumerate(list(display_prefs.items())[:5]):
                with cols[i]:
                    label = labels.get(key, key)
                    value_rounded = round(value, 1)
                    st.metric(label, str(value_rounded))


# =============================================================================
# PAGE RENDERERS
# =============================================================================

def render_start_page():
    """Renders the start/configuration page."""
    st.subheader("🌍 Plan Your Trip")
    
    col1, col2 = st.columns(2)
    with col1:
        total_budget = st.number_input(
            "💰 Total Budget (CHF)",
            min_value=MIN_BUDGET,
            max_value=MAX_BUDGET,
            value=st.session_state.total_budget,
            step=100,
            help="Enter your total travel budget including flights"
        )
    with col2:
        trip_days = st.number_input(
            "📅 Trip Length (days)",
            min_value=MIN_DAYS,
            max_value=MAX_DAYS,
            value=st.session_state.trip_days,
            help="How many days will you be traveling?"
        )
    
    if trip_days > 0:
        st.info(f"💵 Total budget: **CHF {total_budget}** for **{trip_days} days** (including flights)")
    
    st.divider()
    
    st.subheader("🎨 What's Your Travel Style?")
    
    style_options = list(TRAVEL_STYLES.keys())
    selected_style = st.session_state.get("travel_style", "balanced")
    
    row1_styles = style_options[:5]
    row2_styles = style_options[5:]
    
    cols1 = st.columns(len(row1_styles))
    for i, style_key in enumerate(row1_styles):
        style = TRAVEL_STYLES[style_key]
        with cols1[i]:
            btn_type = "primary" if selected_style == style_key else "secondary"
            if st.button(
                style["name"],
                key=f"style_{style_key}",
                use_container_width=True,
                type=btn_type
            ):
                st.session_state.travel_style = style_key
                st.rerun()
    
    cols2 = st.columns(len(row2_styles))
    for i, style_key in enumerate(row2_styles):
        style = TRAVEL_STYLES[style_key]
        with cols2[i]:
            btn_type = "primary" if selected_style == style_key else "secondary"
            if st.button(
                style["name"],
                key=f"style_{style_key}",
                use_container_width=True,
                type=btn_type
            ):
                st.session_state.travel_style = style_key
                st.rerun()
    
    if selected_style in TRAVEL_STYLES:
        st.caption(f"_{TRAVEL_STYLES[selected_style]['description']}_")
    
    st.divider()
    
    st.subheader("🌡️ Preferred Temperature")
    
    use_weather = st.checkbox(
        "Include weather in recommendations",
        value=st.session_state.get("use_weather", True),
        help="Uses real-time weather data from Open-Meteo API"
    )
    st.session_state.use_weather = use_weather
    
    if use_weather:
        temp_col1, temp_col2 = st.columns(2)
        with temp_col1:
            min_temp = st.slider(
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
        st.session_state.temp_preference = (min_temp, max_temp)
        st.caption(f"Preferred temperature range: {min_temp}°C - {max_temp}°C")
    
    st.divider()
    
    if st.button("🚀 Start Matching", type="primary", use_container_width=True):
        with st.spinner("Finding destinations within your budget..."):
            matches = filter_by_budget(total_budget, trip_days)
            
            if not matches:
                st.error("❌ No destinations found within your budget.  Try increasing your budget.")
            else:
                if use_weather:
                    matches = enrich_destinations_with_weather(
                        matches,
                        st.session_state.temp_preference,
                        show_progress=True
                    )
                
                st.session_state.budget_matches = matches
                st.session_state.total_budget = total_budget
                st.session_state.trip_days = trip_days
                st.session_state.id_used = []
                st.session_state.chosen = []
                st.session_state.round = 0
                st.session_state.state = "Matching"
                st.success(f"✅ Found {len(matches)} destinations!")
                st.rerun()


def render_matching_page():
    """Renders the interactive matching page."""
    render_progress_bar()
    
    current_style = st.session_state.get("travel_style", "balanced")
    if current_style in TRAVEL_STYLES:
        st.caption(f"Travel Style: {TRAVEL_STYLES[current_style]['name']}")
    
    current_display_round = st.session_state.round + 1
    st.subheader(f"🎲 Round {current_display_round} of {ROUNDS}")
    st.write("Select the destination that appeals to you most:")
    
    locations = get_current_round_locations()
    
    if not locations:
        st.warning("⚠️ No more destinations available.  Proceeding to results...")
        st.session_state.state = "Results"
        st.rerun()
        return
    
    st.divider()
    
    for i, loc in enumerate(locations):
        render_destination_card(loc, i)
    
    ids = [loc["id"] for loc in locations]
    
    choice = st.radio(
        "**🎯 Your Choice:**",
        options=ids,
        index=None,
        key=f"round_{st.session_state.round}_choice",
        format_func=lambda _id: next(
            f"{loc['city']}, {loc['country']}"
            for loc in locations if loc["id"] == _id
        ),
        horizontal=True,
    )
    
    st.divider()
    
    if choice is not None:
        selected = next((loc for loc in locations if loc["id"] == choice), None)
        if selected:
            st.success(f"✅ Selected: **{selected['city']}, {selected['country']}**")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if current_display_round >= ROUNDS:
                btn_text = "✓ Confirm & See Results"
            else:
                btn_text = f"✓ Confirm & Go to Round {current_display_round + 1}"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                if process_selection(choice, locations):
                    st.rerun()
    else:
        st.warning("👆 Please select a destination above to continue")
    
    st.divider()
    if st.button("← Start Over", use_container_width=False):
        reset_session_state()
        st.rerun()


def render_results_page():
    """Renders the results page with recommendations."""
    st.balloons()
    st.subheader("🎉 Your Perfect Destination!")
    
    travel_style = st.session_state.get("travel_style", "balanced")
    use_weather = st.session_state.get("use_weather", True)
    trip_days = st.session_state.get("trip_days", 7)
    
    with st.spinner("Calculating your best match..."):
        ranked = ranking_destinations(
            st.session_state.budget_matches,
            st.session_state.chosen,
            travel_style=travel_style,
            use_weather=use_weather,
            weather_weight=WEATHER_WEIGHT,
        )
    
    if ranked:
        best = ranked[0]
        
        st.success(f"### 🏆 {best['city']}, {best['country']}")
        st.write("Based on your preferences, this is your ideal destination!")
        
        if travel_style in TRAVEL_STYLES:
            st.caption(f"Based on travel style: {TRAVEL_STYLES[travel_style]['name']}")
        
        st.divider()
        
        # Score Display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            combined_score = best.get('combined_score', 0)
            render_match_score_display(combined_score, "Overall Score")
        
        with col2:
            match_score = best.get('match_score', 0)
            color = get_score_color(match_score)
            st.metric("🎯 Match Score", f"{color} {match_score}%")
            
            if use_weather:
                weather_score = best.get('weather_score', 50)
                w_color = get_score_color(weather_score)
                st.metric("🌤️ Weather Score", f"{w_color} {weather_score}%")
        
        with col3:
            safety = best.get('safety', 'N/A')
            st.metric("Safety Rating", f"🛡️ {safety}/5")
            
            if 'current_temp' in best and best['current_temp'] is not None:
                st.metric("Current Weather", f"🌡️ {best['current_temp']}°C")
        
        st.divider()
        
        # === NEU: Kostenaufschlüsselung ===
        st.subheader("💰 Cost Breakdown")
        
        flight_price = best.get('flight_price') or 0
        daily_budget = best.get('avg_budget_per_day') or 0
        accommodation_food = daily_budget * trip_days
        total_cost = flight_price + accommodation_food
        
        cost_col1, cost_col2, cost_col3, cost_col4 = st.columns(4)
        
        with cost_col1:
            st.metric("✈️ Flight (round-trip)", f"CHF {flight_price}")
        
        with cost_col2:
            st.metric(f"🏨 {trip_days} Days × CHF {daily_budget}", f"CHF {int(accommodation_food)}")
        
        with cost_col3:
            st.metric("💵 Total Trip Cost", f"CHF {int(total_cost)}")
        
        with cost_col4:
            remaining = st.session_state.total_budget - total_cost
            if remaining >= 0:
                st.metric("💚 Budget Remaining", f"CHF {int(remaining)}")
            else:
                st.metric("🔴 Over Budget", f"CHF {int(abs(remaining))}")
        
        st.divider()
        
        with st.expander("📊 Match Score Details"):
            st.write("How well this destination matches your preferences:")
            preference = preference_vector(st.session_state.chosen)
            feature_ranges = calculate_feature_ranges(st.session_state.budget_matches)
            weights = get_travel_style_weights(travel_style)
            breakdown = get_match_breakdown(best, preference, feature_ranges, weights)
            render_score_breakdown(breakdown)
        
        with st.expander("🔍 Your Travel Insights"):
            insights = generate_preference_insights(st.session_state.chosen)
            render_insights(insights)
        
        with st.expander("📋 Your Selections During Matching"):
            for i, chosen in enumerate(st.session_state.chosen, 1):
                st.write(f"**Round {i}:** {chosen['city']}, {chosen['country']}")
        
        with st.expander("🔍 Full Destination Details"):
            st.json(best)
        
        # Other Great Options mit Flugpreisen
        if len(ranked) > 1:
            st.divider()
            st.subheader("🥈 Other Great Options")
            
            for i, dest in enumerate(ranked[1:6], 2):
                combined = dest.get('combined_score', 0)
                match = dest.get('match_score', 0)
                flight = dest.get('flight_price') or 0
                total = dest.get('total_trip_cost') or 0
                color = get_score_color(combined)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{i}. ** {dest['city']}, {dest['country']}")
                with col2:
                    st.write(f"{color} {combined}%")
                with col3:
                    st.caption(f"✈️ CHF {flight}")
                with col4:
                    st.caption(f"💰 CHF {int(total)}")
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Start Over", type="primary", use_container_width=True):
                reset_session_state()
                st.rerun()
        
        with col2:
            json_data = export_session(ranked)
            st.download_button(
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
        st.error("❌ Unable to generate recommendations. Please try again.")
        if st.button("🔄 Start Over", type="primary"):
            reset_session_state()
            st.rerun()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application entry point."""
    initialize_session_state()
    
    st.title("✈️ Travel Matching")
    st.write("Find your perfect travel destination based on your preferences!")
    
    with st.sidebar:
        st.subheader("ℹ️ About")
        st.write("This app helps you find your ideal travel destination through an interactive matching process.")
        
        st.divider()
        
        st.subheader("🔧 Session Info")
        st.write(f"State: {st.session_state.state}")
        st.write(f"Round: {st.session_state.round}/{ROUNDS}")
        st.write(f"Selections: {len(st.session_state.chosen)}")
        st.write(f"Style: {st.session_state.get('travel_style', 'balanced')}")
        weather_status = "On" if st.session_state.get("use_weather", True) else "Off"
        st.write(f"Weather: {weather_status}")
        
        st.divider()
        st.caption("Travel Recommender v2.0")
        st.caption("CS Group 9.1")
    
    if st.session_state.state == "Start":
        render_start_page()
    elif st.session_state.state == "Matching":
        render_matching_page()
    elif st.session_state.state == "Results":
        render_results_page()


if __name__ == "__main__":
    main()