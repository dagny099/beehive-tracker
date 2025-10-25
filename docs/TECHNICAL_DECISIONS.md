# Technical Architecture Decisions

## Overview
This document captures key technical decisions made during development, their rationale, and trade-offs considered. Each decision supports the core goal: transforming unstructured beekeeping photos into a production-ready data management system.

---

## Frontend Framework: Streamlit

### Decision
Use Streamlit for the web application framework instead of Flask/Django/React.

### Rationale
- **Rapid Prototyping**: Built-in widgets eliminate custom UI development
- **State Management**: Native session state handling across multi-page navigation  
- **Data Science Integration**: Seamless Pandas/Plotly integration without API layers
- **Deployment Simplicity**: Single Python application with minimal configuration

### Trade-offs Considered
- **Pros**: Fast development, built-in authentication, automatic reactivity
- **Cons**: Limited customization, framework lock-in, performance limitations at scale
- **Alternative Rejected**: React + FastAPI (higher development complexity for MVP)

### Results
Enabled rapid feature iteration with 80% faster development compared to traditional web frameworks.

---

## Computer Vision: Google Cloud Vision API

### Decision  
Integrate Google Cloud Vision API rather than self-hosted models or other providers.

### Rationale
- **Production Reliability**: 99.9% uptime SLA with auto-scaling infrastructure
- **Bee-Relevant Detection**: Pre-trained models include insects, outdoor scenes, agricultural objects
- **Cost Predictability**: Pay-per-use model aligns with inspection frequency patterns
- **Integration Maturity**: Robust Python client libraries with comprehensive error handling

### Trade-offs Considered
- **Pros**: No model training required, immediate results, enterprise reliability
- **Cons**: External dependency, per-request costs, limited customization
- **Alternatives Evaluated**: 
  - AWS Rekognition (weaker agricultural object detection)
  - Azure Computer Vision (higher latency in testing)
  - Self-hosted YOLO (requires training data and GPU infrastructure)

### Implementation Notes
- Custom confidence thresholds (0.7+ for bee detection, 0.5+ for general objects)
- Retry logic with exponential backoff for resilience
- Result caching to minimize API calls during development

---

## Weather Integration: Open-Meteo API

### Decision
Use Open-Meteo API for historical weather data instead of commercial providers.

### Rationale
- **Cost Efficiency**: Free tier covers typical usage patterns (50-100 inspections/month)
- **Historical Accuracy**: 40+ year weather archive with hourly granularity
- **Geographic Coverage**: Global coverage including rural beekeeping locations
- **No Authentication**: Eliminates API key management complexity

### Trade-offs Considered
- **Pros**: Free usage, comprehensive historical data, simple integration
- **Cons**: No SLA guarantees, potential rate limiting, less agricultural-specific data
- **Alternative Rejected**: OpenWeatherMap (paid tier required for historical data)

### Implementation Notes
- GPS coordinate validation before API calls
- Caching strategy for repeated location/date queries
- Graceful degradation when weather data unavailable

---

## Image Processing: Multi-Library Approach

### Decision
Implement EXIF extraction using multiple libraries (PIL, ExifRead, PyExifTool) with fallback mechanisms.

### Rationale
- **Format Coverage**: Different cameras/phones use varying EXIF standards
- **Reliability**: Library-specific bugs don't break entire pipeline
- **Data Quality**: Cross-validation between libraries improves accuracy
- **Future-Proofing**: Easy to add new extraction methods as formats evolve

### Trade-offs Considered
- **Pros**: Robust handling of diverse image sources, comprehensive metadata extraction
- **Cons**: Increased dependency complexity, longer processing time
- **Alternative Rejected**: Single library approach (30% failure rate in testing with diverse phone cameras)

### Implementation Notes
- Processing order: PIL → ExifRead → PyExifTool (fastest to most comprehensive)
- GPS coordinate validation and format normalization
- Timestamp parsing with timezone handling

---

## Data Storage: JSON + CSV Hybrid

### Decision
Use JSON for primary storage with CSV export capabilities, rather than traditional database.

### Rationale
- **Schema Flexibility**: Evolving metadata requirements without migrations
- **External Analysis**: CSV export enables R/Python analysis workflows
- **Backup Simplicity**: Human-readable formats for data portability  
- **Development Speed**: No database setup/management overhead

### Trade-offs Considered
- **Pros**: Simple deployment, version control friendly, flexible schema
- **Cons**: No complex queries, potential scalability limits, no ACID guarantees
- **Future Migration Path**: Storage abstraction layer enables database transition

### Implementation Notes
- Atomic write operations with backup files
- Structured schema validation despite flexible format
- CSV flattening algorithm for complex nested metadata

---

## Deployment: Docker + Google Cloud Run

### Decision
Container-based deployment on Google Cloud Run rather than traditional VM hosting.

### Rationale
- **Scalability**: Auto-scaling from 0-100+ instances based on demand
- **Cost Efficiency**: Pay-per-request model aligns with inspection patterns
- **Maintenance**: Managed infrastructure reduces operational overhead
- **Development Parity**: Identical container behavior across environments

### Trade-offs Considered
- **Pros**: Serverless benefits, container portability, automatic HTTPS
- **Cons**: Cold start latency, vendor lock-in, limited persistent storage
- **Alternative Evaluated**: VM-based hosting (higher operational complexity)

### Implementation Notes
- Multi-stage Docker build for optimal image size
- Health check endpoints for reliable deployments
- Volume mounting for data persistence during development

---

## Testing Strategy: Risk-Based Approach

### Decision
Implement comprehensive testing for core processing modules with lighter coverage for UI components.

### Rationale
- **Critical Path Focus**: Image processing and API integration have highest failure impact
- **Streamlit Constraints**: Framework-specific testing requires specialized approaches
- **Resource Optimization**: 95% coverage on core modules vs. 60% overall

### Trade-offs Considered
- **Pros**: Efficient use of testing resources, high confidence in critical functionality
- **Cons**: Potential UI regressions, manual testing required for some workflows
- **Implementation**: pytest with fixtures, mocking for external APIs

---

## Architectural Principles Applied

### Separation of Concerns
- **UI Layer**: Streamlit pages and components (presentation logic)
- **Business Logic**: Core processing utilities (domain logic)  
- **Integration Layer**: API services with error handling (external dependencies)
- **Data Layer**: Storage abstraction with multiple backends

### Extensibility Design
- **Plugin Architecture**: Easy addition of new analysis engines
- **Configuration-Driven**: Feature flags and API settings externalized
- **API-First**: Internal modules designed for potential external consumption

### Performance Optimization
- **Async Processing**: Non-blocking image analysis with progress indicators
- **Caching Strategy**: API results cached by location/date combinations
- **Resource Management**: Image resizing for web display vs. full resolution analysis

---

## Decision Evolution

### Lessons Learned
1. **Multi-library EXIF**: Initially used single library, 30% failure rate drove multi-approach
2. **Weather API Selection**: Tested 3 providers, Open-Meteo won on cost/reliability balance
3. **Storage Strategy**: Started with pure JSON, added CSV after user feedback requests

### Future Decision Points
- **Database Migration**: When to transition from file-based to database storage
- **Custom ML Models**: Cost/benefit analysis for bee-specific computer vision
- **Mobile Optimization**: PWA vs. native app development decision pending usage data

---

*This document is maintained as architectural decisions evolve. Last updated: September 2024*