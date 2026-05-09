"""
modules/soil_moisture.py
Soil moisture analysis using NASA SMAP 10km dataset.
Also provides NDWI from Sentinel-2 as supplementary moisture index.
"""

import ee
import pandas as pd
from config import GEE_DATASETS


def get_smap_image(geometry, start_date: str, end_date: str):
    """Mean SMAP surface soil moisture image + stats."""
    col = (
        ee.ImageCollection(GEE_DATASETS["smap"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .select("ssm")
    )
    size = col.size().getInfo()
    if size == 0:
        return None, {"mean": None, "min": None, "max": None}

    mean_img = col.mean().clip(geometry)
    stats    = mean_img.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True),
        geometry=geometry, scale=10000, maxPixels=1e9,
    ).getInfo()
    return mean_img, {
        "mean": round(stats.get("ssm_mean", 0) or 0, 4),
        "min":  round(stats.get("ssm_min",  0) or 0, 4),
        "max":  round(stats.get("ssm_max",  0) or 0, 4),
    }


def get_smap_timeseries(geometry, start_date: str, end_date: str) -> pd.DataFrame:
    """Daily soil moisture time-series from SMAP."""
    col = (
        ee.ImageCollection(GEE_DATASETS["smap"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .select("ssm")
    )

    def extract(image):
        val = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry, scale=10000, maxPixels=1e9,
        )
        return ee.Feature(None, {
            "date": image.date().format("YYYY-MM-dd"),
            "ssm":  val.get("ssm"),
        })

    features = col.map(extract).getInfo().get("features", [])
    if not features:
        return pd.DataFrame(columns=["date", "ssm"])
    df = pd.DataFrame([f["properties"] for f in features])
    df["date"] = pd.to_datetime(df["date"])
    df["ssm"]  = pd.to_numeric(df["ssm"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)
