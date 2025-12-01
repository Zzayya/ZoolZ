# ZoolZ Programs

This directory contains all individual programs within the ZoolZ hub. Each program is self-contained with its own utilities, templates, and static files.

## Programs

### 🎨 [modeling/](modeling/)
3D modeling and STL manipulation program ("Bubble")
- Cookie cutter generation from images
- STL editing tools (thicken, hollow, repair, simplify, mirror, scale, cut, channels)
- Boolean operations (union, intersection, difference)
- Shape generation
- Multi-object scene management

### 📐 [scad/](scad/)
Parametric CAD program (OpenSCAD-like)
- Primitive shape generation
- CSG (Constructive Solid Geometry) operations
- Code-based 3D modeling

### 🔍 [people_finder/](people_finder/)
People search and information gathering
- Multi-source web scraping
- Contact information discovery
- Profile aggregation

### 👣 [digital_footprint/](digital_footprint/)
Digital presence analysis
- Social media presence mapping
- Online footprint visualization

## Structure

Each program follows this structure:
```
program_name/
├── blueprint.py        # Flask blueprint (routes)
├── utils/             # Program-specific utilities
├── static/
│   ├── js/           # JavaScript files
│   └── css/          # Stylesheets
├── templates/         # HTML templates
└── README.md         # Program documentation
```

## Shared Resources

Common utilities used by multiple programs are in the `shared/` directory at the root level.
