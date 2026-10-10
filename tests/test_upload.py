from pathlib import Path
import zipfile

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import LineString, Point, Polygon

from app.main import app


def make_kml_file(path: Path) -> Path:
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


@pytest.fixture
def client():
    return TestClient(app)


def test_successful_kml_upload(client, tmp_path):
    path = tmp_path / "sample.kml"
    make_kml_file(path)

    with path.open("rb") as fh:
        response = client.post("/api/files/", files={"file": (path.name, fh, "application/vnd.google-earth.kml+xml")})

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["filename"] == "sample.kml"
    assert payload["file_type"] == "KML"
    assert payload["feature_count"] >= 1
    assert payload["status"] == "COMPLETED"
    assert payload["measurement_crs"]


def test_missing_crs_upload_is_rejected(client, tmp_path):
    archive_path = tmp_path / "missing_crs.zip"
    shapefile_dir = tmp_path / "missing_crs_shape"
    shapefile_dir.mkdir()
    geom = Polygon([(0, 0), (0, 0.01), (0.01, 0.01), (0.01, 0), (0, 0)])
    gdf = gpd.GeoDataFrame({"name": ["Area A"]}, geometry=[geom], crs="EPSG:4326")
    gdf.to_file(shapefile_dir / "missing_crs.shp", driver="ESRI Shapefile")
    with zipfile.ZipFile(archive_path, "w") as zf:
        for suffix in [".shp", ".shx", ".dbf"]:
            zf.write(shapefile_dir / f"missing_crs{suffix}", arcname=f"missing_crs{suffix}")

    with archive_path.open("rb") as fh:
        response = client.post("/api/files/", files={"file": (archive_path.name, fh, "application/zip")})

    assert response.status_code == 400
    payload = response.json()
    assert "CRS" in payload["detail"] or "crs" in payload["detail"].lower()


def test_unsupported_extension_is_rejected(client):
    response = client.post("/api/files/", files={"file": ("bad.txt", b"not a geospatial file", "text/plain")})
    assert response.status_code == 415
