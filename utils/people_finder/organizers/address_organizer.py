#!/usr/bin/env python3
"""
Address Organizer
Professional-grade address organization
ONE JOB: Process, deduplicate, and organize addresses
"""

import re
from typing import Dict, List

# Import address parser if available
try:
    from ..address_parser import AddressParser
    ADDRESS_PARSER_AVAILABLE = True
except ImportError:
    ADDRESS_PARSER_AVAILABLE = False


class AddressOrganizer:
    """
    Organizes addresses with:
    - Advanced parsing and normalization
    - Deduplication (same address, different formats)
    - Location extraction (city, state, ZIP)
    - Address type detection (PO Box, residential, business)
    - Confidence scoring per address
    """

    def __init__(self, confidence_scorer=None):
        """
        Initialize address organizer.

        Args:
            confidence_scorer: ConfidenceScorer instance (optional)
        """
        self.confidence_scorer = confidence_scorer
        self.parser = AddressParser() if ADDRESS_PARSER_AVAILABLE else None

    def organize_addresses(self, person: Dict) -> List[Dict]:
        """
        Organize all addresses for a person.

        Args:
            person: Person dict with addresses and sources

        Returns:
            List of organized address dicts with full metadata
        """
        raw_addresses = person.get("addresses", [])

        if not raw_addresses:
            return []

        # Deduplicate addresses
        unique_addresses = self._deduplicate_addresses(raw_addresses)

        organized = []

        for addr in unique_addresses:
            # Parse address components
            if self.parser:
                components = self.parser.parse_address(addr)
                normalized = components.get("full_normalized", addr)
                location = {
                    "city": components.get("city", ""),
                    "state": components.get("state", ""),
                    "zip_code": components.get("zip_code", "")
                }
                address_type = self.parser.detect_address_type(addr)
            else:
                # Fallback parsing
                normalized = addr
                location = self._extract_location_fallback(addr)
                address_type = "unknown"

            # Calculate confidence
            if self.confidence_scorer:
                confidence = self.confidence_scorer.calculate_address_confidence(
                    addr,
                    person.get("confidence_sources", [])
                )
            else:
                confidence = "medium"

            # Count how many sources mention this address
            source_count = self._count_address_mentions(addr, person)

            address_data = {
                "full_address": addr,
                "normalized": normalized,
                "city": location.get("city", ""),
                "state": location.get("state", ""),
                "zip_code": location.get("zip_code", ""),
                "address_type": address_type,  # residential, business, po_box
                "is_po_box": address_type == "po_box",
                "confidence": confidence,
                "confidence_percent": self._confidence_to_percent(confidence),
                "source_count": source_count,
                "sources": self._get_address_sources(addr, person)
            }

            organized.append(address_data)

        # Sort by confidence (highest first)
        organized.sort(key=lambda x: x["confidence_percent"], reverse=True)

        return organized

    def _deduplicate_addresses(self, addresses: List[str]) -> List[str]:
        """Deduplicate addresses accounting for format variations"""
        if self.parser:
            return self.parser.deduplicate_addresses(addresses)

        # Fallback deduplication
        seen_normalized = set()
        unique = []

        for addr in addresses:
            normalized = addr.lower().strip()
            normalized = re.sub(r'\s+', ' ', normalized)

            if normalized not in seen_normalized:
                seen_normalized.add(normalized)
                unique.append(addr)

        return unique

    def _extract_location_fallback(self, address: str) -> Dict:
        """Fallback location extraction without parser"""
        location = {"city": "", "state": "", "zip_code": ""}

        # Extract ZIP
        zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', address)
        if zip_match:
            location["zip_code"] = zip_match.group(1)

        # Extract state (2-letter code)
        state_match = re.search(r'\b([A-Z]{2})\b', address)
        if state_match:
            location["state"] = state_match.group(1)

        # Try to extract city (word before state)
        if location["state"]:
            city_pattern = r'([A-Za-z\s]+),?\s+' + location["state"]
            city_match = re.search(city_pattern, address)
            if city_match:
                location["city"] = city_match.group(1).strip().title()

        return location

    def _count_address_mentions(self, address: str, person: Dict) -> int:
        """Count how many times this address appears"""
        count = 0

        # Check public records
        for record in person.get("public_records", []):
            if isinstance(record, dict):
                if address.lower() in str(record).lower():
                    count += 1

        # Check web mentions
        for mention in person.get("web_mentions", []):
            if isinstance(mention, dict):
                if address.lower() in str(mention).lower():
                    count += 1

        return max(count, 1)

    def _get_address_sources(self, address: str, person: Dict) -> List[str]:
        """Get list of sources where this address was found"""
        sources = []

        if "public_records" in person.get("confidence_sources", []):
            sources.append("Public Records")

        if "user_input" in person.get("confidence_sources", []):
            sources.append("User Input")

        if "web_mention" in person.get("confidence_sources", []):
            sources.append("Web Search")

        return sources if sources else ["Unknown"]

    def _confidence_to_percent(self, confidence: str) -> int:
        """Convert confidence level to percentage"""
        mapping = {"high": 85, "medium": 60, "low": 35}
        return mapping.get(confidence, 50)
