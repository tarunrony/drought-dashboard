import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
import ee
import pandas as pd
from datetime import datetime, date

from modules.gee_connect import initialize_gee
from modules.ndvi import get_ndvi, get_ndvi_timeseries
from modules.rainfall import get_rainfall, get_monthly_rainfall
from modules.lst import get_lst, get_lst_timeseries
from modules.soil_moisture import get_ndwi, get_smap_soil_moisture
from config import AREAS, DATE_RANGES

# ─── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="Drought Analysis Dashboard — Bangladesh",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────
st.markdown(
    """
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a2f, #2d5a3d);
        border-radius: 12px; padding: 20px;
        border-left: 4px solid #4CAF50;
        margin: 8px 0;
    }
    .drought-alert {
        background: #3d1a00; border-left: 4px solid #FF5722;
        border-radius: 8px; padding: 12px; margin: 8px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ─── GEE Init ─────────────────────────────────────────────────
@st.cache_resource
def load_gee():
    return initialize_gee()


gee_status = load_gee()

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://flagicons.lipis.dev/flags/4x3/bd.svg", width=60)
    st.title("🌾 Drought Dashboard")
    st.divider()

    # Area Selection
    st.subheader("📍 Area Selection")
    selected_areas = st.multiselect(
        "Select Upazilas", options=list(AREAS.keys()), default=["Sapahar Upazila"]
    )

    # Date Range
    st.subheader("📅 Date Range")
    preset = st.selectbox("Preset Ranges", list(DATE_RANGES.keys()))

    if preset == "Custom":
        start_date = st.date_input("Start Date", date(2022, 1, 1))
        end_date = st.date_input("End Date", date(2022, 12, 31))
    else:
        start_date, end_date = DATE_RANGES[preset]

    # Parameter Selection
    st.subheader("📊 Parameters")
    show_ndvi = st.checkbox("🌿 NDVI (Crop Health)", value=True)
    show_rainfall = st.checkbox("🌧️ Rainfall (CHIRPS)", value=True)
    show_lst = st.checkbox("🌡️ Land Surface Temp", value=True)
    show_moisture = st.checkbox("💧 Soil Moisture / NDWI", value=True)

    analyze_btn = st.button("🔍 Run Analysis", type="primary", use_container_width=True)

# ─── Main Content ─────────────────────────────────────────────
st.title("🌍 Agricultural Drought Analysis — Bangladesh")
st.caption(
    f"Analyzing: {', '.join(selected_areas)} | Period: {start_date} → {end_date}"
)

if not gee_status:
    st.error("⚠️ GEE connection failed. Check authentication.")
    st.stop()

if analyze_btn and selected_areas:
    # Area geometry বানানো
    area = AREAS[selected_areas[0]]
    geometry = ee.Geometry.Point(area["coords"]).buffer(10000)  # 10km buffer

    tabs = st.tabs(["🗺️ Map View", "📊 Charts", "📋 Statistics", "📥 Export"])

    with tabs[0]:  # Map
        m = folium.Map(location=area["coords"][::-1], zoom_start=11)
        # GEE tile layers add হবে এখানে
        st_folium(m, height=500, use_container_width=True)

    with tabs[1]:  # Charts
        col1, col2 = st.columns(2)

        if show_ndvi:
            with col1:
                with st.spinner("Fetching NDVI data..."):
                    ts = get_ndvi_timeseries(geometry, str(start_date), str(end_date))
                    df = pd.DataFrame([f["properties"] for f in ts["features"]])
                    if not df.empty:
                        fig = px.line(
                            df,
                            x="date",
                            y="NDVI_mean",
                            title="NDVI Time Series",
                            color_discrete_sequence=["#4CAF50"],
                        )
                        fig.add_hline(
                            y=0.3, line_dash="dash", annotation_text="Drought threshold"
                        )
                        st.plotly_chart(fig, use_container_width=True)

        if show_rainfall:
            with col2:
                with st.spinner("Fetching rainfall data..."):
                    rf_ts = get_monthly_rainfall(
                        geometry, str(start_date), str(end_date)
                    )
                    df_rf = pd.DataFrame([f["properties"] for f in rf_ts["features"]])
                    if not df_rf.empty:
                        fig2 = px.bar(
                            df_rf,
                            x="date",
                            y="rainfall_mm",
                            title="Daily Rainfall (CHIRPS)",
                            color_discrete_sequence=["#2196F3"],
                        )
                        st.plotly_chart(fig2, use_container_width=True)

    with tabs[2]:  # Statistics
        col1, col2, col3, col4 = st.columns(4)

        if show_ndvi:
            _, ndvi_stats = get_ndvi(geometry, str(start_date), str(end_date))
            stats = ndvi_stats.getInfo()
            col1.metric("🌿 Mean NDVI", f"{stats.get('NDVI_mean', 0):.3f}")

        if show_lst:
            _, lst_stats = get_lst(geometry, str(start_date), str(end_date))
            stats_lst = lst_stats.getInfo()
            col3.metric(
                "🌡️ Mean LST (°C)", f"{stats_lst.get('LST_Celsius_mean', 0):.1f}°C"
            )

    with tabs[3]:  # Export
        st.download_button(
            "📥 Download CSV",
            data="date,NDVI,LST,Rainfall\n",
            file_name="drought_analysis.csv",
            mime="text/csv",
        )
