#!/usr/bin/env python3
"""
Confidence Scorer
Calculates confidence scores for data points
ONE JOB: Determine how confident we are in each piece of data
"""

from typing import Dict, List


class ConfidenceScorer:
    """
    Calculates confidence scores for persons, phones, addresses, emails.
    Uses multiple signals to determine data reliability.
    """

    # Base source weights for overall confidence
    SOURCE_WEIGHTS = {
        "user_input": 30,          # User-provided data (highest initial weight)
        "public_records": 25,      # Official government records
        "phone_api": 20,           # Validated phone number
        "verified_email": 15,      # Verified email address
        "social_media": 5,         # Social media profile (unverified)
        "web_mention": 3           # Web mention (lowest confidence)
    }

    def calculate_person_confidence(self, person: Dict) -> float:
        """
        Calculate overall confidence for a person record.

        Confidence calculation:
        - Base scores from data sources
        - Bonus for multiple data points
        - Bonus for cross-references
        - Higher confidence = more likely to be accurate match

        Scale: 0-100%
        - 70-100%: High confidence (multiple verified sources)
        - 40-69%: Medium confidence (some sources, needs verification)
        - 0-39%: Low confidence (unverified web mentions only)

        Args:
            person: Person dict with data and sources

        Returns:
            Confidence score (0-100)
        """
        score = 0.0

        # Add source scores
        for source in person.get("confidence_sources", []):
            score += self.SOURCE_WEIGHTS.get(source, 1)

        # Bonus for multiple data points (indicates more complete record)
        if len(person.get("phones", [])) > 1:
            score += 5
        if len(person.get("addresses", [])) > 1:
            score += 5
        if len(person.get("emails", [])) > 0:
            score += 5

        # Bonus for public records (very reliable)
        num_records = len(person.get("public_records", []))
        if num_records > 0:
            score += min(num_records * 3, 15)  # Up to +15 for multiple records

        # Bonus for cross-references (shared data with other persons)
        cross_refs = person.get("cross_references", [])
        if cross_refs:
            score += min(len(cross_refs) * 5, 10)  # Up to +10 for cross-references

        # Cap at 100
        return min(score, 100.0)

    def calculate_phone_confidence(
        self,
        phone: str,
        sources: List[str],
        validation_data: Dict
    ) -> str:
        """
        Calculate confidence level for a phone number.

        Args:
            phone: Phone number
            sources: List of sources where this phone was found
            validation_data: Phone validation result dict

        Returns:
            "high", "medium", or "low"
        """
        score = 0

        # Validated via API
        if validation_data.get("valid"):
            score += 40

        # From official sources
        if "public_records" in sources:
            score += 30

        # From user input
        if "user_input" in sources:
            score += 20

        # From web mentions
        if "web_mention" in sources:
            score += 10

        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def calculate_address_confidence(self, address: str, sources: List[str]) -> str:
        """
        Calculate confidence level for an address.

        Args:
            address: Address string
            sources: List of sources where found

        Returns:
            "high", "medium", or "low"
        """
        score = 0

        # From public records (most reliable)
        if "public_records" in sources:
            score += 50

        # From user input
        if "user_input" in sources:
            score += 30

        # Has ZIP code (more complete)
        import re
        if re.search(r'\d{5}', address):
            score += 10

        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def calculate_email_confidence(
        self,
        email: str,
        sources: List[str],
        domain: str
    ) -> str:
        """
        Calculate confidence level for an email.

        Args:
            email: Email address
            sources: List of sources where found
            domain: Email domain

        Returns:
            "high", "medium", or "low"
        """
        score = 0

        # From public records
        if "public_records" in sources:
            score += 40

        # From user input
        if "user_input" in sources:
            score += 30

        # Valid domain
        if self._is_valid_email_domain(domain):
            score += 15

        # Known provider (more reliable)
        if self._is_known_provider(domain):
            score += 15

        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def confidence_to_percent(self, confidence: str) -> int:
        """
        Convert confidence level to percentage.

        Args:
            confidence: "high", "medium", or "low"

        Returns:
            Percentage (0-100)
        """
        mapping = {"high": 85, "medium": 60, "low": 35}
        return mapping.get(confidence, 50)

    def _is_valid_email_domain(self, domain: str) -> bool:
        """Basic domain validation"""
        if not domain:
            return False

        # Must have at least one dot
        if '.' not in domain:
            return False

        # Must not start or end with dot or dash
        if domain.startswith('.') or domain.startswith('-'):
            return False
        if domain.endswith('.') or domain.endswith('-'):
            return False

        # Must have valid TLD (at least 2 chars after last dot)
        parts = domain.split('.')
        if len(parts) < 2 or len(parts[-1]) < 2:
            return False

        return True

    def _is_known_provider(self, domain: str) -> bool:
        """Check if domain is a known email provider"""
        known_providers = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com'
        }
        return domain.lower() in known_providers
