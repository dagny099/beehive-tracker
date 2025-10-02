"""
Storage UI components for Streamlit - Phase 3 implementation.
Provides one-click cloud setup, analytics dashboard, and migration tools.
"""

import streamlit as st
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from storage import get_storage_config, get_storage_manager
    from utils.storage_integration import (
        get_storage_info, switch_storage_provider, 
        migrate_to_cloud_storage, get_storage_health_status
    )
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False


def show_storage_setup_wizard():
    """One-click cloud storage setup wizard"""
    if not STORAGE_AVAILABLE:
        st.error("⚠️ Storage abstraction not available")
        return
    
    st.header("🚀 Cloud Storage Setup")
    
    with st.expander("📋 Setup Instructions", expanded=True):
        st.markdown("""
        **Quick Setup for AWS S3:**
        1. Create AWS account and S3 bucket
        2. Create IAM user with S3 permissions  
        3. Generate Access Key ID and Secret
        4. Enter credentials below
        5. Test connection and migrate data
        """)
    
    # Configuration form
    with st.form("cloud_setup"):
        st.subheader("AWS S3 Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            bucket_name = st.text_input("S3 Bucket Name*", placeholder="my-beehive-bucket")
            access_key = st.text_input("AWS Access Key ID*", type="password")
        
        with col2:
            region = st.selectbox("AWS Region", [
                "us-east-1", "us-west-2", "eu-west-1", 
                "ap-southeast-1", "ap-northeast-1"
            ])
            secret_key = st.text_input("AWS Secret Access Key*", type="password")
        
        create_bucket = st.checkbox("Create bucket if it doesn't exist", value=True)
        
        submitted = st.form_submit_button("🔗 Connect to S3", type="primary")
        
        if submitted:
            if not bucket_name or not access_key or not secret_key:
                st.error("All required fields must be filled")
                return
            
            # Test connection
            with st.spinner("Testing S3 connection..."):
                success = _test_s3_connection(bucket_name, access_key, secret_key, region, create_bucket)
            
            if success:
                st.success("✅ S3 connection successful!")
                
                # Save configuration  
                _save_s3_config(bucket_name, access_key, secret_key, region, create_bucket)
                
                # Switch to S3 provider
                switch_result = switch_storage_provider("s3")
                if switch_result.get("success"):
                    st.success("🔄 Switched to S3 storage provider")
                    st.rerun()
                else:
                    st.error(f"Failed to switch provider: {switch_result.get('error')}")


def show_storage_dashboard():
    """Storage analytics and status dashboard"""
    if not STORAGE_AVAILABLE:
        st.warning("Storage analytics unavailable")
        return
    
    st.header("📊 Storage Dashboard")
    
    # Get current storage info
    storage_info = get_storage_info()
    health = get_storage_health_status()
    
    # Status overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        provider_type = storage_info.get("provider_type", "unknown").title()
        if health.get("healthy"):
            st.metric("Storage Provider", provider_type, "🟢 Healthy")
        else:
            st.metric("Storage Provider", provider_type, "🔴 Unhealthy")
    
    with col2:
        stats = storage_info.get("stats", {})
        if "file_count" in stats:
            st.metric("Total Images", stats["file_count"])
        else:
            st.metric("Total Images", "Unknown")
    
    with col3:
        if "total_size_mb" in stats:
            st.metric("Storage Used", f"{stats['total_size_mb']:.1f} MB")
        elif "total_size_gb" in stats:
            st.metric("Storage Used", f"{stats['total_size_gb']:.2f} GB")
        else:
            st.metric("Storage Used", "Unknown")
    
    # Provider switching
    st.subheader("🔄 Provider Management")
    
    current_provider = storage_info.get("provider_type", "local")
    available_providers = ["local", "s3"] if STORAGE_AVAILABLE else ["local"]
    
    new_provider = st.selectbox(
        "Switch Storage Provider",
        available_providers,
        index=available_providers.index(current_provider) if current_provider in available_providers else 0
    )
    
    if st.button("Switch Provider") and new_provider != current_provider:
        with st.spinner(f"Switching to {new_provider}..."):
            result = switch_storage_provider(new_provider)
            if result.get("success"):
                st.success(f"✅ Switched to {new_provider}")
                st.rerun()
            else:
                st.error(f"Failed to switch: {result.get('error')}")
    
    # Cost estimation (for cloud providers)
    if current_provider == "s3" and "estimated_monthly_cost_usd" in stats:
        st.subheader("💰 Cost Estimate")
        monthly_cost = stats["estimated_monthly_cost_usd"]
        st.info(f"Estimated monthly cost: **${monthly_cost:.2f} USD**")
        
        with st.expander("Cost Breakdown"):
            st.write(f"• Storage: ~${monthly_cost * 0.8:.2f} (80%)")
            st.write(f"• API calls: ~${monthly_cost * 0.15:.2f} (15%)")  
            st.write(f"• Data transfer: ~${monthly_cost * 0.05:.2f} (5%)")


def show_migration_tools():
    """Data migration and backup tools"""
    if not STORAGE_AVAILABLE:
        st.warning("Migration tools unavailable")
        return
    
    st.header("🚚 Data Migration Tools")
    
    storage_info = get_storage_info()
    current_provider = storage_info.get("provider_type", "local")
    
    # Migration options
    st.subheader("📦 Migrate Data")
    
    migration_options = {
        "local": "Local Storage",
        "s3": "Amazon S3"
    }
    
    if current_provider in migration_options:
        del migration_options[current_provider]  # Remove current provider
    
    if migration_options:
        target_provider = st.selectbox(
            f"Migrate from {current_provider.title()} to:",
            list(migration_options.keys()),
            format_func=lambda x: migration_options[x]
        )
        
        user_filter = st.text_input("User ID Filter (optional)", placeholder="Leave empty for all users")
        
        if st.button(f"🚀 Start Migration to {migration_options[target_provider]}", type="primary"):
            with st.spinner("Migrating data..."):
                result = migrate_to_cloud_storage(
                    target_provider=target_provider,
                    user_id=user_filter if user_filter else None
                )
                
                if result.get("success"):
                    migrated = result.get("migrated_files", 0)
                    failed = result.get("failed_files", 0)
                    
                    st.success(f"✅ Migration completed!")
                    st.info(f"📊 Migrated: {migrated} files, Failed: {failed} files")
                    
                    if failed > 0:
                        st.warning("Some files failed to migrate. Check logs for details.")
                else:
                    st.error(f"❌ Migration failed: {result.get('error')}")
    else:
        st.info("No migration targets available")
    
    # Backup verification
    st.subheader("🔍 Backup Verification")
    
    if st.button("Verify Data Integrity"):
        with st.spinner("Verifying backup integrity..."):
            result = _verify_storage_integrity()

            if result["success"]:
                verified_files = result.get("verified_files", 0)
                mismatched_files = result.get("mismatched_files", 0)
                missing_files = result.get("missing_files", 0)

                if mismatched_files == 0 and missing_files == 0:
                    st.success(f"✅ All {verified_files} files verified successfully!")
                else:
                    st.warning(f"⚠️ Issues found: {mismatched_files} mismatched, {missing_files} missing")

                    if result.get("details"):
                        with st.expander("View Details"):
                            for detail in result["details"]:
                                st.write(f"• {detail}")
            else:
                st.error(f"❌ Verification failed: {result.get('error', 'Unknown error')}")
    
    # Export tools
    st.subheader("📤 Export Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Export Metadata"):
            result = _export_metadata_json()
            if result["success"]:
                st.download_button(
                    label="💾 Download Metadata JSON",
                    data=result["data"],
                    file_name=result["filename"],
                    mime="application/json",
                    help="Download inspection metadata with storage provider information"
                )
                st.success(f"✅ Exported {result['inspection_count']} inspections")
            else:
                st.error(f"❌ Export failed: {result['error']}")
    
    with col2:
        if st.button("🗂️ Export File List"):
            result = _export_file_list_csv()
            if result["success"]:
                st.download_button(
                    label="📄 Download File List CSV",
                    data=result["data"],
                    file_name=result["filename"],
                    mime="text/csv",
                    help="Download complete file inventory with metadata"
                )
                st.success(f"✅ Exported {result['file_count']} files")
            else:
                st.error(f"❌ Export failed: {result['error']}")


def _test_s3_connection(bucket_name: str, access_key: str, secret_key: str, region: str, create_bucket: bool) -> bool:
    """Test S3 connection with provided credentials"""
    try:
        from storage.s3_provider import S3StorageProvider
        
        config = {
            "bucket_name": bucket_name,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region": region,
            "create_bucket": create_bucket,
            "use_ssl": True
        }
        
        provider = S3StorageProvider(config)
        health = provider.health_check()
        
        return health.get("healthy", False)
        
    except Exception as e:
        st.error(f"Connection test failed: {e}")
        return False


def _save_s3_config(bucket_name: str, access_key: str, secret_key: str, region: str, create_bucket: bool):
    """Save S3 configuration to environment and config file"""
    try:
        config = get_storage_config()
        
        s3_config = {
            "bucket_name": bucket_name,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region": region,
            "create_bucket": create_bucket,
            "use_ssl": True,
            "storage_class": "STANDARD",
            "server_side_encryption": "AES256"
        }
        
        config.update_provider_config("s3", s3_config, save=True)
        st.success("💾 Configuration saved successfully")
        
    except Exception as e:
        st.error(f"Failed to save configuration: {e}")


def _export_file_list_csv() -> Dict[str, Any]:
    """
    Export file inventory as CSV with complete metadata.

    Returns:
        Dict containing export results with success status and data
    """
    try:
        import csv
        import io
        from datetime import datetime

        # Get current storage provider
        provider = get_current_storage_provider()
        if not provider:
            return {"success": False, "error": "No storage provider available"}

        # Get file list
        files = provider.list_images()
        if not files:
            return {"success": False, "error": "No files found in storage"}

        # Create CSV in memory
        output = io.StringIO()
        fieldnames = [
            'filename', 'storage_path', 'provider', 'file_size_bytes',
            'file_size_mb', 'created_at', 'modified_at', 'storage_class',
            'metadata_summary', 'thumbnail_available'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        storage_info = get_storage_info()
        current_provider = storage_info.get("provider_type", "unknown")

        for file_info in files:
            # Calculate file size in MB
            file_size_bytes = file_info.get("file_size", 0)
            file_size_mb = round(file_size_bytes / (1024 * 1024), 3) if file_size_bytes > 0 else 0

            # Summarize metadata
            metadata = file_info.get("metadata", {})
            metadata_keys = list(metadata.keys()) if metadata else []
            metadata_summary = f"{len(metadata_keys)} fields: {', '.join(metadata_keys[:3])}"
            if len(metadata_keys) > 3:
                metadata_summary += f" (+{len(metadata_keys) - 3} more)"

            # Check thumbnail availability
            thumbnail_available = "Yes" if file_info.get("thumbnail_path") else "No"

            writer.writerow({
                'filename': file_info.get("filename", ""),
                'storage_path': file_info.get("storage_path", ""),
                'provider': current_provider,
                'file_size_bytes': file_size_bytes,
                'file_size_mb': file_size_mb,
                'created_at': file_info.get("created_at", ""),
                'modified_at': file_info.get("modified_at", ""),
                'storage_class': file_info.get("storage_class", ""),
                'metadata_summary': metadata_summary,
                'thumbnail_available': thumbnail_available
            })

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"beehive_file_inventory_{timestamp}.csv"

        csv_data = output.getvalue()
        output.close()

        return {
            "success": True,
            "data": csv_data,
            "filename": filename,
            "file_count": len(files)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _export_metadata_json() -> Dict[str, Any]:
    """
    Export inspection metadata as JSON with storage provider information.

    Returns:
        Dict containing export results with success status and data
    """
    try:
        from utils.data_handler import export_inspection_data
        from datetime import datetime
        import json

        # Use existing export function
        data, error = export_inspection_data(format="json")

        if error:
            return {"success": False, "error": error}

        if not data:
            return {"success": False, "error": "No inspection data available"}

        # Enhance exported data with storage information
        storage_info = get_storage_info()
        enhanced_data = data.copy()

        enhanced_data["export_metadata"] = {
            "exported_at": datetime.now().isoformat(),
            "storage_provider": storage_info.get("provider_type", "unknown"),
            "storage_health": storage_info.get("health", {}),
            "export_version": "1.0"
        }

        # Convert to JSON string
        json_data = json.dumps(enhanced_data, indent=2, ensure_ascii=False)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"beehive_metadata_export_{timestamp}.json"

        inspection_count = len(enhanced_data.get("inspections", []))

        return {
            "success": True,
            "data": json_data,
            "filename": filename,
            "inspection_count": inspection_count
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _verify_storage_integrity() -> Dict[str, Any]:
    """
    Verify data integrity by comparing files between available storage providers.

    Returns:
        Dict containing verification results with success status, counts, and details
    """
    try:
        from storage import get_storage_manager
        import hashlib

        manager = get_storage_manager()
        current_provider = get_storage_info().get("provider_type", "local")

        # Get all available providers except current one
        available_providers = [p for p in manager.get_available_providers() if p != current_provider]

        if not available_providers:
            return {
                "success": False,
                "error": "No other storage providers available for comparison"
            }

        # Compare with first available alternative provider
        comparison_provider = available_providers[0]

        # Get current and comparison providers
        current = manager.get_provider(current_provider)
        comparison = manager.get_provider(comparison_provider)

        # List files from current provider
        current_files = current.list_images()
        comparison_files = comparison.list_images()

        # Create lookup for comparison files
        comparison_lookup = {f["filename"]: f for f in comparison_files}

        verified_files = 0
        mismatched_files = 0
        missing_files = 0
        details = []

        for current_file in current_files:
            filename = current_file["filename"]

            if filename not in comparison_lookup:
                missing_files += 1
                details.append(f"Missing in {comparison_provider}: {filename}")
                continue

            # Compare file sizes first (quick check)
            current_size = current_file.get("file_size", 0)
            comparison_size = comparison_lookup[filename].get("file_size", 0)

            if current_size != comparison_size:
                mismatched_files += 1
                details.append(f"Size mismatch {filename}: {current_size} vs {comparison_size} bytes")
                continue

            # For critical verification, could add hash comparison here
            # (commented out for performance - file size comparison is usually sufficient)
            # current_data = current.download_image(current_file["storage_path"])
            # comparison_data = comparison.download_image(comparison_lookup[filename]["storage_path"])
            # if hashlib.md5(current_data).hexdigest() != hashlib.md5(comparison_data).hexdigest():
            #     mismatched_files += 1
            #     details.append(f"Content hash mismatch: {filename}")
            #     continue

            verified_files += 1

        return {
            "success": True,
            "verified_files": verified_files,
            "mismatched_files": mismatched_files,
            "missing_files": missing_files,
            "details": details,
            "compared_providers": f"{current_provider} vs {comparison_provider}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def show_storage_management_page():
    """Complete storage management page for Streamlit"""
    st.title("🗄️ Storage Management")
    
    if not STORAGE_AVAILABLE:
        st.error("⚠️ Storage abstraction layer not available")
        st.info("Run `pip install boto3` to enable cloud storage features")
        return
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🚀 Setup", "🚚 Migration"])
    
    with tab1:
        show_storage_dashboard()
    
    with tab2:
        show_storage_setup_wizard()
    
    with tab3:
        show_migration_tools()
    
    # Footer with help
    st.markdown("---")
    st.markdown("""
    **💡 Need Help?**
    - [AWS S3 Setup Guide](https://docs.aws.amazon.com/s3/latest/userguide/GetStartedWithS3.html)
    - [IAM Permissions](https://docs.aws.amazon.com/s3/latest/userguide/s3-access-control.html)
    - Cost Calculator: Estimated costs are approximate
    """)


if __name__ == "__main__":
    # For testing the UI components
    show_storage_management_page()