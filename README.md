# 🐝 Beehive Photo Metadata Tracker

## Executive Summary
*AI-powered beekeeping management system with computer vision and environmental data integration*

**Transform unstructured hive inspection photos into a structured, searchable knowledge base that enhances beekeeping management practices.**

<div style="text-align: center; min-width: 250px;">
  <a href="src/default_beepic.jpg" target="_blank">
  <img src="src/default_beepic.jpg" alt="Beehive Inspection Photo" style="max-width: 400px; height: auto; cursor: zoom-in; padding-left: 2em;">
  </a>
</div>

---

## Problem Statement

Beekeepers capture thousands of inspection photographs but lack systematic tools to:
- **Track hive health patterns** over time with objective data
- **Correlate visual observations** with environmental conditions  
- **Search and analyze** historical inspection data efficiently
- **Make data-driven decisions** about hive management

Current solutions require manual documentation, making pattern recognition and seasonal planning inefficient and error-prone.

---

## Solution Impact

This Streamlit-based web application addresses critical apiculture needs through automated data extraction and analysis:

### Business Value Delivered
- **Streamlined Documentation**: Automated metadata extraction eliminates manual data entry
- **Enhanced Decision Making**: Weather correlation provides environmental context for hive conditions
- **Pattern Recognition**: Timeline visualizations reveal seasonal trends and health indicators
- **Searchable Knowledge Base**: Structured data enables rapid historical analysis

### Key Capabilities
- **Interactive timeline visualization** displaying chronological inspection history  
- **Automated metadata extraction** including dates, GPS coordinates, and camera information   
- **Color palette analysis** for identifying honeycomb health indicators  
- **Weather data integration** providing environmental context for inspections  
- **Annotation system** for beekeeper observations and hive state tracking  

---

## Technical Implementation

### Architecture Overview  
Multi-layered design optimized for performance and extensibility:

<div style="text-align: center; margin: 20px 0;">
  <a href="docs/images/tech-stack-depiction-lg.png" target="_blank">
  <img src="docs/images/tech-stack-depiction.png" alt="Tech Stack Architecture" style="max-width: 700px; height: auto; cursor: zoom-in;">
  </a>
</div>

**Layer Architecture:**
- **UI Layer**: Streamlit multi-page app with Plotly visualizations
- **Processing Layer**: Python-based image analysis and metadata extraction  
- **API Layer**: Google Cloud Vision API + Open-Meteo weather integration
- **Storage Layer**: Flexible JSON/CSV with cloud storage abstraction

### Technology Stack & Rationale

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Frontend** | Streamlit, Plotly | Rapid prototyping + built-in state management + interactive visualizations |
| **Image Processing** | PIL, ColorThief | Multi-library EXIF extraction + agricultural color analysis |
| **Computer Vision** | Google Cloud Vision API | Production-ready bee/hive object detection |
| **Weather Integration** | Open-Meteo API | Historical weather correlation with free tier |
| **Data Storage** | JSON, Pandas CSV | Structured metadata + external analysis compatibility |
| **Deployment** | Docker, Google Cloud Run | Containerized scalability + serverless cost efficiency |

### Data Flow Architecture

<div style="text-align: center; margin: 20px 0;">
  <a href="docs/images/diagram_flow.png" target="_blank">
  <img src="docs/images/diagram_flow.png" alt="Data Processing Flow" style="max-width: 650px; height: auto; cursor: zoom-in;">
  </a>
</div>

**Processing Pipeline:** Photo Upload → EXIF Extraction → Computer Vision Analysis → Weather Integration → Color Analysis → Structured Storage → Timeline Visualization

---

## Technical Achievements

### Production-Ready Engineering
- **Multi-page Streamlit Architecture**: Session state management across navigation
- **Containerized Deployment**: Docker with health checks and Cloud Run optimization
- **Robust Error Handling**: Comprehensive user feedback and graceful degradation
- **Test Coverage**: Comprehensive pytest suite for core processing modules

### Advanced Data Processing
- **Multi-Library EXIF Extraction**: Fallback mechanisms for diverse camera formats
- **GPS Validation Pipeline**: Coordinate verification and weather API integration  
- **Computer Vision Optimization**: Custom confidence thresholds for agricultural use cases
- **Color Analysis Pipeline**: Bee-domain specific palette extraction and clustering

### Scalable Architecture Design
- **Storage Abstraction**: Pluggable backends (local → S3 → GCS transition ready)
- **Modular Processing**: Extensible analysis engines for additional AI capabilities
- **API Integration Patterns**: Rate limiting, caching, and retry mechanisms
- **Performance Optimization**: Async processing with user progress indicators

---

## Project Structure

```
beehive-tracker/
├── 📁 notebooks/                     # Portfolio showcase and analysis
│   ├── 01_vision_api_exploration.ipynb    # Computer vision deep dive
│   ├── 02_data_visualization_experiments.ipynb # Plotly timeline development
│   └── 03_portfolio_showcase.ipynb        # Executive summary and workflow demo
├── 📁 src/                           # Production application code
│   ├── 📄 app.py                     # Main dashboard page
│   ├── 📄 login.py                   # Authentication system
│   ├── 📄 calendar_view.py           # Calendar timeline interface
│   ├── 📄 gallery_view.py            # Photo gallery interface
│   ├── 📄 app_components.py          # Reusable UI components
│   ├── 📄 timeline_component.py      # Timeline visualization logic
│   ├── 📁 api_services/              # External API integrations
│   │   ├── 📄 vision.py              # Google Cloud Vision API client
│   │   └── 📄 weather.py             # Weather data API integration
│   ├── 📁 utils/                     # Core processing utilities
│   │   ├── 📄 image_processor.py     # EXIF extraction and color analysis
│   │   ├── 📄 data_handler.py        # Data processing and validation
│   │   └── 📄 session_manager.py     # Session state management
│   ├── 📁 storage/                   # Storage abstraction layer
│   └── 📁 pages/                     # Additional Streamlit pages
├── 📁 tests/                         # Comprehensive test suite
│   ├── 📁 unit/                      # Component-level testing
│   ├── 📁 integration/               # API and workflow testing
│   └── 📁 fixtures/                  # Test data and mocks
├── 📁 docs/                          # Architecture diagrams and guides
├── 📄 run_tracker.py                 # 🚀 Application entry point
├── 📄 TECHNICAL_DECISIONS.md         # Architecture rationale and trade-offs
├── 📄 requirements.txt               # Production dependencies
├── 📄 Dockerfile                     # Container definition
├── 📄 pyproject.toml                 # Poetry configuration
└── 📄 README.md                      # This file
```

---

## User Workflow

**Simple 6-step process:** Upload photo → Review metadata → Get weather context → AI analysis → Add annotations → Save to knowledge base

*See data flow diagram above for detailed processing pipeline.*

---

## Quick Start

```bash
git clone https://github.com/dagny099/beehive-tracker.git && cd beehive-tracker
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
streamlit run run_tracker.py
```

**For detailed deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive setup, Docker configuration, and cloud deployment guide.

---

## Development Approach

### Implementation Strategy
**Phase 1**: Core timeline and metadata extraction (✅ Complete)  
**Phase 2**: Weather API integration and visualization enhancement (✅ Complete)  
**Phase 3**: Computer vision analysis for hive health monitoring (✅ Complete)  
**Phase 4**: Storage abstraction and cloud optimization (🔄 Current)

### Quality Assurance
- **Test-Driven Development**: Pytest suite with fixtures and mocks
- **Continuous Integration**: Automated testing on core processing modules  
- **Performance Monitoring**: API rate limiting and response time optimization
- **User Experience Testing**: Streamlit session state validation

---

## Technical Documentation

For comprehensive implementation details:
- **[📋 Portfolio Showcase](notebooks/03_portfolio_showcase.ipynb)** - Interactive technical walkthrough
- **[🏗️ DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide  
- **[⚙️ TECHNICAL_DECISIONS.md](TECHNICAL_DECISIONS.md)** - Architecture rationale and trade-offs
- **[📊 DEVELOPMENT.md](DEVELOPMENT.md)** - Architecture decisions and testing strategy
- **[🔧 DOCUMENTATION_AND_TESTING_PLAN.md](DOCUMENTATION_AND_TESTING_PLAN.md)** - Development roadmap

---

## Author & License

**Barbara** - Beekeeper, Data Scientist, and Certified Data Management Professional (CDMP)

Licensed under MIT License - see [LICENSE](LICENSE.md) for details.

---

*This project demonstrates production-ready data engineering applied to agricultural technology, showcasing end-to-end system design from computer vision integration to scalable deployment.*