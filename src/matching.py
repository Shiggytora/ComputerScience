# We use this for the main logic of our matching feature

import streamlit as st

# fake data 
DESTINATIONS = [
    {
        "name": "Barcelona",
        "country": "Spain",
        "continent": "Europe",
        "typical_temp_spring": 18,
        "cost_level": "medium",
        "tourist_level": "high",
        "city_size": "large",
        "airport_code": "BCN",
        "currency": "EUR",
        "visa_required": False,
    },
    {
        "name": "Reykjavik",
        "country": "Iceland",
        "continent": "Europe",
        "typical_temp_spring": 5,
        "cost_level": "high",
        "tourist_level": "medium",
        "city_size": "small",
        "airport_code": "KEF",
        "currency": "ISK",
        "visa_required": False,
    },
    
]


def compute_factor_weights(selected_factors, priorities):
    """
    selected_factors: list like ["Weather", "Budget", "Distance"]
    priorities: dict factor -> rank (1 = most important)
    """
    # convert rank to weight (inverse: smaller rank = bigger weight)
    # simple method: weight = (max_rank + 1 - rank) / sum_all
    max_rank = max(priorities.values())
    raw = {}
    for f in selected_factors:
        rank = priorities[f]
        raw[f] = max_rank + 1 - rank

    total = sum(raw.values())
    return {f: raw[f] / total for f in raw}


def score_destination(dest, prefs, weights):
    score = 0.0

    # WEATHER
    if "Weather" in weights:
        desired = prefs["desired_temp"]  # "Warm", "Mild", "Cold"
        t = dest["typical_temp_spring"]
        if desired == "Warm":
            target = 24
        elif desired == "Mild":
            target = 18
        else:
            target = 5
        subscore = max(0, 1 - abs(t - target) / 20)
        score += weights["Weather"] * subscore

    # BUDGET
    if "Budget" in weights:
        desired = prefs["budget_level"]  # "Low", "Medium", "High"
        levels = ["Low", "Medium", "High"]
        dest_level = dest["cost_level"].capitalize()
        diff = abs(levels.index(desired) - levels.index(dest_level))
        subscore = {0: 1, 1: 0.5}.get(diff, 0)
        score += weights["Budget"] * subscore

    # CONTINENT / DISTANCE
    if "Continent / Distance" in weights:
        if prefs["continent"] == "Any" or dest["continent"] == prefs["continent"]:
            subscore = 1
        else:
            subscore = 0
        score += weights["Continent / Distance"] * subscore

    # TOURISM
    if "Tourism" in weights:
        desired = prefs["tourist_level"]  # "Quiet", "Balanced", "Very touristic"
        # very rough mapping
        mapping = {
            "low": "Quiet",
            "medium": "Balanced",
            "high": "Very touristic",
        }
        dest_level = mapping[dest["tourist_level"]]
        subscore = 1 if dest_level == desired else 0.5
        score += weights["Tourism"] * subscore

    # CITY SIZE
    if "City size" in weights:
        desired = prefs["city_size"]  # "Small", "Medium", "Large"
        mapping = {
            "small": "Small",
            "medium": "Medium",
            "large": "Large",
        }
        dest_size = mapping[dest["city_size"]]
        subscore = 1 if dest_size == desired else 0.5
        score += weights["City size"] * subscore

    return score


def main():
    st.title("Travel Match 🔍✈️")

    st.sidebar.header("Your preferences")

    # ----- User inputs -----
    budget_level = st.sidebar.selectbox("Budget", ["Low", "Medium", "High"])
    desired_temp = st.sidebar.selectbox("Preferred weather", ["Warm", "Mild", "Cold"])
    continent = st.sidebar.selectbox("Preferred continent", ["Any", "Europe", "Asia", "Africa", "North America", "South America", "Oceania"])
    tourist_level = st.sidebar.selectbox("Tourism level", ["Quiet", "Balanced", "Very touristic"])
    city_size = st.sidebar.selectbox("City size", ["Small", "Medium", "Large"])

    # Factors to prioritize
    st.sidebar.markdown("### Choose your top factors (3–5)")
    all_factors = ["Weather", "Budget", "Continent / Distance", "Tourism", "City size"]
    selected_factors = st.sidebar.multiselect("Factors", all_factors, default=["Weather", "Budget", "Continent / Distance"])

    # Ranks
    priorities = {}
    if selected_factors:
        st.sidebar.markdown("#### Rank them (1 = most important)")
        for f in selected_factors:
            priorities[f] = st.sidebar.number_input(f"Rank for {f}", min_value=1, max_value=len(selected_factors), value=1)

    if st.sidebar.button("Find my destinations"):
        if not selected_factors:
            st.error("Please select at least one factor.")
            return

        prefs = {
            "budget_level": budget_level,
            "desired_temp": desired_temp,
            "continent": continent,
            "tourist_level": tourist_level,
            "city_size": city_size,
        }

        weights = compute_factor_weights(selected_factors, priorities)

        # compute scores
        scored = []
        for d in DESTINATIONS:
            s = score_destination(d, prefs, weights)
            scored.append((d, s))

        scored.sort(key=lambda x: x[1], reverse=True)

        st.subheader("Best matches for you")
        for dest, s in scored[:5]:
            st.markdown(f"### {dest['name']}, {dest['country']}  — Score: {s:.2f}")
            st.write(f"Continent: {dest['continent']}")
            st.write(f"Typical spring temp: {dest['typical_temp_spring']}°C")
            st.write(f"Cost level: {dest['cost_level']}")
            st.write(f"Tourism level: {dest['tourist_level']}")
            st.write(f"City size: {dest['city_size']}")
            st.divider()


if __name__ == "__main__":
    main()

def test_matching():

    return "Matching successful"
    

