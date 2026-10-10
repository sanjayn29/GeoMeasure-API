from __future__ import annotations

from tests.conftest import build_kml_file


def test_geographic_crs_is_projected_before_measurement(client, tmp_path):
    path = build_kml_file(tmp_path / "crs.kml")
    with path.open("rb") as fh:
        response = client.post("/api/files/", files={"file": (path.name, fh, "application/vnd.google-earth.kml+xml")})

    payload = response.json()
    assert response.status_code == 201, response.text
    assert payload["crs"] == "EPSG:4326"
    assert payload["measurement_crs"].startswith("EPSG:326") or payload["measurement_crs"].startswith("EPSG:327")

    file_id = payload["id"]
    measurements = client.get(f"/api/files/{file_id}/measurements/").json()["features"]
    area_value = next(item["measurement"]["value"] for item in measurements if item["geometry_type"] == "Polygon")
    assert area_value > 100000
