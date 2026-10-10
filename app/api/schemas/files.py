from __future__ import annotations

from pydantic import BaseModel, Field


class MeasurementResult(BaseModel):
    type: str | None = None
    value: float | None = None
    unit: str | None = None


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    feature_count: int
    crs: str | None = None
    measurement_crs: str | None = None
    status: str
    message: str


class FileInfoResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    feature_count: int
    crs: str | None = None
    measurement_crs: str | None = None
    status: str
    message: str | None = None
    created_at: str | None = None


class FeatureMeasurementResponse(BaseModel):
    feature_id: int
    geometry_type: str
    crs: str | None = None
    measurement: MeasurementResult | None = None
    measurement_status: str
    properties: dict
    geometry: dict | None = None


class FileMeasurementsResponse(BaseModel):
    file_id: str
    feature_count: int
    features: list[FeatureMeasurementResponse] = Field(default_factory=list)
