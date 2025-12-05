"""
Visuals Module - Data Visualization Components

This module provides visualization functions for the Travel Matching application,
including radar charts for preference profiles and bar charts for score comparisons. 

Uses Plotly for interactive charts. 

Part of Requirement #3: Data Visualization Implementation
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import streamlit as st


# =============================================================================
# COLOR CONFIGURATION
# =============================================================================

# Color scheme for the application
COLORS = {
    "primary": "#FF6B6B",      # Coral red
    "secondary": "#4ECDC4",    # Teal
    "accent": "#FFE66D",       # Yellow
    "success": "#95E1A3",      # Light green
    "warning": "#FFB347",      # Orange
    "danger": "#FF6B6B",       # Red
    "neutral": "#95A5A6",      # Gray
    "background": "#2D3436",   # Dark gray
    "text": "#FFFFFF",         # White
}

# Feature display names and colors
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
    """
    Creates a radar chart showing user preferences across all features.
    
    The radar chart visualizes the user's preference profile based on
    their selections during the matching process.
    
    Args:
        preferences: Dictionary mapping feature names to values (1-5 scale)
        title: Chart title
        show_legend: Whether to show the legend
        
    Returns:
        Plotly Figure object
        
    Example:
        >>> prefs = {"beach": 4.5, "culture": 3.0, "nature": 4.0}
        >>> fig = create_preference_radar_chart(prefs)
        >>> st.plotly_chart(fig)
    """
    if not preferences:
        return None
    
    # Filter to only include features we have config for
    filtered_prefs = {k: v for k, v in preferences.items() if k in FEATURE_CONFIG}
    
    if not filtered_prefs:
        return None
    
    # Prepare data
    categories = []
    values = []
    
    for feature, value in filtered_prefs.items():
        config = FEATURE_CONFIG.get(feature, {})
        display_name = f"{config.get('emoji', '')} {config.get('name', feature)}"
        categories.append(display_name)
        values.append(value)
    
    # Close the radar chart by repeating the first value
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
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS["text"]),
        margin=dict(l=80, r=80, t=60, b=40),
    )
    
    return fig


def create_comparison_radar_chart(
    user_preferences: Dict[str, float],
    destination_values: Dict[str, float],
    destination_name: str = "Destination",
    title: str = "Preference vs Destination Match"
) -> go.Figure:
    """
    Creates a radar chart comparing user preferences with destination features.
    
    This visualization helps users understand how well a destination
    matches their preferences across different categories.
    
    Args:
        user_preferences: User's preference values
        destination_values: Destination's feature values
        destination_name: Name of the destination for the legend
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    if not user_preferences or not destination_values:
        return None
    
    # Get common features
    common_features = set(user_preferences.keys()) & set(destination_values.keys())
    common_features = [f for f in common_features if f in FEATURE_CONFIG]
    
    if not common_features:
        return None
    
    # Prepare data
    categories = []
    user_values = []
    dest_values = []
    
    for feature in common_features:
        config = FEATURE_CONFIG.get(feature, {})
        display_name = f"{config.get('emoji', '')} {config.get('name', feature)}"
        categories.append(display_name)
        user_values.append(user_preferences.get(feature, 0))
        dest_values.append(destination_values.get(feature, 0))
    
    # Close the radar chart
    categories.append(categories[0])
    user_values.append(user_values[0])
    dest_values.append(dest_values[0])
    
    # Create figure
    fig = go.Figure()
    
    # User preferences trace
    fig.add_trace(go.Scatterpolar(
        r=user_values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(78, 205, 196, 0.3)',
        line=dict(color=COLORS["secondary"], width=2),
        name='Your Preferences'
    ))
    
    # Destination values trace
    fig.add_trace(go.Scatterpolar(
        r=dest_values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(255, 107, 107, 0.3)',
        line=dict(color=COLORS["primary"], width=2),
        name=destination_name
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                gridcolor='rgba(255,255,255,0.2)',
            ),
            angularaxis=dict(
                gridcolor='rgba(255,255,255,0.2)',
            ),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=80, r=80, t=60, b=80),
    )
    
    return fig


# =============================================================================
# BAR CHARTS
# =============================================================================

def create_score_breakdown_chart(
    breakdown: Dict[str, Dict[str, Any]],
    title: str = "Match Score Breakdown"
) -> go.Figure:
    """
    Creates a horizontal bar chart showing the breakdown of match scores by feature.
    
    Args:
        breakdown: Dictionary with feature names as keys and score data as values
                   Each value should have 'similarity' key with percentage value
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    if not breakdown:
        return None
    
    # Prepare data
    features = []
    scores = []
    colors = []
    
    for feature, data in breakdown.items():
        if feature not in FEATURE_CONFIG:
            continue
            
        config = FEATURE_CONFIG[feature]
        similarity = data.get('similarity', 0)
        
        features.append(f"{config['emoji']} {config['name']}")
        scores.append(similarity)
        
        # Color based on score
        if similarity >= 80:
            colors.append("#95E1A3")  # Green
        elif similarity >= 60:
            colors.append("#FDCB6E")  # Yellow
        elif similarity >= 40:
            colors.append("#FFB347")  # Orange
        else:
            colors.append("#FF6B6B")  # Red
    
    if not features:
        return None
    
    # Sort by score descending
    sorted_data = sorted(zip(features, scores, colors), key=lambda x: x[1], reverse=True)
    features, scores, colors = zip(*sorted_data) if sorted_data else ([], [], [])
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=list(features),
        x=list(scores),
        orientation='h',
        marker=dict(
            color=list(colors),
            line=dict(color='rgba(255,255,255,0.3)', width=1)
        ),
        text=[f"{s:.0f}%" for s in scores],
        textposition='inside',
        textfont=dict(color='white', size=12),
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5,
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
        margin=dict(l=120, r=40, t=60, b=40),
        height=max(300, len(features) * 40),
    )
    
    return fig


def create_top_destinations_chart(
    destinations: List[Dict[str, Any]],
    num_destinations: int = 5,
    title: str = "Top Matching Destinations"
) -> go.Figure:
    """
    Creates a horizontal bar chart showing top destination matches.
    
    Args:
        destinations: List of destination dictionaries with 'combined_score'
        num_destinations: Number of top destinations to show
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
    if not destinations:
        return None
    
    # Get top N destinations
    top_dests = destinations[:num_destinations]
    
    # Prepare data
    names = []
    scores = []
    colors = []
    
    for dest in top_dests:
        city = dest.get('city', 'Unknown')
        country = dest.get('country', '')
        score = dest.get('combined_score', 0)
        
        names.append(f"{city}, {country}")
        scores.append(score)
        
        # Color gradient based on rank
        if score >= 80:
            colors.append("#95E1A3")
        elif score >= 70:
            colors.append("#4ECDC4")
        elif score >= 60:
            colors.append("#74B9FF")
        else:
            colors.append("#A29BFE")
    
    # Create chart
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
        height=max(250, num_destinations * 50),
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
    """
    Creates a grouped bar chart comparing flight and daily costs for top destinations.
    
    Args:
        destinations: List of destination dictionaries
        user_budget: User's total budget
        num_travelers: Number of travelers
        trip_days: Number of trip days
        num_destinations: Number of destinations to show
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
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
    
    # Create grouped bar chart
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
    
    # Add budget line
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
    """
    Creates a bar chart showing weather scores with temperature labels.
    
    Args:
        destinations: List of destination dictionaries with weather data
        num_destinations: Number of destinations to show
        title: Chart title
        
    Returns:
        Plotly Figure object
    """
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
        temp = dest.get('current_temp')
        
        names.append(city)
        weather_scores.append(weather if weather else 50)
        temps.append(f"{temp}°C" if temp is not None else "N/A")
        
        # Color based on weather score
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
# GAUGE CHART
# =============================================================================

def create_score_gauge(
    score: float,
    title: str = "Match Score",
    max_value: float = 100
) -> go.Figure:
    """
    Creates a gauge chart for displaying a single score value.
    
    Args:
        score: The score value to display
        title: Chart title
        max_value: Maximum value for the gauge
        
    Returns:
        Plotly Figure object
    """
    # Determine color based on score
    if score >= 80:
        bar_color = "#95E1A3"
    elif score >= 60:
        bar_color = "#FDCB6E"
    elif score >= 40:
        bar_color = "#FFB347"
    else:
        bar_color = "#FF6B6B"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title=dict(text=title, font=dict(size=14)),
        number=dict(suffix="%", font=dict(size=28)),
        gauge=dict(
            axis=dict(
                range=[0, max_value],
                tickwidth=1,
                tickcolor="white",
            ),
            bar=dict(color=bar_color),
            bgcolor="rgba(255,255,255,0.1)",
            borderwidth=2,
            bordercolor="rgba(255,255,255,0.3)",
            steps=[
                dict(range=[0, 40], color="rgba(255,107,107,0.3)"),
                dict(range=[40, 60], color="rgba(255,179,71,0.3)"),
                dict(range=[60, 80], color="rgba(253,203,110,0.3)"),
                dict(range=[80, 100], color="rgba(149,225,163,0.3)"),
            ],
            threshold=dict(
                line=dict(color="white", width=2),
                thickness=0.75,
                value=score
            )
        )
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    return fig


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def test_visuals():
    """Test function to verify module is loaded correctly."""
    return "Visuals test successful"