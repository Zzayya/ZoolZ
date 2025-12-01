# CLAUDE LOOP - Master Tracking File
**Last Updated**: 2025-11-21

---

## 🎯 WHAT IS ZOOLZ?

**ZoolZ** is Isaiah's (Zay's) personal multi-purpose application HUB - a centralized toolbox that houses multiple independent programs/tools under one roof with a unified dark aesthetic.

### The Big Picture
ZoolZ is NOT just one program - it's a **HUB/LAUNCHER** that provides access to multiple distinct tools that Zay is building and using. Think of it like a suite of applications that all share the same visual style and authentication system, but each serves a different purpose.

### Current Programs in the ZoolZ Hub:

1. **3D Modeling Program** (Primary focus)
   - Cookie cutter generator (upload image → extract outline → generate STL)
   - Stamp tool (positive/negative stamps for leather work)
   - Outline editor (edit extracted outlines with precision)
   - STL operations (thicken, hollow, repair, simplify, mirror, boolean)
   - Shape generator (parametric shapes: cube, sphere, cylinder, etc.)
   - My Models library (save/load custom STL files)
   - **Purpose**: Etsy shop (cookie cutters) + in-person clients (custom stamps)

2. **Parametric CAD Program**
   - OpenSCAD-like programmatic 3D modeling
   - Create shapes with code/parameters
   - Boolean operations (union, difference, intersection)
   - **Purpose**: Technical CAD work

3. **People Finder Program**
   - Public records search
   - Federal records integration
   - Relationship detection
   - Address parsing and data organization
   - Machine learning for person identification
   - **Purpose**: Research and data collection tool

4. **Digital Footprint Program**
   - Online presence discovery
   - Reputation management
   - Social media tracking
   - **Purpose**: Digital identity research

### Unified Design Language
- **Theme**: Dark mode with neon blue accent color (#0095ff)
- **Background**: Animated crosshatch grid (neon blue glow)
- **Buttons**: Dark with neon blue borders (no colored fills, just outlines)
- **Navigation**: Each tool has a "Back to Hub" button to return to main launcher
- **Authentication**: Single passkey (442767) protects the entire suite

### Application Flow
```
Login Screen (passkey: 442767)
    ↓
ZoolZ Hub (4 bubbles/icons for each program)
    ↓
User clicks bubble to enter specific program
    ↓
Program loads with "Back to Hub" button
    ↓
User can navigate back to hub and switch to another program
```

### Development Philosophy
- Each program is independent (separate Flask blueprints)
- All programs share authentication and visual style
- Hub is the central navigation point
- Never break existing programs when working on one specific tool
- Read the whole codebase before making changes

---

## 🎨 CURRENT FOCUS: 3D MODELING PROGRAM

**Owner**: Zay (Isaiah)
**Business**: Etsy shop + in-person business clients
**Products**: Cookie cutters, stamps (leather work)
**Workflow**: Upload → Extract → Edit → Generate → Export

---

## 🎯 CURRENT SPRINT (Active Work)

### In Progress
- [ ] Password screen implementation (passkey: 442767)
- [ ] Cookie Cutter tool enhancement
- [ ] Stamp tool creation
- [ ] Inner detail outline tool

### Priority Queue
1. **Cookie Cutter Tool** - Make settings popup, add base hollow control
2. **Outline Editor** - Add line dragging (not just points)
3. **Stamp Tool** - Full implementation with positive/negative, solid/hollow
4. **Save Custom Shapes** - Add to shape library (separate from My Models)

---

## 🔥 BACKBURNER (Important but Not Urgent)

### Security (Local Only - No Rush)
- [ ] Path traversal vulnerability in my_models route
- [ ] Input validation on shape generators
- [ ] File upload size limits
- [ ] Rate limiting on expensive operations
- **NOTE**: Password screen (442767) is sufficient security for now

### Memory Leaks
- [ ] Three.js geometry disposal on mesh reload
- [ ] Undo stack bounded to prevent memory explosion
- [ ] Temp file cleanup job (delete files older than 1 hour)

### Bug Fixes (30 identified)
- [ ] Precision slider exponential scale (detail extraction)
- [ ] Split tool - load BOTH parts to scene
- [ ] Outline data normalization (pixels vs normalized coords)
- [ ] Boolean operations - add mesh validation
- [ ] Scene fusion - implement or hide button
- [ ] Duplicate object offset calculation
- [ ] Transform controls state sync
- [ ] Drainage holes positioning (hollow tool)
- [ ] Mirror merge - remove duplicate vertices
- [ ] Simplify - clamp reduction percent
- [ ] Thread generator - validate pitch/diameter
- [ ] Sphere subdivisions - add max bound
- [ ] Race conditions on multiple async operations
- [ ] State corruption from global mutable state
- [ ] No debouncing on generate button
- [ ] Touch support for outline editor
- [ ] HiDPI canvas support (retina displays)
- [ ] Mobile responsive breakpoints
- [ ] Keyboard shortcuts in input fields
- [ ] Event listener cleanup on unload
- [ ] STL loading blocks main thread
- [ ] No progress indicators on long operations
- [ ] Scene list unnecessary re-renders
- [ ] Cross-site scripting in object names
- [ ] No validation on empty object names
- [ ] No check if extraction fails before opening editor
- [ ] Detail precision value sent as integer not float
- [ ] No client-side parameter validation
- [ ] NaN values crash backend
- [ ] No file type validation (magic bytes)

### UI/UX Improvements
- [ ] Dark/light theme toggle
- [ ] Shape preview in picker
- [ ] Search/filter shapes
- [ ] Favorites/recent shapes
- [ ] Keyboard shortcut help overlay
- [ ] Mobile/tablet support
- [ ] Add undo to outline editor
- [ ] Multi-select objects (Ctrl+Click)
- [ ] Pagination for My Models (if 1000+ files)

### Performance Optimizations
- [ ] Bundle Three.js locally (don't use CDN)
- [ ] Cache shape picker (rebuild only once)
- [ ] Use CSS variables for theming
- [ ] Template system for repetitive HTML

### Missing Features (Advertised but Not Implemented)
- [ ] Multi-object fusion (button exists, shows "coming soon")
- [ ] Export scene as single STL (button exists, not implemented)
- [ ] Add/remove points in outline editor

---

## 🏗️ NEW FEATURES (Business Critical)

### Stamp Tool (Priority 1)
**Purpose**: Cookie cutter details + leather working stamps

**Requirements**:
- Input: Any outline (outer OR inner details)
- Positive stamp (raised) vs Negative stamp (recessed)
- Base options:
  - Full solid base
  - Connected by back bar
- Detail rendering:
  - Solid (filled)
  - Hollow (follow outline like cookie cutter blades)
- Special features:
  - Beveled edges (for leather work)
  - Adjustable bevel angle
  - Sharp vs rounded tips
- Precision controls (more robust than outer outline)

### Inner Detail Outline Tool (Priority 2)
**Purpose**: Extract fine details (eyes, patterns, etc.) with precision

**Requirements**:
- More robust than outer outline extractor
- Adjustable detail threshold (exponential scale)
- Limit to top 50 contours (sorted by area)
- Combined mode: Select outer + inner to get full linework
- Interactive editor:
  - Click and drag points
  - Click and drag lines (NEW - not just points)
  - Add/remove points
  - Smooth/simplify controls

### Save to Shape Library (Priority 3)
**Purpose**: Save custom cookie cutters as reusable shapes

**Requirements**:
- Separate from "My Models" (which is for STL files)
- Save shape definition (parameters + outline data)
- Appears in shape picker under "Custom" category
- Can regenerate with different parameters
- Export/import custom shape library

---

## 🔧 TOOL-SPECIFIC ENHANCEMENTS

### Cookie Cutter Tool
**Current Status**: Working but cluttered
**Needed**:
- ✅ Settings as popup (like shape picker)
- ✅ Blade thickness slider
- ✅ Base toggle (on/off)
- ✅ Base hollow option (see-through with adjustable hole size)
- ✅ Preview of cutter before generating

### Outline Editor
**Current Status**: Can drag points
**Needed**:
- ✅ Drag entire line segments (not just endpoints)
- ✅ Add points by clicking on line
- ✅ Remove points by right-click or Delete key
- ✅ Smooth selected points
- ✅ Reset to original outline
- ✅ Undo/redo within editor

---

## 📊 TESTING CHECKLIST

### Cookie Cutter Workflow
- [ ] Upload image → Extract outline → Edit → Generate cutter
- [ ] Upload image → Extract details → Generate detail stamp
- [ ] Settings: blade thickness variations (0.5mm to 5mm)
- [ ] Settings: base hollow with small push-hole
- [ ] Settings: no base (blades only)
- [ ] Save custom cutter to shape library

### Stamp Workflow
- [ ] Positive stamp (raised details)
- [ ] Negative stamp (recessed details)
- [ ] Solid base vs back bar
- [ ] Solid details vs hollow details
- [ ] Beveled edges for leather work
- [ ] Generate from outer outline
- [ ] Generate from inner details

### Outline Editor Precision
- [ ] Drag points smoothly
- [ ] Drag lines to adjust curve
- [ ] Add points mid-line
- [ ] Remove unnecessary points
- [ ] Undo/redo edits
- [ ] Zoom/pan on canvas

---

## 💼 BUSINESS USE CASES

### Etsy Shop (Cookie Cutters)
1. Customer sends image
2. Extract outline + inner details
3. Edit for clean lines
4. Generate cookie cutter (hollow base, 2mm blade)
5. Preview, download STL
6. Print and ship

### In-Person Clients (Custom Stamps)
1. Client provides logo/design
2. Extract outline with precision
3. Generate stamp (positive, beveled for leather)
4. Show preview to client
5. Adjust and finalize
6. Export STL for production

### Repeat Orders
1. Load saved custom shape from library
2. Adjust size/thickness for new order
3. Generate and export
4. Fast turnaround!

---

## 🐛 BUG PRIORITY LEVELS

### P0 (Breaks functionality - Fix ASAP)
- Outline data normalization mismatch
- Split tool only loads first part
- Race conditions on generate button
- State corruption from async operations

### P1 (Impacts quality - Fix this week)
- Precision slider wrong scale
- No mesh validation before boolean
- Memory leak on geometry reload
- Transform controls state not synced

### P2 (Annoying but workable - Fix this month)
- No progress indicators
- Scene list re-renders
- Touch support missing
- HiDPI canvas blurry

### P3 (Nice to have - Backlog)
- Dark/light theme toggle
- Shape search/filter
- Mobile responsive
- Keyboard shortcut help

---

## 📝 NOTES FOR CLAUDE

### User Preferences
- Name: Zay (Isaiah)
- Passkey: 442767
- Business: Etsy shop + in-person clients
- Products: Cookie cutters, stamps (leather work)
- Style: Dark theme, neon blue (#0095ff), clean UI
- Workflow: Upload → Extract → Edit → Generate → Export

### Code Style
- Backend: Flask blueprints, trimesh for 3D ops
- Frontend: Vanilla JS (no frameworks), Three.js for rendering
- UI: Dark mode, collapsible panels, popup modals
- Theme: Professional but playful (emojis in buttons)

### Key Pain Points
- Needs PRECISION for client work
- Needs SPEED for Etsy orders
- Needs VERSATILITY (cookie cutters AND leather stamps)
- Local only (security not critical yet)

### Development Philosophy
- "Foundation mindset" - nothing is complete, always improving
- Functionality over perfection
- Business needs drive priorities
- Test with real use cases

---

## 🎨 VISUAL DESIGN NOTES

### Password Screen
- Background: Animated wizards, mountains, lightning
- Input: Dark grey centered box
- Text: "ENTER PASSWORD TO PROCEED" in gold fancy font
- Auto-login as "Zay" from passkey 442767

### Cookie Cutter Settings Modal
- Popup overlay (like shape picker)
- Sliders with live preview
- Base hollow toggle with hole size slider
- Generate button at bottom

### Stamp Tool Panel
- Positive/Negative toggle (visual icons)
- Base type: Full solid vs Back bar (radio buttons)
- Detail rendering: Solid vs Hollow (toggle)
- Bevel settings: Angle slider + Sharp/Rounded toggle

---

## 🚀 DEPLOYMENT CHECKLIST (When Ready)

- [ ] Security hardening (when going public)
- [ ] Rate limiting
- [ ] User authentication (if multi-user)
- [ ] Database for saved shapes
- [ ] Backup system for custom library
- [ ] Analytics (track most-used tools)
- [ ] Error reporting (Sentry or similar)
- [ ] Performance monitoring
- [ ] User documentation
- [ ] Video tutorials

---

**End of Loop File** | Keep this updated as work progresses!
