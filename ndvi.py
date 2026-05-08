import ee


def get_ndvi(area_geometry, start_date, end_date):
    """
    Sentinel-2 থেকে NDVI calculate করে return করে
    Returns: ee.Image with NDVI band
    """
    sentinel2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(_mask_clouds)
    )

    def add_ndvi(image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return image.addBands(ndvi)

    ndvi_collection = sentinel2.map(add_ndvi)
    mean_ndvi = ndvi_collection.select("NDVI").mean()

    # Statistics বের করা
    stats = mean_ndvi.reduceRegion(
        reducer=ee.Reducer.mean()
        .combine(ee.Reducer.min(), sharedInputs=True)
        .combine(ee.Reducer.max(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=area_geometry,
        scale=30,
        maxPixels=1e9,
    )
    return mean_ndvi, stats


def _mask_clouds(image):
    qa = image.select("QA60")
    cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    return image.updateMask(cloud_mask)


def get_ndvi_timeseries(area_geometry, start_date, end_date):
    """Monthly NDVI time series — chart এর জন্য"""
    sentinel2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(_mask_clouds)
    )

    def monthly_ndvi(image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        mean = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=area_geometry, scale=30, maxPixels=1e9
        )
        return ee.Feature(
            None,
            {"date": image.date().format("YYYY-MM"), "NDVI_mean": mean.get("NDVI")},
        )

    timeseries = sentinel2.map(monthly_ndvi)
    return timeseries.getInfo()
