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
RUN mkdir -p /app/data /app/api_services /app/.streamlit

# Copy streamlit config
COPY .streamlit/config.toml /app/.streamlit/

# Copy application code
COPY *.py /app/
COPY api_services/*.py /app/api_services/
COPY default_beepic.jpg /app/

# Copy service account key
COPY key.json /app/
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/key.json

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Start Streamlit (using just a simple, direct command)
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
