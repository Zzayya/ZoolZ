#!/usr/bin/env python3
"""
Memory Manager - Running Memory System
Tracks model performance, learned patterns, and adjusts behavior over time.

VISION: Models learn from each search without retraining.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict


class MemoryManager:
    """
    Running memory for ML models.

    Tracks:
    1. Source reliability (which sources give good data)
    2. Pattern recognition (common name variations, address formats)
    3. Model performance (accuracy over time)
    4. Confidence calibration (adjust thresholds based on feedback)
    5. Common mistakes (to avoid repeating)

    Memory persists across restarts and improves over time.
    """

    def __init__(self, memory_path: str = "utils/people_finder/datasets/memory"):
        """
        Initialize memory manager.

        Args:
            memory_path: Directory for memory files
        """
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # Load existing memory
        self.model_performance = self._load_memory("model_performance.json")
        self.learned_patterns = self._load_memory("learned_patterns.json")
        self.source_reliability = self._load_memory("source_reliability.json")
        self.confidence_calibration = self._load_memory("confidence_calibration.json")

    def _load_memory(self, filename: str) -> Dict:
        """Load memory file or create new"""
        file_path = self.memory_path / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_memory(filename)

    def _get_default_memory(self, filename: str) -> Dict:
        """Get default memory structure"""
        defaults = {
            "model_performance.json": {
                "name_matching": {
                    "total_predictions": 0,
                    "correct_predictions": 0,
                    "incorrect_predictions": 0,
                    "accuracy": 0.0,
                    "last_updated": datetime.now().isoformat()
                },
                "entity_extraction": {
                    "total_extractions": 0,
                    "successful_extractions": 0,
                    "failed_extractions": 0,
                    "success_rate": 0.0,
                    "last_updated": datetime.now().isoformat()
                },
                "confidence_scoring": {
                    "total_scores": 0,
                    "avg_user_satisfaction": 0.0,
                    "calibration_error": 0.0,
                    "last_updated": datetime.now().isoformat()
                }
            },
            "learned_patterns.json": {
                "name_variations": {},        # {formal_name: [known_variations]}
                "address_formats": {},        # {state: [common_formats]}
                "phone_patterns": {},         # {area_code: {carrier_patterns}}
                "reliable_indicators": []     # Signals that indicate high confidence
            },
            "source_reliability.json": {
                "public_records": {"total_results": 0, "verified_correct": 0, "score": 0.5},
                "web_search": {"total_results": 0, "verified_correct": 0, "score": 0.5},
                "phone_validation": {"total_results": 0, "verified_correct": 0, "score": 0.5},
                "federal_records": {"total_results": 0, "verified_correct": 0, "score": 0.5}
            },
            "confidence_calibration.json": {
                "thresholds": {
                    "name_similarity": 0.85,    # Adjusts based on feedback
                    "high_confidence": 0.80,    # What counts as "high"
                    "medium_confidence": 0.60,  # What counts as "medium"
                    "low_confidence": 0.35      # What counts as "low"
                },
                "adjustments": {
                    "total_searches": 0,
                    "feedback_count": 0,
                    "last_calibration": datetime.now().isoformat()
                }
            }
        }
        return defaults.get(filename, {})

    def _save_memory(self, filename: str, data: Dict):
        """Save memory to file"""
        file_path = self.memory_path / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    # =========================
    # Model Performance Tracking
    # =========================

    def record_prediction(self, model_type: str, was_correct: bool):
        """
        Record a model prediction result.

        Args:
            model_type: "name_matching", "entity_extraction", "confidence_scoring"
            was_correct: Whether prediction was correct (from user feedback)
        """
        if model_type not in self.model_performance:
            self.model_performance[model_type] = {
                "total_predictions": 0,
                "correct_predictions": 0,
                "incorrect_predictions": 0,
                "accuracy": 0.0
            }

        perf = self.model_performance[model_type]
        perf["total_predictions"] += 1

        if was_correct:
            perf["correct_predictions"] += 1
        else:
            perf["incorrect_predictions"] += 1

        # Update accuracy
        perf["accuracy"] = perf["correct_predictions"] / perf["total_predictions"]
        perf["last_updated"] = datetime.now().isoformat()

        self._save_memory("model_performance.json", self.model_performance)

    def get_model_accuracy(self, model_type: str) -> float:
        """Get current accuracy for a model type"""
        return self.model_performance.get(model_type, {}).get("accuracy", 0.0)

    # =========================
    # Source Reliability Tracking
    # =========================

    def record_source_result(self, source: str, was_useful: bool):
        """
        Track reliability of data sources.

        Args:
            source: Source name (public_records, web_search, etc.)
            was_useful: Whether this source provided useful data
        """
        if source not in self.source_reliability:
            self.source_reliability[source] = {
                "total_results": 0,
                "verified_correct": 0,
                "score": 0.5
            }

        src = self.source_reliability[source]
        src["total_results"] += 1

        if was_useful:
            src["verified_correct"] += 1

        # Update reliability score (exponential moving average)
        if src["total_results"] > 0:
            src["score"] = src["verified_correct"] / src["total_results"]

        self._save_memory("source_reliability.json", self.source_reliability)

    def get_source_reliability(self, source: str) -> float:
        """Get reliability score for a source (0.0 to 1.0)"""
        return self.source_reliability.get(source, {}).get("score", 0.5)

    # =========================
    # Pattern Learning
    # =========================

    def learn_name_variation(self, formal_name: str, variation: str):
        """
        Learn that a name variation exists.

        Args:
            formal_name: Formal name (e.g., "William")
            variation: Variation (e.g., "Bill")
        """
        if "name_variations" not in self.learned_patterns:
            self.learned_patterns["name_variations"] = {}

        formal_lower = formal_name.lower()
        variation_lower = variation.lower()

        if formal_lower not in self.learned_patterns["name_variations"]:
            self.learned_patterns["name_variations"][formal_lower] = []

        if variation_lower not in self.learned_patterns["name_variations"][formal_lower]:
            self.learned_patterns["name_variations"][formal_lower].append(variation_lower)

        self._save_memory("learned_patterns.json", self.learned_patterns)

    def get_known_variations(self, name: str) -> List[str]:
        """Get known variations for a name"""
        name_lower = name.lower()
        return self.learned_patterns.get("name_variations", {}).get(name_lower, [])

    def learn_address_format(self, state: str, address_pattern: str):
        """
        Learn common address format for a state.

        Args:
            state: State code (OH, PA, etc.)
            address_pattern: Pattern (e.g., "number street type, city")
        """
        if "address_formats" not in self.learned_patterns:
            self.learned_patterns["address_formats"] = {}

        if state not in self.learned_patterns["address_formats"]:
            self.learned_patterns["address_formats"][state] = []

        if address_pattern not in self.learned_patterns["address_formats"][state]:
            self.learned_patterns["address_formats"][state].append(address_pattern)

        self._save_memory("learned_patterns.json", self.learned_patterns)

    def learn_reliable_indicator(self, indicator: str):
        """
        Learn that a specific indicator suggests reliable data.

        Args:
            indicator: Description of indicator (e.g., "multiple_sources_agree")
        """
        if "reliable_indicators" not in self.learned_patterns:
            self.learned_patterns["reliable_indicators"] = []

        if indicator not in self.learned_patterns["reliable_indicators"]:
            self.learned_patterns["reliable_indicators"].append(indicator)

        self._save_memory("learned_patterns.json", self.learned_patterns)

    # =========================
    # Confidence Calibration
    # =========================

    def adjust_threshold(self, threshold_name: str, adjustment: float):
        """
        Adjust a confidence threshold based on feedback.

        Args:
            threshold_name: "name_similarity", "high_confidence", etc.
            adjustment: Amount to adjust (+/- 0.01 to 0.10)
        """
        if threshold_name in self.confidence_calibration["thresholds"]:
            current = self.confidence_calibration["thresholds"][threshold_name]
            new_value = max(0.0, min(1.0, current + adjustment))  # Clamp 0-1
            self.confidence_calibration["thresholds"][threshold_name] = new_value

            self.confidence_calibration["adjustments"]["last_calibration"] = datetime.now().isoformat()
            self._save_memory("confidence_calibration.json", self.confidence_calibration)

    def get_threshold(self, threshold_name: str) -> float:
        """Get current threshold value"""
        return self.confidence_calibration["thresholds"].get(threshold_name, 0.5)

    def record_user_feedback(self, predicted_confidence: str, user_agreed: bool):
        """
        Record whether user agreed with confidence level.

        Args:
            predicted_confidence: "high", "medium", "low"
            user_agreed: Whether user agreed (liked result)
        """
        self.confidence_calibration["adjustments"]["feedback_count"] += 1

        # If user disagreed with "high" confidence, lower the threshold
        if predicted_confidence == "high" and not user_agreed:
            self.adjust_threshold("high_confidence", 0.02)  # Raise bar for "high"

        # If user agreed with "low" confidence, it might be too harsh
        elif predicted_confidence == "low" and user_agreed:
            self.adjust_threshold("low_confidence", -0.02)  # Lower bar for "low"

        self._save_memory("confidence_calibration.json", self.confidence_calibration)

    # =========================
    # Memory Statistics
    # =========================

    def get_memory_stats(self) -> Dict:
        """Get statistics about learned memory"""
        return {
            "model_performance": {
                model: {
                    "total": perf.get("total_predictions", 0),
                    "accuracy": perf.get("accuracy", 0.0)
                }
                for model, perf in self.model_performance.items()
            },
            "learned_patterns": {
                "name_variations": len(self.learned_patterns.get("name_variations", {})),
                "address_formats": sum(len(v) for v in self.learned_patterns.get("address_formats", {}).values()),
                "reliable_indicators": len(self.learned_patterns.get("reliable_indicators", []))
            },
            "source_reliability": {
                source: data.get("score", 0.0)
                for source, data in self.source_reliability.items()
            },
            "confidence_thresholds": self.confidence_calibration.get("thresholds", {})
        }

    def export_memory_snapshot(self, output_path: Optional[str] = None) -> str:
        """
        Export complete memory snapshot for backup/analysis.

        Args:
            output_path: Optional custom path

        Returns:
            Path to snapshot file
        """
        if not output_path:
            output_path = self.memory_path / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "model_performance": self.model_performance,
            "learned_patterns": self.learned_patterns,
            "source_reliability": self.source_reliability,
            "confidence_calibration": self.confidence_calibration
        }

        with open(output_path, 'w') as f:
            json.dump(snapshot, f, indent=2)

        return str(output_path)
