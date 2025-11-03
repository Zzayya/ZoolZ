# People Finder - Complete Documentation

**ZoolZ People Finder** - Multi-source public information search and aggregation tool

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** 2025-10-31

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [API Endpoints](#api-endpoints)
5. [Data Sources](#data-sources)
6. [Configuration](#configuration)
7. [Usage Guide](#usage-guide)
8. [Export Formats](#export-formats)
9. [Privacy & Legal](#privacy--legal)

---

## Overview

People Finder searches multiple public data sources to aggregate information about individuals, including:
- Phone number validation and carrier lookup
- Public records (courts, property)
- Web mentions and social media
- De-duplication and confidence scoring

**No API keys required** for basic functionality. Optional API keys enhance results.

---

## Features

### ✅ Core Features (No API Keys Needed)

**Phone Validation:**
- Area code database (55 US area codes)
- Location identification (state/city)
- Phone number formatting
- Support for OH, PA, WV, IN, IL, KY, TN

**Web Search:**
- DuckDuckGo fallback search (no API key)
- Social media profile discovery
- Web mention extraction
- Rate-limited and respectful

**Public Records:**
- Direct links to state court portals
- Property record portal links
- Auto-fill form data generation
- 7 states supported

**Data Organization:**
- Smart de-duplication
- Confidence scoring (0-100%)
- Source tracking
- 24-hour SQLite caching

**Export:**
- CSV format (spreadsheet-ready)
- PDF reports (formatted, color-coded)
- JSON format (raw data)

### ⚡ Enhanced Features (With API Keys)

**Google Custom Search:**
- Better search quality
- 100 free queries/day
- Social media discovery
- Web mention accuracy

**NumVerify Phone API:**
- Carrier identification
- Line type (mobile/landline/VOIP)
- Enhanced validation
- 250 free lookups/month

---

## Architecture

### File Structure

```
blueprints/
└── people_finder.py          # Flask routes (272 lines)

utils/people_finder/
├── __init__.py
├── search_orchestrator.py    # Main coordinator (287 lines)
├── public_records.py          # State court/property portals (328 lines)
├── phone_apis.py              # Phone validation & area codes (327 lines)
├── web_scraper.py             # Google/DuckDuckGo search (368 lines)
└── data_organizer.py          # De-duplication & caching (463 lines)

templates/
└── people_finder.html         # Frontend UI (973 lines)

database/
└── search_cache.db            # SQLite cache (auto-created)
```

**Total:** ~2,039 lines of Python + 973 lines of HTML/JS

---

## API Endpoints

### Search Endpoints

#### `POST /people/api/search`
Main search endpoint - searches all sources

**Request:**
```json
{
  "name": "John A Smith",
  "phone": "5551234567",
  "address": "123 Main St",
  "email": "email@example.com",
  "state": "OH"
}
```

**Response:**
```json
{
  "search_params": {...},
  "total_persons_found": 1,
  "persons": [{
    "name": "John A Smith",
    "overall_confidence": 85.0,
    "organized_data": {
      "phone_numbers": [{
        "number": "5551234567",
        "formatted": "(555) 123-4567",
        "confidence": "high",
        "source": "Validated"
      }],
      "addresses": [...],
      "emails": [...],
      "public_records": [...],
      "social_media": [...]
    },
    "confidence_sources": ["user_input", "phone_api", "web_mention"]
  }],
  "search_timestamp": "2025-10-31T..."
}
```

---

#### `POST /people/api/validate-phone`
Quick phone validation only

**Request:**
```json
{
  "phone": "7408276423"
}
```

**Response:**
```json
{
  "phone_number": "(740) 827-6423",
  "valid": true,
  "carrier": "AT&T",
  "line_type": "mobile",
  "location": {
    "city": "Southern Ohio",
    "state": "OH"
  },
  "confidence": "high",
  "sources": ["Area Code Database"]
}
```

---

### Export Endpoints

#### `POST /people/api/export/csv`
Export results as CSV

**Request:**
```json
{
  "results": { ...search results... }
}
```

**Response:**
- File download: `people_finder_results_20251031_143022.csv`
- Content-Type: `text/csv`

**CSV Format:**
```csv
Name,Confidence %,Phone Numbers,Addresses,Emails,Public Records,Social Media,Sources
John A Smith,85,(740) 827-6423,None,None,0,0,user_input phone_api
```

---

#### `POST /people/api/export/pdf`
Export results as PDF

**Request:**
```json
{
  "results": { ...search results... }
}
```

**Response:**
- File download: `people_finder_results_20251031_143022.pdf`
- Content-Type: `application/pdf`

**PDF Contents:**
- Title page with search metadata
- Color-coded confidence scores
- Formatted person cards
- All data organized by category
- Timestamped footer

---

### Utility Endpoints

#### `POST /people/api/autofill-form`
Generate auto-fill data for manual court searches

**Request:**
```json
{
  "state": "OH",
  "record_type": "courts",
  "name": "John A Smith",
  "phone": "7408276423"
}
```

**Response:**
```json
{
  "state": "OH",
  "record_type": "courts",
  "portal_url": "https://www.supremecourt.ohio.gov/rod/",
  "fields": {
    "firstName": "Isaiah",
    "lastName": "John Miro",
    "phone": "7408276423"
  }
}
```

---

#### `GET /people/api/stats`
Get usage statistics

**Response:**
```json
{
  "total_searches": 42,
  "cached_results": 15,
  "daily_api_queries": 23,
  "api_limit": 100
}
```

---

#### `POST /people/api/cache/clear`
Clear search cache

**Response:**
```json
{
  "success": true,
  "message": "Cache cleared"
}
```

---

## Data Sources

### 1. Phone Validation

**Area Code Database (Built-in):**
- 55 area codes across 7 states
- Instant lookup (no API call)
- Location data (city/state)

**Coverage:**
- Ohio: 216, 220, 234, 330, 380, 419, 440, 513, 567, 614, 740, 937
- Pennsylvania: 215, 267, 272, 412, 484, 570, 610, 717, 724, 814, 878
- West Virginia: 304, 681
- Indiana: 219, 260, 317, 463, 574, 765, 812, 930
- Illinois: 217, 224, 309, 312, 331, 618, 630, 708, 773, 815, 847
- Kentucky: 270, 364, 502, 606, 859
- Tennessee: 423, 615, 629, 731, 865, 901, 931

**NumVerify API (Optional):**
- Carrier identification
- Line type detection
- Enhanced validation
- Requires free API key

---

### 2. Web Search

**DuckDuckGo (Built-in):**
- No API key required
- HTML parsing
- Social media links
- Web mentions

**Google Custom Search (Optional):**
- Better quality results
- 100 free queries/day
- Enhanced social media discovery
- Requires API key + Search Engine ID

---

### 3. Public Records

**State Court Portals (7 States):**

| State | Court Portal | Property Portal | Status |
|-------|--------------|-----------------|--------|
| OH | supremecourt.ohio.gov/rod/ | tax.ohio.gov/property | ⚠️ Manual search (bot protection) |
| PA | ujsportal.pacourts.us/ | pa.gov/ | ✅ Accessible |
| WV | courtswv.gov/public-resources/ | wvtax.gov/property | ✅ Accessible |
| IN | public.courts.in.gov/mycase | in.gov/dlgf/ | ✅ Accessible |
| IL | courts.illinois.gov/ | illinois.gov/rev/.../property/ | ✅ Accessible |
| KY | courts.ky.gov/ | revenue.ky.gov/Property/ | ✅ Accessible |
| TN | tncourts.gov/ | tn.gov/revenue/.../property... | ✅ Accessible |

**Note:** Most court systems require manual searches due to bot protection, CAPTCHAs, or county-specific portals. People Finder provides direct links and auto-fill data.

---

## Configuration

### Database Settings

**File:** `config.py`

```python
PEOPLE_FINDER_DB = os.path.join(DATABASE_FOLDER, 'search_cache.db')
PEOPLE_FINDER_CACHE_HOURS = 24  # Cache duration
```

**Tables Auto-Created:**
- `search_cache` - Cached search results
- `search_history` - Search history log

---

### API Keys (Optional)

**Set via UI (Recommended):**
1. Open People Finder
2. Click ⚙ (Settings) button
3. Enter API keys
4. Keys stored in browser localStorage

**Set via Environment (Alternative):**
```bash
export GOOGLE_API_KEY="your_key_here"
export GOOGLE_SEARCH_ENGINE_ID="your_engine_id"
export NUMVERIFY_API_KEY="your_key_here"
```

**Get Free API Keys:**
- Google Custom Search: https://developers.google.com/custom-search
- NumVerify: https://numverify.com/

---

## Usage Guide

### Basic Search (No API Keys)

**Step 1:** Enter Search Criteria
- At least one field required
- More fields = better results
- Supported fields: name, phone, address, email, state

**Step 2:** Click "Search"
- Progress bars show search phases
- Phase 1: Official sources (5-10 sec)
- Phase 2: Web search (10-20 sec)
- Total time: 15-30 seconds

**Step 3:** Review Results
- Results sorted by confidence score
- Click person card to expand details
- Tabs: Phone Numbers, Addresses, Emails, Public Records, Social Media

**Step 4:** Export (Optional)
- CSV: Spreadsheet format
- PDF: Formatted report
- JSON: Raw data

---

### Enhanced Search (With API Keys)

Same as basic search, plus:
- Better web search quality (Google)
- Carrier information (NumVerify)
- Higher confidence scores
- More social media links

---

### Understanding Results

**Confidence Scores:**
- **70-100% (High):** Multiple verified sources
- **40-69% (Medium):** Some sources, needs verification
- **0-39% (Low):** Unverified web mentions only

**Color Coding:**
- 🟢 Green: High confidence (>=70%)
- 🟠 Orange: Medium confidence (40-69%)
- 🔴 Red: Low confidence (<40%)

**Data Sources:**
- `user_input` - Search parameters
- `phone_api` - NumVerify validation
- `public_records` - Court/property records
- `web_mention` - DuckDuckGo/Google results
- `social_media` - Profile links

---

## Export Formats

### CSV Export

**File Format:** `people_finder_results_YYYYMMDD_HHMMSS.csv`

**Columns:**
1. Name
2. Confidence % (0-100)
3. Phone Numbers (semicolon-separated)
4. Addresses (semicolon-separated)
5. Emails (semicolon-separated)
6. Public Records (count)
7. Social Media (count)
8. Sources (comma-separated)

**Use Cases:**
- Import to Excel/Google Sheets
- Database bulk import
- Data analysis

---

### PDF Export

**File Format:** `people_finder_results_YYYYMMDD_HHMMSS.pdf`

**Contents:**
1. **Title Page**
   - "People Finder - Search Results"
   - Search date and parameters
   - Total results count

2. **Person Cards** (one per person)
   - Name with color-coded confidence badge
   - Phone numbers (formatted)
   - Addresses
   - Emails
   - Public records count
   - Social media links (top 3)
   - Data sources list

3. **Footer**
   - Generated timestamp
   - ZoolZ branding

**Use Cases:**
- Professional reports
- Documentation
- Printable records

---

### JSON Export

**Format:** Raw search results

**Use Cases:**
- API integration
- Custom processing
- Archiving

---

## Privacy & Legal

### Important Legal Notices

**1. Public Information Only**
- All data from publicly accessible sources
- No private database access
- No unauthorized scraping

**2. Intended Use**
- Public records research
- Contact information verification
- Skip tracing (legal purposes)
- Background checks (with consent)

**3. Prohibited Use**
- Stalking or harassment
- Identity theft
- Discrimination
- Unauthorized surveillance

**4. Compliance**
- Comply with all local laws
- Obtain consent where required
- Respect privacy rights
- Follow terms of service for all data sources

**5. Accuracy**
- Results are NOT verified
- May contain outdated information
- May confuse similar names
- Always verify before acting on data

**6. No Warranty**
- Provided "as-is"
- No guarantee of accuracy
- No liability for decisions made using data

---

### Data Privacy

**What We Store:**
- Search parameters (in cache)
- Search results (cached 24 hours)
- Search history (timestamps only)
- API keys (browser localStorage only)

**What We DON'T Store:**
- Credit card information
- Social security numbers
- Passwords
- Personal identifiable information beyond search queries

**Data Retention:**
- Cache: 24 hours (configurable)
- History: Indefinite (can be cleared)
- API keys: Browser local storage only

**Data Deletion:**
- Click "Clear Cache" button
- Or delete `database/search_cache.db`

---

## Troubleshooting

### Common Issues

**"No results found"**
- Try broader search terms
- Use fewer fields
- Check spelling
- Try different name variations

**"Rate limit reached"**
- Google API: 100 queries/day (free tier)
- Wait 24 hours or upgrade API plan

**"Search timeout"**
- Network issue or slow connection
- Try again
- Check firewall settings

**"Invalid API key"**
- Check key format
- Verify key is active
- Re-enter in settings

---

## Performance Tips

### Faster Searches

1. **Use Caching**
   - Repeat searches use cache (<1 sec)
   - Cache expires after 24 hours

2. **Limit Search Fields**
   - More fields = longer search
   - Use 1-2 fields for quick lookup

3. **Use API Keys**
   - Google gives better results faster
   - NumVerify validates instantly

### Better Results

1. **Be Specific**
   - Full name vs partial
   - State limits scope
   - Complete phone number

2. **Multiple Searches**
   - Try name variations
   - Try maiden names
   - Try nicknames

3. **Verify Results**
   - Check confidence scores
   - Cross-reference sources
   - Use public records links

---

## Future Enhancements

### Planned Features
- ⏳ Email validation API
- ⏳ LinkedIn profile parsing
- ⏳ Address standardization
- ⏳ Batch search (CSV import)
- ⏳ Search history UI
- ⏳ Advanced filters
- ⏳ Real-time progress (Server-Sent Events)

### Not Planned
- ❌ Paid database access (TLO, LexisNexis)
- ❌ Dark web searches
- ❌ Social security number lookup
- ❌ Credit report access
- ❌ Automated court scraping (blocked by CAPTCHAs)

---

## Support

### Documentation
- This file: Complete reference
- `PEOPLE_FINDER_TEST_RESULTS.md` - Test results
- `PEOPLE_FINDER_AUDIT.md` - Code audit

### Code Locations
- Blueprint: `blueprints/people_finder.py`
- Utils: `utils/people_finder/*.py`
- Template: `templates/people_finder.html`

### Getting Help
- Check error messages in browser console (F12)
- Review test results document
- Check API key configuration
- Verify database permissions

---

**Built by:** ZoolZ Development Team
**License:** Private Project
**Version:** 1.0.0
**Status:** ✅ Production Ready
**Last Updated:** 2025-10-31
