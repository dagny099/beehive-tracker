# 🐝 Beehive Tracker - Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the Beehive Photo Metadata Tracker application from local development to production on Google Cloud Platform.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Containerization](#docker-containerization)
- [Google Cloud Platform Setup](#google-cloud-platform-setup)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Python 3.11+** (recommended: 3.11.x for compatibility)
- **Docker Desktop** (latest stable version)
- **Google Cloud SDK** (`gcloud` CLI)
- **Git** for version control

### Required Accounts & Services
- **Google Cloud Platform account** with billing enabled
- **Google Cloud Vision API** enabled
- **Container Registry API** enabled
- **Cloud Run API** enabled

### Recommended Tools
- **Poetry** (for dependency management)
- **VS Code** or **PyCharm** (with Python extensions)

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/dagny099/beehive-tracker.git
cd beehive-tracker
```

### 2. Environment Setup

#### Option A: Using Poetry (Recommended)
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### Option B: Using pip + venv
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables:**
```bash
# .env file contents
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
STREAMLIT_SECRET_KEY=your-secret-key-here
WEATHER_API_KEY=your-weather-api-key  # Optional: for weather integration
```

### 4. Google Cloud Service Account Setup

#### Create Service Account
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create service account
gcloud iam service-accounts create beehive-tracker-sa \
    --description="Service account for Beehive Tracker app" \
    --display-name="Beehive Tracker"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:beehive-tracker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/vision.admin"

# Create and download key
gcloud iam service-accounts keys create ./key.json \
    --iam-account=beehive-tracker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 5. Enable Required APIs
```bash
# Enable necessary Google Cloud APIs
gcloud services enable vision.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
```

### 6. Test Local Setup
```bash
# Run the application locally
streamlit run run_tracker.py

# Application should be available at: http://localhost:8501
```

## Docker Containerization

### 1. Understanding the Dockerfile
The project includes a multi-stage Dockerfile optimized for production:

```dockerfile
# Current Dockerfile structure analysis
FROM python:3.11-slim    # Base image
WORKDIR /app            # Working directory
COPY requirements.txt   # Dependencies first (for layer caching)
RUN pip install -r requirements.txt
COPY . .               # Application code
EXPOSE 8080           # Streamlit port
CMD ["streamlit", "run", "run_tracker.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

### 2. Local Docker Build & Test
```bash
# Build Docker image
docker build -t hive-tracker-local .

# Test locally with mounted data directory
docker run -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/key.json:/app/key.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  hive-tracker-local

# Application available at: http://localhost:8080
```

### 3. Docker Optimization Tips
```dockerfile
# Recommended Dockerfile improvements (create Dockerfile.optimized)
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy and install dependencies
COPY --chown=app:app requirements.txt .
RUN pip install --user -r requirements.txt

# Copy application code
COPY --chown=app:app . .

# Set environment variables
ENV PATH="/home/app/.local/bin:${PATH}"
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/_stcore/health || exit 1

CMD ["streamlit", "run", "run_tracker.py"]
```

## Google Cloud Platform Setup

### 1. Project Configuration
```bash
# Set project and region
export PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

gcloud config set project $PROJECT_ID
gcloud config set run/region $GCP_REGION
```

### 2. Container Registry Setup
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Alternative: Use Artifact Registry (recommended for new projects)
gcloud artifacts repositories create hive-tracker \
    --repository-format=docker \
    --location=$GCP_REGION \
    --description="Beehive Tracker container repository"
```

### 3. Cloud Run Service Configuration

#### Basic Deployment
```bash
# Deploy using existing deploy.sh (enhanced version)
chmod +x deploy.sh
./deploy.sh
```

#### Manual Deployment Steps
```bash
# Build and tag image
docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/hive-tracker:latest .

# Push to registry
docker push gcr.io/$PROJECT_ID/hive-tracker:latest

# Deploy to Cloud Run
gcloud run deploy hive-tracker \
  --image gcr.io/$PROJECT_ID/hive-tracker:latest \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 900 \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars="PROJECT_ID=$PROJECT_ID"
```

## Production Deployment

### 1. Enhanced Deploy Script
Create an improved `deploy-production.sh`:

```bash
#!/bin/bash
set -e

# Configuration validation
if [[ -z "$PROJECT_ID" || -z "$GCP_REGION" ]]; then
    echo "Error: PROJECT_ID and GCP_REGION environment variables must be set"
    exit 1
fi

APP_NAME="hive-tracker"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
FULL_IMAGE_NAME="gcr.io/${PROJECT_ID}/${APP_NAME}:${IMAGE_TAG}"

echo "🚀 Starting deployment for ${APP_NAME}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${GCP_REGION}"
echo "Image: ${FULL_IMAGE_NAME}"

# Build with platform specification for Cloud Run
echo "📦 Building Docker image..."
docker build --platform linux/amd64 -t $FULL_IMAGE_NAME .
docker tag $FULL_IMAGE_NAME gcr.io/${PROJECT_ID}/${APP_NAME}:latest

# Push to registry
echo "⬆️ Pushing to Container Registry..."
gcloud auth configure-docker --quiet
docker push $FULL_IMAGE_NAME
docker push gcr.io/${PROJECT_ID}/${APP_NAME}:latest

# Deploy to Cloud Run with production settings
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $APP_NAME \
  --image gcr.io/${PROJECT_ID}/${APP_NAME}:latest \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 900 \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${GCP_REGION}" \
  --labels="app=hive-tracker,env=production"

# Get service URL
SERVICE_URL=$(gcloud run services describe $APP_NAME --region=$GCP_REGION --format='value(status.url)')

echo "✅ Deployment complete!"
echo "🌍 Application URL: $SERVICE_URL"
echo "📊 Monitor at: https://console.cloud.google.com/run/detail/$GCP_REGION/$APP_NAME"
```

### 2. Production Environment Variables
```bash
# Set production environment variables in Cloud Run
gcloud run services update hive-tracker \
  --region=$GCP_REGION \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO"
```

### 3. Custom Domain Setup (Optional)
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service hive-tracker \
  --domain your-domain.com \
  --region $GCP_REGION
```

## Environment Configuration

### 1. Environment-Specific Settings

#### Development (.env.development)
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
STREAMLIT_DEBUG=true
MAX_UPLOAD_SIZE=200MB
CACHE_TIMEOUT=3600
```

#### Production (.env.production)
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
STREAMLIT_DEBUG=false
MAX_UPLOAD_SIZE=50MB
CACHE_TIMEOUT=7200
RATE_LIMIT_ENABLED=true
```

### 2. Secret Management
```bash
# Create secrets in Google Secret Manager
echo "your-secret-key" | gcloud secrets create streamlit-secret-key --data-file=-

# Grant access to Cloud Run service
gcloud secrets add-iam-policy-binding streamlit-secret-key \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

## Monitoring & Logging

### 1. Cloud Logging Setup
```bash
# View logs
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=hive-tracker"

# Set up log-based alerts
gcloud alpha logging sinks create hive-tracker-errors \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/app_logs \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'
```

### 2. Monitoring Dashboard
```bash
# Create monitoring dashboard (monitoring.yaml)
displayName: "Beehive Tracker Dashboard"
mosaicLayout:
  tiles:
  - width: 6
    height: 4
    widget:
      title: "Request Count"
      scorecard:
        timeSeriesQuery:
          timeSeriesFilter:
            filter: 'resource.type="cloud_run_revision" resource.label.service_name="hive-tracker"'
            aggregation:
              alignmentPeriod: "60s"
              perSeriesAligner: "ALIGN_RATE"
```

### 3. Health Checks
Add to your Streamlit app (`src/health.py`):
```python
import streamlit as st
from datetime import datetime

def health_check():
    """
    Simple health check endpoint for monitoring.
    
    Returns status information including:
    - Application status
    - Database connectivity
    - External API availability
    - Resource usage
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {
            "database": "ok",
            "vision_api": "ok",
            "weather_api": "ok"
        }
    }
```

## Troubleshooting

### Common Issues & Solutions

#### 1. Container Build Failures
```bash
# Issue: Multi-platform build issues
# Solution: Specify platform explicitly
docker build --platform linux/amd64 -t your-image .

# Issue: Dependencies installation failures
# Solution: Clear Docker cache
docker system prune -a
```

#### 2. Cloud Run Deployment Issues
```bash
# Issue: Service account permissions
# Solution: Verify IAM roles
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*beehive-tracker*"

# Issue: Memory/CPU limits
# Solution: Check resource usage
gcloud run services describe hive-tracker --region=$GCP_REGION
```

#### 3. Vision API Issues
```bash
# Issue: API not enabled
gcloud services list --enabled | grep vision

# Issue: Quota exceeded
gcloud service-quotas list --service=vision.googleapis.com
```

#### 4. Application Performance Issues
```bash
# Check logs for performance issues
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=hive-tracker" \
  --format="table(timestamp,textPayload)" \
  --limit=50
```

### Debug Mode Setup
```bash
# Enable debug mode locally
export STREAMLIT_DEBUG=true
export LOG_LEVEL=DEBUG
streamlit run run_tracker.py --logger.level debug
```

### Performance Optimization
```bash
# Optimize Docker image size
# Use .dockerignore
echo "*.pyc
__pycache__
.git
.DS_Store
*.md
docs/
tests/" > .dockerignore

# Use multi-stage builds for smaller images
```

## Security Checklist

- [ ] Service account follows principle of least privilege
- [ ] Secrets stored in Google Secret Manager, not environment variables
- [ ] Container runs as non-root user
- [ ] HTTPS enforced for all connections
- [ ] Input validation implemented for file uploads
- [ ] Rate limiting configured
- [ ] Logging excludes sensitive information
- [ ] Regular security updates scheduled

## Backup & Recovery

### 1. Data Backup Strategy
```bash
# Backup uploaded images and metadata
gsutil -m cp -r gs://your-bucket/data gs://backup-bucket/$(date +%Y%m%d)
```

### 2. Disaster Recovery Plan
1. **Code Recovery**: Git repository with tagged releases
2. **Data Recovery**: Automated daily backups to Cloud Storage
3. **Service Recovery**: Infrastructure as Code with Terraform/Deployment Manager
4. **Rollback Strategy**: Blue-green deployment with traffic splitting

## CI/CD Pipeline (Optional)

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Google Cloud CLI
      uses: google-github-actions/setup-gcloud@v0
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Build and Deploy
      run: |
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/hive-tracker
        gcloud run deploy hive-tracker --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/hive-tracker --region us-central1
```

## Support & Maintenance

### Regular Maintenance Tasks
- **Weekly**: Review logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate service account keys
- **Annually**: Disaster recovery testing

### Getting Help
- **Issues**: Create GitHub issues for bugs and feature requests
- **Documentation**: Check project README and this deployment guide
- **Logs**: Use Cloud Logging for runtime issues
- **Monitoring**: Set up alerts for critical failures

---

*Last updated: $(date +%Y-%m-%d)*
*For questions or issues, contact the development team or create a GitHub issue.*