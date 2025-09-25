# Photo Upload Guide

This guide covers uploading and processing beehive inspection photos in the application.

!!! warning "WORK IN PROGRESS -- UPDATES COMING SOON"
    Bulk upload features are currently under development. This documentation will be updated as new functionality becomes available.

## Single Photo Upload

### Basic Upload Process

1. **Access the Dashboard**: Navigate to the main dashboard page
2. **Select Upload Method**: Choose from available upload options
3. **Choose Your Photo**: Click "Browse files" or drag and drop your image
4. **Wait for Processing**: The application automatically processes the image
5. **Review Results**: Check extracted metadata and analysis

### Supported File Formats

The application accepts these image formats:
- **JPEG/JPG** (recommended for photos)
- **PNG** (supports transparency)
- **TIFF** (high-quality, larger files)
- **BMP** (basic bitmap format)
- **WEBP** (modern compressed format)

### File Size Recommendations

- **Optimal size**: Under 5MB for best performance
- **Maximum size**: 10MB (larger files may process slowly)
- **Resolution**: Higher resolution provides better analysis results

## What Happens During Upload

When you upload a photo, the application automatically:

1. **Extracts EXIF metadata**:
   - Date and time taken
   - GPS coordinates (if available)
   - Camera make and model
   - Technical settings (ISO, aperture, etc.)

2. **Performs color analysis**:
   - Identifies dominant colors
   - Generates 5-color palette
   - Analyzes color distribution

3. **Fetches weather data** (if GPS available):
   - Historical weather for photo date/location
   - Temperature, humidity, precipitation
   - Cloud cover and wind conditions

4. **Runs AI analysis** (if configured):
   - Detects bees and honeycomb
   - Identifies text in images
   - Classifies image content

## Photo Organization

### Inspection Association

Photos are automatically organized into inspections based on:
- **Date proximity**: Photos taken on the same day
- **Location similarity**: Photos with matching GPS coordinates
- **Manual grouping**: You can manually assign photos to inspections

### Filename Handling

The application preserves your original filenames and displays them in the interface. For best organization:
- Use descriptive filenames (e.g., "hive1_spring_inspection_2024.jpg")
- Include dates or hive identifiers
- Avoid special characters that might cause issues

## Adding Annotations

After upload, you can enhance the automated analysis:

### Inspection Notes
- **Hive condition**: Rate overall health (1-5 scale)
- **Observations**: Add specific notes about what you observed
- **Treatments**: Record any interventions applied
- **Concerns**: Note any issues that need attention

### Tagging System
Add relevant tags such as:
- "inspection", "maintenance", "harvest"
- Season indicators: "spring", "summer", "fall", "winter"
- Condition tags: "healthy", "concerns", "treatment-needed"

## Best Practices for Photo Quality

### Camera Settings
- **Enable GPS**: Allows automatic weather data lookup
- **Set correct date/time**: Ensures proper chronological organization
- **Use good lighting**: Avoid harsh shadows or overexposure
- **Steady shots**: Keep camera stable for sharp images

### Photo Composition
- **Include context**: Show overall hive condition, not just close-ups
- **Multiple angles**: Take photos from different perspectives
- **Scale references**: Include objects that show size (hands, tools)
- **Consistent timing**: Try to photograph at similar times of day

### Environmental Considerations
- **Weather awareness**: Note weather conditions during photography
- **Lighting conditions**: Avoid backlighting or extreme contrasts
- **Safety first**: Don't compromise safety for better photos

## Bulk Upload (Under Development)

!!! info "Coming Soon"
    Bulk upload functionality is being developed to allow:

    - **Multiple file selection**: Upload entire folders of images
    - **Batch processing**: Process multiple photos simultaneously
    - **Automatic grouping**: Smart organization by date and location
    - **Progress tracking**: Monitor upload and processing status

    Check back for updates as this feature becomes available.

## Troubleshooting Upload Issues

### Common Problems

**Photo Won't Upload**
- Check file size (must be under 10MB)
- Verify supported format (JPEG, PNG, etc.)
- Try refreshing the browser page
- Clear browser cache if issues persist

**Processing Takes Too Long**
- Large files process more slowly
- Check internet connection (required for AI analysis)
- Consider resizing images before upload
- Close other browser tabs to free memory

**Missing GPS Data**
- Enable location services on your camera/phone
- Some cameras don't record GPS by default
- You can manually enter coordinates if needed
- Weather data requires GPS coordinates

**AI Analysis Not Working**
- Verify Google Cloud Vision API is configured
- Check internet connection
- Low-quality images may not process well
- API quotas may be exceeded (check Google Cloud Console)

### Getting Better Results

**For EXIF Data**:
- Use cameras or phones with GPS enabled
- Ensure date/time settings are correct
- Some editing software strips EXIF data

**For Color Analysis**:
- Good lighting produces better color extraction
- Avoid photos with extreme lighting conditions
- Multiple photos of same hive provide richer data

**For AI Analysis**:
- Clear, well-lit photos work best
- Include both close-up and wide shots
- Avoid heavily cropped images that lose context

## Data Storage and Management

### Local Storage
- Uploaded photos are stored locally in the application
- Metadata is saved in both JSON and CSV formats
- Original files are preserved unchanged

### Backup Recommendations
- Regularly export your data (see [Data Export Guide](data-export.md))
- Keep copies of original photos in separate location
- Consider cloud backup solutions for important data

---

This guide covers the current photo upload functionality. As bulk upload and additional features are developed, this documentation will be updated to reflect new capabilities.