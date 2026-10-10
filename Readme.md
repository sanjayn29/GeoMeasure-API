# Geospatial File Measurement API

## 1. Project overview

This project implements a production-oriented FastAPI backend for processing geospatial files, extracting vector features, transforming coordinates into a safe projected CRS, and calculating spatial measurements for supported geometry types. It accepts KML files and zipped Shapefiles, stores metadata in SQLite using SQLAlchemy, and exposes results through a REST API.

This is a complete backend application rather than a toy prototype. It includes upload validation, CRS detection, measurement logic, database persistence, test coverage, and documentation.

## 2. Problem statement

Geospatial datasets often arrive as KML or Shapefiles with geographic coordinates in degrees. Measuring areas and lengths without a proper projection produces incorrect values and can silently mislead downstream workflows. The application addresses this by detecting the source CRS, selecting a projected CRS when needed, transforming the features, and then calculating measurements in metres.

## 3. Features

Implemented features:

- Upload and process KML files
- Upload and process ZIP archives containing Shapefiles
- Extract feature metadata, geometry, properties, and CRS information
- Detect unsupported or invalid geometries without failing the entire batch
- Calculate polygon area and line length in metres
- Return point features with a `NOT_REQUIRED` measurement status
- Detect missing/invalid CRS values and reject unsafe processing
- Persist file metadata and feature results in SQLite
- Expose endpoints for upload, file metadata, and measurements
- Support pagination with `limit` and `offset`
- Provide automated pytest coverage for validation and measurement behavior

Planned future enhancements:

- Background processing for very large datasets
- Support for GeoJSON and GeoPackage
- Better geodesic measurements for global datasets
- Cloud object storage
- Authentication and authorization
- Job tracking and monitoring
- Deployment with Docker
- PostgreSQL/PostGIS spatial database support

## 4. Technology stack

- Python 3.11
- FastAPI
- Uvicorn
- GeoPandas
- Shapely
- PyProj
- SQLAlchemy
- SQLite
- Pydantic
- Python-multipart
- Pytest

## 5. Architecture and module responsibilities

Repository layout:

- `app/main.py`: application bootstrap and CORS setup
- `app/core/config.py`: environment-driven settings
- `app/database.py`: SQLAlchemy engine and session handling
- `app/models/file_record.py`: uploaded file metadata model
- `app/models/feature_record.py`: stored feature and measurement model
- `app/repositories/file_repository.py`: database access layer
- `app/services/file_service.py`: upload orchestration and validation
- `app/services/geospatial_service.py`: file parsing and archive extraction
- `app/services/crs_service.py`: CRS detection and projected CRS selection
- `app/services/measurement_service.py`: feature measurement and serialization logic
- `app/api/routes/files.py`: REST endpoints
- `app/api/schemas/files.py`: request/response models
- `tests/`: automated test suite

## 6. Prerequisites

- Python 3.11 installed and active
- A terminal such as PowerShell or Bash
- Network access to install dependencies from PyPI
- Optional: a browser for Swagger docs at `/docs`

## 7. Installation and setup

Clone the repo, move into the project folder, and create a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

## 8. Virtual environment creation

This project intentionally uses a dedicated local virtual environment for reproducible dependency management.

## 9. Dependency installation

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Potential platform notes:

- The geospatial stack uses wheels for Python 3.11 on Windows and is compatible with the required version in this repository.
- Do not mix project dependencies across interpreter versions.

## 10. Environment configuration

Copy the example settings file:

```bash
copy .env.example .env
```

The defaults are:

```env
DATABASE_URL=sqlite:///./geomeasure.db
MAX_UPLOAD_SIZE=10485760
ALLOWED_ORIGINS=http://localhost:3000,https://example.com
```

## 11. Database initialization

The database is initialized when the FastAPI application starts. Tables are created automatically as part of the boot process.

```bash
python -c "from app.database import init_db; init_db()"
```

## 12. Running the application locally

Start the server with:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The app is then accessible at:

- http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## 13. Swagger documentation access at `/docs`

The FastAPI Swagger UI is available at `/docs` and the OpenAPI schema is available at `/openapi.json`.

## 14. API endpoint documentation

### POST /api/files/

Accepts a multipart upload with the form field `file`.

- Supported extensions: `.kml` and `.zip`
- Returns `201 Created` on success
- Returns `400`, `413`, `415`, or `422` on invalid input

### GET /api/files/{id}/

Returns upload metadata for a known file ID.

### GET /api/files/{id}/measurements/

Returns feature results for the uploaded file.

Optional pagination:

- `limit`: default `50`, max `100`
- `offset`: default `0`

## 15. Sample curl commands

Upload a KML file:

```bash
curl -X POST http://127.0.0.1:8000/api/files/ \
  -F "file=@samples/sample.kml"
```

Upload a zipped Shapefile:

```bash
curl -X POST http://127.0.0.1:8000/api/files/ \
  -F "file=@samples/sample.zip"
```

Get file metadata:

```bash
curl http://127.0.0.1:8000/api/files/<file-id>/
```

Get measurements:

```bash
curl "http://127.0.0.1:8000/api/files/<file-id>/measurements/?limit=50&offset=0"
```

## 16. Example request and response JSON

Example upload response:

```json
{
  "id": "b65ccf3a9d384c2e9e479d15d89c95a",
  "filename": "survey.kml",
  "file_type": "KML",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32644",
  "status": "COMPLETED",
  "message": "File processed successfully"
}
```

Example measurement response:

```json
{
  "file_id": "b65ccf3a9d384c2e9e479d15d89c95a",
  "feature_count": 3,
  "features": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "crs": "EPSG:4326",
      "measurement": {
        "type": "area",
        "value": 1233312.233,
        "unit": "m²"
      },
      "measurement_status": "SUCCESS",
      "properties": {
        "name": "Area A"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[...]]]
      }
    }
  ]
}
```

## 17. Supported file formats and geometry types

Supported input files:

- `.kml`
- `.zip` with a valid Shapefile bundle (`.shp`, `.shx`, `.dbf`, optional `.prj`)

Supported geometry types:

- Polygon / MultiPolygon: area measured in square metres
- LineString / MultiLineString: length measured in metres
- Point / MultiPoint: no measurement required
- Unsupported geometry types: preserved but flagged as unsupported

## 18. CRS detection and projection-selection strategy

The implementation follows a safe workflow:

1. Read the source geometry and inspect the CRS metadata from the file.
2. If the CRS is missing, do not silently assume `EPSG:4326`; reject the file with a descriptive error.
3. For geographic datasets, pick a projected CRS based on the centroid of the data and the bounding box.
4. For most single-zone datasets, use the appropriate UTM zone.
5. If the dataset spans more than about 6 degrees in longitude or latitude, fall back to `EPSG:3857` to avoid a clearly unsafe projection choice.
6. Transform the feature geometries into the chosen projected CRS before measurement.
7. Return the original geometry and original CRS in the stored output, while also recording the measurement CRS in metadata.

This keeps the code dynamic and avoids hardcoding one CRS for every dataset.

## 19. Measurement formulas and units

The measurement logic uses the projected geometries rather than raw degrees.

- Polygon / MultiPolygon: `area` in metres squared
- LineString / MultiLineString: `length` in metres
- Point / MultiPoint: no measurement; status `NOT_REQUIRED`

The code uses Geopandas and Shapely to calculate these values after transforming geographic coordinates to a projected CRS.

## 20. Error handling and security

The application rejects invalid input using consistent JSON errors with HTTP status codes such as:

- `400` for invalid or missing CRS data
- `404` for unknown file IDs
- `413` for oversized uploads
- `415` for unsupported file extensions
- `422` for invalid processing states

Security practices implemented:

- upload size enforcement
- validation of extension and actual file contents
- safe ZIP inspection to prevent traversal and suspicious archive paths
- cleanup of temporary files after request processing
- no execution of uploaded content
- no internal stack traces exposed to clients
- environment-based configuration instead of hardcoded secrets

## 21. Running automated tests

```bash
python -m pytest -q
```

The project includes tests for:

- successful KML upload
- successful zipped Shapefile upload
- metadata retrieval
- measurement retrieval
- area and length calculations
- point handling
- CRS transformation
- invalid uploads
- missing CRS handling
- unsupported geometry handling
- size limits and persistence

## 22. Design decisions and alternatives considered

Several alternatives were considered:

- using only in-memory storage for uploads: rejected because it breaks persistence and testability
- hardcoding a single projected CRS everywhere: rejected because it is unsafe for different regions
- performing measurements directly in degrees: rejected because it produces incorrect values
- storing everything in raw files only: rejected because it complicates retrieval and processing workflows

The chosen design keeps the project simple, maintainable, and aligned with the required acceptance criteria.

## 23. Challenges and lessons learned

Key lessons from implementation:

- KML and Shapefile handling require different validation paths.
- CRS metadata can be absent even when geometry coordinates look valid.
- ZIP extraction must be security-conscious and carefully validated.
- Measured values must be computed after projection, not in raw geographic coordinates.
- JSON serialization of pandas date-like objects requires sanitization before database storage.

## 24. Future scope

The following improvements are planned for future releases:

- Background processing for very large datasets
- Support for GeoJSON and GeoPackage
- Better geodesic measurements for global datasets
- Cloud object storage
- Authentication and authorization
- Job tracking and monitoring
- Deployment with Docker
- Spatial database support using PostgreSQL and PostGIS

## 25. Limitations

- The implementation is designed for moderate-size files and uses SQLite as the default persistence layer.
- Very large spatial datasets may require asynchronous or background processing.
- Global geodesic measurement accuracy is intentionally simplified for the core workflow.
- Some advanced geodetic edge cases and enterprise security features remain future work.

## Implemented vs future scope

Implemented in this project:

- KML + zipped Shapefile upload
- CRS detection and UTM-based measurement workflow
- SQLite-backed persistence
- REST API and test suite
- validation and security checks

Planned for future releases:

- asynchronous jobs
- more file formats
- geodesic support
- cloud storage integration
- auth, monitoring, and deployment automation

## Final notes

This project was designed to be understandable, testable, and easy to extend. It balances correctness and simplicity while staying aligned with the geospatial backend requirements described in the project brief.
