# 3D Modulator - Flask Edition

**Modular Python-based 3D modeling toolkit with parametric CAD and cookie cutter generation**

## 🎯 Project Vision

A powerful, modular 3D modeling application with multiple specialized modes:
- **Parametric CAD** - OpenSCAD-like programmatic modeling with full control
- **Cookie Cutter Generator** - Image to cookie cutter STL converter
- **Future Modes** - Expandable architecture for additional tools

## 🏗️ Current Architecture

```
3d-modulator-flask/
├── app.py                          # Main Flask application
├── blueprints/                     # View logic (routes & endpoints)
│   ├── parametric_cad.py          # OpenSCAD-like CAD mode
│   └── cookie_cutter.py           # Cookie cutter generation
├── utils/                          # Business logic (isolated from views)
│   ├── cookie_logic.py            # Cookie cutter mesh generation
│   ├── cad_operations.py          # Parametric CAD operations
│   └── mesh_ops.py                # (Future) General mesh utilities
├── templates/                      # HTML templates
│   ├── hub.html                   # Main HUB with mode selection
│   ├── parametric_cad.html        # Parametric CAD UI
│   └── cookie_cutter.html         # Cookie cutter UI
├── static/                         # Static assets
│   ├── js/
│   │   └── viewer.js              # Three.js 3D viewer (shared)
│   └── css/
│       └── style.css
├── uploads/                        # User uploads
└── outputs/                        # Generated STL files
```

## 🚀 Quick Start

### 1. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app will start on `http://localhost:5000`

### 3. Using Claude Code (in VS Code)

```bash
# From terminal in VS Code
claude code "help me implement the box creation function in utils/cad_operations.py"
```

## 📋 Status & Roadmap

### ✅ Completed
- [x] Flask application structure
- [x] Blueprint architecture (separate views)
- [x] Cookie cutter logic ported from Python script
- [x] HUB design with neon blue grid background
- [x] Modular, expandable architecture

### 🚧 In Progress
- [ ] Cookie cutter UI template
- [ ] Parametric CAD UI template
- [ ] Three.js viewer integration
- [ ] Implement cookie cutter endpoints

### 📝 TODO - Cookie Cutter Mode
- [ ] Upload image endpoint
- [ ] Generate STL with live params
- [ ] Preview in 3D viewer
- [ ] Download STL
- [ ] Param adjustment after generation

### 📝 TODO - Parametric CAD Mode
- [ ] Implement build123d shape creation
- [ ] Basic shapes: box, cylinder, sphere, cone, torus, prism
- [ ] Boolean operations: union, difference, intersection
- [ ] Advanced operations:
  - [ ] Hollow/shell with optional closed ends
  - [ ] Chamfer & fillet
  - [ ] Male/female screw threads
  - [ ] Brims & inverse brims
  - [ ] Bevels
- [ ] Properties panel with organized sections
- [ ] OpenSCAD code generation
- [ ] Render button → STL export
- [ ] Multi-shape scene management

### 🔮 Future Modes
- [ ] Design Mode (TBD)
- [ ] AI Assistant Mode (TBD)

## 🛠️ Key Technologies

### Cookie Cutter
- **OpenCV** - Image processing & contour detection
- **Shapely** - 2D polygon operations & buffering
- **Trimesh** - 3D mesh creation & export

### Parametric CAD
- **build123d** (planned) - Modern Pythonic CAD with threads support
- **Trimesh** - Mesh export & operations
- **OpenSCAD** code generation

### Web Framework
- **Flask** - Lightweight Python web framework
- **Three.js** - 3D visualization in browser

## 💡 Design Principles

1. **Separation of Concerns**
   - Views (blueprints) handle routes & HTTP
   - Utils handle business logic & algorithms
   - Keep them completely separate

2. **Modularity**
   - Each mode is independent
   - Shared utilities when needed
   - Easy to add new modes

3. **Python-First**
   - All heavy lifting in Python
   - Use best-in-class Python CAD/mesh libraries
   - Browser just for UI & visualization

## 📦 Dependencies Explained

### Core (Required)
- `Flask` - Web framework
- `numpy` - Numerical operations
- `opencv-python` - Image processing
- `trimesh` - 3D mesh operations
- `shapely` - 2D geometry
- `pymeshlab` - Mesh repair & cleanup

### Parametric CAD (To be installed)
- `build123d` - Parametric CAD (recommended)
- `cadquery` - Alternative CAD library

### Optional Enhancements
- `pyclipper` - Advanced 2D polygon ops
- `open3d` - Point cloud & advanced mesh ops
- `ezdxf` - DXF import/export
- `pygltflib` - GLTF/GLB export

## 🔧 Development

### Adding a New Mode

1. Create blueprint in `blueprints/new_mode.py`
2. Create utility functions in `utils/new_mode_logic.py`
3. Create template in `templates/new_mode.html`
4. Add route in `app.py`
5. Add bubble to HUB in `templates/hub.html`

### Working with Claude Code

Claude Code is integrated with VS Code and can help you:
- Generate boilerplate code
- Implement complex algorithms
- Debug issues
- Refactor code

## ❓ Questions & Next Steps

### Need to Know:
1. Do you have the `OutLineLogic.py` file? (Referenced in cookie cutter)
2. Which shapes should we prioritize for Parametric CAD?
3. Any specific thread sizes needed? (M6, M8, custom?)

### Ready to Build:
- Cookie cutter UI (simple form with sliders)
- Three.js viewer integration
- First parametric shape (box with hollow option)

## 📝 Notes

- Cookie cutter default params already match your Python script
- Parametric CAD uses build123d which has built-in thread generation
- HUB design uses neon blue crosshatch grid as requested
- All generation logic separated from views
- Ready for modular expansion

---

**Let's build this thing! 🚀**
