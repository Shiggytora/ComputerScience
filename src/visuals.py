"""
Visuals Module - Data Visualization Components

Uses Plotly for interactive charts.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import streamlit as st


# =============================================================================
# COLOR CONFIGURATION
# =============================================================================

COLORS = {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent": "#FFE66D",
    "success": "#95E1A3",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "neutral": "#95A5A6",
    "background": "#2D3436",
    "text": "#FFFFFF",
}

FEATURE_CONFIG = {
    "safety": {"name": "Safety", "emoji": "🛡️", "color": "#95E1A3"},
    "english_level": {"name": "English", "emoji": "🗣️", "color": "#74B9FF"},
    "crowds": {"name": "Crowds", "emoji": "👥", "color": "#FDCB6E"},
    "beach": {"name": "Beach", "emoji": "🏖️", "color": "#81ECEC"},
    "culture": {"name": "Culture", "emoji": "🏛️", "color": "#A29BFE"},
    "nature": {"name": "Nature", "emoji": "🌿", "color": "#00B894"},
    "food": {"name": "Food", "emoji": "🍽️", "color": "#E17055"},
    "nightlife": {"name": "Nightlife", "emoji": "🌙", "color": "#6C5CE7"},
    "adventure": {"name": "Adventure", "emoji": "🏔️", "color": "#FF7675"},
    "romance": {"name": "Romance", "emoji": "💕", "color": "#FD79A8"},
    "family": {"name": "Family", "emoji": "👨‍👩‍👧‍👦", "color": "#55EFC4"},
}


# =============================================================================
# RADAR CHART
# =============================================================================

def create_preference_radar_chart(
    preferences: Dict[str, float],
    title: str = "Your Travel Preferences",
    show_legend: bool = True
) -> go.Figure:
    """Creates a radar chart showing user preferences across all features."""
    if not preferences:
        return None
    
    filtered_prefs = {k: v for k, v in preferences.items() if k in FEATURE_CONFIG}
    
    if not filtered_prefs:
        return None
    
    categories = []
    values = []
    
    for feature, value in filtered_prefs.items():
        config = FEATURE_CONFIG.get(feature, {})
        display_name = f"{config.get('emoji', '')} {config.get('name', feature)}"
        categories.append(display_name)
        values.append(value)
    
    categories.append(categories[0])
    values.append(values[0])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(78, 205, 196, 0.3)',
        line=dict(color=COLORS["secondary"], width=2),
        marker=dict(size=8, color=COLORS["secondary"]),
        name='Your Preferences'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1', '2', '3', '4', '5'],
                gridcolor='rgba(255,255,255,0.2)',
                linecolor='rgba(255,255,255,0.2)',
            ),
            angularaxis=dict(
                gridcolor='rgba(255,255,255,0.2)',
                linecolor='rgba(255,255,255,0.2)',
            ),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=show_legend,
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text"]),
            x=0.5,
            xanchor='center',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS["text"]),
        margin=dict(l=80, r=80, t=60, b=40),
    )
    
    return fig


# =============================================================================
# BAR CHARTS
# =============================================================================

def create_top_destinations_chart(
    destinations: List[Dict[str, Any]],
    num_destinations: int = 5,
    title: str = "Top Matching Destinations"
) -> go.Figure:
    """Creates a horizontal bar chart showing top destination matches."""
    if not destinations:
        return None
    
    top_dests = destinations[:num_destinations]
    
    names = []
    scores = []
    colors = []
    
    for dest in top_dests:
        city = dest.get('city', 'Unknown')
        country = dest.get('country', '')
        score = dest.get('combined_score', 0)
        
        names.append(f"{city}, {country}")
        scores.append(score)
        
        if score >= 80:
            colors.append("#95E1A3")
        elif score >= 70:
            colors.append("#4ECDC4")
        elif score >= 60:
            colors.append("#74B9FF")
        else:
            colors.append("#A29BFE")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=names,
        x=scores,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=1)
        ),
        text=[f"{s:.1f}%" for s in scores],
        textposition='inside',
        textfont=dict(color='white', size=12),
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(
            title="Match Score (%)",
            range=[0, 100],
            gridcolor='rgba(255,255,255,0.1)',
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=150, r=40, t=60, b=40),
        height=max(250, num_destinations * 40),
    )
    
    return fig


def create_budget_comparison_chart(
    destinations: List[Dict[str, Any]],
    user_budget: float,
    num_travelers: int = 1,
    trip_days: int = 7,
    num_destinations: int = 5,
    title: str = "Budget Comparison"
) -> go.Figure:
    """Creates a grouped bar chart comparing flight and daily costs."""
    if not destinations:
        return None
    
    top_dests = destinations[:num_destinations]
    
    names = []
    flight_costs = []
    daily_costs = []
    
    for dest in top_dests:
        city = dest.get('city', 'Unknown')
        flight = (dest.get('flight_price') or 0) * num_travelers
        daily = (dest.get('avg_budget_per_day') or 0) * trip_days * num_travelers
        
        names.append(city)
        flight_costs.append(flight)
        daily_costs.append(daily)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='✈️ Flights',
        x=names,
        y=flight_costs,
        marker_color=COLORS["secondary"],
        text=[f"CHF {c:.0f}" for c in flight_costs],
        textposition='inside',
    ))
    
    fig.add_trace(go.Bar(
        name='🏨 Accommodation & Food',
        x=names,
        y=daily_costs,
        marker_color=COLORS["primary"],
        text=[f"CHF {c:.0f}" for c in daily_costs],
        textposition='inside',
    ))
    
    fig.add_hline(
        y=user_budget,
        line_dash="dash",
        line_color=COLORS["accent"],
        annotation_text=f"Budget: CHF {user_budget:.0f}",
        annotation_position="top right",
    )
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(title="Destination"),
        yaxis=dict(
            title="Cost (CHF)",
            gridcolor='rgba(255,255,255,0.1)',
        ),
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=40, t=60, b=80),
        height=400,
    )
    
    return fig


def create_weather_score_chart(
    destinations: List[Dict[str, Any]],
    num_destinations: int = 5,
    title: str = "Weather Compatibility"
) -> go.Figure:
    """Creates a bar chart showing weather scores with temperature labels."""
    if not destinations:
        return None
    
    top_dests = destinations[:num_destinations]
    
    names = []
    weather_scores = []
    temps = []
    colors = []
    
    for dest in top_dests:
        city = dest.get('city', 'Unknown')
        weather = dest.get('weather_score', 50)
        
        temp = dest.get('forecast_temp') or dest.get('current_temp')
        
        names.append(city)
        weather_scores.append(weather if weather else 50)
        temps.append(f"{temp}°C" if temp is not None else "N/A")
        
        if weather and weather >= 80:
            colors.append("#95E1A3")
        elif weather and weather >= 60:
            colors.append("#FDCB6E")
        else:
            colors.append("#FF6B6B")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=names,
        y=weather_scores,
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=1)
        ),
        text=[f"{s:.0f}% ({t})" for s, t in zip(weather_scores, temps)],
        textposition='outside',
        textfont=dict(size=11),
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(title="Destination"),
        yaxis=dict(
            title="Weather Score (%)",
            range=[0, 110],
            gridcolor='rgba(255,255,255,0.1)',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=40, t=60, b=40),
        height=350,
    )
    
    return fig


# =============================================================================
# MAP VISUALIZATION
# =============================================================================

def create_destinations_map(
    destinations: List[Dict[str, Any]],
    highlight_best: bool = True,
    title: str = "Your Matching Destinations"
) -> go.Figure:
    """Creates an interactive world map showing all matching destinations."""
    if not destinations:
        return None
    
    lats = []
    lons = []
    names = []
    scores = []
    texts = []
    colors = []
    
    for i, dest in enumerate(destinations):
        lat = dest.get('latitude')
        lon = dest.get('longitude')
        
        if lat is None or lon is None:
            continue
        
        city = dest.get('city', 'Unknown')
        country = dest.get('country', '')
        score = dest.get('combined_score', 50)
        temp = dest.get('forecast_temp') or dest.get('current_temp')
        flight = dest.get('flight_price', 0)
        
        lats.append(lat)
        lons.append(lon)
        names.append(f"{city}, {country}")
        scores.append(score)
        
        hover_text = f"<b>{city}, {country}</b><br>"
        hover_text += f"Match Score: {score:.1f}%<br>"
        if temp is not None:
            hover_text += f"Temperature: {temp}°C<br>"
        if flight:
            hover_text += f"Flight: CHF {flight}"
        texts.append(hover_text)
        
        if i == 0 and highlight_best:
            colors.append("#FFD700")
        elif score >= 80:
            colors.append("#95E1A3")
        elif score >= 70:
            colors.append("#4ECDC4")
        elif score >= 60:
            colors.append("#74B9FF")
        else:
            colors.append("#A29BFE")
    
    if not lats:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lat=lats,
        lon=lons,
        text=texts,
        hoverinfo='text',
        marker=dict(
            size=20,
            color=colors,
            line=dict(width=1, color='white'),
            opacity=0.85,
        ),
        name='Destinations'
    ))
    
    for i in range(min(5, len(lats))):
        fig.add_trace(go.Scattergeo(
            lat=[lats[i]],
            lon=[lons[i]],
            text=[f"#{i+1}"],
            mode='text',
            textfont=dict(size=10, color='white', family='Arial Black'),
            hoverinfo='skip',
            showlegend=False,
        ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18),
            x=0.5,
            xanchor='center',
        ),
        geo=dict(
            showland=True,
            landcolor='rgb(40, 40, 40)',
            showocean=True,
            oceancolor='rgb(30, 50, 70)',
            showlakes=True,
            lakecolor='rgb(30, 50, 70)',
            showcountries=True,
            countrycolor='rgb(80, 80, 80)',
            showcoastlines=True,
            coastlinecolor='rgb(60, 60, 60)',
            projection_type='natural earth',
            bgcolor='rgba(0,0,0,0)',
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-60, 85]),
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=50, b=0),
        height=500,
        showlegend=False,
    )
    
    return fig