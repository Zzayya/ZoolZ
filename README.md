# ZoolZ - Multi-Program Creative Hub

A sophisticated Flask-based web application hub featuring 3D modeling, parametric CAD, people finding, and digital footprint analysis tools.

## 🚀 Quick Start

```bash
# Clone and setup
cd ZoolZ
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (for People Finder)
python -m spacy download en_core_web_lg

# Setup environment variables
cp .env.example .env
# Edit .env with your settings

# Run the app
python3 app.py
```

Visit: `http://localhost:5000`
**Passkey:** 442767

## 📦 Programs

### 1. 🎨 3D Modeling (Bubble)
Professional STL manipulation and cookie cutter generation.

**Features:**
- Cookie cutter generation from images (PNG, JPG, etc.)
- STL editing tools (thicken, hollow, scale, cut, mirror)
- Parametric shape generation (cube, sphere, cylinder, etc.)
- Advanced operations (boolean, channels, repair, simplify)
- Multi-object scene management
- Undo/redo system (50 states)

[→ Full Documentation](programs/modeling/README.md)

### 2. 🔧 Parametric CAD (SCAD)
OpenSCAD-like parametric modeling.

**Features:**
- Primitive shapes (box, cylinder, sphere, cone)
- Boolean operations (union, difference, intersection)
- OpenSCAD code generation
- STL export

### 3. 🔍 People Finder
Advanced OSINT tool for finding people online.

**Features:**
- Multi-source web scraping
- Public records search
- Phone/email validation
- Address parsing
- Relationship mapping (trail following)
- ML/NLP intelligence (deduplication, scoring)
- Temporal dataset tracking (movement patterns)
- Export to PDF/CSV/JSON

### 4. 👤 Digital Footprint
Analyze and manage online presence.

**Features:**
- Social media account discovery
- Online mention tracking
- Data breach detection
- Exposure risk analysis
- Cleanup recommendations
- Removal request generation

## 🏗️ Architecture

```
ZoolZ/
├── app.py                    # Main Flask application
├── config.py                 # Configuration system
├── decorators.py            # Reusable route decorators
├── tasks.py                 # Celery background tasks
│
├── programs/                # Modern program structure
│   ├── modeling/           # 3D Modeling program
│   │   ├── blueprint.py
│   │   ├── utils/          # 11 utility modules
│   │   ├── static/js/      # 14 JavaScript modules
│   │   └── templates/
│   ├── scad/               # Parametric CAD (pending migration)
│   ├── people_finder/      # People finder (pending migration)
│   └── digital_footprint/  # Digital footprint (pending migration)
│
├── shared/                  # Cross-program utilities
│   ├── cookie_logic.py     # Cookie cutter generation
│   └── stamp_logic.py      # Stamp generation
│
├── templates/               # Shared templates (hub, login)
├── static/                  # Shared static files
├── database/                # SQLite databases
├── uploads/                 # User uploaded files
├── my_models/              # Saved models
├── tests/                   # Pytest test suite
└── docs/                    # Documentation
```

## 🛠️ Technology Stack

### Backend
- **Flask 3.0** - Web framework
- **trimesh** - 3D mesh processing
- **OpenCV** - Image processing
- **Celery** - Background task queue
- **Redis** - Task broker
- **SQLite** - Database
- **python-dotenv** - Environment management

### Frontend
- **Three.js r128** - 3D rendering
- **Vanilla JavaScript** - No framework dependencies
- **HTML5 Canvas** - Outline editing
- **Server-Sent Events** - Real-time progress updates

### ML/AI (People Finder)
- **spaCy** - Named entity recognition
- **sentence-transformers** - Semantic similarity
- **usaddress** - Address parsing

## 🔧 Development

### Running Tests
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test suite
python3 -m pytest tests/test_modeling/ -v

# Run with coverage
python3 -m pytest tests/ --cov=programs --cov-report=html
```

### Background Tasks (Celery)

For long-running operations like cookie cutter generation:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
celery -A tasks.celery worker --loglevel=info

# Terminal 3: Start Flask
python3 app.py
```

[→ Full Celery Setup Guide](docs/START_CELERY.md)

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .
```

## 📝 Environment Variables

Create a `.env` file (never commit this!):

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# File Upload
UPLOAD_FOLDER=/path/to/ZoolZ/uploads
MAX_CONTENT_LENGTH=104857600  # 100MB

# Celery/Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Mesh Processing
MAX_MESH_VERTICES=10000000

# People Finder (optional)
NUMVERIFY_API_KEY=your-api-key-here
```

See [.env.example](.env.example) for full list.

## 🎯 Key Features

### Decorator System
Eliminates code duplication with reusable decorators:

```python
@stl_operation  # Handles: file upload, validation, error handling, JSON response
def my_route():
    # Just business logic here
    return {'result': 'data'}
```

### Background Tasks
Long operations run in background with progress tracking:

```python
from tasks import generate_cookie_cutter_task

task = generate_cookie_cutter_task.delay(params)
# Returns immediately, processes in background
```

### Security
- Parameter validation with constraints
- File size limits (100MB default)
- Mesh complexity limits (10M vertices)
- Secure filename handling
- Path traversal protection
- No secrets in code (.env required)

## 📊 API Examples

### 3D Modeling

**Generate cookie cutter from image:**
```bash
curl -X POST http://localhost:5000/modeling/api/generate \
  -F "image=@logo.png" \
  -F "height=10" \
  -F "base_height=2" \
  -F "preset=cookie"
```

**Scale an STL file:**
```bash
curl -X POST http://localhost:5000/modeling/api/stl/scale \
  -F "stl=@model.stl" \
  -F "mode=uniform" \
  -F "scale_factor=2.0"
```

### People Finder

**Search for a person:**
```bash
curl -X POST http://localhost:5000/people_finder/api/search \
  -H "Content-Type: application/json" \
  -d '{"first_name": "John", "last_name": "Smith", "state": "CA"}'
```

## 📚 Documentation

- [Testing Guide](docs/TESTING_GUIDE.md) - How to run and write tests
- [Celery Setup](docs/START_CELERY.md) - Background task configuration
- [Modeling Program](programs/modeling/README.md) - 3D modeling documentation
- [Data Collection Guide](docs/DATA_COLLECTION_GUIDE.md) - People Finder setup

## 🚧 Current Status

### ✅ Completed
- 3D Modeling program fully reorganized
- Environment variable system
- Celery background tasks
- Decorator patterns
- Pytest test suite (30 tests passing)
- Comprehensive documentation

### 🔄 In Progress
- Main README (this file)
- Cleanup script for old files

### ⏳ Planned
- Migrate other programs to `/programs/` structure
- Add health check endpoints
- Set up CI/CD pipeline
- Production deployment guide

## 🤝 Contributing

This is a personal project, but if you want to contribute:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📋 Requirements

- **Python:** 3.8 or higher
- **RAM:** ~2GB (for ML models in People Finder)
- **Disk:** ~1.5GB (for ML models)
- **GPU:** Not required (models run on CPU)

## 🐛 Troubleshooting

### spaCy model not found
```bash
python -m spacy download en_core_web_lg
```

### Redis connection error
```bash
# Install Redis
brew install redis  # macOS
# Start Redis
redis-server
```

### Import errors
```bash
# Make sure you're in the venv
source venv/bin/activate
# Reinstall requirements
pip install -r requirements.txt
```

## 📄 License

Personal project - All rights reserved

## 👨‍💻 Author

Built by a self-taught developer learning Flask, 3D processing, and web development.

---

**Last Updated:** 2025-01-26
**Version:** 2.0 (Post-reorganization)
