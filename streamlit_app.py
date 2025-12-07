"""
Travel Matching App
Helps users find their perfect travel destination based on budget, preferences and weather.
"""

import streamlit as st
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.matching import (
    filter_by_budget,
    ranking_destinations,
    preference_vector,
    find_similar_destinations,
    TRAVEL_STYLES,
)
from src.weather_matching import (
    enrich_destinations_with_weather,
    enrich_destinations_with_forecast,
)
from src.visuals import (
    create_preference_radar_chart,
    create_top_destinations_chart,
    create_budget_comparison_chart,
    create_weather_score_chart,
    create_destinations_map,
)
from src.images import get_thumbnail_url, get_hero_image_url

# App config
ROUNDS = 7
MIN_BUDGET = 100
MAX_BUDGET = 15000
DEFAULT_BUDGET = 3000
DEFAULT_DAYS = 7
MAX_DAYS = 60
DEFAULT_TRAVELERS = 1
MAX_TRAVELERS = 10
LOCATIONS_PER_ROUND = 3
WEATHER_WEIGHT = 0.2
MAX_DESTINATIONS = 50

st.set_page_config(
    page_title="Travel Matching",
    page_icon="✈️",
    layout="centered"
)


# Session state functions

def initialize_session_state():
    """Set up default session values on first load."""
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
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session_state():
    """Clear session to start over."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# Matching logic

def get_smart_round_locations() -> List[Dict[str, Any]]:
    """
    Get destinations for current round.
    First 3 rounds: random (to explore preferences)
    Later rounds: prioritize better matches based on what user picked
    """
    current_round = st.session_state.round
    round_key = f"locations_round_{current_round}"
    
    # Return cached if already picked for this round
    if round_key in st.session_state and st.session_state[round_key]:
        return st.session_state[round_key]
    
    # Get destinations not shown yet
    available = [
        d for d in st.session_state.budget_matches
        if d["id"] not in st.session_state.id_used
    ]
    
    if not available:
        return []
    
    # Early rounds: random to learn preferences
    if current_round < 3 or len(st.session_state.chosen) < 3:
        if len(available) <= LOCATIONS_PER_ROUND:
            locations = available
        else:
            locations = random.sample(available, LOCATIONS_PER_ROUND)
    else:
        # Later rounds: use what we learned to show better matches
        ranked = ranking_destinations(
            available,
            st.session_state.chosen,
            travel_style=st.session_state.get("travel_style", "balanced"),
            use_weather=st.session_state.get("use_weather", True),
            weather_weight=WEATHER_WEIGHT,
        )
        
        if len(ranked) <= LOCATIONS_PER_ROUND:
            locations = ranked
        else:
            # Mix: 2 from top matches, 1 random for variety
            top_pool = ranked[:10]
            selected_top = random.sample(top_pool, min(2, len(top_pool)))
            remaining = [d for d in ranked if d not in selected_top]
            selected_other = random.sample(remaining, 1) if remaining else []
            locations = selected_top + selected_other
            random.shuffle(locations)
    
    st.session_state[round_key] = locations
    return locations


def process_selection(choice_id: int, locations: List[Dict[str, Any]]) -> bool:
    """Save user choice and move to next round."""
    picked = next((loc for loc in locations if loc["id"] == choice_id), None)
    
    if picked is None:
        st.error("Something went wrong. Try again.")
        return False
    
    # Save choice for preference learning
    st.session_state.chosen.append(picked)
    
    # Mark all shown destinations as used
    ids = [loc["id"] for loc in locations]
    st.session_state.id_used.extend(ids)
    
    st.session_state.round += 1
    
    if st.session_state.round >= ROUNDS:
        st.session_state.state = "Results"
    else:
        st.session_state.state = "Matching"
    
    return True


# UI helpers

def get_score_color(score: float) -> str:
    """Color emoji based on score."""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    return "🔴"


def get_score_label(score: float) -> str:
    """Text label for score."""
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
    return "Less Compatible"


def get_temperature_display(dest: Dict[str, Any]) -> str:
    """Get temperature string for a destination."""
    forecast_temp = dest.get('forecast_temp')
    current_temp = dest.get('current_temp')
    rain_days = dest.get('rain_days')
    
    if forecast_temp is not None:
        temp_str = f"🌡️ {forecast_temp}°C"
        if rain_days is not None:
            if rain_days > 0:
                temp_str += f" | 🌧️ {rain_days} rainy days"
            else:
                temp_str += f" | ☀️ No rain expected"
        return temp_str
    elif current_temp is not None:
        # Indicate this is current, not forecast
        return f"🌡️ {current_temp}°C (current)"
    return None


def render_destination_card(loc: Dict[str, Any], index: int):
    """Display destination card with image, info and temperature."""
    image_url = get_thumbnail_url(loc.get('city', ''), loc.get('country', ''))
    st.image(image_url, use_container_width=True)
    
    col1, col2, col3 = st.columns([3, 1.5, 1.2])
    
    with col1:
        st.markdown(f"### {loc['city']}")
        st.caption(f"📍 {loc['country']}")
        
        # Show temperature
        temp_display = get_temperature_display(loc)
        if temp_display:
            st.caption(temp_display)
    
    with col2:
        flight = loc.get('flight_price')
        if flight:
            st.metric("✈️ Flight", f"{flight} CHF")
        else:
            st.metric("✈️ Flight", "N/A")
    
    with col3:
        daily = loc.get('avg_budget_per_day', 0)
        st.metric("📅 /Day", f"{int(daily)} CHF")
    
    st.divider()


def render_progress_bar():
    """Show matching progress."""
    current = st.session_state.round
    progress = current / ROUNDS
    st.progress(progress, text=f"Progress: {current}/{ROUNDS} rounds")
    
    remaining = ROUNDS - current
    if remaining > 0:
        st.info(f"🎯 {remaining} round{'s' if remaining > 1 else ''} to go!")


# Page: Start

def render_start_page():
    """Config page for budget, dates, preferences."""
    st.subheader("🌍 Plan Your Trip")
    
    # Budget and travelers
    col1, col2 = st.columns(2)
    with col1:
        total_budget = st.number_input(
            "💰 Total Budget (CHF)",
            min_value=MIN_BUDGET,
            max_value=MAX_BUDGET,
            value=st.session_state.total_budget,
            step=100,
            help="Total for ALL travelers including flights"
        )
    with col2:
        num_travelers = st.number_input(
            "👥 Travelers",
            min_value=1,
            max_value=MAX_TRAVELERS,
            value=st.session_state.num_travelers,
        )
    
    st.divider()
    
    # Travel dates
    st.subheader("📅 Travel Dates")
    date_col1, date_col2 = st.columns(2)
    
    with date_col1:
        default_start = datetime.now() + timedelta(days=7)
        travel_date_start = st.date_input(
            "Departure",
            value=default_start,
            min_value=datetime.now().date(),
            max_value=datetime.now().date() + timedelta(days=365),
        )
    
    with date_col2:
        default_end = travel_date_start + timedelta(days=DEFAULT_DAYS)
        travel_date_end = st.date_input(
            "Return",
            value=default_end,
            min_value=travel_date_start + timedelta(days=1),
            max_value=travel_date_start + timedelta(days=MAX_DAYS),
        )
    
    trip_days = (travel_date_end - travel_date_start).days
    travelers_text = "person" if num_travelers == 1 else "people"
    st.info(f"💵 **CHF {total_budget}** for **{num_travelers} {travelers_text}** over **{trip_days} days**")
    
    # Check forecast availability
    days_until = (travel_date_start - datetime.now().date()).days
    can_use_forecast = 0 <= days_until <= 16

    if can_use_forecast:
        st.success(f"✅ Weather forecast available!  (Trip in {days_until} days)")
    else:
        st.warning(f"⚠️ Trip is {days_until} days away - weather shown is current, not forecast")
    
    st.divider()
    
    # Travel style
    st.subheader("🎨 Travel Style")
    
    style_options = list(TRAVEL_STYLES.keys())
    selected_style = st.session_state.get("travel_style", "balanced")
    
    row1 = style_options[:5]
    row2 = style_options[5:]
    
    cols1 = st.columns(len(row1))
    for i, style_key in enumerate(row1):
        style = TRAVEL_STYLES[style_key]
        with cols1[i]:
            btn_type = "primary" if selected_style == style_key else "secondary"
            if st.button(style["name"], key=f"style_{style_key}", 
                        use_container_width=True, type=btn_type):
                st.session_state.travel_style = style_key
                st.rerun()
    
    if row2:
        cols2 = st.columns(len(row2))
        for i, style_key in enumerate(row2):
            style = TRAVEL_STYLES[style_key]
            with cols2[i]:
                btn_type = "primary" if selected_style == style_key else "secondary"
                if st.button(style["name"], key=f"style_{style_key}", 
                            use_container_width=True, type=btn_type):
                    st.session_state.travel_style = style_key
                    st.rerun()
    
    if selected_style in TRAVEL_STYLES:
        st.caption(f"_{TRAVEL_STYLES[selected_style]['description']}_")
    
    st.divider()
    
    # Temperature
    st.subheader("🌡️ Weather Preferences")
    
    use_weather = st.checkbox(
        "Include weather in recommendations",
        value=st.session_state.get("use_weather", True),
        help="Uses Open-Meteo API for real weather data"
    )
    st.session_state.use_weather = use_weather
    
    if use_weather:
        temp_col1, temp_col2 = st.columns(2)
        with temp_col1:
            min_temp = st.slider("Min °C", min_value=-10, max_value=30, value=st.session_state.temp_preference[0])
        with temp_col2:
            max_temp = st.slider("Max °C", min_value=10, max_value=45, value=st.session_state.temp_preference[1])
        st.session_state.temp_preference = (min_temp, max_temp)
        st.caption(f"Looking for destinations with {min_temp}°C to {max_temp}°C")
    
    st.divider()
    
    # Start button
    if st.button("🚀 Start Matching", type="primary", use_container_width=True):
        with st.spinner("Finding destinations..."):
            matches = filter_by_budget(total_budget, trip_days, num_travelers)
            
            if not matches:
                st.error("❌ No destinations found. Try higher budget.")
                return
            
            if len(matches) > MAX_DESTINATIONS:
                matches = matches[:MAX_DESTINATIONS]
            
            # Add weather data
            if use_weather:
                start_str = travel_date_start.strftime("%Y-%m-%d")
                end_str = travel_date_end.strftime("%Y-%m-%d")
                
                if can_use_forecast:
                    st.session_state.use_forecast = True
                    matches = enrich_destinations_with_forecast(matches, st.session_state.temp_preference, start_str, end_str, show_progress=True)
                else:
                    st.session_state.use_forecast = False
                    matches = enrich_destinations_with_weather(matches, st.session_state.temp_preference, show_progress=True)
                
                # Check how many got weather data
                with_temp = sum(1 for m in matches if m.get('forecast_temp') or m.get('current_temp'))
                if with_temp > 0:
                    st.success(f"🌡️ Weather data loaded for {with_temp}/{len(matches)} destinations")
            else:
                st.session_state.use_forecast = False
            
            # Save to session
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
            
            st.success(f"✅ Found {len(matches)} destinations!")
            st.rerun()


# Page: Matching

def render_matching_page():
    """Interactive matching where user picks preferred destinations."""
    render_progress_bar()
    
    current_style = st.session_state.get("travel_style", "balanced")
    num_travelers = st.session_state.get("num_travelers", 1)
    travel_date = st.session_state.get("travel_date_start")
    use_forecast = st.session_state.get("use_forecast", False)
    
    if current_style in TRAVEL_STYLES:
        info = f"Style: {TRAVEL_STYLES[current_style]['name']} | 👥 {num_travelers}"
        if travel_date:
            info += f" | 📅 {travel_date.strftime('%b %d, %Y')}"
        if use_forecast:
            info += " | 🌤️ Forecast"
        st.caption(info)
    
    current_display_round = st.session_state.round + 1
    st.subheader(f"🎲 Round {current_display_round} of {ROUNDS}")
    st.write("Which destination appeals to you most?")
    
    locations = get_smart_round_locations()
    
    if not locations:
        st.warning("No more destinations available.")
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
            f"{loc['city']}, {loc['country']}" for loc in locations if loc["id"] == _id
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
            btn_text = "✓ See Results" if current_display_round >= ROUNDS else "✓ Continue"
            if st.button(btn_text, type="primary", use_container_width=True):
                if process_selection(choice, locations):
                    st.rerun()
    else:
        st.warning("👆 Pick a destination above")
    
    st.divider()
    if st.button("← Start Over"):
        reset_session_state()
        st.rerun()


# Page: Results

def render_results_page():
    """Show final recommendations."""
    st.subheader("🎉 Your Perfect Destination!")
    
    travel_style = st.session_state.get("travel_style", "balanced")
    use_weather = st.session_state.get("use_weather", True)
    trip_days = st.session_state.get("trip_days", 7)
    num_travelers = st.session_state.get("num_travelers", 1)
    travel_date_start = st.session_state.get("travel_date_start")
    travel_date_end = st.session_state.get("travel_date_end")
    use_forecast = st.session_state.get("use_forecast", False)
    
    # Calculate rankings
    with st.spinner("Finding your best match..."):
        ranked = ranking_destinations(
            st.session_state.budget_matches,
            st.session_state.chosen,
            travel_style=travel_style,
            use_weather=use_weather,
            weather_weight=WEATHER_WEIGHT,
        )
    
    if not ranked:
        st.error("❌ Something went wrong.")
        if st.button("🔄 Start Over", type="primary"):
            reset_session_state()
            st.rerun()
        return
    
    best = ranked[0]
    
    # 1. Hero image
    hero_url = get_hero_image_url(best.get('city', ''), best.get('country', ''))
    st.image(hero_url, use_container_width=True)
    
    # 2. Winner info with temperature
    score = best.get('combined_score', 0)
    color = get_score_color(score)
    label = get_score_label(score)
    
    st.success(f"### 🏆 {best['city']}, {best['country']}")
    st.markdown(f"**{color} Score: {score}%** - {label}")
    
    # Show temperature for winner
    temp_display = get_temperature_display(best)
    if temp_display:
        st.write(temp_display)
    
    st.write("Based on your choices, this is your ideal destination!")
    
    if travel_style in TRAVEL_STYLES:
        info = f"Style: {TRAVEL_STYLES[travel_style]['name']} | 👥 {num_travelers}"
        if travel_date_start and travel_date_end:
            info += f" | 📅 {travel_date_start.strftime('%b %d')} - {travel_date_end.strftime('%b %d, %Y')}"
        if use_forecast:
            info += " | 🌤️ Forecast"
        st.caption(info)
    
    st.divider()
    
    # 3. Cost breakdown
    st.subheader("💰 Cost Breakdown")
    
    flight_price = best.get('flight_price') or 0
    daily_budget = best.get('avg_budget_per_day') or 0
    flight_total = flight_price * num_travelers
    accommodation_total = daily_budget * trip_days * num_travelers
    total_cost = flight_total + accommodation_total
    
    if num_travelers > 1:
        st.info(f"💡 Costs for **{num_travelers} travelers** over **{trip_days} days**")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("✈️ Flights", f"CHF {int(flight_total)}")
    with c2:
        st.metric("🏨 Stay", f"CHF {int(accommodation_total)}")
    with c3:
        st.metric("💵 Total", f"CHF {int(total_cost)}")
    with c4:
        remaining = st.session_state.total_budget - total_cost
        if remaining >= 0:
            st.metric("💚 Budget left", f"CHF {int(remaining)}")
        else:
            st.metric("🔴 Over budget", f"CHF {int(abs(remaining))}")
    
    st.divider()
    
    # 4. Similar destinations with temperature
    st.subheader("✨ You Might Also Like")
    st.caption("Destinations with similar characteristics")
    
    similar = find_similar_destinations(best, ranked, num_similar=3)
    
    if similar:
        for dest in similar:
            sim_score = dest.get('similarity_score', 0)
            city = dest.get('city', 'Unknown')
            country = dest.get('country', '')
            flight = dest.get('flight_price') or 0
            daily = dest.get('avg_budget_per_day') or 0
            combined = dest.get('combined_score', 0)
            total = (flight * num_travelers) + (daily * trip_days * num_travelers)
            
            img_col, info_col = st.columns([1, 3])
            with img_col:
                st.image(get_thumbnail_url(city, country), use_container_width=True)
            with info_col:
                st.write(f"**{city}, {country}**")
                
                # Show similarity and temperature
                caption_text = f"🔗 {sim_score}% similar to {best['city']}"
                temp_display = get_temperature_display(dest)
                if temp_display:
                    caption_text += f" | {temp_display}"
                st.caption(caption_text)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"{get_score_color(combined)} {combined}%")
                    st.caption("Match")
                with c2:
                    st.write(f"✈️ CHF {flight * num_travelers}")
                    st.caption("Flights")
                with c3:
                    st.write(f"💰 CHF {int(total)}")
                    st.caption("Total")
    else:
        st.info("Not enough data for suggestions.")
    
    st.divider()
    
    # 5. Map
    st.subheader("🗺️ Your Top Matches")
    st.caption("Based on your selections during matching")
    dest_map = create_destinations_map(ranked[:5], highlight_best=True, title="Top 5 Based on Your Preferences")
    if dest_map:
        st.plotly_chart(dest_map, use_container_width=True)    

    st.divider()
    
    # 6. Charts
    st.subheader("📊 Insights")
    
    preference = preference_vector(st.session_state.chosen)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Preferences", "🏆 Top 10", "💰 Budget", "🌤️ Weather"])
    
    with tab1:
        radar = create_preference_radar_chart(preference, title="Your Preference Profile")
        if radar:
            st.plotly_chart(radar, use_container_width=True)
    
    with tab2:
        bar = create_top_destinations_chart(ranked, num_destinations=10, title="Top 10 Based on Your Preferences")
        if bar:
            st.plotly_chart(bar, use_container_width=True)
    
    with tab3:
        budget_chart = create_budget_comparison_chart(
            ranked, st.session_state.total_budget, num_travelers, trip_days,
            num_destinations=5, title="Cost Comparison"
        )
        if budget_chart:
            st.plotly_chart(budget_chart, use_container_width=True)
    
    with tab4:
        if use_weather:
            weather_chart = create_weather_score_chart(ranked, num_destinations=5, title="Weather Compatibility")
            if weather_chart:
                st.plotly_chart(weather_chart, use_container_width=True)
        else:
            st.info("Weather was not included.")
    
    st.divider()
    
    # 7. User selections
    with st.expander("📋 Your Selections"):
        for i, chosen in enumerate(st.session_state.chosen, 1):
            st.write(f"Round {i}: {chosen['city']}, {chosen['country']}")
    
    st.divider()
    
    # 8. Start over
    if st.button("🔄 Start Over", type="primary", use_container_width=True):
        reset_session_state()
        st.rerun()


# Main

def main():
    """App entry point."""
    initialize_session_state()
    
    st.title("✈️ Travel Matching")
    st.write("Find your perfect travel destination!")
    
    if st.session_state.state == "Start":
        render_start_page()
    elif st.session_state.state == "Matching":
        render_matching_page()
    elif st.session_state.state == "Results":
        render_results_page()


if __name__ == "__main__":
    main()