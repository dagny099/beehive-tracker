# System Architecture

The Beehive Photo Metadata Tracker follows a **multi-layered architecture** designed for performance, extensibility, and maintainability. This document provides both high-level understanding for users interested in how the application works, and detailed technical information for developers.

!!! info "For Different Audiences"
    - **Curious Users**: Focus on the "How It Works" and "Data Flow" sections to understand what happens to your photos
    - **Technical Users**: The complete architecture details show how components interact and can be extended
    - **Developers**: See the API Reference section for implementation details

## How It Works (User Perspective)

When you upload a beehive photo, here's what happens behind the scenes:

1. **Photo Processing**: Your image is analyzed for technical details (EXIF data) and visual content (colors)
2. **Environmental Context**: If GPS data exists, weather information is automatically retrieved
3. **AI Analysis**: Computer vision (if configured) identifies bees, honeycomb, and other relevant features
4. **Data Organization**: Everything is organized into inspection records with timeline visualization
5. **Export Options**: Your structured data can be exported for external analysis

This multi-step process transforms a simple photo into rich, searchable metadata while preserving all your original content.

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Multi-Page App]
        VIZ[Plotly Visualizations]
        COMP[UI Components]
    end
    
    subgraph "Application Layer"
        APP[Main App Logic]
        AUTH[Authentication]
        SESSION[Session Management]
    end
    
    subgraph "Processing Layer"  
        IMG[Image Processing]
        META[Metadata Extraction]
        COLOR[Color Analysis]
    end
    
    subgraph "Integration Layer"
        VISION[Google Vision API]
        WEATHER[Weather API]
        STORAGE[Data Persistence]
    end
    
    subgraph "Data Layer"
        JSON[JSON Storage]
        CSV[CSV Export]
        FILES[File System]
    end
    
    UI --> APP
    VIZ --> APP
    COMP --> UI
    APP --> SESSION
    APP --> AUTH
    APP --> IMG
    IMG --> META
    IMG --> COLOR
    APP --> VISION
    APP --> WEATHER
    APP --> STORAGE
    STORAGE --> JSON
    STORAGE --> CSV
    STORAGE --> FILES
    
    style UI fill:#e1f5fe
    style APP fill:#f3e5f5
    style IMG fill:#fff3e0
    style VISION fill:#e8f5e8
    style JSON fill:#fce4ec
```

## Layer Details

### 1. User Interface Layer

The presentation layer built with **Streamlit** provides an intuitive multi-page web interface.

#### Components:
- **`run_tracker.py`**: Main entry point with navigation
- **`src/app.py`**: Primary dashboard and analysis interface
- **`src/calendar_view.py`**: Calendar-based timeline visualization
- **`src/gallery_view.py`**: Photo gallery with search and filtering
- **`src/login.py`**: Simple authentication system

#### UI Component Library:
```python
# Core reusable components
src/ui_components.py       # Basic UI elements
src/app_components.py      # Photo analysis components  
src/timeline_component.py  # Timeline visualization logic
```

### 2. Application Layer

The business logic layer that orchestrates user interactions and data flow.

#### Session Management:
```python
# Comprehensive session state management
src/utils/session_manager.py
```

Key session variables:
- `logged_in`: Authentication status
- `inspection_data`: Current analysis results
- `timeline_data`: Historical inspection data
- `color_analysis`: Extracted color palettes

### 3. Processing Layer

The core image analysis and metadata extraction engine.

```mermaid
flowchart LR
    UPLOAD[Photo Upload] --> EXIF[EXIF Extraction]
    EXIF --> GPS[GPS Coordinates]
    EXIF --> TIME[Timestamp]  
    EXIF --> CAMERA[Camera Info]
    UPLOAD --> COLOR[Color Analysis]
    COLOR --> PALETTE[Color Palette]
    COLOR --> DOMINANT[Dominant Colors]
```

#### Image Processing Pipeline:
```python
# Image analysis and metadata extraction
src/utils/image_processor.py
```

**EXIF Data Extraction:**
- GPS coordinates (lat/lng)
- Capture timestamp
- Camera make/model
- Technical settings (ISO, aperture, etc.)

**Color Analysis:**
- Dominant color extraction using ColorThief
- Color palette generation (5-color scheme)
- Color distribution analysis

### 4. Integration Layer

External API services that enrich photo data with additional context.

#### Google Cloud Vision API
```python
# Computer vision analysis
src/api_services/vision.py
```

**Capabilities:**
- Object detection (bees, honeycomb, equipment)
- Text recognition (hive labels, dates)
- Safety search (content filtering)
- Image properties analysis

#### Weather API Integration  
```python
# Weather data correlation
src/api_services/weather.py
```

**Features:**
- Historical weather data retrieval
- GPS-based location services
- Temperature, humidity, precipitation data
- API rate limiting and caching

### 5. Data Layer

Flexible storage system supporting multiple export formats.

```mermaid
graph LR
    DATA[Photo Data] --> JSON[JSON Storage]
    DATA --> CSV[CSV Export]
    DATA --> META[Metadata Files]
    
    JSON --> STRUCT[Structured Relationships]
    CSV --> FLAT[Flat Analysis Format]
    META --> SEARCH[Searchable Index]
```

#### Data Handler:
```python
# Data processing and validation
src/utils/data_handler.py
```

**Storage Formats:**
- **JSON**: Complex nested metadata with relationships
- **CSV**: Flattened format for Excel/analytics tools  
- **File System**: Organized photo storage with thumbnails

## Data Flow Architecture

### Photo Analysis Workflow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Processor as Image Processor
    participant Vision as Vision API
    participant Weather as Weather API
    participant Storage as Data Handler
    
    User->>UI: Upload Photo
    UI->>Processor: Extract EXIF Data
    Processor->>UI: Return Metadata
    
    alt GPS Available
        UI->>Weather: Fetch Weather Data
        Weather->>UI: Return Weather Info
    end
    
    UI->>Vision: Analyze Image
    Vision->>UI: Return AI Analysis
    
    UI->>Processor: Extract Colors
    Processor->>UI: Return Color Palette
    
    UI->>Storage: Save Complete Record
    Storage->>UI: Confirm Save
    
    UI->>User: Display Analysis Results
```

## Component Interactions

### Multi-Page Navigation
```python
# Navigation structure in run_tracker.py
pages = {
    "Dashboard": "src.app",
    "Timeline": "src.calendar_view", 
    "Gallery": "src.gallery_view"
}
```

### Session State Flow
```python
# Session persistence across pages
if 'inspection_data' not in st.session_state:
    st.session_state.inspection_data = {}
    
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
```

## Security & Performance

### API Security
- Environment-based credential management
- Service account authentication for Google APIs
- Rate limiting and quota management

### Performance Optimizations
- Image thumbnail generation
- Session state caching
- Lazy loading of heavy components
- Asynchronous API calls where possible

### Error Handling
```python
# Consistent error patterns across services
try:
    result = api_call()
except APIException as e:
    log_error(e)
    return fallback_response()
```

## Deployment Architecture

### Docker Containerization
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim AS base
# ... dependencies installation

FROM base AS production  
# ... application setup
EXPOSE 8080
CMD ["streamlit", "run", "run_tracker.py"]
```

### Cloud Deployment
- **Platform**: Google Cloud Run
- **Scaling**: Automatic based on traffic
- **Storage**: File-based with volume mounts
- **Environment**: Production/staging configurations

## Extensibility Points

### Adding New Analysis Features
1. Create new API service in `src/api_services/`
2. Register with data handler
3. Update UI components
4. Extend session state management

### Custom Visualization Components
1. Implement in `src/timeline_component.py`
2. Integrate with Plotly framework
3. Add to navigation structure

### New Export Formats
1. Extend `src/data_io.py`
2. Update data handler interface
3. Add UI export options

---

This architecture provides a solid foundation for current features while maintaining flexibility for future enhancements and scaling requirements.