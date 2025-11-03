#!/usr/bin/env python3
"""
People Finder - Search Orchestrator
Coordinates searches across multiple data sources and aggregates results
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json

from .public_records import PublicRecordsSearcher
from .phone_apis import PhoneValidator
from .web_scraper import WebSearcher
from .data_organizer import ResultOrganizer
from .name_variations import get_name_variations, has_variations, get_variation_count


class SearchOrchestrator:
    """
    Main coordinator for people searches.
    Manages parallel searches and result aggregation.
    """
    
    def __init__(self, cache_db_path: str = "database/search_cache.db"):
        self.public_records = PublicRecordsSearcher()
        self.phone_validator = PhoneValidator()
        self.web_scraper = WebSearcher()
        self.organizer = ResultOrganizer(cache_db_path)
        
    async def search_person(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        state: Optional[str] = None,
        county: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Main search function - accepts any combination of search parameters.
        Automatically searches name variations/pseudonyms as separate complete searches.

        Args:
            name: Person's full or partial name
            phone: Phone number (any format)
            address: Street address
            email: Email address
            state: Two-letter state code (OH, PA, WV, etc.)
            county: County name (optional - searches all counties if not specified)
            progress_callback: Function to call with progress updates

        Returns:
            Dict containing organized results with confidence levels
        """

        if progress_callback:
            progress_callback("Starting search...", 0)

        # Validate inputs
        if not any([name, phone, address, email]):
            return {"error": "At least one search parameter required"}

        # Check cache first
        cached_result = self.organizer.check_cache(name, phone, address, email)
        if cached_result:
            if progress_callback:
                progress_callback("Found cached results", 100)
            return cached_result

        # Detect if name has variations (Samuel → Sam, William → Will/Bill)
        if name and has_variations(name):
            if progress_callback:
                variation_count = get_variation_count(name)
                progress_callback(f"Detected {variation_count} name variations - searching each separately...", 5)

            # Perform separate searches for each name variation
            return await self._search_with_name_variations(
                name, phone, address, email, state, county, progress_callback
            )

        # Standard single-name search
        return await self._search_single_name(
            name, phone, address, email, state, county, progress_callback
        )

    async def _search_single_name(
        self,
        name: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str],
        state: Optional[str],
        county: Optional[str],
        progress_callback: Optional[callable]
    ) -> Dict:
        """
        Perform a single search (no name variations).
        """

        # Phase 1: Fast official sources (public records + phone APIs)
        if progress_callback:
            progress_callback("Searching public records and validating phones...", 10)

        official_results = await self._search_official_sources(
            name, phone, address, email, state, county, progress_callback
        )

        # Phase 2: Slower web scraping (social media, forums, etc.)
        if progress_callback:
            progress_callback("Searching web sources (this may take a while)...", 60)

        web_results = await self._search_web_sources(
            name, phone, address, email, state, progress_callback
        )

        # Phase 3: Organize and de-duplicate
        if progress_callback:
            progress_callback("Organizing results and removing duplicates...", 90)

        organized = self.organizer.organize_results(
            official_results,
            web_results,
            search_params={
                "name": name,
                "phone": phone,
                "address": address,
                "email": email,
                "state": state,
                "county": county
            }
        )

        # Cache the results
        self.organizer.cache_results(organized)

        if progress_callback:
            progress_callback("Search complete!", 100)

        return organized

    async def _search_with_name_variations(
        self,
        original_name: str,
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str],
        state: Optional[str],
        county: Optional[str],
        progress_callback: Optional[callable]
    ) -> Dict:
        """
        Perform separate complete searches for each name variation.

        Example: "Samuel Johnson" →
          - Search 1: "Samuel Johnson"
          - Search 2: "Sam Johnson"
          - Search 3: "Sammy Johnson"

        Each search is independent and complete (public records + web sources).
        Results are then aggregated with proper de-duplication.
        """

        # Get all name variations
        name_variations = get_name_variations(original_name)

        if progress_callback:
            progress_callback(f"Searching {len(name_variations)} name variations: {', '.join(name_variations)}", 5)

        # Store results from all variation searches
        all_variation_results = []

        # Calculate progress increments
        progress_per_variation = 90 / len(name_variations)  # 90% total (save 10% for final aggregation)
        current_progress = 5

        # Perform separate search for each name variation
        for idx, name_variant in enumerate(name_variations, 1):
            if progress_callback:
                progress_callback(f"[{idx}/{len(name_variations)}] Searching '{name_variant}'...", int(current_progress))

            # Official sources (public records + phone)
            if progress_callback:
                progress_callback(f"[{idx}/{len(name_variations)}] '{name_variant}' - Public records...", int(current_progress + progress_per_variation * 0.3))

            official_results = await self._search_official_sources(
                name_variant, phone, address, email, state, county, None  # No sub-callbacks
            )

            # Web sources (social media, web mentions)
            if progress_callback:
                progress_callback(f"[{idx}/{len(name_variations)}] '{name_variant}' - Web sources...", int(current_progress + progress_per_variation * 0.7))

            web_results = await self._search_web_sources(
                name_variant, phone, address, email, state, None  # No sub-callbacks
            )

            # Store raw results for this variation
            all_variation_results.append({
                "name_variant": name_variant,
                "official_results": official_results,
                "web_results": web_results
            })

            current_progress += progress_per_variation

        # Aggregate and organize all results from all variations
        if progress_callback:
            progress_callback("Aggregating results from all name variations...", 95)

        # Combine all results
        combined_official = {
            "county_records": [],
            "federal_records": {},
            "public_records": [],
            "phone_data": {},
            "errors": []
        }

        combined_web = {
            "social_media": [],
            "web_mentions": [],
            "phone_mentions": [],
            "email_mentions": [],
            "emails": [],
            "errors": []
        }

        # Merge results from all variations
        for variation_result in all_variation_results:
            official = variation_result["official_results"]
            web = variation_result["web_results"]

            # Merge official sources
            combined_official["county_records"].extend(official.get("county_records", []))

            # Merge federal records (dict of lists)
            for category, records in official.get("federal_records", {}).items():
                if category not in combined_official["federal_records"]:
                    combined_official["federal_records"][category] = []
                combined_official["federal_records"][category].extend(records)

            combined_official["public_records"].extend(official.get("public_records", []))

            # Keep phone data if not already set
            if not combined_official["phone_data"] and official.get("phone_data"):
                combined_official["phone_data"] = official["phone_data"]

            combined_official["errors"].extend(official.get("errors", []))

            # Merge web sources
            combined_web["social_media"].extend(web.get("social_media", []))
            combined_web["web_mentions"].extend(web.get("web_mentions", []))
            combined_web["phone_mentions"].extend(web.get("phone_mentions", []))
            combined_web["email_mentions"].extend(web.get("email_mentions", []))
            combined_web["emails"].extend(web.get("emails", []))
            combined_web["errors"].extend(web.get("errors", []))

        # Organize with enhanced de-duplication (will properly separate distinct people)
        if progress_callback:
            progress_callback("Organizing and de-duplicating results...", 97)

        organized = self.organizer.organize_results(
            combined_official,
            combined_web,
            search_params={
                "name": original_name,
                "name_variations": name_variations,
                "phone": phone,
                "address": address,
                "email": email,
                "state": state,
                "county": county
            }
        )

        # Add metadata about name variations searched
        organized["name_variations_searched"] = name_variations
        organized["search_notes"] = f"Searched {len(name_variations)} name variations: {', '.join(name_variations)}"

        # Cache the aggregated results
        self.organizer.cache_results(organized)

        if progress_callback:
            progress_callback(f"Search complete! Found results for {len(name_variations)} name variations.", 100)

        return organized
    
    async def _search_official_sources(
        self,
        name: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str],
        state: Optional[str],
        county: Optional[str],
        progress_callback: Optional[callable]
    ) -> Dict:
        """Search public records (county + federal) and phone validation APIs in parallel"""

        tasks = []

        # Comprehensive public records search (county + federal)
        if name or address:
            tasks.append(
                self.public_records.search_comprehensive(
                    name=name,
                    address=address,
                    state=state,
                    county=county
                )
            )

        # Phone validation
        if phone:
            tasks.append(self.phone_validator.validate_and_lookup(phone))

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        combined = {
            "county_records": [],
            "federal_records": {},
            "public_records": [],  # Legacy compatibility
            "phone_data": {},
            "errors": []
        }

        for result in results:
            if isinstance(result, Exception):
                combined["errors"].append(str(result))
            elif "county_records" in result and "federal_records" in result:
                # New comprehensive search results
                combined["county_records"] = result.get("county_records", [])
                combined["federal_records"] = result.get("federal_records", {})
                # Also add to legacy public_records for compatibility
                combined["public_records"].append(result)
            elif "carrier" in result or "line_type" in result:
                combined["phone_data"] = result
        
        return combined
    
    async def _search_web_sources(
        self,
        name: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str],
        state: Optional[str],
        progress_callback: Optional[callable]
    ) -> Dict:
        """
        Search web sources using enhanced search algorithms.
        Uses specialized phone and social media searches for better results.
        """

        results = {
            "social_media": [],
            "web_mentions": [],
            "phone_mentions": [],
            "email_mentions": [],
            "emails": [],
            "errors": []
        }

        search_tasks = []

        # Enhanced phone search (multiple formats, reverse lookup sites)
        if phone:
            if progress_callback:
                progress_callback("Searching phone mentions (enhanced)...", 62)
            search_tasks.append(("phone", self.web_scraper.search_phone_mentions(phone)))

        # Enhanced social media search (targeted platform searches)
        if name:
            if progress_callback:
                progress_callback("Searching social media profiles...", 68)
            location_hint = f"{address}, {state}" if address and state else (state if state else None)
            search_tasks.append(("social", self.web_scraper.search_social_media(name, location_hint)))

        # Email mentions search
        if email:
            if progress_callback:
                progress_callback("Searching email mentions...", 74)
            search_tasks.append(("email", self.web_scraper.search_email_mentions(email)))

        # Generic name search (for additional context)
        if name and not phone and not email:
            if progress_callback:
                progress_callback("Searching web mentions...", 80)
            search_tasks.append(("name", self.web_scraper.search(f'"{name}"', num_results=10)))

        # Execute all searches in parallel
        if search_tasks:
            task_results = await asyncio.gather(
                *[task for _, task in search_tasks],
                return_exceptions=True
            )

            # Process results
            for (search_type, _), result in zip(search_tasks, task_results):
                if isinstance(result, Exception):
                    results["errors"].append(f"{search_type} search error: {str(result)}")
                    continue

                if search_type == "phone":
                    # Enhanced phone search results
                    results["phone_mentions"] = result
                    results["web_mentions"].extend(result)  # Also add to general mentions

                elif search_type == "social":
                    # Enhanced social media results (organized by platform)
                    for platform, platform_results in result.items():
                        if isinstance(platform_results, list):
                            for social_result in platform_results:
                                results["social_media"].append({
                                    "platform": platform.title(),
                                    "url": social_result.get("url", ""),
                                    "title": social_result.get("title", ""),
                                    "snippet": social_result.get("snippet", ""),
                                    "source": social_result.get("source", "Web Search")
                                })

                elif search_type == "email":
                    # Email mention results
                    results["email_mentions"] = result
                    results["web_mentions"].extend(result)

                elif search_type == "name":
                    # Generic name search results
                    results["web_mentions"].extend(result.get("results", []))

        return results
    
    def _get_target_states(self, state: Optional[str]) -> List[str]:
        """Get list of states to search"""
        priority_states = ["OH", "WV", "PA", "IN", "IL", "KY", "TN"]
        
        if state:
            # If specific state provided, prioritize it
            return [state.upper()] + [s for s in priority_states if s != state.upper()]
        
        return priority_states
    
    def _build_web_queries(
        self,
        name: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str]
    ) -> List[str]:
        """Build search queries for web scraping"""
        queries = []
        
        if name and phone:
            queries.append(f'"{name}" "{phone}"')
        
        if name and email:
            queries.append(f'"{name}" "{email}"')
        
        if name:
            queries.append(f'"{name}" site:facebook.com')
            queries.append(f'"{name}" site:linkedin.com')
        
        if phone:
            queries.append(f'"{phone}" contact OR "phone number"')
        
        if email:
            queries.append(f'"{email}" contact OR profile')
        
        return queries
    
    def _extract_social_links(self, web_mentions: List[Dict]) -> List[Dict]:
        """Extract social media profile links from web results"""
        social_platforms = [
            "facebook.com",
            "linkedin.com",
            "twitter.com",
            "instagram.com",
            "tiktok.com"
        ]
        
        social_links = []
        
        for mention in web_mentions:
            url = mention.get("url", "")
            
            for platform in social_platforms:
                if platform in url:
                    social_links.append({
                        "platform": platform.replace(".com", "").title(),
                        "url": url,
                        "title": mention.get("title", ""),
                        "snippet": mention.get("snippet", ""),
                        "confidence": "low",  # Web-scraped = low confidence
                        "found_at": datetime.now().isoformat()
                    })
                    break
        
        return social_links


# Async helper for progress updates
async def run_search_with_progress(
    orchestrator: SearchOrchestrator,
    search_params: Dict,
    progress_queue: asyncio.Queue
):
    """Helper function to run search with progress updates via queue"""
    
    def progress_callback(message: str, percent: int):
        try:
            progress_queue.put_nowait({"message": message, "percent": percent})
        except:
            pass  # Queue full, skip update
    
    result = await orchestrator.search_person(
        **search_params,
        progress_callback=progress_callback
    )
    
    return result
