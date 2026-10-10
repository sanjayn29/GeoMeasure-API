from __future__ import annotations

import json
from typing import Any

from shapely.geometry import shape


def _normalise_measurement(value: float, unit: str) -> float:
    return round(float(value), 3)


def _serialize_json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize_json_safe(item) for key, item in value.items()}
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return _serialize_json_safe(value.item())
        except Exception:
            pass
    if str(value) == "NaT":
        return None
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def calculate_measurement_for_geometry(geometry: Any) -> tuple[dict | None, str, str | None, str | None]:
    if geometry is None:
        return None, "EMPTY", None, "Geometry is empty."

    geom = shape(geometry)
    if geom.is_empty:
        return None, "EMPTY", None, "Geometry is empty."
    if not geom.is_valid:
        return None, "INVALID_GEOMETRY", None, "Geometry is invalid."

    geom_type = geom.geom_type
    if geom_type in {"Polygon", "MultiPolygon"}:
        value = geom.area
        return {
            "type": "area",
            "value": _normalise_measurement(value, "m²"),
            "unit": "m²",
        }, "SUCCESS", "area", None

    if geom_type in {"LineString", "MultiLineString"}:
        value = geom.length
        return {
            "type": "length",
            "value": _normalise_measurement(value, "m"),
            "unit": "m",
        }, "SUCCESS", "length", None

    if geom_type in {"Point", "MultiPoint"}:
        return None, "NOT_REQUIRED", None, None

    return None, "UNSUPPORTED", None, f"Unsupported geometry type '{geom_type}'."


def build_feature_row(index: int, row: Any, measurement_crs: str) -> dict:
    geometry = row.geometry
    geometry_json = None
    if geometry is not None:
        geometry_json = geometry.__geo_interface__

    measurement, status, measurement_type, error = calculate_measurement_for_geometry(geometry_json)
    if geometry is None:
        geometry_type = "Unknown"
    else:
        geometry_type = geometry.geom_type

    properties = row.to_dict()
    properties.pop("geometry", None)
    properties = {str(key): _serialize_json_safe(value) for key, value in properties.items()}

    row_payload = {
        "feature_id": index,
        "geometry_type": geometry_type,
        "crs": measurement_crs,
        "properties": properties,
        "geometry": geometry_json,
        "measurement_type": measurement_type,
        "measurement_value": None if measurement is None else measurement["value"],
        "measurement_unit": None if measurement is None else measurement["unit"],
        "measurement_status": status,
        "measurement_error": error,
    }
    return row_payload
