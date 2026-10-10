from sqlalchemy.orm import Session

from app.models.feature_record import FeatureRecord
from app.models.file_record import FileRecord


class FileRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_file_record(self, payload: dict) -> FileRecord:
        record = FileRecord(**payload)
        self.db.add(record)
        self.db.flush()
        return record

    def get_file_record(self, file_id: str) -> FileRecord | None:
        return self.db.query(FileRecord).filter(FileRecord.id == file_id).first()

    def get_features(self, file_id: str, limit: int = 50, offset: int = 0):
        return (
            self.db.query(FeatureRecord)
            .filter(FeatureRecord.file_id == file_id)
            .order_by(FeatureRecord.feature_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def add_feature_records(self, file_id: str, feature_rows: list[dict]) -> None:
        for row in feature_rows:
            self.db.add(FeatureRecord(file_id=file_id, **row))

    def update_file_record(self, record: FileRecord, **kwargs) -> FileRecord:
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        self.db.flush()
        return record

    def count_features(self, file_id: str) -> int:
        return self.db.query(FeatureRecord).filter(FeatureRecord.file_id == file_id).count()
