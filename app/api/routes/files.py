from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas.files import FileInfoResponse, FileMeasurementsResponse, FileUploadResponse
from app.database import get_db
from app.services import file_service

router = APIRouter(prefix="/api", tags=["files"])


@router.post("/files/", response_model=FileUploadResponse, status_code=201)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    data = await file_service.process_upload(file, db)
    return FileUploadResponse(**data)


@router.get("/files/{file_id}/", response_model=FileInfoResponse)
async def get_file(file_id: str, db: Session = Depends(get_db)) -> FileInfoResponse:
    record = file_service.get_file_metadata(file_id, db)
    return FileInfoResponse(
        id=record.id,
        filename=record.filename,
        file_type=record.file_type,
        feature_count=record.feature_count,
        crs=record.crs,
        measurement_crs=record.measurement_crs,
        status=record.status,
        message=record.message,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )


@router.get("/files/{file_id}/measurements/", response_model=FileMeasurementsResponse)
async def list_measurements(
    file_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> FileMeasurementsResponse:
    payload = file_service.get_feature_measurements(file_id, db, limit=limit, offset=offset)
    return FileMeasurementsResponse(**payload)
