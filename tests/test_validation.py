from __future__ import annotations

import zipfile
from pathlib import Path

from tests.conftest import build_kml_file


def test_corrupt_zip_is_rejected(client, tmp_path):
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"not a valid zip archive")

    response = client.post("/api/files/", files={"file": (bad_zip.name, bad_zip.open("rb"), "application/zip")})
    assert response.status_code == 400


def test_upload_size_limit_is_enforced(client):
    oversized = b"x" * 20_000_000
    response = client.post("/api/files/", files={"file": ("oversized.kml", oversized, "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 413


def test_empty_file_is_rejected(client):
    response = client.post("/api/files/", files={"file": ("empty.kml", b"", "application/vnd.google-earth.kml+xml")})
    assert response.status_code == 400


def test_file_not_found_returns_404(client):
    response = client.get("/api/files/nope/")
    assert response.status_code == 404
