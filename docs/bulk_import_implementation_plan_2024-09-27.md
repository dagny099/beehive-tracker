# Bulk Import Implementation Plan - September 27, 2024

## Comprehensive LLM Implementation Prompt

You are tasked with implementing a complete bulk photo import system for the Beehive Tracker application. This system allows users to import hundreds of photos from S3, local directories, or URLs, automatically group them into inspections, and process them with computer vision analysis.

## Current State Overview

**COMPLETED**: Phase 1 bug fix - JSON loading now properly populates all session state variables via `load_photo_into_session_state()` helper function.

**ARCHITECTURE FOUNDATION**: Three bulk import templates already exist with comprehensive testing:
- `src/bulk_import/s3_bulk_importer.py` - AWS S3 import with authentication
- `src/bulk_import/local_bulk_importer.py` - Local directory traversal
- `src/bulk_import/url_bulk_importer.py` - Network-based URL imports
- `src/bulk_import/photo_processing_contract.py` - ABC contracts ensuring consistency
- `tests/bulk_import/` - 1,483 lines of comprehensive test coverage

**EXISTING APP STRUCTURE**:
- Date-based inspection grouping already implemented
- Multi-page Streamlit navigation (`run_tracker.py`)
- Rich photo metadata display and session state management
- Background processing patterns exist in vision/weather API integration

## Implementation Requirements

### Phase 2: Foundation & Navigation (2 days)

#### Task 2.1: Navigation Integration
**Objective**: Add bulk import as a new main page in the app navigation

**Requirements**:
1. **Update main navigation** in `run_tracker.py`:
   - Add "Bulk Import" page alongside Dashboard, Calendar, Gallery
   - Handle navigation state properly
   - Maintain session state across page transitions

2. **Create bulk import page** at `src/bulk_import_page.py`:
   - 4-step wizard layout (Source → Preview → Processing → Complete)
   - Session state management for bulk import workflow
   - Progress persistence across page navigation
   - Error handling and user feedback

**Expected Files Created**:
- `src/bulk_import_page.py` - Main bulk import interface
- Updates to `run_tracker.py` - Navigation integration

**Tests to Pass**:
```python
def test_navigation_integration():
    # Test bulk import page loads without errors
    # Test navigation state persistence
    # Test session state isolation from main app

def test_page_structure():
    # Test 4-step wizard renders correctly
    # Test step navigation works
    # Test error handling displays properly
```

#### Task 2.2: Session State Management
**Objective**: Implement robust state management for bulk import workflow

**Requirements**:
1. **Bulk import session state structure**:
```python
bulk_import_state = {
    'step': 1,  # 1=config, 2=preview, 3=processing, 4=complete
    'source_type': None,  # 's3', 'local', 'url'
    'source_config': {},  # Credentials, paths, etc
    'discovered_photos': [],
    'grouped_inspections': [],
    'processing_progress': {
        'total_photos': 0,
        'stage1_complete': 0,  # Discovery
        'stage2_complete': 0,  # Basic metadata
        'stage3_complete': 0,  # Vision analysis
        'stage4_complete': 0   # Weather integration
    },
    'created_inspections': [],
    'error_log': [],
    'import_id': None,  # Unique identifier for this import
    'start_time': None,
    'completion_time': None
}
```

2. **State persistence functions**:
   - `initialize_bulk_import_state()`
   - `save_bulk_import_progress()`
   - `resume_bulk_import_session()`
   - `clear_bulk_import_state()`

### Phase 3: Source Configuration (2 days)

#### Task 3.1: S3 Configuration Interface
**Objective**: Create user-friendly S3 credential input and validation

**Requirements**:
1. **S3 Configuration Form**:
   - Bucket name input with validation
   - Region selection dropdown (all AWS regions)
   - Access key ID input (with show/hide toggle)
   - Secret access key input (masked, with show/hide toggle)
   - Optional prefix filter for subdirectories
   - Session token support (for temporary credentials)

2. **Connection Testing**:
   - "Test Connection" button
   - Real-time validation feedback
   - Photo count preview ("✅ Connected, 247 photos found")
   - Error handling with helpful messages
   - Progress indicator during testing

3. **Integration with existing S3BulkImporter**:
   - Use factory function `create_s3_bulk_importer()`
   - Handle all authentication methods
   - Validate bucket access and permissions

**Tests to Pass**:
```python
def test_s3_configuration():
    # Test form renders correctly
    # Test credential validation
    # Test connection testing
    # Test error handling for invalid credentials
    # Test photo discovery and counting

def test_s3_integration():
    # Test factory function integration
    # Test bulk importer initialization
    # Test photo listing functionality
```

#### Task 3.2: Local Directory Configuration
**Objective**: File system browser and directory selection

**Requirements**:
1. **Directory Selection Interface**:
   - Directory path input
   - Browse button (using Streamlit file uploader workaround)
   - Recursive scanning toggle
   - File type filter options
   - Max depth setting

2. **Directory Validation**:
   - Path existence checking
   - Permission validation
   - Photo discovery preview
   - File count and size estimation

#### Task 3.3: URL Configuration Interface
**Objective**: URL list input and validation

**Requirements**:
1. **URL Input Methods**:
   - Text area for URL list (one per line)
   - File upload for URL lists
   - URL validation and testing
   - Authentication options (basic auth, headers)

2. **URL Validation**:
   - Format validation
   - Connectivity testing
   - Content-type verification
   - Size estimation

### Phase 4: Preview & Grouping (2 days)

#### Task 4.1: Photo Discovery Integration
**Objective**: Use existing bulk import templates to discover and preview photos

**Requirements**:
1. **Photo Discovery**:
   - Integrate with `list_available_photos()` from templates
   - Display photo count and estimated processing time
   - Show sample photos (thumbnails if possible)
   - Group photos by date automatically

2. **Grouping Preview**:
   - Show inspection groups that will be created
   - Display photos per group
   - Allow manual grouping adjustments
   - Estimate processing time and API costs

**Tests to Pass**:
```python
def test_photo_discovery():
    # Test integration with bulk import templates
    # Test photo counting and grouping
    # Test preview display
    # Test grouping strategy application

def test_grouping_preview():
    # Test inspection group creation
    # Test group editing functionality
    # Test processing estimation
```

#### Task 4.2: Processing Options
**Objective**: Allow users to choose processing depth

**Requirements**:
1. **Processing Levels**:
   - **Quick Import**: Basic metadata only (EXIF, file info)
   - **Standard Import**: + Vision analysis sampling (every Nth photo)
   - **Full Analysis**: All photos get complete analysis

2. **Cost and Time Estimation**:
   - Calculate Vision API costs
   - Estimate processing time
   - Show resource usage warnings
   - Allow user to proceed with informed choice

### Phase 5: Processing Pipeline (3 days)

#### Task 5.1: Background Processing System
**Objective**: Implement robust background processing with progress tracking

**Requirements**:
1. **Processing Architecture**:
```python
class BulkImportProcessor:
    def __init__(self, import_config, progress_callback):
        self.config = import_config
        self.progress_callback = progress_callback

    async def process_bulk_import(self):
        # Stage 1: Photo discovery
        # Stage 2: Basic metadata extraction
        # Stage 3: Vision analysis (if selected)
        # Stage 4: Weather integration
        # Stage 5: Integration with existing inspections

    def update_progress(self, stage, completed, total):
        # Update session state
        # Trigger UI refresh
        # Log progress events
```

2. **Stage-by-Stage Processing**:
   - **Stage 1**: Discovery - populate `discovered_photos`
   - **Stage 2**: Metadata - extract EXIF, basic info for all photos
   - **Stage 3**: Vision - analyze photos based on processing level
   - **Stage 4**: Weather - fetch weather data for unique locations/dates
   - **Stage 5**: Integration - convert to existing inspection format

3. **Progress Tracking**:
   - Real-time progress bars for each stage
   - Overall completion percentage
   - ETA calculation
   - Recent activity log
   - Error tracking and recovery

**Tests to Pass**:
```python
def test_background_processing():
    # Test processing pipeline stages
    # Test progress tracking
    # Test error handling and recovery
    # Test session state updates

def test_integration_with_existing_system():
    # Test conversion to existing inspection format
    # Test data consistency
    # Test timeline/gallery integration
```

#### Task 5.2: Real-Time UI Updates
**Objective**: Show processing progress without requiring user to stay on page

**Requirements**:
1. **Auto-refresh Pattern**:
   - Check processing status every 10 seconds
   - Update progress bars and statistics
   - Show recent activity feed
   - Handle browser refresh gracefully

2. **User Interaction During Processing**:
   - Allow navigation away from processing page
   - Resume progress display when returning
   - Provide pause/cancel functionality
   - Show completion notifications

#### Task 5.3: Error Handling & Recovery
**Objective**: Robust error handling with user-friendly recovery options

**Requirements**:
1. **Error Categories**:
   - Network errors (retry automatically)
   - Authentication errors (prompt for new credentials)
   - File access errors (skip file, continue processing)
   - API quota errors (pause, resume later)

2. **Recovery Mechanisms**:
   - Automatic retry with exponential backoff
   - Manual retry options
   - Skip problematic files
   - Resume from last successful stage

### Phase 6: Completion & Integration (1-2 days)

#### Task 6.1: Results Integration
**Objective**: Seamlessly integrate bulk import results with existing app

**Requirements**:
1. **Data Format Conversion**:
```python
def convert_bulk_results_to_inspections(bulk_groups):
    """Convert InspectionGroup objects to existing inspection format"""
    # Maintain compatibility with existing data structure
    # Preserve all metadata and analysis results
    # Ensure timeline/gallery integration works
```

2. **Session State Integration**:
   - Update main app session state with new inspections
   - Trigger timeline refresh
   - Navigate to gallery or timeline view
   - Preserve import history

**Tests to Pass**:
```python
def test_results_integration():
    # Test data format conversion
    # Test session state updates
    # Test timeline/gallery integration
    # Test import history tracking

def test_end_to_end_workflow():
    # Test complete S3 import workflow
    # Test complete local import workflow
    # Test complete URL import workflow
    # Verify final data consistency
```

#### Task 6.2: Success Summary & Navigation
**Objective**: Provide clear completion feedback and next steps

**Requirements**:
1. **Completion Summary**:
   - Photos processed count
   - Inspections created count
   - Processing time and statistics
   - Error summary (if any)

2. **Next Steps**:
   - Navigate to timeline view
   - Navigate to gallery view
   - Export data options
   - Import additional photos

## Critical Implementation Notes

### 1. Background Processing Pattern
Use this pattern for processing that can take several minutes:
```python
# Store processing state in session_state with unique ID
if st.button("Start Import"):
    import_id = str(uuid.uuid4())
    st.session_state.bulk_import_state['import_id'] = import_id
    st.session_state.bulk_import_state['processing_active'] = True
    # Start background processing

# Check progress periodically
if st.session_state.bulk_import_state.get('processing_active'):
    # Auto-refresh every 10 seconds
    time.sleep(0.1)  # Brief pause
    st.rerun()
```

### 2. Data Consistency Requirements
- All bulk imported photos must integrate seamlessly with existing single-photo workflow
- Use existing `add_photo_to_inspection()` logic for consistency
- Maintain existing JSON export/import compatibility
- Preserve all metadata fields and analysis results

### 3. User Experience Principles
- **Transparency**: Users always know what's happening and why
- **Control**: Users can pause, cancel, or modify processing
- **Feedback**: Clear progress indication and error messages
- **Recovery**: Graceful handling of failures with retry options

### 4. Performance Considerations
- Process photos in batches (10-20 at a time)
- Rate limit API calls to avoid quotas
- Use existing caching mechanisms where possible
- Provide realistic time estimates

### 5. Testing Requirements
- Mock all external dependencies (S3, Vision API, etc.)
- Test error scenarios extensively
- Verify cross-template consistency
- End-to-end workflow testing for each source type

## Expected Deliverables

1. **Navigation Integration** - Bulk import accessible from main menu
2. **Source Configuration** - S3, Local, URL setup with validation
3. **Photo Discovery** - Preview and grouping functionality
4. **Processing Pipeline** - Background processing with progress tracking
5. **Results Integration** - Seamless integration with existing app
6. **Comprehensive Testing** - Unit and integration tests for all components
7. **Documentation** - User guide and troubleshooting information

## Success Criteria

The implementation is complete when:
- [ ] Users can import 100+ photos from any source (S3/Local/URL)
- [ ] Photos are automatically grouped into date-based inspections
- [ ] Processing continues in background without requiring user presence
- [ ] Results integrate seamlessly with existing timeline/gallery views
- [ ] All error scenarios are handled gracefully with recovery options
- [ ] Comprehensive test coverage ensures reliability
- [ ] User documentation enables self-service troubleshooting

**Estimated Timeline**: 8-9 days total development time
**Priority**: High - Transforms single-photo tool into comprehensive hive monitoring system