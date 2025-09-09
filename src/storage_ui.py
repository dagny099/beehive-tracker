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
            # This would implement hash comparison between providers
            st.info("🔧 Backup verification feature coming soon")
    
    # Export tools
    st.subheader("📤 Export Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Export Metadata"):
            # Export metadata as JSON
            st.info("🔧 Metadata export feature coming soon")
    
    with col2:
        if st.button("🗂️ Export File List"):
            # Export file inventory
            st.info("🔧 File list export feature coming soon")


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