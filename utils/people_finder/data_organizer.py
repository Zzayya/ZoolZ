#!/usr/bin/env python3
"""
Data Organizer
Handles de-duplication, credibility scoring, and result organization
"""

import sqlite3
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re

# Import relationship detector
try:
    from .relationship_detector import RelationshipDetector
    RELATIONSHIP_DETECTION_AVAILABLE = True
except ImportError:
    RELATIONSHIP_DETECTION_AVAILABLE = False


class ResultOrganizer:
    """
    Organizes search results, removes duplicates, assigns confidence scores,
    and manages caching.
    """
    
    def __init__(self, db_path: str = "database/search_cache.db"):
        """
        Initialize organizer with SQLite cache database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_hash TEXT UNIQUE NOT NULL,
                search_params TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_params TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_search_hash(
        self,
        name: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str]
    ) -> str:
        """Generate unique hash for search parameters"""
        params = f"{name}|{phone}|{address}|{email}"
        return hashlib.md5(params.encode()).hexdigest()
    
    def check_cache(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        max_age_hours: int = 24
    ) -> Optional[Dict]:
        """
        Check if we have recent cached results for this search.
        
        Args:
            name, phone, address, email: Search parameters
            max_age_hours: Maximum age of cached results to accept
            
        Returns:
            Cached results dict or None if not found/expired
        """
        
        search_hash = self._generate_search_hash(name, phone, address, email)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT results FROM search_cache
            WHERE search_hash = ? AND expires_at > datetime('now')
        ''', (search_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        
        return None
    
    def cache_results(self, results: Dict, cache_duration_hours: int = 24):
        """
        Cache search results for future use.
        
        Args:
            results: Search results to cache
            cache_duration_hours: How long to keep cached (default 24 hours)
        """
        
        search_params = results.get("search_params", {})
        search_hash = self._generate_search_hash(
            search_params.get("name"),
            search_params.get("phone"),
            search_params.get("address"),
            search_params.get("email")
        )
        
        expires_at = datetime.now() + timedelta(hours=cache_duration_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO search_cache
                (search_hash, search_params, results, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (
                search_hash,
                json.dumps(search_params),
                json.dumps(results),
                expires_at
            ))
            
            conn.commit()
        
        finally:
            conn.close()
    
    def organize_results(
        self,
        official_results: Dict,
        web_results: Dict,
        search_params: Dict
    ) -> Dict:
        """
        Main organization function. Combines results, de-duplicates,
        and assigns confidence scores.
        
        Returns organized results by person with confidence scoring.
        """
        
        # Extract all persons found
        persons = self._extract_persons(official_results, web_results, search_params)
        
        # De-duplicate and merge person records
        unique_persons = self._deduplicate_persons(persons)
        
        # Score confidence for each data point
        for person in unique_persons:
            person["overall_confidence"] = self._calculate_overall_confidence(person)
            
            # Organize data by category with confidence
            person["organized_data"] = {
                "phone_numbers": self._organize_phones(person),
                "addresses": self._organize_addresses(person),
                "emails": self._organize_emails(person),
                "public_records": self._organize_public_records(person),
                "county_records": official_results.get("county_records", []),
                "federal_records": official_results.get("federal_records", {}),
                "social_media": self._organize_social_media(person),
                "web_mentions": self._organize_web_mentions(person)
            }
        
        # Sort by confidence
        unique_persons.sort(key=lambda p: p["overall_confidence"], reverse=True)

        # Detect relationships between persons (NEW FEATURE!)
        relationship_data = None
        if RELATIONSHIP_DETECTION_AVAILABLE and len(unique_persons) > 1:
            try:
                detector = RelationshipDetector()
                relationship_data = detector.analyze_relationships(unique_persons)

                # Add associates to each person's data
                associates_dict = relationship_data.get("associates", {})
                for person in unique_persons:
                    person["associates"] = self._get_person_associates(
                        person.get("name"),
                        associates_dict,
                        unique_persons
                    )
            except Exception as e:
                # Relationship detection failed - continue without it
                pass

        result = {
            "search_params": search_params,
            "total_persons_found": len(unique_persons),
            "persons": unique_persons,
            "search_timestamp": datetime.now().isoformat()
        }

        # Add relationship data if available
        if relationship_data:
            result["relationships"] = {
                "associates": relationship_data.get("associates", {}),
                "summary": relationship_data.get("relationship_summary", {}),
                "total_relationships": relationship_data.get("total_relationships", 0)
            }

        return result
    
    def _extract_persons(
        self,
        official_results: Dict,
        web_results: Dict,
        search_params: Dict
    ) -> List[Dict]:
        """
        Extract individual person records from all results.
        Each record represents a DISTINCT potential person match.
        We extract names from public records to create separate person entries.
        """

        persons = []

        # Start with search params as base person (if name provided)
        if search_params.get("name"):
            base_person = {
                "name": search_params["name"],
                "phones": [search_params["phone"]] if search_params.get("phone") else [],
                "addresses": [search_params["address"]] if search_params.get("address") else [],
                "emails": [search_params["email"]] if search_params.get("email") else [],
                "public_records": [],
                "social_media": [],
                "web_mentions": [],
                "phone_mentions": [],
                "confidence_sources": ["user_input"]
            }
            persons.append(base_person)

        # Extract from county records - each record may have a different person name
        for record in official_results.get("county_records", []):
            if isinstance(record, dict):
                # Extract name from "search_name" field
                record_name = record.get("search_name")
                if record_name and record_name != "N/A":
                    person = self._find_or_create_person(persons, record_name)
                    if "public_records" not in person:
                        person["public_records"] = []
                    person["public_records"].append(record)
                    if "public_records" not in person.get("confidence_sources", []):
                        if "confidence_sources" not in person:
                            person["confidence_sources"] = []
                        person["confidence_sources"].append("public_records")

        # Extract from federal records
        federal_records = official_results.get("federal_records", {})
        for category, records_list in federal_records.items():
            if isinstance(records_list, list):
                for record in records_list:
                    if isinstance(record, dict):
                        # Try to extract name from record
                        record_name = None
                        for key in ["name", "full_name", "person_name", "search_name"]:
                            if key in record and record[key] != "N/A":
                                record_name = record[key]
                                break

                        if record_name:
                            person = self._find_or_create_person(persons, record_name)
                            if "public_records" not in person:
                                person["public_records"] = []
                            person["public_records"].append(record)
                            if "public_records" not in person.get("confidence_sources", []):
                                if "confidence_sources" not in person:
                                    person["confidence_sources"] = []
                                person["confidence_sources"].append("public_records")

        # Add from phone validation (link to search name if available)
        phone_data = official_results.get("phone_data", {})
        if phone_data and phone_data.get("valid"):
            search_name = search_params.get("name")
            if search_name:
                person = self._find_or_create_person(persons, search_name)
                if "phones" not in person:
                    person["phones"] = []
                if phone_data.get("phone_number") not in person["phones"]:
                    person["phones"].append(phone_data.get("phone_number"))
                if "phone_validation" not in person:
                    person["phone_validation"] = phone_data
                if "phone_api" not in person.get("confidence_sources", []):
                    if "confidence_sources" not in person:
                        person["confidence_sources"] = []
                    person["confidence_sources"].append("phone_api")

        # Add from phone mentions (extract associated names)
        for phone_mention in web_results.get("phone_mentions", []):
            if isinstance(phone_mention, dict):
                # Check if this phone mention has associated names
                associated_names = phone_mention.get("associated_names", [])

                if associated_names:
                    # Create separate person entries for each associated name
                    for name in associated_names:
                        person = self._find_or_create_person(persons, name)
                        if "phone_mentions" not in person:
                            person["phone_mentions"] = []
                        person["phone_mentions"].append(phone_mention)
                        if "web_mention" not in person.get("confidence_sources", []):
                            if "confidence_sources" not in person:
                                person["confidence_sources"] = []
                            person["confidence_sources"].append("web_mention")
                else:
                    # No associated name - link to search name if available
                    search_name = search_params.get("name")
                    if search_name:
                        person = self._find_or_create_person(persons, search_name)
                        if "phone_mentions" not in person:
                            person["phone_mentions"] = []
                        person["phone_mentions"].append(phone_mention)

        # Add from web mentions
        for mention in web_results.get("web_mentions", []):
            search_name = search_params.get("name")
            if search_name:
                person = self._find_or_create_person(persons, search_name)
                if "web_mentions" not in person:
                    person["web_mentions"] = []
                person["web_mentions"].append(mention)
                if "web_mention" not in person.get("confidence_sources", []):
                    if "confidence_sources" not in person:
                        person["confidence_sources"] = []
                    person["confidence_sources"].append("web_mention")

        # Add from social media - extract profile names
        for social_link in web_results.get("social_media", []):
            if isinstance(social_link, dict):
                # Try to extract profile name from title
                profile_name = self._extract_profile_name_from_social(social_link)

                if profile_name:
                    person = self._find_or_create_person(persons, profile_name)
                else:
                    # Fallback to search name
                    search_name = search_params.get("name")
                    if search_name:
                        person = self._find_or_create_person(persons, search_name)
                    else:
                        continue

                if "social_media" not in person:
                    person["social_media"] = []
                person["social_media"].append(social_link)
                if "social_media" not in person.get("confidence_sources", []):
                    if "confidence_sources" not in person:
                        person["confidence_sources"] = []
                    person["confidence_sources"].append("social_media")

        return persons

    def _find_or_create_person(self, persons: List[Dict], name: str) -> Dict:
        """
        Find existing person by name or create new person entry.
        Uses strict name matching to avoid incorrectly merging different people.
        """

        # Normalize name for comparison
        name_normalized = name.lower().strip()

        # Search for existing person with this name
        for person in persons:
            person_name = person.get("name", "").lower().strip()

            # Strict name match (not fuzzy)
            if person_name == name_normalized:
                return person

        # Not found - create new person
        new_person = {
            "name": name,
            "phones": [],
            "addresses": [],
            "emails": [],
            "public_records": [],
            "social_media": [],
            "web_mentions": [],
            "phone_mentions": [],
            "confidence_sources": []
        }

        persons.append(new_person)
        return new_person

    def _extract_profile_name_from_social(self, social_link: Dict) -> Optional[str]:
        """
        Extract person name from social media profile title.
        Example: "John Smith | Facebook" → "John Smith"
        """

        title = social_link.get("title", "")

        if not title:
            return None

        # Common patterns to extract name
        # Remove platform names
        for platform in ["Facebook", "LinkedIn", "Twitter", "Instagram", "TikTok", "YouTube"]:
            title = title.replace(f" | {platform}", "")
            title = title.replace(f" - {platform}", "")
            title = title.replace(f" on {platform}", "")

        # Remove common suffixes
        title = re.sub(r'\s*\|\s*.*$', '', title)
        title = re.sub(r'\s*-\s*Profile$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(.*?\)\s*$', '', title)

        # Clean up
        title = title.strip()

        # Validate it looks like a name (2-4 words, capitalized)
        words = title.split()
        if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word):
            return title

        return None
    
    def _deduplicate_persons(self, persons: List[Dict]) -> List[Dict]:
        """
        Enhanced de-duplication with conservative merging and cross-referencing.

        Key changes from previous version:
        - MUCH more conservative about merging (requires strong evidence)
        - Uses cross-referencing to build confidence scores, not to merge
        - Only merges when exact name match + exact data match (phone/email/address)
        - Keeps people separate unless overwhelming evidence they're the same

        Cross-referencing logic:
        - If two people share an address → likely related but may be different people
        - If two people share phone + address → very likely same person → merge
        - If two people share email → very likely same person → merge
        - Similar names alone → NOT enough to merge (could be different people)
        """

        if not persons:
            return []

        unique = []

        for person in persons:
            merged = False

            # Try to merge with existing unique persons (very strict criteria)
            for existing in unique:
                if self._should_merge_persons(person, existing):
                    # MERGE - Strong evidence these are the same person
                    self._merge_person_data(existing, person)
                    merged = True
                    break
                elif self._are_related_persons(person, existing):
                    # CROSS-REFERENCE - They share some data but keep separate
                    # Add cross-reference note to boost confidence
                    self._add_cross_reference(existing, person)

            if not merged:
                # New distinct person
                unique.append(person)

        return unique

    def _should_merge_persons(self, person1: Dict, person2: Dict) -> bool:
        """
        Determine if two person records should be merged (very strict).

        Merge criteria (requires ALL of the following):
        1. EXACT name match (case-insensitive)
        2. At least ONE exact data match:
           - Exact phone number match
           - Exact email match
           - Exact address match

        This prevents incorrectly merging different people with similar names.
        """

        # Requirement 1: EXACT name match
        name1 = person1.get("name", "").lower().strip()
        name2 = person2.get("name", "").lower().strip()

        if not (name1 and name2 and name1 == name2):
            return False

        # Requirement 2: At least ONE exact data match

        # Check for exact phone match
        phones1 = set(person1.get("phones", []))
        phones2 = set(person2.get("phones", []))
        if phones1 & phones2:  # Intersection - shared phone
            return True

        # Check for exact email match
        emails1 = set(person1.get("emails", []))
        emails2 = set(person2.get("emails", []))
        if emails1 & emails2:  # Shared email
            return True

        # Check for exact address match (normalized)
        addresses1 = [addr.lower().strip() for addr in person1.get("addresses", [])]
        addresses2 = [addr.lower().strip() for addr in person2.get("addresses", [])]
        if set(addresses1) & set(addresses2):  # Shared address
            return True

        # No strong evidence - don't merge
        return False

    def _are_related_persons(self, person1: Dict, person2: Dict) -> bool:
        """
        Determine if two persons are related (share some data) but not the same person.
        Used for cross-referencing to boost confidence without merging.

        Examples:
        - Same address but different names → Roommates/family
        - Similar names but no shared data → Different people
        - Share one data point but names don't match → Related but distinct
        """

        # Different names
        name1 = person1.get("name", "").lower().strip()
        name2 = person2.get("name", "").lower().strip()

        if name1 != name2:
            # Check if they share any data
            phones1 = set(person1.get("phones", []))
            phones2 = set(person2.get("phones", []))
            if phones1 & phones2:
                return True

            addresses1 = [addr.lower().strip() for addr in person1.get("addresses", [])]
            addresses2 = [addr.lower().strip() for addr in person2.get("addresses", [])]
            if set(addresses1) & set(addresses2):
                return True

        return False

    def _merge_person_data(self, existing: Dict, new_person: Dict):
        """
        Merge data from new_person into existing person record.
        Combines all data fields.
        """

        # Merge phones
        existing["phones"] = list(set(
            existing.get("phones", []) + new_person.get("phones", [])
        ))

        # Merge addresses
        existing["addresses"] = list(set(
            existing.get("addresses", []) + new_person.get("addresses", [])
        ))

        # Merge emails
        existing["emails"] = list(set(
            existing.get("emails", []) + new_person.get("emails", [])
        ))

        # Merge public records
        existing["public_records"] = existing.get("public_records", []) + new_person.get("public_records", [])

        # Merge social media
        existing["social_media"] = existing.get("social_media", []) + new_person.get("social_media", [])

        # Merge web mentions
        existing["web_mentions"] = existing.get("web_mentions", []) + new_person.get("web_mentions", [])

        # Merge phone mentions
        existing["phone_mentions"] = existing.get("phone_mentions", []) + new_person.get("phone_mentions", [])

        # Merge confidence sources
        existing["confidence_sources"] = list(set(
            existing.get("confidence_sources", []) + new_person.get("confidence_sources", [])
        ))

        # Merge phone validation data if available
        if "phone_validation" in new_person and "phone_validation" not in existing:
            existing["phone_validation"] = new_person["phone_validation"]

    def _add_cross_reference(self, person1: Dict, person2: Dict):
        """
        Add cross-reference information between related persons.
        This boosts confidence without merging the records.

        Example: If "John Smith" and "Jane Smith" share an address,
        we note they're related but keep them as separate people.
        """

        if "cross_references" not in person1:
            person1["cross_references"] = []

        person1["cross_references"].append({
            "related_person": person2.get("name", "Unknown"),
            "relationship_type": "shared_data",
            "shared_data": self._identify_shared_data(person1, person2)
        })

    def _identify_shared_data(self, person1: Dict, person2: Dict) -> List[str]:
        """
        Identify what data is shared between two persons.
        Used for cross-referencing and confidence scoring.

        Returns list of shared data types:
        - "phone": Share phone number
        - "email": Share email
        - "address": Share address
        """

        shared = []

        # Check for shared phones
        phones1 = set(person1.get("phones", []))
        phones2 = set(person2.get("phones", []))
        if phones1 & phones2:
            shared.append("phone")

        # Check for shared emails
        emails1 = set(person1.get("emails", []))
        emails2 = set(person2.get("emails", []))
        if emails1 & emails2:
            shared.append("email")

        # Check for shared addresses (normalized)
        addresses1 = [addr.lower().strip() for addr in person1.get("addresses", [])]
        addresses2 = [addr.lower().strip() for addr in person2.get("addresses", [])]
        if set(addresses1) & set(addresses2):
            shared.append("address")

        return shared

    def _names_match(self, name1: str, name2: str) -> bool:
        """
        Enhanced name matching that handles:
        - Middle initials: "John A Smith" vs "John Andrew Smith"
        - Missing middle names: "John Smith" vs "John A Smith"
        - Different name orders
        - Simple typos

        Returns True if names likely represent the same person.
        """

        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Exact match
        if name1 == name2:
            return True

        # Split into parts
        parts1 = name1.split()
        parts2 = name2.split()

        # Need at least first and last name
        if len(parts1) < 2 or len(parts2) < 2:
            # Fuzzy match if we don't have enough parts
            return SequenceMatcher(None, name1, name2).ratio() > 0.85

        # Extract first and last names (assuming last name is last part)
        first1, last1 = parts1[0], parts1[-1]
        first2, last2 = parts2[0], parts2[-1]

        # First and last names must match closely
        first_match = SequenceMatcher(None, first1, first2).ratio() > 0.85
        last_match = SequenceMatcher(None, last1, last2).ratio() > 0.85

        if not (first_match and last_match):
            return False

        # If we have middle names/initials, check them
        if len(parts1) > 2 and len(parts2) > 2:
            middle1 = ' '.join(parts1[1:-1])
            middle2 = ' '.join(parts2[1:-1])

            # Check if one is an initial of the other
            if self._is_initial_match(middle1, middle2):
                return True

            # Check if middles are similar
            if SequenceMatcher(None, middle1, middle2).ratio() > 0.8:
                return True

            # Different middles, but first/last match - still likely same person
            return True

        # One has middle name, one doesn't - still a match if first/last match
        return True

    def _is_initial_match(self, name1: str, name2: str) -> bool:
        """
        Check if one name is an initial/abbreviation of the other.
        Examples:
        - "a" matches "andrew"
        - "j" matches "john"
        - "a j" matches "andrew james"
        """

        # Clean up
        name1 = name1.strip().lower()
        name2 = name2.strip().lower()

        # Check if one is a single letter (initial)
        if len(name1) == 1:
            return name2.startswith(name1)
        if len(name2) == 1:
            return name1.startswith(name2)

        # Check if both are single letters
        if len(name1) == 1 and len(name2) == 1:
            return name1 == name2

        # Check multi-part initials (e.g., "a j" vs "andrew james")
        parts1 = name1.split()
        parts2 = name2.split()

        # If one is all single letters (initials)
        if all(len(p) == 1 for p in parts1):
            # Check if each initial matches the start of corresponding part2
            if len(parts1) <= len(parts2):
                return all(p2.startswith(p1) for p1, p2 in zip(parts1, parts2))

        if all(len(p) == 1 for p in parts2):
            # Check if each initial matches the start of corresponding part1
            if len(parts2) <= len(parts1):
                return all(p1.startswith(p2) for p1, p2 in zip(parts1, parts2))

        return False

    def _calculate_overall_confidence(self, person: Dict) -> float:
        """
        Enhanced confidence scoring with cross-referencing support.

        Confidence calculation:
        - Base scores from data sources (user input, public records, etc.)
        - Bonus for multiple data points (phones, addresses, emails)
        - Bonus for cross-references (shared data with other persons)
        - Higher confidence = more likely to be accurate match

        Scale: 0-100%
        - 70-100%: High confidence (multiple verified sources)
        - 40-69%: Medium confidence (some sources, needs verification)
        - 0-39%: Low confidence (unverified web mentions only)
        """

        score = 0.0

        # Base source weights
        source_weights = {
            "user_input": 30,          # User-provided data (highest initial weight)
            "public_records": 25,      # Official government records
            "phone_api": 20,           # Validated phone number
            "verified_email": 15,      # Verified email address
            "social_media": 5,         # Social media profile (unverified)
            "web_mention": 3           # Web mention (lowest confidence)
        }

        # Add source scores
        for source in person.get("confidence_sources", []):
            score += source_weights.get(source, 1)

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
            # Each cross-reference adds confidence
            score += min(len(cross_refs) * 5, 10)  # Up to +10 for cross-references

        # Cap at 100
        return min(score, 100.0)
    
    def _organize_phones(self, person: Dict) -> List[Dict]:
        """Organize phone numbers with metadata"""
        phones = []
        for phone in person.get("phones", []):
            phones.append({
                "number": phone,
                "formatted": self._format_phone(phone),
                "confidence": "high" if "phone_api" in person.get("confidence_sources", []) else "medium",
                "source": "Validated" if "phone_api" in person.get("confidence_sources", []) else "Found"
            })
        return phones

    def _format_phone(self, phone: str) -> str:
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
    
    def _organize_addresses(self, person: Dict) -> List[Dict]:
        """Organize addresses with metadata"""
        addresses = []
        for address in person.get("addresses", []):
            addresses.append({
                "full_address": address,
                "confidence": "high" if "public_records" in person.get("confidence_sources", []) else "medium"
            })
        return addresses
    
    def _organize_emails(self, person: Dict) -> List[Dict]:
        """Organize emails with metadata"""
        emails = []
        for email in person.get("emails", []):
            emails.append({
                "email": email,
                "confidence": "medium"
            })
        return emails
    
    def _organize_public_records(self, person: Dict) -> List[Dict]:
        """Organize public records with high confidence flag"""
        records = person.get("public_records", [])
        for record in records:
            if isinstance(record, dict):
                record["confidence"] = "high"
                record["verified"] = True
        return records
    
    def _organize_social_media(self, person: Dict) -> List[Dict]:
        """Organize social media with LOW confidence flag"""
        social = person.get("social_media", [])
        for link in social:
            if isinstance(link, dict):
                link["confidence"] = "low"
                link["requires_verification"] = True
        return social
    
    def _organize_web_mentions(self, person: Dict) -> List[Dict]:
        """Organize web mentions with LOW confidence flag"""
        mentions = person.get("web_mentions", [])
        for mention in mentions:
            if isinstance(mention, dict):
                mention["confidence"] = "low"
                mention["requires_verification"] = True
        return mentions
    
    def _person_from_public_record(self, record: Dict) -> Optional[Dict]:
        """Extract person data from a public record"""
        # This depends on record format - stub for now
        return None
    
    def _person_from_web_mention(self, mention: Dict, search_params: Dict) -> Optional[Dict]:
        """Extract person data from web mention"""
        return {
            "name": search_params.get("name", "Unknown"),
            "phones": [],
            "addresses": [],
            "emails": [],
            "public_records": [],
            "social_media": [],
            "web_mentions": [mention],
            "confidence_sources": ["web_mention"]
        }
    
    def _person_from_social_link(self, social_link: Dict, search_params: Dict) -> Optional[Dict]:
        """Extract person data from social media link"""
        return {
            "name": search_params.get("name", "Unknown"),
            "phones": [],
            "addresses": [],
            "emails": [],
            "public_records": [],
            "social_media": [social_link],
            "web_mentions": [],
            "confidence_sources": ["social_media"]
        }

    def _get_person_associates(
        self,
        person_name: Optional[str],
        associates_dict: Dict,
        all_persons: List[Dict]
    ) -> Dict:
        """
        Get all associates for a specific person, organized by relationship type.

        Returns:
            Dict with associates grouped by category:
            - immediate_family
            - possible_spouse
            - possible_parent
            - possible_child
            - possible_sibling
            - roommate
            - business_associate
            - close_contact
            - possible_friend
        """

        if not person_name:
            return {}

        person_associates = {}

        # Check each relationship category
        for category, relationships in associates_dict.items():
            person_associates[category] = []

            for rel in relationships:
                # Check if this person is involved in this relationship
                if rel.get("person1") == person_name or rel.get("person2") == person_name:
                    # Get the other person's name
                    other_person_name = rel.get("person2") if rel.get("person1") == person_name else rel.get("person1")

                    # Find full person data
                    other_person_data = None
                    for p in all_persons:
                        if p.get("name") == other_person_name:
                            other_person_data = p
                            break

                    person_associates[category].append({
                        "name": other_person_name,
                        "relationship_indicators": rel.get("relationship_indicators", []),
                        "strength": rel.get("strength", 0.0),
                        "shared_data": rel.get("shared_data", {}),
                        "confidence": other_person_data.get("overall_confidence", 0) if other_person_data else 0
                    })

        return person_associates

    def clear_old_cache(self, days: int = 7):
        """Remove cache entries older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM search_cache
            WHERE expires_at < datetime('now')
        ''')
        
        conn.commit()
        conn.close()
