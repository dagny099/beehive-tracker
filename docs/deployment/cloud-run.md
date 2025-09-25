# Google Cloud Run Deployment

This guide covers deploying the Beehive Photo Metadata Tracker to Google Cloud Run for production use.

!!! warning "🔴 Critical Gap - TODO"
    **This deployment guide needs complete step-by-step instructions including:**
    - Screenshots of Google Cloud Console setup process
    - Complete gcloud CLI command sequences
    - Environment variable configuration for production
    - Domain setup and SSL certificate management
    - Monitoring and logging configuration

## Overview

Google Cloud Run provides serverless, scalable hosting for the Beehive Tracker with automatic HTTPS, monitoring, and pay-per-use pricing.

### Prerequisites

- Google Cloud account with billing enabled
- Google Cloud SDK (gcloud CLI) installed locally
- Docker installed for building container images
- Project with necessary APIs enabled

## Quick Deployment

### Automated Script

The project includes a deployment script for streamlined deployment:

```bash
# Set required environment variables
export PROJECT_ID=your-gcp-project-id
export GCP_REGION=us-central1

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment Steps

1. **Configure gcloud CLI**:
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
gcloud auth configure-docker
```

2. **Build and push container image**:
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/beehive-tracker .
docker push gcr.io/YOUR_PROJECT_ID/beehive-tracker
```

3. **Deploy to Cloud Run**:
```bash
gcloud run deploy beehive-tracker \
  --image gcr.io/YOUR_PROJECT_ID/beehive-tracker \
  --port 8080 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production
```

## Environment Configuration

### Production Environment Variables

```bash
# Set production configuration
gcloud run services update beehive-tracker \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars LOG_LEVEL=INFO \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
```

### Service Configuration

```bash
# Configure service limits and scaling
gcloud run services update beehive-tracker \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10 \
  --min-instances 1
```

## Domain and SSL Setup

### Custom Domain Mapping

```bash
# Map custom domain to service
gcloud run domain-mappings create \
  --service beehive-tracker \
  --domain your-domain.com \
  --region us-central1
```

SSL certificates are automatically managed by Google Cloud Run.

## Monitoring and Logging

### Cloud Logging

```bash
# View application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=beehive-tracker" \
  --limit 50 \
  --format="table(timestamp,severity,textPayload)"
```

### Cloud Monitoring

Set up monitoring alerts through Google Cloud Console:
- CPU utilization alerts
- Memory usage monitoring
- Request latency tracking
- Error rate monitoring

## Security Best Practices

### IAM and Permissions

- Use least-privilege service accounts
- Enable Cloud Security Command Center
- Configure VPC connector if needed
- Set up proper firewall rules

### Data Security

- Enable encryption at rest
- Use Google Secret Manager for sensitive data
- Configure proper CORS settings
- Implement rate limiting

---

!!! info "🔴 Critical Gap - TODO"
    **Missing deployment content that needs to be added:**
    - Complete screenshot walkthrough of Cloud Console setup
    - Environment-specific configuration examples
    - Troubleshooting common deployment issues
    - Cost optimization and scaling recommendations
    - CI/CD pipeline integration examples
    - Backup and disaster recovery procedures