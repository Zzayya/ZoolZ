# 📎 Attachment System - How It Works

## Overview

The attachment system allows you to **add features to existing objects** instead of generating them standalone.

**Example:** Instead of generating a random snap clip, you:
1. Load a cube
2. Click "Add Snap Clip"
3. Click an edge
4. System measures the edge (83mm)
5. Shows popup: "Clip for 83mm edge"
6. Click "Attach"
7. System generates clip, positions it, and boolean-unions it to the cube
8. Done! Cube now has a functional snap clip on the edge

---

## How to Use

### 1. **Load an Object**
- Generate a shape (cube, container, etc.)
- OR upload an STL file

### 2. **Click Attachment Button**
- Click "Add Snap Clip" (or any attachment tool)
- System enters **Attachment Mode**

### 3. **Select Object**
- Click on the object you want to add the feature to
- Object highlights in blue

### 4. **Select Location**
- For snap clips: Click on an edge
- For threads: Click on a cylinder surface
- For mounting holes: Click on a flat surface

### 5. **System Measures**
- Edge length automatically detected
- Surface dimensions calculated
- Popup shows measurements with defaults

### 6. **Configure & Attach**
- Adjust parameters if needed
- Click "Attach"
- System generates the feature
- Boolean-unions it to your object
- Loads the merged result

---

## Current Attachments

### ✅ **Snap Clip** (Working)
- Click edge
- Auto-sizes to edge length
- Boolean-unions to object

### 🚧 **510 Thread** (In Progress)
- Will detect cylinder surfaces
- Auto-size to diameter
- Add male or female threads

### 🚧 **Mounting Holes** (In Progress)
- Will detect flat surfaces
- Pattern options (grid, corners, line)
- Configurable spacing

---

## How It Works Internally

### Frontend (attachment_system.js)

1. **Enter Attachment Mode**
```javascript
enterAttachmentMode('snap_clip')
// - Sets mode active
// - Shows instructions
// - Enables raycasting
```

2. **Click Detection**
```javascript
onAttachmentClick(event)
// - Raycast to find clicked object/face
// - First click: Select object
// - Second click: Select edge/surface
```

3. **Edge Measurement**
```javascript
detectAndMeasureEdge(point, face, object)
// - Finds nearest edge to click
// - Calculates edge length
// - Stores edge start/end points
```

4. **Generation & Merge**
```javascript
generateAndAttachClip()
// - Step 1: Generate clip via /api/generate/shape
// - Step 2: Fetch current object STL
// - Step 3: Boolean union via /api/stl/boolean
// - Step 4: Load merged result
```

### Backend (blueprint.py)

**Existing Routes Used:**
- `/api/generate/shape` - Generates the attachment (clip, thread, etc.)
- `/api/stl/boolean` - Merges attachment with object via boolean union

**No new backend needed!** The attachment system is purely a frontend workflow that uses existing backend routes.

---

## Architecture Pattern

This is a **SMART workflow pattern**:

**Old Way (Generators):**
```
User clicks "Snap Clip"
→ Generates random 50mm clip
→ User confused: "How do I attach this?"
```

**New Way (Attachments):**
```
User clicks "Add Snap Clip"
→ Click object
→ Click edge
→ System measures (83mm)
→ Generates 83mm clip
→ Auto-positions and merges
→ Done!
```

This pattern can be used for ANY attachment:
- Threads (measure cylinder diameter)
- Mounting holes (measure surface area)
- Handles (measure side dimensions)
- Drainage holes (detect bottom surface)
- Text labels (detect flat surface for embossing)

---

## Adding New Attachments

To add a new attachment type:

1. **Add button to HTML**
```html
<button onclick="enterAttachmentMode('new_attachment')">
    Add New Feature
</button>
```

2. **Add instructions**
```javascript
// In getInstructionsForType()
'new_attachment': {
    step1: '1. Click on a SURFACE',
    step2: '2. Configure feature'
}
```

3. **Add detection function**
```javascript
function detectNewFeatureSurface(point, face, object) {
    // Measure what you need
    // Store in attachmentMode.measurements
}
```

4. **Add popup**
```javascript
function showNewFeaturePopup(measurements) {
    // Create popup with parameters
    // Button calls generateAndAttachNewFeature()
}
```

5. **Add generation function**
```javascript
async function generateAndAttachNewFeature() {
    // Generate feature via API
    // Boolean union with object
    // Load result
}
```

That's it! The framework handles everything else.

---

## Why This Matters

**Traditional 3D modeling software:**
- Generate clip manually
- Position it manually (tedious)
- Align to edge manually (error-prone)
- Boolean union manually
- 10+ steps, takes minutes

**ZoolZ Attachment System:**
- Click "Add Snap Clip"
- Click edge
- Click "Attach"
- 3 steps, takes seconds

This is **professional-grade UX** for makers who just want to get shit done.
