"""
Bulk Import Page for Beehive Tracker

This page provides a 4-step wizard for importing multiple photos from:
- AWS S3 buckets
- Local directories
- URL lists

The wizard handles source configuration, photo discovery, processing, and integration.
"""

import streamlit as st
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
import uuid
import time

# Add bulk_import to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import bulk import components
from bulk_import.s3_bulk_importer import create_s3_bulk_importer
from bulk_import.local_bulk_importer import create_local_bulk_importer
from bulk_import.url_bulk_importer import create_url_bulk_importer


def _format_resolution(exif_data: Dict[str, Any]) -> str:
    """
    Build a "WIDTHxHEIGHT" string from extracted EXIF.

    BulkImportTemplate._extract_exif_data fills ImageWidth/ImageHeight from the
    decoded image when the tags are missing, so this is usually available. The
    bulk path previously hard-coded 'Unknown' with a "Phase 4" comment.
    """
    if not exif_data:
        return 'Unknown'

    width = exif_data.get('ImageWidth') or exif_data.get('ExifImageWidth')
    height = exif_data.get('ImageHeight') or exif_data.get('ExifImageHeight')

    try:
        if width and height:
            return f"{int(width)}x{int(height)}"
    except (TypeError, ValueError):
        pass

    return 'Unknown'


def initialize_bulk_import_state():
    """Initialize session state for bulk import workflow"""
    if 'bulk_import_state' not in st.session_state:
        st.session_state.bulk_import_state = {
            'step': 1,  # 1=config, 2=preview, 3=processing, 4=complete
            'source_type': None,  # 's3', 'local', 'url'
            'source_config': {},  # Credentials, paths, etc
            'discovered_photos': [],
            'grouped_inspections': [],
            'processing_progress': {
                'total_photos': 0,
                'stage1_complete': 0,  # Discovery
                'stage2_complete': 0,  # Basic metadata
                'stage3_complete': 0,  # Vision analysis
                'stage4_complete': 0   # Weather integration
            },
            'created_inspections': [],
            'error_log': [],
            'import_id': None,  # Unique identifier for this import
            'start_time': None,
            'completion_time': None,
            'processing_active': False
        }

def render_step_header(current_step: int):
    """Render the step progress indicator"""
    steps = [
        "📂 Source Configuration",
        "🔍 Preview & Group",
        "⚡ Processing",
        "✅ Complete"
    ]

    # Create columns for each step
    cols = st.columns(4)

    for i, (col, step_name) in enumerate(zip(cols, steps), 1):
        with col:
            if i == current_step:
                st.markdown(f"**🔵 Step {i}**")
                st.markdown(f"**{step_name}**")
            elif i < current_step:
                st.markdown(f"✅ Step {i}")
                st.markdown(f"{step_name}")
            else:
                st.markdown(f"⚪ Step {i}")
                st.markdown(f"{step_name}")

    st.markdown("---")

def render_source_configuration():
    """Step 1: Source Configuration"""
    st.header("🔄 Bulk Import - Step 1: Choose Source")

    # Add helpful guidance
    st.markdown("""
    Welcome to the bulk import wizard! This will help you import multiple hive photos at once
    and automatically organize them by date into inspections.
    """)

    st.info("💡 **Tip**: Start with a small batch (10-20 photos) to test the import process before processing larger collections.")

    source_type = st.radio(
        "Select Import Source:",
        options=["local", "s3", "url"],
        format_func=lambda x: {
            "local": "📁 Local Directory - Photos stored on your computer or network drive",
            "s3": "☁️ AWS S3 Bucket - Photos in Amazon cloud storage with metadata",
            "url": "🔗 Photo URLs - Individual image links from web or cloud sources"
        }[x],
        key="source_type_selector",
        help="Choose the option that matches where your hive photos are currently stored."
    )

    st.session_state.bulk_import_state['source_type'] = source_type

    if source_type == "s3":
        render_s3_configuration()
    elif source_type == "local":
        render_local_configuration()
    elif source_type == "url":
        render_url_configuration()

def render_s3_configuration():
    """S3 configuration form"""
    st.subheader("🗂️ AWS S3 Configuration")

    # Add helpful information
    with st.expander("ℹ️ S3 Setup Help"):
        st.markdown("""
        **Prerequisites:**
        - AWS account with S3 access
        - Bucket with photos you want to import
        - Access keys with S3 read permissions

        **Security Note:**
        - Your credentials are only used for this session
        - They are not stored permanently
        """)

    with st.form("s3_config_form"):
        bucket_name = st.text_input(
            "Bucket Name",
            placeholder="beehive-photos-2024",
            help="The name of your S3 bucket"
        )

        region = st.selectbox(
            "Region",
            options=[
                "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                "eu-west-1", "eu-west-2", "eu-central-1", "ap-southeast-1"
            ],
            help="The AWS region where your bucket is located"
        )

        col1, col2 = st.columns(2)
        with col1:
            access_key = st.text_input(
                "Access Key ID",
                type="password",
                help="Your AWS access key ID"
            )
        with col2:
            secret_key = st.text_input(
                "Secret Access Key",
                type="password",
                help="Your AWS secret access key"
            )

        prefix_filter = st.text_input(
            "Path Prefix (optional)",
            placeholder="hive-photos/",
            help="Filter to specific folder within bucket"
        )

        test_connection = st.form_submit_button("🔍 Test Connection")

    # Handle form submission outside the form context
    if test_connection:
        # Validate input fields
        validation_errors = []

        if not bucket_name:
            validation_errors.append("Bucket name is required")
        elif not bucket_name.replace('-', '').replace('.', '').isalnum():
            validation_errors.append("Bucket name contains invalid characters")

        if not access_key:
            validation_errors.append("Access Key ID is required")
        elif len(access_key) < 16:
            validation_errors.append("Access Key ID seems too short")

        if not secret_key:
            validation_errors.append("Secret Access Key is required")
        elif len(secret_key) < 20:
            validation_errors.append("Secret Access Key seems too short")

        if validation_errors:
            for error in validation_errors:
                st.error(f"❌ {error}")
        else:
            config = {
                'bucket_name': bucket_name,
                'region': region,
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key,
                'prefix_filter': prefix_filter
            }

            with st.spinner("Testing S3 connection..."):
                try:
                    # Test the connection
                    importer = create_s3_bulk_importer(**config)
                    if importer.validate_source():
                        photos = importer.list_available_photos()
                        if len(photos) == 0:
                            st.warning("⚠️ Connected to bucket but no photos found. Check your prefix filter or upload some photos.")
                        else:
                            st.success(f"✅ Connected! Found {len(photos)} photos in bucket")
                            st.session_state.bulk_import_state['source_config'] = config
                            st.session_state.bulk_import_state['discovered_photos'] = photos
                    else:
                        st.error("❌ Connection failed - check your credentials and bucket name")

                except ImportError:
                    st.error("❌ boto3 library not available. Please install it first: `pip install boto3`")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "nosuchbucket" in error_msg:
                        st.error(f"❌ Bucket '{bucket_name}' does not exist or you don't have access to it")
                    elif "invalidaccesskeyid" in error_msg:
                        st.error("❌ Invalid Access Key ID. Please check your credentials")
                    elif "signaturemismatch" in error_msg:
                        st.error("❌ Invalid Secret Access Key. Please check your credentials")
                    elif "access denied" in error_msg:
                        st.error("❌ Access denied. Please check your S3 permissions")
                    else:
                        st.error(f"❌ Connection error: {str(e)}")
                        with st.expander("Technical Details"):
                            st.code(str(e))

    # Continue button outside form - only show if we have valid configuration
    if (st.session_state.bulk_import_state.get('source_config') and
        st.session_state.bulk_import_state.get('discovered_photos')):
        if st.button("Continue to Preview", type="primary", key="s3_continue"):
            st.session_state.bulk_import_state['step'] = 2
            st.rerun()

def render_local_configuration():
    """Local directory configuration"""
    st.subheader("📁 Local Directory Configuration")

    # Add helpful information
    with st.expander("ℹ️ Directory Selection Help"):
        st.markdown("""
        **Supported Image Formats:**
        - JPEG (.jpg, .jpeg)
        - PNG (.png)
        - TIFF (.tif, .tiff)
        - BMP (.bmp)

        **Tips:**
        - Use full absolute paths (e.g., `/Users/username/Pictures/beehive-photos`)
        - Enable "Include subdirectories" to scan nested folders
        - Adjust max depth to control how deep to search
        """)

    # Show current directory for reference
    current_dir = os.getcwd()
    st.info(f"💡 Current directory: `{current_dir}`")

    with st.form("local_config_form"):
        directory_path = st.text_input(
            "Directory Path",
            placeholder="/path/to/photos",
            help="Full path to the directory containing photos"
        )

        col1, col2 = st.columns(2)
        with col1:
            recursive = st.checkbox("Include subdirectories", value=True)
        with col2:
            max_depth = st.number_input("Max depth", min_value=1, max_value=10, value=5)

        test_directory = st.form_submit_button("🔍 Test Directory")

    # Handle form submission outside the form context
    if test_directory:
        # Validate directory path
        validation_errors = []

        if not directory_path:
            validation_errors.append("Directory path is required")
        elif not os.path.exists(directory_path):
            validation_errors.append(f"Directory '{directory_path}' does not exist")
        elif not os.path.isdir(directory_path):
            validation_errors.append(f"'{directory_path}' is not a directory")
        else:
            # Check if directory is readable
            try:
                os.listdir(directory_path)
            except PermissionError:
                validation_errors.append(f"Permission denied: Cannot read directory '{directory_path}'")

        if validation_errors:
            for error in validation_errors:
                st.error(f"❌ {error}")
        else:
            config = {
                'base_path': directory_path,
                'recursive': recursive,
                'max_depth': max_depth
            }

            with st.spinner("Scanning directory for photos..."):
                try:
                    importer = create_local_bulk_importer(**config)
                    if importer.validate_source():
                        photos = importer.discover_photos()
                        if len(photos) == 0:
                            st.warning("⚠️ Directory is accessible but no supported image files found")
                            st.info("Supported formats: .jpg, .jpeg, .png, .tiff, .bmp")

                            # Show directory contents for debugging
                            try:
                                all_files = os.listdir(directory_path)[:10]  # Show first 10 files
                                if all_files:
                                    st.expander("🔍 First 10 files in directory:").write(all_files)
                            except:
                                pass
                        else:
                            st.success(f"✅ Directory valid! Found {len(photos)} photos")

                            # Show sample file names for confidence
                            sample_files = photos[:5]  # Show first 5 files
                            if sample_files:
                                with st.expander("📁 Sample files found:"):
                                    for file_path in sample_files:
                                        st.write(f"• {os.path.basename(file_path)}")
                                    if len(photos) > 5:
                                        st.write(f"... and {len(photos) - 5} more files")

                            st.session_state.bulk_import_state['source_config'] = config
                            st.session_state.bulk_import_state['discovered_photos'] = photos

                            # Show sample of found files
                            with st.expander("📋 Preview of discovered photos"):
                                for i, photo in enumerate(photos[:10]):  # Show first 10
                                    st.write(f"• {os.path.basename(photo)}")
                                if len(photos) > 10:
                                    st.write(f"... and {len(photos) - 10} more")
                    else:
                        st.error("❌ Directory validation failed")

                except Exception as e:
                    st.error(f"❌ Directory scanning error: {str(e)}")
                    with st.expander("Technical Details"):
                        st.code(str(e))

    # Continue button outside form - only show if we have valid configuration
    if (st.session_state.bulk_import_state.get('source_config') and
        st.session_state.bulk_import_state.get('discovered_photos')):
        if st.button("Continue to Preview", type="primary", key="local_continue"):
            st.session_state.bulk_import_state['step'] = 2
            st.rerun()

def render_url_configuration():
    """URL list configuration"""
    st.subheader("🌐 URL List Configuration")

    # Add helpful information
    with st.expander("ℹ️ URL Import Help"):
        st.markdown("""
        **Supported URL Types:**
        - Direct image links (https://example.com/photo.jpg)
        - HTTP and HTTPS protocols
        - Common image formats: JPG, PNG, WebP

        **Requirements:**
        - URLs must be publicly accessible
        - Images should be direct links (not web pages)
        - Consider rate limiting for large imports

        **Example URLs:**
        ```
        https://example.com/photos/hive1.jpg
        https://website.com/images/inspection-2024.png
        ```
        """)

    # Security warning
    st.warning("⚠️ Only import from trusted sources. Malicious URLs could expose your IP address.")

    with st.form("url_config_form"):
        url_input_method = st.radio(
            "Input Method:",
            options=["text", "file"],
            format_func=lambda x: "Text Area" if x == "text" else "Upload File"
        )

        urls = []
        if url_input_method == "text":
            url_text = st.text_area(
                "URLs (one per line)",
                height=150,
                placeholder="https://example.com/photo1.jpg\nhttps://example.com/photo2.jpg"
            )
            urls = [url.strip() for url in url_text.split('\n') if url.strip()]
        else:
            uploaded_file = st.file_uploader("Upload URL list", type=['txt'])
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                urls = [url.strip() for url in content.split('\n') if url.strip()]

        timeout = st.number_input("Request timeout (seconds)", min_value=5, max_value=60, value=30)

        test_urls = st.form_submit_button("🔍 Test URLs")

    # Handle form submission outside the form context
    if test_urls:
        # Validate URLs
        validation_errors = []
        valid_urls = []

        if not urls:
            validation_errors.append("At least one URL is required")
        else:
            # Validate each URL
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)

            for i, url in enumerate(urls):
                url = url.strip()
                if not url:
                    continue

                if not url_pattern.match(url):
                    validation_errors.append(f"Invalid URL format (line {i+1}): {url[:50]}...")
                elif not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff', '.bmp']):
                    validation_errors.append(f"URL doesn't appear to be an image (line {i+1}): {url[:50]}...")
                else:
                    valid_urls.append(url)

            if len(valid_urls) == 0 and len(validation_errors) == 0:
                validation_errors.append("No valid URLs found")

        if validation_errors:
            for error in validation_errors:
                st.error(f"❌ {error}")
            if valid_urls:
                st.info(f"ℹ️ Found {len(valid_urls)} valid URLs out of {len(urls)} provided")
        else:
            config = {
                'urls': valid_urls,
                'timeout': timeout
            }

            with st.spinner(f"Testing {len(valid_urls)} URLs..."):
                try:
                    importer = create_url_bulk_importer(**config)
                    if importer.validate_source():
                        st.success(f"✅ URLs validated! {len(valid_urls)} photos ready for import")
                        st.session_state.bulk_import_state['source_config'] = config
                        st.session_state.bulk_import_state['discovered_photos'] = valid_urls

                        # Show sample URLs
                        with st.expander("📋 Preview of URLs to import"):
                            for i, url in enumerate(valid_urls[:10]):  # Show first 10
                                st.write(f"• {url}")
                            if len(valid_urls) > 10:
                                st.write(f"... and {len(valid_urls) - 10} more")
                    else:
                        st.error("❌ URL validation failed - some URLs may not be accessible")

                except Exception as e:
                    st.error(f"❌ URL validation error: {str(e)}")
                    with st.expander("Technical Details"):
                        st.code(str(e))

    # Continue button outside form - only show if we have valid configuration
    if (st.session_state.bulk_import_state.get('source_config') and
        st.session_state.bulk_import_state.get('discovered_photos')):
        if st.button("Continue to Preview", type="primary", key="url_continue"):
            st.session_state.bulk_import_state['step'] = 2
            st.rerun()

def render_preview_and_grouping():
    """Step 2: Preview and Grouping"""
    st.header("🔍 Bulk Import - Step 2: Preview & Group")

    discovered_photos = st.session_state.bulk_import_state['discovered_photos']
    source_type = st.session_state.bulk_import_state['source_type']

    # Enhanced source summary
    source_icons = {'local': '📁', 's3': '☁️', 'url': '🌐'}
    source_names = {'local': 'Local Directory', 's3': 'AWS S3 Bucket', 'url': 'URL List'}

    st.success(f"{source_icons[source_type]} Found **{len(discovered_photos)} photos** from {source_names[source_type]}")

    # Show more detailed preview based on source type
    if source_type == 'local':
        config = st.session_state.bulk_import_state['source_config']
        st.info(f"📂 Source: `{config['base_path']}` {'(recursive)' if config.get('recursive') else '(non-recursive)'}")
    elif source_type == 's3':
        config = st.session_state.bulk_import_state['source_config']
        bucket_info = f"s3://{config['bucket_name']}"
        if config.get('prefix_filter'):
            bucket_info += f"/{config['prefix_filter']}"
        st.info(f"🗂️ Source: `{bucket_info}` in {config['region']}")
    elif source_type == 'url':
        st.info(f"🔗 Source: {len(discovered_photos)} URLs from various domains")

    # Grouping strategy selection
    grouping_strategy = st.selectbox(
        "Group photos by:",
        options=["date", "location", "manual"],
        format_func=lambda x: {
            "date": "📅 Date (recommended)",
            "location": "📍 GPS Location",
            "manual": "✋ Manual Selection"
        }[x]
    )

    # Processing level selection
    st.subheader("⚙️ Processing Options")

    # Create columns for better layout
    option_col, estimate_col = st.columns([2, 1])

    with option_col:
        processing_level = st.radio(
            "Choose analysis level:",
            options=["quick", "standard", "full"],
            format_func=lambda x: {
                "quick": "⚡ Quick Import - Basic metadata only",
                "standard": "🔍 Standard Import - + Vision analysis sampling",
                "full": "🔬 Full Analysis - Complete photo analysis"
            }[x],
            help="Higher levels provide more detailed analysis but take longer and may cost money"
        )

    with estimate_col:
        # Calculate estimates based on selection
        photo_count = len(discovered_photos)

        if processing_level == "quick":
            time_estimate = "< 1 minute"
            cost_estimate = "Free"
            api_calls = 0
        elif processing_level == "standard":
            # Sample ~10% of photos for vision analysis
            sample_size = max(1, photo_count // 10)
            time_estimate = f"~{sample_size // 5 + 1} minutes"
            cost_estimate = f"~${sample_size * 0.0015:.3f}"
            api_calls = sample_size
        else:  # full
            time_estimate = f"~{photo_count // 10 + 1} minutes"
            cost_estimate = f"~${photo_count * 0.0015:.2f}"
            api_calls = photo_count

        # Display estimates in a nice format
        st.metric("⏱️ Time Estimate", time_estimate)
        st.metric("💰 Cost Estimate", cost_estimate)
        if api_calls > 0:
            st.metric("🔍 API Calls", f"{api_calls:,}")

    # Add processing level explanations
    with st.expander(f"ℹ️ What happens in {processing_level.title()} Import?"):
        if processing_level == "quick":
            st.markdown("""
            **Included:**
            - ✅ File metadata extraction (name, size, date)
            - ✅ Basic EXIF data (camera, GPS if available)
            - ✅ Photo grouping by date
            - ✅ Integration with timeline

            **Not included:**
            - ❌ Computer vision analysis
            - ❌ Weather data integration
            - ❌ Color analysis
            """)
        elif processing_level == "standard":
            st.markdown(f"""
            **Included:**
            - ✅ Everything from Quick Import
            - ✅ Vision analysis on ~{max(1, photo_count // 10)} sample photos
            - ✅ Basic weather data for unique locations/dates
            - ✅ Representative analysis across your collection

            **Note:** Samples are distributed across different days for coverage
            """)
        else:  # full
            st.markdown("""
            **Included:**
            - ✅ Everything from Standard Import
            - ✅ Computer vision analysis on ALL photos
            - ✅ Complete weather data integration
            - ✅ Full color analysis
            - ✅ Maximum detail and insights

            **Best for:** Small collections or when you need complete analysis
            """)

    # Warning for large imports
    if photo_count > 100 and processing_level == "full":
        st.warning(f"⚠️ Full analysis of {photo_count} photos will take significant time and may incur API costs. Consider Standard Import for large collections.")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Source", type="secondary"):
            st.session_state.bulk_import_state['step'] = 1
            st.rerun()

    with col2:
        if st.button(f"Start Import: {len(discovered_photos)} photos", type="primary"):
            # Store processing configuration
            st.session_state.bulk_import_state.update({
                'grouping_strategy': grouping_strategy,
                'processing_level': processing_level,
                'step': 3,
                'import_id': str(uuid.uuid4()),
                'start_time': datetime.now(),
                'processing_active': True
            })
            st.rerun()

def render_processing():
    """Step 3: Processing Pipeline"""
    st.header("⚡ Bulk Import - Step 3: Processing")

    import_state = st.session_state.bulk_import_state

    if not import_state.get('processing_started'):
        st.info("🔄 Starting bulk import processing...")

        # Do REAL processing for all import types
        if import_state['source_type'] in ['local', 's3', 'url']:
            try:
                # Create the appropriate bulk importer
                if import_state['source_type'] == 'local':
                    from bulk_import.local_bulk_importer import create_local_bulk_importer
                    importer = create_local_bulk_importer(**import_state['source_config'])
                    discovered_photos = import_state['discovered_photos']
                elif import_state['source_type'] == 's3':
                    from bulk_import.s3_bulk_importer import create_s3_bulk_importer
                    importer = create_s3_bulk_importer(**import_state['source_config'])
                    discovered_photos = import_state['discovered_photos']
                elif import_state['source_type'] == 'url':
                    from bulk_import.url_bulk_importer import create_url_bulk_importer
                    importer = create_url_bulk_importer(**import_state['source_config'])
                    discovered_photos = import_state['discovered_photos']

                # Process each photo and extract metadata
                processed_photos = []
                failed_photos = []

                # Enhanced progress tracking
                progress_container = st.container()
                with progress_container:
                    st.markdown("### 📊 Processing Progress")

                    # Overall progress
                    overall_progress = st.progress(0, text="Starting photo processing...")

                    # Stats columns
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    processed_metric = stat_col1.metric("✅ Processed", "0", f"of {len(discovered_photos)}")
                    failed_metric = stat_col2.metric("❌ Failed", "0", "errors")
                    current_metric = stat_col3.metric("🔄 Current", "Initializing...", "")

                    # Processing loop with enhanced timing
                    start_time = time.time()
                    for i, photo_identifier in enumerate(discovered_photos):
                        try:
                            # Update current file being processed
                            current_name = os.path.basename(str(photo_identifier)) if import_state['source_type'] == 'local' else str(photo_identifier)[:50]
                            current_metric.metric("🔄 Current", current_name, f"Photo {i+1}")

                            # Extract metadata for this photo
                            metadata = importer.extract_photo_metadata(photo_identifier)
                            processed_photos.append(metadata)

                            # Update progress with timing
                            progress = (i + 1) / len(discovered_photos)
                            processed_metric.metric("✅ Processed", f"{i+1}", f"of {len(discovered_photos)}")

                            # Calculate and show ETA
                            elapsed_time = time.time() - start_time
                            if i > 0:  # Avoid division by zero
                                avg_time_per_photo = elapsed_time / (i + 1)
                                remaining_photos = len(discovered_photos) - (i + 1)
                                estimated_remaining = avg_time_per_photo * remaining_photos
                                eta_text = f"ETA: {int(estimated_remaining // 60)}m {int(estimated_remaining % 60)}s"
                            else:
                                eta_text = "Calculating ETA..."

                            overall_progress.progress(progress, text=f"Processing photo {i+1} of {len(discovered_photos)} • {eta_text}")

                            # Brief pause for UI updates
                            time.sleep(0.05)

                        except Exception as e:
                            failed_photos.append({'identifier': photo_identifier, 'error': str(e)})
                            failed_metric.metric("❌ Failed", f"{len(failed_photos)}", "errors")
                            st.warning(f"⚠️ Failed to process: {os.path.basename(str(photo_identifier))}")

                    # Final status update
                    current_metric.metric("🔄 Status", "Complete!", f"{len(processed_photos)} photos")
                    overall_progress.progress(1.0, text=f"✅ Completed processing {len(processed_photos)} photos")

                # Show summary of any failures
                if failed_photos:
                    with st.expander(f"⚠️ {len(failed_photos)} photos failed to process"):
                        for failed in failed_photos:
                            st.write(f"❌ {failed['identifier']}: {failed['error']}")

                # Group photos into inspections
                grouped_inspections = importer.group_into_inspections(processed_photos)

                # Convert to main app format and integrate
                from src.utils.data_handler import (
                    add_photo_to_inspection,
                    save_inspections_to_disk,
                )
                inspections_created = 0

                for group in grouped_inspections:
                    for photo_metadata in group.photos:
                        # Convert PhotoMetadata to format expected by main app
                        # Handle different path formats for different sources
                        if import_state['source_type'] == 'local':
                            file_path = photo_metadata.original_path.replace('file://', '')
                        elif import_state['source_type'] == 's3':
                            # Keep S3 paths as-is for now (s3://bucket/key format)
                            file_path = photo_metadata.original_path
                        elif import_state['source_type'] == 'url':
                            # Keep URL paths as-is (https://... format)
                            file_path = photo_metadata.original_path
                        else:
                            file_path = photo_metadata.original_path

                        photo_data = {
                            'filename': photo_metadata.filename,
                            'file_path': file_path,
                            'date_taken': photo_metadata.timestamp.strftime("%Y:%m:%d %H:%M:%S") if photo_metadata.timestamp else 'Unknown',
                            'camera_model': photo_metadata.camera_make or photo_metadata.camera_model or 'Unknown',
                            'resolution': _format_resolution(photo_metadata.exif_data),
                            'color_palette': photo_metadata.colors or [],
                            'lat': photo_metadata.gps_coordinates[0] if photo_metadata.gps_coordinates else None,
                            'lon': photo_metadata.gps_coordinates[1] if photo_metadata.gps_coordinates else None,
                            # The importers have always collected this; the bulk
                            # path used to drop it here, so nothing downstream
                            # ever saw it. data_handler and ui_components both
                            # read photo['vision_analysis'].
                            'vision_analysis': photo_metadata.vision_analysis or {},
                        }

                        # Add to main app inspections. defer_save keeps the
                        # write out of the loop; we save once below.
                        add_photo_to_inspection(photo_data, defer_save=True)
                        inspections_created += 1

                # One write for the whole import instead of one per photo.
                save_inspections_to_disk()

                # Update processing state
                import_state['processing_started'] = True
                import_state['processing_active'] = False
                import_state['completion_time'] = datetime.now()
                import_state['step'] = 4
                import_state['inspections_created'] = len(grouped_inspections)

                # Initialize and update progress tracking.
                # stage3 used to be hard-coded to 0 with the comment "No vision
                # analysis yet", which stayed true and unnoticed for ~10 months.
                # It now reports what the Vision stage actually did.
                total_photos = len(import_state['discovered_photos'])
                vision_stats = getattr(importer, 'vision_stats', {}) or {}
                import_state['vision_stats'] = dict(vision_stats)

                # Weather. Contrary to the old "No weather integration yet"
                # comment, add_photo_to_inspection already calls
                # fetch_weather_for_inspection, so the bulk path does get
                # weather via Open-Meteo whenever an inspection has GPS and a
                # date. What was missing was any accounting of it. Count the
                # inspections that actually came back with data.
                all_inspections = st.session_state.get('inspections', []) or []
                weather_ok = sum(
                    1 for insp in all_inspections
                    if isinstance(insp.get('weather_data'), dict)
                    and insp['weather_data'].get('weather_temperature_C') is not None
                )
                weather_attempted = sum(
                    1 for insp in all_inspections if insp.get('weather_fetch_attempted')
                )
                import_state['weather_stats'] = {
                    'succeeded': weather_ok,
                    'attempted': weather_attempted,
                }

                import_state['processing_progress'] = {
                    'total_photos': total_photos,
                    'stage1_complete': total_photos,
                    'stage2_complete': len(processed_photos),
                    'stage3_complete': vision_stats.get('succeeded', 0),
                    'stage4_complete': weather_ok
                }

                # Say out loud when a stage produced nothing.
                if vision_stats.get('succeeded', 0) == 0 and vision_stats.get('attempted', 0) > 0:
                    st.warning(
                        f"🔍 Vision analysis produced no results for any of "
                        f"{vision_stats['attempted']} photos. "
                        f"Reason: {vision_stats.get('last_error') or 'unknown'}. "
                        "Photos, dates, GPS and colors were still imported."
                    )
                elif vision_stats.get('skipped', 0):
                    st.info(
                        f"🔍 Vision analysis: {vision_stats.get('succeeded', 0)} of "
                        f"{vision_stats.get('attempted', 0)} photos analyzed, "
                        f"{vision_stats['skipped']} skipped. "
                        f"Last reason: {vision_stats.get('last_error') or 'unknown'}."
                    )

                # Load first photo from latest inspection for display on Dashboard
                # This ensures Inspection Overview appears after bulk import
                if st.session_state.inspections:
                    # Sort inspections by date to get the most recent
                    def get_date(insp):
                        d = insp.get('date')
                        if isinstance(d, datetime):
                            return d
                        try:
                            return datetime.fromisoformat(str(d))
                        except:
                            return datetime(2000, 1, 1)

                    sorted_inspections = sorted(st.session_state.inspections, key=get_date, reverse=True)
                    latest_inspection = sorted_inspections[0]

                    if latest_inspection.get('photos'):
                        first_photo = latest_inspection['photos'][0]
                        file_path = first_photo.get('file_path', '')

                        if file_path and os.path.exists(file_path):
                            # Load photo into session state for Dashboard display
                            from src.utils.session_manager import load_photo_into_session_state
                            try:
                                load_photo_into_session_state(first_photo, image_path=file_path)
                                # Find the index of this inspection in the original list
                                for idx, insp in enumerate(st.session_state.inspections):
                                    if insp == latest_inspection:
                                        st.session_state.selected_inspection = idx
                                        break
                            except:
                                # Silently fail - photo loading is optional
                                pass

                st.success(f"✅ Successfully processed {len(processed_photos)} photos into {len(grouped_inspections)} inspections!")
                # Don't rerun here - it would wipe out the photo we just loaded into session state
                # The page will naturally show completion state and user can click "View Timeline"

            except Exception as e:
                st.error(f"❌ Processing failed: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_completion():
    """Step 4: Completion Summary"""
    st.header("🎉 Bulk Import Complete!")

    import_state = st.session_state.bulk_import_state
    total_photos = len(import_state['discovered_photos'])
    processing_time = (import_state['completion_time'] - import_state['start_time']).total_seconds()
    source_type = import_state['source_type']
    source_icons = {'local': '📁', 's3': '☁️', 'url': '🌐'}

    # Celebratory success message
    st.balloons()
    st.success(f"{source_icons[source_type]} Successfully imported **{total_photos} photos** from {source_type.upper()} source!")

    # Per-stage honesty. A run that imported photos but analyzed none of them
    # is a partial success, and the summary should say so on the same screen
    # as the balloons rather than in a DEBUG log.
    vision_stats = import_state.get('vision_stats') or {}
    attempted = vision_stats.get('attempted', 0)
    succeeded = vision_stats.get('succeeded', 0)
    if attempted:
        if succeeded == 0:
            st.warning(
                f"🔍 **Vision analysis: 0 of {attempted} photos.** "
                f"Reason: {vision_stats.get('last_error') or 'unknown'}. "
                "Everything else on this page still imported correctly."
            )
        elif succeeded < attempted:
            st.info(
                f"🔍 Vision analysis: {succeeded} of {attempted} photos analyzed. "
                f"Last skip reason: {vision_stats.get('last_error') or 'unknown'}."
            )
        else:
            st.success(f"🔍 Vision analysis: {succeeded} of {attempted} photos analyzed.")

    weather_stats = import_state.get('weather_stats') or {}
    w_attempted = weather_stats.get('attempted', 0)
    w_ok = weather_stats.get('succeeded', 0)
    if w_attempted:
        if w_ok == 0:
            st.warning(
                f"🌤️ **Weather: 0 of {w_attempted} inspections.** Open-Meteo returned "
                "nothing usable, which usually means the photos carry no GPS "
                "coordinates or the dates fall outside the archive."
            )
        elif w_ok < w_attempted:
            st.info(f"🌤️ Weather: {w_ok} of {w_attempted} inspections enriched.")
        else:
            st.success(f"🌤️ Weather: {w_ok} of {w_attempted} inspections enriched.")

    # Enhanced summary statistics with better visuals
    st.markdown("### 📊 Import Summary")

    # Main metrics in a more prominent layout
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric(
            "📸 Photos Processed",
            f"{total_photos:,}",
            help="Total number of photos successfully processed"
        )

    with metric_col2:
        inspections_created = import_state.get('inspections_created', 0)
        st.metric(
            "📅 Inspections Created",
            f"{inspections_created:,}",
            help="Number of date-based inspection groups created"
        )

    with metric_col3:
        st.metric(
            "⏱️ Processing Time",
            f"{processing_time:.1f}s",
            help="Total time taken for import and processing"
        )

    with metric_col4:
        processing_level = import_state.get('processing_level', 'quick')
        level_icons = {'quick': '⚡', 'standard': '🔍', 'full': '🔬'}
        st.metric(
            "🎯 Analysis Level",
            f"{level_icons[processing_level]} {processing_level.title()}",
            help="Level of analysis performed on photos"
        )

    # Show source-specific details
    st.markdown("### 📋 Import Details")
    details_col1, details_col2 = st.columns(2)

    with details_col1:
        st.markdown("**Source Information:**")
        config = import_state['source_config']

        if source_type == 'local':
            st.write(f"📂 Directory: `{config['base_path']}`")
            st.write(f"🔄 Recursive: {'Yes' if config.get('recursive') else 'No'}")
            st.write(f"📏 Max Depth: {config.get('max_depth', 'N/A')}")

        elif source_type == 's3':
            st.write(f"🗂️ Bucket: `{config['bucket_name']}`")
            st.write(f"🌍 Region: {config['region']}")
            if config.get('prefix_filter'):
                st.write(f"📁 Prefix: `{config['prefix_filter']}`")

        elif source_type == 'url':
            st.write(f"🔗 URLs: {len(config['urls'])} sources")
            st.write(f"⏰ Timeout: {config['timeout']}s")

    with details_col2:
        st.markdown("**Processing Results:**")

        # Calculate processing rate
        rate = total_photos / max(processing_time, 0.1)  # Avoid division by zero
        st.write(f"🚀 Processing Rate: {rate:.1f} photos/second")

        # Show timeline integration
        total_inspections = len(st.session_state.get('inspections', []))
        st.write(f"📊 Total Inspections in App: {total_inspections}")

        # Show next steps preview
        if total_inspections > 0:
            latest_inspection = st.session_state.inspections[-1]
            if latest_inspection.get('photos'):
                st.write(f"📷 Latest Photo: {latest_inspection['photos'][0].get('filename', 'Unknown')}")

    st.markdown("---")

    # Next steps with enhanced guidance
    st.subheader("🎯 What's Next?")

    # Add helpful tips
    with st.expander("💡 Tips for exploring your imported data"):
        st.markdown("""
        **Timeline View**: See your inspections organized chronologically with weather data and trends

        **Gallery View**: Browse all photos with filtering options by date, weather conditions, or analysis results

        **Export Options**: You can export your data anytime from the Storage Management page

        **Adding More Photos**: Use this bulk import wizard again, or upload individual photos through the main dashboard
        """)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 View Timeline", type="primary", help="See your inspections on an interactive timeline"):
            # Clear the manual clear flag so imported data stays visible
            st.session_state.data_manually_cleared = False
            st.switch_page("src/app.py")

    with col2:
        if st.button("🖼️ Browse Gallery", type="secondary", help="Explore your photos with advanced filtering"):
            # Clear the manual clear flag so imported data stays visible
            st.session_state.data_manually_cleared = False
            st.switch_page("src/gallery_view.py")

    with col3:
        if st.button("🔄 Import More Photos", type="secondary"):
            # Reset for new import
            st.session_state.bulk_import_state = {
                'step': 1,
                'source_type': None,
                'source_config': {},
                'discovered_photos': [],
                'grouped_inspections': [],
                'processing_progress': {
                    'total_photos': 0,
                    'stage1_complete': 0,
                    'stage2_complete': 0,
                    'stage3_complete': 0,
                    'stage4_complete': 0
                },
                'created_inspections': [],
                'error_log': [],
                'import_id': None,
                'start_time': None,
                'completion_time': None,
                'processing_active': False
            }
            st.rerun()

def main():
    """Main bulk import page function"""
    # st.set_page_config(
    #     page_title="Bulk Import - Hive Tracker",
    #     page_icon="📤",
    #     layout="wide"
    # )

    # Initialize session state
    initialize_bulk_import_state()

    # Get current step
    current_step = st.session_state.bulk_import_state['step']

    # Render step header
    render_step_header(current_step)

    # Render appropriate step
    if current_step == 1:
        render_source_configuration()
    elif current_step == 2:
        render_preview_and_grouping()
    elif current_step == 3:
        render_processing()
    elif current_step == 4:
        render_completion()

if __name__ == "__main__":
    main()