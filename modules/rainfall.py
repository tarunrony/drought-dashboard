"""
modules/rainfall.py
Rainfall analysis using CHIRPS Daily dataset.
"""

import ee
import pandas as pd
from config import GEE_DATASETS


def get_rainfall_image(geometry, start_date: str, end_date: str):
    """Total accumulated rainfall image + stats."""
    col       = (
        ee.ImageCollection(GEE_DATASETS["chirps"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .select("precipitation")
    )
    total_img = col.sum().clip(geometry)
    stats     = total_img.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.sum(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True),
        geometry=geometry, scale=5000, maxPixels=1e9,
    ).getInfo()
    return total_img, {
        "total_mm": round(stats.get("precipitation_sum",  0) or 0, 1),
        "mean_mm":  round(stats.get("precipitation_mean", 0) or 0, 2),
        "max_mm":   round(stats.get("precipitation_max",  0) or 0, 1),
    }


def get_rainfall_timeseries(geometry, start_date: str, end_date: str) -> pd.DataFrame:
    """Daily rainfall time-series."""
    col = (
        ee.ImageCollection(GEE_DATASETS["chirps"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .select("precipitation")
    )

    def extract(image):
        val = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry, scale=5000, maxPixels=1e9,
        )
        return ee.Feature(None, {
            "date":         image.date().format("YYYY-MM-dd"),
            "rainfall_mm":  val.get("precipitation"),
        })

    features = col.map(extract).getInfo().get("features", [])
    if not features:
        return pd.DataFrame(columns=["date", "rainfall_mm"])
    df = pd.DataFrame([f["properties"] for f in features])
    df["date"]        = pd.to_datetime(df["date"])
    df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)

    # Add 7-day rolling average
    df["rolling_7d"] = df["rainfall_mm"].rolling(7, min_periods=1).mean().round(2)
    return df
