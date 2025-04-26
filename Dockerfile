# Use official Python image as base
FROM python:3.9-slim AS builder

# Set up working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Second stage - clean deployment
FROM python:3.9-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Create app directories
RUN mkdir -p /app/data /app/.streamlit /app/src /app/data/uploads /app/src/utils

# Copy streamlit config if it exists
COPY .streamlit/config.toml /app/.streamlit/ 

# Copy application code 
COPY run_tracker.py /app/
COPY src/login.py /app/src/
COPY src/calendar_view.py /app/src/
COPY src/gallery_view.py /app/src/
COPY src/app.py /app/src/
COPY src/timeline_component.py /app/src/
COPY src/app_components.py /app/src/
COPY src/utils/session_manager.py /app/src/utils
COPY src/utils/image_processor.py /app/src/utils
COPY src/utils/data_handler.py /app/src/utils
COPY src/default_beepic.jpg /app/src/ 
COPY src/default_beepic2.jpg /app/src/ 


# Copy service account key
COPY .streamlit/key.json /app/
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/key.json

# Expose port
EXPOSE 8080

# Create volume for data persistence
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Start Streamlit
CMD ["streamlit", "run", "run_tracker.py", "--server.port=8080", "--server.address=0.0.0.0"]
