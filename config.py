"""
config.py — Central configuration for Drought Dashboard
Area boundaries, date presets, thresholds, GEE dataset IDs
"""

AREAS = {
    "Sapahar Upazila": {
        "district": "Naogaon", "division": "Rajshahi",
        "lat": 24.8833, "lon": 88.4333, "gaul_name": "Sapahar",
    },
    "Porsha Upazila": {
        "district": "Naogaon", "division": "Rajshahi",
        "lat": 24.9167, "lon": 88.5167, "gaul_name": "Porsha",
    },
    "Badalgachi Upazila": {
        "district": "Naogaon", "division": "Rajshahi",
        "lat": 24.7333, "lon": 88.6167, "gaul_name": "Badalgachhi",
    },
    "Manda Upazila": {
        "district": "Naogaon", "division": "Rajshahi",
        "lat": 24.7167, "lon": 88.8667, "gaul_name": "Manda",
    },
    "Niamatpur Upazila": {
        "district": "Naogaon", "division": "Rajshahi",
        "lat": 24.6833, "lon": 88.7000, "gaul_name": "Niamatpur",
    },
    "Naogaon Sadar": {
        "district": "Naogaon", "division": "Rajshahi",
        "lat": 24.9133, "lon": 88.7514, "gaul_name": "Naogaon",
    },
    "Rajshahi Sadar": {
        "district": "Rajshahi", "division": "Rajshahi",
        "lat": 24.3636, "lon": 88.6241, "gaul_name": "Rajshahi",
    },
    "Chapai Nawabganj": {
        "district": "Chapai Nawabganj", "division": "Rajshahi",
        "lat": 24.5972, "lon": 88.2733, "gaul_name": "Chapai Nawabgonj",
    },
}

DATE_PRESETS = {
    "2020 Boro Season (Jan–Jun)":     ("2020-01-01", "2020-06-30"),
    "2021 Boro Season (Jan–Jun)":     ("2021-01-01", "2021-06-30"),
    "2022 Drought Period (Mar–Sep)":  ("2022-03-01", "2022-09-30"),
    "2022 Full Year":                 ("2022-01-01", "2022-12-31"),
    "2023 Aman Season (Jun–Nov)":     ("2023-06-01", "2023-11-30"),
    "2023 Full Year":                 ("2023-01-01", "2023-12-31"),
    "2024 Full Year":                 ("2024-01-01", "2024-12-31"),
    "Custom Range":                   None,
}

DROUGHT_THRESHOLDS = {
    "ndvi":               {"normal": 0.5,  "mild": 0.4,  "moderate": 0.3,  "severe": 0.2},
    "rainfall_mm":        {"normal": 100,  "mild": 75,   "moderate": 50,   "severe": 25},
    "lst_celsius":        {"normal": 32,   "mild": 35,   "moderate": 38,   "severe": 42},
    "soil_moisture":      {"normal": 0.25, "mild": 0.20, "moderate": 0.15, "severe": 0.10},
}

GEE_DATASETS = {
    "sentinel2": "COPERNICUS/S2_SR_HARMONIZED",
    "chirps":    "UCSB-CHG/CHIRPS/DAILY",
    "modis_lst": "MODIS/061/MOD11A2",
    "smap":      "NASA_USDA/HSL/SMAP10KM_soil_moisture",
    "gaul3":     "FAO/GAUL/2015/level3",
}

BUFFER_METERS = 12000
DEFAULT_ZOOM  = 10

VIS_PARAMS = {
    "ndvi": {
        "min": -0.2, "max": 0.8,
        "palette": ["#d73027","#f46d43","#fdae61","#fee08b","#d9ef8b","#a6d96a","#1a9850"],
    },
    "lst": {
        "min": 20, "max": 50,
        "palette": ["#313695","#4575b4","#74add1","#abd9e9","#fee090","#fdae61","#d73027"],
    },
    "rainfall": {
        "min": 0, "max": 20,
        "palette": ["#f7fbff","#c6dbef","#6baed6","#2171b5","#08306b"],
    },
    "soil_moisture": {
        "min": 0, "max": 0.5,
        "palette": ["#8c510a","#d8b365","#f6e8c3","#c7eae5","#5ab4ac","#01665e"],
    },
}
