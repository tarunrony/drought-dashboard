"""
app.py
Drought Analysis Dashboard — Bangladesh
Sapahar Upazila & surrounding areas | Google Earth Engine + Streamlit
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import io
from datetime import date, datetime

# ── Page config (must be first Streamlit call) ────────────────
st.set_page_config(
    page_title="Drought Dashboard — Bangladesh",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* General */
html, body, [data-testid="stAppViewContainer"] {
    background: #0e1117;
}
/* Metric cards */
.metric-box {
    background: linear-gradient(135deg, #1a1f2e, #1e2a1e);
    border: 1px solid rgba(76,175,80,0.25);
    border-left: 4px solid #4CAF50;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 6px 0;
}
.metric-box.red   { border-left-color: #f44336; border-color: rgba(244,67,54,0.25); background: linear-gradient(135deg,#1a1f2e,#2a1e1e); }
.metric-box.blue  { border-left-color: #2196F3; border-color: rgba(33,150,243,0.25); background: linear-gradient(135deg,#1a1f2e,#1e1e2a); }
.metric-box.teal  { border-left-color: #00BCD4; border-color: rgba(0,188,212,0.25);  background: linear-gradient(135deg,#1a1f2e,#1e2a2a); }
.metric-label { font-size: 12px; color: #9e9e9e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.metric-value { font-size: 28px; font-weight: 700; color: #fff; }
.metric-sub   { font-size: 11px; color: #757575; margin-top: 2px; }

/* Severity badge */
.sev-normal   { background:#1b5e20; color:#a5d6a7; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.sev-mild     { background:#f57f17; color:#fff9c4; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.sev-moderate { background:#bf360c; color:#ffccbc; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.sev-severe   { background:#b71c1c; color:#ffcdd2; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }

/* Status bar */
.status-ok  { background:#1b5e20; color:#c8e6c9; padding:6px 16px; border-radius:6px; font-size:13px; display:inline-block; }
.status-err { background:#b71c1c; color:#ffcdd2; padding:6px 16px; border-radius:6px; font-size:13px; display:inline-block; }

/* Tabs */
.stTabs [data-baseweb="tab"] { color: #9e9e9e; font-size: 14px; }
.stTabs [aria-selected="true"] { color: #4CAF50 !important; border-bottom: 2px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)


# ── Imports (after page config) ───────────────────────────────
from config import AREAS, DATE_PRESETS, DROUGHT_THRESHOLDS, VIS_PARAMS, BUFFER_METERS
from modules.gee_connect import initialize_gee, get_geometry
from modules.ndvi         import get_ndvi_image, get_ndvi_timeseries, get_ndwi_image
from modules.rainfall     import get_rainfall_image, get_rainfall_timeseries
from modules.lst          import get_lst_image, get_lst_timeseries
from modules.soil_moisture import get_smap_image, get_smap_timeseries
from utils.chart_utils    import (ndvi_chart, rainfall_chart,
                                  lst_chart, soil_moisture_chart, comparison_radar)
from utils.map_utils      import build_base_map, add_gee_layer, add_area_marker, add_legend


# ── GEE Initialization ────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_gee():
    return initialize_gee()


# ── Cached GEE fetch functions ────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ndvi(area_name, start_date, end_date):
    from modules.gee_connect import get_geometry
    geom = get_geometry(AREAS[area_name], BUFFER_METERS)
    img, stats = get_ndvi_image(geom, start_date, end_date)
    ts         = get_ndvi_timeseries(geom, start_date, end_date)
    return stats, ts

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_rainfall(area_name, start_date, end_date):
    from modules.gee_connect import get_geometry
    geom = get_geometry(AREAS[area_name], BUFFER_METERS)
    _, stats = get_rainfall_image(geom, start_date, end_date)
    ts       = get_rainfall_timeseries(geom, start_date, end_date)
    return stats, ts

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_lst(area_name, start_date, end_date):
    from modules.gee_connect import get_geometry
    geom = get_geometry(AREAS[area_name], BUFFER_METERS)
    _, stats = get_lst_image(geom, start_date, end_date)
    ts       = get_lst_timeseries(geom, start_date, end_date)
    return stats, ts

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_moisture(area_name, start_date, end_date):
    from modules.gee_connect import get_geometry
    geom = get_geometry(AREAS[area_name], BUFFER_METERS)
    _, stats = get_smap_image(geom, start_date, end_date)
    ts       = get_smap_timeseries(geom, start_date, end_date)
    return stats, ts


# ── Drought severity helper ───────────────────────────────────
def get_severity(param: str, value: float | None) -> tuple[str, str]:
    """Returns (label, css_class) for a parameter value."""
    if value is None:
        return "N/A", "sev-normal"
    t = DROUGHT_THRESHOLDS.get(param, {})
    if param == "lst_celsius":
        if value >= t.get("severe", 42):   return "Severe",   "sev-severe"
        if value >= t.get("moderate", 38): return "Moderate", "sev-moderate"
        if value >= t.get("mild", 35):     return "Mild",     "sev-mild"
        return "Normal", "sev-normal"
    else:  # NDVI, soil_moisture, rainfall_mm — higher is better
        key = "ndvi" if param == "ndvi" else ("soil_moisture" if param == "soil_moisture" else "rainfall_mm")
        thresh = DROUGHT_THRESHOLDS.get(key, t)
        if value <= thresh.get("severe",   0.2): return "Severe",   "sev-severe"
        if value <= thresh.get("moderate", 0.3): return "Moderate", "sev-moderate"
        if value <= thresh.get("mild",     0.4): return "Mild",     "sev-mild"
        return "Normal", "sev-normal"


def metric_card(label: str, value: str, sub: str = "", color: str = "green") -> str:
    cls_map = {"green": "", "red": "red", "blue": "blue", "teal": "teal"}
    cls = cls_map.get(color, "")
    return f"""
    <div class="metric-box {cls}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-sub">{sub}</div>
    </div>
    """


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌾 Drought Dashboard")
    st.markdown("**Agricultural Analysis — Bangladesh**")
    st.divider()

    # ── Area selection ────────────────────────────────────────
    st.markdown("### 📍 Select Areas")
    selected_areas = st.multiselect(
        "Upazilas / Districts",
        options=list(AREAS.keys()),
        default=["Sapahar Upazila"],
        help="Select one or more areas to analyze",
    )
    primary_area = selected_areas[0] if selected_areas else "Sapahar Upazila"

    st.divider()

    # ── Date range ────────────────────────────────────────────
    st.markdown("### 📅 Date Range")
    preset = st.selectbox("Preset Period", list(DATE_PRESETS.keys()), index=3)

    if preset == "Custom Range":
        c1, c2 = st.columns(2)
        start_date = str(c1.date_input("From", date(2022, 1, 1)))
        end_date   = str(c2.date_input("To",   date(2022, 12, 31)))
    else:
        start_date, end_date = DATE_PRESETS[preset]

    st.caption(f"📆 {start_date}  →  {end_date}")
    st.divider()

    # ── Parameters ────────────────────────────────────────────
    st.markdown("### 📊 Parameters")
    show_ndvi     = st.checkbox("🌿 NDVI — Crop Health",         value=True)
    show_rainfall = st.checkbox("🌧️ Rainfall — CHIRPS",          value=True)
    show_lst      = st.checkbox("🌡️ Land Surface Temp",          value=True)
    show_moisture = st.checkbox("💧 Soil Moisture — SMAP",       value=True)
    st.divider()

    # ── Map layers ────────────────────────────────────────────
    st.markdown("### 🗺️ Map Layer")
    map_layer = st.radio(
        "Overlay",
        ["None", "NDVI Heatmap", "LST Heatmap", "Rainfall", "Soil Moisture"],
        index=1,
    )

    run_btn = st.button("🔍  Run Analysis", type="primary", use_container_width=True)

    st.divider()
    st.caption(f"Last run: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🌍 Agricultural Drought Analysis")
    st.caption(
        f"**Areas:** {', '.join(selected_areas) or 'None selected'}  |  "
        f"**Period:** {start_date} → {end_date}"
    )
with col_status:
    gee_ok = load_gee()
    if gee_ok:
        st.markdown('<span class="status-ok">🟢 GEE Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-err">🔴 GEE Offline</span>', unsafe_allow_html=True)

st.divider()

if not gee_ok:
    st.error("GEE not connected. Check authentication setup in `gee_auth/` folder.")
    st.stop()

if not selected_areas:
    st.info("👈 Select at least one area from the sidebar, then click **Run Analysis**.")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# ANALYSIS STATE
# ═══════════════════════════════════════════════════════════════
if "results" not in st.session_state:
    st.session_state.results = {}

if run_btn:
    st.session_state.results = {}
    progress = st.progress(0, text="Fetching data from GEE…")
    total_steps = len(selected_areas) * sum([show_ndvi, show_rainfall, show_lst, show_moisture])
    step = 0

    for area_name in selected_areas:
        area_data = {}

        if show_ndvi:
            with st.spinner(f"NDVI — {area_name}"):
                try:
                    stats, ts = fetch_ndvi(area_name, start_date, end_date)
                    area_data["ndvi"] = {"stats": stats, "ts": ts}
                except Exception as e:
                    area_data["ndvi"] = {"error": str(e)}
            step += 1; progress.progress(step / max(total_steps, 1), text=f"NDVI done — {area_name}")

        if show_rainfall:
            with st.spinner(f"Rainfall — {area_name}"):
                try:
                    stats, ts = fetch_rainfall(area_name, start_date, end_date)
                    area_data["rainfall"] = {"stats": stats, "ts": ts}
                except Exception as e:
                    area_data["rainfall"] = {"error": str(e)}
            step += 1; progress.progress(step / max(total_steps, 1), text=f"Rainfall done — {area_name}")

        if show_lst:
            with st.spinner(f"LST — {area_name}"):
                try:
                    stats, ts = fetch_lst(area_name, start_date, end_date)
                    area_data["lst"] = {"stats": stats, "ts": ts}
                except Exception as e:
                    area_data["lst"] = {"error": str(e)}
            step += 1; progress.progress(step / max(total_steps, 1), text=f"LST done — {area_name}")

        if show_moisture:
            with st.spinner(f"Soil Moisture — {area_name}"):
                try:
                    stats, ts = fetch_moisture(area_name, start_date, end_date)
                    area_data["moisture"] = {"stats": stats, "ts": ts}
                except Exception as e:
                    area_data["moisture"] = {"error": str(e)}
            step += 1; progress.progress(step / max(total_steps, 1), text=f"Moisture done — {area_name}")

        st.session_state.results[area_name] = area_data

    progress.empty()
    st.success("✅ Analysis complete!")


# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════
tab_map, tab_charts, tab_stats, tab_compare, tab_export = st.tabs([
    "🗺️ Map View",
    "📈 Time Series Charts",
    "📋 Statistics",
    "🔁 Area Comparison",
    "📥 Export Data",
])


# ── TAB 1: MAP ────────────────────────────────────────────────
with tab_map:
    area_cfg = AREAS[primary_area]
    m = build_base_map(area_cfg["lat"], area_cfg["lon"], zoom=10)

    # Add markers for all selected areas
    for a in selected_areas:
        cfg = AREAS[a]
        m = add_area_marker(m, cfg["lat"], cfg["lon"], a)

    # GEE overlay layer
    if st.session_state.results and map_layer != "None":
        try:
            import ee
            geom = get_geometry(AREAS[primary_area], BUFFER_METERS)
            with st.spinner("Loading map layer…"):
                if map_layer == "NDVI Heatmap" and show_ndvi:
                    from modules.ndvi import get_ndvi_image
                    img, _ = get_ndvi_image(geom, start_date, end_date)
                    m = add_gee_layer(m, img, VIS_PARAMS["ndvi"], "NDVI")
                    m = add_legend(m, "NDVI",
                        ["#d73027","#fdae61","#fee08b","#d9ef8b","#1a9850"],
                        ["<0.0", "0.2", "0.4", "0.5", "0.65+"])
                elif map_layer == "LST Heatmap" and show_lst:
                    from modules.lst import get_lst_image
                    img, _ = get_lst_image(geom, start_date, end_date)
                    m = add_gee_layer(m, img, VIS_PARAMS["lst"], "LST (°C)")
                    m = add_legend(m, "LST (°C)",
                        ["#313695","#74add1","#fee090","#fdae61","#d73027"],
                        ["20°C", "27°C", "34°C", "41°C", "48°C+"])
                elif map_layer == "Rainfall":
                    from modules.rainfall import get_rainfall_image
                    img, _ = get_rainfall_image(geom, start_date, end_date)
                    m = add_gee_layer(m, img, VIS_PARAMS["rainfall"], "Rainfall (mm)")
                elif map_layer == "Soil Moisture":
                    from modules.soil_moisture import get_smap_image
                    img, _ = get_smap_image(geom, start_date, end_date)
                    if img:
                        m = add_gee_layer(m, img, VIS_PARAMS["soil_moisture"], "Soil Moisture")
        except Exception as e:
            st.warning(f"Map layer error: {e}")

    folium.LayerControl().add_to(m)
    st_folium(m, height=520, use_container_width=True)
    st.caption(f"Showing: **{primary_area}** | Layer: **{map_layer}**")


# ── TAB 2: CHARTS ─────────────────────────────────────────────
with tab_charts:
    if not st.session_state.results:
        st.info("Run analysis first (click **Run Analysis** in the sidebar).")
    else:
        area_data = st.session_state.results.get(primary_area, {})

        if len(selected_areas) > 1:
            chart_area = st.selectbox("Select area for charts", selected_areas)
            area_data  = st.session_state.results.get(chart_area, {})

        col1, col2 = st.columns(2)

        if show_ndvi and "ndvi" in area_data:
            nd = area_data["ndvi"]
            with col1:
                if "error" in nd:
                    st.error(f"NDVI: {nd['error']}")
                elif not nd["ts"].empty:
                    st.plotly_chart(ndvi_chart(nd["ts"]), use_container_width=True)
                else:
                    st.warning("No NDVI data for this period.")

        if show_rainfall and "rainfall" in area_data:
            rf = area_data["rainfall"]
            with col2:
                if "error" in rf:
                    st.error(f"Rainfall: {rf['error']}")
                elif not rf["ts"].empty:
                    st.plotly_chart(rainfall_chart(rf["ts"]), use_container_width=True)
                else:
                    st.warning("No rainfall data for this period.")

        col3, col4 = st.columns(2)

        if show_lst and "lst" in area_data:
            ls = area_data["lst"]
            with col3:
                if "error" in ls:
                    st.error(f"LST: {ls['error']}")
                elif not ls["ts"].empty:
                    st.plotly_chart(lst_chart(ls["ts"]), use_container_width=True)
                else:
                    st.warning("No LST data for this period.")

        if show_moisture and "moisture" in area_data:
            mo = area_data["moisture"]
            with col4:
                if "error" in mo:
                    st.error(f"Soil Moisture: {mo['error']}")
                elif not mo["ts"].empty:
                    st.plotly_chart(soil_moisture_chart(mo["ts"]), use_container_width=True)
                else:
                    st.warning("No SMAP soil moisture data for this period.")


# ── TAB 3: STATISTICS ─────────────────────────────────────────
with tab_stats:
    if not st.session_state.results:
        st.info("Run analysis first.")
    else:
        area_data = st.session_state.results.get(primary_area, {})
        if len(selected_areas) > 1:
            stat_area = st.selectbox("Select area for statistics", selected_areas, key="stat_sel")
            area_data = st.session_state.results.get(stat_area, {})

        st.markdown(f"### 📊 Summary — {primary_area if len(selected_areas)==1 else stat_area}")

        c1, c2, c3, c4 = st.columns(4)

        # NDVI
        ndvi_mean = None
        if show_ndvi and "ndvi" in area_data and "stats" in area_data["ndvi"]:
            ndvi_mean = area_data["ndvi"]["stats"].get("mean")
            sev, _ = get_severity("ndvi", ndvi_mean)
            c1.markdown(
                metric_card("🌿 Mean NDVI", f"{ndvi_mean:.3f}" if ndvi_mean else "N/A",
                            f"Drought: {sev}", "green"),
                unsafe_allow_html=True,
            )

        # Rainfall
        rain_total = None
        if show_rainfall and "rainfall" in area_data and "stats" in area_data["rainfall"]:
            rain_total = area_data["rainfall"]["stats"].get("total_mm")
            sev, _ = get_severity("rainfall_mm", rain_total)
            c2.markdown(
                metric_card("🌧️ Total Rainfall", f"{rain_total:.1f} mm" if rain_total else "N/A",
                            f"Drought: {sev}", "blue"),
                unsafe_allow_html=True,
            )

        # LST
        lst_mean = None
        if show_lst and "lst" in area_data and "stats" in area_data["lst"]:
            lst_mean = area_data["lst"]["stats"].get("mean_c")
            sev, _ = get_severity("lst_celsius", lst_mean)
            c3.markdown(
                metric_card("🌡️ Mean LST", f"{lst_mean:.1f} °C" if lst_mean else "N/A",
                            f"Drought: {sev}", "red"),
                unsafe_allow_html=True,
            )

        # Soil Moisture
        ssm_mean = None
        if show_moisture and "moisture" in area_data and "stats" in area_data["moisture"]:
            ssm_mean = area_data["moisture"]["stats"].get("mean")
            sev, _ = get_severity("soil_moisture", ssm_mean)
            c4.markdown(
                metric_card("💧 Soil Moisture", f"{ssm_mean:.4f}" if ssm_mean else "N/A",
                            f"Drought: {sev}", "teal"),
                unsafe_allow_html=True,
            )

        st.divider()

        # Overall severity assessment
        st.markdown("### 🚨 Overall Drought Severity")
        scores = []
        if ndvi_mean   is not None: scores.append(1 - min(max(ndvi_mean / 0.8, 0), 1))
        if lst_mean    is not None: scores.append(min(max((lst_mean - 20) / 30, 0), 1))
        if ssm_mean    is not None: scores.append(1 - min(max(ssm_mean / 0.5, 0), 1))
        if rain_total  is not None: scores.append(1 - min(max(rain_total / 500, 0), 1))

        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score >= 0.75:   overall, badge = "SEVERE",   "sev-severe"
            elif avg_score >= 0.50: overall, badge = "MODERATE", "sev-moderate"
            elif avg_score >= 0.25: overall, badge = "MILD",     "sev-mild"
            else:                   overall, badge = "NORMAL",   "sev-normal"

            st.markdown(
                f"**Drought Index Score:** `{avg_score:.2f}` &nbsp;&nbsp;"
                f'<span class="{badge}">{overall}</span>',
                unsafe_allow_html=True,
            )
            st.caption("Score: 0.0 = No drought | 1.0 = Extreme drought")
            st.progress(avg_score)


# ── TAB 4: COMPARISON ─────────────────────────────────────────
with tab_compare:
    if not st.session_state.results or len(st.session_state.results) < 2:
        st.info("Select **2 or more areas** in the sidebar and run analysis to compare.")
    else:
        # Build comparison table
        rows = []
        radar_stats = []
        for area_name, area_data in st.session_state.results.items():
            row = {"Area": area_name}
            rstat = {}
            if "ndvi"     in area_data and "stats" in area_data["ndvi"]:
                v = area_data["ndvi"]["stats"].get("mean"); row["NDVI Mean"] = round(v,3) if v else "N/A"; rstat["ndvi_mean"] = v or 0
            if "rainfall" in area_data and "stats" in area_data["rainfall"]:
                v = area_data["rainfall"]["stats"].get("total_mm"); row["Rainfall (mm)"] = round(v,1) if v else "N/A"; rstat["rain_total"] = v or 0
            if "lst"      in area_data and "stats" in area_data["lst"]:
                v = area_data["lst"]["stats"].get("mean_c"); row["LST (°C)"] = round(v,1) if v else "N/A"; rstat["lst_mean"] = v or 30
            if "moisture" in area_data and "stats" in area_data["moisture"]:
                v = area_data["moisture"]["stats"].get("mean"); row["Soil Moisture"] = round(v,4) if v else "N/A"; rstat["ssm_mean"] = v or 0
            rows.append(row)
            radar_stats.append(rstat)

        df_cmp = pd.DataFrame(rows).set_index("Area")
        st.dataframe(df_cmp, use_container_width=True)
        st.divider()

        # Radar chart
        fig_radar = comparison_radar(radar_stats, list(st.session_state.results.keys()))
        st.plotly_chart(fig_radar, use_container_width=True)


# ── TAB 5: EXPORT ─────────────────────────────────────────────
with tab_export:
    if not st.session_state.results:
        st.info("Run analysis first.")
    else:
        st.markdown("### 📥 Download Data")

        # Merge all time-series into one CSV per parameter
        for param, label, ts_key in [
            ("ndvi",     "NDVI",          "ts"),
            ("rainfall", "Rainfall",      "ts"),
            ("lst",      "LST",           "ts"),
            ("moisture", "Soil Moisture", "ts"),
        ]:
            frames = []
            for area_name, area_data in st.session_state.results.items():
                if param in area_data and ts_key in area_data[param]:
                    df_tmp = area_data[param][ts_key].copy()
                    df_tmp.insert(0, "Area", area_name)
                    frames.append(df_tmp)
            if frames:
                merged = pd.concat(frames, ignore_index=True)
                csv_bytes = merged.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"⬇️  {label} Time Series (.csv)",
                    data=csv_bytes,
                    file_name=f"drought_{param}_{start_date}_{end_date}.csv",
                    mime="text/csv",
                )

        st.divider()
        st.markdown("### 📋 Summary Statistics")
        summary_rows = []
        for area_name, area_data in st.session_state.results.items():
            row = {"Area": area_name, "Period Start": start_date, "Period End": end_date}
            if "ndvi"     in area_data and "stats" in area_data["ndvi"]:
                for k, v in area_data["ndvi"]["stats"].items():
                    row[f"NDVI_{k}"] = v
            if "rainfall" in area_data and "stats" in area_data["rainfall"]:
                for k, v in area_data["rainfall"]["stats"].items():
                    row[f"Rain_{k}"] = v
            if "lst"      in area_data and "stats" in area_data["lst"]:
                for k, v in area_data["lst"]["stats"].items():
                    row[f"LST_{k}"] = v
            if "moisture" in area_data and "stats" in area_data["moisture"]:
                for k, v in area_data["moisture"]["stats"].items():
                    row[f"SSM_{k}"] = v
            summary_rows.append(row)

        if summary_rows:
            df_sum = pd.DataFrame(summary_rows)
            st.dataframe(df_sum, use_container_width=True)
            st.download_button(
                "⬇️  Summary Statistics (.csv)",
                data=df_sum.to_csv(index=False).encode("utf-8"),
                file_name=f"drought_summary_{start_date}_{end_date}.csv",
                mime="text/csv",
            )
