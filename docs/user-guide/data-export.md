# Data Export and Import Guide

This guide covers exporting your beehive inspection data for external analysis and importing existing data into the application.

!!! warning "WORK IN PROGRESS -- UPDATES COMING SOON"
    Advanced import/export features are being developed, including bulk import capabilities and enhanced export formats. Documentation will be updated as new functionality becomes available.

## Export Options

The application provides multiple export formats to suit different analysis needs:

### JSON Export

**Purpose**: Complete data preservation with full structure and relationships

**What's Included**:
- Complete inspection metadata
- Photo analysis results (EXIF, color analysis, AI results)
- Weather data correlations
- Your annotations and notes
- Session groupings and associations
- Timestamp information

**When to Use**:
- Backing up your complete dataset
- Moving data between application installations
- Preserving all metadata relationships
- Advanced analysis requiring structured data

### CSV Export

**Purpose**: Flattened data format for spreadsheet analysis and external tools

**What's Included**:
- Essential metadata in tabular format
- Date, location, weather data
- Color analysis results
- Basic photo information
- Inspection notes and ratings

**When to Use**:
- Analysis in Excel, Google Sheets, or similar tools
- Statistical analysis and graphing
- Sharing data with others who don't use the application
- Creating reports for beekeeping associations

## How Export Currently Works

### JSON Export Process

1. **Access Timeline Dashboard**: Navigate to the Timeline view
2. **Locate Export Options**: Look for "Save as JSON" or export buttons
3. **Choose Export Type**:
   - Complete dataset: All inspections and photos
   - Filtered data: Only selected date ranges or inspections
4. **Select Save Location**: Choose where to store the JSON file
5. **Confirm Export**: Verify the export completed successfully

### CSV Export Process

1. **Access Data Management**: Available through main interface or export menu
2. **Select CSV Export**: Choose the CSV export option
3. **Configure Columns**: Select which data fields to include (if option available)
4. **Download File**: Save CSV to your preferred location
5. **Verify Contents**: Open in spreadsheet software to confirm data

## Data Import Capabilities

### JSON Import

**Current Functionality**:
- Load previously exported JSON files
- Restore complete inspection sessions
- Merge with existing data (where supported)
- Maintain all metadata relationships

**Import Process**:
1. **Access Timeline Dashboard**: Go to Timeline view
2. **Find Import Option**: Look for "Load JSON" button
3. **Select File**: Browse to your saved JSON file
4. **Verify Import**: Check that data appears correctly in timeline
5. **Review Data**: Confirm all inspections and photos loaded properly

### Bulk Photo Import (Under Development)

!!! info "Coming Soon"
    Advanced import features being developed:

    - **Folder import**: Import entire directories of photos
    - **EXIF batch processing**: Process multiple files simultaneously
    - **Smart grouping**: Automatic inspection session creation
    - **Duplicate detection**: Avoid importing the same photos twice
    - **Progress tracking**: Monitor import status for large batches

## Data Structure and Formats

### JSON Data Structure

The JSON export contains hierarchical data:

```json
{
  "inspections": [
    {
      "date": "2024-03-15T10:30:00",
      "location": {"lat": 40.7128, "lng": -74.0060},
      "photos": [
        {
          "filename": "hive1_spring.jpg",
          "metadata": {...},
          "analysis": {...},
          "weather": {...}
        }
      ],
      "notes": "Spring inspection - healthy hive",
      "tags": ["spring", "healthy", "inspection"]
    }
  ]
}
```

### CSV Data Structure

The CSV export flattens data into rows:

| Date | Filename | GPS_Lat | GPS_Lng | Temperature | Dominant_Color | Notes |
|------|----------|---------|---------|-------------|---------------|-------|
| 2024-03-15 | hive1.jpg | 40.7128 | -74.0060 | 15.5 | #D4A017 | Healthy |

## Best Practices for Data Management

### Regular Backup Strategy

**Export Frequency**:
- Export JSON after each inspection session
- Weekly or monthly CSV exports for analysis
- Before major application updates or changes
- When switching devices or installations

**Storage Organization**:
- Create dated backup folders
- Use descriptive filenames (e.g., "beehive_data_2024_spring.json")
- Store backups in multiple locations (local + cloud)
- Document export dates and contents

### Data Sharing and Collaboration

**Sharing with Others**:
- CSV format for non-technical users
- JSON format for other application users
- Include documentation explaining data structure
- Consider privacy implications of location data

**Version Control**:
- Keep track of data export versions
- Note any manual edits made to exported files
- Document source and processing dates
- Maintain change logs for important datasets

## Working with Exported Data

### Excel/Spreadsheet Analysis

**CSV Data Tips**:
- Date columns may need formatting adjustment
- GPS coordinates can be used with mapping tools
- Color data is in hex format (#RRGGBB)
- Weather data uses metric units (Celsius, mm, km/h)

**Common Analyses**:
- Seasonal trends in hive conditions
- Weather correlations with inspection findings
- Color analysis patterns over time
- Inspection frequency and timing patterns

### External Tool Integration

**GIS Mapping**:
- Use GPS coordinates for location mapping
- Overlay weather data on maps
- Visualize apiary locations and conditions

**Statistical Software**:
- Import CSV into R, Python pandas, or SPSS
- Perform correlation analyses
- Create advanced visualizations
- Build predictive models

## Troubleshooting Export/Import Issues

### Common Export Problems

**Export File Not Created**:
- Check file permissions in target directory
- Verify sufficient disk space
- Try different export location
- Check browser download settings

**Incomplete Data in Export**:
- Ensure all photos have finished processing
- Wait for weather data to load completely
- Verify AI analysis has completed (if enabled)
- Check session state before exporting

### Common Import Problems

**JSON Import Fails**:
- Verify JSON file structure is valid
- Check file wasn't corrupted during transfer
- Ensure file size isn't too large for browser
- Try importing smaller datasets

**Missing Data After Import**:
- Confirm import process completed successfully
- Check that data appears in all relevant views
- Verify photo files are accessible
- Reload application if data doesn't appear

### Performance Considerations

**Large Dataset Handling**:
- JSON exports of many inspections can be large
- Consider exporting date ranges rather than complete history
- Allow extra time for large imports to complete
- Monitor browser memory usage during operations

---

This guide covers current export and import capabilities. As bulk upload and advanced data management features are developed, this documentation will be expanded to include new functionality and best practices.