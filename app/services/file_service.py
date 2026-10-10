from __future__ import annotations

import logging
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file_record import FileRecord
from app.repositories.file_repository import FileRepository
from app.services import crs_service, geospatial_service, measurement_service

logger = logging.getLogger(__name__)


def _normalise_file_type(extension: str) -> str:
    mapping = {".kml": "KML", ".zip": "Shapefile ZIP"}
    return mapping.get(extension.lower(), "UNKNOWN")


async def process_upload(file: UploadFile, db: Session) -> dict:
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail="A file name is required.")

    extension = Path(file.filename).suffix.lower()
    if extension not in {".kml", ".zip"}:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{extension or 'unknown'}'. Supported types are .kml and .zip.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_size} byte upload limit.")

    safe_name = Path(file.filename).name
    with TemporaryDirectory(prefix="geomeasure-") as temp_dir:
        temp_path = Path(temp_dir) / safe_name
        temp_path.write_bytes(content)
        try:
            gdf = geospatial_service.load_geospatial_file(temp_path, extension)
            source_crs = crs_service.detect_crs(gdf.crs)
            if source_crs is None:
                raise HTTPException(status_code=400, detail="Source CRS is missing or invalid. Upload a file with a valid projection definition.")

            measurement_crs = crs_service.choose_measurement_crs(source_crs, tuple(gdf.total_bounds))
            projected = crs_service.project_geodata(gdf, measurement_crs)

            repository = FileRepository(db)
            file_id = uuid.uuid4().hex
            file_record_payload = {
                "id": file_id,
                "filename": safe_name,
                "file_type": _normalise_file_type(extension),
                "feature_count": int(len(projected)),
                "crs": source_crs.to_string(),
                "measurement_crs": measurement_crs,
                "status": "COMPLETED",
                "message": "File processed successfully",
            }
            record = repository.create_file_record(file_record_payload)

            feature_payloads = []
            for idx, row in projected.iterrows():
                feature = measurement_service.build_feature_row(int(idx), row, source_crs.to_string())
                feature_payloads.append(feature)
            repository.add_feature_records(file_id, feature_payloads)
            db.commit()

            return {
                "id": record.id,
                "filename": record.filename,
                "file_type": record.file_type,
                "feature_count": record.feature_count,
                "crs": record.crs,
                "measurement_crs": record.measurement_crs,
                "status": record.status,
                "message": record.message,
            }
        except (BadZipFile, ValueError, OSError) as exc:
            if isinstance(exc, ValueError) and "CRS" in str(exc):
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            raise HTTPException(status_code=400, detail=str(exc) or "Invalid geospatial file upload.") from exc
        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Unexpected upload processing error")
            raise HTTPException(status_code=422, detail="The file could not be processed.") from exc


def get_file_metadata(file_id: str, db: Session) -> FileRecord:
    repository = FileRepository(db)
    record = repository.get_file_record(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' was not found.")
    return record


def get_feature_measurements(file_id: str, db: Session, limit: int, offset: int):
    repository = FileRepository(db)
    if repository.get_file_record(file_id) is None:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' was not found.")
    features = repository.get_features(file_id, limit=limit, offset=offset)
    return {
        "file_id": file_id,
        "feature_count": len(features),
        "features": [
            {
                "feature_id": feature.feature_id,
                "geometry_type": feature.geometry_type,
                "crs": feature.crs,
                "measurement": None if feature.measurement_value is None else {"type": feature.measurement_type, "value": feature.measurement_value, "unit": feature.measurement_unit},
                "measurement_status": feature.measurement_status,
                "properties": feature.properties,
                "geometry": feature.geometry,
            }
            for feature in features
        ],
    }
