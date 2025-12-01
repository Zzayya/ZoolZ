#!/usr/bin/env python3
"""
Phone Validator and Lookup
Uses free APIs to validate phone numbers and get carrier info
"""

import aiohttp
import asyncio
import re
from typing import Dict, Optional


class PhoneValidator:
    """
    Phone number validation and lookup using free APIs.
    Combines multiple sources for best coverage.
    """
    
    # Free API endpoints
    NUMVERIFY_API = "http://apilayer.net/api/validate"
    NUMVERIFY_KEY = None  # User can add their free key from numverify.com
    
    def __init__(self, numverify_key: Optional[str] = None):
        """
        Initialize phone validator.
        
        Args:
            numverify_key: Optional API key from numverify.com (has free tier)
        """
        self.numverify_key = numverify_key
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def normalize_phone(self, phone: str) -> str:
        """
        Enhanced phone number normalization.
        Handles multiple formats and edge cases:
        - Removes all non-numeric characters
        - Handles country codes
        - Handles extensions
        - Validates length
        """
        # Handle None or empty
        if not phone:
            return ""

        # Remove extension if present (ext, x, extension)
        phone_without_ext = re.sub(r'\s*(?:ext|x|extension)[\s\.]*\d+', '', phone, flags=re.IGNORECASE)

        # Remove all non-digits
        digits_only = re.sub(r'\D', '', phone_without_ext)

        # Handle different lengths
        if len(digits_only) == 10:
            # Standard 10-digit US number
            digits_only = "1" + digits_only
        elif len(digits_only) == 11:
            # Already has country code
            if digits_only[0] != '1':
                # Non-US country code or malformed
                # Try to extract last 10 digits if available
                if len(digits_only) >= 10:
                    digits_only = "1" + digits_only[-10:]
        elif len(digits_only) > 11:
            # Might have international prefix or extra digits
            # Extract last 10 digits and add US country code
            digits_only = "1" + digits_only[-10:]
        elif len(digits_only) < 10:
            # Too short, return as-is (validation will fail later)
            pass

        return digits_only
    
    def format_phone(self, phone: str) -> str:
        """
        Enhanced phone number formatting.
        Returns standardized US format: (XXX) XXX-XXXX
        Handles multiple input formats gracefully.
        """
        # Handle None or empty
        if not phone:
            return ""

        normalized = self.normalize_phone(phone)

        # Handle different normalized lengths
        if len(normalized) == 11 and normalized[0] == '1':
            # US number with country code: 1XXXXXXXXXX
            return f"({normalized[1:4]}) {normalized[4:7]}-{normalized[7:11]}"
        elif len(normalized) == 10:
            # 10-digit US number: XXXXXXXXXX
            return f"({normalized[0:3]}) {normalized[3:6]}-{normalized[6:10]}"
        elif len(normalized) > 11:
            # International or extra digits - format last 10 digits
            last_10 = normalized[-10:]
            return f"({last_10[0:3]}) {last_10[3:6]}-{last_10[6:10]}"

        # If unable to format, return original input
        return phone
    
    async def validate_and_lookup(self, phone: str) -> Dict:
        """
        Validate phone number and get carrier/line type info.
        Returns all available information about the number.
        """
        
        normalized = self.normalize_phone(phone)
        formatted = self.format_phone(phone)
        
        result = {
            "phone_number": formatted,
            "normalized": normalized,
            "valid": False,
            "carrier": "Unknown",
            "line_type": "Unknown",  # mobile, landline, voip, etc.
            "location": {},
            "active": "Unknown",
            "confidence": "medium",
            "sources": []
        }
        
        # Basic validation
        if len(normalized) not in [10, 11]:
            result["confidence"] = "low"
            result["error"] = "Invalid phone number format"
            return result
        
        # Try multiple lookup methods
        tasks = [
            self._numverify_lookup(normalized),
            self._basic_area_code_lookup(normalized),
            self._free_carrier_lookup(normalized)
        ]
        
        lookup_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results from all sources
        for lookup_result in lookup_results:
            if isinstance(lookup_result, Exception):
                continue
            
            if lookup_result.get("valid"):
                result["valid"] = True
            
            if lookup_result.get("carrier"):
                result["carrier"] = lookup_result["carrier"]
            
            if lookup_result.get("line_type"):
                result["line_type"] = lookup_result["line_type"]
            
            if lookup_result.get("location"):
                result["location"].update(lookup_result["location"])
            
            if lookup_result.get("source"):
                result["sources"].append(lookup_result["source"])
        
        # If we have data from at least one source, it's valid
        if result["sources"]:
            result["valid"] = True
            result["confidence"] = "high" if len(result["sources"]) > 1 else "medium"
        
        return result
    
    async def _numverify_lookup(self, phone: str) -> Dict:
        """
        Use NumVerify API (free tier: 250 requests/month).
        Sign up at: https://numverify.com/
        """
        
        if not self.numverify_key:
            return {"error": "NumVerify API key not configured"}
        
        try:
            session = await self._get_session()
            
            # Remove country code for API
            phone_without_country = phone[-10:]
            
            async with session.get(
                self.NUMVERIFY_API,
                params={
                    "access_key": self.numverify_key,
                    "number": phone_without_country,
                    "country_code": "US"
                }
            ) as response:
                data = await response.json()
                
                if data.get("valid"):
                    return {
                        "valid": True,
                        "carrier": data.get("carrier", "Unknown"),
                        "line_type": data.get("line_type", "Unknown"),
                        "location": {
                            "city": data.get("location", ""),
                            "state": data.get("country_code", "")
                        },
                        "source": "NumVerify"
                    }
        
        except Exception as e:
            return {"error": str(e)}
        
        return {}
    
    async def _basic_area_code_lookup(self, phone: str) -> Dict:
        """
        Basic area code lookup (always free, no API needed).
        Returns location info based on area code.
        """
        
        # Extract area code (first 3 digits after country code)
        if len(phone) == 11:
            area_code = phone[1:4]
        elif len(phone) == 10:
            area_code = phone[0:3]
        else:
            return {}
        
        # Area code database (subset - add more as needed)
        area_code_map = {
            # Ohio
            "216": {"state": "OH", "city": "Cleveland"},
            "220": {"state": "OH", "city": "Newark/Zanesville"},
            "234": {"state": "OH", "city": "Akron/Canton"},
            "330": {"state": "OH", "city": "Akron/Canton"},
            "380": {"state": "OH", "city": "Columbus"},
            "419": {"state": "OH", "city": "Toledo"},
            "440": {"state": "OH", "city": "Cleveland suburbs"},
            "513": {"state": "OH", "city": "Cincinnati"},
            "567": {"state": "OH", "city": "Toledo"},
            "614": {"state": "OH", "city": "Columbus"},
            "740": {"state": "OH", "city": "Southern Ohio"},
            "937": {"state": "OH", "city": "Dayton"},
            
            # Pennsylvania
            "215": {"state": "PA", "city": "Philadelphia"},
            "267": {"state": "PA", "city": "Philadelphia"},
            "272": {"state": "PA", "city": "Northeast PA"},
            "412": {"state": "PA", "city": "Pittsburgh"},
            "484": {"state": "PA", "city": "Philadelphia suburbs"},
            "570": {"state": "PA", "city": "Wilkes-Barre"},
            "610": {"state": "PA", "city": "Philadelphia suburbs"},
            "717": {"state": "PA", "city": "Harrisburg"},
            "724": {"state": "PA", "city": "Pittsburgh suburbs"},
            "814": {"state": "PA", "city": "Erie"},
            "878": {"state": "PA", "city": "Pittsburgh"},
            
            # West Virginia
            "304": {"state": "WV", "city": "Charleston"},
            "681": {"state": "WV", "city": "Charleston"},
            
            # Indiana
            "219": {"state": "IN", "city": "Northwest IN"},
            "260": {"state": "IN", "city": "Fort Wayne"},
            "317": {"state": "IN", "city": "Indianapolis"},
            "463": {"state": "IN", "city": "Indianapolis"},
            "574": {"state": "IN", "city": "South Bend"},
            "765": {"state": "IN", "city": "Lafayette"},
            "812": {"state": "IN", "city": "Southern IN"},
            "930": {"state": "IN", "city": "Evansville"},
            
            # Illinois
            "217": {"state": "IL", "city": "Springfield"},
            "224": {"state": "IL", "city": "Chicago suburbs"},
            "309": {"state": "IL", "city": "Peoria"},
            "312": {"state": "IL", "city": "Chicago"},
            "331": {"state": "IL", "city": "Chicago suburbs"},
            "618": {"state": "IL", "city": "Southern IL"},
            "630": {"state": "IL", "city": "Chicago suburbs"},
            "708": {"state": "IL", "city": "Chicago suburbs"},
            "773": {"state": "IL", "city": "Chicago"},
            "815": {"state": "IL", "city": "Rockford"},
            "847": {"state": "IL", "city": "Chicago suburbs"},
            
            # Kentucky
            "270": {"state": "KY", "city": "Western KY"},
            "364": {"state": "KY", "city": "Northern KY"},
            "502": {"state": "KY", "city": "Louisville"},
            "606": {"state": "KY", "city": "Eastern KY"},
            "859": {"state": "KY", "city": "Lexington"},
            
            # Tennessee
            "423": {"state": "TN", "city": "Chattanooga"},
            "615": {"state": "TN", "city": "Nashville"},
            "629": {"state": "TN", "city": "Nashville"},
            "731": {"state": "TN", "city": "Jackson"},
            "865": {"state": "TN", "city": "Knoxville"},
            "901": {"state": "TN", "city": "Memphis"},
            "931": {"state": "TN", "city": "Clarksville"}
        }
        
        location_data = area_code_map.get(area_code, {})
        
        if location_data:
            return {
                "valid": True,
                "location": location_data,
                "source": "Area Code Database"
            }
        
        return {}
    
    async def _free_carrier_lookup(self, phone: str) -> Dict:
        """
        Enhanced carrier detection using pattern analysis and heuristics.
        Provides educated guesses about carrier and line type based on:
        - Area code patterns
        - Exchange prefix patterns
        - Common carrier number blocks
        """

        # Extract components
        if len(phone) == 11:
            area_code = phone[1:4]
            exchange = phone[4:7]
        elif len(phone) == 10:
            area_code = phone[0:3]
            exchange = phone[3:6]
        else:
            return {}

        result = {}

        # Detect line type based on exchange patterns
        # Mobile numbers often use certain exchange prefixes
        mobile_exchanges = {
            # Common mobile exchange patterns (first digit of exchange)
            '2', '3', '4', '5', '6', '7', '8', '9'  # Mobile often starts with these
        }

        landline_exchanges = {
            # Landline patterns (often geographic)
            '0', '1'  # Traditional landlines often start with these
        }

        first_exchange_digit = exchange[0] if exchange else None

        # Educated guess about line type
        if first_exchange_digit:
            if first_exchange_digit in mobile_exchanges:
                # Higher likelihood of mobile
                result["line_type"] = "mobile (estimated)"
            elif first_exchange_digit in landline_exchanges:
                result["line_type"] = "landline (estimated)"
            else:
                result["line_type"] = "unknown"

        # Carrier hints based on common area code ownership patterns
        # Note: This is heuristic-based and not 100% accurate
        carrier_hints = self._get_carrier_hints(area_code, exchange)
        if carrier_hints:
            result["carrier"] = f"{carrier_hints} (estimated)"
            result["source"] = "Pattern Analysis"

        # VOIP detection heuristics
        # Certain area codes are heavily used by VOIP providers
        voip_heavy_area_codes = {
            '800', '888', '877', '866', '855', '844', '833',  # Toll-free (VOIP)
            '456',  # Often VOIP testing
        }

        if area_code in voip_heavy_area_codes:
            result["line_type"] = "voip/toll-free"
            result["carrier"] = "VOIP Provider (estimated)"

        if result:
            result["valid"] = True
            result["source"] = "Pattern Analysis (Heuristic)"

        return result

    def _get_carrier_hints(self, area_code: str, exchange: str) -> str:
        """
        Get carrier hints based on known patterns.
        This is heuristic and for educational purposes - not 100% accurate.
        """

        # Some area codes have dominant carriers
        # This is a simplified mapping for demonstration
        dominant_carriers = {
            # Major carriers by region (examples - not exhaustive)
            '740': 'AT&T/Verizon',  # Ohio - mixed
            '614': 'AT&T/T-Mobile',  # Columbus, OH
            '216': 'AT&T/Verizon',  # Cleveland, OH
            '513': 'AT&T/Verizon',  # Cincinnati, OH
            '419': 'AT&T/Verizon',  # Toledo, OH
            '330': 'AT&T/Verizon',  # Akron, OH
            '937': 'AT&T/Verizon',  # Dayton, OH

            # Pennsylvania
            '215': 'Verizon/Comcast',  # Philadelphia
            '412': 'Verizon/AT&T',  # Pittsburgh
            '717': 'Verizon',  # Harrisburg

            # West Virginia
            '304': 'Frontier/AT&T',  # Charleston
            '681': 'Frontier/AT&T',

            # Indiana
            '317': 'AT&T/Verizon',  # Indianapolis
            '260': 'AT&T/Frontier',  # Fort Wayne

            # Illinois
            '312': 'AT&T/T-Mobile',  # Chicago
            '773': 'AT&T/T-Mobile',  # Chicago
            '217': 'AT&T',  # Springfield

            # Kentucky
            '502': 'AT&T/T-Mobile',  # Louisville
            '859': 'AT&T/Verizon',  # Lexington

            # Tennessee
            '615': 'AT&T/T-Mobile',  # Nashville
            '901': 'AT&T/Verizon',  # Memphis
        }

        return dominant_carriers.get(area_code, '')
    
    async def batch_validate(self, phones: list) -> Dict[str, Dict]:
        """
        Validate multiple phone numbers at once.
        Returns dict mapping phone numbers to their validation results.
        """
        
        results = {}
        
        for phone in phones:
            result = await self.validate_and_lookup(phone)
            results[phone] = result
            
            # Rate limiting - wait 1 second between requests
            await asyncio.sleep(1)
        
        return results
    
    async def close(self):
        """Clean up session"""
        if self.session:
            await self.session.close()


# Utility function to extract phone numbers from text
def extract_phone_numbers(text: str) -> list:
    """
    Extract phone numbers from unstructured text with enhanced pattern matching.
    Handles multiple formats and validates results.
    Returns list of found phone numbers.
    """

    # Comprehensive regex patterns for different phone formats
    patterns = [
        # Standard US formats
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 123-456-7890 or 123.456.7890
        r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123)456-7890
        r'\d{10}',  # 1234567890 (10 digits)

        # With country code
        r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 (123) 456-7890
        r'1[-.\s]\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # 1-123-456-7890

        # International format (broader)
        r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',

        # With extensions
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}[\s]?(?:ext|x|extension)[\s]?\d{2,5}',
    ]

    found_numbers = []

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_numbers.extend(matches)

    # Validate and normalize results
    validated = []
    for phone in found_numbers:
        # Extract digits only for validation
        digits = re.sub(r'\D', '', phone)

        # Valid US phone numbers should have 10 or 11 digits
        if len(digits) == 10 or (len(digits) == 11 and digits[0] == '1'):
            validated.append(phone)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(validated))
