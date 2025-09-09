# Installation Guide

This guide covers multiple installation methods for the Beehive Photo Metadata Tracker. Choose the approach that best fits your needs and technical requirements.

## Local Installation

### Method 1: Using Poetry (Recommended)

[Poetry](https://python-poetry.org/) provides robust dependency management and virtual environment handling.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/dagny099/beehive-tracker.git
cd beehive-tracker
```

#### Step 2: Install Poetry
If you don't have Poetry installed:
```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### Step 3: Install Dependencies
```bash
poetry install
poetry shell  # Activate the virtual environment
```

#### Step 4: Verify Installation
```bash
streamlit run run_tracker.py
```

The application should start and be available at `http://localhost:8501`.

---

### Method 2: Using pip + venv

If you prefer traditional pip installation:

#### Step 1: Create Virtual Environment
```bash
# Clone repository
git clone https://github.com/dagny099/beehive-tracker.git
cd beehive-tracker

# Create and activate virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 3: Run Application
```bash
streamlit run run_tracker.py
```

---

## Docker Installation

Docker provides a consistent, isolated environment regardless of your host system.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running

### Step 1: Clone and Build
```bash
git clone https://github.com/dagny099/beehive-tracker.git
cd beehive-tracker

# Build the Docker image
docker build -t hive-tracker-local .
```

### Step 2: Run Container
```bash
# Run with data persistence
docker run -p 8080:8080 -v $(pwd)/data:/app/data hive-tracker-local
```

The application will be available at `http://localhost:8080`.

### Docker Compose (Alternative)
For easier management, create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  beehive-tracker:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - ENVIRONMENT=production
```

Then run:
```bash
docker-compose up -d
```

---

## Google Cloud Vision API Setup

To enable computer vision analysis, you'll need to configure the Google Cloud Vision API.

!!! warning "Optional but Recommended"
    While the Vision API setup is optional, it provides significant value through automated image analysis and bee detection.

### Step 1: Create Google Cloud Project
1. Visit the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** for later use

### Step 2: Enable Vision API
```bash
# Using gcloud CLI (if installed)
gcloud services enable vision.googleapis.com --project=YOUR_PROJECT_ID
```

Or enable through the [Cloud Console](https://console.cloud.google.com/apis/library/vision.googleapis.com).

### Step 3: Create Service Account
```bash
# Create service account
gcloud iam service-accounts create beehive-tracker \
    --description="Service account for Beehive Tracker" \
    --display-name="Beehive Tracker"

# Grant Vision API permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:beehive-tracker@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/vision.annotator"

# Create and download key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=beehive-tracker@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Step 4: Set Environment Variable
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"

# Or create a .env file in the project root
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json" > .env
```

---

## Verification & Testing

### Test Basic Functionality
1. **Start the application**:
   ```bash
   streamlit run run_tracker.py
   ```

2. **Access the interface**: Open `http://localhost:8501` in your browser

3. **Upload a test image**: Use any photo to verify the upload process works

4. **Check metadata extraction**: Verify that EXIF data is displayed

### Test API Integration
1. **Upload a beehive photo**: Use an image with clear beehive content
2. **Verify Vision API**: Check if AI analysis results appear
3. **Test weather data**: Ensure weather information loads (if GPS data available)

---

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process (replace PID)
kill -9 <PID>

# Or use a different port
streamlit run run_tracker.py --server.port 8502
```

#### Missing Dependencies
```bash
# Reinstall with Poetry
poetry install --no-dev

# Or with pip
pip install -r requirements.txt --force-reinstall
```

#### Google Credentials Error
```bash
# Verify credentials file exists
ls -la /path/to/your/credentials.json

# Test credentials
gcloud auth activate-service-account --key-file=credentials.json
gcloud auth list
```

#### Docker Issues
```bash
# Clean build (remove cache)
docker build --no-cache -t hive-tracker-local .

# Check container logs
docker logs <container_id>

# Interactive debugging
docker run -it hive-tracker-local /bin/bash
```

### Performance Issues

#### Slow Image Processing
- Ensure adequate RAM (4GB+ recommended)
- Check disk space for temporary files
- Consider resizing large images before upload

#### API Rate Limits
- Monitor Google Vision API quotas in Cloud Console
- Implement request throttling if needed
- Consider caching frequent requests

### Getting Help

!!! question "Still Having Issues?"
    1. Check the [GitHub Issues](https://github.com/dagny099/beehive-tracker/issues) for similar problems
    2. Review the [deployment troubleshooting guide](../deployment/index.md#troubleshooting)  
    3. Create a new issue with:
        - Your operating system and Python version
        - Complete error messages
        - Steps to reproduce the problem

---

## Next Steps

✅ **Installation Complete!** Now you can:

1. **[Configure the application](configuration.md)** with your preferred settings
2. **[Follow the quick start guide](quick-start.md)** for your first photo upload
3. **[Explore the user interface](../user-guide/index.md)** to understand all features

*Ready to start analyzing your beehive photos? Let's move on to the [Quick Start Guide](quick-start.md)!* 🐝