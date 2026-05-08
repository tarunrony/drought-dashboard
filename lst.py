import ee


def get_lst(area_geometry, start_date, end_date):
    """
    MODIS Terra থেকে Land Surface Temperature
    Unit: Kelvin → Celsius convert করা হবে
    """
    modis_lst = (
        ee.ImageCollection("MODIS/061/MOD11A2")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
        .select("LST_Day_1km")
    )

    def kelvin_to_celsius(image):
        lst_celsius = image.multiply(0.02).subtract(273.15).rename("LST_Celsius")
        return lst_celsius.copyProperties(image, ["system:time_start"])

    lst_celsius = modis_lst.map(kelvin_to_celsius)
    mean_lst = lst_celsius.mean()

    stats = mean_lst.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=area_geometry,
        scale=1000,
        maxPixels=1e9,
    )
    return mean_lst, stats


def get_lst_timeseries(area_geometry, start_date, end_date):
    """8-day LST time series"""
    modis_lst = (
        ee.ImageCollection("MODIS/061/MOD11A2")
        .filterBounds(area_geometry)
        .filterDate(start_date, end_date)
        .select("LST_Day_1km")
    )

    def extract(image):
        lst_c = image.multiply(0.02).subtract(273.15)
        val = lst_c.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=area_geometry, scale=1000, maxPixels=1e9
        )
        return ee.Feature(
            None,
            {
                "date": image.date().format("YYYY-MM-dd"),
                "LST_mean": val.get("LST_Day_1km"),
            },
        )

    return modis_lst.map(extract).getInfo()
