# ZoolZ - IDE Setup & File Organization

## 🎨 VSCode File Tree Color Scheme

To get color-coded folders in VSCode sidebar, you need one of these extensions:

### Option 1: Material Icon Theme (Recommended)
1. Install extension: `PKief.material-icon-theme`
2. File → Preferences → File Icon Theme → "Material Icon Theme"
3. Our `.vscode/settings.json` will automatically apply colors!

### Option 2: Folder Icons
1. Install extension: `alefragnani.project-manager` or similar
2. Colors will be applied based on folder purpose

---

## 📁 Color Organization Scheme

### 🔵 BLUE - Source Code (Application Core)
```
blueprints/    - Flask routes (controller logic)
utils/         - Business logic (helper functions)
templates/     - HTML views
static/        - CSS/JS/Assets
```
**Purpose:** Core application files that make ZoolZ work

### 🟢 GREEN - Documentation (Information)
```
docs/          - All markdown guides and documentation
README.md      - Main project readme
```
**Purpose:** Learning, setup, and reference materials

### 🟣 PURPLE - Tools & Scripts (Automation)
```
scripts/       - Launchers, tests, utilities
```
**Purpose:** Development and deployment tools

### 🟡 YELLOW/ORANGE - Data & Runtime (Generated)
```
uploads/       - User uploaded files
outputs/       - Generated STL files
database/      - SQLite caches
```
**Purpose:** Runtime data, temporary files, user content

### 🔴 RED - Tests & Testing Assets
```
TestImages/    - Test images for cookie cutter
test_*.py      - Test scripts
```
**Purpose:** Testing and quality assurance

### ⚪ GRAY - Configuration (Root level)
```
app.py
config.py
requirements.txt
.gitignore
```
**Purpose:** Project configuration and entry points

---

## 🎯 Visual Organization Goals

1. **Quick Identification** - Know what each folder does at a glance
2. **Color Grouping** - Similar-purpose folders share colors
3. **Mental Map** - Colors match folder function
4. **Professional** - Clean, organized appearance

---

## 🔧 Alternative: File Nesting

If you don't want colors, enable **File Nesting** instead:

1. VSCode: File → Preferences → Settings
2. Search: "explorer.fileNesting.enabled"
3. Check the box

This groups related files together:
- `cookie_cutter.py` nests → `cookie_logic.py`, `cookie_viewer.js`
- `parametric_cad.py` nests → `cad_operations.py`, `parametric_viewer*.js`
- `people_finder.py` nests → all people finder utils

---

## 📊 Folder Purpose Quick Reference

| Folder | Color | Purpose | Edit Frequency |
|--------|-------|---------|----------------|
| `blueprints/` | 🔵 Blue | Flask routes | Medium |
| `utils/` | 🔵 Blue | Business logic | Medium |
| `templates/` | 🔵 Blue | HTML views | Medium |
| `static/` | 🔵 Blue | JS/CSS/Assets | Medium |
| `docs/` | 🟢 Green | Documentation | Low |
| `scripts/` | 🟣 Purple | Tools/Launchers | Low |
| `uploads/` | 🟡 Yellow | User files | High (runtime) |
| `outputs/` | 🟡 Yellow | Generated STL | High (runtime) |
| `database/` | 🟡 Yellow | SQLite cache | High (runtime) |
| Root files | ⚪ Gray | Configuration | Low |

---

## 🎨 Custom Color Setup (Advanced)

### Method 1: Peacock Extension
1. Install: `johnpapa.vscode-peacock`
2. Color entire workspace
3. Quick visual distinction for multi-project work

### Method 2: Custom CSS/JS Loader
1. Install: `be5invis.vscode-custom-css`
2. Completely custom file tree colors
3. Advanced - requires CSS knowledge

### Method 3: Material Theme Settings
Already configured in `.vscode/settings.json`!

---

## 🚀 Quick Setup

### Automatic (Recommended):
1. Open ZoolZ in VSCode
2. Install "Material Icon Theme" extension
3. Settings already configured in `.vscode/settings.json`
4. Reload VSCode
5. **Done!** Colors should appear

### Manual:
1. File → Preferences → Settings
2. Search "material-icon-theme.folders.associations"
3. Copy settings from `.vscode/settings.json`
4. Reload VSCode

---

## 💡 Pro Tips

1. **Collapse runtime folders** - Minimize `uploads/`, `outputs/`, `database/` to reduce clutter
2. **Pin important files** - Right-click → "Open to Side" for app.py, config.py
3. **Use breadcrumbs** - View → Show Breadcrumbs for easy navigation
4. **Explorer sorting** - Sort by type to group similar files

---

## 🎯 Visual Result

After setup, your sidebar will show:
```
📦 ZoolZ
├── 🔵 blueprints/          (Blue - Application code)
├── 🔵 utils/               (Blue - Helper functions)
├── 🔵 templates/           (Blue - Views)
├── 🔵 static/              (Blue - Assets)
├── 🟢 docs/                (Green - Documentation)
├── 🟣 scripts/             (Purple - Tools)
├── 🟡 uploads/             (Yellow - User data)
├── 🟡 outputs/             (Yellow - Generated)
├── 🟡 database/            (Yellow - Runtime)
├── ⚪ app.py               (Gray - Config)
├── ⚪ config.py            (Gray - Config)
└── ⚪ requirements.txt     (Gray - Config)
```

**Much easier to navigate!** 🎨✨

---

This makes the ZoolZ project **visually organized and easy to navigate**!
