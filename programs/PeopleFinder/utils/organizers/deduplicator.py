#!/usr/bin/env python3
"""
Person Deduplicator
Finds and merges duplicate person records
ONE JOB: Identify when multiple records represent the same person

NOW WITH ML: Uses pre-trained Sentence-BERT for semantic name matching
"""

import re
from typing import Dict, List, Optional, Any

# Try to import Levenshtein for fuzzy matching, fallback to difflib
try:
    from Levenshtein import ratio as levenshtein_ratio
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    # Fallback: Use difflib.SequenceMatcher
    from difflib import SequenceMatcher
    def levenshtein_ratio(str1: str, str2: str) -> float:
        """Fallback implementation using difflib"""
        return SequenceMatcher(None, str1, str2).ratio()
    LEVENSHTEIN_AVAILABLE = False

# Try to import ML models
try:
    from ..ml_models import ml_models
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class PersonDeduplicator:
    """
    Deduplicates person records using:
    - Name similarity (ML-powered semantic matching OR fuzzy matching fallback)
    - Shared phone numbers
    - Shared addresses
    - Shared emails
    - Geographic compatibility

    Merges duplicate records into single comprehensive person.

    ML Features:
    - Sentence-BERT for semantic name matching (handles nicknames, typos)
    - Learns name variations over time via memory manager
    - Tracks predictions for dataset creation
    """

    # State neighbors for geographic validation
    NEIGHBORING_STATES = {
        "OH": ["PA", "WV", "IN", "KY", "MI"],
        "PA": ["OH", "WV", "NY", "NJ", "DE", "MD"],
        "WV": ["OH", "PA", "VA", "KY", "MD"],
        "IN": ["OH", "KY", "IL", "MI"],
        "IL": ["IN", "WI", "IA", "MO", "KY"],
        "KY": ["OH", "WV", "VA", "TN", "MO", "IL", "IN"],
        "TN": ["KY", "VA", "NC", "GA", "AL", "MS", "AR", "MO"]
    }

    def __init__(self, use_ml: bool = True, data_collector: Optional[Any] = None):
        """
        Initialize deduplicator.

        Args:
            use_ml: Whether to use ML models (True = Sentence-BERT, False = Levenshtein)
            data_collector: Optional DataCollector for tracking predictions
        """
        self.use_ml = use_ml and ML_AVAILABLE
        self.data_collector = data_collector
        self.name_matcher = None
        self.predictions_cache = []  # Store predictions for dataset creation

        if self.use_ml:
            try:
                self.name_matcher = ml_models.get_name_matcher()
            except Exception as e:
                print(f"⚠ Could not load ML name matcher: {e}")
                self.use_ml = False

    def deduplicate_persons(self, persons: List[Dict]) -> List[Dict]:
        """
        Find and merge duplicate person records.

        Args:
            persons: List of person dicts

        Returns:
            Deduplicated list of persons
        """
        if not persons:
            return []

        # Track which persons have been merged
        merged_indices = set()
        unique_persons = []

        for i, person1 in enumerate(persons):
            if i in merged_indices:
                continue  # Already merged into another person

            # Start with this person
            merged_person = person1.copy()

            # Find all duplicates of this person
            for j, person2 in enumerate(persons[i+1:], start=i+1):
                if j in merged_indices:
                    continue

                if self._are_same_person(person1, person2):
                    # Merge person2 into merged_person
                    merged_person = self._merge_persons(merged_person, person2)
                    merged_indices.add(j)

            unique_persons.append(merged_person)

        return unique_persons

    def _are_same_person(self, person1: Dict, person2: Dict) -> bool:
        """
        Determine if two person records represent the same individual.

        Returns:
            True if likely the same person
        """
        # Check name similarity
        name1 = person1.get("name", "").lower().strip()
        name2 = person2.get("name", "").lower().strip()

        if not name1 or not name2:
            return False

        # Exact match
        if name1 == name2:
            return True

        # Fuzzy match (handles typos, middle names, nicknames)
        if self._names_are_similar(name1, name2):
            # Names are similar - check for shared data
            if self._share_contact_info(person1, person2):
                return True

        # Check for shared unique identifiers (even if names different)
        if self._share_unique_identifiers(person1, person2):
            return True

        return False

    def _names_are_similar(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """
        Check if names are similar using ML semantic matching OR fuzzy fallback.

        ML Mode: Sentence-BERT semantic similarity (understands "Bill" = "William")
        Fallback: Levenshtein/difflib string similarity
        """
        similarity = 0.0

        if self.use_ml and self.name_matcher:
            # ML-based semantic similarity
            is_same, similarity = self.name_matcher.predict_same_person(name1, name2, threshold)

            # Track prediction for dataset creation
            self.predictions_cache.append({
                "name1": name1,
                "name2": name2,
                "similarity": float(similarity),
                "predicted_same": is_same,
                "method": "sentence_bert"
            })

            if is_same:
                return True

        else:
            # Fallback: Levenshtein/difflib
            similarity = levenshtein_ratio(name1, name2)

            # Track prediction for dataset creation
            self.predictions_cache.append({
                "name1": name1,
                "name2": name2,
                "similarity": float(similarity),
                "predicted_same": similarity >= threshold,
                "method": "levenshtein"
            })

            if similarity >= threshold:
                return True

        # Check if one name is substring of other (handles middle names)
        # "John Smith" vs "John Michael Smith"
        name1_parts = set(name1.split())
        name2_parts = set(name2.split())

        # If all parts of shorter name appear in longer name
        shorter = name1_parts if len(name1_parts) < len(name2_parts) else name2_parts
        longer = name2_parts if len(name1_parts) < len(name2_parts) else name1_parts

        if shorter.issubset(longer):
            return True

        # Check for nickname variations (if available)
        return False

    def _share_contact_info(self, person1: Dict, person2: Dict) -> bool:
        """Check if persons share contact information"""
        # Share phone number
        phones1 = set(self._normalize_phones(person1.get("phones", [])))
        phones2 = set(self._normalize_phones(person2.get("phones", [])))

        if phones1 & phones2:  # Intersection
            return True

        # Share address
        addrs1 = set([addr.lower().strip() for addr in person1.get("addresses", [])])
        addrs2 = set([addr.lower().strip() for addr in person2.get("addresses", [])])

        if addrs1 & addrs2:
            return True

        # Share email
        emails1 = set([e.lower() for e in person1.get("emails", [])])
        emails2 = set([e.lower() for e in person2.get("emails", [])])

        if emails1 & emails2:
            return True

        return False

    def _share_unique_identifiers(self, person1: Dict, person2: Dict) -> bool:
        """Check if persons share unique identifiers (phone, email)"""
        # Phone numbers are pretty unique
        phones1 = set(self._normalize_phones(person1.get("phones", [])))
        phones2 = set(self._normalize_phones(person2.get("phones", [])))

        if phones1 and phones2 and (phones1 & phones2):
            return True

        # Emails are unique
        emails1 = set([e.lower() for e in person1.get("emails", [])])
        emails2 = set([e.lower() for e in person2.get("emails", [])])

        if emails1 and emails2 and (emails1 & emails2):
            return True

        return False

    def _normalize_phones(self, phones: List[str]) -> List[str]:
        """Normalize phone numbers for comparison"""
        normalized = []
        for phone in phones:
            # Remove all non-digits
            digits = re.sub(r'\D', '', phone)
            # Handle 10 vs 11 digit numbers
            if len(digits) == 11 and digits[0] == '1':
                digits = digits[1:]
            if len(digits) == 10:
                normalized.append(digits)
        return normalized

    def _merge_persons(self, person1: Dict, person2: Dict) -> Dict:
        """
        Merge two person records into one comprehensive record.

        Args:
            person1: First person (base)
            person2: Second person (to merge in)

        Returns:
            Merged person dict
        """
        merged = person1.copy()

        # Use longer/more complete name
        if len(person2.get("name", "")) > len(person1.get("name", "")):
            merged["name"] = person2["name"]

        # Merge lists (deduplicate)
        for list_field in ["phones", "addresses", "emails", "public_records", "phone_mentions", "social_media", "web_mentions"]:
            list1 = person1.get(list_field, [])
            list2 = person2.get(list_field, [])

            # Combine and deduplicate
            if list_field in ["phones", "addresses", "emails"]:
                # Deduplicate strings
                combined = list(dict.fromkeys([item for item in list1 + list2 if item]))
            else:
                # Combine dicts
                combined = list1 + list2

            merged[list_field] = combined

        # Merge confidence sources
        sources1 = set(person1.get("confidence_sources", []))
        sources2 = set(person2.get("confidence_sources", []))
        merged["confidence_sources"] = list(sources1 | sources2)

        # Merge phone validation data
        if person2.get("phone_validation"):
            if not merged.get("phone_validation"):
                merged["phone_validation"] = {}
            merged["phone_validation"].update(person2["phone_validation"])

        # Track that this was merged
        merged["merged_from_sources"] = merged.get("merged_from_sources", 0) + 1

        return merged

    def _geographic_compatible(self, person1: Dict, person2: Dict) -> bool:
        """Check if persons' locations are geographically compatible"""
        # Extract states from addresses
        states1 = self._extract_states_from_addresses(person1.get("addresses", []))
        states2 = self._extract_states_from_addresses(person2.get("addresses", []))

        if not states1 or not states2:
            return True  # Can't determine, assume compatible

        # Check if any states overlap or are neighbors
        for state1 in states1:
            if state1 in states2:
                return True  # Same state

            # Check if neighbors
            neighbors = self.NEIGHBORING_STATES.get(state1, [])
            if any(state2 in neighbors for state2 in states2):
                return True

        # States are far apart - likely not same person
        return False

    def _extract_states_from_addresses(self, addresses: List[str]) -> List[str]:
        """Extract state codes from addresses"""
        states = []
        for addr in addresses:
            # Look for 2-letter state code
            match = re.search(r'\b([A-Z]{2})\b', addr)
            if match:
                state = match.group(1)
                if state in self.NEIGHBORING_STATES.keys() or state in [s for neighbors in self.NEIGHBORING_STATES.values() for s in neighbors]:
                    states.append(state)
        return states

    def get_predictions_for_dataset(self) -> List[Dict]:
        """
        Get all name matching predictions made during this deduplication run.
        Used for creating training datasets.

        Returns:
            List of prediction dicts with name pairs and similarity scores
        """
        predictions = self.predictions_cache.copy()
        self.predictions_cache = []  # Clear for next run
        return predictions
