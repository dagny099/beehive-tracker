# Deployment Guide

This guide covers deploying the Beehive Photo Metadata Tracker in various environments, from local development to production cloud deployment.

!!! todo "Visual Enhancement Needed"
    Add deployment architecture diagrams and step-by-step screenshots for:
    - Docker deployment workflow
    - Google Cloud Run deployment process
    - Local production setup

## Deployment Options

### Local Development
**Best for**: Testing, development, personal use
- Quick setup with minimal configuration
- All data stored locally
- Full feature access for single user

### Docker Container
**Best for**: Consistent environments, easy deployment
- Isolated environment with all dependencies
- Portable across different systems
- Simple backup and restoration

### Cloud Deployment
**Best for**: Production use, team sharing, reliability
- Scalable hosting with automatic management
- Built-in monitoring and logging
- Professional SSL certificates

## Local Development Deployment

### Quick Setup

```bash
# Clone and setup
git clone https://github.com/username/beehive-tracker.git
cd beehive-tracker

# Using Poetry (recommended)
poetry install
poetry shell
streamlit run run_tracker.py

# Using pip
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
streamlit run run_tracker.py
```

**Access**: http://localhost:8501

### Production-Ready Local Setup

For local production use with enhanced security:

```bash
# Create production environment
cp .env.example .env.production
# Edit .env.production with your settings

# Run with production settings
ENVIRONMENT=production streamlit run run_tracker.py --server.port 8080
```

## Docker Deployment

### Basic Docker Setup

```bash
# Build the image
docker build -t beehive-tracker .

# Run with data persistence
docker run -d \
  --name beehive-tracker \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  beehive-tracker
```

**Access**: http://localhost:8080

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  beehive-tracker:
    build: .
    container_name: beehive-tracker
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./.env:/app/.env
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Deploy with Docker Compose:**
```bash
docker-compose up -d
docker-compose logs -f  # View logs
docker-compose down     # Stop services
```

### Docker Best Practices

**Data Backup:**
```bash
# Backup application data
docker run --rm -v beehive_data:/data -v $(pwd):/backup ubuntu tar czf /backup/beehive-backup.tar.gz /data

# Restore data
docker run --rm -v beehive_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/beehive-backup.tar.gz -C /
```

## Cloud Deployment (Google Cloud Run)

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed locally
3. **Docker** installed for building images

### Automated Deployment Script

The project includes a deployment script for easy cloud deployment:

```bash
# Set required environment variables
export PROJECT_ID=your-gcp-project-id
export GCP_REGION=us-central1

# Make script executable and run
chmod +x deploy.sh
./deploy.sh
```

### Manual Cloud Run Deployment

```bash
# Configure gcloud
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1

# Build and push image to Google Container Registry
docker build -t gcr.io/YOUR_PROJECT_ID/beehive-tracker .
docker push gcr.io/YOUR_PROJECT_ID/beehive-tracker

# Deploy to Cloud Run
gcloud run deploy beehive-tracker \
  --image gcr.io/YOUR_PROJECT_ID/beehive-tracker \
  --port 8080 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production
```

### Cloud Run Configuration

**Environment Variables for Cloud Run:**
```bash
# Set production environment variables
gcloud run services update beehive-tracker \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
```

**Resource Allocation:**
```bash
# Configure memory and CPU
gcloud run services update beehive-tracker \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

## Environment-Specific Configuration

### Development Environment

```bash
# .env.development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
STREAMLIT_SECRET_KEY=dev-secret-key
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
STREAMLIT_SECRET_KEY=secure-production-key-here
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
```

### Cloud Environment

```bash
# Cloud-specific settings
ENVIRONMENT=cloud
LOG_LEVEL=INFO
USE_CLOUD_STORAGE=true
AWS_S3_BUCKET=your-production-bucket
```

## Monitoring and Maintenance

### Health Checks

The application includes built-in health checking:
- **Local**: http://localhost:8501/_stcore/health
- **Docker**: http://localhost:8080/_stcore/health
- **Cloud**: Automatic health checks configured

### Logging

**View Application Logs:**
```bash
# Docker logs
docker logs -f beehive-tracker

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=beehive-tracker"
```

### Backup Strategies

**Local Deployment:**
- Regular file system backups of `data/` directory
- Export JSON data periodically
- Database dumps if using external database

**Cloud Deployment:**
- Automated Cloud Storage backups
- Regular export to multiple formats
- Cross-region backup replication

## Troubleshooting Deployment

### Common Issues

**Port Conflicts**
```bash
# Check what's using port 8501/8080
lsof -i :8501
lsof -i :8080

# Use different port
streamlit run run_tracker.py --server.port 8502
```

**Memory Issues**
```bash
# Monitor memory usage
docker stats beehive-tracker

# Increase Docker memory limits
docker run --memory=2g beehive-tracker
```

**Environment Variable Issues**
```bash
# Debug environment variables in container
docker exec -it beehive-tracker env
docker exec -it beehive-tracker cat /app/.env
```

### Performance Optimization

**Production Deployment Tips:**
- Use Docker multi-stage builds for smaller images
- Enable gzip compression for static assets
- Configure appropriate memory limits
- Set up proper logging and monitoring
- Use CDN for static assets if applicable

## Security Considerations

### Production Security Checklist

- [ ] **Secure Environment Variables**: Never expose sensitive data
- [ ] **HTTPS Only**: Force secure connections in production
- [ ] **Regular Updates**: Keep base images and dependencies updated
- [ ] **Access Controls**: Implement proper authentication if needed
- [ ] **Network Security**: Configure firewalls and VPC if using cloud
- [ ] **Data Encryption**: Encrypt data at rest and in transit
- [ ] **Regular Backups**: Automated backup strategy in place

### SSL Certificate Setup

**For custom domains on Cloud Run:**
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service beehive-tracker \
  --domain your-domain.com
```

**SSL certificates are automatically managed by Google Cloud Run.**

---

This deployment guide covers the main deployment scenarios. As the application evolves and new deployment options become available, this guide will be updated with additional methods and best practices.

!!! info "🔴 Critical Gap - TODO"
    **Missing deployment content that needs to be added:**
    - Detailed AWS deployment guide
    - Kubernetes deployment configurations
    - CI/CD pipeline setup instructions
    - Database deployment options
    - Load balancer configuration examples