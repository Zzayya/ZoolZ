# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

3D Modulator is a modular Flask-based 3D modeling toolkit with multiple specialized modes:
- **Cookie Cutter Generator**: Converts images to cookie cutter STL files
- **Parametric CAD**: OpenSCAD-like programmatic 3D modeling (in progress)
- **Future modes**: Expandable architecture for additional tools

## Running the Application

### Quick Start (Desktop Launcher)
```bash
# Mac: Double-click this file
START_3D_MODULATOR.command

# Windows: Double-click this file
START_3D_MODULATOR.bat

# Both scripts:
# - Check dependencies
# - Activate virtual environment
# - Start Flask server on port 5001
# - Auto-open browser
```

### Manual Start
```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Run the Flask server
python app.py

# The app starts on http://localhost:5001
```

**Note**: Port changed from 5000 to 5001 to avoid conflicts with macOS AirPlay Receiver.

## Installing Dependencies

```bash
# After activating venv
pip install -r requirements.txt

# For Parametric CAD features (when ready):
# Uncomment build123d in requirements.txt and run pip install again
```

## Testing Cookie Cutter Logic

```bash
# Test with all images in TestImages/ folder
python test_all_images.py

# Test with custom image
python test_cookie.py
```

## Architecture

### Separation of Concerns

The codebase follows strict separation between views and business logic:

- **`blueprints/`**: Flask blueprints handling HTTP routes and request/response
  - `cookie_cutter.py`: Cookie cutter mode endpoints
  - `parametric_cad.py`: Parametric CAD mode endpoints

- **`utils/`**: Pure business logic, isolated from Flask/HTTP
  - `cookie_logic.py`: Cookie cutter mesh generation algorithms
  - `cad_operations.py`: Parametric CAD shape creation (placeholder, needs build123d)

**Important**: Never mix view logic with business logic. Blueprints should only handle HTTP concerns. All algorithms and mesh operations belong in `utils/`.

### Blueprint URL Structure

Each mode is isolated under its own URL prefix:
- Cookie Cutter: `/cookie` (registered with `url_prefix='/cookie'`)
- Parametric CAD: `/parametric` (registered with `url_prefix='/parametric'`)

### File Upload/Output Flow

1. Files uploaded to `uploads/` folder
2. STL files generated to `outputs/` folder
3. Download endpoints serve files from `outputs/`
4. Both folders are created automatically on startup in `app.py:18-19`

## Cookie Cutter Mode

### Status: Fully Functional ✓

The cookie cutter mode is complete and tested with multiple image formats and backgrounds.

### Key Features

- **Smart Background Detection**: Automatically handles white backgrounds, transparent backgrounds (alpha channel), and colored images
- **Detail Level Control**: User-adjustable smoothing (0.0 = smooth, 1.0 = detailed)
- **Multiple Format Support**: PNG, JPG, JPEG, GIF, BMP, WebP
- **Robust Processing**: Otsu's thresholding, morphological operations, contour filling
- **Validation**: Parameter constraints enforced via config

### Key Components

- **`utils/cookie_logic.py`**: Contains the core algorithm
  - `build_mask_from_image()`: Smart mask generation with alpha channel support, GrabCut algorithm, and Otsu's thresholding fallback
  - `find_and_smooth_contour()`: Extracts **perfect outside perimeter** first (CHAIN_APPROX_NONE), then applies controlled Douglas-Peucker smoothing
  - `make_cookie_cutter_mesh()`: Creates 3D mesh with detailed blade and **smooth ergonomic base** (round joins)
  - `generate_cookie_cutter()`: Main entry point with detail level mapping

### Default Parameters

```python
blade_thick: 2.0      # Blade thickness (mm)
blade_height: 20.0    # Blade height (mm)
base_thick: 3.0       # Base thickness (mm)
base_extra: 10.0      # Base extension beyond blade (mm)
max_dim: 90.0         # Maximum dimension to scale to (mm)
no_base: False        # Omit base plate if True
detail_level: 0.5     # Detail level 0.0-1.0 (affects outline smoothing)
```

### Detail Level Parameter

The `detail_level` parameter (0.0 to 1.0) controls outline smoothing:
- **0.0-0.3**: Very smooth, fewer vertices, good for simple shapes
- **0.4-0.6**: Medium detail, balanced (default 0.5)
- **0.7-1.0**: High detail, more vertices, preserves intricate features

Internally maps to Douglas-Peucker epsilon factor: `epsilon = 0.01 - (detail_level * 0.009)`

### Cookie Cutter Mesh Generation Details

The algorithm creates a two-part mesh with smart base smoothing:

1. **Blade wall** (detailed and sharp):
   - Uses `poly.buffer(blade_thick, join_style=2)` with mitered joins
   - Follows the detailed contour from Douglas-Peucker smoothing
   - Extruded to `blade_height` for cutting edge

2. **Base ring** (smooth and ergonomic):
   - Applies `blade_footprint.buffer(base_extra, join_style=1, resolution=32)`
   - **join_style=1** creates rounded joins (not sharp corners)
   - High resolution (32) for smooth curves
   - Results in comfortable, ergonomic grip surface

3. **Assembly**:
   - Meshes are positioned (wall sits on top of base)
   - Boolean union attempted first, falls back to concatenation if needed
   - Final mesh rotated 180° around Z-axis for proper print orientation

### API Endpoints

- `POST /cookie/api/generate`: Upload image + params → generate STL
- `GET /cookie/download/<filename>`: Download generated STL
- `GET /cookie/api/params/default`: Get default parameters

## Parametric CAD Mode

### Status: ✅ FUNCTIONAL (Basic Features Working)

The parametric CAD mode now has working shape creation, OpenSCAD code generation, and 3D preview!

### Current Implementation

Uses **trimesh** (already installed) for shape creation:
- All basic primitives working
- Boolean operations available in backend
- Proper OpenSCAD code generation
- Real-time 3D preview

### Shape Registry Pattern

`utils/cad_operations.py` uses a global `SHAPE_REGISTRY` dict to track created shapes:
- Each shape gets unique ID (`shape_0`, `shape_1`, etc.)
- Shapes stored as `Shape3D` wrapper objects with metadata
- Enables multi-shape scene management and boolean operations between shapes

### Working Shapes (✅ Implemented)

**Primitives:**
- **Box/Cube**: width, height, depth, center option
- **Cylinder**: radius, height, segments (resolution), center option
- **Sphere**: radius, subdivisions (quality: 1-5)
- **Cone**: radius, height, segments, center option
- **Torus**: major_radius (ring), minor_radius (tube), section counts
- **Prism**: sides (3-12 sides), radius, height

**Not Yet Implemented:**
- Boolean operations UI (backend exists)
- Hollow/shell, chamfer/fillet
- Threads (male/female)
- Transform operations UI

### OpenSCAD Code Generation (✅ Working)

The `generate_openscad_code()` function generates proper OpenSCAD syntax:
- Valid syntax for all shapes
- All parameters included as comments
- Proper $fn usage for resolution
- Special cases: torus uses rotate_extrude, prism uses linear_extrude

### API Endpoints

- `GET /parametric/api/shapes/available`: List all shape types and parameters
- `POST /parametric/api/shape/create`: Create new shape → returns preview data for Three.js
- `POST /parametric/api/combine`: Boolean operations between shapes
- `POST /parametric/api/render`: Export scene to STL
- `POST /parametric/api/openscad/export`: Export as OpenSCAD script

## Key Technologies

### Cookie Cutter Stack
- **OpenCV**: Image processing, contour detection, morphological operations
- **Shapely**: 2D polygon operations (buffer, difference, validation, scaling)
- **Trimesh**: 3D mesh creation, extrusion, boolean ops, STL export
- **PyMeshLab**: Mesh repair and cleanup

### Parametric CAD Stack (Planned)
- **build123d**: Modern CAD kernel with thread support (currently commented out in requirements.txt)
- **Trimesh**: Mesh export and operations
- OpenSCAD code generation for interoperability

### Web Stack
- **Flask**: Lightweight Python web framework with blueprints
- **Three.js**: Client-side 3D visualization (to be integrated)

## Adding New Modes

Follow this pattern to add a new mode:

1. Create blueprint in `blueprints/new_mode.py`
   ```python
   from flask import Blueprint
   new_bp = Blueprint('new_mode', __name__)
   ```

2. Create business logic in `utils/new_mode_logic.py` (no Flask imports!)

3. Register blueprint in `app.py`:
   ```python
   from blueprints.new_mode import new_bp
   app.register_blueprint(new_bp, url_prefix='/new_mode')
   ```

4. Create template in `templates/new_mode.html`

5. Add bubble to HUB in `templates/hub.html` (follow existing mode-bubble structure)

## Development Notes

### HUB Design
- Neon blue crosshatch grid background with pulse animation
- Mode bubbles with hover effects and glow
- "SOON" badges for placeholder modes
- Parallax effect on mouse move (see hub.html:236-241)

### File Upload Security
- Uses `werkzeug.utils.secure_filename()` for safe filenames
- Max upload size: 16MB (see app.py:13)
- Allowed image types: PNG, JPG, JPEG, GIF, BMP (see cookie_cutter.py:14)

### Mesh Processing
- Cookie cutter meshes are validated with `is_watertight` check
- Meshes repaired with `mesh.process(validate=True)` if not watertight
- Trimesh Scene objects are flattened with `concatenate()` when needed

### Thread Generation (Future)
When implementing threads in Parametric CAD mode, use build123d's `IsoThread`:
```python
from build123d import IsoThread
thread = IsoThread(
    major_diameter=6,  # M6 thread
    pitch=1.0,
    length=10,
    external=True  # False for female threads
)
```

## Configuration System

The project uses a centralized configuration system (`config.py`):

- **`Config`**: Base configuration class with all settings
- **`DevelopmentConfig`**: Development-specific settings (DEBUG=True)
- **`ProductionConfig`**: Production settings (requires SECRET_KEY env var)

Settings are loaded in `app.py` based on `FLASK_ENV` environment variable:
```bash
export FLASK_ENV=production  # Use production config
python app.py
```

### Configuration Options

- `MAX_CONTENT_LENGTH`: File upload size limit (default 16MB)
- `ALLOWED_IMAGE_EXTENSIONS`: Supported image formats
- `COOKIE_CUTTER_DEFAULTS`: Default cookie cutter parameters
- `COOKIE_CUTTER_CONSTRAINTS`: Min/max validation ranges for parameters
- `UPLOAD_FOLDER` / `OUTPUT_FOLDER`: Directory paths

Blueprints access config via `current_app.config['KEY']`.

## Common Issues

### Cookie Cutter Contour Detection

The improved mask building algorithm handles multiple scenarios:

1. **Transparent images (PNG/WebP with alpha)**: Uses alpha channel directly - best quality
2. **Colored subjects on white backgrounds (like Spongebob)**: Uses Otsu's thresholding with automatic inversion
3. **Complex backgrounds**: Falls back to GrabCut algorithm (advanced foreground extraction)
4. **Morphological operations**: Closes gaps and removes noise with adaptive kernel sizing
5. **Contour filling**: Fills largest contour only for solid, clean mask

### Outline Perimeter Extraction

The outline extraction follows a two-stage process:

1. **Perfect Perimeter** (stage 1): Uses `cv2.CHAIN_APPROX_NONE` to get every single pixel on the boundary
2. **Controlled Smoothing** (stage 2): Applies Douglas-Peucker algorithm with user-controlled epsilon factor
3. **Result**: Clean, accurate outline that preserves important features while removing noise

### Mesh Not Watertight
The cookie cutter generator attempts boolean union of base and wall. If this fails (due to precision issues), it falls back to simple concatenation, then repairs with `.process(validate=True)`.

## UI Status

### Cookie Cutter UI - ✅ COMPLETE
- **Template**: `templates/cookie_cutter.html` - Fully functional
- **JavaScript**: `static/js/cookie_viewer.js` - Complete with Three.js integration
- **Features**:
  - Drag & drop image upload
  - Live parameter adjustment with sliders
  - Real-time 3D STL preview with orbit controls
  - Mesh statistics display
  - Download button for generated STL
- **Design**: Dark theme with neon blue accents matching HUB

### Parametric CAD UI - ⏳ PLACEHOLDER
- **Template**: `templates/parametric_cad.html` - "Coming Soon" page
- Shows planned features list
- Needs full implementation when backend is ready

## Future Work

### Parametric CAD Implementation
1. Uncomment `build123d` in `requirements.txt` and install
2. Implement shape creation functions in `cad_operations.py`
3. Create `parametric_cad.html` template with shape palette and properties panel
4. Integrate Three.js viewer for real-time preview
5. Add OpenSCAD export functionality

### Three.js Integration
Both modes need shared 3D viewer:
- Viewer.js in `static/js/` (referenced in README but not yet created)
- STL loading with STLLoader
- Orbit controls for camera manipulation
- Grid and axes helpers

## Recent Improvements (Latest)

### Cookie Cutter Enhancements - Round 2 (Current)
- ✓ **MAJOR: Smooth ergonomic base/brim** - Uses rounded joins (join_style=1) instead of jagged outline
- ✓ **MAJOR: Perfect perimeter extraction** - Uses CHAIN_APPROX_NONE for accurate boundary, then smooths
- ✓ **MAJOR: Fixed colored subjects on white** - Spongebob JPEG now works perfectly
- ✓ **Improved mask detection** - Added GrabCut algorithm for complex backgrounds
- ✓ **Better Otsu's thresholding** - Validates foreground ratio (5-95%) before accepting
- ✓ **Enhanced morphological operations** - Adaptive kernel sizing based on image dimensions

### Cookie Cutter Enhancements - Round 1
- ✓ Added `detail_level` parameter (0.0-1.0) for user-controlled outline smoothing
- ✓ Improved background detection with alpha channel support
- ✓ Added Otsu's thresholding for automatic white background handling
- ✓ Added WebP format support
- ✓ Implemented centralized configuration system (`config.py`)
- ✓ Added parameter validation with constraints
- ✓ Comprehensive testing with `test_all_images.py`
- ✓ Fixed missing dependency: `mapbox-earcut` required by trimesh
- ✓ Updated `pymeshlab` version to `2023.12.post3`

### Project Structure Improvements
- ✓ Added `config.py` for centralized configuration
- ✓ Updated blueprints to use `current_app.config`
- ✓ Added `.gitkeep` files for empty directories
- ✓ Updated `.gitignore` for test files
- ✓ Created comprehensive test suite

### Test Results
All test images working perfectly:
- ✓ **spngbob.jpeg** (yellow on white) - 9/9 tests passed
- ✓ **blue.jpg** (complex blue design on white) - 9/9 tests passed
- ✓ **Scooby_Doo.webp** (transparent background) - 9/9 tests passed
- Total: **9/9 tests passed** across 3 detail levels (0.2, 0.5, 0.8)

### UI & Launch Ready - Round 3
- ✓ **Complete Cookie Cutter UI** - Drag & drop upload, parameter sliders, 3D preview
- ✓ **Three.js 3D Viewer** - Real-time STL loading with orbit controls
- ✓ **Desktop Launcher Scripts** - Mac (.command) and Windows (.bat) startup files
- ✓ **Launch Documentation** - LAUNCH_CHECKLIST.md and WHATS_NOT_WORKING.md
- ✓ **All Pages Tested** - Hub, Cookie Cutter, Parametric CAD (placeholder)
- ✓ **Port Configuration** - Changed to 5001 to avoid macOS conflicts
- ✓ **Ready for Production Testing**

### Parametric CAD Implementation - Round 4 (Latest)
- ✓ **All Basic Shapes Implemented** - Box, Cylinder, Sphere, Cone, Torus, Prism
- ✓ **Proper OpenSCAD Code Generation** - Valid syntax with all parameters
- ✓ **Full Parametric UI** - Shape selector, dynamic parameter forms, 3D preview
- ✓ **Shape Registry System** - Backend tracks all created shapes with IDs
- ✓ **Boolean Operations Backend** - Union, difference, intersection (needs UI)
- ✓ **STL Export** - Download generated shapes
- ✓ **Copy Code Feature** - Copy OpenSCAD code to clipboard
- ✓ **Real-time 3D Preview** - Three.js viewer with orbit controls

## Questions for Original Developer

From the README:
1. Do you have the `OutLineLogic.py` file? (Referenced in cookie cutter implementation)
2. Which shapes should be prioritized for Parametric CAD?
3. Any specific thread sizes needed? (M6, M8, custom?)
