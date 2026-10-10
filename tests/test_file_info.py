from __future__ import annotations

from tests.conftest import build_kml_file


def test_file_metadata_is_returned(client, tmp_path):
    path = build_kml_file(tmp_path / "metadata.kml")
    with path.open("rb") as fh:
        response = client.post("/api/files/", files={"file": (path.name, fh, "application/vnd.google-earth.kml+xml")})

    assert response.status_code == 201, response.text
    file_id = response.json()["id"]

    info_response = client.get(f"/api/files/{file_id}/")
    payload = info_response.json()
    assert info_response.status_code == 200, info_response.text
    assert payload["id"] == file_id
    assert payload["filename"] == "metadata.kml"
    assert payload["file_type"] == "KML"
    assert payload["feature_count"] == 3
    assert payload["status"] == "COMPLETED"


def test_unknown_file_id_returns_404(client):
    response = client.get("/api/files/does-not-exist/")
    assert response.status_code == 404
