from __future__ import annotations

import zipfile
from pathlib import Path

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import LineString, Point, Polygon

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def build_kml_file(path: Path) -> Path:
    gdf = gpd.GeoDataFrame(
        {
            "name": ["Area A", "Line B", "Point C"],
            "feature_type": ["polygon", "line", "point"],
        },
        geometry=[
            Polygon([(0, 0), (0, 0.01), (0.01, 0.01), (0.01, 0), (0, 0)]),
            LineString([(0, 0), (0.01, 0)]),
            Point(0.005, 0.005),
        ],
        crs="EPSG:4326",
    )
    gdf.to_file(path, driver="KML")
    return path


def build_shapefile_zip(path: Path, feature_name: str = "sample") -> Path:
    polygon = Polygon([(0, 0), (0, 0.01), (0.01, 0.01), (0.01, 0), (0, 0)])
    gdf = gpd.GeoDataFrame({"name": [feature_name]}, geometry=[polygon], crs="EPSG:4326")
    shapefile_dir = path.parent / feature_name
    shapefile_dir.mkdir(exist_ok=True)
    gdf.to_file(shapefile_dir / f"{feature_name}.shp", driver="ESRI Shapefile")

    with zipfile.ZipFile(path, "w") as zf:
        for suffix in [".shp", ".shx", ".dbf", ".prj"]:
            zf.write(shapefile_dir / f"{feature_name}{suffix}", arcname=f"{feature_name}{suffix}")
    return path
