#!/usr/bin/env python3
"""
People Finder - Data Organizers Module
Modular, focused classes for data organization and processing
"""

from .cache_manager import CacheManager
from .person_extractor import PersonExtractor
from .deduplicator import PersonDeduplicator
from .confidence_scorer import ConfidenceScorer
from .phone_organizer import PhoneOrganizer
from .address_organizer import AddressOrganizer
from .email_organizer import EmailOrganizer
from .result_builder import ResultBuilder

# Main orchestrator class that uses all the above
from .result_organizer import ResultOrganizer

__all__ = [
    'CacheManager',
    'PersonExtractor',
    'PersonDeduplicator',
    'ConfidenceScorer',
    'PhoneOrganizer',
    'AddressOrganizer',
    'EmailOrganizer',
    'ResultBuilder',
    'ResultOrganizer'
]
