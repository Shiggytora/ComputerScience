"""
Travel Matching Application - Main Streamlit Application
"""

import streamlit as st
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Import custom modules
from src.matching import (
    filter_by_budget,
    test_locations,
    ranking_destinations,
    preference_vector,
    calculate_feature_ranges,
    get_match_breakdown,
    get_travel_style_weights,
    find_similar_destinations,
    calculate_recommendation_confidence,
    TRAVEL_STYLES,
)
from src.weather_matching import (
    enrich_destinations_with_weather,
    enrich_destinations_with_forecast,
)
from src.insights import generate_preference_insights
from src.session_manager import (
    export_session,
    get_export_filename,
    create_share_data,
    encode_share_data,
    parse_shared_results,
)
from src.visuals import (
    create_preference_radar_chart,
    create_comparison_radar_chart,
    create_score_breakdown_chart,
    create_top_destinations_chart,
    create_budget_comparison_chart,
    create_weather_score_chart,
    create_score_gauge,
    create_destinations_map,
    create_route_map,
    FEATURE_CONFIG,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

ROUNDS = 7
MIN_BUDGET = 100
MAX_BUDGET = 15000
DEFAULT_BUDGET = 3000
MIN_DAYS = 1
MAX_DAYS = 60
DEFAULT_DAYS = 7
MIN_TRAVELERS = 1
MAX_TRAVELERS = 10
DEFAULT_TRAVELERS = 1
LOCATIONS_PER_ROUND = 3
WEATHER_WEIGHT = 0.2
MAX_DESTINATIONS = 50

DEFAULT_ORIGIN = {
    "city": "Zurich",
    "latitude": 47.3769,
    "longitude": 8.5417
}

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
        "num_travelers": DEFAULT_TRAVELERS,
        "travel_style": "balanced",
        "temp_preference": (15, 28),
        "use_weather": True,
        "weather_cache": {},
        "travel_date_start": None,
        "travel_date_end": None,
        "use_forecast": False,
        "show_share_modal": False,
        "share_url": "",
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
    """Gets destinations for the current matching round (random selection)."""
    round_key = f"locations_round_{st.session_state.round}"
    
    if round_key not in st.session_state or not st.session_state[round_key]:
        locations = test_locations(
            st.session_state.budget_matches,
            st.session_state.id_used,
            x=LOCATIONS_PER_ROUND,
        )
        st.session_state[round_key] = locations
    
    return st.session_state[round_key]


def get_smart_round_locations() -> List[Dict[str, Any]]:
    """
    Gets destinations for the current round with smart selection.
    
    Rounds 1-3: Random selection (exploration phase)
    Rounds 4+: Prioritizes destinations that match learned preferences
    """
    current_round = st.session_state.round
    round_key = f"locations_round_{current_round}"
    
    if round_key in st.session_state and st.session_state[round_key]:
        return st.session_state[round_key]
    
    available = [
        d for d in st.session_state.budget_matches 
        if d["id"] not in st.session_state.id_used
    ]
    
    if not available:
        return []
    
    if current_round < 3 or len(st.session_state.chosen) < 3:
        if len(available) <= LOCATIONS_PER_ROUND:
            locations = available
        else:
            locations = random.sample(available, LOCATIONS_PER_ROUND)
    else:
        travel_style = st.session_state.get("travel_style", "balanced")
        use_weather = st.session_state.get("use_weather", True)
        
        ranked = ranking_destinations(
            available,
            st.session_state.chosen,
            travel_style=travel_style,
            use_weather=use_weather,
            weather_weight=WEATHER_WEIGHT,
        )
        
        if len(ranked) <= LOCATIONS_PER_ROUND:
            locations = ranked
        else:
            top_pool = ranked[:10]
            selected_top = random.sample(top_pool, min(2, len(top_pool)))
            remaining = [d for d in ranked if d not in selected_top]
            if remaining:
                selected_other = random.sample(remaining, 1)
            else:
                selected_other = []
            
            locations = selected_top + selected_other
            random.shuffle(locations)
    
    st.session_state[round_key] = locations
    return locations


def process_selection(choice_id: int, locations: List[Dict[str, Any]]) -> bool:
    """Processes the user's destination selection."""
    picked = next((loc for loc in locations if loc["id"] == choice_id), None)
    
    if picked is None:
        st.error("Selected destination not found. Please try again.")
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
    """Renders a destination card with flight price and weather info."""
    with st.container():
        col1, col2, col3 = st.columns([3, 1.5, 1.2])
        
        with col1:
            st.markdown(f"### {loc['city']}")
            st.caption(f"📍 {loc['country']}")
            
            if loc.get('forecast_temp') is not None:
                st.caption(f"🌡️ Forecast: {loc['forecast_temp']}°C")
                if loc.get('rain_days', 0) > 0:
                    st.caption(f"🌧️ {loc['rain_days']} rainy days expected")
            elif loc.get('current_temp') is not None:
                st.caption(f"🌡️ Now: {loc['current_temp']}°C")
        
        with col2:
            flight = loc.get('flight_price')
            if flight:
                st.metric("✈️ Flight/Person", f"{flight} CHF")
            else:
                st.metric("✈️ Flight", "N/A")
        
        with col3:
            daily = loc.get('avg_budget_per_day', 0)
            st.metric("📅 /Day/Person", f"{int(daily)} CHF")
        
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


def render_confidence_display(confidence_data: Dict[str, Any]):
    """Renders the recommendation confidence indicator."""
    confidence = confidence_data.get('confidence', 0)
    label = confidence_data.get('label', 'Unknown')
    emoji = confidence_data.get('emoji', '❓')
    recommendation = confidence_data.get('recommendation', '')
    gap = confidence_data.get('gap_to_second', 0)
    
    st.markdown(f"### {emoji} Recommendation Confidence: {label}")
    st.progress(confidence / 100)
    st.caption(f"Score gap to #2: {gap} points")
    st.info(f"💡 {recommendation}")


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


def render_similar_destinations(
    similar: List[Dict[str, Any]], 
    ranked: List[Dict[str, Any]],
    num_travelers: int, 
    trip_days: int
):
    """Renders the similar destinations section with correct scores."""
    if not similar:
        return
    
    score_lookup = {d.get('id'): d.get('combined_score', 0) for d in ranked}
    
    st.subheader("🔄 Similar Destinations You Might Like")
    st.caption("These destinations have a similar profile to your top match")
    
    for dest in similar:
        similarity = dest.get('similarity_score', 0)
        city = dest.get('city', 'Unknown')
        country = dest.get('country', '')
        flight = dest.get('flight_price') or 0
        daily = dest.get('avg_budget_per_day') or 0
        
        dest_id = dest.get('id')
        combined = score_lookup.get(dest_id, dest.get('combined_score', 0))
        
        total = (flight * num_travelers) + (daily * trip_days * num_travelers)
        
        col1, col2, col3, col4 = st.columns([3, 1.2, 1, 1])
        
        with col1:
            st.write(f"**{city}, {country}**")
            st.caption(f"🔄 {similarity}% similar to your top match")
        
        with col2:
            color = get_score_color(combined)
            st.write(f"{color} {combined}%")
            st.caption("Match Score")
        
        with col3:
            st.write(f"✈️ CHF {flight * num_travelers}")
            st.caption("Flights")
        
        with col4:
            st.write(f"💰 CHF {int(total)}")
            st.caption("Total")
    
    st.divider()


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
            help="Enter your total travel budget including flights for ALL travelers"
        )
    with col2:
        num_travelers = st.number_input(
            "👥 Number of Travelers",
            min_value=MIN_TRAVELERS,
            max_value=MAX_TRAVELERS,
            value=st.session_state.num_travelers,
            help="How many people are traveling?"
        )
    
    st.divider()
    
    st.subheader("📅 Travel Dates")
    
    date_col1, date_col2 = st.columns(2)
    
    with date_col1:
        default_start = datetime.now() + timedelta(days=14)
        travel_date_start = st.date_input(
            "Departure Date",
            value=default_start,
            min_value=datetime.now().date(),
            max_value=datetime.now().date() + timedelta(days=365),
            help="When do you plan to start your trip?"
        )
    
    with date_col2:
        default_end = travel_date_start + timedelta(days=DEFAULT_DAYS)
        travel_date_end = st.date_input(
            "Return Date",
            value=default_end,
            min_value=travel_date_start + timedelta(days=1),
            max_value=travel_date_start + timedelta(days=MAX_DAYS),
            help="When do you plan to return?"
        )
    
    trip_days = (travel_date_end - travel_date_start).days
    
    travelers_text = "person" if num_travelers == 1 else "people"
    days_text = "day" if trip_days == 1 else "days"
    st.info(f"💵 **CHF {total_budget}** total budget for **{num_travelers} {travelers_text}** over **{trip_days} {days_text}** (including flights)")
    
    days_until_travel = (travel_date_start - datetime.now().date()).days
    
    if days_until_travel <= 16 and days_until_travel >= 0:
        st.success("✅ Weather forecast available for your travel dates!")
    elif days_until_travel > 16:
        st.warning(f"⚠️ Travel date is {days_until_travel} days away. Using current weather data as estimate.")
    
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
    
    if row2_styles:
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
        help="Uses weather forecast or current data from Open-Meteo API"
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
            matches = filter_by_budget(total_budget, trip_days, num_travelers)
            
            if not matches:
                st.error("❌ No destinations found within your budget. Try increasing your budget or reducing travelers.")
            else:
                if len(matches) > MAX_DESTINATIONS:
                    matches = matches[:MAX_DESTINATIONS]
                
                days_until = (travel_date_start - datetime.now().date()).days
                can_use_forecast = 0 <= days_until <= 16
                
                if use_weather:
                    start_str = travel_date_start.strftime("%Y-%m-%d")
                    end_str = travel_date_end.strftime("%Y-%m-%d")
                    
                    if can_use_forecast:
                        matches = enrich_destinations_with_forecast(
                            matches,
                            st.session_state.temp_preference,
                            start_str,
                            end_str,
                            show_progress=True
                        )
                        st.session_state.use_forecast = True
                    else:
                        matches = enrich_destinations_with_weather(
                            matches,
                            st.session_state.temp_preference,
                            show_progress=True
                        )
                        st.session_state.use_forecast = False
                else:
                    st.session_state.use_forecast = False
                
                st.session_state.budget_matches = matches
                st.session_state.total_budget = total_budget
                st.session_state.trip_days = trip_days
                st.session_state.num_travelers = num_travelers
                st.session_state.travel_date_start = travel_date_start
                st.session_state.travel_date_end = travel_date_end
                st.session_state.id_used = []
                st.session_state.chosen = []
                st.session_state.round = 0
                st.session_state.state = "Matching"
                
                travelers_text = "traveler" if num_travelers == 1 else "travelers"
                weather_info = "with forecast" if st.session_state.use_forecast else "with current weather"
                st.success(f"✅ Found {len(matches)} destinations for {num_travelers} {travelers_text} {weather_info}!")
                st.rerun()


def render_matching_page():
    """Renders the interactive matching page."""
    render_progress_bar()
    
    current_style = st.session_state.get("travel_style", "balanced")
    num_travelers = st.session_state.get("num_travelers", 1)
    travel_date = st.session_state.get("travel_date_start")
    use_forecast = st.session_state.get("use_forecast", False)
    
    if current_style in TRAVEL_STYLES:
        travelers_text = "traveler" if num_travelers == 1 else "travelers"
        info_text = f"Travel Style: {TRAVEL_STYLES[current_style]['name']} | 👥 {num_travelers} {travelers_text}"
        if travel_date:
            info_text += f" | 📅 {travel_date.strftime('%b %d, %Y')}"
        if use_forecast:
            info_text += " | 🌤️ Forecast"
        st.caption(info_text)
    
    current_display_round = st.session_state.round + 1
    st.subheader(f"🎲 Round {current_display_round} of {ROUNDS}")
    st.write("Select the destination that appeals to you most:")
    
    locations = get_smart_round_locations()
    
    if not locations:
        st.warning("⚠️ No more destinations available. Proceeding to results...")
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
    num_travelers = st.session_state.get("num_travelers", 1)
    travel_date_start = st.session_state.get("travel_date_start")
    travel_date_end = st.session_state.get("travel_date_end")
    use_forecast = st.session_state.get("use_forecast", False)
    
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
            travelers_text = "traveler" if num_travelers == 1 else "travelers"
            info_text = f"Travel style: {TRAVEL_STYLES[travel_style]['name']} | 👥 {num_travelers} {travelers_text}"
            if travel_date_start and travel_date_end:
                info_text += f" | 📅 {travel_date_start.strftime('%b %d')} - {travel_date_end.strftime('%b %d, %Y')}"
            if use_forecast:
                info_text += " | 🌤️ Using weather forecast"
            st.caption(info_text)
        
        st.divider()
        
        confidence_data = calculate_recommendation_confidence(ranked)
        render_confidence_display(confidence_data)
        
        st.divider()
        
        st.subheader("🗺️ Your Destinations on the Map")
        
        map_tab1, map_tab2 = st.tabs(["🌍 Top 5 Matches", "✈️ Your Journey"])
        
        with map_tab1:
            destinations_map = create_destinations_map(
                ranked[:5],
                highlight_best=True,
                title="Top 5 Matching Destinations"
            )
            if destinations_map:
                st.plotly_chart(destinations_map, use_container_width=True)
                st.caption("🥇 Gold = Best match | Larger markers = Higher scores")
        
        with map_tab2:
            route_map = create_route_map(
                DEFAULT_ORIGIN,
                best,
                title=f"Zurich → {best['city']}, {best['country']}"
            )
            if route_map:
                st.plotly_chart(route_map, use_container_width=True)
        
        st.divider()
        
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
                weather_label = "🌤️ Forecast Score" if use_forecast else "🌤️ Weather Score"
                st.metric(weather_label, f"{w_color} {weather_score}%")
        
        with col3:
            safety = best.get('safety', 'N/A')
            st.metric("Safety Rating", f"🛡️ {safety}/5")
            
            if use_forecast and best.get('forecast_temp') is not None:
                st.metric("📅 Forecast Temp", f"🌡️ {best['forecast_temp']}°C")
                if best.get('forecast_min') and best.get('forecast_max'):
                    st.caption(f"Range: {best['forecast_min']}°C - {best['forecast_max']}°C")
            elif best.get('current_temp') is not None:
                st.metric("Current Weather", f"🌡️ {best['current_temp']}°C")
        
        if use_forecast and best.get('rain_days', 0) > 0:
            total_days = best.get('total_days', trip_days)
            rain_pct = (best['rain_days'] / total_days) * 100
            if rain_pct > 50:
                st.warning(f"🌧️ Expect rain on {best['rain_days']} of {total_days} days ({rain_pct:.0f}%)")
            else:
                st.info(f"🌧️ Light rain expected on {best['rain_days']} of {total_days} days")
        
        st.divider()
        
        st.subheader("💰 Cost Breakdown")
        
        flight_price = best.get('flight_price') or 0
        daily_budget = best.get('avg_budget_per_day') or 0
        
        flight_total = flight_price * num_travelers
        accommodation_food = daily_budget * trip_days * num_travelers
        total_cost = flight_total + accommodation_food
        
        if num_travelers > 1:
            st.info(f"💡 Costs calculated for **{num_travelers} travelers** over **{trip_days} days**")
        
        cost_col1, cost_col2, cost_col3, cost_col4 = st.columns(4)
        
        with cost_col1:
            if num_travelers > 1:
                st.metric(
                    "✈️ Flights (round-trip)", 
                    f"CHF {int(flight_total)}",
                    help=f"CHF {flight_price} × {num_travelers} travelers"
                )
            else:
                st.metric("✈️ Flight (round-trip)", f"CHF {flight_price}")
        
        with cost_col2:
            if num_travelers > 1:
                st.metric(
                    "🏨 Accommodation & Food",
                    f"CHF {int(accommodation_food)}",
                    help=f"CHF {daily_budget}/day × {trip_days} days × {num_travelers} travelers"
                )
            else:
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
        
        similar_destinations = find_similar_destinations(
            best,
            st.session_state.budget_matches,
            num_similar=3
        )
        
        if similar_destinations:
            render_similar_destinations(similar_destinations, ranked, num_travelers, trip_days)
        
        st.subheader("📊 Visual Insights")
        
        preference = preference_vector(st.session_state.chosen)
        feature_ranges = calculate_feature_ranges(st.session_state.budget_matches)
        weights = get_travel_style_weights(travel_style)
        breakdown = get_match_breakdown(best, preference, feature_ranges, weights)
        
        viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
            "🎯 Preference Profile", 
            "📈 Score Breakdown", 
            "🏆 Top Destinations",
            "💰 Budget & Weather"
        ])
        
        with viz_tab1:
            radar_fig = create_preference_radar_chart(
                preference, 
                title="Your Travel Preference Profile"
            )
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
            
            st.write("---")
            st.write("**How does your top match compare? **")
            
            dest_values = {
                k: best.get(k, 0) 
                for k in FEATURE_CONFIG.keys() 
                if best.get(k) is not None
            }
            comparison_fig = create_comparison_radar_chart(
                preference,
                dest_values,
                destination_name=f"{best['city']}, {best['country']}",
                title="Your Preferences vs Top Destination"
            )
            if comparison_fig:
                st.plotly_chart(comparison_fig, use_container_width=True)
        
        with viz_tab2:
            breakdown_fig = create_score_breakdown_chart(
                breakdown,
                title=f"Why {best['city']} Matches You"
            )
            if breakdown_fig:
                st.plotly_chart(breakdown_fig, use_container_width=True)
            
            st.write("---")
            gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
            
            with gauge_col1:
                overall_gauge = create_score_gauge(
                    best.get('combined_score', 0),
                    title="Overall Score"
                )
                if overall_gauge:
                    st.plotly_chart(overall_gauge, use_container_width=True)
            
            with gauge_col2:
                match_gauge = create_score_gauge(
                    best.get('match_score', 0),
                    title="Match Score"
                )
                if match_gauge:
                    st.plotly_chart(match_gauge, use_container_width=True)
            
            with gauge_col3:
                if use_weather:
                    weather_gauge = create_score_gauge(
                        best.get('weather_score', 50),
                        title="Weather Score"
                    )
                    if weather_gauge:
                        st.plotly_chart(weather_gauge, use_container_width=True)
        
        with viz_tab3:
            top_dest_fig = create_top_destinations_chart(
                ranked,
                num_destinations=7,
                title="Top 7 Matching Destinations"
            )
            if top_dest_fig:
                st.plotly_chart(top_dest_fig, use_container_width=True)
        
        with viz_tab4:
            budget_fig = create_budget_comparison_chart(
                ranked,
                st.session_state.total_budget,
                num_travelers,
                trip_days,
                num_destinations=5,
                title="Cost Breakdown by Destination"
            )
            if budget_fig:
                st.plotly_chart(budget_fig, use_container_width=True)
            
            if use_weather:
                st.write("---")
                weather_fig = create_weather_score_chart(
                    ranked,
                    num_destinations=5,
                    title="Weather Compatibility Scores"
                )
                if weather_fig:
                    st.plotly_chart(weather_fig, use_container_width=True)
        
        st.divider()
        
        with st.expander("📊 Match Score Details (Text)"):
            st.write("How well this destination matches your preferences:")
            render_score_breakdown(breakdown)
        
        with st.expander("🔍 Your Travel Insights"):
            insights = generate_preference_insights(st.session_state.chosen)
            render_insights(insights)
        
        with st.expander("📋 Your Selections During Matching"):
            for i, chosen in enumerate(st.session_state.chosen, 1):
                st.write(f"**Round {i}:** {chosen['city']}, {chosen['country']}")
        
        with st.expander("🔍 Full Destination Details"):
            st.json(best)
        
        if len(ranked) > 1:
            st.divider()
            st.subheader("🥈 Other Great Options")
            
            for i, dest in enumerate(ranked[1:6], 2):
                combined = dest.get('combined_score', 0)
                flight = dest.get('flight_price') or 0
                daily = dest.get('avg_budget_per_day') or 0
                
                total = (flight * num_travelers) + (daily * trip_days * num_travelers)
                color = get_score_color(combined)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{i}.** {dest['city']}, {dest['country']}")
                with col2:
                    st.write(f"{color} {combined}%")
                with col3:
                    if num_travelers > 1:
                        st.caption(f"✈️ CHF {flight * num_travelers}")
                    else:
                        st.caption(f"✈️ CHF {flight}")
                with col4:
                    st.caption(f"💰 CHF {int(total)}")
        
        st.divider()
        
        # === ACTION BUTTONS ===
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
                share_data = create_share_data(ranked)
                encoded = encode_share_data(share_data)
                
                if encoded:
                    st.session_state.show_share_modal = True
                    st.session_state.share_url = f"?share={encoded}"
                    st.rerun()
        
        # === SHARE MODAL ===
        if st.session_state.get("show_share_modal", False):
            st.divider()
            st.subheader("🔗 Share Your Results")
            
            share_url = st.session_state.get("share_url", "")
            
            st.success("✅ Share link created!")
            st.caption("Add this to your app URL to share:")
            st.code(share_url, language=None)
            
            # Create share text
            share_text = f"🌍 My Travel Match: {best['city']}, {best['country']} ({best.get('combined_score', 0)}% match)!  Find your perfect destination too!"
            
            st.text_area("📝 Share text:", value=share_text, height=80)
            
            st.caption("💡 Copy the parameter above and add it to your app's URL to share your results with friends!")
            
            if st.button("✕ Close", key="close_share"):
                st.session_state.show_share_modal = False
                st.rerun()
    
    else:
        st.error("❌ Unable to generate recommendations. Please try again.")
        if st.button("🔄 Start Over", type="primary"):
            reset_session_state()
            st.rerun()


def render_shared_view_page():
    """Renders the shared results view."""
    shared_data = st.session_state.get("shared_results", {})
    
    if not shared_data:
        st.error("❌ Invalid share link")
        if st.button("🏠 Go to Start"):
            st.session_state.state = "Start"
            st.query_params.clear()
            st.rerun()
        return
    
    st.subheader("🔗 Shared Travel Recommendations")
    st.info("Someone shared their travel match results with you!")
    
    # Show trip info
    budget = shared_data.get("b", 0)
    days = shared_data.get("t", 7)
    travelers = shared_data.get("n", 1)
    style = shared_data.get("st", "balanced")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Budget", f"CHF {budget}")
    with col2:
        st.metric("📅 Days", str(days))
    with col3:
        st.metric("👥 Travelers", str(travelers))
    with col4:
        if style in TRAVEL_STYLES:
            style_name = TRAVEL_STYLES[style]["name"]
            # Kürze lange Namen
            if len(style_name) > 10:
                style_name = style_name[:8] + "..."
            st.metric("🎨 Style", style_name)
        else:
            st.metric("🎨 Style", style.title())
    
    st.divider()
    
    # Show results
    results = shared_data.get("r", [])
    
    if results:
        st.subheader("🏆 Top Recommendations")
        
        for i, dest in enumerate(results, 1):
            city = dest.get("c", "Unknown")
            country = dest.get("co", "")
            score = int(dest.get("s", 0))
            flight = int(dest.get("f", 0))
            daily = int(dest.get("d", 0))
            
            total = (flight * travelers) + (daily * days * travelers)
            color = get_score_color(score)
            
            # Use different layout for better display
            if i == 1:
                st.markdown(f"### 🥇 {city}, {country}")
            elif i == 2:
                st.markdown(f"### 🥈 {city}, {country}")
            else:
                st.markdown(f"### 🥉 {city}, {country}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Match Score", f"{color} {score}%")
            
            with col2:
                st.metric("✈️ Flight", f"CHF {flight}")
            
            with col3:
                st.metric("💰 Total", f"CHF {int(total)}")
            
            st.divider()
    else:
        st.warning("No recommendations found in shared link.")
    
    st.subheader("🚀 Find Your Own Match!")
    st.write("Want to find your perfect travel destination? ")
    
    if st.button("🎯 Start My Own Matching", type="primary", use_container_width=True):
        st.session_state.state = "Start"
        st.session_state.shared_results = None
        st.query_params.clear()
        st.rerun()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application entry point."""
    initialize_session_state()
    
    # === CHECK FOR SHARED RESULTS ===
    query_params = st.query_params
    shared_data = parse_shared_results(dict(query_params))
    
    if shared_data and st.session_state.state == "Start":
        st.session_state.shared_results = shared_data
        st.session_state.state = "SharedView"
    
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
        st.write(f"👥 Travelers: {st.session_state.get('num_travelers', 1)}")
        st.write(f"Style: {st.session_state.get('travel_style', 'balanced')}")
        
        travel_date = st.session_state.get('travel_date_start')
        if travel_date:
            st.write(f"📅 Departure: {travel_date.strftime('%b %d, %Y')}")
        
        weather_status = "On" if st.session_state.get("use_weather", True) else "Off"
        st.write(f"Weather: {weather_status}")
        
        if st.session_state.get("use_forecast"):
            st.caption("📡 Using weather forecast")
        elif st.session_state.get("use_weather"):
            st.caption("🌡️ Using current weather")
        
        st.divider()
        st.caption("Travel Recommender v2.6")
        st.caption("CS Group 9.1")
    
    # === PAGE ROUTING ===
    if st.session_state.state == "Start":
        render_start_page()
    elif st.session_state.state == "Matching":
        render_matching_page()
    elif st.session_state.state == "Results":
        render_results_page()
    elif st.session_state.state == "SharedView":
        render_shared_view_page()


if __name__ == "__main__":
    main()