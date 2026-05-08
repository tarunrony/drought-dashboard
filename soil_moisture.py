import ee


def get_ndwi(area_geometry, start_date, end_date):
    """Sentinel-2 থেকে NDWI (water/moisture index)"""
    sentinel2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )

    def add_ndwi(image):
        # NDWI = (Green - NIR) / (Green + NIR)
        ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
        return image.addBands(ndwi)

    ndwi_col = sentinel2.map(add_ndwi)
    mean_ndwi = ndwi_col.select("NDWI").mean()

    stats = mean_ndwi.reduceRegion(
        reducer=ee.Reducer.mean()
        .combine(ee.Reducer.min(), sharedInputs=True)
        .combine(ee.Reducer.max(), sharedInputs=True),
        geometry=area_geometry,
        scale=30,
        maxPixels=1e9,
    )
    return mean_ndwi, stats


def get_smap_soil_moisture(area_geometry, start_date, end_date):
    """NASA SMAP থেকে actual soil moisture data"""
    smap = (
        ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
        .select("ssm")  # Surface soil moisture
    )

    mean_ssm = smap.mean()
    stats = mean_ssm.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=area_geometry, scale=10000, maxPixels=1e9
    )
    return mean_ssm, stats
