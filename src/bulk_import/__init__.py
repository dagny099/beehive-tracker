"""
Bulk Import System for Beehive Tracker.

This module provides a Test-Driven Development approach to bulk photo imports
with guaranteed consistency across different sources (S3, Local, URL).

Key Components:
- photo_processing_contract: Abstract interfaces ensuring identical behavior
- Template implementations: Reference patterns for each import source
- Consistency testing: Automated verification of template uniformity

Usage:
    from bulk_import import PhotoMetadata, BulkImportTemplate
    from bulk_import.s3_bulk_importer import S3BulkImporter
"""

from .photo_processing_contract import (
    PhotoMetadata,
    InspectionGroup,
    ProcessingResult,
    BulkImportTemplate,
    GroupingStrategy,
    TemplateConsistencyError,
    verify_template_consistency
)

__all__ = [
    'PhotoMetadata',
    'InspectionGroup',
    'ProcessingResult',
    'BulkImportTemplate',
    'GroupingStrategy',
    'TemplateConsistencyError',
    'verify_template_consistency'
]

__version__ = '1.0.0'
__author__ = 'Beehive Tracker Team'