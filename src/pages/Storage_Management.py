"""
Streamlit page for storage management - Phase 3 UI implementation.
Provides complete storage management interface as a dedicated page.
"""

import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from storage_ui import show_storage_management_page

# Page configuration
# st.set_page_config(
#     page_title="Storage Management - Beehive Tracker",
#     page_icon="🗄️",
#     layout="wide"
# )

# Main page content
show_storage_management_page()