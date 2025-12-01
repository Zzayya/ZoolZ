#!/usr/bin/env python3
"""
County Website Scraper
Actually visits county websites and extracts real data (not just links)
Uses aiohttp + BeautifulSoup for async HTML parsing

NOW WITH ML: Uses pre-trained spaCy NER for intelligent entity extraction
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

# Try to import ML models
try:
    from .ml_models import ml_models
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class CountySiteScraper:
    """
    Scrapes county websites to extract actual public records data.
    Handles different portal types: courts, property, voter registration, vehicles.

    ML Features:
    - spaCy NER for extracting persons, dates, locations from HTML
    - Better accuracy than regex alone
    - Tracks extractions for dataset creation
    """

    def __init__(self, timeout: int = 30, max_retries: int = 2, use_ml: bool = True):
        """
        Initialize scraper with timeout and retry settings.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for failed requests
            use_ml: Whether to use ML for entity extraction
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session = None
        self.use_ml = use_ml and ML_AVAILABLE
        self.entity_extractor = None
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        if self.use_ml:
            try:
                self.entity_extractor = ml_models.get_entity_extractor()
            except Exception as e:
                print(f"⚠ Could not load ML entity extractor: {e}")
                self.use_ml = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent}
            )
        return self.session

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def scrape_court_records(
        self,
        url: str,
        name: Optional[str] = None,
        county: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape court records from county clerk of courts website.

        Args:
            url: Court records portal URL
            name: Person's name to search for
            county: County name
            state: State code

        Returns:
            Dict with extracted court record data
        """
        result = {
            "type": "court_records_scraped",
            "county": county,
            "state": state,
            "source_url": url,
            "records_found": [],
            "scraped_at": datetime.now().isoformat(),
            "success": False,
            "error": None
        }

        try:
            session = await self._get_session()

            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    return result

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract court records data
                # Look for common patterns in court record tables
                records = self._extract_court_records_from_html(soup, name)

                if records:
                    result["records_found"] = records
                    result["success"] = True
                else:
                    # If no records found in tables, check for search forms
                    search_forms = self._find_search_forms(soup)
                    result["search_forms_available"] = len(search_forms)
                    result["requires_form_submission"] = len(search_forms) > 0

        except asyncio.TimeoutError:
            result["error"] = "Request timeout"
        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"

        return result

    async def scrape_property_records(
        self,
        url: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        county: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape property records from county auditor/assessor website.

        Args:
            url: Property records portal URL
            name: Owner's name
            address: Property address
            county: County name
            state: State code

        Returns:
            Dict with extracted property data
        """
        result = {
            "type": "property_records_scraped",
            "county": county,
            "state": state,
            "source_url": url,
            "properties_found": [],
            "scraped_at": datetime.now().isoformat(),
            "success": False,
            "error": None
        }

        try:
            session = await self._get_session()

            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    return result

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract property records
                properties = self._extract_property_records_from_html(soup, name, address)

                if properties:
                    result["properties_found"] = properties
                    result["success"] = True
                else:
                    # Check for search forms
                    search_forms = self._find_search_forms(soup)
                    result["search_forms_available"] = len(search_forms)
                    result["requires_form_submission"] = len(search_forms) > 0

        except asyncio.TimeoutError:
            result["error"] = "Request timeout"
        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"

        return result

    async def scrape_voter_registration(
        self,
        url: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape voter registration data from state election board.

        Args:
            url: Voter registration lookup URL
            name: Voter's name
            address: Voter's address
            state: State code

        Returns:
            Dict with extracted voter data
        """
        result = {
            "type": "voter_registration_scraped",
            "state": state,
            "source_url": url,
            "voters_found": [],
            "scraped_at": datetime.now().isoformat(),
            "success": False,
            "error": None
        }

        try:
            session = await self._get_session()

            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    return result

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Most voter lookup sites require form submission
                # Check if this is a search form or results page
                search_forms = self._find_search_forms(soup)

                if search_forms:
                    result["search_forms_available"] = len(search_forms)
                    result["requires_form_submission"] = True
                    result["note"] = "Voter lookup requires interactive form submission"
                else:
                    # Try to extract any visible voter data
                    voter_data = self._extract_voter_data_from_html(soup, name)
                    if voter_data:
                        result["voters_found"] = voter_data
                        result["success"] = True

        except asyncio.TimeoutError:
            result["error"] = "Request timeout"
        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"

        return result

    async def scrape_vehicle_records(
        self,
        url: str,
        name: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check vehicle records portal (usually requires authenticated access).

        Args:
            url: BMV/DMV portal URL
            name: Vehicle owner's name
            state: State code

        Returns:
            Dict with portal information
        """
        result = {
            "type": "vehicle_records_portal",
            "state": state,
            "source_url": url,
            "scraped_at": datetime.now().isoformat(),
            "success": False,
            "error": None
        }

        try:
            session = await self._get_session()

            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    return result

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Most BMV/DMV portals require login or have strict access controls
                # Check what's available
                search_forms = self._find_search_forms(soup)
                login_forms = soup.find_all('form', {'id': re.compile(r'login', re.I)})

                result["requires_authentication"] = len(login_forms) > 0
                result["search_forms_available"] = len(search_forms)
                result["note"] = "Vehicle records typically require authenticated access"
                result["success"] = True  # Portal reachable

        except asyncio.TimeoutError:
            result["error"] = "Request timeout"
        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"

        return result

    def _extract_court_records_from_html(self, soup: BeautifulSoup, name: Optional[str]) -> List[Dict]:
        """
        Extract court records from HTML tables and lists.
        Uses ML entity extraction if available for better accuracy.

        Args:
            soup: BeautifulSoup parsed HTML
            name: Name to search for

        Returns:
            List of extracted court records
        """
        records = []

        # Look for common table patterns
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                # If name is provided, check if this row mentions it
                if name and name.lower() in row_text.lower():
                    record = {
                        "row_text": row_text,
                        "matched_name": name,
                        "cells": [cell.get_text(strip=True) for cell in cells]
                    }

                    # Use ML entity extraction if available
                    if self.use_ml and self.entity_extractor:
                        entities = self.entity_extractor.extract_from_text(row_text)

                        # Add extracted entities to record
                        if entities.get("case_numbers"):
                            record["case_number"] = entities["case_numbers"][0]["text"]
                        if entities.get("dates"):
                            record["date"] = entities["dates"][0]["text"]
                        if entities.get("persons"):
                            record["persons_mentioned"] = [p["text"] for p in entities["persons"]]
                        if entities.get("locations"):
                            record["locations"] = [loc["text"] for loc in entities["locations"]]

                        # Track ML extraction
                        record["ml_extracted"] = True
                    else:
                        # Fallback to regex extraction
                        case_number = self._extract_case_number(row_text)
                        if case_number:
                            record["case_number"] = case_number

                        date = self._extract_date(row_text)
                        if date:
                            record["date"] = date

                        record["ml_extracted"] = False

                    records.append(record)

        return records

    def _extract_property_records_from_html(
        self,
        soup: BeautifulSoup,
        name: Optional[str],
        address: Optional[str]
    ) -> List[Dict]:
        """
        Extract property records from HTML.

        Args:
            soup: BeautifulSoup parsed HTML
            name: Owner name to search for
            address: Address to search for

        Returns:
            List of extracted property records
        """
        properties = []

        # Look for property data in tables
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                # Check if row matches search criteria
                matches = False
                if name and name.lower() in row_text.lower():
                    matches = True
                if address and address.lower() in row_text.lower():
                    matches = True

                if matches:
                    property_record = {
                        "row_text": row_text,
                        "cells": [cell.get_text(strip=True) for cell in cells]
                    }

                    # Try to extract parcel number
                    parcel = self._extract_parcel_number(row_text)
                    if parcel:
                        property_record["parcel_number"] = parcel

                    # Try to extract address
                    addr = self._extract_address(row_text)
                    if addr:
                        property_record["address"] = addr

                    properties.append(property_record)

        return properties

    def _extract_voter_data_from_html(self, soup: BeautifulSoup, name: Optional[str]) -> List[Dict]:
        """Extract voter registration data from HTML"""
        voters = []

        # Look for voter data patterns
        # Most voter sites show results after form submission
        # This method handles pre-populated results if any

        if name:
            # Search for name mentions
            text_content = soup.get_text()
            if name.lower() in text_content.lower():
                voters.append({
                    "note": "Name found on page but requires form submission for full details",
                    "page_snippet": text_content[:500]
                })

        return voters

    def _find_search_forms(self, soup: BeautifulSoup) -> List[Dict]:
        """Find search forms on the page"""
        forms = []
        for form in soup.find_all('form'):
            form_info = {
                "action": form.get('action', ''),
                "method": form.get('method', 'GET'),
                "inputs": []
            }

            for input_field in form.find_all('input'):
                form_info["inputs"].append({
                    "name": input_field.get('name', ''),
                    "type": input_field.get('type', 'text'),
                    "id": input_field.get('id', '')
                })

            forms.append(form_info)

        return forms

    def _extract_case_number(self, text: str) -> Optional[str]:
        """Extract case number from text"""
        # Common case number patterns
        patterns = [
            r'\b\d{2,4}-[A-Z]{2,3}-\d{4,6}\b',  # e.g., 2023-CR-12345
            r'\bCase\s*#?\s*:?\s*(\d+[\w-]+)\b',
            r'\b\d{4}[A-Z]{2}\d{4,6}\b'  # e.g., 2023CV123456
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0) if not match.groups() else match.group(1)

        return None

    def _extract_parcel_number(self, text: str) -> Optional[str]:
        """Extract parcel number from text"""
        patterns = [
            r'\bParcel\s*#?\s*:?\s*([\w-]+)\b',
            r'\b\d{2,3}-\d{2,3}-\d{2,3}-\d{2,3}\b',  # e.g., 12-34-56-78
            r'\b[A-Z]?\d{6,12}\b'  # Generic number pattern
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0) if not match.groups() else match.group(1)

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract dates from text"""
        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0)

        return None

    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address from text"""
        # Basic address pattern: number followed by street name
        pattern = r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct)\b'
        match = re.search(pattern, text, re.I)

        if match:
            return match.group(0)

        return None


# Async context manager support
class CountySiteScraperContextManager:
    """Context manager for CountySiteScraper"""

    def __init__(self, *args, **kwargs):
        self.scraper = CountySiteScraper(*args, **kwargs)

    async def __aenter__(self):
        return self.scraper

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scraper.close()
        return False
