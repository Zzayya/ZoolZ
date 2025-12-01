#!/usr/bin/env python3
"""
Relationship Detector & Associate Finder
Builds relationship networks between people based on shared data
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from difflib import SequenceMatcher

# Try to import Levenshtein for fuzzy matching, fallback to difflib
try:
    from Levenshtein import ratio as levenshtein_ratio
except ImportError:
    # Fallback: Use difflib.SequenceMatcher
    def levenshtein_ratio(str1: str, str2: str) -> float:
        """Fallback implementation using difflib"""
        return SequenceMatcher(None, str1, str2).ratio()


class RelationshipDetector:
    """
    Detects relationships between people based on:
    - Shared addresses (family, roommates)
    - Shared phone numbers (family, close contacts)
    - Same last name (family relations)
    - Property co-ownership (spouse, family)
    - Age differences (parent/child, siblings)
    - Co-occurrence in records (associates)
    """

    def __init__(self):
        self.relationship_graph = nx.Graph()

    def analyze_relationships(self, persons: List[Dict]) -> Dict:
        """
        Analyze relationships between all persons found in search results.

        Returns:
            Dict with:
            - relationship_graph: NetworkX graph of relationships
            - associates: List of associates grouped by relationship type
            - relationship_summary: Summary statistics
        """

        # Build relationship graph
        self._build_relationship_graph(persons)

        # Classify relationships
        associates = self._classify_relationships(persons)

        # Generate summary
        summary = self._generate_relationship_summary(associates)

        return {
            "relationship_graph": self.relationship_graph,
            "associates": associates,
            "relationship_summary": summary,
            "total_persons": len(persons),
            "total_relationships": self.relationship_graph.number_of_edges()
        }

    def _build_relationship_graph(self, persons: List[Dict]):
        """
        Build a graph where nodes are people and edges are relationships.
        """

        # Add all persons as nodes
        for person in persons:
            person_name = person.get("name", "Unknown")
            self.relationship_graph.add_node(person_name, data=person)

        # Detect relationships between all pairs
        for i, person1 in enumerate(persons):
            for person2 in persons[i+1:]:
                relationships = self._detect_relationship_types(person1, person2)

                if relationships:
                    # Add edge with relationship types
                    name1 = person1.get("name", "Unknown")
                    name2 = person2.get("name", "Unknown")

                    self.relationship_graph.add_edge(
                        name1,
                        name2,
                        relationships=relationships,
                        strength=self._calculate_relationship_strength(relationships)
                    )

    def _detect_relationship_types(self, person1: Dict, person2: Dict) -> List[str]:
        """
        Detect all possible relationship types between two people.

        Returns list of relationship indicators:
        - "same_address": Live together (family, roommates)
        - "same_phone": Share phone (family, close contact)
        - "same_last_name": Family relation
        - "property_co_owner": Co-own property (spouse, family)
        - "age_parent_child": Age suggests parent/child
        - "age_sibling": Similar age suggests siblings
        - "business_associate": Linked in business records
        - "co_occurrence": Appear together in records
        """

        relationships = []

        # Check shared address
        if self._shares_address(person1, person2):
            relationships.append("same_address")

        # Check shared phone
        if self._shares_phone(person1, person2):
            relationships.append("same_phone")

        # Check same last name
        if self._same_last_name(person1, person2):
            relationships.append("same_last_name")

        # Check property co-ownership
        if self._property_co_owners(person1, person2):
            relationships.append("property_co_owner")

        # Check age-based relationships (if ages available)
        age_relation = self._detect_age_relationship(person1, person2)
        if age_relation:
            relationships.append(age_relation)

        # Check business association
        if self._business_associates(person1, person2):
            relationships.append("business_associate")

        # Check co-occurrence in records
        if self._co_occur_in_records(person1, person2):
            relationships.append("co_occurrence")

        return relationships

    def _shares_address(self, person1: Dict, person2: Dict) -> bool:
        """Check if two people share an address"""
        addresses1 = [addr.lower().strip() for addr in person1.get("addresses", [])]
        addresses2 = [addr.lower().strip() for addr in person2.get("addresses", [])]

        # Exact match
        if set(addresses1) & set(addresses2):
            return True

        # Fuzzy match (partial addresses)
        for addr1 in addresses1:
            for addr2 in addresses2:
                # Check if addresses are similar (>80% match)
                if levenshtein_ratio(addr1, addr2) > 0.8:
                    return True

        return False

    def _shares_phone(self, person1: Dict, person2: Dict) -> bool:
        """Check if two people share a phone number"""
        phones1 = set(person1.get("phones", []))
        phones2 = set(person2.get("phones", []))
        return bool(phones1 & phones2)

    def _same_last_name(self, person1: Dict, person2: Dict) -> bool:
        """Check if two people have the same last name"""
        name1 = person1.get("name", "")
        name2 = person2.get("name", "")

        if not name1 or not name2:
            return False

        # Extract last names
        last1 = name1.split()[-1].lower() if name1.split() else ""
        last2 = name2.split()[-1].lower() if name2.split() else ""

        # Exact match or very similar
        if last1 == last2:
            return True

        # Fuzzy match for typos
        if levenshtein_ratio(last1, last2) > 0.9:
            return True

        return False

    def _property_co_owners(self, person1: Dict, person2: Dict) -> bool:
        """
        Check if two people co-own property.
        Look for both names in the same property record.
        """

        records1 = person1.get("public_records", [])
        records2 = person2.get("public_records", [])

        name1 = person1.get("name", "").lower()
        name2 = person2.get("name", "").lower()

        # Check if both names appear in same record
        for record in records1:
            if isinstance(record, dict):
                record_text = str(record).lower()
                if name1 in record_text and name2 in record_text:
                    return True

        for record in records2:
            if isinstance(record, dict):
                record_text = str(record).lower()
                if name1 in record_text and name2 in record_text:
                    return True

        return False

    def _detect_age_relationship(self, person1: Dict, person2: Dict) -> Optional[str]:
        """
        Detect age-based relationships (parent/child, siblings).
        Returns "age_parent_child", "age_sibling", or None.
        """

        # Try to extract ages from records
        age1 = self._extract_age(person1)
        age2 = self._extract_age(person2)

        if not age1 or not age2:
            return None

        age_diff = abs(age1 - age2)

        # Parent/child relationship (20+ years age difference)
        if age_diff >= 20:
            return "age_parent_child"

        # Sibling relationship (0-10 years age difference + same last name)
        if age_diff <= 10 and self._same_last_name(person1, person2):
            return "age_sibling"

        return None

    def _extract_age(self, person: Dict) -> Optional[int]:
        """
        Try to extract age from person's records.
        Look for birth dates, ages, etc.
        """

        # Check public records for age indicators
        records = person.get("public_records", [])

        for record in records:
            if isinstance(record, dict):
                # Look for age field
                if "age" in record:
                    try:
                        return int(record["age"])
                    except:
                        pass

                # Look for DOB field
                if "date_of_birth" in record or "dob" in record:
                    dob = record.get("date_of_birth") or record.get("dob")
                    age = self._calculate_age_from_dob(dob)
                    if age:
                        return age

                # Look for birth year in text
                record_text = str(record)
                birth_year_match = re.search(r'born[:\s]+(\d{4})', record_text, re.IGNORECASE)
                if birth_year_match:
                    birth_year = int(birth_year_match.group(1))
                    current_year = datetime.now().year
                    return current_year - birth_year

        return None

    def _calculate_age_from_dob(self, dob: str) -> Optional[int]:
        """Calculate age from date of birth string"""
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]:
                try:
                    birth_date = datetime.strptime(dob, fmt)
                    today = datetime.now()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    return age
                except:
                    continue
        except:
            pass

        return None

    def _business_associates(self, person1: Dict, person2: Dict) -> bool:
        """
        Check if two people are business associates.
        Look for business records linking them.
        """

        records1 = person1.get("public_records", [])
        records2 = person2.get("public_records", [])

        name1 = person1.get("name", "").lower()
        name2 = person2.get("name", "").lower()

        # Check for business-related records
        business_keywords = ["llc", "inc", "corp", "business", "company", "partner", "owner"]

        for record in records1:
            if isinstance(record, dict):
                record_text = str(record).lower()
                # If record contains business keywords and both names
                if any(keyword in record_text for keyword in business_keywords):
                    if name2 in record_text:
                        return True

        return False

    def _co_occur_in_records(self, person1: Dict, person2: Dict) -> bool:
        """
        Check if two people co-occur in the same records.
        Indicates some level of association.
        """

        name1 = person1.get("name", "").lower()
        name2 = person2.get("name", "").lower()

        # Check web mentions
        mentions1 = person1.get("web_mentions", [])
        mentions2 = person2.get("web_mentions", [])

        for mention in mentions1:
            if isinstance(mention, dict):
                text = (mention.get("title", "") + " " + mention.get("snippet", "")).lower()
                if name2 in text:
                    return True

        for mention in mentions2:
            if isinstance(mention, dict):
                text = (mention.get("title", "") + " " + mention.get("snippet", "")).lower()
                if name1 in text:
                    return True

        return False

    def _calculate_relationship_strength(self, relationships: List[str]) -> float:
        """
        Calculate relationship strength (0.0 - 1.0) based on indicators.

        Stronger relationships:
        - same_address + same_last_name = very strong (family)
        - same_address + same_phone = very strong (family)
        - property_co_owner = strong (spouse/family)
        - same_phone = strong (close contact)
        - same_address alone = medium (roommates)
        - co_occurrence = weak (associates)
        """

        strength = 0.0

        # Weight each relationship type
        weights = {
            "same_address": 0.3,
            "same_phone": 0.3,
            "same_last_name": 0.25,
            "property_co_owner": 0.35,
            "age_parent_child": 0.2,
            "age_sibling": 0.2,
            "business_associate": 0.15,
            "co_occurrence": 0.1
        }

        for rel_type in relationships:
            strength += weights.get(rel_type, 0.1)

        # Bonus for multiple strong indicators
        if "same_address" in relationships and "same_last_name" in relationships:
            strength += 0.3  # Likely immediate family

        if "same_address" in relationships and "same_phone" in relationships:
            strength += 0.3  # Likely family or very close

        # Cap at 1.0
        return min(strength, 1.0)

    def _classify_relationships(self, persons: List[Dict]) -> Dict:
        """
        Classify all relationships into categories for display.

        Categories:
        - immediate_family: Same address + same last name OR property co-owners
        - possible_spouse: Same address + different last name + property co-owners
        - possible_parent: Age difference 20+ years + same last name
        - possible_child: Age difference 20+ years + same last name
        - possible_sibling: Similar age + same last name + same address
        - roommate: Same address + different last name
        - business_associate: Business records link them
        - close_contact: Share phone number
        - possible_friend: Co-occur in records
        """

        classified = {
            "immediate_family": [],
            "possible_spouse": [],
            "possible_parent": [],
            "possible_child": [],
            "possible_sibling": [],
            "roommate": [],
            "business_associate": [],
            "close_contact": [],
            "possible_friend": [],
            "other_associate": []
        }

        # Analyze each edge in the graph
        for person1_name, person2_name, data in self.relationship_graph.edges(data=True):
            relationships = data.get("relationships", [])
            strength = data.get("strength", 0.0)

            # Get person data
            person1 = self.relationship_graph.nodes[person1_name]["data"]
            person2 = self.relationship_graph.nodes[person2_name]["data"]

            # Classify relationship
            category = self._determine_relationship_category(
                person1, person2, relationships, strength
            )

            classified[category].append({
                "person1": person1_name,
                "person2": person2_name,
                "relationship_indicators": relationships,
                "strength": strength,
                "shared_data": self._identify_shared_data_detailed(person1, person2)
            })

        return classified

    def _determine_relationship_category(
        self,
        person1: Dict,
        person2: Dict,
        relationships: List[str],
        strength: float
    ) -> str:
        """
        Determine the primary relationship category.
        """

        # Immediate family: Same address + same last name
        if "same_address" in relationships and "same_last_name" in relationships:
            # Check if parent/child or sibling
            if "age_parent_child" in relationships:
                # Determine who is parent vs child by age
                age1 = self._extract_age(person1)
                age2 = self._extract_age(person2)
                if age1 and age2:
                    if age1 > age2:
                        return "possible_parent"  # person1 is parent of person2
                    else:
                        return "possible_child"  # person1 is child of person2
                return "immediate_family"
            elif "age_sibling" in relationships:
                return "possible_sibling"
            else:
                return "immediate_family"

        # Possible spouse: Same address + different last name + property co-owner
        if "same_address" in relationships and "property_co_owner" in relationships:
            if not self._same_last_name(person1, person2):
                return "possible_spouse"

        # Business associate
        if "business_associate" in relationships:
            return "business_associate"

        # Roommate: Same address but different last name
        if "same_address" in relationships:
            return "roommate"

        # Close contact: Share phone
        if "same_phone" in relationships:
            return "close_contact"

        # Co-occurrence: Appear together
        if "co_occurrence" in relationships:
            return "possible_friend"

        return "other_associate"

    def _identify_shared_data_detailed(self, person1: Dict, person2: Dict) -> Dict:
        """
        Identify all shared data between two people.
        """

        shared = {
            "addresses": [],
            "phones": [],
            "emails": [],
            "records": []
        }

        # Shared addresses
        addresses1 = set(addr.lower().strip() for addr in person1.get("addresses", []))
        addresses2 = set(addr.lower().strip() for addr in person2.get("addresses", []))
        shared["addresses"] = list(addresses1 & addresses2)

        # Shared phones
        phones1 = set(person1.get("phones", []))
        phones2 = set(person2.get("phones", []))
        shared["phones"] = list(phones1 & phones2)

        # Shared emails
        emails1 = set(person1.get("emails", []))
        emails2 = set(person2.get("emails", []))
        shared["emails"] = list(emails1 & emails2)

        return shared

    def _generate_relationship_summary(self, associates: Dict) -> Dict:
        """
        Generate summary statistics about relationships found.
        """

        summary = {
            "total_associates": 0,
            "by_category": {}
        }

        for category, relationships in associates.items():
            count = len(relationships)
            summary["by_category"][category] = count
            summary["total_associates"] += count

        return summary

    def find_degrees_of_separation(self, person1_name: str, person2_name: str) -> Optional[List]:
        """
        Find the shortest path (degrees of separation) between two people.

        Example:
        - John -> Mary (1 degree: direct connection)
        - John -> Mary -> Bob (2 degrees: connected through Mary)
        """

        try:
            path = nx.shortest_path(self.relationship_graph, person1_name, person2_name)
            return path
        except nx.NetworkXNoPath:
            return None

    def get_associate_network(self, person_name: str, max_depth: int = 2) -> Dict:
        """
        Get all associates within N degrees of separation.

        Args:
            person_name: Center person
            max_depth: How many degrees of separation (1=direct, 2=friends of friends)

        Returns:
            Dict with associates grouped by depth
        """

        if person_name not in self.relationship_graph:
            return {"error": "Person not found in graph"}

        associates_by_depth = {}

        # Get associates at each depth level
        for depth in range(1, max_depth + 1):
            associates_by_depth[depth] = []

            # Use BFS to find nodes at specific depth
            nodes_at_depth = nx.single_source_shortest_path_length(
                self.relationship_graph,
                person_name,
                cutoff=depth
            )

            for node, distance in nodes_at_depth.items():
                if distance == depth:
                    # Get relationship data
                    edge_data = self.relationship_graph.get_edge_data(person_name, node)
                    if edge_data:
                        associates_by_depth[depth].append({
                            "name": node,
                            "relationships": edge_data.get("relationships", []),
                            "strength": edge_data.get("strength", 0.0)
                        })

        return associates_by_depth
