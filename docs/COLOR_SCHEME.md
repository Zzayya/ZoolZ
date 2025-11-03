# ZoolZ Color Scheme Guide

## 🎨 Official Color Palette

Each tool in the ZoolZ hub has its own distinct color scheme for easy visual identification.

---

## 🍪 Cookie Cutter - CREAM

### Color Codes
```css
Primary:   #F5DEB3  (Wheat)
Secondary: #FFE4B5  (Moccasin)
Accent:    #FAEBD7  (Antique White)
Dark:      #D2B48C  (Tan)
Glow:      #FFEFD5  (Papaya Whip)
```

### Usage
- **Hub bubble:** Cream gradient with tan glow
- **Headers:** Cream to moccasin gradient
- **Buttons:** Cream backgrounds with tan borders
- **Accents:** Soft cream borders and glows
- **Hover effects:** Brighter cream with enhanced glow

### Why Cream?
Warm, inviting color that evokes baking and cookies. Soft and friendly, perfect for the cookie cutter tool's playful nature.

---

## 🔧 Parametric CAD - ORANGE

### Color Codes
```css
Primary:   #FF8C42  (Burnt Orange)
Secondary: #FFA500  (Orange)
Accent:    #FF9E4D  (Light Orange)
Dark:      #E67E22  (Pumpkin)
Glow:      #FFB366  (Soft Orange)
```

### Usage
- **Hub bubble:** Orange gradient with vibrant glow
- **Headers:** Burnt orange to bright orange gradient
- **Buttons:** Orange backgrounds with pumpkin borders
- **Accents:** Orange borders and glows
- **Transform controls:** Orange highlight states
- **Grid/axes:** Orange accent colors

### Why Orange?
Energetic and technical. Orange represents precision, engineering, and creative problem-solving. Associated with CAD/engineering tools.

---

## 🕵️ People Finder - RED

### Color Codes
```css
Primary:   #E74C3C  (Crimson)
Secondary: #DC3545  (Red)
Accent:    #FF6B6B  (Coral Red)
Dark:      #C0392B  (Dark Red)
Glow:      #FF8A80  (Light Red)
```

### Usage
- **Hub bubble:** Red gradient with strong glow
- **Headers:** Crimson to red gradient
- **Buttons:** Red backgrounds with dark red borders
- **Accents:** Red borders and glows
- **Status indicators:** Red for search/action states
- **Form highlights:** Coral red accents

### Why Red?
Bold and attention-grabbing. Red represents investigation, urgency, and important information. Perfect for a search/detective tool.

---

## 📐 Implementation Details

### Hub (Landing Page)
**File:** `templates/hub.html`

Each mode bubble uses a specific class:
- `mode-cream` - Cookie Cutter
- `mode-orange` - Parametric CAD
- `mode-red` - People Finder

CSS gradients, borders, and glow effects are color-coded accordingly.

### Individual Tool Pages

#### Cookie Cutter (`templates/cookie_cutter.html`)
- [ ] TODO: Update header gradient to cream
- [ ] TODO: Update button colors to cream
- [ ] TODO: Update border accents to cream
- [ ] TODO: Update 3D viewer grid to cream

#### Parametric CAD (`templates/parametric_cad.html`)
- [x] Headers use blue (to be updated to orange)
- [x] Transform controls present
- [ ] TODO: Update to orange theme
- [ ] TODO: Update grid/axes to orange
- [ ] TODO: Update buttons to orange

#### People Finder (`templates/people_finder.html`)
- [x] Currently uses blue gradient (to be updated to red)
- [ ] TODO: Update background gradient to red
- [ ] TODO: Update button colors to red
- [ ] TODO: Update form accents to red

---

## 🎯 Color Psychology

### Cream (Cookie Cutter)
- **Feeling:** Warm, approachable, creative
- **Association:** Baking, crafts, hobbies
- **User emotion:** Fun, playful, experimental

### Orange (Parametric CAD)
- **Feeling:** Energetic, precise, technical
- **Association:** Engineering, construction, tools
- **User emotion:** Focused, professional, innovative

### Red (People Finder)
- **Feeling:** Bold, urgent, investigative
- **Association:** Search, discovery, investigation
- **User emotion:** Alert, curious, determined

---

## 🔄 Future Tools

When adding new tools to ZoolZ, choose colors that:
1. Don't clash with existing cream/orange/red
2. Have strong visual identity
3. Match the tool's purpose/personality

Suggested future colors:
- **Green** - For organic/nature-related tools
- **Purple** - For AI/mystical/advanced features
- **Blue** - For data/analytics tools
- **Yellow** - For productivity/utility tools

---

## 📝 Implementation Checklist

### Completed ✅
- [x] Hub color scheme implemented
- [x] Documentation created
- [x] Junk files cleaned
- [x] Project analysis completed

### Pending 📌
- [ ] Cookie Cutter template colors
- [ ] Parametric CAD template colors
- [ ] People Finder template colors
- [ ] Test all color schemes
- [ ] Screenshot gallery in docs

---

## 🎨 Color Reference Card

Quick reference for developers:

```css
/* Cookie Cutter - CREAM */
--cream-primary: #F5DEB3;
--cream-hover: #FFE4B5;
--cream-glow: rgba(245, 222, 179, 0.6);

/* Parametric CAD - ORANGE */
--orange-primary: #FF8C42;
--orange-hover: #FFA500;
--orange-glow: rgba(255, 140, 66, 0.6);

/* People Finder - RED */
--red-primary: #E74C3C;
--red-hover: #FF6B6B;
--red-glow: rgba(231, 76, 60, 0.6);
```

---

This color scheme creates a **cohesive yet distinctive** visual identity for each ZoolZ tool! 🎨✨
