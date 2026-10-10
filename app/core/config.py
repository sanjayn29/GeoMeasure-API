from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Geospatial File Measurement API"
    database_url: str = "sqlite:///./geomeasure.db"
    max_upload_size: int = 10 * 1024 * 1024
    allowed_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
