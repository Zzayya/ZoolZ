"""
Temporal Dataset Manager - Historical Intelligence System

Manages temporal datasets for tracking person history over time.
Stores address history, phone history, and detects patterns.

Created: November 18, 2025
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class TemporalDatasetManager:
    """
    Manages temporal datasets for historical person tracking.

    Datasets:
    - address_history.jsonl: All addresses seen for each person
    - phone_history.jsonl: All phone numbers seen for each person
    - movement_patterns.jsonl: Detected relocations
    - relationship_graph.jsonl: Detected relationships
    """

    def __init__(self, datasets_path: str = "utils/people_finder/datasets"):
        """
        Initialize temporal dataset manager.

        Args:
            datasets_path: Root path for dataset storage
        """
        self.datasets_path = datasets_path
        self.temporal_path = os.path.join(datasets_path, "temporal")
        self.relationships_path = os.path.join(datasets_path, "relationships")

        # Ensure directories exist
        os.makedirs(self.temporal_path, exist_ok=True)
        os.makedirs(self.relationships_path, exist_ok=True)

        # Dataset file paths
        self.address_history_path = os.path.join(self.temporal_path, "address_history.jsonl")
        self.phone_history_path = os.path.join(self.temporal_path, "phone_history.jsonl")
        self.movement_patterns_path = os.path.join(self.temporal_path, "movement_patterns.jsonl")
        self.relationship_graph_path = os.path.join(self.relationships_path, "relationship_graph.jsonl")

        # Initialize files if they don't exist
        for file_path in [self.address_history_path, self.phone_history_path,
                         self.movement_patterns_path, self.relationship_graph_path]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass  # Create empty file

    def save_address_history(self, person_uuid: str, addresses: List[Dict[str, Any]]) -> bool:
        """
        Save or update address history for a person.

        Args:
            person_uuid: Person's unique identifier
            addresses: List of address dictionaries

        Returns:
            True if successful
        """
        if not addresses:
            return True

        timestamp = datetime.now().isoformat()

        try:
            # Read existing history to check for duplicates
            existing_addresses = self._get_existing_addresses(person_uuid)

            # Process each address
            for addr in addresses:
                if isinstance(addr, dict):
                    address_str = addr.get('full_address', str(addr))
                else:
                    address_str = str(addr)

                # Normalize address
                address_normalized = self._normalize_address(address_str)

                # Check if this address already exists
                if address_normalized not in existing_addresses:
                    record = {
                        "person_uuid": person_uuid,
                        "address": address_str,
                        "address_normalized": address_normalized,
                        "first_seen": timestamp,
                        "last_seen": timestamp,
                        "status": "current",
                        "source": "search",
                        "confidence": 0.85
                    }

                    with open(self.address_history_path, 'a') as f:
                        f.write(json.dumps(record) + "\n")

                    existing_addresses.add(address_normalized)
                else:
                    # Update last_seen for existing address
                    self._update_address_last_seen(person_uuid, address_normalized, timestamp)

            return True
        except Exception as e:
            print(f"⚠️ Error saving address history: {e}")
            return False

    def save_phone_history(self, person_uuid: str, phones: List[Dict[str, Any]]) -> bool:
        """
        Save or update phone history for a person.

        Args:
            person_uuid: Person's unique identifier
            phones: List of phone dictionaries

        Returns:
            True if successful
        """
        if not phones:
            return True

        timestamp = datetime.now().isoformat()

        try:
            # Read existing history
            existing_phones = self._get_existing_phones(person_uuid)

            # Process each phone
            for phone in phones:
                if isinstance(phone, dict):
                    phone_number = phone.get('number', str(phone))
                    carrier = phone.get('carrier', 'Unknown')
                    line_type = phone.get('line_type', 'Unknown')
                else:
                    phone_number = str(phone)
                    carrier = 'Unknown'
                    line_type = 'Unknown'

                # Normalize phone
                phone_normalized = self._normalize_phone(phone_number)

                # Check if this phone already exists
                if phone_normalized not in existing_phones:
                    record = {
                        "person_uuid": person_uuid,
                        "phone": phone_number,
                        "phone_normalized": phone_normalized,
                        "carrier": carrier,
                        "line_type": line_type,
                        "first_seen": timestamp,
                        "last_seen": timestamp,
                        "status": "active",
                        "source": "search"
                    }

                    with open(self.phone_history_path, 'a') as f:
                        f.write(json.dumps(record) + "\n")

                    existing_phones.add(phone_normalized)
                else:
                    # Update last_seen for existing phone
                    self._update_phone_last_seen(person_uuid, phone_normalized, timestamp)

            return True
        except Exception as e:
            print(f"⚠️ Error saving phone history: {e}")
            return False

    def get_address_history(self, person_uuid: str) -> List[Dict[str, Any]]:
        """
        Get all addresses for a person, sorted by first_seen.

        Args:
            person_uuid: Person's unique identifier

        Returns:
            List of address records
        """
        addresses = []

        if not os.path.exists(self.address_history_path):
            return addresses

        try:
            with open(self.address_history_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == person_uuid:
                            addresses.append(record)
                    except json.JSONDecodeError:
                        continue

            # Sort by first_seen
            addresses.sort(key=lambda x: x.get('first_seen', ''))
        except Exception as e:
            print(f"⚠️ Error reading address history: {e}")

        return addresses

    def get_phone_history(self, person_uuid: str) -> List[Dict[str, Any]]:
        """
        Get all phones for a person, sorted by first_seen.

        Args:
            person_uuid: Person's unique identifier

        Returns:
            List of phone records
        """
        phones = []

        if not os.path.exists(self.phone_history_path):
            return phones

        try:
            with open(self.phone_history_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == person_uuid:
                            phones.append(record)
                    except json.JSONDecodeError:
                        continue

            # Sort by first_seen
            phones.sort(key=lambda x: x.get('first_seen', ''))
        except Exception as e:
            print(f"⚠️ Error reading phone history: {e}")

        return phones

    def detect_movement(self, person_uuid: str, new_addresses: List[str]) -> Optional[Dict[str, Any]]:
        """
        Detect if person has moved based on address history.

        Args:
            person_uuid: Person's unique identifier
            new_addresses: List of new addresses from search

        Returns:
            Movement pattern dictionary if detected, None otherwise
        """
        if not new_addresses:
            return None

        # Get address history
        history = self.get_address_history(person_uuid)

        if not history:
            # First time seeing this person
            return None

        # Get most recent previous address
        if len(history) > 0:
            previous = history[-1]
            previous_addr = previous.get('address_normalized', '')

            # Check if new address is different
            for new_addr in new_addresses:
                new_addr_normalized = self._normalize_address(str(new_addr))

                if new_addr_normalized != previous_addr:
                    # Possible movement detected
                    movement = {
                        "person_uuid": person_uuid,
                        "movement_type": "relocation",
                        "from_address": previous.get('address', ''),
                        "to_address": str(new_addr),
                        "from_date": previous.get('last_seen', ''),
                        "to_date": datetime.now().isoformat(),
                        "detected_on": datetime.now().isoformat(),
                        "confidence": 0.75,
                        "evidence": ["address_change"]
                    }

                    # Save movement pattern
                    try:
                        with open(self.movement_patterns_path, 'a') as f:
                            f.write(json.dumps(movement) + "\n")
                    except Exception as e:
                        print(f"⚠️ Error saving movement pattern: {e}")

                    return movement

        return None

    def get_historical_context(self, person_uuid: str) -> Dict[str, Any]:
        """
        Get complete historical context for a person.

        Args:
            person_uuid: Person's unique identifier

        Returns:
            Dictionary with historical context
        """
        context = {
            "person_uuid": person_uuid,
            "has_history": False,
            "address_history": [],
            "phone_history": [],
            "movement_patterns": [],
            "total_addresses": 0,
            "total_phones": 0
        }

        # Get address history
        addresses = self.get_address_history(person_uuid)
        if addresses:
            context["has_history"] = True
            context["address_history"] = addresses
            context["total_addresses"] = len(addresses)

        # Get phone history
        phones = self.get_phone_history(person_uuid)
        if phones:
            context["has_history"] = True
            context["phone_history"] = phones
            context["total_phones"] = len(phones)

        # Get movement patterns
        movements = self._get_movement_patterns(person_uuid)
        if movements:
            context["movement_patterns"] = movements

        return context

    # Private helper methods

    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""

        address = address.upper()
        address = " ".join(address.split())

        replacements = {
            " STREET": " ST",
            " AVENUE": " AVE",
            " ROAD": " RD",
            " DRIVE": " DR",
            " BOULEVARD": " BLVD",
            " LANE": " LN"
        }

        for old, new in replacements.items():
            address = address.replace(old, new)

        return address

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone to digits only."""
        if not phone:
            return ""
        return "".join(c for c in phone if c.isdigit())

    def _get_existing_addresses(self, person_uuid: str) -> set:
        """Get set of existing normalized addresses for person."""
        existing = set()

        if not os.path.exists(self.address_history_path):
            return existing

        try:
            with open(self.address_history_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == person_uuid:
                            existing.add(record.get('address_normalized', ''))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️ Error reading existing addresses: {e}")

        return existing

    def _get_existing_phones(self, person_uuid: str) -> set:
        """Get set of existing normalized phones for person."""
        existing = set()

        if not os.path.exists(self.phone_history_path):
            return existing

        try:
            with open(self.phone_history_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == person_uuid:
                            existing.add(record.get('phone_normalized', ''))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️ Error reading existing phones: {e}")

        return existing

    def _update_address_last_seen(self, person_uuid: str, address_normalized: str, timestamp: str) -> bool:
        """Update last_seen timestamp for an existing address."""
        if not os.path.exists(self.address_history_path):
            return False

        try:
            records = []
            updated = False

            with open(self.address_history_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)

                        if (record.get('person_uuid') == person_uuid and
                            record.get('address_normalized') == address_normalized):
                            record['last_seen'] = timestamp
                            updated = True

                        records.append(record)
                    except json.JSONDecodeError:
                        continue

            if updated:
                with open(self.address_history_path, 'w') as f:
                    for record in records:
                        f.write(json.dumps(record) + "\n")
                return True
        except Exception as e:
            print(f"⚠️ Error updating address last_seen: {e}")

        return False

    def _update_phone_last_seen(self, person_uuid: str, phone_normalized: str, timestamp: str) -> bool:
        """Update last_seen timestamp for an existing phone."""
        if not os.path.exists(self.phone_history_path):
            return False

        try:
            records = []
            updated = False

            with open(self.phone_history_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)

                        if (record.get('person_uuid') == person_uuid and
                            record.get('phone_normalized') == phone_normalized):
                            record['last_seen'] = timestamp
                            updated = True

                        records.append(record)
                    except json.JSONDecodeError:
                        continue

            if updated:
                with open(self.phone_history_path, 'w') as f:
                    for record in records:
                        f.write(json.dumps(record) + "\n")
                return True
        except Exception as e:
            print(f"⚠️ Error updating phone last_seen: {e}")

        return False

    def _get_movement_patterns(self, person_uuid: str) -> List[Dict[str, Any]]:
        """Get all movement patterns for a person."""
        patterns = []

        if not os.path.exists(self.movement_patterns_path):
            return patterns

        try:
            with open(self.movement_patterns_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == person_uuid:
                            patterns.append(record)
                    except json.JSONDecodeError:
                        continue

            # Sort by detected_on
            patterns.sort(key=lambda x: x.get('detected_on', ''))
        except Exception as e:
            print(f"⚠️ Error reading movement patterns: {e}")

        return patterns
