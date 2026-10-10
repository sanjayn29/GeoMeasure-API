from __future__ import annotations

from pyproj import CRS


def detect_crs(source_crs: object | None) -> CRS | None:
    if source_crs is None:
        return None
    try:
        return CRS.from_user_input(source_crs)
    except Exception:
        return None


def choose_measurement_crs(source_crs: CRS | None, bounds: tuple[float, float, float, float] | None = None) -> str:
    if source_crs is None:
        raise ValueError("Source CRS is missing; cannot determine a safe projected measurement CRS.")

    if not source_crs.is_geographic:
        return source_crs.to_string()

    if bounds is not None:
        minx, miny, maxx, maxy = bounds
        width = maxx - minx
        height = maxy - miny
        if width > 6 or height > 6:
            return "EPSG:3857"

    lon = 0.0 if bounds is None else (bounds[0] + bounds[2]) / 2
    lat = 0.0 if bounds is None else (bounds[1] + bounds[3]) / 2
    zone = int((lon + 180) / 6) + 1
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return f"EPSG:{epsg}"


def project_geodata(gdf, measurement_crs: str):
    if measurement_crs == "EPSG:3857":
        return gdf.to_crs("EPSG:3857")
    return gdf.to_crs(measurement_crs)
