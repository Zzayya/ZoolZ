#!/usr/bin/env python3
"""
Data Collector - Memory System
Captures and saves ALL search data for dataset creation and model training.
Creates structured datasets from every search, prediction, and interaction.

VISION: Build self-improving system by capturing everything.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class DataCollector:
    """
    Collects and saves all search data for:
    1. Building training datasets
    2. Model performance tracking
    3. Running memory for models
    4. Future custom model training

    Every search creates:
    - Query data (what user asked for)
    - Raw results (what sources returned)
    - ML predictions (what models predicted)
    - Final results (what system returned)
    - User feedback (likes/corrections)
    """

    def __init__(self, base_path: str = "utils/people_finder/datasets"):
        """
        Initialize data collector.

        Args:
            base_path: Root directory for all datasets
        """
        self.base_path = Path(base_path)
        self._ensure_folder_structure()

    def _ensure_folder_structure(self):
        """Create all necessary folders for data collection"""
        folders = [
            self.base_path / "searches",           # Daily search logs
            self.base_path / "training_data",      # Formatted for training
            self.base_path / "memory",             # Running memory
            self.base_path / "feedback",           # User corrections
            self.base_path / "raw_data",           # Raw scraper output
            self.base_path / "predictions"         # Model predictions
        ]

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    def start_search(self, search_params: Dict) -> str:
        """
        Start tracking a new search.

        Args:
            search_params: Search parameters (name, phone, address, etc.)

        Returns:
            search_id: Unique identifier for this search
        """
        search_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Create dated folder
        date_folder = self.base_path / "searches" / datetime.now().strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        # Save search query
        query_file = date_folder / f"{search_id}_query.json"
        query_data = {
            "search_id": search_id,
            "timestamp": datetime.now().isoformat(),
            "parameters": search_params,
            "metadata": {
                "version": "1.0",
                "source": "people_finder"
            }
        }

        with open(query_file, 'w') as f:
            json.dump(query_data, f, indent=2)

        return search_id

    def save_raw_results(self, search_id: str, raw_results: Dict):
        """
        Save raw search results before organization.

        Args:
            search_id: Search identifier
            raw_results: Unorganized results from all sources
        """
        date_folder = self.base_path / "searches" / datetime.now().strftime("%Y-%m-%d")
        raw_file = date_folder / f"{search_id}_raw_results.json"

        data = {
            "search_id": search_id,
            "timestamp": datetime.now().isoformat(),
            "raw_results": raw_results
        }

        with open(raw_file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_ml_predictions(self, search_id: str, predictions: Dict):
        """
        Save ML model predictions for training data.

        Args:
            search_id: Search identifier
            predictions: Dict of model predictions
                {
                    "name_matches": [{name1, name2, similarity, predicted_same}],
                    "entities_extracted": [{text, entity_type, confidence}],
                    "address_parses": [{raw_address, parsed_components, confidence}],
                    "confidence_scores": [{person, predicted_confidence, actual_sources}]
                }
        """
        date_folder = self.base_path / "predictions" / datetime.now().strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        pred_file = date_folder / f"{search_id}_predictions.json"

        data = {
            "search_id": search_id,
            "timestamp": datetime.now().isoformat(),
            "predictions": predictions
        }

        with open(pred_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Also append to training data files
        self._append_to_training_data(predictions)

    def save_final_results(self, search_id: str, final_results: Dict):
        """
        Save final organized results.

        Args:
            search_id: Search identifier
            final_results: Organized results returned to user
        """
        date_folder = self.base_path / "searches" / datetime.now().strftime("%Y-%m-%d")
        results_file = date_folder / f"{search_id}_final_results.json"

        data = {
            "search_id": search_id,
            "timestamp": datetime.now().isoformat(),
            "final_results": final_results
        }

        with open(results_file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_user_feedback(self, search_id: str, feedback: Dict):
        """
        Save user feedback (likes, corrections, flags).

        Args:
            search_id: Search identifier
            feedback: User feedback
                {
                    "item_id": "phone_123",
                    "item_type": "phone",
                    "feedback_type": "correct" | "incorrect" | "spam",
                    "correction": "actual value if corrected",
                    "timestamp": "2025-11-17T..."
                }
        """
        feedback_file = self.base_path / "feedback" / f"{search_id}_feedback.jsonl"

        # Append to JSONL (one JSON object per line)
        with open(feedback_file, 'a') as f:
            f.write(json.dumps({
                "search_id": search_id,
                "timestamp": datetime.now().isoformat(),
                **feedback
            }) + '\n')

        # Update training data with feedback
        self._update_training_with_feedback(search_id, feedback)

    def _append_to_training_data(self, predictions: Dict):
        """Append predictions to training data files in JSONL format"""

        # Name matching training data
        if "name_matches" in predictions:
            name_file = self.base_path / "training_data" / "name_matching.jsonl"
            with open(name_file, 'a') as f:
                for match in predictions["name_matches"]:
                    f.write(json.dumps(match) + '\n')

        # Entity extraction training data
        if "entities_extracted" in predictions:
            entity_file = self.base_path / "training_data" / "entity_extraction.jsonl"
            with open(entity_file, 'a') as f:
                for entity in predictions["entities_extracted"]:
                    f.write(json.dumps(entity) + '\n')

        # Address parsing training data
        if "address_parses" in predictions:
            addr_file = self.base_path / "training_data" / "address_parsing.jsonl"
            with open(addr_file, 'a') as f:
                for parse in predictions["address_parses"]:
                    f.write(json.dumps(parse) + '\n')

        # Confidence scoring training data
        if "confidence_scores" in predictions:
            conf_file = self.base_path / "training_data" / "confidence_scoring.jsonl"
            with open(conf_file, 'a') as f:
                for score in predictions["confidence_scores"]:
                    f.write(json.dumps(score) + '\n')

    def _update_training_with_feedback(self, search_id: str, feedback: Dict):
        """Update training data with user corrections"""
        feedback_training = self.base_path / "training_data" / "feedback_corrections.jsonl"

        with open(feedback_training, 'a') as f:
            f.write(json.dumps({
                "search_id": search_id,
                "timestamp": datetime.now().isoformat(),
                **feedback
            }) + '\n')

    def get_training_stats(self) -> Dict:
        """
        Get statistics about collected training data.

        Returns:
            Dict with counts of collected data
        """
        stats = {
            "total_searches": 0,
            "name_matches": 0,
            "entities_extracted": 0,
            "address_parses": 0,
            "confidence_scores": 0,
            "user_feedback": 0
        }

        # Count searches
        searches_folder = self.base_path / "searches"
        if searches_folder.exists():
            stats["total_searches"] = len(list(searches_folder.rglob("*_query.json")))

        # Count training data lines
        training_folder = self.base_path / "training_data"
        if training_folder.exists():
            for key, filename in [
                ("name_matches", "name_matching.jsonl"),
                ("entities_extracted", "entity_extraction.jsonl"),
                ("address_parses", "address_parsing.jsonl"),
                ("confidence_scores", "confidence_scoring.jsonl"),
                ("user_feedback", "feedback_corrections.jsonl")
            ]:
                file_path = training_folder / filename
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        stats[key] = sum(1 for _ in f)

        return stats

    def export_training_dataset(self, dataset_type: str, output_format: str = "jsonl") -> str:
        """
        Export a specific training dataset for model training.

        Args:
            dataset_type: "name_matching", "entity_extraction", "address_parsing", "confidence_scoring"
            output_format: "jsonl", "csv", or "json"

        Returns:
            Path to exported file
        """
        source_file = self.base_path / "training_data" / f"{dataset_type}.jsonl"

        if not source_file.exists():
            raise FileNotFoundError(f"No training data found for {dataset_type}")

        # For now, just return the JSONL path (already in good format)
        # Future: Add CSV/JSON conversion if needed
        return str(source_file)

    def save_scraper_raw_data(self, search_id: str, source: str, data: Dict):
        """
        Save raw scraper output before any processing.

        Args:
            search_id: Search identifier
            source: Source name (e.g., "adams_county_court", "web_search")
            data: Raw HTML, JSON, or extracted data
        """
        date_folder = self.base_path / "raw_data" / datetime.now().strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        raw_file = date_folder / f"{search_id}_{source}.json"

        data_to_save = {
            "search_id": search_id,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        with open(raw_file, 'w') as f:
            json.dump(data_to_save, f, indent=2)
