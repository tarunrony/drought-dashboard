"""
utils/map_utils.py
Folium map builder with GEE tile overlays.
"""

import ee
import folium
from config import VIS_PARAMS


def build_base_map(lat: float, lon: float, zoom: int = 10) -> folium.Map:
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
    )
    # Satellite base layer
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="Satellite",
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)
    return m


def add_gee_layer(m: folium.Map, image: ee.Image, vis_params: dict, name: str) -> folium.Map:
    """Add a GEE image as a tile layer on the folium map."""
    try:
        map_id = image.getMapId(vis_params)
        tile_url = map_id["tile_fetcher"].url_format
        folium.TileLayer(
            tiles=tile_url,
            attr="Google Earth Engine",
            name=name,
            overlay=True,
            control=True,
            opacity=0.75,
        ).add_to(m)
    except Exception as e:
        print(f"Could not add layer {name}: {e}")
    return m


def add_area_marker(m: folium.Map, lat: float, lon: float, name: str) -> folium.Map:
    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color="#FF5722",
        fill=True,
        fill_color="#FF5722",
        fill_opacity=0.7,
        tooltip=name,
        popup=folium.Popup(f"<b>{name}</b>", max_width=200),
    ).add_to(m)
    return m


def add_legend(m: folium.Map, title: str, colors: list, labels: list) -> folium.Map:
    legend_html = f"""
    <div style="position:fixed; bottom:30px; right:10px; z-index:1000;
         background:rgba(30,30,30,0.9); padding:12px; border-radius:8px;
         border:1px solid rgba(255,255,255,0.15); font-family:monospace; font-size:12px;">
      <b style="color:#fff;">{title}</b><br>
      {"".join(f'<span style="background:{c};display:inline-block;width:14px;height:14px;margin-right:6px;border-radius:2px;"></span><span style="color:#ddd;">{l}</span><br>' for c, l in zip(colors, labels))}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


def get_ndvi_map(geometry, image: ee.Image) -> folium.Map:
    """Ready-made NDVI map."""
    centroid = geometry.centroid().coordinates().getInfo()
    m = build_base_map(lat=centroid[1], lon=centroid[0])
    m = add_gee_layer(m, image, VIS_PARAMS["ndvi"], "NDVI")
    m = add_legend(
        m, "NDVI",
        ["#d73027","#fdae61","#fee08b","#d9ef8b","#a6d96a","#1a9850"],
        ["< 0.0","0.0–0.2","0.2–0.4","0.4–0.5","0.5–0.65","0.65–0.8"],
    )
    folium.LayerControl().add_to(m)
    return m
