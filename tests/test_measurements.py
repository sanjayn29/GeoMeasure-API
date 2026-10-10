from __future__ import annotations

from tests.conftest import build_kml_file, build_shapefile_zip


def test_zipped_shapefile_upload_succeeds(client, tmp_path):
    path = build_shapefile_zip(tmp_path / "survey.zip", feature_name="survey")
    with path.open("rb") as fh:
        response = client.post("/api/files/", files={"file": (path.name, fh, "application/zip")})

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["file_type"] == "Shapefile ZIP"
    assert payload["feature_count"] == 1
    assert payload["measurement_crs"]


def test_feature_measurements_return_values(client, tmp_path):
    path = build_kml_file(tmp_path / "measurements.kml")
    with path.open("rb") as fh:
        response = client.post("/api/files/", files={"file": (path.name, fh, "application/vnd.google-earth.kml+xml")})

    file_id = response.json()["id"]
    measurements_response = client.get(f"/api/files/{file_id}/measurements/")
    payload = measurements_response.json()

    assert measurements_response.status_code == 200, measurements_response.text
    assert payload["file_id"] == file_id
    assert payload["feature_count"] == 3
    polygon = payload["features"][0]
    line = payload["features"][1]
    point = payload["features"][2]

    assert polygon["geometry_type"] == "Polygon"
    assert polygon["measurement"]["type"] == "area"
    assert polygon["measurement"]["unit"] == "m²"
    assert polygon["measurement"]["value"] > 100000

    assert line["geometry_type"] == "LineString"
    assert line["measurement"]["type"] == "length"
    assert line["measurement"]["unit"] == "m"
    assert line["measurement"]["value"] > 1000

    assert point["geometry_type"] == "Point"
    assert point["measurement"] is None
    assert point["measurement_status"] == "NOT_REQUIRED"
