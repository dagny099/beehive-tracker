# 🐝 Hive Photo Metadata Tracker

A Streamlit application that helps beekeepers analyze and organize photos of their hives with rich metadata.

![Beehive Image](default_beepic.jpg)

## 📸 Overview

The Hive Photo Metadata Tracker combines beekeeping, data management, and computer vision to turn hive photos into a structured, queryable knowledge base. As both a beekeeping tool and a data management showcase, this application extracts, analyzes, and stores comprehensive metadata about your beehive photos.

### Features

- **EXIF Metadata Extraction**: Automatically extract camera information, dates, and GPS coordinates
- **Color Palette Analysis**: Generate and display dominant colors from your hive photos
- **Weather Data Integration**: Retrieve historical weather data for when photos were taken via Open-Meteo API
- **Computer Vision Analysis**: Identify bee-related elements using Google's Vision API
- **Metadata Storage**: Save all information in both CSV and JSON formats
- **Entry Browser**: Browse, search, and load previously saved entries
- **Annotations**: Add notes and observations about hive state

## 🔧 Installation

### Prerequisites

- Python 3.9+
- Streamlit
- Google Cloud account (for Vision API)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/hive-photo-tracker.git
   cd hive-photo-tracker
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Cloud Vision API:
   - Create a Google Cloud account if you don't already have one
   - Create a new project in the Google Cloud Console
   - Enable the Vision API for your project
   - Create a service account with Vision API access
   - Download the service account key (JSON file)
   - Set the environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-credentials.json"
     ```

## 🚀 Usage

### Running Locally

Start the application:
```bash
streamlit run app.py
```

### Using the Deployed Version

You can access the deployed version at [hivetracker.barbhs.com](https://hivetracker.barbhs.com)

### Typical Workflow

1. Upload a beehive photo or load an existing entry
2. View automatically extracted metadata (EXIF, colors, etc.)
3. Retrieve weather data for the photo's date and location
4. Analyze the image with Vision API to detect bee-related features
5. Add your annotations and observations
6. Save the entry for future reference and analysis

## 🗂️ Data Storage Strategy

This project uses a dual-storage approach for flexibility and compatibility:

### CSV Output (`hive_color_log.csv`)

Used for flat, tabular exports. Includes fields such as:
- Filename, Date Taken, Resolution, Camera Model
- Top 5 palette colors
- Weather fields (temperature, wind speed, etc.)
- User annotations (hive state, notes)

### JSON Output (`hive_color_log.json`)

Used for structured, nested records. Includes everything in the CSV plus:
- Full weather information dictionary
- Complete Vision API analysis results
- Structured metadata for more complex queries

## 🔄 Project Structure

```
hive-photo-tracker/
├── api_services/        # API integrations
├── data/                # Data storage
├── app.py               # Main application
├── data_io.py           # Data storage operations
├── ui_components.py     # Streamlit UI elements
├── utils.py             # Core utility functions
├── requirements.txt     # Dependencies
├── Dockerfile           # Container definition
└── deploy.sh            # Deployment script
```

## 🚢 Deployment

This application can be deployed to Google Cloud Run using Docker:

1. Update the `PROJECT_ID` in `deploy.sh` with your GCP project ID
2. Make the deploy script executable:
   ```bash
   chmod +x deploy.sh
   ```
3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

## 🔍 Future Enhancements

- Enhanced search capabilities
- Data visualization and trends analysis
- Beekeeping ontology integration
- Multi-user support
- Advanced analytics on hive health

## 👩‍💻 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙌 Author

Barbara - Beekeeper, Data Scientist, and Certified Data Management Professional (CDMP)

---

*This project serves as both a practical tool for beekeepers and a showcase of data management principles applied to a specialized domain.*
