# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Beehive Photo Metadata Tracker is a Streamlit-based web application that helps beekeepers analyze and organize photos of their hives with rich metadata. The app uses computer vision APIs, weather data integration, and image processing to transform unstructured photo collections into a structured, searchable knowledge base.

## Development Commands

### Environment Setup
```bash
# Using Poetry (recommended)
poetry install
poetry shell

# Using pip + venv (alternative)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Main application entry point
streamlit run run_tracker.py

# Development server (default port 8501)
# Application will be available at: http://localhost:8501
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests
pytest tests/system/ -v                  # System tests

# Run with coverage reporting
pytest tests/ --cov=src --cov-report=html

# Run tests matching specific patterns
pytest tests/ -k "test_vision" -v       # All vision API tests
pytest tests/ -k "test_error" -v        # All error handling tests

# Run specific marker groups
pytest -m unit -v                        # Run unit tests
pytest -m integration -v                 # Run integration tests
pytest -m gps -v                         # Run GPS-related tests
```

### Docker Commands
```bash
# Build Docker image locally
docker build -t hive-tracker-local .

# Run with mounted data directory
docker run -p 8080:8080 -v $(pwd)/data:/app/data hive-tracker-local

# Application available at: http://localhost:8080
```

### Cloud Deployment
```bash
# Deploy to Google Cloud Run (requires PROJECT_ID and GCP_REGION env vars)
chmod +x deploy.sh
./deploy.sh

# Manual deployment steps documented in docs/DEPLOYMENT.md
```

### Dependency Management
```bash
# The project uses both Poetry and pip:
# - pyproject.toml: Poetry configuration with locked versions (poetry.lock)
# - requirements.txt: Simplified pip dependencies for Docker deployment

# Update dependencies
poetry update                    # Updates poetry.lock
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Architecture Overview

### Multi-Page Streamlit Structure
The application follows a multi-page Streamlit architecture with navigation defined in `run_tracker.py`:

- **Main Entry Point**: `run_tracker.py` - Sets up navigation, session management, and page routing
- **Authentication**: `src/login.py` - Simple authentication system
- **Core Pages**:
  - `src/app.py` - Main dashboard with photo upload and analysis
  - `src/calendar_view.py` - Calendar timeline interface
  - `src/gallery_view.py` - Photo gallery interface
  - `src/bulk_import_page.py` - Bulk import wizard (S3, local, URLs)
  - `src/pages/Storage_Management.py` - Storage backend configuration

### Storage Architecture

**Storage Abstraction Layer** (`src/storage/`):
The app uses a provider pattern for flexible storage backends:

- `base.py` - Abstract `StorageProvider` interface and `StorageConfig` management
- `manager.py` - `StorageManager` for runtime provider switching and initialization
- `local_provider.py` - Local filesystem storage implementation
- `s3_provider.py` - AWS S3 storage implementation (requires boto3)
- `config.py` - Storage configuration helpers

**Key Storage Patterns**:
- All storage operations go through the `StorageManager`
- Providers implement: `upload_image()`, `download_image()`, `delete_image()`, `list_images()`, `get_image_url()`, `generate_thumbnail()`, `health_check()`
- Configuration via environment variables or runtime UI
- Graceful fallback when cloud providers unavailable

### Bulk Import System

**Bulk Import Architecture** (`src/bulk_import/`):
Supports importing multiple photos from various sources:

- `photo_processing_contract.py` - Common interface for all importers
- `s3_bulk_importer.py` - AWS S3 bucket import with credential management
- `local_bulk_importer.py` - Local directory recursive scanning
- `url_bulk_importer.py` - Import from URL lists

**4-Step Import Wizard**:
1. Source configuration (credentials, paths)
2. Photo discovery and preview
3. Processing (EXIF → Vision API → Weather API)
4. Integration into timeline

### Core Components

**API Services** (`src/api_services/`):
- `vision.py` - Google Cloud Vision API integration for image analysis
- `weather.py` - Open-Meteo API integration for weather data

**Utilities** (`src/utils/`):
- `image_processor.py` - Multi-library EXIF extraction (PIL, exifread, pyexiftool as fallback) and color analysis
- `data_handler.py` - Data processing, validation, and persistence (JSON/CSV)
- `session_manager.py` - Streamlit session state management
- `storage_integration.py` - Integration layer between app and storage providers

**UI Components**:
- `src/app_components.py` - Reusable UI components for photo analysis
- `src/ui_components.py` - Core UI element library
- `src/timeline_component.py` - Timeline visualization using Plotly
- `src/storage_ui.py` - Storage management UI components

### Data Flow Architecture

**Single Photo Upload**:
1. Photo Upload → `app_components.py` handles file upload and validation
2. EXIF Extraction → `image_processor.py` extracts metadata (date, GPS, camera)
3. Vision API → `vision.py` analyzes image for bee-related content
4. Weather Integration → `weather.py` fetches environmental context
5. Color Analysis → `image_processor.py` performs palette extraction
6. Storage → `StorageManager` persists image via configured provider
7. Data Persistence → `data_handler.py` saves metadata to JSON
8. Visualization → `timeline_component.py` renders timeline

**Bulk Import Flow**:
1. Source Configuration → User selects S3/local/URL and provides credentials
2. Discovery → Importer scans source and groups photos by date
3. Processing → Each photo goes through standard pipeline (EXIF, Vision, Weather)
4. Progress Tracking → 4-stage progress bar with error logging
5. Integration → Creates inspections and updates timeline

Step 3 became true on 2026-08-23. Before that the Vision call targeted a
function that did not exist and returned `{}` silently; see "Bulk import: the
2026-08-23 repair" below before trusting any description of this pipeline.

Weather in bulk import is not called by the importers. It arrives indirectly:
`add_photo_to_inspection` (`src/utils/data_handler.py`) calls
`fetch_weather_for_inspection`, which needs `inspection['location']` as a dict
with lat/lon, so it only fires for photos carrying GPS.

## Environment Variables

### Required for Core Functionality
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Storage Configuration
```bash
# Storage provider selection
STORAGE_PROVIDER=local                  # Options: local, s3, gcs

# Local storage (default)
LOCAL_STORAGE_PATH=data/uploads
LOCAL_CREATE_DIRS=true
LOCAL_PRESERVE_STRUCTURE=true

# S3 storage
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_USE_SSL=true
S3_CREATE_BUCKET=false

# GCS storage
GCS_BUCKET_NAME=your-bucket-name
GCS_PROJECT_ID=your-project-id
GCS_CREDENTIALS_PATH=/path/to/credentials.json
```

### Optional Configuration
```bash
# Application settings
STREAMLIT_SECRET_KEY=your-secret-key
ENVIRONMENT=development|production
LOG_LEVEL=DEBUG|INFO

# Cloud deployment (for deploy.sh)
PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
```

## Key Dependencies

**Core Framework**: Streamlit 1.44.1 with multi-page navigation
**Image Processing**: PIL/Pillow, exifread, pyexiftool (fallback)
**Color Analysis**: ColorThief
**Computer Vision**: Google Cloud Vision API 3.7.1
**Data Visualization**: Plotly 6.0.1
**Weather Data**: Open-Meteo API (free tier)
**Cloud Storage**: boto3 (AWS S3), google-cloud-storage (GCS)
**Data Management**: Pandas
**Testing**: pytest, pytest-cov

## Session State Management

The app uses comprehensive session state management via `src/utils/session_manager.py`. Key session state variables:

- `logged_in` - Authentication status
- `inspections` - List of all inspection records
- `current_image` - Currently displayed photo data
- `timeline_data` - Historical inspection timeline
- `color_analysis` - Extracted color palettes
- `bulk_import_state` - Multi-step wizard state for bulk imports
- `storage_config` - Current storage provider configuration

**Important**: Session state persists across page navigation but not across browser sessions.

## Data Storage Formats

### JSON Format (Primary)
Structured inspection data stored in `data/inspections.json`:
```json
{
  "inspections": [
    {
      "id": "uuid",
      "date": "2024-01-15T14:30:00",
      "location": {"lat": 30.42, "lon": -97.68},
      "photos": [
        {
          "filename": "hive.jpg",
          "storage_path": "s3://bucket/path or local/path",
          "date_taken": "2024:01:15 14:30:00",
          "camera": "iPhone 12 Pro",
          "gps": {"lat": 30.42, "lon": -97.68},
          "vision_analysis": {...},
          "color_palette": [[255, 200, 50], ...],
          "weather": {...}
        }
      ],
      "notes": "Hive looks healthy"
    }
  ]
}
```

### CSV Export
Flattened data for external analysis (generated via `data_handler.py`)

### Upload Directory
- **Local**: `data/uploads/` by default (configurable)
- **S3**: Stored in configured bucket with user/inspection hierarchy
- **GCS**: Similar hierarchy in Google Cloud Storage bucket

## Testing Approach

The project includes comprehensive test suites demonstrating best practices for external API testing and Streamlit applications.

### Test Structure
- `tests/unit/` - Fast, isolated unit tests with comprehensive mocking
- `tests/integration/` - Multi-component integration tests
- `tests/system/` - End-to-end system tests
- `tests/bulk_import/` - Bulk import template consistency tests
- `tests/fixtures/` - Reusable mock data and API responses
- `tests/conftest.py` - Shared pytest fixtures

### API Testing Standards
- **Vision API Tests** (`test_vision_api.py`): Mock Google Cloud Vision client, test bee detection, error handling, input validation
- **Weather API Tests** (`test_weather_api.py`): Mock HTTP requests, test data parsing, network errors, parameter validation
- **Test Fixtures**: Realistic mock responses in `tests/fixtures/` for consistent testing
- **Never make real API calls in tests** - All external dependencies are mocked

### Coverage Requirements
- Minimum 80% code coverage (configured in `pytest.ini`)
- Focus on business logic and error handling
- HTML coverage reports generated in `htmlcov/`

### Risk-Based Testing for Streamlit
All Streamlit changes require risk assessment:
- 🔴 **HIGH RISK**: Core flows, session state, navigation → Full testing required
- 🟡 **MEDIUM RISK**: Secondary features, UI logic → Standard testing
- 🟢 **LOW RISK**: Styling, copy, config → Minimal testing

**Always perform integration testing** - Streamlit has framework-specific constraints that unit tests miss.

**For session state/widget changes**: Check [Streamlit docs](https://docs.streamlit.io/library/api-reference/session-state) upfront to avoid costly rework.

## Development Patterns

### Adding New Storage Providers
1. Create new provider class in `src/storage/`
2. Inherit from `StorageProvider` base class
3. Implement all abstract methods: `upload_image()`, `download_image()`, `delete_image()`, `list_images()`, `get_image_url()`, `generate_thumbnail()`, `health_check()`
4. Register in `StorageManager._providers` dict
5. Add configuration template to `StorageConfig.DEFAULT_CONFIGS`
6. Create tests in `tests/system/`

### Adding New Analysis Features
1. Create new module in `src/api_services/` or extend existing
2. Follow existing patterns: error handling, retries, caching
3. Add mock responses to `tests/fixtures/`
4. Create comprehensive unit tests with mocked API calls
5. Update `app_components.py` to display results

### Adding New Pages
1. Create page file in `src/` or `src/pages/`
2. Add to navigation in `run_tracker.py`
3. Use `st.session_state` for state management
4. Follow existing UI patterns from `app_components.py`

### EXIF Extraction Strategy
The `image_processor.py` module uses a multi-library fallback approach:
1. **Primary**: `exifread` - Most comprehensive EXIF parsing
2. **Secondary**: PIL/Pillow - Standard library with basic EXIF
3. **Fallback**: `pyexiftool` - External tool wrapper (requires exiftool binary)

This handles diverse camera formats and EXIF variations robustly.

## Common Development Tasks

1. **Adding New Analysis Features**: Extend `src/api_services/vision.py` or create new API service modules
2. **UI Enhancements**: Modify `src/app_components.py` or create new component files
3. **Data Export Options**: Extend `src/utils/data_handler.py` with new format handlers
4. **Timeline Visualizations**: Enhance `src/timeline_component.py` with new Plotly chart types
5. **Storage Providers**: Follow storage provider pattern in `src/storage/base.py`
6. **Bulk Import Sources**: Implement `photo_processing_contract.py` interface
7. **API Integration Testing**: Use `tests/fixtures/` for mock responses

## Troubleshooting

### Vision API Issues
- Check `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Verify service account has Vision API permissions
- Check quota limits in GCP console
- Review error logs for API-specific error codes

### Image Processing Issues
- Verify PIL can read the image format
- Check if EXIF data exists (not all images have EXIF)
- Test with `exifread` directly: `python -m exifread <image_path>`
- For GPS issues, verify coordinates are in valid range

### Session State Problems
- Use `src/utils/session_manager.py` functions for consistent state management
- Check session state keys exist before accessing
- Remember session state resets on page reload (browser refresh)

### Storage Provider Issues
- Local: Verify directory permissions and path exists
- S3: Check AWS credentials, bucket name, region, and IAM permissions
- GCS: Verify service account credentials and bucket permissions
- Use provider's `health_check()` method to diagnose issues

### Bulk Import Issues
- S3: Verify credentials and bucket access
- Local: Check directory permissions and file formats
- URL: Verify URLs are accessible and return images
- Check error logs in bulk import wizard UI

### Docker Build Issues
- Ensure platform compatibility: `docker build --platform linux/amd64`
- For Cloud Run: Use provided `deploy.sh` script
- Check that all files referenced in Dockerfile exist
- Verify service account key is in `.streamlit/key.json`

### Common Streamlit Issues
- Widget state not persisting: Use `st.session_state` with unique keys
- Page not refreshing: Check for `st.rerun()` usage
- Navigation issues: Verify page files are in correct locations
- Session state conflicts: Use unique key prefixes per page

## Bulk import: the 2026-08-23 repair (read before changing this area)

**Verify claims about this codebase against source, not against README,
CHANGELOG, or docstrings.** Every problem below was documented as working.

What was actually wrong, and where:

- All three bulk importers called `analyze_image_with_vision_api`, which had
  never been written. The call sat inside `except ImportError`, returned `{}`,
  and logged at DEBUG. Every bulk-imported photo got zero vision data from
  `2206b78` (2025-10-02) until the fix. `vision.py` had been touched by exactly
  one commit in the repo's entire history (`139a103`, 2025-03-24), which is the
  cheapest way to confirm the feature was scaffolded and never wired.
- `stage3_complete` was hard-coded `0`; `stage4_complete` was hard-coded `0`
  with the comment "No weather integration yet". Weather in fact worked. A
  counter that reports nothing makes a working stage and a dead stage look
  identical, which is how this survived ~10 months.
- The photo dict handed to `add_photo_to_inspection` omitted `vision_analysis`,
  so results would have been dropped even after the call worked.
- **Two more of the same skeleton, found by auditing for it.**
  `_extract_gps_coordinates` imported `get_image_gps_coordinates` (never
  defined anywhere, any branch) inside `except Exception: pass`, so bulk GPS
  was always `None` — which silently redirected weather lookups to the default
  location. `_extract_color_palette` passed bytes to a function expecting a PIL
  Image, threw every time, and returned a hard-coded grey triple that looks
  like real data. The audit that found them: parse every `from X import Y` in
  `src/` and check `Y` is actually defined in `X`. Worth re-running after any
  large refactor.

Design rules that came out of it:

- **A stage that produces nothing must say so on screen.** `vision_stats`
  (`attempted`/`succeeded`/`skipped`/`last_error`) lives on
  `BulkImportTemplate`; the Step 4 summary renders it. Add the same accounting
  to any new stage rather than a hard-coded counter.
- **`_perform_vision_analysis` lives once, on `BulkImportTemplate`.** It used
  to be copy-pasted into all three importers, so one broken copy meant three.
- **Do not widen `except Exception` around deliberate raises.**
  `extract_photo_metadata` was flattening its own `RuntimeError("File does not
  exist")` into `ValueError`. Specific exceptions re-raise first now.
- **Vision client is a lazy module-level singleton** (`get_vision_analyzer`).
  Constructing `ImageAnnotatorClient` per photo re-authenticates per image, and
  a credentials failure would otherwise log once per photo.
- **`add_photo_to_inspection(photo_data, defer_save=False)`.** Bulk callers
  pass `defer_save=True` and save once; saving per photo is quadratic.

Testing note: `tests/unit/test_vision_api.py` must construct the analyzer
*inside* the patch. `setup_method` builds nothing; `self.analyzer` is a lazy
property and an autouse fixture stubs `ImageAnnotatorClient`. Reverting to
`self.analyzer = BeeVisionAnalyzer()` in setup reintroduces 12
`DefaultCredentialsError` errors and lets "mocked" tests hit the real API.

Still open in this area: weather is inspection-level and GPS-dependent; 3
tests in `tests/bulk_import/` fail on mock fixtures returning `MagicMock`
where a content-type string belongs (pre-existing, test-side).

## Documentation

Additional documentation available in `docs/`:
- `DEPLOYMENT.md` - Production deployment guide
- `DEVELOPMENT.md` - Detailed development setup and workflows
- `TECHNICAL_DECISIONS.md` - Architecture rationale and trade-offs
- `DOCUMENTATION_AND_TESTING_PLAN.md` - Testing strategy and standards
