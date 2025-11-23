#!/usr/bin/env python3
"""
Phone Organizer
Professional-grade phone number organization
ONE JOB: Process, deduplicate, and organize phone numbers
"""

import re
import json
import os
from typing import Dict, List


class PhoneOrganizer:
    """
    Organizes phone numbers with:
    - Deduplication across all formats
    - Carrier and line type detection
    - Location data from area codes
    - Confidence scoring per phone
    - Source tracking
    - VOIP/suspicious number flagging
    """

    def __init__(self, confidence_scorer=None):
        """
        Initialize phone organizer.

        Args:
            confidence_scorer: ConfidenceScorer instance (optional)
        """
        self.confidence_scorer = confidence_scorer

        # Load area codes from external JSON file
        self.AREA_CODE_MAP = self._load_area_codes()

    def _load_area_codes(self) -> Dict:
        """Load area code database from JSON file"""
        try:
            # Get the directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, '..', 'data', 'area_codes.json')

            with open(json_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback to minimal hardcoded data if file not found
            return {
                "740": {"state": "OH", "city": "Southern/Eastern OH", "region": "Southeast OH"},
                "614": {"state": "OH", "city": "Columbus", "region": "Central OH"},
                "412": {"state": "PA", "city": "Pittsburgh", "region": "Southwest PA"},
                "304": {"state": "WV", "city": "Charleston", "region": "Central WV"}
            }
        except Exception as e:
            # Log error and use fallback
            print(f"Warning: Could not load area codes from JSON: {e}")
            return {}

    def organize_phones(self, person: Dict) -> List[Dict]:
        """
        Organize all phone numbers for a person.

        Args:
            person: Person dict with phones, phone_validation, phone_mentions

        Returns:
            List of organized phone dicts with full metadata
        """
        raw_phones = person.get("phones", [])
        phone_validation = person.get("phone_validation", {})
        phone_mentions = person.get("phone_mentions", [])

        if not raw_phones:
            return []

        # Deduplicate phones (same number, different formats)
        unique_phones = self._deduplicate_phones(raw_phones)

        organized = []

        for phone in unique_phones:
            # Format and normalize
            formatted = self.format_phone(phone)
            normalized = self.normalize_phone_for_comparison(phone)

            # Extract area code for location lookup
            area_code = self._extract_area_code(normalized)
            location = self._get_location_from_area_code(area_code) if area_code else {}

            # Determine confidence
            if self.confidence_scorer:
                confidence = self.confidence_scorer.calculate_phone_confidence(
                    phone,
                    person.get("confidence_sources", []),
                    phone_validation
                )
            else:
                confidence = "medium"

            # Detect line type and carrier
            line_type = phone_validation.get("line_type", "Unknown")
            carrier = phone_validation.get("carrier", "Unknown")

            # Check if VOIP or suspicious
            is_voip = 'voip' in line_type.lower() or 'toll-free' in line_type.lower()
            is_suspicious = self._is_suspicious_phone(normalized, phone_mentions)

            # Count sources
            source_count = sum(1 for mention in phone_mentions
                             if self.normalize_phone_for_comparison(mention.get("phone", "")) == normalized)

            phone_data = {
                "number": formatted,
                "normalized": normalized,
                "area_code": area_code,
                "location": location,
                "line_type": line_type,
                "carrier": carrier,
                "is_voip": is_voip,
                "is_suspicious": is_suspicious,
                "confidence": confidence,
                "confidence_percent": self._confidence_to_percent(confidence),
                "source_count": source_count,
                "sources": self._get_phone_sources(phone, person, phone_validation),
                "mentions": [m for m in phone_mentions
                           if self.normalize_phone_for_comparison(m.get("phone", "")) == normalized][:5]
            }

            organized.append(phone_data)

        # Sort by confidence (highest first)
        organized.sort(key=lambda x: x["confidence_percent"], reverse=True)

        return organized

    def _deduplicate_phones(self, phones: List[str]) -> List[str]:
        """Deduplicate phone numbers accounting for different formats"""
        seen_normalized = set()
        unique = []

        for phone in phones:
            normalized = self.normalize_phone_for_comparison(phone)
            if normalized and normalized not in seen_normalized:
                seen_normalized.add(normalized)
                unique.append(phone)

        return unique

    def normalize_phone_for_comparison(self, phone: str) -> str:
        """Normalize phone to digits only for comparison"""
        if not phone:
            return ""
        digits = re.sub(r'\D', '', phone)
        # Handle 10 vs 11 digit numbers (with/without country code)
        if len(digits) == 11 and digits[0] == '1':
            return digits[1:]  # Remove leading 1
        return digits

    def format_phone(self, phone: str) -> str:
        """Format phone number as (XXX) XXX-XXXX"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)

        # Format based on length
        if len(digits) == 11 and digits[0] == '1':
            # Remove leading 1 for US numbers
            digits = digits[1:]

        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11:
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        else:
            # Return original if can't format
            return phone

    def _extract_area_code(self, normalized_phone: str) -> str:
        """Extract area code from normalized phone"""
        if len(normalized_phone) >= 10:
            return normalized_phone[:3]
        return ""

    def _get_location_from_area_code(self, area_code: str) -> Dict:
        """Get location data from area code"""
        return self.AREA_CODE_MAP.get(area_code, {})

    def _is_suspicious_phone(self, normalized: str, mentions: List[Dict]) -> bool:
        """Detect if phone number might be suspicious/spam"""
        # Check for toll-free (often spam)
        if normalized[:3] in ['800', '888', '877', '866', '855', '844', '833']:
            return True

        # Check mentions for spam indicators
        for mention in mentions:
            snippet = mention.get("snippet", "").lower()
            if any(word in snippet for word in ['spam', 'scam', 'robocall', 'telemarketer']):
                return True

        return False

    def _get_phone_sources(self, phone: str, person: Dict, validation: Dict) -> List[str]:
        """Get list of sources where this phone was found"""
        sources = []

        if validation.get("valid"):
            sources.append("Phone Validation API")

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
