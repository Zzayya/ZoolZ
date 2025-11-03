#!/usr/bin/env python3
"""
Federal Records Integration
Searches federal government databases and public records
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime


class FederalRecordsSearcher:
    """
    Handles searches across federal public record databases.
    All sources are legitimate government websites with public data.
    """

    # Federal Court System - PACER (Public Access to Court Electronic Records)
    FEDERAL_COURTS = {
        "pacer": {
            "name": "PACER - Federal Courts",
            "url": "https://pacer.uscourts.gov/",
            "description": "Federal court case records (requires account, $0.10/page)",
            "search_url": "https://pcl.uscourts.gov/",
            "free": False,
            "notes": "Requires free PACER account. First $30/quarter is free."
        },
        "pacer_case_locator": {
            "name": "PACER Case Locator",
            "url": "https://pcl.uscourts.gov/pcl/pages/search/findCases.jsf",
            "description": "Search federal cases across all districts",
            "free": False,
            "notes": "Most comprehensive federal case search"
        }
    }

    # Federal Inmate/Criminal Records
    FEDERAL_CRIMINAL = {
        "bop_inmate": {
            "name": "Federal Bureau of Prisons - Inmate Locator",
            "url": "https://www.bop.gov/inmateloc/",
            "description": "Current federal inmates",
            "free": True,
            "searchable": True,
            "notes": "Search by name or register number"
        },
        "national_sex_offender": {
            "name": "National Sex Offender Public Website",
            "url": "https://www.nsopw.gov/",
            "description": "Sex offender registry (all states)",
            "free": True,
            "searchable": True,
            "notes": "Nationwide sex offender search"
        },
        "fbi_most_wanted": {
            "name": "FBI Most Wanted",
            "url": "https://www.fbi.gov/wanted",
            "description": "FBI's most wanted fugitives",
            "free": True,
            "searchable": True,
            "notes": "Public fugitive database"
        }
    }

    # Death Records
    FEDERAL_VITAL_RECORDS = {
        "ssdi": {
            "name": "Social Security Death Index",
            "url": "https://www.ssa.gov/",
            "description": "Death records from Social Security Administration",
            "free": True,
            "searchable": False,
            "notes": "Available through third-party sites (Ancestry, FamilySearch)"
        },
        "cemetery_va": {
            "name": "National Cemetery Administration",
            "url": "https://www.cem.va.gov/burial_search/",
            "description": "Veterans buried in national cemeteries",
            "free": True,
            "searchable": True,
            "notes": "Search veterans burial locations"
        }
    }

    # Federal Background Checks & Licenses
    FEDERAL_LICENSES = {
        "faa_airmen": {
            "name": "FAA Airmen Certification",
            "url": "https://amsrvs.registry.faa.gov/airmeninquiry/",
            "description": "Pilot licenses and certificates",
            "free": True,
            "searchable": True,
            "notes": "Search by name or certificate number"
        },
        "faa_aircraft": {
            "name": "FAA Aircraft Registration",
            "url": "https://registry.faa.gov/aircraftinquiry/",
            "description": "Aircraft ownership records",
            "free": True,
            "searchable": True,
            "notes": "Search by N-number or owner name"
        },
        "fcc_licenses": {
            "name": "FCC License Search",
            "url": "https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp",
            "description": "Radio/broadcast licenses",
            "free": True,
            "searchable": True,
            "notes": "Amateur radio, commercial licenses"
        }
    }

    # Federal Property & Financial
    FEDERAL_PROPERTY = {
        "usps_address": {
            "name": "USPS Address Verification",
            "url": "https://tools.usps.com/zip-code-lookup.htm",
            "description": "Verify addresses with USPS",
            "free": True,
            "searchable": True,
            "notes": "Official address standardization"
        },
        "treasury_sanctions": {
            "name": "OFAC Sanctions List",
            "url": "https://sanctionssearch.ofac.treas.gov/",
            "description": "Specially Designated Nationals list",
            "free": True,
            "searchable": True,
            "notes": "Check if person is on sanctions list"
        }
    }

    # Professional Licenses
    FEDERAL_PROFESSIONAL = {
        "npi_registry": {
            "name": "National Provider Identifier Registry",
            "url": "https://npiregistry.cms.hhs.gov/",
            "description": "Healthcare provider lookup",
            "free": True,
            "searchable": True,
            "notes": "Doctors, nurses, medical facilities"
        },
        "sam_gov": {
            "name": "SAM.gov Entity Search",
            "url": "https://sam.gov/",
            "description": "Government contractor registry",
            "free": True,
            "searchable": True,
            "notes": "Businesses registered for federal contracts"
        }
    }

    def __init__(self):
        self.session = None
        self.rate_limit_delay = 12  # 12 seconds between requests (VERY polite)

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

    async def search_federal_records(
        self,
        name: Optional[str] = None,
        address: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Search federal records for a person.
        Returns links to search portals (most require manual search due to CAPTCHAs).
        """

        results = {
            "federal_courts": [],
            "criminal_records": [],
            "vital_records": [],
            "licenses": [],
            "property_records": [],
            "professional_licenses": [],
            "search_timestamp": datetime.now().isoformat(),
            "notes": []
        }

        # Federal Courts
        for key, portal in self.FEDERAL_COURTS.items():
            results["federal_courts"].append({
                "source": portal["name"],
                "url": portal["url"],
                "description": portal["description"],
                "free": portal["free"],
                "notes": portal["notes"],
                "search_name": name if name else "N/A",
                "requires_manual_search": True
            })

        # Criminal Records
        for key, portal in self.FEDERAL_CRIMINAL.items():
            record = {
                "source": portal["name"],
                "url": portal["url"],
                "description": portal["description"],
                "free": portal["free"],
                "searchable": portal["searchable"],
                "notes": portal["notes"],
                "search_name": name if name else "N/A"
            }

            # Attempt automated search for BOP Inmate Locator
            if key == "bop_inmate" and name:
                bop_result = await self._search_bop_inmates(name)
                if bop_result:
                    record["automated_search"] = bop_result
                await asyncio.sleep(self.rate_limit_delay)

            results["criminal_records"].append(record)

        # Vital Records
        for key, portal in self.FEDERAL_VITAL_RECORDS.items():
            results["vital_records"].append({
                "source": portal["name"],
                "url": portal["url"],
                "description": portal["description"],
                "free": portal["free"],
                "searchable": portal["searchable"],
                "notes": portal["notes"],
                "search_name": name if name else "N/A"
            })

        # Licenses (FAA, FCC)
        for key, portal in self.FEDERAL_LICENSES.items():
            results["licenses"].append({
                "source": portal["name"],
                "url": portal["url"],
                "description": portal["description"],
                "free": portal["free"],
                "searchable": portal["searchable"],
                "notes": portal["notes"],
                "search_name": name if name else "N/A"
            })

        # Property & Financial
        for key, portal in self.FEDERAL_PROPERTY.items():
            results["property_records"].append({
                "source": portal["name"],
                "url": portal["url"],
                "description": portal["description"],
                "free": portal["free"],
                "searchable": portal["searchable"],
                "notes": portal["notes"]
            })

        # Professional Licenses
        for key, portal in self.FEDERAL_PROFESSIONAL.items():
            results["professional_licenses"].append({
                "source": portal["name"],
                "url": portal["url"],
                "description": portal["description"],
                "free": portal["free"],
                "searchable": portal["searchable"],
                "notes": portal["notes"],
                "search_name": name if name else "N/A"
            })

        # Add general notes
        results["notes"].append(
            "Federal records are public but many require manual searches due to CAPTCHA protection."
        )
        results["notes"].append(
            "PACER (federal courts) requires free account. First $30/quarter is free."
        )
        results["notes"].append(
            "All sources are legitimate U.S. government websites with public data."
        )

        return results

    async def _search_bop_inmates(self, name: str) -> Optional[Dict]:
        """
        Attempt to search Bureau of Prisons inmate database.
        Note: This is a public API but may have rate limiting.
        """
        try:
            session = await self._get_session()

            # BOP has a public search form, but it's protected
            # We'll just return the direct link with auto-fill data
            name_parts = name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            return {
                "search_url": "https://www.bop.gov/inmateloc/",
                "auto_fill": {
                    "firstName": first_name,
                    "lastName": last_name
                },
                "notes": "Visit URL and use auto-fill data to search"
            }

        except Exception as e:
            return {
                "error": str(e),
                "fallback_url": "https://www.bop.gov/inmateloc/"
            }

    def get_all_federal_sources(self) -> Dict:
        """Get complete list of all federal sources with metadata"""
        all_sources = {
            "courts": self.FEDERAL_COURTS,
            "criminal": self.FEDERAL_CRIMINAL,
            "vital_records": self.FEDERAL_VITAL_RECORDS,
            "licenses": self.FEDERAL_LICENSES,
            "property": self.FEDERAL_PROPERTY,
            "professional": self.FEDERAL_PROFESSIONAL
        }

        summary = {
            "total_sources": sum(len(category) for category in all_sources.values()),
            "by_category": {
                category: len(sources) for category, sources in all_sources.items()
            },
            "sources": all_sources
        }

        return summary

    async def close(self):
        """Clean up session"""
        if self.session:
            await self.session.close()


# Helper function to generate direct search URLs with auto-fill data
def generate_federal_search_link(source_key: str, search_params: Dict) -> str:
    """
    Generate a direct link to federal search portal with pre-filled parameters.

    Args:
        source_key: Key identifying the federal source (e.g., 'bop_inmate')
        search_params: Dict with search parameters (name, address, etc.)

    Returns:
        URL string with query parameters where possible
    """

    name = search_params.get("name", "")
    name_parts = name.split() if name else []
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    # BOP Inmate Search
    if source_key == "bop_inmate":
        # Note: BOP doesn't accept URL parameters, must use form
        return "https://www.bop.gov/inmateloc/"

    # Sex Offender Registry
    elif source_key == "national_sex_offender":
        # NSOPW has a search form
        return "https://www.nsopw.gov/Search"

    # FAA Airmen
    elif source_key == "faa_airmen":
        return "https://amsrvs.registry.faa.gov/airmeninquiry/"

    # NPI Registry (Healthcare providers)
    elif source_key == "npi_registry":
        if first_name and last_name:
            return f"https://npiregistry.cms.hhs.gov/search?firstName={first_name}&lastName={last_name}"
        return "https://npiregistry.cms.hhs.gov/"

    # Default: return base URL
    else:
        return ""
