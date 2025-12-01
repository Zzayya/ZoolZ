#!/usr/bin/env python3
"""
Person Extractor
Extracts person records from raw search results
ONE JOB: Turn raw search data into structured person objects
"""

from typing import Dict, List


class PersonExtractor:
    """
    Extracts person records from various sources:
    - Public records
    - Phone validation data
    - Web mentions
    - Social media profiles
    - Federal records

    Creates structured person objects with all available data.
    """

    def extract_persons_from_results(self, results: Dict) -> List[Dict]:
        """
        Extract all unique persons from search results.

        Args:
            results: Raw search results dict

        Returns:
            List of person dicts
        """
        persons = []

        # Extract from public records
        if results.get("public_records"):
            persons.extend(self._extract_from_public_records(results["public_records"]))

        # Extract from phone mentions
        if results.get("phone_mentions"):
            persons.extend(self._extract_from_phone_mentions(results["phone_mentions"]))

        # Extract from social media
        if results.get("social_media"):
            persons.extend(self._extract_from_social_media(results["social_media"]))

        # Extract from web mentions
        if results.get("web_mentions"):
            persons.extend(self._extract_from_web_mentions(results["web_mentions"]))

        # Add search params as source data
        search_params = results.get("search_params", {})
        if search_params.get("name"):
            # Create person from user input
            input_person = self._create_person_from_input(search_params)
            persons.append(input_person)

        return persons

    def _extract_from_public_records(self, public_records: List[Dict]) -> List[Dict]:
        """Extract persons from public records"""
        persons = []

        for record in public_records:
            if not isinstance(record, dict):
                continue

            person = {
                "name": record.get("name", ""),
                "phones": [],
                "addresses": [],
                "emails": [],
                "public_records": [record],
                "confidence_sources": ["public_records"],
                "phone_validation": {},
                "phone_mentions": [],
                "social_media": [],
                "web_mentions": []
            }

            # Extract contact info from record
            if record.get("phone"):
                person["phones"].append(record["phone"])

            if record.get("address"):
                person["addresses"].append(record["address"])

            if record.get("email"):
                person["emails"].append(record["email"])

            # Add scraped data if available
            if record.get("scraped_data"):
                person["scraped_data"] = record["scraped_data"]
                person["has_scraped_data"] = True

            if person["name"]:  # Only add if we have a name
                persons.append(person)

        return persons

    def _extract_from_phone_mentions(self, phone_mentions: List[Dict]) -> List[Dict]:
        """Extract persons from phone number mentions"""
        persons = []

        for mention in phone_mentions:
            if not isinstance(mention, dict):
                continue

            # Look for associated names in mentions
            associated_names = mention.get("associated_names", [])

            for name in associated_names:
                person = {
                    "name": name,
                    "phones": [mention.get("phone", "")],
                    "addresses": [],
                    "emails": [],
                    "public_records": [],
                    "confidence_sources": ["web_mention"],
                    "phone_validation": {},
                    "phone_mentions": [mention],
                    "social_media": [],
                    "web_mentions": []
                }

                persons.append(person)

        return persons

    def _extract_from_social_media(self, social_media: Dict) -> List[Dict]:
        """Extract persons from social media profiles"""
        persons = []

        for platform, profiles in social_media.items():
            if not isinstance(profiles, list):
                continue

            for profile in profiles:
                if not isinstance(profile, dict):
                    continue

                # Try to extract name from title or snippet
                title = profile.get("title", "")
                name = self._extract_name_from_text(title)

                if name:
                    person = {
                        "name": name,
                        "phones": [],
                        "addresses": [],
                        "emails": [],
                        "public_records": [],
                        "confidence_sources": ["social_media"],
                        "phone_validation": {},
                        "phone_mentions": [],
                        "social_media": [profile],
                        "web_mentions": []
                    }

                    persons.append(person)

        return persons

    def _extract_from_web_mentions(self, web_mentions: List[Dict]) -> List[Dict]:
        """Extract persons from web mentions"""
        persons = []

        for mention in web_mentions:
            if not isinstance(mention, dict):
                continue

            # Try to extract name from title or snippet
            title = mention.get("title", "")
            snippet = mention.get("snippet", "")
            name = self._extract_name_from_text(title + " " + snippet)

            if name:
                person = {
                    "name": name,
                    "phones": [],
                    "addresses": [],
                    "emails": [],
                    "public_records": [],
                    "confidence_sources": ["web_mention"],
                    "phone_validation": {},
                    "phone_mentions": [],
                    "social_media": [],
                    "web_mentions": [mention]
                }

                persons.append(person)

        return persons

    def _create_person_from_input(self, search_params: Dict) -> Dict:
        """Create person record from user input"""
        person = {
            "name": search_params.get("name", ""),
            "phones": [],
            "addresses": [],
            "emails": [],
            "public_records": [],
            "confidence_sources": ["user_input"],
            "phone_validation": {},
            "phone_mentions": [],
            "social_media": [],
            "web_mentions": []
        }

        if search_params.get("phone"):
            person["phones"].append(search_params["phone"])

        if search_params.get("address"):
            person["addresses"].append(search_params["address"])

        if search_params.get("email"):
            person["emails"].append(search_params["email"])

        return person

    def _extract_name_from_text(self, text: str) -> str:
        """Extract likely person name from text"""
        # Simple extraction - look for capitalized words
        import re

        # Pattern: 2-3 capitalized words (likely a name)
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'
        match = re.search(pattern, text)

        if match:
            return match.group(1)

        return ""
