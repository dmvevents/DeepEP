"""
Property Lookup Module

Handles property address validation, geocoding, and data retrieval.
Integrates with tax scraper database and external APIs.

Created by: Neumann Rashid AI Development
Date: November 8, 2025
"""

from .property_service import (
    PropertyAddress,
    PropertyData,
    PropertyLookupService
)

__all__ = [
    'PropertyAddress',
    'PropertyData',
    'PropertyLookupService',
]
