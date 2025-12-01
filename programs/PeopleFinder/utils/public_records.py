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
from .site_scraper import CountySiteScraper


class PublicRecordsSearcher:
    """
    Handles searches across public record databases.
    Integrates county-level and federal searches with polite rate limiting.
    """

    def __init__(self):
        self.session = None
        self.rate_limit_delay = 12  # 12 seconds between requests (VERY POLITE)
        self.federal_searcher = FederalRecordsSearcher()
        self.site_scraper = CountySiteScraper(timeout=15, max_retries=2)

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
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> Dict:
        """
        Comprehensive search across county AND federal records.
        Counties are searched SEQUENTIALLY in alphabetical order across all states.

        Args:
            name: Person's full name
            address: Address (used to identify county)
            state: Two-letter state code (OH, PA, WV) or list of states - if None, searches all
            county: County name (optional - if provided, only searches that county)
            progress_callback: Optional callback function(message, percent) for progress updates
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

        # Determine which states to search - support multiple states!
        states_to_search = []
        if state:
            # Handle comma-separated states: "OH,PA,WV" or list ["OH", "PA"]
            if isinstance(state, str):
                states_to_search = [s.strip().upper() for s in state.split(',') if s.strip().upper() in ["OH", "PA", "WV", "IN", "IL", "KY", "TN"]]
            elif isinstance(state, list):
                states_to_search = [s.upper() for s in state if s.upper() in ["OH", "PA", "WV", "IN", "IL", "KY", "TN"]]

        if not states_to_search:
            states_to_search = ["OH", "PA", "WV"]  # Default priority states

        # VALIDATION: Remove duplicate states
        states_to_search = list(set(states_to_search))

        # Use provided county, or extract from address if not provided
        target_county = county if county else (self._extract_county_from_address(address) if address else None)

        # BUILD ALPHABETICAL COUNTY LIST ACROSS ALL STATES
        all_counties_list = []
        for search_state in states_to_search:
            try:
                state_counties = get_all_counties_for_state(search_state)
                if state_counties:
                    # Add each county with its state
                    for county_name in state_counties:
                        all_counties_list.append({
                            "county": county_name,
                            "state": search_state
                        })
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ Error loading counties for {search_state}", 5)
                continue

        # If specific county requested, filter to just that one
        if target_county:
            all_counties_list = [c for c in all_counties_list if c["county"].lower() == target_county.lower()]

        # SORT ALPHABETICALLY BY COUNTY NAME (across all states!)
        all_counties_list.sort(key=lambda x: (x["county"].lower(), x["state"]))

        total_counties = len(all_counties_list)

        # VALIDATION: Sanity check on county count (prevent explosions from bad input)
        if total_counties > 500:
            error_msg = f"County list unexpectedly large ({total_counties} counties). Check for data errors."
            if progress_callback:
                progress_callback(f"❌ {error_msg}", 5)
            raise ValueError(error_msg)

        if progress_callback:
            progress_callback(f"📋 Prepared {total_counties} counties across {len(states_to_search)} state(s) for sequential search", 8)

        # SEARCH COUNTIES ONE AT A TIME IN ALPHABETICAL ORDER
        for county_idx, county_data in enumerate(all_counties_list, 1):
            county_name = county_data["county"]
            county_state = county_data["state"]

            try:
                # Calculate progress (10-50% reserved for county searches)
                current_progress = 10 + (county_idx / total_counties) * 40

                # ENHANCED PROGRESS MESSAGE - Show exactly what's being searched
                if progress_callback:
                    progress_callback(
                        f"🔍 County {county_idx} of {total_counties}: {county_name} County, {county_state}",
                        current_progress
                    )

                # Search THIS specific county
                county_results = await self._search_single_county(
                    county_state,
                    county_name,
                    name,
                    address,
                    progress_callback=progress_callback,
                    county_number=county_idx,
                    total_counties=total_counties
                )

                results["county_records"].extend(county_results)
                results["total_sources_searched"] += len(county_results)

            except Exception as e:
                # If a county search fails, log but continue to next
                if progress_callback:
                    progress_callback(
                        f"⚠️ Skipped {county_name} County, {county_state} due to error",
                        current_progress
                    )
                continue

        if progress_callback:
            progress_callback("✅ All county searches complete! Starting federal records scan...", 55)

        # ALWAYS search federal records (automatic - no matter what!)
        try:
            federal_results = await self.federal_searcher.search_federal_records(
                name=name,
                address=address,
                progress_callback=progress_callback,
                **kwargs
            )
            results["federal_records"] = federal_results
            results["total_sources_searched"] += self._count_federal_sources(federal_results)
        except Exception as e:
            # If federal search fails, log but don't crash entire search
            if progress_callback:
                progress_callback("⚠️ Federal records scan encountered an error - continuing...", 58)
            results["federal_records"] = {}

        if progress_callback:
            progress_callback("✅ Federal records scan complete!", 60)

        return results

    async def _search_single_county(
        self,
        state: str,
        county: str,
        name: Optional[str],
        address: Optional[str],
        progress_callback: Optional[callable] = None,
        county_number: int = 1,
        total_counties: int = 1
    ) -> List[Dict]:
        """
        Search a SINGLE specific county with detailed progress updates.
        ACTUALLY SCRAPES DATA from county websites instead of just returning links.

        Args:
            state: State code (OH, PA, WV, etc.)
            county: County name
            name: Person's name
            address: Address
            progress_callback: Progress callback function
            county_number: Current county number (for display)
            total_counties: Total counties being searched (for display)

        Returns:
            List of records found for this county (with scraped data)
        """

        county_results = []

        try:
            # Court records - ACTUALLY SCRAPE THE WEBSITE
            if progress_callback:
                progress_callback(
                    f"  → Scraping Court Records: {county} County, {state}",
                    10 + (county_number / total_counties) * 40
                )

            court_portal = get_county_portal(state, county, "courts")
            if court_portal:
                search_url = self._build_search_url(
                    court_portal.get("url", ""),
                    name=name,
                    record_type="court"
                )

                # ACTUALLY SCRAPE THE COURT WEBSITE
                scraped_data = await self.site_scraper.scrape_court_records(
                    url=search_url,
                    name=name,
                    county=county,
                    state=state
                )

                # Log scraping results to user
                if scraped_data.get("error"):
                    if progress_callback:
                        progress_callback(
                            f"    ⚠️ Court scraping error: {scraped_data['error']}",
                            10 + (county_number / total_counties) * 40
                        )
                elif scraped_data.get("success") and scraped_data.get("records_found"):
                    if progress_callback:
                        record_count = len(scraped_data["records_found"])
                        progress_callback(
                            f"    ✓ Found {record_count} court record(s)",
                            10 + (county_number / total_counties) * 40
                        )

                # Combine scraped data with portal info
                result = {
                    "type": "county_court_records",
                    "state": state,
                    "county": county,
                    "source": f"{county} County Clerk of Courts",
                    "url": search_url,
                    "base_url": court_portal.get("url", ""),
                    "notes": court_portal.get("notes", ""),
                    "search_name": name if name else "N/A",
                    "scraped_data": scraped_data,  # Real data from website
                    "scraping_success": scraped_data.get("success", False),
                    "scraping_error": scraped_data.get("error"),  # Include error details
                    "records_found": scraped_data.get("records_found", []),
                    "confidence": "high" if scraped_data.get("success") else "manual_required",
                    "auto_fill_available": True
                }

                county_results.append(result)

            # Property records - ACTUALLY SCRAPE THE WEBSITE
            if progress_callback:
                progress_callback(
                    f"  → Scraping Property Records: {county} County, {state}",
                    10 + (county_number / total_counties) * 40
                )

            property_portal = get_county_portal(state, county, "property")
            if property_portal:
                search_url = self._build_search_url(
                    property_portal.get("url", ""),
                    name=name,
                    address=address,
                    record_type="property"
                )

                # ACTUALLY SCRAPE THE PROPERTY WEBSITE
                scraped_data = await self.site_scraper.scrape_property_records(
                    url=search_url,
                    name=name,
                    address=address,
                    county=county,
                    state=state
                )

                # Log scraping results to user
                if scraped_data.get("error"):
                    if progress_callback:
                        progress_callback(
                            f"    ⚠️ Property scraping error: {scraped_data['error']}",
                            10 + (county_number / total_counties) * 40
                        )
                elif scraped_data.get("success") and scraped_data.get("properties_found"):
                    if progress_callback:
                        property_count = len(scraped_data["properties_found"])
                        progress_callback(
                            f"    ✓ Found {property_count} property record(s)",
                            10 + (county_number / total_counties) * 40
                        )

                result = {
                    "type": "county_property_records",
                    "state": state,
                    "county": county,
                    "source": f"{county} County Auditor/Assessor",
                    "url": search_url,
                    "base_url": property_portal.get("url", ""),
                    "notes": property_portal.get("notes", ""),
                    "search_address": address if address else "N/A",
                    "search_name": name if name else "N/A",
                    "scraped_data": scraped_data,  # Real data from website
                    "scraping_success": scraped_data.get("success", False),
                    "scraping_error": scraped_data.get("error"),  # Include error details
                    "properties_found": scraped_data.get("properties_found", []),
                    "confidence": "high" if scraped_data.get("success") else "manual_required",
                    "auto_fill_available": True
                }

                county_results.append(result)

            # Voter registration - ACTUALLY SCRAPE
            if progress_callback:
                progress_callback(
                    f"  → Checking Voter Registration: {county} County, {state}",
                    10 + (county_number / total_counties) * 40
                )

            voter_portal = self._get_voter_registration_portal(state)
            if voter_portal:
                # ACTUALLY SCRAPE VOTER REGISTRATION
                scraped_data = await self.site_scraper.scrape_voter_registration(
                    url=voter_portal,
                    name=name,
                    address=address,
                    state=state
                )

                result = {
                    "type": "voter_registration",
                    "state": state,
                    "county": county,
                    "source": f"{state} Board of Elections",
                    "url": voter_portal,
                    "search_name": name if name else "N/A",
                    "search_address": address if address else "N/A",
                    "scraped_data": scraped_data,  # Real data from website
                    "scraping_success": scraped_data.get("success", False),
                    "voters_found": scraped_data.get("voters_found", []),
                    "confidence": "high" if scraped_data.get("success") else "manual_required",
                    "notes": scraped_data.get("note", "State-level voter registration database")
                }

                county_results.append(result)

            # Car/Auto/VIN records - CHECK PORTAL
            if progress_callback:
                progress_callback(
                    f"  → Checking Motor Vehicle Portal: {county} County, {state}",
                    10 + (county_number / total_counties) * 40
                )

            vehicle_portal = self._get_vehicle_records_portal(state)
            if vehicle_portal:
                # ACTUALLY CHECK VEHICLE PORTAL
                scraped_data = await self.site_scraper.scrape_vehicle_records(
                    url=vehicle_portal,
                    name=name,
                    state=state
                )

                result = {
                    "type": "vehicle_records",
                    "state": state,
                    "county": county,
                    "source": f"{state} Bureau of Motor Vehicles",
                    "url": vehicle_portal,
                    "search_name": name if name else "N/A",
                    "scraped_data": scraped_data,  # Portal info
                    "portal_accessible": scraped_data.get("success", False),
                    "confidence": "manual_required",  # Usually requires auth
                    "notes": scraped_data.get("note", "State-level vehicle registration database")
                }

                county_results.append(result)

            # Brief delay for rate limiting (very polite)
            await asyncio.sleep(0.1)

        except Exception as e:
            if progress_callback:
                progress_callback(
                    f"  ⚠️ Error scraping {county} County, {state}: {str(e)}",
                    10 + (county_number / total_counties) * 40
                )

        return county_results

    async def _search_state_counties(
        self,
        state: str,
        name: Optional[str],
        address: Optional[str],
        target_county: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        state_progress_base: float = 0,
        state_progress_range: float = 100
    ) -> List[Dict]:
        """
        Search county records for a specific state.

        Args:
            state: OH, PA, or WV
            name: Person's name
            address: Address
            target_county: Specific county to search (if known), otherwise searches all
            progress_callback: Optional progress callback
            state_progress_base: Base progress percentage for this state
            state_progress_range: Progress range allocated for this state

        Returns:
            List of county record results
        """

        county_results = []

        # Get all counties for this state
        try:
            all_counties = get_all_counties_for_state(state)
            if not all_counties:
                if progress_callback:
                    progress_callback(f"No county data available for {state}", state_progress_base)
                return []
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error loading counties for {state}: {str(e)}", state_progress_base)
            return []

        # If we have a target county, only search that one
        # Otherwise, search ALL counties for the state (user wants comprehensive search)
        if target_county and target_county in all_counties:
            counties_to_search = [target_county]
        else:
            # Search ALL counties when state is selected but no specific county chosen
            counties_to_search = all_counties

        total_counties = len(counties_to_search)

        # Search each county separately (step-by-step, algorithmic)
        for county_idx, county in enumerate(counties_to_search, 1):
            try:
                # Show progress for THIS specific county
                if progress_callback:
                    current_progress = state_progress_base + (county_idx / total_counties) * state_progress_range
                    progress_callback(
                        f"[{county_idx}/{total_counties}] Searching {county} County, {state}...",
                        current_progress
                    )

                # Court records
                try:
                    court_portal = get_county_portal(state, county, "courts")
                    if court_portal:
                        # Build URL with query parameters to pre-fill search forms
                        search_url = self._build_search_url(
                            court_portal.get("url", ""),
                            name=name,
                            record_type="court"
                        )

                        if progress_callback:
                            progress_callback(
                                f"  → Court Records: {court_portal.get('url', '')[:50]}...",
                                current_progress
                            )

                        county_results.append({
                            "type": "county_court_records",
                            "state": state,
                            "county": county,
                            "source": f"{county} County Clerk of Courts",
                            "url": search_url,
                            "base_url": court_portal.get("url", ""),
                            "notes": court_portal.get("notes", ""),
                            "search_name": name if name else "N/A",
                            "confidence": "manual_required",
                            "auto_fill_available": True
                        })
                except Exception as e:
                    # Skip this court record if there's an error, don't crash
                    pass

                # Property records
                try:
                    property_portal = get_county_portal(state, county, "property")
                    if property_portal:
                        # Build URL with query parameters to pre-fill search forms
                        search_url = self._build_search_url(
                            property_portal.get("url", ""),
                            name=name,
                            address=address,
                            record_type="property"
                        )

                        if progress_callback:
                            progress_callback(
                                f"  → Property Records: {property_portal.get('url', '')[:50]}...",
                                current_progress
                            )

                        county_results.append({
                            "type": "county_property_records",
                            "state": state,
                            "county": county,
                            "source": f"{county} County Auditor/Assessor",
                            "url": search_url,
                            "base_url": property_portal.get("url", ""),
                            "notes": property_portal.get("notes", ""),
                            "search_address": address if address else "N/A",
                            "search_name": name if name else "N/A",
                            "confidence": "manual_required",
                            "auto_fill_available": True
                        })
                except Exception as e:
                    # Skip this property record if there's an error, don't crash
                    pass

                # Dynamic delay based on data collected (fluid timing)
                # More results = slightly longer processing time for proper categorization
                records_found = len(county_results) - len([r for r in county_results if r.get('county') != county])
                if records_found > 0:
                    # Brief pause for data organization (0.1-0.5 seconds based on volume)
                    await asyncio.sleep(0.1 + min(records_found * 0.05, 0.4))

            except Exception as e:
                # If an entire county search fails, log but continue to next county
                if progress_callback:
                    progress_callback(f"Skipped {county} County due to error", current_progress)
                continue

        return county_results

    def _build_search_url(
        self,
        base_url: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        record_type: str = "court"
    ) -> str:
        """
        Build a search URL with query parameters to pre-fill search forms.
        Attempts common parameter patterns used by court/property websites.
        """
        from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

        if not base_url:
            return ""

        # Parse the base URL
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)

        # Parse name into first/last if possible
        first_name = ""
        last_name = ""
        if name:
            name_parts = name.strip().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:])
            else:
                last_name = name_parts[0] if name_parts else ""

        # Common parameter names for court/property record systems
        if record_type == "court":
            # Try multiple common parameter patterns
            if name:
                query_params.update({
                    'lastName': [last_name],
                    'firstName': [first_name],
                    'name': [name],  # Full name fallback
                    'searchName': [name],
                    'partyName': [name],
                })
        elif record_type == "property":
            if name:
                query_params.update({
                    'ownerName': [name],
                    'owner': [name],
                    'name': [name],
                })
            if address:
                query_params.update({
                    'address': [address],
                    'streetAddress': [address],
                    'propertyAddress': [address],
                })

        # Rebuild URL with query parameters
        # Only include parameters with values
        clean_params = {k: v[0] if isinstance(v, list) else v for k, v in query_params.items() if v}

        if clean_params:
            new_query = urlencode(clean_params)
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))

        return base_url

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

    def _get_voter_registration_portal(self, state: str) -> Optional[str]:
        """
        Get voter registration portal URL for a state.
        Returns state-level voter registration lookup websites.
        """
        voter_portals = {
            "OH": "https://voterlookup.ohiosos.gov/voterlookup.aspx",
            "PA": "https://www.pavoterservices.pa.gov/pages/voterregistrationstatus.aspx",
            "WV": "https://services.sos.wv.gov/Elections/Voter/FindMyPollingPlace",
            "IN": "https://indianavoters.in.gov/",
            "IL": "https://ova.elections.il.gov/RegistrationLookup.aspx",
            "KY": "https://vrsws.sos.ky.gov/vic/",
            "TN": "https://tnmap.tn.gov/voterlookup/"
        }
        return voter_portals.get(state.upper())

    def _get_vehicle_records_portal(self, state: str) -> Optional[str]:
        """
        Get motor vehicle records portal URL for a state.
        Returns state-level BMV/DMV websites.
        """
        vehicle_portals = {
            "OH": "https://www.bmv.ohio.gov/",
            "PA": "https://www.dmv.pa.gov/Pages/default.aspx",
            "WV": "https://transportation.wv.gov/DMV/Pages/default.aspx",
            "IN": "https://www.in.gov/bmv/",
            "IL": "https://www.ilsos.gov/departments/vehicles/home.html",
            "KY": "https://drive.ky.gov/",
            "TN": "https://www.tn.gov/safety/driver-services.html"
        }
        return vehicle_portals.get(state.upper())

    async def close(self):
        """Clean up sessions"""
        if self.session:
            await self.session.close()
        if self.federal_searcher:
            await self.federal_searcher.close()
        if self.site_scraper:
            await self.site_scraper.close()


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
