#!/bin/bash

# Local development script
# Uses port 8501 (Streamlit default) for local development

# Build the docker image
docker build -t hive-tracker-local .

# Run locally with PORT=8501
docker run -p 8501:8501 -e PORT=8501 hive-tracker-local
