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
pip install -r requirements.txt
```

### Running the Application
```bash
# Main application entry point
streamlit run run_tracker.py

# Development server (default port 8501)
# Application will be available at: http://localhost:8501
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

# Manual deployment steps documented in DEPLOYMENT.md
```

### Dependency Management
```bash
# The project uses both Poetry and pip for different purposes:
# - pyproject.toml: Poetry configuration with locked versions (poetry.lock)
# - requirements.txt: Simplified pip dependencies for Docker deployment

# Update dependencies
poetry update  # Updates poetry.lock
pip freeze > requirements.txt  # Update requirements.txt if needed
```

## Architecture Overview

### Multi-Page Streamlit Structure
The application follows a multi-page Streamlit architecture with navigation defined in `run_tracker.py`:

- **Main Entry Point**: `run_tracker.py` - Sets up navigation and session management
- **Authentication**: `src/login.py` - Simple authentication system
- **Core Pages**:
  - `src/app.py` - Main dashboard with photo analysis
  - `src/calendar_view.py` - Calendar timeline interface  
  - `src/gallery_view.py` - Photo gallery interface

### Core Components

**API Services** (`src/api_services/`):
- `vision.py` - Google Cloud Vision API integration for image analysis
- `weather.py` - Open-Meteo API integration for weather data

**Utilities** (`src/utils/`):
- `image_processor.py` - EXIF extraction and color analysis using PIL and ColorThief
- `data_handler.py` - Data processing, validation, and persistence
- `session_manager.py` - Streamlit session state management

**UI Components**:
- `src/app_components.py` - Reusable UI components for photo analysis
- `src/ui_components.py` - Core UI element library
- `src/timeline_component.py` - Timeline visualization logic using Plotly

### Data Flow Architecture
1. **Photo Upload** → `app_components.py` handles file upload and validation
2. **EXIF Extraction** → `image_processor.py` extracts metadata (date, GPS, camera info)
3. **Vision API Analysis** → `vision.py` analyzes image for bee-related content
4. **Weather Integration** → `weather.py` fetches environmental context using GPS/date
5. **Color Analysis** → `image_processor.py` performs color palette extraction
6. **Data Storage** → `data_handler.py` manages persistence to JSON/CSV formats
7. **Visualization** → `timeline_component.py` renders interactive timelines with Plotly

## Environment Variables

Required environment variables (create `.env` file):
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
```

Optional environment variables:
```bash
STREAMLIT_SECRET_KEY=your-secret-key
WEATHER_API_KEY=your-weather-api-key
ENVIRONMENT=development|production
LOG_LEVEL=DEBUG|INFO
```

## Key Dependencies

**Core Framework**: Streamlit 1.44.1 with multi-page navigation
**Image Processing**: PIL (Pillow) for EXIF extraction, ColorThief for color analysis
**Computer Vision**: Google Cloud Vision API 3.7.1 for beehive analysis
**Data Visualization**: Plotly 6.0.1 for interactive timelines and charts
**Weather Data**: Open-Meteo API integration via requests
**Data Management**: Pandas for CSV export, JSON for structured storage

## File Structure Patterns

### Session State Management
The app uses comprehensive session state management via `src/utils/session_manager.py`. Key session state variables:
- `logged_in` - Authentication status
- `inspection_data` - Current photo analysis data
- `timeline_data` - Historical inspection timeline
- `color_analysis` - Extracted color palettes

### Data Storage Format
- **JSON Format**: Structured inspection data with metadata, analysis results, and annotations
- **CSV Format**: Flattened data for external analysis and reporting
- **Upload Directory**: `data/uploads/` for user-uploaded images

### API Integration Patterns
- **Vision API**: Handles rate limiting, error retries, and result parsing in `vision.py`
- **Weather API**: Asynchronous weather data fetching with caching in `weather.py`
- **Error Handling**: Consistent error patterns across all API services

## Testing Approach

The project includes comprehensive test suites demonstrating best practices for external API testing:

### Test Commands
```bash
# Run all tests
pytest tests/ -v

# Run specific API tests
pytest tests/unit/test_vision_api.py tests/unit/test_weather_api.py -v

# Run with coverage reporting
pytest tests/unit/ --cov=src/api_services --cov-report=html

# Run tests matching specific patterns
pytest tests/ -k "test_error" -v
```

### Test Structure
- **`tests/unit/`**: Fast, isolated unit tests with comprehensive mocking
- **`tests/integration/`**: Multi-component integration tests
- **`tests/system/`**: End-to-end system tests
- **`tests/fixtures/`**: Reusable mock data and API responses

### API Testing Standards
- **Vision API Tests** (`test_vision_api.py`): Mock Google Cloud Vision client, test bee detection logic, error handling, input validation
- **Weather API Tests** (`test_weather_api.py`): Mock HTTP requests, test data parsing, network error scenarios, parameter validation
- **Test Fixtures**: Realistic mock responses in `tests/fixtures/` for consistent testing
- **Documentation**: `tests/README_API_TESTING.md` provides comprehensive testing patterns for junior developers

### Key Testing Principles
1. **Never make real API calls in tests** - All external dependencies are mocked
2. **Test multiple scenarios** - Success, failure, edge cases, malformed data
3. **Validate business logic** - Bee classification, weather processing, data transformation
4. **Error resilience** - Graceful degradation when external services fail
5. **Production patterns** - Demonstrate professional testing practices

### Risk-Based Testing for Streamlit
All Streamlit changes require risk assessment:
- 🔴 HIGH RISK: Core flows, session state, navigation → Full testing required
- 🟡 MEDIUM RISK: Secondary features, UI logic → Standard testing
- 🟢 LOW RISK: Styling, copy, config → Minimal testing

**Always perform integration testing** - Streamlit has framework-specific constraints that unit tests miss.

**For session state/widget changes**: Check [Streamlit docs](https://docs.streamlit.io/library/api-reference/session-state) upfront to avoid costly rework.


## Development Notes

### Google Cloud Vision API Setup
- Requires service account with Vision API permissions
- Optimized for bee-related image analysis with custom confidence thresholds
- Handles quota management and error responses gracefully

### Multi-page Navigation
- Navigation structure defined in `run_tracker.py` using Streamlit's native multi-page feature
- Session state persists across page navigation
- Authentication gates access to main application pages

### Docker Deployment
- Multi-stage Docker build optimized for Cloud Run
- Uses Python 3.11 slim base image for smaller container size
- Health checks and proper signal handling for production deployment

## Common Development Tasks

1. **Adding New Analysis Features**: Extend `src/api_services/vision.py` or create new API service modules
2. **UI Enhancements**: Modify `src/app_components.py` or create new component files
3. **Data Export Options**: Extend `src/data_io.py` with new format handlers
4. **Timeline Visualizations**: Enhance `src/timeline_component.py` with new Plotly chart types
5. **API Integration Testing**: Use `tests/fixtures/` for mock responses and follow patterns in `test_vision_api.py` and `test_weather_api.py`
6. **Adding New External APIs**: Follow comprehensive testing patterns documented in `tests/README_API_TESTING.md`

## Troubleshooting

- **Vision API Errors**: Check `GOOGLE_APPLICATION_CREDENTIALS` path and service account permissions
- **Image Processing Issues**: Verify PIL can read the image format and EXIF data exists
- **Session State Problems**: Use `src/utils/session_manager.py` functions for consistent state management
- **Docker Build Issues**: Ensure platform compatibility with `--platform linux/amd64` flag for Cloud Run