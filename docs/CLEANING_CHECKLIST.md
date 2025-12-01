# Project Cleaning Checklist

**Last Updated:** November 17, 2025
**Purpose:** Keep the project organized and clutter-free

---

## 🧹 REGULAR CLEANING TASKS

### 1. Python Cache Files
**When:** After major code changes, before git commits
**Command:**
```bash
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
```

**Why:** These are automatically generated and can be recreated. They bloat the repo.

---

### 2. Old Documentation Files
**When:** After creating new documentation
**Action:** Move old docs to `docs/` folder
**Keep in Root:**
- Most recent complete documentation (e.g., `ML_INTEGRATION_COMPLETE.md`)
- Current task list (e.g., `POLISH_BREAKDOWN.md`)
- README.md (always)

**Move to `docs/`:**
- All older AUDIT, COMPLETE, BREAKDOWN files
- Test result files older than 1 week

**Command:**
```bash
# Check what's in root
ls -1 *.md

# Move old ones (example)
mv OLD_FILE.md docs/
```

---

### 3. Test Files
**Current Test Files:**
- `test_search_isaiah.py` (in root)
- `SEARCH_TEST_RESULTS.md` (in root)

**Action:**
- If older than 1 week → Move to `docs/test_results/`
- If no longer relevant → Delete

**Create test results folder:**
```bash
mkdir -p docs/test_results
mv SEARCH_TEST_RESULTS.md docs/test_results/
```

---

### 4. Log Files
**Check for:**
```bash
find . -name "*.log" -type f
```

**Action:**
- Development logs → Delete
- Important logs → Move to `logs/` folder

---

### 5. Database Files
**Current Locations:**
- `database/search_cache.db`
- `utils/people_finder/datasets/` (ML training data)

**Keep:** All database files (they contain important data)
**Clean:** Use built-in cache cleanup
```python
from utils.people_finder.organizers.cache_manager import CacheManager
cache = CacheManager()
cache.clear_old_cache(days=30)  # Remove cache older than 30 days
```

---

### 6. Temporary/Generated Files
**Check for:**
```bash
# Temp files
find . -name "*.tmp" -o -name "*.temp" -o -name "*.bak"

# OS files
find . -name ".DS_Store" -o -name "Thumbs.db"

# Editor files
find . -name "*~" -o -name "*.swp"
```

**Delete all:**
```bash
find . -name "*.tmp" -delete
find . -name ".DS_Store" -delete
find . -name "*~" -delete
```

---

### 7. Duplicate Requirements Files
**Check:**
```bash
ls -1 *requirements*.txt
```

**Keep:**
- `requirements.txt` (main file with all sections)

**Delete:**
- Any separate ML/test/dev requirements files (merge into main first)

---

### 8. Virtual Environment
**Location:** `venv/` or `.venv/`

**Action:**
- ✅ Keep it (contains installed packages)
- ⚠️ Make sure it's in `.gitignore`
- ❌ Never commit it to git

**Check `.gitignore` has:**
```
venv/
.venv/
__pycache__/
*.pyc
*.pyo
.DS_Store
*.log
```

---

### 9. Node Modules (if any)
**Check:**
```bash
find . -name "node_modules" -type d
```

**Action:**
- If found and not needed → Delete
- If needed → Make sure it's in `.gitignore`

---

### 10. Large Data Files
**Check for large files:**
```bash
find . -type f -size +10M | grep -v venv | grep -v ".git"
```

**Action:**
- ML models (Sentence-BERT, spaCy) → Keep (they're needed)
- Old dataset backups → Archive or delete
- Large test files → Move to external storage

---

## 📊 FOLDER ORGANIZATION

### Current Structure:
```
ZoolZ/
├── app.py                          # Main Flask app
├── config.py                       # Configuration
├── requirements.txt                # All dependencies (organized)
├── README.md                       # Project overview
├── ML_INTEGRATION_COMPLETE.md      # Latest doc (KEEP)
├── POLISH_BREAKDOWN.md             # Current tasks (KEEP)
├── CLEANING_CHECKLIST.md           # This file
│
├── docs/                           # OLD DOCUMENTATION (✓ Created)
│   ├── PEOPLE_FINDER_AUDIT.md
│   ├── FIXES_COMPLETED.md
│   ├── REFACTORING_COMPLETE.md
│   └── test_results/               # Old test results
│
├── blueprints/                     # Flask blueprints
├── static/                         # JS, CSS, images
├── templates/                      # HTML templates
├── database/                       # SQLite databases
├── venv/                           # Virtual environment
│
└── utils/                          # Utility modules
    ├── modeling/
    ├── parametric_cad/
    ├── digital_footprint/
    └── people_finder/
        ├── datasets/               # AUTO-GENERATED ML DATA
        │   ├── searches/           # Daily search logs
        │   ├── training_data/      # ML training datasets (JSONL)
        │   ├── predictions/        # Model predictions
        │   ├── memory/             # Running memory (optional)
        │   ├── feedback/           # User feedback
        │   └── raw_data/           # Raw scraper output
        │
        ├── data/                   # Static data (area codes, etc.)
        ├── organizers/             # Modular organizers
        └── *.py                    # Core modules
```

---

## 🔄 CLEANING SCRIPT (Quick Clean)

Create this file: `clean_project.sh`

```bash
#!/bin/bash
# Quick project cleaning script

echo "🧹 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

echo "🧹 Cleaning OS files..."
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete

echo "🧹 Cleaning temp files..."
find . -name "*.tmp" -delete
find . -name "*~" -delete

echo "✅ Project cleaned!"
```

Make it executable:
```bash
chmod +x clean_project.sh
./clean_project.sh
```

---

## 📋 MONTHLY CLEANUP CHECKLIST

- [ ] Run Python cache cleanup
- [ ] Move old documentation to `docs/`
- [ ] Clean database cache (30+ days old)
- [ ] Archive large datasets (if any)
- [ ] Review and delete obsolete test files
- [ ] Check for duplicate files
- [ ] Update this checklist if needed

---

## 🚫 FILES TO NEVER DELETE

### Critical Files:
- `app.py` - Main application
- `config.py` - Configuration
- `requirements.txt` - Dependencies
- `README.md` - Documentation
- All `.py` files in `utils/`, `blueprints/`
- `database/*.db` - Contains search cache
- `utils/people_finder/datasets/` - ML training data
- `utils/people_finder/data/` - Static data (area codes, etc.)

### Can Safely Delete:
- `__pycache__/` folders
- `*.pyc`, `*.pyo` files
- `.DS_Store`, `Thumbs.db`
- Old `*_COMPLETE.md` files (after moving to `docs/`)
- `*.log` files (unless important)
- Test result files older than 1 week

---

## 📝 NOTES

**When Adding New Features:**
1. Create new doc file for major features
2. After next major feature, move current doc to `docs/`
3. Keep only 2 most recent docs in root

**When Creating Test Files:**
1. Name with date: `test_feature_2025_11_17.py`
2. Move to `docs/test_results/` after 1 week
3. Or create a `tests/` folder for permanent tests

**Dataset Growth:**
- `datasets/` folder will grow over time
- This is NORMAL and EXPECTED
- Don't delete unless you're sure you don't need the data
- ~68MB per 100 searches is typical

---

**Last Cleaned:** November 17, 2025
**Next Cleaning:** December 17, 2025
**Cleaned By:** Claude
