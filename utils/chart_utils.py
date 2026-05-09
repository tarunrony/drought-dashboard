"""
utils/chart_utils.py
Plotly chart builders for each parameter.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import DROUGHT_THRESHOLDS

COLORS = {
    "ndvi":     "#4CAF50",
    "rainfall": "#2196F3",
    "lst":      "#FF5722",
    "moisture": "#00BCD4",
    "threshold":"#FF9800",
}

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e0e0e0", size=12),
    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", showgrid=True),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", showgrid=True),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def ndvi_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["NDVI_mean"],
        mode="lines+markers", name="NDVI",
        line=dict(color=COLORS["ndvi"], width=2),
        marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(76,175,80,0.1)",
    ))
    # Drought threshold lines
    thresholds = DROUGHT_THRESHOLDS["ndvi"]
    for label, value, color in [
        ("Normal",   thresholds["normal"],   "#1a9850"),
        ("Mild",     thresholds["mild"],     "#fee08b"),
        ("Moderate", thresholds["moderate"], "#f46d43"),
        ("Severe",   thresholds["severe"],   "#d73027"),
    ]:
        fig.add_hline(
            y=value, line_dash="dot", line_color=color,
            annotation_text=label, annotation_position="right",
        )
    fig.update_layout(title="🌿 NDVI Time Series", yaxis_title="NDVI", **_LAYOUT)
    return fig


def rainfall_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["date"], y=df["rainfall_mm"],
        name="Daily Rainfall", marker_color=COLORS["rainfall"],
        opacity=0.7,
    ))
    if "rolling_7d" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["rolling_7d"],
            mode="lines", name="7-day Average",
            line=dict(color="#FFC107", width=2),
        ))
    fig.update_layout(title="🌧️ Daily Rainfall (CHIRPS)", yaxis_title="mm", **_LAYOUT)
    return fig


def lst_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["LST_C"],
        mode="lines+markers", name="LST (°C)",
        line=dict(color=COLORS["lst"], width=2),
        marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(255,87,34,0.08)",
    ))
    thresholds = DROUGHT_THRESHOLDS["lst_celsius"]
    for label, value, color in [
        ("Normal",   thresholds["normal"],   "#1a9850"),
        ("Mild",     thresholds["mild"],     "#fee08b"),
        ("Moderate", thresholds["moderate"], "#f46d43"),
        ("Severe",   thresholds["severe"],   "#d73027"),
    ]:
        fig.add_hline(
            y=value, line_dash="dot", line_color=color,
            annotation_text=label, annotation_position="right",
        )
    fig.update_layout(title="🌡️ Land Surface Temperature", yaxis_title="°C", **_LAYOUT)
    return fig


def soil_moisture_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["ssm"],
        mode="lines+markers", name="Soil Moisture",
        line=dict(color=COLORS["moisture"], width=2),
        marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(0,188,212,0.1)",
    ))
    thresholds = DROUGHT_THRESHOLDS["soil_moisture"]
    for label, value, color in [
        ("Normal",   thresholds["normal"],   "#1a9850"),
        ("Severe",   thresholds["severe"],   "#d73027"),
    ]:
        fig.add_hline(y=value, line_dash="dot", line_color=color,
                      annotation_text=label, annotation_position="right")
    fig.update_layout(title="💧 Soil Moisture (SMAP)", yaxis_title="m³/m³", **_LAYOUT)
    return fig


def comparison_radar(stats_list: list, labels: list) -> go.Figure:
    """Multi-upazila radar chart comparing normalized parameter scores."""
    categories = ["NDVI", "Rainfall", "LST (inv)", "Soil Moisture"]
    fig = go.Figure()
    colors = ["#4CAF50", "#2196F3", "#FF5722", "#FF9800", "#9C27B0", "#00BCD4"]
    for i, (stats, label) in enumerate(zip(stats_list, labels)):
        ndvi_norm = min(max((stats.get("ndvi_mean", 0)) / 0.8, 0), 1)
        rain_norm = min(max((stats.get("rain_total", 0)) / 500, 0), 1)
        lst_norm  = 1 - min(max((stats.get("lst_mean", 30) - 20) / 30, 0), 1)
        ssm_norm  = min(max((stats.get("ssm_mean", 0)) / 0.5, 0), 1)
        fig.add_trace(go.Scatterpolar(
            r=[ndvi_norm, rain_norm, lst_norm, ssm_norm, ndvi_norm],
            theta=categories + [categories[0]],
            fill="toself", name=label,
            line_color=colors[i % len(colors)],
            fillcolor=colors[i % len(colors)].replace(")", ",0.15)").replace("rgb", "rgba"),
        ))
    fig.update_layout(
        title="📡 Multi-Area Drought Comparison",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig
