#!/usr/bin/env python3
"""
Result Builder
Assembles final organized search results
ONE JOB: Build the final result structure for API response
"""

from typing import Dict, List
from datetime import datetime


class ResultBuilder:
    """
    Builds final search result structure.
    Takes organized data and creates API-ready response.
    """

    def build_final_results(
        self,
        persons: List[Dict],
        search_params: Dict,
        metadata: Dict = None,
        ml_insights: Dict = None
    ) -> Dict:
        """
        Build final search results.

        Args:
            persons: List of organized person dicts
            search_params: Original search parameters
            metadata: Optional metadata (timing, sources, etc.)
            ml_insights: Optional ML predictions and insights

        Returns:
            Complete results dict ready for API response
        """
        metadata = metadata or {}
        ml_insights = ml_insights or {}

        results = {
            "search_params": search_params,
            "timestamp": datetime.now().isoformat(),
            "persons": persons,
            "total_persons_found": len(persons),
            "summary": self._build_summary(persons),
            "metadata": metadata,
            "ml_insights": self._build_ml_insights(ml_insights, persons)  # ML summary
        }

        return results

    def _build_summary(self, persons: List[Dict]) -> Dict:
        """Build summary statistics"""
        summary = {
            "total_persons": len(persons),
            "total_phones": sum(len(p.get("organized_phones", [])) for p in persons),
            "total_addresses": sum(len(p.get("organized_addresses", [])) for p in persons),
            "total_emails": sum(len(p.get("organized_emails", [])) for p in persons),
            "total_public_records": sum(len(p.get("public_records", [])) for p in persons),
            "total_web_mentions": sum(len(p.get("web_mentions", [])) for p in persons),
            "confidence_breakdown": self._count_confidence_levels(persons)
        }

        return summary

    def _count_confidence_levels(self, persons: List[Dict]) -> Dict:
        """Count persons by confidence level"""
        breakdown = {"high": 0, "medium": 0, "low": 0}

        for person in persons:
            confidence = person.get("overall_confidence", "medium")
            confidence_num = person.get("overall_confidence_score", 50)

            if confidence_num >= 70:
                breakdown["high"] += 1
            elif confidence_num >= 40:
                breakdown["medium"] += 1
            else:
                breakdown["low"] += 1

        return breakdown

    def _build_ml_insights(self, ml_insights: Dict, persons: List[Dict]) -> Dict:
        """
        Build ML insights summary for UI display.

        Args:
            ml_insights: Raw ML predictions from organizer
            persons: Final organized persons

        Returns:
            ML insights dict with user-friendly summaries
        """
        name_matches = ml_insights.get("name_matches", [])

        # Count ML-enhanced features
        ml_verified_count = 0
        name_variations_found = 0
        addresses_normalized = 0

        for person in persons:
            # Check if person has ML verification
            if person.get("merged_from_sources", 0) > 0:
                ml_verified_count += 1

            # Count address normalizations (if ML was used)
            for addr in person.get("organized_addresses", []):
                if addr.get("ml_parsed"):
                    addresses_normalized += 1

        insights = {
            "ml_enabled": len(name_matches) > 0,  # ML was used if predictions exist
            "name_matches_checked": len(name_matches),
            "ml_verified_persons": ml_verified_count,
            "addresses_normalized": addresses_normalized,
            "semantic_matching_used": any(m.get("method") == "sentence_bert" for m in name_matches),
            "predictions": {
                "name_matches": name_matches[:10]  # Limit to 10 for UI display
            }
        }

        return insights

    def add_cross_references(self, persons: List[Dict]) -> List[Dict]:
        """
        Add cross-references between persons (shared data).

        Args:
            persons: List of person dicts

        Returns:
            Persons with cross_references added
        """
        for i, person1 in enumerate(persons):
            cross_refs = []

            for j, person2 in enumerate(persons):
                if i == j:
                    continue  # Don't compare to self

                # Check for shared data
                shared = self._find_shared_data(person1, person2)

                if shared:
                    cross_refs.append({
                        "person_index": j,
                        "person_name": person2.get("name", "Unknown"),
                        "shared_data": shared
                    })

            person1["cross_references"] = cross_refs

        return persons

    def _find_shared_data(self, person1: Dict, person2: Dict) -> List[str]:
        """Find what data two persons share"""
        shared = []

        # Check phones
        phones1 = set(p.get("normalized", "") for p in person1.get("organized_phones", []))
        phones2 = set(p.get("normalized", "") for p in person2.get("organized_phones", []))
        if phones1 & phones2:
            shared.append("phone")

        # Check addresses
        addrs1 = set(a.get("normalized", "") for a in person1.get("organized_addresses", []))
        addrs2 = set(a.get("normalized", "") for a in person2.get("organized_addresses", []))
        if addrs1 & addrs2:
            shared.append("address")

        # Check emails
        emails1 = set(e.get("email", "") for e in person1.get("organized_emails", []))
        emails2 = set(e.get("email", "") for e in person2.get("organized_emails", []))
        if emails1 & emails2:
            shared.append("email")

        return shared

    def sort_persons_by_relevance(self, persons: List[Dict], search_params: Dict) -> List[Dict]:
        """
        Sort persons by relevance to search query.

        Most relevant first (highest confidence, most data, best name match)
        """
        def relevance_score(person: Dict) -> float:
            score = 0.0

            # Confidence is most important
            score += person.get("overall_confidence_score", 50)

            # Number of data points
            score += len(person.get("organized_phones", [])) * 5
            score += len(person.get("organized_addresses", [])) * 5
            score += len(person.get("organized_emails", [])) * 3
            score += len(person.get("public_records", [])) * 10

            # User input match
            if "user_input" in person.get("confidence_sources", []):
                score += 20

            return score

        return sorted(persons, key=relevance_score, reverse=True)
