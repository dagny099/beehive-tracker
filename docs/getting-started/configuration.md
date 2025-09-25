# Configuration Guide

This guide covers configuring the Beehive Photo Metadata Tracker for optimal performance, including essential environment setup and cloud storage options.

!!! todo "Visual Enhancement Needed"
    Add screenshots of:
    - Environment variable setup in different operating systems
    - Google Cloud Console configuration steps
    - S3 configuration interface

## Environment Variables

### Required for Core Features

Create a `.env` file in your project root directory:

```bash
# Core Application Settings
STREAMLIT_SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Google Cloud Vision API (Recommended)

For automated image analysis and bee detection:

```bash
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
```

**Setup Steps:**
1. **Create Google Cloud Project**: Visit [Google Cloud Console](https://console.cloud.google.com/)
2. **Enable Vision API**: Navigate to APIs & Services → Library → Vision API → Enable
3. **Create Service Account**: IAM & Admin → Service Accounts → Create Service Account
4. **Download Credentials**: Generate and download JSON key file
5. **Set Environment Variable**: Point `GOOGLE_APPLICATION_CREDENTIALS` to your JSON file

### Weather Integration (Optional)

For automatic weather data correlation:

```bash
# Weather API (uses Open-Meteo - no key required)
WEATHER_API_KEY=your-weather-api-key  # Optional, for premium services
```

## Cloud Storage Configuration (S3)

!!! warning "WORK IN PROGRESS -- UPDATES COMING SOON"
    Advanced S3 storage integration is being developed with one-click cloud setup wizard. Current basic S3 configuration is available.

### AWS S3 Setup

For cloud storage and data backup:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-beehive-bucket
```

**S3 Setup Process:**

1. **Create AWS Account**: Visit [AWS Console](https://aws.amazon.com/console/)
2. **Create S3 Bucket**:
   - S3 → Create bucket
   - Choose unique bucket name
   - Select region closest to you
   - Enable versioning (recommended)

3. **Create IAM User**:
   - IAM → Users → Add user
   - Select "Programmatic access"
   - Attach policy: `AmazonS3FullAccess` (or create custom policy)

4. **Configure Application**:
   - Add S3 credentials to `.env` file
   - Test connection using storage dashboard (when available)

### S3 Permissions Policy (Recommended)

For enhanced security, use this custom IAM policy instead of full S3 access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BeehiveTrackerAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-beehive-bucket",
        "arn:aws:s3:::your-beehive-bucket/*"
      ]
    }
  ]
}
```

## Application Settings

### Streamlit Configuration

Create `.streamlit/config.toml` for customized interface:

```toml
[server]
port = 8501
headless = true
enableCORS = true
enableXsrfProtection = true

[theme]
primaryColor = "#FFC300"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[browser]
gatherUsageStats = false
```

### Performance Optimization

For better performance with large photo collections:

```bash
# Performance Settings
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
IMAGE_THUMBNAIL_SIZE=300
CACHE_TIMEOUT=3600        # 1 hour
```

## Local Storage Configuration

### Data Directory Structure

Configure local storage paths:

```bash
# Local Storage Paths
DATA_DIR=./data
UPLOAD_DIR=./data/uploads
THUMBNAIL_DIR=./data/thumbnails
EXPORT_DIR=./data/exports
```

**Directory Setup:**
```bash
mkdir -p data/{uploads,thumbnails,exports,metadata}
chmod 755 data/
chmod 755 data/*
```

## Security Best Practices

### Environment Variables Security

!!! warning "Security Important"
    Never commit `.env` files to version control. Add `.env` to your `.gitignore` file.

**Secure Storage Options:**
- **Development**: Local `.env` file (not committed)
- **Production**: Environment variables set by deployment platform
- **Docker**: Use Docker secrets or environment variable injection
- **Cloud**: Use platform-specific secret management (Google Secret Manager, AWS Secrets Manager)

### API Key Rotation

**Regular Maintenance:**
- Rotate Google Cloud service account keys annually
- Monitor API usage in cloud consoles
- Set up billing alerts to catch unexpected usage
- Use least-privilege access policies

## Troubleshooting Configuration

### Common Issues

**Environment Variables Not Loading**
```bash
# Check if .env file exists and is readable
ls -la .env
cat .env  # Verify contents (be careful with sensitive data)

# Test environment loading
python -c "import os; print(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))"
```

**Google Cloud Authentication Errors**
```bash
# Verify credentials file exists and is valid JSON
cat /path/to/your/credentials.json | python -m json.tool

# Test authentication
gcloud auth activate-service-account --key-file=/path/to/credentials.json
gcloud auth list
```

**S3 Connection Issues**
```bash
# Test S3 connection using AWS CLI
aws s3 ls s3://your-bucket-name --profile your-profile
aws s3 cp test.txt s3://your-bucket-name/ --profile your-profile
```

### Verification Steps

**Test Complete Setup:**

1. **Start Application**: `streamlit run run_tracker.py`
2. **Upload Test Photo**: Verify EXIF extraction works
3. **Check Weather Data**: Confirm weather integration (if GPS available)
4. **Test AI Analysis**: Verify Google Vision API responds (if configured)
5. **Test Export**: Try JSON and CSV export functions

## Advanced Configuration

!!! info "Coming Soon"
    Advanced configuration options being developed:

    - **Multi-user Authentication**: User account management
    - **Custom Storage Backends**: Additional cloud providers
    - **API Rate Limiting**: Configurable quotas and throttling
    - **Custom Analysis Pipelines**: Configurable processing workflows
    - **Integration Webhooks**: Connect to external systems

### Future Configuration Options

**Planned Settings:**
- Custom color analysis parameters
- Configurable AI confidence thresholds
- Weather data source preferences
- Automated backup schedules
- Custom export formats and templates

---

This configuration guide covers essential setup for core application features. As cloud storage integration and advanced features are developed, this guide will be updated with new configuration options and best practices.