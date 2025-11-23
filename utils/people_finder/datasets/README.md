# Datasets - Auto-Generated Training Data

This folder automatically collects data from every search to build training datasets.

## Folder Structure

```
datasets/
├── searches/               # Every search saved by date
│   └── 2025-11-17/
│       ├── <search_id>_query.json          # What user searched for
│       ├── <search_id>_raw_results.json    # Unorganized results
│       └── <search_id>_final_results.json  # Organized results
│
├── predictions/            # ML model predictions
│   └── 2025-11-17/
│       └── <search_id>_predictions.json    # All ML predictions
│
├── training_data/          # Formatted for model training (JSONL)
│   ├── name_matching.jsonl          # Name similarity pairs
│   ├── entity_extraction.jsonl      # Extracted entities
│   ├── address_parsing.jsonl        # Parsed addresses
│   ├── confidence_scoring.jsonl     # Confidence predictions
│   └── feedback_corrections.jsonl   # User corrections
│
├── memory/                 # Running memory (models learn over time)
│   ├── model_performance.json       # Accuracy tracking
│   ├── learned_patterns.json        # Discovered patterns
│   ├── source_reliability.json      # Source quality scores
│   └── confidence_calibration.json  # Threshold adjustments
│
├── feedback/               # User likes/corrections (JSONL)
│   └── <search_id>_feedback.jsonl
│
└── raw_data/               # Raw scraper output
    └── 2025-11-17/
        └── <search_id>_<source>.json

## Data Flow

1. **User searches** → `searches/<date>/<id>_query.json`
2. **Raw results collected** → `searches/<date>/<id>_raw_results.json`
3. **ML predictions made** → `predictions/<date>/<id>_predictions.json`
4. **Results organized** → `searches/<date>/<id>_final_results.json`
5. **User gives feedback** → `feedback/<id>_feedback.jsonl`
6. **Training data updated** → `training_data/*.jsonl`
7. **Memory updated** → `memory/*.json`

## Using the Data

### View Training Stats
```python
from utils.people_finder.data_collector import DataCollector
collector = DataCollector()
stats = collector.get_training_stats()
print(stats)
```

### Export Training Dataset
```python
# Export name matching data for training
path = collector.export_training_dataset("name_matching", "jsonl")
print(f"Dataset saved to: {path}")
```

### Check Memory Stats
```python
from utils.people_finder.memory_manager import MemoryManager
memory = MemoryManager()
stats = memory.get_memory_stats()
print(stats)
```

## File Formats

### JSONL (JSON Lines)
Each line is a separate JSON object. Perfect for streaming and training.

Example `name_matching.jsonl`:
```json
{"name1": "John Smith", "name2": "Jon Smith", "similarity": 0.92, "predicted_same": true}
{"name1": "William Jones", "name2": "Bill Jones", "similarity": 0.88, "predicted_same": true}
```

### JSON (Pretty)
Individual search files are pretty-printed for human readability.

## Auto-Collection

**Everything is collected automatically.** No manual work needed.

Every search creates:
- Query log
- Raw results
- ML predictions
- Final results

User feedback updates:
- Training data files
- Memory/learning files

## Privacy Note

All data is stored **locally only**. Nothing is sent to external servers unless you explicitly export and upload for cloud training.

## Future Use

This data can be used for:
1. Training custom models in Google Cloud
2. Fine-tuning pre-trained models
3. Analyzing system performance
4. A/B testing different approaches
5. Building completely new ML features

**The longer the system runs, the more valuable this data becomes.**
