# ZoolZ 3D Modeling - Quick Start Guide

## 🚀 START THE APP

```bash
cd /Users/isaiahmiro/Desktop/ZoolZ
python3 app.py
```

Then open: **http://localhost:5000/modeling/**

---

## 📁 FOLDER STRUCTURE

- **uploads/** - Temporary folder for images you upload (auto-cleaned)
- **outputs/** - Temporary generated STL files before saving
- **ModelingSaves/** - YOUR permanent model library ⭐

When you save a model, it goes to **ModelingSaves/** - that's your library!

---

## 🎯 YOUR KEY WORKFLOWS

### 1. COOKIE CUTTER (Ponyo Example)
1. Click "Cookie Cutter" tool
2. Upload `ModelingSaves/Ponyo.png`
3. Adjust blade height, thickness, etc.
4. Click "Generate"
5. Click "Save to My Models" → saves to ModelingSaves/

**API Route:** `POST /modeling/api/generate`

### 2. WIDEN HOLE (Pain Beads)
**NEW TOOL! ✨**

For your hoodie string beads:
1. Click "Widen Hole" tool
2. Upload `ModelingSaves/Pain Bead 1.stl`
3. Enter new radius (e.g., 3mm → 4mm)
4. Click "Auto-detect & Widen"
5. Download or save result

**API Route:** `POST /modeling/api/stl/widen_hole`

**Parameters:**
- `new_radius` - desired hole size
- `auto_detect` - true (finds center hole automatically)
- `height_min/max` - optional (widen only part of hole)

### 3. THICKEN WALLS (Flexy Worm)
For making walls thicker:
1. Click "Thicken" tool
2. Upload `ModelingSaves/Morf Worm.stl`
3. Set thickness increase (e.g., 0.5mm)
4. Click "Apply"
5. Walls get thicker evenly!

**API Route:** `POST /modeling/api/stl/thicken`

### 4. FIDGET PEN WORKFLOW (Complex Example)
To recreate `FdgtPenRemix.stl` from `Fdgtmstr.stl`:

1. **Load** `Fdgtmstr.stl`
2. **Cut/Shave Top:**
   - Use "Split" tool
   - Cut at specific height
   - Keep bottom part
3. **Widen Center Hole:**
   - Use "Widen Hole" tool
   - Set height_min to 5mm (above bottom)
   - Set new_radius to fit pen
4. **Keep Bottom Hole:**
   - Bottom hole stays same size automatically
   - Only the portion above height_min gets widened

---

## 🛠 ALL AVAILABLE TOOLS

### COOKIE CUTTER TOOLS
- ✅ **Cookie Cutter Generator** - Image → STL
- ✅ **Outline Editor** - Manual outline editing
- ✅ **Detect Holes** - Find holes in model ⭐ NEW!

### STL EDITING TOOLS
- ✅ **Thicken** - Make walls thicker
- ✅ **Hollow** - Hollow out models
- ✅ **Repair** - Fix mesh issues
- ✅ **Simplify** - Reduce polygons
- ✅ **Mirror** - Mirror across axis
- ✅ **Scale** - Resize models
- ✅ **Boolean** - Union/difference/intersection
- ✅ **Split/Cut** - Cut models
- ✅ **Widen Hole** - Enlarge cylindrical holes ⭐ NEW!
- ✅ **Channels** - Add drainage channels
- ✅ **Array** - Create patterns

### FILE OPERATIONS
- ✅ **My Models** - Browse ModelingSaves/ library
- ✅ **Save** - Save to ModelingSaves/
- ✅ **Download** - Export STL
- ✅ **Open in Cura** - Send directly to slicer (coming soon)

---

## 🎨 TESTING CHECKLIST

### Test 1: Cookie Cutter ✓
```bash
curl -X POST http://localhost:5000/modeling/api/generate \
  -F "image=@ModelingSaves/Ponyo.png" \
  -F "blade_height=15" \
  -F "blade_thick=2"
```

### Test 2: Widen Hole (Pain Bead) ✓
```bash
curl -X POST http://localhost:5000/modeling/api/stl/widen_hole \
  -F "stl=@ModelingSaves/Pain Bead 1.stl" \
  -F "new_radius=4.0" \
  -F "auto_detect=true"
```

### Test 3: Thicken (Flexy Worm) ✓
```bash
curl -X POST http://localhost:5000/modeling/api/stl/thicken \
  -F "stl=@ModelingSaves/Morf Worm.stl" \
  -F "thickness_mm=0.5" \
  -F "auto_detect=true"
```

### Test 4: Detect Holes ✓
```bash
curl -X POST http://localhost:5000/modeling/api/stl/detect_holes \
  -F "stl=@ModelingSaves/Pain Bead 1.stl"
```

---

## 🐛 TROUBLESHOOTING

### Import Error
```bash
cd /Users/isaiahmiro/Desktop/ZoolZ
python3 -c "from programs.modeling.utils import bore_hole; print('OK')"
```

### Port Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### Check Config
```bash
python3 -c "from config import Config; print(Config.MY_MODELS_FOLDER)"
# Should print: /Users/isaiahmiro/Desktop/ZoolZ/ModelingSaves
```

---

## 📝 API QUICK REFERENCE

All routes are under `/modeling/api/`

### Generation
- `POST /generate` - Cookie cutter from image
- `POST /extract_outline` - Get outline data
- `POST /generate_from_outline` - Cookie from edited outline

### STL Operations
- `POST /stl/widen_hole` ⭐ NEW! - Widen cylindrical holes
- `POST /stl/detect_holes` ⭐ NEW! - Find holes in mesh
- `POST /stl/thicken` - Thicken walls
- `POST /stl/hollow` - Hollow out
- `POST /stl/repair` - Fix mesh
- `POST /stl/simplify` - Reduce polygons
- `POST /stl/mirror` - Mirror mesh
- `POST /stl/scale` - Scale mesh
- `POST /stl/boolean` - Boolean operations
- `POST /stl/split` - Cut/split mesh
- `POST /stl/cut` - Cut with plane
- `POST /stl/channels` - Add channels

### My Models
- `GET /api/my_models/list` - List ModelingSaves/
- `GET /my_models/<filename>` - Load specific model
- `POST /api/my_models/save` - Save to ModelingSaves/
- `DELETE /api/my_models/delete/<filename>` - Delete model

---

## ✅ WHAT'S READY NOW

✅ Cookie cutter generation
✅ Outline detection and editing
✅ **Widen hole tool (NEW!)** - Perfect for pain beads
✅ Thicken tool - Perfect for flexy worm
✅ Cut/split tools - Perfect for fidget pen top removal
✅ All STL operations working
✅ ModelingSaves folder properly configured
✅ Save/load from My Models library

## 🔜 COMING SOON

⏳ "Open in Cura" button (next)
⏳ UI improvements for widen hole controls
⏳ Visual hole detection preview

---

## 💡 PRO TIPS

1. **Pain Beads:** Use auto-detect mode, it finds the center hole automatically
2. **Flexy Worm:** Start with small thickness increase (0.3-0.5mm), test print
3. **Fidget Pen:** Use height_min/max to widen only top portion
4. **Cookie Cutters:** Higher detail_level = more detail but more polygons
5. **Always save to My Models** so you don't lose your work!

---

**You're all set! Your Etsy orders are ready to go! 🎉**
