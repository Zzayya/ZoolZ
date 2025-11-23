#!/usr/bin/env python3
"""
Result Organizer - Main Orchestrator
Coordinates all organization modules to process search results
This is the main entry point - replaces the old monolithic data_organizer.py

NOW WITH ML & DATA COLLECTION:
- Uses ML models for better accuracy
- Collects predictions for training datasets
"""

from typing import Dict, List, Optional, Any

from .cache_manager import CacheManager
from .person_extractor import PersonExtractor
from .deduplicator import PersonDeduplicator
from .confidence_scorer import ConfidenceScorer
from .phone_organizer import PhoneOrganizer
from .address_organizer import AddressOrganizer
from .email_organizer import EmailOrganizer
from .result_builder import ResultBuilder

# Try to import data collector
try:
    from ..data_collector import DataCollector
    DATA_COLLECTOR_AVAILABLE = True
except ImportError:
    DATA_COLLECTOR_AVAILABLE = False


class ResultOrganizer:
    """
    Main orchestrator for result organization.

    Coordinates all specialized organizers to:
    1. Extract persons from raw search data
    2. Deduplicate person records (WITH ML)
    3. Organize phones, addresses, emails
    4. Calculate confidence scores
    5. Build cross-references
    6. Assemble final results
    7. Cache results for future use
    8. Collect ML predictions for training

    This class is THIN - it just coordinates. Each organizer does its own job.
    """

    def __init__(self, db_path: str = "database/search_cache.db", data_collector: Optional[Any] = None, enable_ml: bool = True):
        """
        Initialize result organizer with all sub-organizers.

        Args:
            db_path: Path to cache database
            data_collector: Optional DataCollector for tracking predictions
            enable_ml: Enable/disable ML features (controlled by frontend toggle)
        """
        self.data_collector = data_collector
        self.enable_ml = enable_ml

        # Initialize all organizers
        self.cache_manager = CacheManager(db_path)
        self.person_extractor = PersonExtractor()
        self.deduplicator = PersonDeduplicator(use_ml=self.enable_ml, data_collector=data_collector)
        self.confidence_scorer = ConfidenceScorer()
        self.phone_organizer = PhoneOrganizer(self.confidence_scorer)
        self.address_organizer = AddressOrganizer(self.confidence_scorer)
        self.email_organizer = EmailOrganizer(self.confidence_scorer)
        self.result_builder = ResultBuilder()

    def organize_results(
        self,
        results: Dict,
        use_cache: bool = True,
        cache_duration_hours: int = 24
    ) -> Dict:
        """
        Main entry point: Organize raw search results.

        Args:
            results: Raw search results from SearchOrchestrator
            use_cache: Whether to use/update cache
            cache_duration_hours: How long to cache results

        Returns:
            Fully organized results ready for API response
        """
        search_params = results.get("search_params", {})

        # Check cache first
        if use_cache:
            cached = self.cache_manager.check_cache(
                name=search_params.get("name"),
                phone=search_params.get("phone"),
                address=search_params.get("address"),
                email=search_params.get("email"),
                max_age_hours=cache_duration_hours
            )
            if cached:
                cached["from_cache"] = True
                return cached

        # STEP 1: Extract persons from raw results
        persons = self.person_extractor.extract_persons_from_results(results)

        # STEP 2: Deduplicate persons (merge duplicates) WITH ML
        persons = self.deduplicator.deduplicate_persons(persons)

        # COLLECT ML PREDICTIONS: Get name matching predictions for dataset
        ml_predictions = {"name_matches": []}
        if hasattr(self.deduplicator, 'get_predictions_for_dataset'):
            ml_predictions["name_matches"] = self.deduplicator.get_predictions_for_dataset()

        # STEP 3: Organize contact data for each person
        for person in persons:
            # Organize phones
            person["organized_phones"] = self.phone_organizer.organize_phones(person)

            # Organize addresses
            person["organized_addresses"] = self.address_organizer.organize_addresses(person)

            # Organize emails
            person["organized_emails"] = self.email_organizer.organize_emails(person)

            # Create organized_data structure for frontend compatibility
            person["organized_data"] = {
                "phone_numbers": person.get("organized_phones", []),
                "addresses": person.get("organized_addresses", []),
                "emails": person.get("organized_emails", []),
                "public_records": person.get("public_records", []),
                "social_media": person.get("web_mentions", []),
                "county_records": person.get("county_records", [])
            }

            # Calculate overall confidence
            person["overall_confidence_score"] = self.confidence_scorer.calculate_person_confidence(person)
            person["overall_confidence"] = self._score_to_level(person["overall_confidence_score"])

        # STEP 4: Add cross-references between persons
        persons = self.result_builder.add_cross_references(persons)

        # STEP 5: Sort by relevance
        persons = self.result_builder.sort_persons_by_relevance(persons, search_params)

        # STEP 6: Build final results WITH ML insights
        final_results = self.result_builder.build_final_results(
            persons=persons,
            search_params=search_params,
            metadata={
                "organized_at": True,
                "cache_enabled": use_cache
            },
            ml_insights=ml_predictions  # Pass ML predictions to frontend
        )

        # Cache results
        if use_cache:
            self.cache_manager.cache_results(final_results, cache_duration_hours)
            self.cache_manager.add_to_history(search_params)

        return final_results

    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to confidence level"""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def clear_old_cache(self, days: int = 7):
        """Clear cache entries older than specified days"""
        self.cache_manager.clear_old_cache(days)

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self.cache_manager.get_stats()


# Backward compatibility: create instance that can be imported like old data_organizer
_default_organizer = ResultOrganizer()


def organize_results(results: Dict, use_cache: bool = True) -> Dict:
    """
    Convenience function for backward compatibility.
    Mimics old data_organizer.organize_results() interface.
    """
    return _default_organizer.organize_results(results, use_cache)
