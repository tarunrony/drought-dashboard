"""
modules/lst.py
Land Surface Temperature using MODIS MOD11A2 (8-day composite).
Converts Kelvin → Celsius automatically.
"""

import ee
import pandas as pd
from config import GEE_DATASETS


def _to_celsius(image):
    """Scale factor 0.02, then subtract 273.15 K → °C."""
    lst_c = image.select("LST_Day_1km").multiply(0.02).subtract(273.15).rename("LST_C")
    return lst_c.copyProperties(image, ["system:time_start"])


def get_lst_image(geometry, start_date: str, end_date: str):
    """Mean LST image (°C) + stats."""
    col      = (
        ee.ImageCollection(GEE_DATASETS["modis_lst"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .map(_to_celsius)
    )
    mean_img = col.mean().clip(geometry)
    stats    = mean_img.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True),
        geometry=geometry, scale=1000, maxPixels=1e9,
    ).getInfo()
    return mean_img, {
        "mean_c": round(stats.get("LST_C_mean", 0) or 0, 1),
        "min_c":  round(stats.get("LST_C_min",  0) or 0, 1),
        "max_c":  round(stats.get("LST_C_max",  0) or 0, 1),
    }


def get_lst_timeseries(geometry, start_date: str, end_date: str) -> pd.DataFrame:
    """8-day LST time-series (°C)."""
    col = (
        ee.ImageCollection(GEE_DATASETS["modis_lst"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .map(_to_celsius)
    )

    def extract(image):
        val = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry, scale=1000, maxPixels=1e9,
        )
        return ee.Feature(None, {
            "date":   image.date().format("YYYY-MM-dd"),
            "LST_C":  val.get("LST_C"),
        })

    features = col.map(extract).getInfo().get("features", [])
    if not features:
        return pd.DataFrame(columns=["date", "LST_C"])
    df = pd.DataFrame([f["properties"] for f in features])
    df["date"]  = pd.to_datetime(df["date"])
    df["LST_C"] = pd.to_numeric(df["LST_C"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)
