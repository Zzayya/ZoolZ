#!/usr/bin/env python3
"""
Trail Follower - Iterative Deep Search
Follows the trail by searching associates, then their associates, building a network
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
import time


class TrailFollower:
    """
    Performs iterative deep searches by "following the trail":
    1. Search initial person
    2. Find their associates (people at same address, same phone, etc.)
    3. Search each associate
    4. Find THEIR associates
    5. Continue up to max_depth levels
    6. Build comprehensive relationship network

    This is how professional skip tracing works - following breadcrumbs!
    """

    def __init__(self, orchestrator):
        """
        Args:
            orchestrator: SearchOrchestrator instance to perform searches
        """
        self.orchestrator = orchestrator
        self.searched_names = set()  # Track who we've searched to avoid duplicates
        self.all_persons_found = []  # All unique persons discovered
        self.search_trail = []  # Log of search path taken

    async def follow_trail(
        self,
        initial_name: str,
        initial_phone: Optional[str] = None,
        initial_address: Optional[str] = None,
        initial_email: Optional[str] = None,
        state: Optional[str] = None,
        county: Optional[str] = None,
        max_depth: int = 2,
        max_associates: int = 10,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Follow the trail starting from initial person.

        Args:
            initial_name: Starting person's name
            initial_phone, initial_address, initial_email: Starting person's info
            state, county: Location filters
            max_depth: How many degrees of separation to search (1-3 recommended)
            max_associates: Max associates to search at each level (prevent explosion)
            progress_callback: Function to call with progress updates

        Returns:
            Dict with:
            - all_persons: All people found
            - search_trail: Path taken through searches
            - relationship_network: Connections between people
            - search_summary: Statistics
        """

        if progress_callback:
            progress_callback(f"🔍 Starting trail following from '{initial_name}'...", 0)

        # Reset state
        self.searched_names = set()
        self.all_persons_found = []
        self.search_trail = []

        # Level 0: Initial search
        if progress_callback:
            progress_callback(f"[Level 0] Searching '{initial_name}' (initial person)...", 5)

        initial_results = await self._search_person(
            name=initial_name,
            phone=initial_phone,
            address=initial_address,
            email=initial_email,
            state=state,
            county=county,
            depth_level=0
        )

        # Add initial person to trail
        self.search_trail.append({
            "level": 0,
            "person_searched": initial_name,
            "reason": "Initial search",
            "timestamp": datetime.now().isoformat(),
            "persons_found": len(initial_results.get("persons", []))
        })

        # Extract all persons from initial search
        initial_persons = initial_results.get("persons", [])
        self.all_persons_found.extend(initial_persons)

        # Mark initial names as searched
        for person in initial_persons:
            self.searched_names.add(person.get("name", "").lower())

        # Follow the trail through associates
        if max_depth > 0:
            await self._follow_associates_recursively(
                current_persons=initial_persons,
                current_depth=1,
                max_depth=max_depth,
                max_associates=max_associates,
                state=state,
                county=county,
                progress_callback=progress_callback
            )

        # Build final results
        if progress_callback:
            progress_callback("📊 Building relationship network...", 95)

        final_results = self._build_comprehensive_results()

        if progress_callback:
            progress_callback(f"✅ Trail following complete! Found {len(self.all_persons_found)} people.", 100)

        return final_results

    async def _follow_associates_recursively(
        self,
        current_persons: List[Dict],
        current_depth: int,
        max_depth: int,
        max_associates: int,
        state: Optional[str],
        county: Optional[str],
        progress_callback: Optional[callable]
    ):
        """
        Recursively follow associates up to max_depth.
        """

        if current_depth > max_depth:
            return

        if progress_callback:
            progress_callback(
                f"[Level {current_depth}] Analyzing {len(current_persons)} people for associates...",
                20 + (current_depth * 30)
            )

        # Find all associates from current level
        associates_to_search = self._find_unsearched_associates(
            current_persons,
            max_associates
        )

        if not associates_to_search:
            if progress_callback:
                progress_callback(f"[Level {current_depth}] No new associates found.", 20 + (current_depth * 30) + 10)
            return

        if progress_callback:
            progress_callback(
                f"[Level {current_depth}] Found {len(associates_to_search)} associates to search...",
                20 + (current_depth * 30) + 15
            )

        # Search each associate
        next_level_persons = []

        for idx, associate in enumerate(associates_to_search, 1):
            associate_name = associate["name"]
            reason = associate["reason"]

            if progress_callback:
                progress_callback(
                    f"[Level {current_depth}] Searching associate {idx}/{len(associates_to_search)}: '{associate_name}' ({reason})...",
                    20 + (current_depth * 30) + 15 + (idx / len(associates_to_search) * 10)
                )

            # Search this associate
            associate_results = await self._search_person(
                name=associate_name,
                phone=associate.get("phone"),
                address=associate.get("address"),
                state=state,
                county=county,
                depth_level=current_depth
            )

            # Log search
            self.search_trail.append({
                "level": current_depth,
                "person_searched": associate_name,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "persons_found": len(associate_results.get("persons", []))
            })

            # Add newly found persons
            for person in associate_results.get("persons", []):
                person_name_lower = person.get("name", "").lower()

                # Only add if not already in our list
                if not any(p.get("name", "").lower() == person_name_lower for p in self.all_persons_found):
                    self.all_persons_found.append(person)
                    next_level_persons.append(person)

            # Mark as searched
            self.searched_names.add(associate_name.lower())

            # Small delay to be polite
            await asyncio.sleep(0.5)

        # Recursively search next level
        if next_level_persons and current_depth < max_depth:
            await self._follow_associates_recursively(
                current_persons=next_level_persons,
                current_depth=current_depth + 1,
                max_depth=max_depth,
                max_associates=max_associates,
                state=state,
                county=county,
                progress_callback=progress_callback
            )

    def _find_unsearched_associates(
        self,
        persons: List[Dict],
        max_associates: int
    ) -> List[Dict]:
        """
        Find associates who haven't been searched yet.

        Associates are people who:
        - Share an address (family, roommates)
        - Share a phone number (family, close contacts)
        - Are mentioned in records (co-owners, business partners)
        """

        associates = []

        for person in persons:
            # Extract potential associates from shared addresses
            addresses = person.get("addresses", [])
            for address in addresses:
                # Look for other people at this address in records
                associates.extend(self._extract_associates_from_address(person, address))

            # Extract associates from phone mentions
            phone_mentions = person.get("phone_mentions", [])
            for mention in phone_mentions:
                associated_names = mention.get("associated_names", [])
                for name in associated_names:
                    if name.lower() not in self.searched_names:
                        associates.append({
                            "name": name,
                            "reason": f"Linked to phone {mention.get('url', '')}",
                            "phone": None,
                            "address": None
                        })

            # Extract associates from public records (co-owners, etc.)
            associates.extend(self._extract_associates_from_records(person))

            # Extract associates from social media (tagged friends, etc.)
            associates.extend(self._extract_associates_from_social(person))

        # Deduplicate associates
        unique_associates = self._deduplicate_associates(associates)

        # Limit to max_associates to prevent explosion
        return unique_associates[:max_associates]

    def _extract_associates_from_address(self, person: Dict, address: str) -> List[Dict]:
        """
        Look through all found persons for others at same address.
        """

        associates = []
        person_name_lower = person.get("name", "").lower()

        for other_person in self.all_persons_found:
            other_name = other_person.get("name", "")
            other_name_lower = other_name.lower()

            # Skip self and already searched
            if other_name_lower == person_name_lower or other_name_lower in self.searched_names:
                continue

            # Check if this person has the same address
            other_addresses = [addr.lower() for addr in other_person.get("addresses", [])]
            if address.lower() in other_addresses:
                associates.append({
                    "name": other_name,
                    "reason": f"Lives at same address: {address}",
                    "phone": other_person.get("phones", [None])[0] if other_person.get("phones") else None,
                    "address": address
                })

        return associates

    def _extract_associates_from_records(self, person: Dict) -> List[Dict]:
        """
        Extract associate names mentioned in public records.
        Look for co-owners, business partners, etc.
        """

        associates = []
        records = person.get("public_records", [])

        for record in records:
            if not isinstance(record, dict):
                continue

            # Look for other names in record text
            record_text = str(record)

            # Simple name extraction (capitalized words)
            import re
            potential_names = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', record_text)

            for name in potential_names:
                name_lower = name.lower()

                # Skip if already searched or is current person
                if name_lower in self.searched_names or name_lower == person.get("name", "").lower():
                    continue

                # Check if looks like a real name (not title/place)
                if self._is_likely_person_name(name):
                    associates.append({
                        "name": name,
                        "reason": f"Mentioned in {record.get('type', 'public')} record",
                        "phone": None,
                        "address": None
                    })

        return associates

    def _extract_associates_from_social(self, person: Dict) -> List[Dict]:
        """
        Extract potential associates from social media mentions.
        """

        associates = []
        social_media = person.get("social_media", [])

        for link in social_media:
            if not isinstance(link, dict):
                continue

            # Look for tagged/mentioned names in social media snippets
            snippet = link.get("snippet", "")
            title = link.get("title", "")
            text = snippet + " " + title

            # Extract names
            import re
            potential_names = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', text)

            for name in potential_names:
                name_lower = name.lower()

                if name_lower in self.searched_names or name_lower == person.get("name", "").lower():
                    continue

                if self._is_likely_person_name(name):
                    associates.append({
                        "name": name,
                        "reason": f"Mentioned with {person.get('name')} on social media",
                        "phone": None,
                        "address": None
                    })

        return associates

    def _is_likely_person_name(self, name: str) -> bool:
        """
        Check if a string is likely a person's name.
        Filter out titles, places, organizations.
        """

        name_lower = name.lower()

        # Exclude common non-person words
        excluded = {
            'united states', 'customer service', 'home page', 'contact us',
            'about us', 'privacy policy', 'terms service', 'copyright',
            'all rights', 'rights reserved'
        }

        if name_lower in excluded:
            return False

        # Must have 2-3 words
        words = name.split()
        if len(words) < 2 or len(words) > 3:
            return False

        # Each word should be reasonably short (names are typically 2-12 chars)
        if any(len(word) < 2 or len(word) > 15 for word in words):
            return False

        return True

    def _deduplicate_associates(self, associates: List[Dict]) -> List[Dict]:
        """Remove duplicate associates"""

        seen_names = set()
        unique = []

        for associate in associates:
            name_lower = associate["name"].lower()

            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique.append(associate)

        return unique

    async def _search_person(
        self,
        name: str,
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str] = None,
        state: Optional[str] = None,
        county: Optional[str] = None,
        depth_level: int = 0
    ) -> Dict:
        """
        Perform a single person search.
        """

        try:
            results = await self.orchestrator.search_person(
                name=name,
                phone=phone,
                address=address,
                email=email,
                state=state,
                county=county,
                progress_callback=None  # Don't pass sub-progress to avoid clutter
            )

            return results

        except Exception as e:
            return {
                "persons": [],
                "error": str(e),
                "search_params": {"name": name}
            }

    def _build_comprehensive_results(self) -> Dict:
        """
        Build final comprehensive results with all discovered data.
        """

        return {
            "all_persons": self.all_persons_found,
            "total_persons_found": len(self.all_persons_found),
            "total_searches_performed": len(self.search_trail),
            "search_trail": self.search_trail,
            "search_summary": {
                "unique_persons": len(self.all_persons_found),
                "total_searches": len(self.search_trail),
                "max_depth_reached": max(trail["level"] for trail in self.search_trail) if self.search_trail else 0
            },
            "timestamp": datetime.now().isoformat()
        }
