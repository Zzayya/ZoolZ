# ZoolZ - Multi-Purpose 3D Design Toolkit

A modular Flask-based web application for 3D modeling and design workflows.

## 🚀 Quick Start

### Launch the App (Recommended)

**Mac/Linux:**
```bash
./scripts/START_ZOOLZ.command
```

**Windows:**
```cmd
scripts\START_ZOOLZ.bat
```

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux
   # venv\Scripts\activate   # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open browser:** http://localhost:5001

## 🎨 Features

### 🍪 Cookie Cutter Generator
Convert images to 3D-printable cookie cutter STL files with smart background detection and adjustable detail levels.

### 🔧 Parametric CAD
OpenSCAD-like programmatic 3D modeling with boolean operations and real-time preview.

### 🕵️ People Finder
Search public records, validate phone numbers, and discover web mentions across multiple sources.

## 📁 Project Structure

```
ZoolZ/
├── app.py              # Flask application entry point
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── docs/               # 📚 Full documentation
│   ├── CLAUDE.md       # Development guide
│   ├── LAUNCH_CHECKLIST.md
│   └── WHATS_NOT_WORKING.md
├── scripts/            # Launcher scripts & tests
│   ├── START_ZOOLZ.command
│   ├── START_ZOOLZ.bat
│   ├── test_all_images.py
│   └── TestImages/
├── blueprints/         # Flask route modules
├── templates/          # HTML templates
├── static/             # CSS, JavaScript, assets
├── utils/              # Business logic modules
├── uploads/            # User uploads
├── outputs/            # Generated STL files
└── database/           # SQLite caches
```

## 📚 Documentation

- **[Full Documentation](docs/CLAUDE.md)** - Architecture, development guide, API reference
- **[Launch Checklist](docs/LAUNCH_CHECKLIST.md)** - Pre-deployment testing
- **[Known Issues](docs/WHATS_NOT_WORKING.md)** - Current limitations

## 🔑 Optional API Keys

People Finder works without API keys but results are enhanced with:

- **Google Custom Search API** (100 free queries/day)
  Sign up: https://developers.google.com/custom-search

- **NumVerify Phone API** (250 free lookups/month)
  Sign up: https://numverify.com/

Set in environment or use the **"G" settings button** in People Finder UI.

## 🧪 Testing

```bash
# Test cookie cutter with all images
python scripts/test_all_images.py

# Run Flask in debug mode
export FLASK_ENV=development
python app.py
```

## 🛠️ Tech Stack

- **Backend:** Flask, Python 3.12+
- **3D Processing:** Trimesh, Shapely, OpenCV, PyMeshLab
- **Frontend:** Three.js, Vanilla JavaScript
- **Database:** SQLite (caching)
- **Async:** aiohttp, asyncio

## 📝 License

Private project - All rights reserved

## 🤝 Contributing

This is a private project. For development guidance, see [docs/CLAUDE.md](docs/CLAUDE.md).

---

**Version:** 1.0.0-alpha
**Port:** 5001 (changed from 5000 to avoid macOS AirPlay conflicts)
