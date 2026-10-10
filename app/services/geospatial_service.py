from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

import geopandas as gpd


def _reject_unsafe_archive_path(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("The archive contains an unsafe file path.")


def extract_shapefile_archive(file_path: Path) -> Path:
    if not file_path.exists():
        raise FileNotFoundError("The uploaded archive could not be read.")

    extracted_dir = file_path.parent
    with zipfile.ZipFile(file_path) as archive:
        shapes_by_stem: dict[str, set[str]] = {}
        for info in archive.infolist():
            if info.is_dir():
                continue
            _reject_unsafe_archive_path(info.filename)
            suffix = Path(info.filename).suffix.lower()
            if suffix not in {".shp", ".shx", ".dbf", ".prj", ".cpg"}:
                continue
            stem = Path(info.filename).stem
            shapes_by_stem.setdefault(stem, set()).add(suffix)

        if not shapes_by_stem:
            raise ValueError("The archive does not contain a usable Shapefile.")

        chosen_stem = None
        for stem, suffixes in shapes_by_stem.items():
            if ".shp" in suffixes and ".dbf" in suffixes and ".shx" in suffixes:
                chosen_stem = stem
                break

        if chosen_stem is None:
            raise ValueError("The archive is missing required Shapefile components (.shp, .shx, .dbf).")

        for info in archive.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename)
            if name.stem != chosen_stem:
                continue
            target = extracted_dir / name.name
            with archive.open(info) as src, target.open("wb") as dst:
                dst.write(src.read())

        shapefile_path = extracted_dir / f"{chosen_stem}.shp"
        if not shapefile_path.exists():
            raise ValueError("The archive does not contain a valid Shapefile.")
        return shapefile_path


def load_geospatial_file(file_path: Path, file_extension: str) -> gpd.GeoDataFrame:
    if file_extension.lower() == ".zip":
        shapefile_path = extract_shapefile_archive(file_path)
        gdf = gpd.read_file(shapefile_path)
    else:
        gdf = gpd.read_file(file_path)

    if gdf.empty:
        raise ValueError("The uploaded file contains no geospatial features.")
    if gdf.crs is None:
        raise ValueError("The source CRS is missing. The file does not provide enough projection information to measure safely.")
    return gdf
