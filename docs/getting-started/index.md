# Getting Started

Welcome to the Beehive Photo Metadata Tracker! This guide will help you get up and running quickly, whether you're setting up a local development environment or deploying to production.

## Quick Overview

The Beehive Tracker is a **Streamlit-based web application** that transforms your beehive inspection photos into structured, analyzable data. Here's what you can expect:

!!! success "What You'll Achieve"
    - Upload beehive photos and automatically extract metadata
    - View interactive timelines of your inspection history  
    - Correlate weather data with hive conditions
    - Analyze photos with computer vision AI
    - Export data for further analysis

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** (Python 3.11 recommended)
- **Git** for cloning the repository
- **Google Cloud Account** (for Vision API - optional but recommended)
- **Docker** (optional, for containerized deployment)

## Installation Options

Choose the installation method that best fits your needs:

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Local Installation**

    ---
    
    Install directly on your machine with Python and pip/poetry.
    
    **Best for**: Development, customization, full feature access
    
    [:octicons-arrow-right-24: Local Setup](installation.md#local-installation)

-   :material-docker:{ .lg .middle } **Docker Container**

    ---
    
    Run in an isolated container with all dependencies included.
    
    **Best for**: Quick testing, production deployment, consistency
    
    [:octicons-arrow-right-24: Docker Setup](installation.md#docker-installation)

-   :material-cloud:{ .lg .middle } **Cloud Deployment**

    ---
    
    Deploy to Google Cloud Run for scalable, managed hosting.
    
    **Best for**: Production use, sharing with team, reliability
    
    [:octicons-arrow-right-24: Cloud Setup](../deployment/cloud-run.md)

</div>

## Quick Start Checklist

Once you've chosen your installation method, follow these steps:

- [ ] **[Install the application](installation.md)** using your preferred method
- [ ] **[Configure environment variables](configuration.md)** (especially for Google Vision API)
- [ ] **[Run the application](quick-start.md)** and access the web interface
- [ ] **[Upload your first photo](quick-start.md#first-photo-upload)** to see the analysis in action
- [ ] **[Explore the timeline view](../user-guide/timeline-view.md)** to visualize your data

## What's Next?

After completing the basic setup:

### 🔧 **Configure Features**
Learn how to set up optional features like weather integration and computer vision analysis in the [Configuration Guide](configuration.md).

### 📖 **Learn the Interface**  
Explore all the application features in our comprehensive [User Guide](../user-guide/index.md).

### 🚀 **Deploy to Production**
When you're ready to go live, check out our [Deployment Guide](../deployment/index.md).

## Getting Help

!!! question "Need Assistance?"
    - Check the [FAQ section](../user-guide/index.md#common-questions) for common issues
    - Review the [troubleshooting guide](installation.md#troubleshooting) for installation problems
    - Visit the [GitHub repository](https://github.com/dagny099/beehive-tracker) for community support

## System Requirements

### Minimum Requirements
- **OS**: macOS, Linux, or Windows 10+
- **RAM**: 2GB available memory
- **Storage**: 1GB free disk space
- **Network**: Internet connection for API services

### Recommended Specifications  
- **OS**: macOS or Linux (for best performance)
- **RAM**: 4GB+ available memory
- **Storage**: 5GB+ free disk space (for photo storage)
- **Network**: Stable broadband connection

---

Ready to transform your beehive photo management? Let's start with the [installation process](installation.md)! 🐝