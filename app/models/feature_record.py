from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeatureRecord(Base):
    __tablename__ = "feature_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("file_records.id"), index=True, nullable=False)
    feature_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    geometry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    crs: Mapped[str | None] = mapped_column(String(100), nullable=True)
    properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    geometry: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    measurement_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    measurement_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    measurement_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    measurement_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    measurement_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_record: Mapped["FileRecord"] = relationship("FileRecord", back_populates="features")
