#!/usr/bin/env python3
"""
Advanced Address Parser and Normalizer
Professional-grade address handling for deduplication and validation

NOW WITH ML: Uses pre-trained usaddress for better parsing accuracy
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

# Try to import ML models
try:
    from .ml_models import ml_models
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class AddressParser:
    """
    Advanced address parser with normalization, deduplication, and validation.
    Handles multiple formats and provides confidence scoring.

    ML Features:
    - usaddress ML model for component extraction (handles non-standard formats)
    - Learns address patterns over time via memory manager
    - Tracks parses for dataset creation
    """

    # Street type abbreviations (comprehensive list)
    STREET_TYPES = {
        'alley': 'aly', 'anex': 'anx', 'arcade': 'arc', 'avenue': 'ave',
        'bayou': 'byu', 'beach': 'bch', 'bend': 'bnd', 'bluff': 'blf',
        'boulevard': 'blvd', 'branch': 'br', 'bridge': 'brg', 'brook': 'brk',
        'burg': 'bg', 'bypass': 'byp', 'camp': 'cp', 'canyon': 'cyn',
        'cape': 'cpe', 'causeway': 'cswy', 'center': 'ctr', 'circle': 'cir',
        'cliff': 'clf', 'club': 'clb', 'common': 'cmn', 'corner': 'cor',
        'course': 'crse', 'court': 'ct', 'cove': 'cv', 'creek': 'crk',
        'crescent': 'cres', 'crossing': 'xing', 'dale': 'dl', 'dam': 'dm',
        'divide': 'dv', 'drive': 'dr', 'estate': 'est', 'expressway': 'expy',
        'extension': 'ext', 'fall': 'fall', 'ferry': 'fry', 'field': 'fld',
        'flat': 'flt', 'ford': 'frd', 'forest': 'frst', 'forge': 'frg',
        'fork': 'frk', 'fort': 'ft', 'freeway': 'fwy', 'garden': 'gdn',
        'gateway': 'gtwy', 'glen': 'gln', 'green': 'grn', 'grove': 'grv',
        'harbor': 'hbr', 'haven': 'hvn', 'heights': 'hts', 'highway': 'hwy',
        'hill': 'hl', 'hollow': 'holw', 'inlet': 'inlt', 'island': 'is',
        'isle': 'isle', 'junction': 'jct', 'key': 'ky', 'knoll': 'knl',
        'lake': 'lk', 'land': 'land', 'landing': 'lndg', 'lane': 'ln',
        'light': 'lgt', 'loaf': 'lf', 'lock': 'lck', 'lodge': 'ldg',
        'loop': 'loop', 'mall': 'mall', 'manor': 'mnr', 'meadow': 'mdw',
        'mill': 'ml', 'mission': 'msn', 'mount': 'mt', 'mountain': 'mtn',
        'neck': 'nck', 'orchard': 'orch', 'oval': 'oval', 'park': 'park',
        'parkway': 'pkwy', 'pass': 'pass', 'path': 'path', 'pike': 'pike',
        'pine': 'pne', 'place': 'pl', 'plain': 'pln', 'plaza': 'plz',
        'point': 'pt', 'port': 'prt', 'prairie': 'pr', 'radial': 'radl',
        'ranch': 'rnch', 'rapid': 'rpd', 'rest': 'rst', 'ridge': 'rdg',
        'river': 'riv', 'road': 'rd', 'route': 'rte', 'row': 'row',
        'rue': 'rue', 'run': 'run', 'shoal': 'shl', 'shore': 'shr',
        'skyway': 'skwy', 'spring': 'spg', 'spur': 'spur', 'square': 'sq',
        'station': 'sta', 'stravenue': 'stra', 'stream': 'strm', 'street': 'st',
        'summit': 'smt', 'terrace': 'ter', 'throughway': 'trwy', 'trace': 'trce',
        'track': 'trak', 'trail': 'trl', 'trailer': 'trlr', 'tunnel': 'tunl',
        'turnpike': 'tpke', 'underpass': 'upas', 'union': 'un', 'valley': 'vly',
        'viaduct': 'via', 'view': 'vw', 'village': 'vlg', 'ville': 'vl',
        'vista': 'vis', 'walk': 'walk', 'wall': 'wall', 'way': 'way',
        'well': 'wl', 'wells': 'wls'
    }

    # Directional abbreviations
    DIRECTIONALS = {
        'north': 'n', 'south': 's', 'east': 'e', 'west': 'w',
        'northeast': 'ne', 'northwest': 'nw', 'southeast': 'se', 'southwest': 'sw',
        'n': 'n', 's': 's', 'e': 'e', 'w': 'w',
        'ne': 'ne', 'nw': 'nw', 'se': 'se', 'sw': 'sw'
    }

    # Unit type abbreviations
    UNIT_TYPES = {
        'apartment': 'apt', 'building': 'bldg', 'department': 'dept',
        'floor': 'fl', 'room': 'rm', 'suite': 'ste', 'unit': 'unit',
        '#': 'unit', 'number': 'unit'
    }

    # US State abbreviations
    US_STATES = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
        'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
    }

    def __init__(self, use_ml: bool = True):
        """
        Initialize address parser.

        Args:
            use_ml: Whether to use ML model (True = usaddress, False = regex only)
        """
        self.use_ml = use_ml and ML_AVAILABLE
        self.ml_parser = None

        if self.use_ml:
            try:
                self.ml_parser = ml_models.get_address_parser()
            except Exception as e:
                print(f"⚠ Could not load ML address parser: {e}")
                self.use_ml = False

    def parse_address(self, address: str, try_ml_first: bool = True) -> Dict:
        """
        Parse an address into its components.
        Tries ML parsing first if available, falls back to regex.

        Args:
            address: Raw address string
            try_ml_first: Whether to try ML model first

        Returns:
            Dict with keys: street_number, street_name, street_type, unit,
                           city, state, zip_code, full_normalized, ml_parsed
        """

        if not address:
            return {"full_normalized": "", "parsed": False, "ml_parsed": False}

        # Try ML parsing first
        if try_ml_first and self.use_ml and self.ml_parser:
            try:
                ml_result = self.ml_parser.parse_address(address)

                # If ML parsing was successful and confident, use it
                if ml_result.get("confidence", 0) >= 0.85:
                    # Convert ML format to our format
                    components = {
                        "street_number": ml_result["components"].get("number", ""),
                        "street_name": ml_result["components"].get("street", ""),
                        "unit_number": ml_result["components"].get("unit", ""),
                        "city": ml_result["components"].get("city", ""),
                        "state": ml_result["components"].get("state", ""),
                        "zip_code": ml_result["components"].get("zip", ""),
                        "full_normalized": self._build_normalized_from_ml(ml_result["components"]),
                        "parsed": True,
                        "ml_parsed": True,
                        "ml_confidence": ml_result.get("confidence", 0)
                    }
                    return components
            except Exception as e:
                # ML parsing failed, continue to regex fallback
                pass

        # Fallback to regex parsing
        # Clean the address
        cleaned = address.strip().lower()
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace

        components = {
            "street_number": "",
            "pre_directional": "",
            "street_name": "",
            "street_type": "",
            "post_directional": "",
            "unit_type": "",
            "unit_number": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "full_normalized": "",
            "parsed": True,
            "ml_parsed": False  # Using regex fallback
        }

        # Extract ZIP code (5 digits or 5+4)
        zip_match = re.search(r'\b(\d{5})(?:-(\d{4}))?\b', cleaned)
        if zip_match:
            components["zip_code"] = zip_match.group(0)
            cleaned = cleaned.replace(zip_match.group(0), '').strip()

        # Extract state (must be 2-letter abbreviation or full name)
        state_pattern = r'\b(' + '|'.join(self.US_STATES.keys()) + r')\b|\b(' + '|'.join(self.US_STATES.values()) + r')\b'
        state_match = re.search(state_pattern, cleaned, re.IGNORECASE)
        if state_match:
            state_text = state_match.group(0).lower()
            components["state"] = self.US_STATES.get(state_text, state_text.upper())
            cleaned = cleaned.replace(state_match.group(0), '').strip()

        # Split remaining parts (should be: street, city)
        parts = [p.strip() for p in cleaned.split(',') if p.strip()]

        if len(parts) >= 2:
            street_part = parts[0]
            components["city"] = parts[1].title()
        elif len(parts) == 1:
            street_part = parts[0]
        else:
            components["full_normalized"] = self.normalize_address(address)
            return components

        # Parse street address
        street_components = self._parse_street(street_part)
        components.update(street_components)

        # Build normalized address
        components["full_normalized"] = self._build_normalized(components)

        return components

    def _parse_street(self, street: str) -> Dict:
        """Parse street address into components"""

        components = {
            "street_number": "",
            "pre_directional": "",
            "street_name": "",
            "street_type": "",
            "post_directional": "",
            "unit_type": "",
            "unit_number": ""
        }

        # Remove punctuation except # (for unit numbers)
        street = re.sub(r'[^\w\s#-]', '', street)
        tokens = street.split()

        if not tokens:
            return components

        idx = 0

        # Extract street number (first numeric token)
        if tokens and re.match(r'^\d+[a-z]?$', tokens[idx], re.IGNORECASE):
            components["street_number"] = tokens[idx]
            idx += 1

        # Check for pre-directional
        if idx < len(tokens) and tokens[idx].lower() in self.DIRECTIONALS:
            components["pre_directional"] = self.DIRECTIONALS[tokens[idx].lower()]
            idx += 1

        # Extract unit info if present (e.g., "apt 5", "unit 202", "#123")
        unit_start_idx = None
        for i in range(idx, len(tokens)):
            token = tokens[i].lower()
            # Check for unit indicators
            if token in self.UNIT_TYPES or token.startswith('#'):
                unit_start_idx = i
                break

        # Extract street name and type (everything before unit info)
        end_idx = unit_start_idx if unit_start_idx else len(tokens)
        street_tokens = tokens[idx:end_idx]

        if street_tokens:
            # Check if last token is a street type
            last_token = street_tokens[-1].lower()
            if last_token in self.STREET_TYPES:
                components["street_type"] = self.STREET_TYPES[last_token]
                street_tokens = street_tokens[:-1]

            # Check if last remaining token is post-directional
            if street_tokens and street_tokens[-1].lower() in self.DIRECTIONALS:
                components["post_directional"] = self.DIRECTIONALS[street_tokens[-1].lower()]
                street_tokens = street_tokens[:-1]

            # Remaining tokens are street name
            components["street_name"] = ' '.join(street_tokens).title()

        # Extract unit info
        if unit_start_idx:
            unit_tokens = tokens[unit_start_idx:]
            if unit_tokens:
                unit_type = unit_tokens[0].lower().replace('#', 'unit')
                components["unit_type"] = self.UNIT_TYPES.get(unit_type, unit_type)

                if len(unit_tokens) > 1:
                    components["unit_number"] = ' '.join(unit_tokens[1:])
                elif unit_tokens[0].startswith('#'):
                    components["unit_number"] = unit_tokens[0][1:]

        return components

    def _build_normalized(self, components: Dict) -> str:
        """Build normalized address from components"""

        parts = []

        # Street number
        if components.get("street_number"):
            parts.append(components["street_number"])

        # Pre-directional
        if components.get("pre_directional"):
            parts.append(components["pre_directional"].upper())

        # Street name
        if components.get("street_name"):
            parts.append(components["street_name"])

        # Street type
        if components.get("street_type"):
            parts.append(components["street_type"].upper())

        # Post-directional
        if components.get("post_directional"):
            parts.append(components["post_directional"].upper())

        # Unit info
        if components.get("unit_type") and components.get("unit_number"):
            parts.append(f"{components['unit_type']} {components['unit_number']}")

        street = ' '.join(parts)

        # City, State ZIP
        location_parts = []
        if components.get("city"):
            location_parts.append(components["city"])
        if components.get("state"):
            location_parts.append(components["state"])
        if components.get("zip_code"):
            location_parts.append(components["zip_code"])

        if location_parts:
            return f"{street}, {', '.join(location_parts)}"

        return street

    def normalize_address(self, address: str) -> str:
        """
        Normalize an address to a standard format.
        Handles abbreviations, capitalization, spacing.
        """

        if not address:
            return ""

        # Parse and rebuild
        components = self.parse_address(address)
        return components.get("full_normalized", address)

    def are_addresses_same(self, addr1: str, addr2: str, threshold: float = 0.85) -> bool:
        """
        Determine if two addresses are the same, accounting for variations.

        Args:
            addr1: First address
            addr2: Second address
            threshold: Similarity threshold (0-1)

        Returns:
            True if addresses are likely the same
        """

        if not addr1 or not addr2:
            return False

        # Normalize both addresses
        norm1 = self.normalize_address(addr1)
        norm2 = self.normalize_address(addr2)

        # Exact match after normalization
        if norm1.lower() == norm2.lower():
            return True

        # Fuzzy match using sequence matcher
        similarity = SequenceMatcher(None, norm1.lower(), norm2.lower()).ratio()

        if similarity >= threshold:
            return True

        # Component-based comparison
        comp1 = self.parse_address(addr1)
        comp2 = self.parse_address(addr2)

        # Key components must match
        key_components = ["street_number", "street_name", "zip_code"]
        matches = sum(1 for key in key_components
                     if comp1.get(key) and comp2.get(key) and
                        comp1[key].lower() == comp2[key].lower())

        # If 2+ key components match, consider it the same address
        return matches >= 2

    def deduplicate_addresses(self, addresses: List[str]) -> List[str]:
        """
        Remove duplicate addresses from a list, keeping the most complete version.

        Returns:
            List of unique addresses
        """

        if not addresses:
            return []

        unique = []

        for addr in addresses:
            is_duplicate = False
            for existing in unique:
                if self.are_addresses_same(addr, existing):
                    # Replace with longer/more complete version
                    if len(addr) > len(existing):
                        unique.remove(existing)
                        unique.append(addr)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(addr)

        return unique

    def detect_address_type(self, address: str) -> str:
        """
        Detect if address is PO Box, residential, business, etc.

        Returns:
            'po_box', 'residential', 'business', or 'unknown'
        """

        addr_lower = address.lower()

        # PO Box detection
        if re.search(r'\bp\.?o\.?\s*box\b', addr_lower) or re.search(r'\bpost office box\b', addr_lower):
            return 'po_box'

        # Business indicators
        business_keywords = ['suite', 'ste', 'floor', 'building', 'office', 'plaza', 'mall', 'center']
        if any(keyword in addr_lower for keyword in business_keywords):
            return 'business'

        # Apartment indicators (residential)
        residential_keywords = ['apt', 'apartment', 'unit']
        if any(keyword in addr_lower for keyword in residential_keywords):
            return 'residential'

        # Default to residential if it has a street number
        if re.search(r'^\d+\s', address.strip()):
            return 'residential'

        return 'unknown'

    def _build_normalized_from_ml(self, ml_components: Dict) -> str:
        """Build normalized address from ML-parsed components"""
        parts = []

        if ml_components.get("number"):
            parts.append(ml_components["number"])
        if ml_components.get("street"):
            parts.append(ml_components["street"])
        if ml_components.get("unit"):
            parts.append(f"Unit {ml_components['unit']}")

        street = " ".join(parts)

        if ml_components.get("city"):
            street += f", {ml_components['city']}"
        if ml_components.get("state"):
            street += f", {ml_components['state']}"
        if ml_components.get("zip"):
            street += f" {ml_components['zip']}"

        return street

    def extract_location(self, address: str) -> Dict:
        """
        Extract city, state, and ZIP from address.

        Returns:
            Dict with city, state, zip
        """

        components = self.parse_address(address)

        return {
            "city": components.get("city", ""),
            "state": components.get("state", ""),
            "zip_code": components.get("zip_code", "")
        }
