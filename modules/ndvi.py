"""
modules/ndvi.py
NDVI analysis using Sentinel-2 SR Harmonized.
Returns mean image + statistics + monthly time-series.
"""

import ee
import pandas as pd
from config import GEE_DATASETS


def _mask_clouds(image):
    qa = image.select("QA60")
    mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    return image.updateMask(mask)


def _add_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


def _add_ndwi(image):
    ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
    return image.addBands(ndwi)


def _base_collection(geometry, start_date, end_date):
    return (
        ee.ImageCollection(GEE_DATASETS["sentinel2"])
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(_mask_clouds)
    )


# ── Mean NDVI image + stats ──────────────────────────────────
def get_ndvi_image(geometry, start_date: str, end_date: str):
    col      = _base_collection(geometry, start_date, end_date).map(_add_ndvi)
    mean_img = col.select("NDVI").mean().clip(geometry)
    stats    = mean_img.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(),    sharedInputs=True)
            .combine(ee.Reducer.max(),    sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=geometry, scale=30, maxPixels=1e9,
    ).getInfo()
    return mean_img, {
        "mean":   round(stats.get("NDVI_mean",   0) or 0, 4),
        "min":    round(stats.get("NDVI_min",    0) or 0, 4),
        "max":    round(stats.get("NDVI_max",    0) or 0, 4),
        "stddev": round(stats.get("NDVI_stdDev", 0) or 0, 4),
    }


# ── Mean NDWI image + stats ──────────────────────────────────
def get_ndwi_image(geometry, start_date: str, end_date: str):
    col      = _base_collection(geometry, start_date, end_date).map(_add_ndwi)
    mean_img = col.select("NDWI").mean().clip(geometry)
    stats    = mean_img.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True),
        geometry=geometry, scale=30, maxPixels=1e9,
    ).getInfo()
    return mean_img, {
        "mean": round(stats.get("NDWI_mean", 0) or 0, 4),
        "min":  round(stats.get("NDWI_min",  0) or 0, 4),
        "max":  round(stats.get("NDWI_max",  0) or 0, 4),
    }


# ── Monthly NDVI time-series ─────────────────────────────────
def get_ndvi_timeseries(geometry, start_date: str, end_date: str) -> pd.DataFrame:
    col = _base_collection(geometry, start_date, end_date).map(_add_ndvi)

    def extract(image):
        val = image.select("NDVI").reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry, scale=30, maxPixels=1e9,
        )
        return ee.Feature(None, {
            "date":      image.date().format("YYYY-MM-dd"),
            "NDVI_mean": val.get("NDVI"),
        })

    features = col.map(extract).getInfo().get("features", [])
    if not features:
        return pd.DataFrame(columns=["date", "NDVI_mean"])
    df = pd.DataFrame([f["properties"] for f in features])
    df["date"] = pd.to_datetime(df["date"])
    df["NDVI_mean"] = pd.to_numeric(df["NDVI_mean"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)
