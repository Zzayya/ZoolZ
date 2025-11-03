# Parametric CAD - What's New (Enhanced Version)

## 🎉 Major Enhancements Added

### ✅ 1. Click to Select Shapes (3D Interaction)
**What it does:** Click directly on shapes in the 3D viewer to select them

**How to use:**
- **Click** a shape → Select it
- **Ctrl+Click** → Add to selection (multi-select)
- **Click empty space** → Deselect all
- **Escape key** → Deselect all

**Visual feedback:**
- Selected shapes turn **cyan/bright blue**
- Selected shapes **glow** (emissive material)
- Transform gizmo attaches to selected shape

---

### ✅ 2. Transform Gizmos (Move/Rotate/Scale)
**What it does:** Interactive 3D gizmos for transforming shapes with your mouse

**How to use:**
- **Move mode (G key):** Drag arrows to move along X/Y/Z axes
- **Rotate mode (R key):** Drag circles to rotate around axes
- **Scale mode (S key):** Drag cubes to scale along axes

**Keyboard shortcuts:**
- `G` = Move (translate)
- `R` = Rotate
- `S` = Scale
- `Esc` = Deselect

**Visual:**
- Red arrow/circle/cube = X axis
- Green = Y axis
- Blue = Z axis

---

### ✅ 3. Properties Panel (Right sidebar)
**What it does:** Edit selected shape properties with numeric inputs

**Features:**
- **Shape name** - Rename shapes (e.g., "base_plate", "mounting_hole")
- **Visibility toggle** - Hide/show shapes
- **Lock** - Prevent accidental edits (TODO)
- **Position X/Y/Z** - Precise numeric positioning
- **Rotation X/Y/Z** - Precise rotation in degrees
- **Scale X/Y/Z** - Precise scaling multipliers
- **Reset transforms** - Zero out all transforms

**Live updates:**
- Dragging gizmo updates numeric inputs
- Typing numbers updates gizmo position

---

### ✅ 4. Shape Naming System
**What it does:** Give meaningful names to shapes for better organization

**Default names:** `box_0`, `cylinder_1`, etc.
**Custom names:** "base_plate", "left_bracket", "mounting_hole_front"

**Benefits:**
- Find shapes easily in the list
- Better OpenSCAD code comments
- Organize complex designs

---

### ✅ 5. Undo/Redo System
**What it does:** Step backward/forward through your design history

**Keyboard shortcuts:**
- `Ctrl+Z` = Undo
- `Ctrl+Y` or `Ctrl+Shift+Z` = Redo

**What's saved:**
- Shape positions
- Shape rotations
- Shape scales
- Shape names

**History limit:** Last 50 actions

---

### ✅ 6. Delete Selected Shapes
**What it does:** Remove shapes from the scene

**How to use:**
- Select shape(s)
- Press `Delete` or `Backspace` key
- Or click "Delete" button in shapes list

---

### ✅ 7. Enhanced Shape List
**What it does:** Manage all shapes in your scene

**Features:**
- Click shape in list → Select in 3D viewer
- Selected shapes highlighted in list
- Shows shape name and type
- Delete button per shape

---

## 🎮 Complete Interaction Guide

### Mouse Controls
- **Left click** - Select shape or deselect all
- **Ctrl+Left click** - Add to selection (multi-select)
- **Left drag** (on gizmo) - Transform selected shape
- **Right drag** - Rotate camera (orbit)
- **Middle drag** or **Shift+Right drag** - Pan camera
- **Scroll wheel** - Zoom in/out

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `G` | Switch to Move mode |
| `R` | Switch to Rotate mode |
| `S` | Switch to Scale mode |
| `Esc` | Deselect all |
| `Delete` / `Backspace` | Delete selected |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |

### Workflow Example

**Before (Old Way):**
```
1. Create box
2. Realize it's in wrong position
3. Delete it
4. Create new box with different parameters
5. Repeat until correct
```

**After (New Way):**
```
1. Create box
2. Click it to select
3. Press G to move
4. Drag to position
5. Press R to rotate
6. Drag to angle
7. Type exact values in properties panel
8. Done! Undo if needed.
```

---

## 🔧 What's Coming Next

### High Priority (Week 1-2)
- [ ] **Modifiers panel**
  - Fillet (round edges)
  - Chamfer (bevel edges)
  - Array (duplicate in patterns)
  - Mirror (flip across axis)
  - Hollow/Shell (make hollow with walls)

- [ ] **Measurement tools**
  - Distance between points
  - Bounding box dimensions
  - Volume and surface area

- [ ] **Alignment tools**
  - Snap to grid
  - Align left/right/center
  - Distribute evenly

- [ ] **Enhanced OpenSCAD export**
  - Use shape names as module names
  - Add comments for each operation
  - Include transform history
  - Generate clean, readable code

### Medium Priority (Month 1)
- [ ] **2D to 3D operations**
  - Extrude 2D shapes into 3D
  - Revolve profiles around axes
  - Sweep along paths

- [ ] **Advanced primitives**
  - 3D text
  - Polygons (custom sided)
  - Helixes/springs
  - Wedges, capsules, domes

- [ ] **Variables system**
  - Define global variables
  - Parametric relationships (width = height * 2)
  - Update all shapes when variable changes

### Long-term (Month 2+)
- [ ] **Threads and mechanical parts**
  - ISO metric threads (M3, M4, M5, etc.)
  - Gears (spur, helical)
  - Bearings, bolts, nuts

- [ ] **Assembly mode**
  - Group related shapes
  - Hierarchical relationships
  - Move groups together

---

## 📊 Current vs Enhanced Comparison

| Feature | Before | After |
|---------|--------|-------|
| **Select shapes** | Click in list only | Click in 3D viewer ✅ |
| **Move shapes** | Recreate from scratch | Drag gizmo or type values ✅ |
| **Rotate shapes** | ❌ Not possible | Drag rotate gizmo ✅ |
| **Scale shapes** | ❌ Not possible | Drag scale gizmo ✅ |
| **Shape names** | shape_0, shape_1 | Custom names ✅ |
| **Properties panel** | ❌ None | Full transform editor ✅ |
| **Undo/Redo** | ❌ Not possible | Ctrl+Z / Ctrl+Y ✅ |
| **Keyboard shortcuts** | ❌ None | G/R/S/Esc/Delete ✅ |
| **Multi-select** | ❌ Not possible | Ctrl+Click ✅ |
| **Precise values** | Only at creation | Edit anytime ✅ |

---

## 🎯 Benefits

### For Beginners:
- **Visual** - See and click shapes instead of remembering IDs
- **Intuitive** - Drag to move, just like other 3D software
- **Forgiving** - Undo mistakes instantly
- **Discoverable** - Right-click or explore panels

### For Advanced Users:
- **Precise** - Type exact numeric values
- **Efficient** - Keyboard shortcuts for speed
- **Flexible** - Transform shapes after creation
- **Professional** - Proper naming and organization

### For Everyone:
- **Better OpenSCAD code** - Named shapes, comments, structure
- **Share designs** - Others can understand your code
- **Iterate faster** - Try variations without recreating
- **Learn programmatic design** - Bridge visual → code

---

## 🚀 Getting Started

1. **Create some shapes** - Add box, cylinder, etc.
2. **Click a shape** in the 3D viewer
3. **Press G** and drag to move it
4. **Press R** and drag to rotate it
5. **Look at properties panel** on the right
6. **Type exact values** if needed
7. **Rename the shape** to something meaningful
8. **Create more shapes** and position them
9. **Select multiple** with Ctrl+Click
10. **Apply boolean operations** (union, difference)
11. **Export OpenSCAD code** - now it has comments and names!

---

## 💡 Pro Tips

1. **Use meaningful names** - "base_plate" not "box_3"
2. **G/R/S are your friends** - Muscle memory for speed
3. **Undo liberally** - Try things, undo if wrong
4. **Properties panel for precision** - Type exact 10.5mm not drag
5. **Multi-select for bulk ops** - Move multiple shapes together
6. **Delete key is quick** - Select and delete, no confirm

---

This is a **MASSIVE** upgrade from the basic viewer! 🎉

Next steps: Do you want me to implement the **modifiers** (fillet, chamfer, array, mirror) or the **measurement tools** next?
