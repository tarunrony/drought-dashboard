import ee


def get_rainfall(area_geometry, start_date, end_date):
    """
    CHIRPS dataset থেকে rainfall data
    Resolution: 5km, Daily → Monthly aggregate
    """
    chirps = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
    )

    # Total rainfall (sum)
    total_rainfall = chirps.select("precipitation").sum()

    stats = total_rainfall.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.sum(), sharedInputs=True),
        geometry=area_geometry,
        scale=5000,
        maxPixels=1e9,
    )
    return total_rainfall, stats


def get_monthly_rainfall(area_geometry, start_date, end_date):
    """Monthly rainfall time series"""
    chirps = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
    )

    def extract_monthly(image):
        monthly_sum = image.reduceRegion(
            reducer=ee.Reducer.sum(), geometry=area_geometry, scale=5000, maxPixels=1e9
        )
        return ee.Feature(
            None,
            {
                "date": image.date().format("YYYY-MM-dd"),
                "rainfall_mm": monthly_sum.get("precipitation"),
            },
        )

    return chirps.map(extract_monthly).getInfo()
