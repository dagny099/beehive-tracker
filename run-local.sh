#!/bin/bash
# Make sure we're in the project root
cd "$(dirname "$0")"

# Set up environment variables
export PYTHONPATH=.

# Run the app
streamlit run src/app.py
