# Changelog

All notable changes to the Beehive Photo Metadata Tracker project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

#### Bulk import Vision stage (2026-08-23)
- **Vision analysis now runs during bulk import.** All three bulk importers
  called `analyze_image_with_vision_api`, a function that did not exist. The
  call sat inside `except ImportError`, returned `{}`, and logged at DEBUG, so
  every bulk-imported photo silently received zero vision data from the
  feature's introduction (`2206b78`, 2025-10-02) until this fix. This
  supersedes the 0.1.0 entry claiming "Stage 3: Vision API analysis"; that
  stage was scaffolded but never functional. `vision.py` had been touched by
  exactly one commit in the repo's history (`139a103`, 2025-03-24).
- **`vision_analysis` is carried into the app.** The bulk path built its photo
  dict without the key, so results would have been discarded at handoff even
  once the call worked. `data_handler` and `ui_components` both read it.
- **Specific exceptions are no longer flattened.** `extract_photo_metadata` in
  all three importers ended with `except Exception: raise ValueError(...)`,
  which caught the deliberate `RuntimeError("File does not exist")` raised
  above it. Callers could not distinguish a missing file from an invalid
  image, contrary to the docstring contract.
- **GPS was never extracted during bulk import.** `_extract_gps_coordinates`
  imported `get_image_gps_coordinates`, a function that has never existed on
  any branch, inside `except Exception: pass`. Every bulk-imported photo came
  back with `gps_coordinates=None`. The damage cascaded: no GPS meant
  `get_inspection_location` fell back to the configured default, so weather
  was fetched for the default coordinates rather than where the photo was
  taken. Now uses the real helper, `convert_gps_to_decimal`, with `GPSTAGS` to
  decode PIL's integer-keyed GPSInfo, and range-checks the result.
- **Colour palettes were fake.** `_extract_color_palette` passed raw bytes to
  `extract_color_palette`, which expects a PIL Image and calls `img.save()`.
  It threw on every photo, and the handler returned a hard-coded
  `["#CCCCCC", "#DDDDDD", "#EEEEEE"]` that looks like real data in the
  gallery. Now decodes the image first, and returns `[]` on genuine failure
  so missing data reads as missing.
- **Repeated failed weather lookups.** A failed fetch left `weather_data`
  falsy, so every subsequent photo in the same inspection retried it, blocking
  HTTP call and timeout included. Guarded with `weather_fetch_attempted`.
- **Quadratic saves during bulk import.** `add_photo_to_inspection` wrote the
  entire inspection set to disk once per photo. It accepts `defer_save` now;
  bulk import saves once at the end. Single-photo callers are unchanged.
- **Photo resolution.** The bulk path hard-coded `'Unknown'` with a "Phase 4"
  comment. `_extract_exif_data` now records `ImageWidth`/`ImageHeight` from the
  decoded image when EXIF omits them, which is common on phone photos.
- **Vision unit tests could not run.** `setup_method` constructed a real
  `BeeVisionAnalyzer` before each test's `@patch` took effect: 12 tests errored
  with `DefaultCredentialsError` without credentials, and with credentials the
  mocks never replaced the live client, so "mocked" tests could reach the real
  API. Also fixed a patch target typo
  (`...vision.vision.vision.Image`) and a concurrency test that built its
  analyzer outside the patch. Suite went from 2 passed/1 failed/12 errors to
  15 passed.

### Changed
- **Per-stage reporting in bulk import.** `stage3_complete` was hard-coded to
  `0` and `stage4_complete` to `0` with the comment "No weather integration
  yet". Both now report real counts, and the Step 4 summary states how many
  photos were analyzed and how many inspections were weather-enriched,
  including the reason when a stage produced nothing. A stage that silently
  does nothing is what let the Vision gap survive ~10 months.
- **Shared `_perform_vision_analysis`.** Removed three near-identical copies
  from the importers in favour of one implementation on `BulkImportTemplate`,
  which also owns the new `vision_stats` counters.
- Vision client is built lazily and reused rather than per photo, and the
  `print(f"Analyzing image: {image_data}")` that dumped whole JPEGs to stdout
  is now a `logger.debug` with type and size.
- Reorganized documentation structure for better maintainability
- Updated `.gitignore` to exclude additional temporary files

### Known issues
- Weather enrichment works in bulk import (via `add_photo_to_inspection`), but
  is inspection-level only and depends on photos carrying GPS.
- 3 tests in `tests/bulk_import/test_url_template.py` and
  `test_template_consistency.py` fail on mock fixtures that return a
  `MagicMock` where a content-type string is expected. Test-fixture bugs, not
  product bugs. They failed identically before these changes.

## [0.1.0] - 2025-10-25

Initial release of the Beehive Photo Metadata Tracker - an AI-powered beekeeping management system with computer vision and environmental data integration.

### Added

#### Core Application (March - April 2025)
- **Multi-page Streamlit application** with authentication system
- **Photo upload and metadata extraction** using PIL, exifread, and pyexiftool
- **Interactive timeline visualization** using Plotly for chronological inspection history
- **Calendar view** for date-based inspection browsing
- **Photo gallery interface** for visual inspection management
- **Google Cloud Vision API integration** for beehive and bee detection
- **Weather data integration** via Open-Meteo API with GPS-based lookup
- **Color palette analysis** using ColorThief for honeycomb health indicators
- **EXIF metadata extraction** with multi-library fallback strategy
- **GPS coordinate extraction and validation** from photo metadata
- **Docker containerization** with multi-stage build for deployment
- **Google Cloud Run deployment** scripts and configuration

#### Data Management (September 2025)
- **JSON-based persistence** for inspection data with auto-save functionality
- **CSV export capability** for external analysis tools
- **Auto-load last backup** feature - automatically loads most recent JSON backup on app refresh
- **Inspection labeling system** with human-readable titles based on date/time
- **Data migration tools** for moving between storage providers
- **Backup and restore functionality** with timestamp tracking

#### Storage System (September 2025)
- **Storage abstraction layer** with provider pattern architecture
- **Local filesystem storage provider** with configurable base path
- **AWS S3 storage provider** with full CRUD operations
  - Credential management and validation
  - Bucket creation and configuration
  - Signed URL generation for secure access
  - Thumbnail generation support
- **Storage Manager** for runtime provider switching
- **Storage configuration UI** with guided setup wizard
- **Storage health checks** and status monitoring
- **Storage analytics dashboard** showing usage metrics and cost estimates
- **Environment-based configuration** for storage backends

#### Bulk Import System (October 2025)
- **4-step bulk import wizard** with progress tracking
- **AWS S3 bulk importer** for importing entire buckets or prefixes
- **Local directory bulk importer** with recursive scanning
- **URL-based bulk importer** for importing from web sources
- **Photo processing contract** interface for consistent importer behavior
- **Batch processing pipeline** with stage-based progress indicators
  - Stage 1: Photo discovery
  - Stage 2: EXIF metadata extraction
  - Stage 3: Vision API analysis
  - Stage 4: Weather data integration
- **Error logging and reporting** for failed imports
- **Photo grouping by date** for automatic inspection creation

#### Testing Infrastructure (September 2025)
- **Comprehensive pytest test suite** with 80% minimum coverage requirement
- **Unit tests** for core utilities and business logic
- **Integration tests** for API services and multi-component workflows
- **System tests** for storage providers and end-to-end flows
- **Bulk import template consistency tests**
- **Mock fixtures** for Google Cloud Vision API responses
- **Mock fixtures** for Open-Meteo weather API responses
- **Device coverage tests** for EXIF extraction across different cameras
- **Performance benchmarks** for image processing operations
- **Coverage reporting** with HTML reports

#### Documentation (August - September 2025)
- **Comprehensive README** with architecture diagrams and technical overview
- **MkDocs documentation site** with dual-audience configuration
  - Engineering site with API references and implementation details
  - Portfolio site for project showcase and onboarding
- **DEPLOYMENT.md** with Cloud Run setup instructions
- **DEVELOPMENT.md** with development workflows and patterns
- **TECHNICAL_DECISIONS.md** documenting architecture rationale
- **DOCUMENTATION_AND_TESTING_PLAN.md** for testing strategy
- **API Reference documentation** for all major modules
- **User guide** with feature walkthroughs
- **CLAUDE.md** for AI-assisted development guidance

#### Developer Experience
- **Poetry dependency management** with locked versions
- **pytest configuration** with markers and coverage settings
- **Docker multi-stage builds** optimized for production
- **Deployment automation** with `deploy.sh` script
- **Custom beehive theming** with honey-inspired color palette
  - Amber/orange color scheme
  - Hexagon patterns and bee iconography
  - Animated hover effects and gradients
  - Dark/light mode support with consistent branding
- **Mermaid diagram support** with custom beehive styling
- **Environment variable configuration** for flexible deployment

### Changed
- **Project structure reorganization** (September 2025) - Consolidated code organization with clear separation of concerns
- **Streamlit navigation** - Upgraded to native multi-page navigation from custom implementation
- **EXIF extraction** - Enhanced with three-library fallback for maximum compatibility
- **Session state management** - Centralized in `session_manager.py` for consistency
- **Docker base image** - Optimized to Python 3.9-slim for smaller container size
- **Documentation structure** - Reorganized from flat to hierarchical for better discoverability

### Fixed
- **Image upload stability** - Improved error handling for corrupt or malformed images
- **GPS coordinate parsing** - Fixed edge cases with DMS to decimal conversion
- **Session state persistence** - Resolved issues with state loss during navigation
- **Docker deployment** - Fixed Cloud Run compatibility issues with proper health checks
- **Documentation links** - Corrected broken internal references
- **EXIF extraction edge cases** - Handled missing or malformed EXIF data gracefully
- **.gitignore coverage** - Excluded temporary upload files and build artifacts

### Security
- **Credential management** - Secure storage of AWS and GCP credentials
- **Service account handling** - Proper GOOGLE_APPLICATION_CREDENTIALS environment variable usage
- **Signed URLs** - Temporary authenticated access to S3 objects with expiration
- **Input validation** - Comprehensive validation of file uploads and user inputs

## Release Notes

### Version 0.1.0 Highlights

**Transform Your Beekeeping Practice**: This initial release provides beekeepers with a production-ready system to turn unstructured hive photos into a searchable, analyzable knowledge base.

**Key Capabilities**:
- 📸 **Automated Metadata Extraction** - Pull EXIF data from photos automatically
- 🤖 **AI-Powered Analysis** - Computer vision identifies bees and hive components
- 🌦️ **Environmental Context** - Weather data correlated with inspection dates
- 🎨 **Color Intelligence** - Palette analysis for honeycomb health indicators
- 📊 **Visual Timeline** - Interactive Plotly charts showing inspection history
- ☁️ **Flexible Storage** - Local, AWS S3, or Google Cloud Storage backends
- 📦 **Bulk Import** - Process hundreds of photos from S3, local dirs, or URLs
- 🐳 **Cloud Ready** - Docker containerization and Cloud Run deployment

**Technical Excellence**:
- 80% test coverage with comprehensive mocking of external APIs
- Multi-library EXIF extraction for broad camera compatibility
- Storage abstraction layer for easy provider switching
- Professional error handling and graceful degradation
- Production-ready Docker deployment

**Perfect For**:
- Hobbyist beekeepers tracking 1-10 hives
- Commercial operations managing inspection records
- Researchers analyzing seasonal patterns
- Educators documenting hive development

---

## Migration Guide

### Upgrading from Pre-0.1.0 Development Versions

If you were using an early development version, follow these steps:

1. **Backup your data**:
   ```bash
   cp -r data/ data_backup_$(date +%Y%m%d)/
   ```

2. **Update dependencies**:
   ```bash
   poetry install
   # or
   pip install -r requirements.txt
   ```

3. **Configure storage** (if using cloud storage):
   ```bash
   export STORAGE_PROVIDER=local  # or s3, gcs
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
   ```

4. **Run migrations** (if needed):
   - JSON data format is backward compatible
   - Storage paths may need updating for cloud providers

---

## Future Roadmap

Planned features for future releases:

### [0.2.0] - Planned
- **Advanced Analytics Dashboard**
  - Seasonal trend analysis
  - Hive health scoring algorithms
  - Predictive insights based on historical data
- **Multi-user Support**
  - User authentication and authorization
  - Shared hive management
  - Collaborative annotations
- **Mobile App**
  - iOS and Android native apps
  - On-site photo capture with instant metadata
  - Offline-first architecture with sync

### [0.3.0] - Planned
- **Enhanced Computer Vision**
  - Varroa mite detection
  - Queen bee identification
  - Brood pattern analysis
  - Honey flow estimation
- **Export and Reporting**
  - PDF inspection reports
  - Automated seasonal summaries
  - Data export to common beekeeping platforms

### [0.4.0] - Planned
- **Integration Ecosystem**
  - Weather station direct integration
  - Hive scale data correlation
  - Third-party beekeeping app connections
- **Notification System**
  - Inspection reminders
  - Anomaly detection alerts
  - Seasonal task suggestions

---

## Contributing

We welcome contributions! Please see our [DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Development setup instructions
- Coding standards and patterns
- Testing requirements
- Pull request process

## Support

- 📖 **Documentation**: See `docs/` directory
- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Open an issue with the "enhancement" label
- 📧 **Contact**: dagny099@gmail.com

## License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

---

**Note**: All dates in this changelog reflect the actual development timeline of the project. Version 0.1.0 represents the first stable release consolidating features developed from March through October 2025.

[Unreleased]: https://github.com/dagny099/beehive-tracker/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dagny099/beehive-tracker/releases/tag/v0.1.0
