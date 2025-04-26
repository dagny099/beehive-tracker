# 🐝 Hive Photo Metadata Tracker

A Streamlit application that helps beekeepers analyze and organize photos of their hives with rich metadata.

<div align="center">
  <img src="docs/app_screenshot.png" alt="Hive Tracker Screenshot" width="80%">
</div>

## Project Overview

The Hive Photo Metadata Tracker is a web application designed for beekeepers to organize, analyze, and extract insights from their hive inspection photographs. The app transforms unstructured photo collections into a structured, searchable knowledge base that enhances beekeeping management practices.

### Business Value

This solution addresses a critical need in apiculture by leveraging modern data techniques to:

- Streamline documentation of hive inspections through automated metadata extraction
- Visualize inspection timelines for better seasonal planning and hive health monitoring
- Create a searchable knowledge base that correlates visual data with environmental conditions
- Enhance decision-making by connecting weather data with inspection findings

### Key Features

- **Interactive Timeline**: Chronological visualization of inspection history
- **Calendar View**: Monthly calendar displaying inspection events
- **Photo Gallery**: Organized collection of inspection photos
- **Automated Metadata Extraction**: Dates, location, and camera information
- **Color Palette Analysis**: Identifying honeycomb health indicators
- **Weather Data Integration**: Environmental context for inspections
- **Annotation System**: Beekeeper observations and hive state tracking
- **Computer Vision Analysis**: AI-powered insights (via Google Cloud Vision API)

## Architecture

The application employs a multi-layered architecture designed for performance and extensibility:

1. **User Interface Layer**: Streamlit-based web application with interactive components
2. **Core Processing Layer**: Python-based image analysis and metadata extraction
3. **API Integration Layer**: Connections to weather services and computer vision APIs
4. **Data Storage Layer**: Flexible storage with JSON persistence

### Technology Stack

- **Frontend**: Streamlit, Plotly, Streamlit-Calendar
- **Backend**: Python (Image Processing)
- **Data Analysis**: Pandas, ColorThief, PIL
- **APIs**: Open-Meteo Weather, Google Cloud Vision
- **Storage**: File-based with JSON persistence

<div align="center">
  <img src="docs/architecture-diagram.png" alt="Architecture Diagram" width="70%">
</div>

## 🔧 Installation

### Prerequisites

- Python 3.9+
- Streamlit
- Google Cloud account (for Vision API)

### Setup

1. Clone this repository:
git clone https://github.com/yourusername/hive-tracker.git
cd hive-tracker

2. Install required dependencies:
pip install -r requirements.txt

3. Set up Google Cloud Vision API (optional but recommended):
- Create a Google Cloud account
- Create a new project in the Google Cloud Console
- Enable the Vision API for your project
- Create a service account with Vision API access
- Download the service account key (JSON file)
- Set the environment variable:
  ```
  export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-credentials.json"
  ```

4. Run the application:
streamlit run run_tracker.py

## 🚀 Usage

### Typical Workflow

1. Log in to the application
2. Upload beehive photos or load from URL
3. View automatically extracted metadata (EXIF, colors, etc.)
4. Retrieve weather data for the photo's date and location
5. Analyze images with Vision API to detect bee-related features
6. Add beekeeper annotations and observations
7. Navigate through your inspection history using the timeline or calendar
8. Browse photos in the gallery view

### Data Management

The application automatically organizes photos into inspections based on date. Photos taken on the same day are grouped together. You can:

- Export inspection data as JSON
- View inspection details on the calendar
- Browse photos by inspection in the gallery view
- Add notes and annotations to specific photos

## 🔍 Project Structure
hive-tracker/
├── run_tracker.py           # Main entry point with navigation
├── data/
│   └── uploads/             # Directory for uploaded image files
├── src/
│   ├── app3.py              # Main dashboard
│   ├── app_components.py    # Reusable UI components
│   ├── calendar_view.py     # Calendar page
│   ├── gallery_view.py      # Gallery page
│   ├── login.py             # Login page
│   ├── timeline_component.py # Timeline visualization
│   ├── default_beepic2.jpg  # Default image
│   └── utils/
│       ├── data_handler.py  # Data load/save functions
│       ├── image_processor.py # Image processing
│       └── session_manager.py # Session state management
├── docs/                    # Documentation
└── requirements.txt         # Dependencies

## 🚢 Deployment Options

The application can be deployed in several ways:

1. **Local Development**:
   - Run `streamlit run run_tracker.py` for local testing

2. **Docker Deployment**:
   - Build the Docker image: `docker build -t hive-tracker .`
   - Run the container: `docker run -p 8501:8501 hive-tracker`

3. **Cloud Deployment**:
   - Deploy to Google Cloud Run for serverless hosting
   - Deploy to Heroku using the Procfile

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙌 Author

Barbara H. - Beekeeper, Data Scientist, and Certified Data Management Professional (CDMP)

---

*This project serves as both a practical tool for beekeepers and a showcase of data management principles applied to a specialized domain.*