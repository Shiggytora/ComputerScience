"""
Visualization functions using Plotly.
Creates charts for the results page.
Strucure as following:
    - Radar chart for user preferences
    - Horizontal bar chart for top destinations
    - Stacked bar chart for budget comparison
    - Bar chart for weather scores
    - World map for destination locations
"""

import plotly.graph_objects as go
from typing import Dict, List

# Color scheme
COLORS = {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent": "#FFE66D",
    "success": "#95E1A3",
}

# Feature display config with emojis
FEATURE_CONFIG = {
    "safety": {"name": "Safety", "emoji": "🛡️"},
    "english_level": {"name": "English", "emoji": "🗣️"},
    "crowds": {"name": "Crowds", "emoji": "👥"},
    "beach": {"name": "Beach", "emoji": "🏖️"},
    "culture": {"name": "Culture", "emoji": "🏛️"},
    "nature": {"name": "Nature", "emoji": "🌿"},
    "food": {"name": "Food", "emoji": "🍽️"},
    "nightlife": {"name": "Nightlife", "emoji": "🌙"},
    "adventure": {"name": "Adventure", "emoji": "🏔️"},
    "romance": {"name": "Romance", "emoji": "💕"},
    "family": {"name": "Family", "emoji": "👨‍👩‍👧‍👦"}}


# Radar Chart for User Preferences
def create_preference_radar_chart(preferences: Dict[str, float], title: str = "Your Preferences") -> go.Figure:
    if not preferences:
        return None
    
    # Filter preferences to known features
    filtered = {k: v for k, v in preferences.items() if k in FEATURE_CONFIG}
    if not filtered:
        return None
    
    categories = []
    values = []
    
    # Prepare data for radar chart
    for feature, value in filtered.items():
        cfg = FEATURE_CONFIG.get(feature, {})
        label = f"{cfg.get('emoji', '')} {cfg.get('name', feature)}"
        categories.append(label)
        values.append(value)
    
    # Close the radar loop
    categories.append(categories[0])
    values.append(values[0])
    
    # Create radar chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(78, 205, 196, 0.3)',
        line=dict(color=COLORS["secondary"], width=2),
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5]),
            bgcolor='rgba(0,0,0,0)',
        ),
        title=dict(text=title, x=0.5, xanchor='center'),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=80, r=80, t=60, b=40),
    )
    
    return fig


# Horizontal Bar Chart for Top Destinations
def create_top_destinations_chart(destinations: List[Dict], num_destinations: int = 5, title: str = "Top Destinations") -> go.Figure:
    if not destinations:
        return None
    
    # Get top destinations
    top = destinations[:num_destinations]
    names = [f"{d.get('city', '? ')}, {d.get('country', '')}" for d in top]
    scores = [d.get('combined_score', 0) for d in top]
    
    # Color by score
    colors = []
    for s in scores:
        if s >= 80:
            colors.append("#95E1A3")
        elif s >= 70:
            colors.append("#4ECDC4")
        else:
            colors.append("#74B9FF")
    
    # Create horizontal bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names,
        x=scores,
        orientation='h',
        marker=dict(color=colors),
        text=[f"{s:.1f}%" for s in scores],
        textposition='inside',
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        xaxis=dict(title="Match Score (%)", range=[0, 100]),
        yaxis=dict(autorange="reversed"),
        paper_bgcolor='rgba(0,0,0,0)',
        height=max(250, num_destinations * 40),
    )
    
    return fig


# Stacked Bar Chart for Budget Comparison
def create_budget_comparison_chart(destinations: List[Dict], user_budget: float, num_travelers: int = 1, trip_days: int = 7, num_destinations: int = 5, title: str = "Budget Comparison") -> go.Figure:
    if not destinations:
        return None
    
    # Get top destinations
    top = destinations[:num_destinations]
    names = [d.get('city', '?') for d in top]
    flights = [(d.get('flight_price') or 0) * num_travelers for d in top]
    stays = [(d.get('avg_budget_per_day') or 0) * trip_days * num_travelers for d in top]
    
    # Create stacked bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='✈️ Flights',
        x=names,
        y=flights,
        marker_color=COLORS["secondary"]
    ))

    # Stay bars
    fig.add_trace(go.Bar(
        name='🏨 Stay',
        x=names,
        y=stays,
        marker_color=COLORS["primary"]
    ))
    
    # Budget line
    fig.add_hline(
        y=user_budget,
        line_dash="dash",
        line_color=COLORS["accent"],
        annotation_text=f"Budget: CHF {user_budget:.0f}"
    )
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
    )
    
    return fig


# Bar Chart for Weather Scores
def create_weather_score_chart(destinations: List[Dict], num_destinations: int = 5, title: str = "Weather Compatibility") -> go.Figure:
    """Bar chart of weather scores."""
    if not destinations:
        return None
    
    # Get top destinations
    top = destinations[:num_destinations]
    names = [d.get('city', '? ') for d in top]
    scores = [d.get('weather_score', 50) or 50 for d in top]
    temps = [d.get('forecast_temp') or d.get('current_temp') for d in top]
    
    # Color by score
    colors = []
    for s in scores:
        if s >= 80:
            colors.append("#95E1A3")
        elif s >= 60:
            colors.append("#FDCB6E")
        else:
            colors.append("#FF6B6B")
    
    # Create bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names,
        y=scores,
        marker=dict(color=colors),
        text=[f"{s:.0f}% ({t}°C)" if t else f"{s:.0f}%" for s, t in zip(scores, temps)],
        textposition='outside',
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        yaxis=dict(range=[0, 110]),
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
    )
    
    return fig


# # World Map for Destination Locations
def create_destinations_map(destinations: List[Dict], highlight_best: bool = True, title: str = "Destinations") -> go.Figure:
    if not destinations:
        return None
    
    # Prepare data for map
    lats, lons, texts, colors = [], [], [], []
    
    # Iterate through destinations
    for i, dest in enumerate(destinations):
        lat = dest.get('latitude')
        lon = dest.get('longitude')
        
        # Skip if no coordinates
        if lat is None or lon is None:
            continue
        
        city = dest.get('city', '?')
        country = dest.get('country', '')
        score = dest.get('combined_score', 50)
        
        # Collect data
        lats.append(lat)
        lons.append(lon)
        texts.append(f"<b>{city}, {country}</b><br>Score: {score:.1f}%")
        
        # Gold for best, others by score
        if i == 0 and highlight_best:
            colors.append("#FFD700")
        elif score >= 80:
            colors.append("#95E1A3")
        elif score >= 70:
            colors.append("#4ECDC4")
        else:
            colors.append("#74B9FF")
    
    if not lats:
        return None
    
    # Create map figure
    fig = go.Figure()
    
    # Destination points
    fig.add_trace(go.Scattergeo(
        lat=lats,
        lon=lons,
        text=texts,
        hoverinfo='text',
        marker=dict(size=20, color=colors, line=dict(width=1, color='white')),
    ))
    
    # Add ranking numbers for top 5
    for i in range(min(5, len(lats))):
        fig.add_trace(go.Scattergeo(
            lat=[lats[i]],
            lon=[lons[i]],
            text=[f"#{i+1}"],
            mode='text',
            textfont=dict(size=10, color='white'),
            hoverinfo='skip',
            showlegend=False,
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        geo=dict(
            showland=True,
            landcolor='rgb(40, 40, 40)',
            showocean=True,
            oceancolor='rgb(30, 50, 70)',
            showcountries=True,
            countrycolor='rgb(80, 80, 80)',
            projection_type='natural earth',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        height=500,
        showlegend=False,
    )
    
    return fig