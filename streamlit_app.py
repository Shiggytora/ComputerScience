import streamlit as st
from typing import List, Dict, Any
from src.amadeus import test_amadeus
from src.  weather import get_current_weather
from src.data import test_data
from src.matching import (
    test_matching, 
    filter_by_budget, 
    test_locations, 
    ranking_destinations,
    preference_vector,
    calculate_feature_ranges,
    get_match_breakdown,
    NUMERIC_FEATURES,
    FEATURE_WEIGHTS,
)
from src.machinelearning import test_ml
from src.visuals import test_visuals

ROUNDS = 7
MIN_BUDGET = 100
MAX_BUDGET = 10000
DEFAULT_BUDGET = 2000
MIN_DAYS = 1
MAX_DAYS = 60
DEFAULT_DAYS = 7
LOCATIONS_PER_ROUND = 3

st. set_page_config(
    page_title="Travel Matching",
    page_icon="⛱️",
    layout="centered"
)


def initialize_session_state():
    """Initialisiert alle session state Variablen mit sicheren Defaults."""
    defaults = {
        "state": "Start",
        "budget_matches": [],
        "id_used": [],
        "chosen": [],
        "round": 0,
        "total_budget": DEFAULT_BUDGET,
        "trip_days": DEFAULT_DAYS,
        "current_locations": [],
        "pending_choice": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session_state():
    """Setzt alle session state Variablen zurück."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def get_current_round_locations() -> List[Dict[str, Any]]:
    """Holt die Locations für die aktuelle Runde."""
    round_key = f"locations_round_{st. session_state.round}"
    
    if round_key not in st.session_state or not st.session_state[round_key]:
        locations = test_locations(
            st.session_state. budget_matches,
            st.session_state.id_used,
            x=LOCATIONS_PER_ROUND,
        )
        st.session_state[round_key] = locations
    
    return st.session_state[round_key]


def process_selection(choice_id: int, locations: List[Dict[str, Any]]):
    """Verarbeitet die Benutzerauswahl und aktualisiert den State."""
    picked = next((loc for loc in locations if loc["id"] == choice_id), None)
    
    if picked is None:
        st.error("Ausgewähltes Ziel nicht gefunden.  Bitte erneut versuchen.")
        return False
    
    st.session_state. chosen. append(picked)
    
    ids = [loc["id"] for loc in locations]
    st.session_state.id_used.extend(ids)
    
    st.session_state. round += 1
    
    if st.session_state.round >= ROUNDS:
        st. session_state.state = "Results"
    else:
        st. session_state.state = "Matching"
    
    return True


def get_score_color(score: float) -> str:
    """Gibt eine Farbe basierend auf dem Score zurück."""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"


def get_score_label(score: float) -> str:
    """Gibt ein Label basierend auf dem Score zurück."""
    if score >= 90:
        return "Perfekter Match!"
    elif score >= 80:
        return "Ausgezeichnet"
    elif score >= 70:
        return "Sehr gut"
    elif score >= 60:
        return "Gut"
    elif score >= 50:
        return "Okay"
    else:
        return "Weniger passend"


def render_destination_card(loc: Dict[str, Any], index: int):
    """Rendert eine einzelne Destination-Karte."""
    with st.container():
        col1, col2, col3 = st. columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {loc['city']}")
            st. caption(f"📍 {loc['country']}")
        
        with col2:
            rating = loc. get('tourist_rating', 'N/A')
            st.metric("Rating", f"⭐ {rating}")
        
        with col3:
            if 'avg_budget_per_day' in loc:
                budget_value = int(loc['avg_budget_per_day'])
                st.metric("Daily Budget", f"CHF {budget_value}")
        
        st.divider()


def render_progress_bar():
    """Rendert die Fortschrittsanzeige."""
    current_round = st.session_state.round
    progress = current_round / ROUNDS
    
    st.progress(progress, text=f"Progress: {current_round}/{ROUNDS} rounds completed")
    
    remaining = ROUNDS - current_round
    if remaining > 0:
        st.info(f"🎯 Noch {remaining} Runde{'n' if remaining > 1 else ''} bis zu deiner Empfehlung!")


def render_start_page():
    """Rendert die Startseite."""
    st.subheader("🌍 Plan your trip")
    
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
            value=st.session_state. trip_days,
            help="How many days will you be traveling?"
        )
    
    if trip_days > 0:
        budget_per_day = total_budget / trip_days
        st.info(f"💵 Budget per day: **CHF {budget_per_day:.2f}**")
    
    st. divider()
    
    if st.button("🚀 Start Matching", type="primary", use_container_width=True):
        with st.spinner("Finding destinations within your budget..."):
            matches = filter_by_budget(total_budget, trip_days)
            
            if not matches:
                st. error("❌ No destinations found within your budget.  Try adjusting your parameters.")
            else:
                st.session_state.budget_matches = matches
                st.session_state.total_budget = total_budget
                st. session_state.trip_days = trip_days
                st. session_state.id_used = []
                st.session_state.chosen = []
                st.session_state.round = 0
                st.session_state. state = "Matching"
                st.success(f"✅ Found {len(matches)} destinations!")
                st. rerun()


def render_matching_page():
    """Rendert die Matching-Seite mit verbesserter UX."""
    render_progress_bar()
    
    current_display_round = st. session_state.round + 1
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
        "**🎯 Your choice:**",
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
        st. warning("👆 Please select a destination above to continue")
    
    st. divider()
    if st.button("← Start Over", use_container_width=False):
        reset_session_state()
        st.rerun()


def render_match_score_display(score: float):
    """Rendert eine visuelle Match Score Anzeige."""
    color = get_score_color(score)
    label = get_score_label(score)
    
    st.markdown(f"### {color} Match Score: {score}%")
    st.caption(label)
    
    # Progress-Bar für den Score
    st.progress(score / 100)


def render_score_breakdown(breakdown: Dict[str, Dict[str, Any]]):
    """Rendert eine detaillierte Aufschlüsselung des Scores."""
    
    # Feature Namen auf Deutsch
    feature_names = {
        "city_size": "🏙️ Stadtgröße",
        "tourist_rating": "⭐ Touristen-Rating",
        "tourist_volume_base": "👥 Touristen-Volumen",
        "is_coastal": "🏖️ Küstenlage",
        "climate_category": "🌡️ Klima",
        "cost_index": "💰 Kostenindex",
    }
    
    for feature, data in breakdown.items():
        name = feature_names. get(feature, feature)
        similarity = data['similarity']
        color = get_score_color(similarity)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"{name}")
        with col2:
            st. write(f"{color} {similarity}%")
        with col3:
            weight = data['weight']
            if weight > 1.5:
                st. caption("⬆️ Hoch")
            elif weight > 1.0:
                st.caption("➡️ Mittel")
            else:
                st. caption("⬇️ Normal")


def render_results_page():
    """Rendert die Ergebnisseite mit Match Score."""
    st. balloons()
    st.subheader("🎉 Your Perfect Destination!")
    
    with st.spinner("Calculating your best match... "):
        ranked = ranking_destinations(
            st.session_state.budget_matches,
            st.session_state. chosen,
        )
    
    if ranked:
        best = ranked[0]
        
        st.success(f"### 🏆 {best['city']}, {best['country']}")
        st. write("Based on your preferences, this is your ideal destination!")
        
        st.divider()
        
        # Match Score prominent anzeigen
        col1, col2 = st.columns([1, 1])
        
        with col1:
            match_score = best. get('match_score', 0)
            render_match_score_display(match_score)
        
        with col2:
            rating = best.get('tourist_rating', 'N/A')
            st.metric("Tourist Rating", f"⭐ {rating}")
            
            if 'avg_budget_per_day' in best:
                total_cost = best['avg_budget_per_day'] * st.session_state.trip_days
                total_cost_rounded = round(total_cost, 2)
                st.metric("Estimated Total", f"💰 CHF {total_cost_rounded}")
        
        st.divider()
        
        # Score Breakdown
        with st.expander("📊 Match Score Details"):
            st. write("So gut passt diese Destination zu deinen Präferenzen:")
            preference = preference_vector(st.session_state. chosen)
            feature_ranges = calculate_feature_ranges(st.session_state.budget_matches)
            breakdown = get_match_breakdown(best, preference, feature_ranges)
            render_score_breakdown(breakdown)
        
        # Deine Auswahlen anzeigen
        with st.expander("📋 Your selections during matching"):
            for i, chosen in enumerate(st. session_state.chosen, 1):
                st.write(f"**Round {i}:** {chosen['city']}, {chosen['country']}")
        
        with st.expander("🔍 See all destination details"):
            st.json(best)
        
        # Andere Optionen mit Match Score
        if len(ranked) > 1:
            st.divider()
            st.subheader("🥈 Other Great Options:")
            
            for i, dest in enumerate(ranked[1:6], 2):
                score = dest.get('match_score', 0)
                color = get_score_color(score)
                
                col1, col2, col3 = st. columns([3, 1, 1])
                with col1:
                    st.write(f"**{i}. ** {dest['city']}, {dest['country']}")
                with col2:
                    st.write(f"{color} {score}%")
                with col3:
                    dest_rating = dest.get('tourist_rating', 'N/A')
                    st. caption(f"⭐ {dest_rating}")
        
        st.divider()
    else:
        st.error("❌ Unable to generate recommendations. Please try again.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start Over", type="primary", use_container_width=True):
            reset_session_state()
            st.rerun()
    
    with col2:
        if st.button("💾 Save Results", use_container_width=True):
            st.info("🚧 Feature in progress...")


def main():
    initialize_session_state()
    
    st.title("✈️ Travel Matching")
    st.write("Welcome to our travel matching application!")
    
    with st.sidebar:
        st. subheader("🔧 Debug Info")
        st. write(f"State: {st.session_state.state}")
        st.write(f"Round: {st.session_state.round}")
        st.write(f"Chosen: {len(st.session_state.chosen)}")
    
    if st.session_state.state == "Start":
        render_start_page()
    elif st. session_state.state == "Matching":
        render_matching_page()
    elif st. session_state.state == "Results":
        render_results_page()


if __name__ == "__main__":
    main()