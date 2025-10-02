"""
Test suite for Bulk Import System.

This test suite enforces Template Consistency through Test-Driven Development.
All bulk import templates must pass these tests to ensure identical behavior
across different photo sources.

Test Structure:
- test_template_consistency.py: Core consistency enforcement tests
- test_integration.py: Integration tests with real data sources
- fixtures/: Shared test data and utilities

Usage:
    # Run all consistency tests
    pytest tests/bulk_import/test_template_consistency.py -v

    # Run specific test category
    pytest tests/bulk_import/test_template_consistency.py::TestTemplateConsistency -v
"""

import os
import sys

# Add src to path for imports during testing
test_dir = os.path.dirname(__file__)
src_dir = os.path.join(test_dir, '..', '..', 'src')
sys.path.insert(0, src_dir)