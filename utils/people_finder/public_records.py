#!/usr/bin/env python3
"""
Public Records Searcher
Searches court websites, county records, and federal databases
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re

# Import our county and federal databases
from .county_portals import (
    get_county_portal,
    get_all_counties_for_state,
    OHIO_COUNTIES,
    PENNSYLVANIA_COUNTIES,
    WEST_VIRGINIA_COUNTIES
)
from .federal_records import FederalRecordsSearcher


class PublicRecordsSearcher:
    """
    Handles searches across public record databases.
    Integrates county-level and federal searches with polite rate limiting.
    """

    def __init__(self):
        self.session = None
        self.rate_limit_delay = 12  # 12 seconds between requests (VERY POLITE)
        self.federal_searcher = FederalRecordsSearcher()

    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36"
                }
            )
        return self.session

    async def search_comprehensive(
        self,
        name: Optional[str] = None,
        address: Optional[str] = None,
        state: Optional[str] = None,
        county: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Comprehensive search across county AND federal records.

        Args:
            name: Person's full name
            address: Address (used to identify county)
            state: Two-letter state code (OH, PA, WV) - if None, searches all
            county: County name (optional - if provided, only searches that county)
            **kwargs: Additional search parameters

        Returns:
            Dict with county_records and federal_records
        """

        results = {
            "county_records": [],
            "federal_records": {},
            "search_params": {
                "name": name,
                "address": address,
                "state": state,
                "county": county
            },
            "search_timestamp": datetime.now().isoformat(),
            "total_sources_searched": 0
        }

        # Determine which states to search
        states_to_search = []
        if state and state.upper() in ["OH", "PA", "WV"]:
            states_to_search = [state.upper()]
        else:
            states_to_search = ["OH", "PA", "WV"]  # All priority states

        # Use provided county, or extract from address if not provided
        target_county = county if county else (self._extract_county_from_address(address) if address else None)

        # Search county records
        for search_state in states_to_search:
            county_results = await self._search_state_counties(
                search_state,
                name,
                address,
                target_county
            )
            results["county_records"].extend(county_results)
            results["total_sources_searched"] += len(county_results)

            # Polite delay between states
            await asyncio.sleep(self.rate_limit_delay)

        # Search federal records
        federal_results = await self.federal_searcher.search_federal_records(
            name=name,
            address=address,
            **kwargs
        )
        results["federal_records"] = federal_results
        results["total_sources_searched"] += self._count_federal_sources(federal_results)

        return results

    async def _search_state_counties(
        self,
        state: str,
        name: Optional[str],
        address: Optional[str],
        target_county: Optional[str] = None
    ) -> List[Dict]:
        """
        Search county records for a specific state.

        Args:
            state: OH, PA, or WV
            name: Person's name
            address: Address
            target_county: Specific county to search (if known), otherwise searches all

        Returns:
            List of county record results
        """

        county_results = []

        # Get all counties for this state
        all_counties = get_all_counties_for_state(state)

        # If we have a target county, only search that one
        # Otherwise, search ALL counties for the state (user wants comprehensive search)
        if target_county and target_county in all_counties:
            counties_to_search = [target_county]
        else:
            # Search ALL counties when state is selected but no specific county chosen
            counties_to_search = all_counties

        # Search each county
        for county in counties_to_search:
            # Court records
            court_portal = get_county_portal(state, county, "courts")
            if court_portal:
                county_results.append({
                    "type": "county_court_records",
                    "state": state,
                    "county": county,
                    "source": f"{county} County Clerk of Courts",
                    "url": court_portal["url"],
                    "notes": court_portal["notes"],
                    "search_name": name if name else "N/A",
                    "confidence": "manual_required",
                    "auto_fill_available": True
                })

            # Property records
            property_portal = get_county_portal(state, county, "property")
            if property_portal:
                county_results.append({
                    "type": "county_property_records",
                    "state": state,
                    "county": county,
                    "source": f"{county} County Auditor/Assessor",
                    "url": property_portal["url"],
                    "notes": property_portal["notes"],
                    "search_address": address if address else "N/A",
                    "confidence": "manual_required",
                    "auto_fill_available": True
                })

        return county_results

    def _extract_county_from_address(self, address: str) -> Optional[str]:
        """Try to extract county name from address string"""

        if not address:
            return None

        # Common county patterns
        county_pattern = r'([A-Z][a-z]+)\s+County'
        match = re.search(county_pattern, address, re.IGNORECASE)

        if match:
            return match.group(1).title()

        # Try to match known county names
        address_upper = address.upper()

        # Check Ohio counties
        for county in OHIO_COUNTIES.keys():
            if county.upper() in address_upper:
                return county

        # Check Pennsylvania counties
        for county in PENNSYLVANIA_COUNTIES.keys():
            if county.upper() in address_upper:
                return county

        # Check West Virginia counties
        for county in WEST_VIRGINIA_COUNTIES.keys():
            if county.upper() in address_upper:
                return county

        return None

    def _count_federal_sources(self, federal_results: Dict) -> int:
        """Count total number of federal sources in results"""
        count = 0
        for category in federal_results.values():
            if isinstance(category, list):
                count += len(category)
        return count

    async def get_auto_fill_form_data(
        self,
        state: str,
        county: str,
        record_type: str,
        search_params: Dict
    ) -> Dict:
        """
        Generate pre-filled form data for manual county submission.

        Args:
            state: Two-letter state code
            county: County name
            record_type: "courts" or "property"
            search_params: Dict with name, address, phone, etc.

        Returns:
            Dict with portal URL and auto-fill field values
        """

        portal_info = get_county_portal(state, county, record_type)

        if not portal_info:
            return {
                "error": f"County {county}, {state} not found",
                "state": state,
                "county": county
            }

        form_data = {
            "state": state,
            "county": county,
            "record_type": record_type,
            "portal_url": portal_info["url"],
            "notes": portal_info["notes"],
            "fields": {}
        }

        # Map our search params to common form field names
        if "name" in search_params and search_params["name"]:
            name_parts = search_params["name"].split()
            if len(name_parts) >= 2:
                form_data["fields"]["firstName"] = name_parts[0]
                form_data["fields"]["lastName"] = " ".join(name_parts[1:])
            else:
                form_data["fields"]["fullName"] = search_params["name"]

        if "address" in search_params and search_params["address"]:
            form_data["fields"]["address"] = search_params["address"]

        if "phone" in search_params and search_params["phone"]:
            form_data["fields"]["phone"] = search_params["phone"]

        if "email" in search_params and search_params["email"]:
            form_data["fields"]["email"] = search_params["email"]

        return form_data

    async def get_statistics(self) -> Dict:
        """Get statistics about available data sources"""

        federal_stats = self.federal_searcher.get_all_federal_sources()

        return {
            "county_sources": {
                "ohio_counties": len(OHIO_COUNTIES),
                "pennsylvania_counties": len(PENNSYLVANIA_COUNTIES),
                "west_virginia_counties": len(WEST_VIRGINIA_COUNTIES),
                "total_counties": len(OHIO_COUNTIES) + len(PENNSYLVANIA_COUNTIES) + len(WEST_VIRGINIA_COUNTIES)
            },
            "federal_sources": {
                "total": federal_stats["total_sources"],
                "by_category": federal_stats["by_category"]
            },
            "grand_total_sources": (
                (len(OHIO_COUNTIES) + len(PENNSYLVANIA_COUNTIES) + len(WEST_VIRGINIA_COUNTIES)) * 2 +  # courts + property per county
                federal_stats["total_sources"]
            )
        }

    async def close(self):
        """Clean up sessions"""
        if self.session:
            await self.session.close()
        await self.federal_searcher.close()


# Standalone helper function for quick county lookup
def find_county_portal(state: str, county: str, record_type: str = "courts") -> Optional[str]:
    """
    Quick lookup for county portal URL.

    Args:
        state: OH, PA, or WV
        county: County name
        record_type: "courts" or "property"

    Returns:
        URL string or None
    """
    portal_info = get_county_portal(state, county, record_type)
    return portal_info["url"] if portal_info else None
