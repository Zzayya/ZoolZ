"""
Person Identifier - UUID Generation for Temporal Tracking

Generates unique identifiers for persons to track them across searches.
Uses fuzzy matching to avoid duplicates while preventing false merges.

Created: November 18, 2025
"""

import hashlib
import json
import os
from typing import Optional, Dict, List, Any
from datetime import datetime


class PersonIdentifier:
    """
    Generates and manages unique person UUIDs for temporal tracking.

    Purpose:
    - Create unique IDs for persons based on identifying data
    - Avoid mixing different people with the same name
    - Find existing persons across searches
    - Verify if two UUIDs represent the same person
    """

    def __init__(self, datasets_path: str = "utils/people_finder/datasets"):
        """
        Initialize person identifier.

        Args:
            datasets_path: Root path for dataset storage
        """
        self.datasets_path = datasets_path
        self.person_master_path = os.path.join(datasets_path, "person_master.jsonl")

        # Ensure datasets directory exists
        os.makedirs(datasets_path, exist_ok=True)

        # Initialize person master file if it doesn't exist
        if not os.path.exists(self.person_master_path):
            with open(self.person_master_path, 'w') as f:
                pass  # Create empty file

    def normalize_name(self, name: str) -> str:
        """
        Normalize name for consistent UUID generation.

        Args:
            name: Raw name string

        Returns:
            Normalized name (uppercase, no extra spaces)
        """
        if not name:
            return ""

        # Convert to uppercase
        name = name.upper()

        # Remove extra spaces
        name = " ".join(name.split())

        # Remove common suffixes for matching
        suffixes = [" JR", " SR", " III", " II", " IV"]
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()

        return name

    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to digits only.

        Args:
            phone: Raw phone string

        Returns:
            Digits only (e.g., "2165551234")
        """
        if not phone:
            return ""

        # Keep only digits
        return "".join(c for c in phone if c.isdigit())

    def normalize_address(self, address: str) -> str:
        """
        Normalize address for matching.

        Args:
            address: Raw address string

        Returns:
            Normalized address
        """
        if not address:
            return ""

        # Convert to uppercase
        address = address.upper()

        # Remove extra spaces
        address = " ".join(address.split())

        # Common abbreviations
        replacements = {
            " STREET": " ST",
            " AVENUE": " AVE",
            " ROAD": " RD",
            " DRIVE": " DR",
            " BOULEVARD": " BLVD",
            " LANE": " LN",
            " COURT": " CT"
        }

        for old, new in replacements.items():
            address = address.replace(old, new)

        return address

    def generate_person_uuid(self, person_data: Dict[str, Any]) -> str:
        """
        Generate unique UUID for a person.

        Creates UUID based on:
        - Name (normalized)
        - Primary phone (if available)
        - Primary address (if available)
        - DOB (if available)

        Args:
            person_data: Dictionary with person information

        Returns:
            16-character hex UUID string
        """
        # Extract and normalize identifying data
        name = self.normalize_name(person_data.get('name', ''))

        # Get primary phone (first phone if multiple)
        phones = person_data.get('phones', [])
        primary_phone = ""
        if phones:
            if isinstance(phones[0], dict):
                primary_phone = self.normalize_phone(phones[0].get('number', ''))
            else:
                primary_phone = self.normalize_phone(str(phones[0]))

        # Get primary address (first address if multiple)
        addresses = person_data.get('addresses', [])
        primary_address = ""
        if addresses:
            if isinstance(addresses[0], dict):
                primary_address = self.normalize_address(addresses[0].get('full_address', ''))
            else:
                primary_address = self.normalize_address(str(addresses[0]))

        # Get DOB if available
        dob = person_data.get('dob', '')

        # Create fingerprint string
        fingerprint_parts = [name]

        if primary_phone:
            fingerprint_parts.append(primary_phone)

        if primary_address:
            fingerprint_parts.append(primary_address)

        if dob:
            fingerprint_parts.append(dob)

        fingerprint = "|".join(fingerprint_parts)

        # Generate UUID from fingerprint
        person_uuid = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()[:16]

        return person_uuid

    def find_existing_person(self, person_data: Dict[str, Any]) -> Optional[str]:
        """
        Check if person already exists in person_master.

        Args:
            person_data: Dictionary with person information

        Returns:
            UUID if found, None otherwise
        """
        # Generate UUID for this person
        candidate_uuid = self.generate_person_uuid(person_data)

        # Check if this UUID exists in person_master
        if not os.path.exists(self.person_master_path):
            return None

        try:
            with open(self.person_master_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == candidate_uuid:
                            return candidate_uuid
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️ Error reading person_master: {e}")
            return None

        return None

    def get_person_record(self, person_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get person record from person_master by UUID.

        Args:
            person_uuid: Person's UUID

        Returns:
            Person record dictionary or None
        """
        if not os.path.exists(self.person_master_path):
            return None

        try:
            with open(self.person_master_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        if record.get('person_uuid') == person_uuid:
                            return record
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️ Error reading person_master: {e}")
            return None

        return None

    def register_person(self, person_uuid: str, person_data: Dict[str, Any]) -> bool:
        """
        Register new person in person_master.jsonl.

        Args:
            person_uuid: Generated UUID
            person_data: Person information

        Returns:
            True if successful
        """
        # Check if already exists
        existing = self.get_person_record(person_uuid)

        if existing:
            # Update last_seen and increment sightings
            return self.update_person_sighting(person_uuid, person_data)

        # Create new record
        name = person_data.get('name', 'Unknown')

        record = {
            "person_uuid": person_uuid,
            "primary_name": name,
            "name_variations": [name],
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "total_sightings": 1,
            "confidence_level": "medium"
        }

        try:
            with open(self.person_master_path, 'a') as f:
                f.write(json.dumps(record) + "\n")
            return True
        except Exception as e:
            print(f"⚠️ Error registering person: {e}")
            return False

    def update_person_sighting(self, person_uuid: str, person_data: Dict[str, Any]) -> bool:
        """
        Update person record with new sighting.

        Args:
            person_uuid: Person's UUID
            person_data: New person data

        Returns:
            True if successful
        """
        # Read all records
        if not os.path.exists(self.person_master_path):
            return False

        try:
            records = []
            updated = False

            with open(self.person_master_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)

                        if record.get('person_uuid') == person_uuid:
                            # Update this record
                            record['last_seen'] = datetime.now().isoformat()
                            record['total_sightings'] = record.get('total_sightings', 0) + 1

                            # Add name variation if new
                            name = person_data.get('name', '')
                            if name and name not in record.get('name_variations', []):
                                record.setdefault('name_variations', []).append(name)

                            updated = True

                        records.append(record)
                    except json.JSONDecodeError:
                        continue

            # Write all records back
            if updated:
                with open(self.person_master_path, 'w') as f:
                    for record in records:
                        f.write(json.dumps(record) + "\n")
                return True
        except Exception as e:
            print(f"⚠️ Error updating person sighting: {e}")
            return False

        return False

    def get_all_persons(self) -> List[Dict[str, Any]]:
        """
        Get all person records.

        Returns:
            List of person records
        """
        persons = []

        if not os.path.exists(self.person_master_path):
            return persons

        try:
            with open(self.person_master_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        persons.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️ Error reading person_master: {e}")

        return persons
