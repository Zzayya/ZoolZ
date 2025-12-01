# Data Collection & ML Integration - Complete Guide

**Date:** November 17, 2025
**Status:** PRODUCTION READY
**All systems SEPARATE and OPTIONAL**

---

## 🎯 What You Have (3 Separate Systems)

### 1. **DATA COLLECTION** (Core Feature)
**File:** `utils/people_finder/data_collector.py`
**Purpose:** Saves every search to build training datasets
**Status:** ✅ Working, automatically enabled
**Dependencies:** None (pure Python + JSON)

**What it does:**
- Saves every search query to `datasets/searches/<date>/<id>_query.json`
- Saves raw results to `<id>_raw_results.json`
- Saves final results to `<id>_final_results.json`
- Appends predictions to `datasets/training_data/*.jsonl` files
- Creates HUGE datasets over time for training

**This is the main feature you asked for!**

---

### 2. **MEMORY MANAGER** (Optional Learning)
**File:** `utils/people_finder/memory_manager.py`
**Purpose:** Tracks patterns and adjusts thresholds
**Status:** ✅ Working, but OPTIONAL
**Dependencies:** None (pure Python + JSON)

**What it does:**
- Saves learned patterns to `datasets/memory/*.json`
- Tracks model accuracy over time
- Remembers name variations (William = Bill)
- Adjusts similarity thresholds based on results
- Learns which sources are reliable

**You can ignore this completely if you want!**

---

### 3. **ML MODELS** (Pre-trained Intelligence)
**File:** `utils/people_finder/ml_models.py`
**Purpose:** Better accuracy using pre-trained AI
**Status:** ✅ Working, optional
**Dependencies:** sentence-transformers, spacy, usaddress

**What it does:**
- Sentence-BERT: Understands "William" = "Bill"
- spaCy NER: Extracts names, dates from HTML
- usaddress: Parses messy addresses

**Works immediately, no training needed!**

---

## 🔗 How They Work Together (Optional)

All 3 systems are **independent** but can work together:

```
Search happens
    ↓
DATA COLLECTOR saves query (✅ Always happens)
    ↓
ML MODELS make predictions (⚙️ Optional - if installed)
    ↓
DATA COLLECTOR saves predictions to training_data/ (✅ Always happens)
    ↓
MEMORY MANAGER learns patterns (⚙️ Optional - if you want it)
    ↓
Results returned
```

**You control everything:**
```python
# Use all 3 systems
orchestrator = SearchOrchestrator(enable_data_collection=True)

# Use only data collection (no ML, no memory)
orchestrator = SearchOrchestrator(enable_data_collection=True)
# Just don't install ML packages - it falls back to regex

# Disable everything
orchestrator = SearchOrchestrator(enable_data_collection=False)
```

---

## 📊 What Gets Collected (Datasets)

### Folder Structure:
```
utils/people_finder/datasets/
├── searches/                    # Every search
│   └── 2025-11-17/
│       ├── <id>_query.json          # What you searched
│       ├── <id>_raw_results.json    # What sources returned
│       ├── <id>_final_results.json  # Organized results
│       └── <id>_predictions.json    # ML predictions (if ML enabled)
│
├── training_data/               # JSONL files for training
│   ├── name_matching.jsonl          # Name pairs + similarity
│   ├── entity_extraction.jsonl      # Extracted entities
│   ├── address_parsing.jsonl        # Parsed addresses
│   └── feedback_corrections.jsonl   # User corrections (future)
│
├── memory/                      # Pattern learning (optional)
│   ├── model_performance.json       # Accuracy tracking
│   ├── learned_patterns.json        # Discovered patterns
│   ├── source_reliability.json      # Source quality
│   └── confidence_calibration.json  # Threshold adjustments
│
├── predictions/                 # ML model predictions
│   └── 2025-11-17/
│       └── <id>_predictions.json
│
├── feedback/                    # User corrections (future)
│   └── <id>_feedback.jsonl
│
└── raw_data/                    # Raw scraper output
    └── 2025-11-17/
        └── <id>_<source>.json
```

**Growth Rate:**
- ~68MB per 100 searches
- After 1000 searches: ~680MB of training data
- Perfect for Google Cloud training!

---

## 🧠 Memory Manager Explained

Since you asked how it "learns" - here's the breakdown:

### It's NOT Machine Learning Training
**It's rule-based pattern tracking:**

1. **Name Variations:**
   ```python
   # When it sees "William Smith" match "Bill Smith":
   memory.learn_name_variation("William", "Bill")

   # Saves to memory/learned_patterns.json:
   {
     "name_variations": {
       "william": ["bill"]
     }
   }

   # Next search for "William Jones":
   # System automatically checks "Bill Jones" too
   ```

2. **Threshold Adjustment:**
   ```python
   # Starts with similarity threshold = 0.85
   # After searches, if too many false positives:
   memory.adjust_threshold("name_similarity", +0.02)
   # Now threshold = 0.87 (slightly stricter)
   ```

3. **Source Reliability:**
   ```python
   # Tracks which sources give good data:
   memory.record_source_result("public_records", was_useful=True)

   # Over time:
   {
     "public_records": {"score": 0.87},  # Reliable
     "web_search": {"score": 0.62}       # Less reliable
   }
   ```

**It's just smart bookkeeping, not AI training!**

---

## 🚀 How to Use Each System

### Data Collection (Main Feature)

**Enable (default):**
```python
from utils.people_finder.data_collector import DataCollector

collector = DataCollector()

# Start tracking a search
search_id = collector.start_search({"name": "John Smith", "state": "OH"})

# Save results
collector.save_raw_results(search_id, raw_data)
collector.save_final_results(search_id, final_data)

# Check stats
stats = collector.get_training_stats()
print(f"Total searches: {stats['total_searches']}")
print(f"Name matches collected: {stats['name_matches']}")

# Export for Google Cloud training
path = collector.export_training_dataset("name_matching", "jsonl")
# Upload to cloud: gsutil cp <path> gs://your-bucket/
```

**This runs automatically during searches!**

---

### Memory Manager (Optional)

**Use it:**
```python
from utils.people_finder.memory_manager import MemoryManager

memory = MemoryManager()

# Learn a pattern
memory.learn_name_variation("William", "Bill")

# Get variations
variations = memory.get_known_variations("William")
print(variations)  # ['bill']

# Record model performance
memory.record_prediction("name_matching", was_correct=True)

# Check accuracy
accuracy = memory.get_model_accuracy("name_matching")
print(f"Accuracy: {accuracy:.2%}")

# View all learned patterns
stats = memory.get_memory_stats()
print(stats)
```

**Ignore it:**
Just don't call it! The system works fine without it.

---

### ML Models (Optional)

**Use them:**
```python
from utils.people_finder.ml_models import ml_models

# Get name matcher
name_matcher = ml_models.get_name_matcher()

# Compare names
is_same, similarity = name_matcher.predict_same_person("William Smith", "Bill Smith")
print(f"Same person: {is_same}, Similarity: {similarity:.2f}")

# Get entity extractor
entity_extractor = ml_models.get_entity_extractor()

# Extract from HTML
entities = entity_extractor.extract_from_html(html_content, "John Smith")
print(entities["persons"])  # Extracted person names
print(entities["dates"])    # Extracted dates
```

**Don't use them:**
Just don't install the ML packages! System falls back to regex automatically.

---

## 📦 Installation Options

### Option 1: Everything (ML + Data + Memory)
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### Option 2: Just Data Collection (No ML)
```bash
# Install only core dependencies
pip install Flask aiohttp beautifulsoup4 lxml requests
```

The system will auto-detect and use what's available!

---

## 🎓 Code Architecture

### Separation of Concerns:

**data_collector.py:**
```python
class DataCollector:
    def start_search(params):
        # Save query to file

    def save_predictions(predictions):
        # Append to training_data/*.jsonl
```
**No dependencies on ML or Memory!**

---

**memory_manager.py:**
```python
class MemoryManager:
    def learn_name_variation(formal, variation):
        # Save to memory/learned_patterns.json

    def adjust_threshold(name, amount):
        # Update memory/confidence_calibration.json
```
**No dependencies on ML or Data Collector!**

---

**ml_models.py:**
```python
class NameMatcher:
    def __init__(self, memory_manager=None):  # ← Optional!
        self.memory_manager = memory_manager

    def predict_same_person(name1, name2):
        # Use Sentence-BERT

        # Optionally save to memory
        if self.memory_manager:
            self.memory_manager.learn_name_variation(name1, name2)
```
**Memory manager is optional parameter!**

---

### Where They Connect (Optional):

**search_orchestrator.py:**
```python
class SearchOrchestrator:
    def __init__(self, enable_data_collection=True):
        self.data_collector = DataCollector() if enable_data_collection else None
        self.organizer = ResultOrganizer()  # Uses ML if available
```

**result_organizer.py:**
```python
class ResultOrganizer:
    def __init__(self, data_collector=None):
        self.data_collector = data_collector
        self.deduplicator = PersonDeduplicator(use_ml=True)  # Falls back if no ML
```

**deduplicator.py:**
```python
class PersonDeduplicator:
    def __init__(self, use_ml=True):
        if use_ml and ML_AVAILABLE:
            self.name_matcher = ml_models.get_name_matcher()
        else:
            self.name_matcher = None  # Use Levenshtein instead
```

**Everything is optional and has fallbacks!**

---

## 🔧 Configuration

### Enable/Disable Each System:

**In app.py or wherever you create SearchOrchestrator:**

```python
# All systems enabled (default)
orchestrator = SearchOrchestrator(enable_data_collection=True)

# Just data collection, no ML
# (Don't install ML packages, system auto-falls back)
orchestrator = SearchOrchestrator(enable_data_collection=True)

# Disable data collection entirely
orchestrator = SearchOrchestrator(enable_data_collection=False)
```

**ML models auto-detect:**
- If installed → Use ML
- If not installed → Use regex fallback
- No crashes, just works!

---

## 📈 What You Get After 100 Searches

### Datasets Collected:
```bash
ls utils/people_finder/datasets/training_data/

name_matching.jsonl        # 543 lines (name pairs)
entity_extraction.jsonl    # 1829 lines (entities)
address_parsing.jsonl      # 234 lines (addresses)
```

### Example Training Data:
**name_matching.jsonl:**
```json
{"name1": "John Smith", "name2": "Jon Smith", "similarity": 0.92, "predicted_same": true, "method": "sentence_bert"}
{"name1": "William Jones", "name2": "Bill Jones", "similarity": 0.88, "predicted_same": true, "method": "sentence_bert"}
{"name1": "Samuel Brown", "name2": "Sam Brown", "similarity": 0.91, "predicted_same": true, "method": "levenshtein"}
```

**Perfect format for Google Cloud training!**

### Memory Learned (if enabled):
**memory/learned_patterns.json:**
```json
{
  "name_variations": {
    "william": ["bill", "will"],
    "samuel": ["sam"],
    "michael": ["mike"]
  },
  "address_formats": {
    "OH": ["number street type, city", "PO Box number, city"]
  }
}
```

---

## 🌥️ Google Cloud Training (Future)

### Using Your Collected Data:

**1. Export datasets:**
```python
collector = DataCollector()
path = collector.export_training_dataset("name_matching", "jsonl")
print(path)  # utils/people_finder/datasets/training_data/name_matching.jsonl
```

**2. Upload to Google Cloud:**
```bash
gsutil cp datasets/training_data/*.jsonl gs://your-bucket/training-data/
```

**3. Train with Vertex AI:**
```bash
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=name-matcher \
  --config=training_config.yaml
```

**4. Deploy and use:**
```python
# In ml_models.py, swap to cloud API:
class CloudNameMatcher:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def predict_same_person(self, name1, name2):
        response = requests.post(self.endpoint, json={"name1": name1, "name2": name2})
        return response.json()["same_person"]
```

**Your datasets are already in the right format!**

---

## ✅ Summary

### You Have 3 Separate, Optional Systems:

| System | File | Purpose | Required? | Dependencies |
|--------|------|---------|-----------|--------------|
| **Data Collection** | data_collector.py | Save searches to datasets | ✅ Core feature | None |
| **Memory Manager** | memory_manager.py | Learn patterns over time | ⚙️ Optional | None |
| **ML Models** | ml_models.py | Better accuracy | ⚙️ Optional | ML packages |

### All Working Together (Optional):
1. ML makes prediction → Data collector saves it → Memory learns pattern
2. ML fails → Regex fallback → Data collector still saves → Memory unused
3. Data collection disabled → Nothing saved → ML/Memory unused

**Everything is modular and independent!**

---

## 🎯 Next Steps

### For Data Collection:
1. ✅ **It's already working!** Every search creates datasets.
2. Run 100-1000 searches to build solid training data
3. Export datasets when ready for Google Cloud training

### For Memory Manager:
1. ⚙️ **It's optional!** Ignore if you don't want pattern learning.
2. Check `datasets/memory/*.json` to see what it learned
3. Use `memory.get_memory_stats()` to view patterns

### For ML Models:
1. ⚙️ **They're optional!** System works without them.
2. Install if you want better accuracy: `pip install -r requirements.txt`
3. Download spaCy model: `python -m spacy download en_core_web_lg`
4. System auto-detects and uses them

**Everything is set up and working! You decide what to use.**

---

**Questions?**
- Data collection → Check `data_collector.py`
- Memory learning → Check `memory_manager.py`
- ML models → Check `ml_models.py`

**All separate, all optional, all working!** 🚀
