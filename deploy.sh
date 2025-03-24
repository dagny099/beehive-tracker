#!/bin/bash

# GCP configuration
PROJECT_ID="gen-lang-client-0846443908"  # GCP project ID
APP_NAME="hive-tracker"
REGION="us-central1"  # Replace with your preferred region


# Build the Docker image
echo "Building Docker image..."
#docker build -t gcr.io/${PROJECT_ID}/${APP_NAME}:latest . || { echo "Docker build failed"; exit 1; }
docker build --platform linux/amd64 -t gcr.io/${PROJECT_ID}/${APP_NAME}:latest .

# Verify the image was built
echo "Verifying image..."
docker images | grep ${APP_NAME}

# Push to Google Container Registry
echo "Pushing to Container Registry..."
gcloud auth configure-docker
docker push gcr.io/${PROJECT_ID}/${APP_NAME}:latest || { echo "Docker push failed"; exit 1; }

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${APP_NAME} \
  --image gcr.io/${PROJECT_ID}/${APP_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 900 
#  --cpu 2 \
#  --min-instances 0 \
#  --max-instances 5 \
#  --set-env-vars STREAMLIT_SERVER_PORT=8080,STREAMLIT_SERVER_ADDRESS=0.0.0.0

echo "Deployment complete!"

