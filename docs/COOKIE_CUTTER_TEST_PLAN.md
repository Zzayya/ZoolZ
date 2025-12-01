# Cookie Cutter Tool - Test Plan & Enhancement Roadmap

**Date**: 2025-11-20
**Owner**: Zay
**Status**: Testing & Enhancement

---

## 🧪 CURRENT FUNCTIONALITY TEST

### Test 1: Direct Generation (Old Workflow)
- [ ] Upload image (PNG/JPG)
- [ ] Adjust blade thickness (0.5mm - 5mm)
- [ ] Adjust blade height (5mm - 60mm)
- [ ] Adjust base thickness
- [ ] Click "Generate" button
- [ ] **Expected**: Cookie cutter STL downloads
- [ ] **Expected**: Model appears in 3D viewer
- [ ] **Expected**: Can download and print

**ISSUES TO CHECK**:
- Does blade thickness actually affect output?
- Is "No Base" checkbox working?
- Are sliders updating their value displays?

### Test 2: Extract & Edit Outline (New Workflow)
- [ ] Upload image
- [ ] Click "Extract & Edit Outline"
- [ ] **Expected**: Outline editor opens with detected outline
- [ ] Drag control points to adjust outline
- [ ] Click "Generate Cookie Cutter"
- [ ] **Expected**: STL generated from edited outline

**KNOWN BUGS TO VERIFY**:
1. ❌ Outline data might be in pixel coords (not normalized)
2. ❌ Outline might have 10,000+ points (slow)
3. ❌ Can't drag line segments (only endpoints)
4. ❌ Can't add/remove points
5. ❌ No undo in outline editor

### Test 3: Extract Inner Details (New Workflow)
- [ ] Upload image with details (eyes, patterns)
- [ ] Adjust "Inner Detail Precision" slider
- [ ] Click "Extract Inner Details"
- [ ] **Expected**: Opens outline editor with detail contours
- [ ] Click "Generate Detail Stamp"
- [ ] **Expected**: STL with raised/recessed details

**KNOWN BUGS TO VERIFY**:
1. ❌ Precision slider uses linear scale (should be exponential)
2. ❌ Sends integer 0-100 instead of float 0.0-1.0
3. ❌ Can return 10,000+ tiny contours (crashes browser)
4. ❌ Details not sorted by area (random order)

---

## 🔧 ENHANCEMENT CHECKLIST

### Enhancement 1: Cookie Cutter Settings Popup
**Purpose**: Reduce clutter, make UI cleaner

**Requirements**:
- [ ] Create popup modal (like shape picker)
- [ ] Move all cookie cutter settings into modal
- [ ] Add "⚙️ Cookie Cutter Settings" button in top toolbar
- [ ] Settings persist between opens
- [ ] "Apply" and "Cancel" buttons

**Settings to Include**:
- Blade thickness slider
- Blade height slider
- Base thickness slider
- Base extension slider
- Max dimension slider
- Detail level slider
- Base options (see Enhancement 2)
- Inner detail precision slider

### Enhancement 2: Base Hollow Option
**Purpose**: Create see-through base with push-hole (Zay's preferred style)

**New Controls**:
- [ ] Base Type dropdown/toggle:
  - Full Solid Base (current default)
  - Hollow Base (see-through)
  - No Base (blades only - existing)

- [ ] Hollow Base Settings (only show if "Hollow Base" selected):
  - [ ] Hole Size slider (5mm - 50mm)
    - Label: "Center Hole Diameter"
    - Default: 20mm (good for pushing out dough)
  - [ ] Wall Thickness slider (2mm - 10mm)
    - Label: "Outer Wall Thickness"
    - Default: 5mm

**Backend Changes Needed**:
```python
# In utils/cookie_logic.py
def generate_cookie_cutter(..., base_type='solid', hole_diameter=20, wall_thickness=5):
    if base_type == 'hollow':
        # Create base with center hole
        # Boolean subtract cylinder from base
    elif base_type == 'none':
        # Existing no-base logic
    else:
        # Full solid base
```

### Enhancement 3: Outline Editor Improvements
**Purpose**: Precision editing for business-quality cookie cutters

**New Features**:
- [ ] **Drag entire line segments** (not just points)
  - Click on line between points
  - Drag to adjust curve
  - Both endpoints move proportionally

- [ ] **Add points mid-line**
  - Double-click on line
  - New point inserted at click position

- [ ] **Remove points**
  - Right-click on point → "Delete Point"
  - Or select + press Delete key
  - Can't delete if < 3 points remain

- [ ] **Smooth points**
  - Select point(s)
  - Click "Smooth" button
  - Applies bezier smoothing

- [ ] **Undo/Redo within editor**
  - Track edit history
  - Ctrl+Z / Ctrl+Y
  - Show undo stack count

- [ ] **Reset to original**
  - "Reset Outline" button
  - Reverts to initial extraction

- [ ] **Zoom & Pan**
  - Mouse wheel to zoom
  - Middle-click drag to pan
  - Fit to view button

**UI Additions**:
```html
<div class="outline-editor-toolbar">
    <button onclick="outlineEditor.undo()">↶ Undo</button>
    <button onclick="outlineEditor.redo()">↷ Redo</button>
    <button onclick="outlineEditor.smooth()">〜 Smooth</button>
    <button onclick="outlineEditor.reset()">⟲ Reset</button>
    <button onclick="outlineEditor.fitView()">🔍 Fit</button>
</div>
```

### Enhancement 4: Inner Detail Tool (Robust Version)
**Purpose**: Extract fine details with precision for stamps

**Improvements Over Current**:
- [ ] **Exponential precision scale**
  ```javascript
  // Instead of linear 0-100
  const minArea = totalArea * Math.pow(0.001, precision);
  ```

- [ ] **Contour limiting**
  - Sort contours by area (largest first)
  - Limit to top 50 contours
  - Show count: "Found 50 details (showing largest)"

- [ ] **Contour preview**
  - Show each contour as separate color
  - Toggle visibility per contour
  - Select which to include in stamp

- [ ] **Detail categories**
  - Auto-categorize: Large, Medium, Small, Tiny
  - Filter by category
  - Batch select/deselect

**New UI Panel**:
```html
<div class="detail-contours-panel">
    <h4>Detected Details (50)</h4>
    <div class="contour-list">
        <div class="contour-item">
            <input type="checkbox" checked>
            <span class="contour-color" style="background: red;"></span>
            <span class="contour-label">Large Detail 1 (450px²)</span>
        </div>
        <!-- Repeat for each contour -->
    </div>
</div>
```

---

## 🆕 NEW TOOL: STAMP GENERATOR

### Purpose
Create raised (positive) or recessed (negative) stamps for:
- Cookie dough details
- Leather working (beveled, sharp edges)
- Clay stamping

### UI Layout
**New Tool Button**: 🎫 Stamp (in left tool panel)

**Settings Panel** (popup modal):

#### 1. Stamp Type
```html
<div class="stamp-type-selector">
    <label>
        <input type="radio" name="stampType" value="positive" checked>
        <div class="stamp-type-card">
            <div class="stamp-icon">⬆️</div>
            <div class="stamp-label">Positive (Raised)</div>
            <div class="stamp-desc">Details stick up</div>
        </div>
    </label>
    <label>
        <input type="radio" name="stampType" value="negative">
        <div class="stamp-type-card">
            <div class="stamp-icon">⬇️</div>
            <div class="stamp-label">Negative (Recessed)</div>
            <div class="stamp-desc">Details press in</div>
        </div>
    </label>
</div>
```

#### 2. Base Structure
```html
<div class="param-group">
    <label>Base Type</label>
    <select id="stampBaseType">
        <option value="solid">Full Solid Base</option>
        <option value="backbar">Connected by Back Bar</option>
        <option value="minimal">Minimal Support</option>
    </select>
</div>

<div class="param-group">
    <label>Base Thickness (mm)</label>
    <input type="range" id="stampBaseThickness" min="2" max="20" value="5">
    <span class="param-value">5mm</span>
</div>
```

#### 3. Detail Rendering
```html
<div class="param-group">
    <label>Detail Style</label>
    <div class="toggle-buttons">
        <button class="toggle-btn active" data-value="solid">
            ⬛ Solid (Filled)
        </button>
        <button class="toggle-btn" data-value="hollow">
            ⭕ Hollow (Outline)
        </button>
    </div>
</div>

<div id="hollowDetailSettings" style="display: none;">
    <div class="param-group">
        <label>Wall Thickness (mm)</label>
        <input type="range" id="detailWallThickness" min="0.5" max="3" value="1.5">
        <span class="param-value">1.5mm</span>
    </div>
</div>
```

#### 4. Edge Style (For Leather Work)
```html
<div class="param-group">
    <label>Edge Profile</label>
    <select id="stampEdgeProfile">
        <option value="rounded">Rounded (Safe)</option>
        <option value="sharp">Sharp (Cutting)</option>
        <option value="beveled">Beveled (Leather Work)</option>
    </select>
</div>

<div id="bevelSettings" style="display: none;">
    <div class="param-group">
        <label>Bevel Angle (degrees)</label>
        <input type="range" id="bevelAngle" min="15" max="60" value="30">
        <span class="param-value">30°</span>
    </div>

    <div class="param-group">
        <label>Bevel Depth (mm)</label>
        <input type="range" id="bevelDepth" min="0.5" max="5" value="2">
        <span class="param-value">2mm</span>
    </div>
</div>
```

#### 5. Stamp Dimensions
```html
<div class="param-group">
    <label>Detail Height/Depth (mm)</label>
    <input type="range" id="stampDetailHeight" min="0.5" max="10" value="2">
    <span class="param-value">2mm</span>
</div>

<div class="param-group">
    <label>Max Dimension (mm)</label>
    <input type="range" id="stampMaxDim" min="20" max="300" value="80">
    <span class="param-value">80mm</span>
</div>
```

### Backend Implementation
**New File**: `utils/stamp_logic.py`

```python
def generate_stamp(
    outline_data,
    stamp_type='positive',  # 'positive' or 'negative'
    base_type='solid',  # 'solid', 'backbar', 'minimal'
    base_thickness=5,
    detail_style='solid',  # 'solid' or 'hollow'
    detail_wall_thickness=1.5,
    edge_profile='rounded',  # 'rounded', 'sharp', 'beveled'
    bevel_angle=30,
    bevel_depth=2,
    detail_height=2,
    max_dimension=80
):
    """
    Generate stamp STL from outline data
    """
    # Implementation here
    pass
```

**New Route**: `/modeling/api/generate_stamp` in `blueprints/modeling.py`

---

## 🔖 SAVE CUSTOM SHAPES TO LIBRARY

### Purpose
Save useful cookie cutter shapes (especially no-base/hollow ones) for reuse

### UI
**"Save to Library" button** in modeling interface (when cookie cutter is loaded)

### Workflow
1. User generates cookie cutter (no base, specific blade thickness)
2. Clicks "💾 Save to Library"
3. Popup asks for:
   - Shape name
   - Category (or create new)
   - Icon emoji (optional)
4. Shape saved with parameters
5. Appears in Shape Picker under "Custom" category

### Data Structure
```json
{
    "id": "custom_001",
    "name": "Star Cookie Cutter",
    "category": "Custom",
    "icon": "⭐",
    "type": "cookie_cutter",
    "params": {
        "outline": [[x1,y1], [x2,y2], ...],
        "blade_thickness": 2.0,
        "blade_height": 20,
        "base_type": "none"
    },
    "created_at": "2025-11-20T12:00:00Z"
}
```

### Storage
**File**: `my_models/custom_shapes.json`

### Import/Export
- Export entire custom library as JSON
- Import from other ZoolZ installations
- Share custom shapes

---

## 🐛 CRITICAL BUGS TO FIX (From Analysis)

### P0 (Fix During Enhancement)
1. ❌ **Outline data normalization**
   - Currently sends pixel coords
   - Should normalize to 0-1 range
   - **Fix**: In outline_editor.js

2. ❌ **Precision slider scale**
   - Currently linear 0-100
   - Should be exponential
   - **Fix**: In modeling_controller.js extractDetailsFromImage()

3. ❌ **Precision value sent as integer**
   - Sends 50 instead of 0.5
   - **Fix**: `precision: parseFloat(val) / 100`

4. ❌ **No contour limiting**
   - Can return 10,000+ contours
   - **Fix**: Limit to top 50, sorted by area

### P1 (Fix After Testing)
5. ❌ **No simplification of outline**
   - 10,000+ points creates huge STL
   - **Fix**: Add Douglas-Peucker simplification

6. ❌ **No validation of self-intersecting outlines**
   - Creates non-manifold mesh
   - **Fix**: Check for self-intersection before generating

7. ❌ **Blade thickness not validated**
   - Can be 0.01mm (impossible to print)
   - **Fix**: Warn if < 0.8mm

---

## 📊 TESTING PRIORITIES

### Round 1: Verify Current Functionality
- [ ] Test direct generation
- [ ] Test outline extraction
- [ ] Test detail extraction
- [ ] Document all bugs found

### Round 2: Implement Enhancements
- [ ] Cookie Cutter settings popup
- [ ] Base hollow option
- [ ] Outline editor improvements

### Round 3: New Tools
- [ ] Stamp tool implementation
- [ ] Save to library feature

### Round 4: Production Testing
- [ ] End-to-end Etsy workflow
- [ ] Leather stamp workflow
- [ ] Performance testing (large images)

---

## 💼 BUSINESS USE CASES (Priority Order)

### 1. Standard Cookie Cutter (Most Common)
**Workflow**:
1. Upload image
2. Extract outline
3. Minor edits (smooth corners)
4. Settings: 2mm blade, 20mm height, hollow base
5. Generate & download
6. **Time**: < 5 minutes

### 2. Detailed Cookie Cutter (Inner Details)
**Workflow**:
1. Upload image (character with eyes, clothing)
2. Extract outer outline
3. Extract inner details (precision: medium)
4. Edit both outlines
5. Generate cutter + detail stamp separately
6. **Time**: < 10 minutes

### 3. Leather Stamp (Custom Orders)
**Workflow**:
1. Upload logo/design
2. Extract outline (high precision)
3. Edit for clean lines
4. Stamp tool: Positive, beveled 30°, solid details
5. Preview, adjust
6. Generate & download
7. **Time**: < 15 minutes

### 4. Repeat Order (Saved Shape)
**Workflow**:
1. Open shape library
2. Load saved shape
3. Adjust size if needed
4. Generate
5. **Time**: < 2 minutes

---

**Next Steps**: Start testing current functionality, then implement enhancements systematically.
