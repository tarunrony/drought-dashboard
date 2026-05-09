"""
modules/gee_connect.py
GEE authentication — Service Account (deploy) or personal auth (local).
"""

import ee
import os
import json
import streamlit as st


def initialize_gee() -> bool:
    """Try Service Account → JSON file → personal auth. Returns True on success."""

    # ── 1. Streamlit Cloud secrets (production) ──────────────────
    try:
        sa_email   = st.secrets.get("GEE_SERVICE_ACCOUNT", "")
        project_id = st.secrets.get("GEE_PROJECT_ID", "")
        sa_key_str = st.secrets.get("GEE_KEY_JSON", "")
        if sa_email and project_id and sa_key_str:
            creds = ee.ServiceAccountCredentials(
                email=sa_email,
                key_data=sa_key_str,
            )
            ee.Initialize(creds, project=project_id)
            return True
    except Exception:
        pass

    # ── 2. Local JSON file ───────────────────────────────────────
    try:
        sa_file    = "gee_auth/service-account.json"
        project_id = os.environ.get("GEE_PROJECT_ID", "")
        if os.path.exists(sa_file):
            with open(sa_file) as f:
                key_data = json.load(f)
            creds = ee.ServiceAccountCredentials(
                email=key_data["client_email"],
                key_file=sa_file,
            )
            ee.Initialize(creds, project=project_id or key_data.get("project_id", ""))
            return True
    except Exception:
        pass

    # ── 3. Personal auth (earthengine authenticate) ──────────────
    try:
        ee.Initialize()
        return True
    except Exception as e:
        st.error(f"❌ GEE init failed: {e}")
        st.markdown(
            "**Fix:** Run `earthengine authenticate` in terminal, "
            "or add your Service Account JSON to `gee_auth/service-account.json` "
            "and set `GEE_PROJECT_ID` in your `.env`."
        )
        return False


def get_geometry(area_cfg: dict, buffer_m: int = 12000):
    """Return ee.Geometry for an upazila — GAUL boundary or buffered point."""
    try:
        gaul  = ee.FeatureCollection("FAO/GAUL/2015/level3")
        match = gaul.filter(
            ee.Filter.And(
                ee.Filter.eq("ADM2_NAME", area_cfg.get("district", "")),
                ee.Filter.eq("ADM3_NAME", area_cfg.get("gaul_name", "")),
            )
        )
        if match.size().getInfo() > 0:
            return match.geometry()
    except Exception:
        pass
    # Fallback
    return ee.Geometry.Point([area_cfg["lon"], area_cfg["lat"]]).buffer(buffer_m)
