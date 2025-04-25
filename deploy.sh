#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# GCP configuration
PROJECT_ID="gen-lang-client-0846443908"
APP_NAME="hive-tracker"
REGION="us-central1"

# Build the Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t gcr.io/${PROJECT_ID}/${APP_NAME}:latest .

# Tag with date for versioning
DATE_TAG=$(date +%Y%m%d-%H%M)
docker tag gcr.io/${PROJECT_ID}/${APP_NAME}:latest gcr.io/${PROJECT_ID}/${APP_NAME}:${DATE_TAG}

# Verify the image was built
echo "Verifying image..."
docker images | grep ${APP_NAME}

# Push to Google Container Registry
echo "Pushing to Container Registry..."
gcloud auth configure-docker --quiet
docker push gcr.io/${PROJECT_ID}/${APP_NAME}:latest 
docker push gcr.io/${PROJECT_ID}/${APP_NAME}:${DATE_TAG}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${APP_NAME} \
  --image gcr.io/${PROJECT_ID}/${APP_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 900 \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 3

echo "Deployment complete!"
echo "Your app should be available at: https://${APP_NAME}-${PROJECT_ID}.${REGION}.run.app"
