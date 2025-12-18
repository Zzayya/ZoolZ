// ============================================================================
// OUTLINE EDITOR V2 - Persistent floating window with advanced editing
// ============================================================================

class OutlineEditorV2 {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.points = [];
        this.originalPoints = [];
        this.width = 0;
        this.height = 0;
        this.imageData = null;
        this.outlineType = 'outer'; // 'outer' or 'inner'
        this.detailContours = []; // For inner details

        // Interaction state
        this.draggedPointIndex = -1;
        this.draggedLineIndex = -1;
        this.hoveredPointIndex = -1;
        this.hoveredLineIndex = -1;
        this.isDragging = false;
        this.panOffset = { x: 0, y: 0 };
        this.zoom = 1.0;

        // Undo/Redo
        this.undoStack = [];
        this.redoStack = [];

        // Settings
        this.pointRadius = 6;
        this.lineWidth = 2;
        this.hitRadius = 12; // Click detection radius

        this.window = null;
        this.isOpen = false;
    }

    // Open outline editor with extracted outline data
    open(outlineData, imageDataUrl = null) {
        if (!outlineData) {
            console.error('No outline data provided');
            return;
        }

        // Store data
        this.points = JSON.parse(JSON.stringify(outlineData.outline));
        this.originalPoints = JSON.parse(JSON.stringify(outlineData.outline));
        this.width = outlineData.width || 800;
        this.height = outlineData.height || 600;
        this.outlineType = outlineData.type || 'outer';
        this.imageData = imageDataUrl;

        // Reset undo/redo
        this.undoStack = [];
        this.redoStack = [];

        // Create window if doesn't exist
        if (!this.window) {
            this.createWindow();
        } else {
            this.window.show();
        }

        this.isOpen = true;

        // Initialize canvas
        setTimeout(() => {
            this.initCanvas();
            this.render();
        }, 100);

        console.log(`📐 Outline editor opened with ${this.points.length} points`);
    }

    createWindow() {
        const content = `
            <div style="display: flex; flex-direction: column; height: 100%; gap: 10px;">
                <!-- Toolbar -->
                <div style="display: flex; gap: 8px; flex-wrap: wrap; padding-bottom: 10px; border-bottom: 1px solid rgba(0, 149, 255, 0.2);">
                    <button class="tool-btn" onclick="outlineEditorV2.undo()" id="outlineUndoBtn" disabled>
                        ↶ Undo
                    </button>
                    <button class="tool-btn" onclick="outlineEditorV2.redo()" id="outlineRedoBtn" disabled>
                        ↷ Redo
                    </button>
                    <button class="tool-btn" onclick="outlineEditorV2.reset()">
                        ⟲ Reset
                    </button>
                    <button class="tool-btn" onclick="outlineEditorV2.smooth()">
                        〜 Smooth
                    </button>
                    <button class="tool-btn" onclick="outlineEditorV2.simplify()">
                        ◇ Simplify
                    </button>
                    <button class="tool-btn" onclick="outlineEditorV2.fitView()">
                        🔍 Fit
                    </button>
                </div>

                <!-- Canvas Container -->
                <div style="flex: 1; background: rgba(0, 0, 0, 0.3); border-radius: 8px; overflow: hidden; position: relative;">
                    <canvas id="outlineEditorCanvas" style="width: 100%; height: 100%; cursor: crosshair;"></canvas>
                </div>

                <!-- Info Bar -->
                <div style="padding: 8px 12px; background: rgba(0, 149, 255, 0.05); border-radius: 6px; font-size: 12px; color: #8ab4f8;">
                    <span id="outlinePointCount">0 points</span> •
                    <span id="outlineHoverInfo">Drag points or lines to adjust</span>
                </div>

                <!-- Action Buttons -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button class="btn-primary" onclick="outlineEditorV2.generateCookieCutter()">
                        🍪 Cookie Cutter
                    </button>
                    <button class="btn-primary" onclick="outlineEditorV2.generateStamp()">
                        🎫 Stamp
                    </button>
                </div>

                <style>
                    .tool-btn {
                        padding: 6px 12px;
                        background: rgba(0, 149, 255, 0.1);
                        border: 1px solid rgba(0, 149, 255, 0.3);
                        border-radius: 5px;
                        color: #0095ff;
                        font-size: 12px;
                        cursor: pointer;
                        transition: all 0.2s;
                    }
                    .tool-btn:hover:not(:disabled) {
                        background: rgba(0, 149, 255, 0.25);
                        border-color: #0095ff;
                    }
                    .tool-btn:disabled {
                        opacity: 0.3;
                        cursor: not-allowed;
                    }
                </style>
            </div>
        `;

        this.window = windowManager.create(
            'outline-editor-v2',
            '✏️ Outline Editor',
            content,
            {
                width: 700,
                height: 600,
                x: window.innerWidth / 2 - 350,
                y: 100,
                persistent: true,
                minimizable: true,
                closable: false // Keep open always
            }
        );
    }

    initCanvas() {
        this.canvas = document.getElementById('outlineEditorCanvas');
        if (!this.canvas) {
            console.error('Canvas not found');
            return;
        }

        // Set canvas size with HiDPI support
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx = this.canvas.getContext('2d');
        this.ctx.scale(dpr, dpr);

        // Setup event listeners
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('dblclick', (e) => this.onDoubleClick(e));
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e));

        // Right-click to delete point
        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.onRightClick(e);
        });

        // Fit view initially
        this.fitView();
    }

    render() {
        if (!this.ctx) return;

        const rect = this.canvas.getBoundingClientRect();
        this.ctx.clearRect(0, 0, rect.width, rect.height);


        // Transform for zoom/pan
        this.ctx.save();
        this.ctx.translate(this.panOffset.x, this.panOffset.y);
        this.ctx.scale(this.zoom, this.zoom);

        // Draw outline
        if (this.points.length > 0) {
            // Draw lines
            this.ctx.strokeStyle = '#0095ff';
            this.ctx.lineWidth = this.lineWidth;
            this.ctx.beginPath();
            this.ctx.moveTo(this.points[0][0], this.points[0][1]);
            for (let i = 1; i < this.points.length; i++) {
                this.ctx.lineTo(this.points[i][0], this.points[i][1]);
            }
            this.ctx.closePath();
            this.ctx.stroke();

            // Highlight hovered line
            if (this.hoveredLineIndex >= 0) {
                const i = this.hoveredLineIndex;
                const j = (i + 1) % this.points.length;
                this.ctx.strokeStyle = '#ffaa00';
                this.ctx.lineWidth = this.lineWidth * 2;
                this.ctx.beginPath();
                this.ctx.moveTo(this.points[i][0], this.points[i][1]);
                this.ctx.lineTo(this.points[j][0], this.points[j][1]);
                this.ctx.stroke();
            }

            // Draw points
            this.points.forEach((point, i) => {
                const isHovered = i === this.hoveredPointIndex;
                const isDragged = i === this.draggedPointIndex;

                this.ctx.fillStyle = isDragged ? '#ff0000' : (isHovered ? '#ffaa00' : '#00ff00');
                this.ctx.beginPath();
                this.ctx.arc(point[0], point[1], this.pointRadius, 0, Math.PI * 2);
                this.ctx.fill();

                // Outline
                this.ctx.strokeStyle = '#000';
                this.ctx.lineWidth = 1;
                this.ctx.stroke();
            });
        }

        this.ctx.restore();

        // Update info
        document.getElementById('outlinePointCount').textContent = `${this.points.length} points`;
    }

    // Mouse event handlers
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left - this.panOffset.x) / this.zoom,
            y: (e.clientY - rect.top - this.panOffset.y) / this.zoom
        };
    }

    onMouseDown(e) {
        const pos = this.getMousePos(e);

        // Check if clicking on point
        for (let i = 0; i < this.points.length; i++) {
            const dx = pos.x - this.points[i][0];
            const dy = pos.y - this.points[i][1];
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < this.hitRadius / this.zoom) {
                this.draggedPointIndex = i;
                this.isDragging = true;
                this.pushUndo();
                return;
            }
        }

        // Check if clicking on line
        for (let i = 0; i < this.points.length; i++) {
            const j = (i + 1) % this.points.length;
            const dist = this.distanceToSegment(pos, this.points[i], this.points[j]);

            if (dist < this.hitRadius / this.zoom) {
                this.draggedLineIndex = i;
                this.isDragging = true;
                this.pushUndo();
                return;
            }
        }
    }

    onMouseMove(e) {
        const pos = this.getMousePos(e);

        if (this.isDragging) {
            if (this.draggedPointIndex >= 0) {
                // Drag point
                this.points[this.draggedPointIndex] = [pos.x, pos.y];
                this.render();
            } else if (this.draggedLineIndex >= 0) {
                // Drag line (move both endpoints)
                const i = this.draggedLineIndex;
                const j = (i + 1) % this.points.length;

                // Calculate offset from last position
                if (!this.lastDragPos) {
                    this.lastDragPos = pos;
                }

                const dx = pos.x - this.lastDragPos.x;
                const dy = pos.y - this.lastDragPos.y;

                this.points[i][0] += dx;
                this.points[i][1] += dy;
                this.points[j][0] += dx;
                this.points[j][1] += dy;

                this.lastDragPos = pos;
                this.render();
            }
        } else {
            // Update hover state
            this.hoveredPointIndex = -1;
            this.hoveredLineIndex = -1;

            // Check point hover
            for (let i = 0; i < this.points.length; i++) {
                const dx = pos.x - this.points[i][0];
                const dy = pos.y - this.points[i][1];
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < this.hitRadius / this.zoom) {
                    this.hoveredPointIndex = i;
                    this.canvas.style.cursor = 'move';
                    this.render();
                    return;
                }
            }

            // Check line hover
            for (let i = 0; i < this.points.length; i++) {
                const j = (i + 1) % this.points.length;
                const dist = this.distanceToSegment(pos, this.points[i], this.points[j]);

                if (dist < this.hitRadius / this.zoom) {
                    this.hoveredLineIndex = i;
                    this.canvas.style.cursor = 'move';
                    this.render();
                    return;
                }
            }

            this.canvas.style.cursor = 'crosshair';
            this.render();
        }
    }

    onMouseUp(e) {
        this.isDragging = false;
        this.draggedPointIndex = -1;
        this.draggedLineIndex = -1;
        this.lastDragPos = null;
    }

    onDoubleClick(e) {
        // Add point on line
        const pos = this.getMousePos(e);

        for (let i = 0; i < this.points.length; i++) {
            const j = (i + 1) % this.points.length;
            const dist = this.distanceToSegment(pos, this.points[i], this.points[j]);

            if (dist < this.hitRadius / this.zoom) {
                this.pushUndo();
                this.points.splice(j, 0, [pos.x, pos.y]);
                this.render();
                return;
            }
        }
    }

    onRightClick(e) {
        // Delete point
        const pos = this.getMousePos(e);

        for (let i = 0; i < this.points.length; i++) {
            const dx = pos.x - this.points[i][0];
            const dy = pos.y - this.points[i][1];
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < this.hitRadius / this.zoom) {
                if (this.points.length > 3) { // Keep at least 3 points
                    this.pushUndo();
                    this.points.splice(i, 1);
                    this.render();
                }
                return;
            }
        }
    }

    onWheel(e) {
        e.preventDefault();
        // Zoom
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoom *= delta;
        this.zoom = Math.max(0.1, Math.min(5, this.zoom));
        this.render();
    }

    // Utility: Distance from point to line segment
    distanceToSegment(p, a, b) {
        const dx = b[0] - a[0];
        const dy = b[1] - a[1];
        const len2 = dx * dx + dy * dy;

        if (len2 === 0) return Math.sqrt((p.x - a[0]) ** 2 + (p.y - a[1]) ** 2);

        const t = Math.max(0, Math.min(1, ((p.x - a[0]) * dx + (p.y - a[1]) * dy) / len2));
        const projX = a[0] + t * dx;
        const projY = a[1] + t * dy;

        return Math.sqrt((p.x - projX) ** 2 + (p.y - projY) ** 2);
    }

    // Undo/Redo
    pushUndo() {
        this.undoStack.push(JSON.parse(JSON.stringify(this.points)));
        this.redoStack = [];
        this.updateUndoRedoButtons();
    }

    undo() {
        if (this.undoStack.length === 0) return;

        this.redoStack.push(JSON.parse(JSON.stringify(this.points)));
        this.points = this.undoStack.pop();
        this.render();
        this.updateUndoRedoButtons();
    }

    redo() {
        if (this.redoStack.length === 0) return;

        this.undoStack.push(JSON.parse(JSON.stringify(this.points)));
        this.points = this.redoStack.pop();
        this.render();
        this.updateUndoRedoButtons();
    }

    updateUndoRedoButtons() {
        const undoBtn = document.getElementById('outlineUndoBtn');
        const redoBtn = document.getElementById('outlineRedoBtn');
        if (undoBtn) undoBtn.disabled = this.undoStack.length === 0;
        if (redoBtn) redoBtn.disabled = this.redoStack.length === 0;
    }

    // Tools
    reset() {
        if (confirm('Reset outline to original?')) {
            this.pushUndo();
            this.points = JSON.parse(JSON.stringify(this.originalPoints));
            this.render();
        }
    }

    smooth() {
        // Simple smoothing algorithm
        this.pushUndo();
        const smoothed = [];

        for (let i = 0; i < this.points.length; i++) {
            const prev = this.points[(i - 1 + this.points.length) % this.points.length];
            const curr = this.points[i];
            const next = this.points[(i + 1) % this.points.length];

            const x = (prev[0] + curr[0] * 2 + next[0]) / 4;
            const y = (prev[1] + curr[1] * 2 + next[1]) / 4;

            smoothed.push([x, y]);
        }

        this.points = smoothed;
        this.render();
    }

    simplify() {
        // Douglas-Peucker simplification
        const epsilon = 5 / this.zoom; // Adjust tolerance
        this.pushUndo();
        this.points = this.douglasPeucker(this.points, epsilon);
        this.render();
    }

    douglasPeucker(points, epsilon) {
        if (points.length < 3) return points;

        // Find point with max distance
        let maxDist = 0;
        let maxIndex = 0;

        for (let i = 1; i < points.length - 1; i++) {
            const dist = this.distanceToSegment(
                { x: points[i][0], y: points[i][1] },
                points[0],
                points[points.length - 1]
            );

            if (dist > maxDist) {
                maxDist = dist;
                maxIndex = i;
            }
        }

        if (maxDist > epsilon) {
            const left = this.douglasPeucker(points.slice(0, maxIndex + 1), epsilon);
            const right = this.douglasPeucker(points.slice(maxIndex), epsilon);
            return left.slice(0, -1).concat(right);
        } else {
            return [points[0], points[points.length - 1]];
        }
    }

    fitView() {
        if (this.points.length === 0) return;

        // Calculate bounds
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;

        this.points.forEach(p => {
            minX = Math.min(minX, p[0]);
            minY = Math.min(minY, p[1]);
            maxX = Math.max(maxX, p[0]);
            maxY = Math.max(maxY, p[1]);
        });

        const rect = this.canvas.getBoundingClientRect();
        const padding = 50;
        const scaleX = (rect.width - padding * 2) / (maxX - minX);
        const scaleY = (rect.height - padding * 2) / (maxY - minY);

        this.zoom = Math.min(scaleX, scaleY);
        this.panOffset.x = padding - minX * this.zoom;
        this.panOffset.y = padding - minY * this.zoom;

        this.render();
    }

    // Generate functions
    async generateCookieCutter() {
        if (!this.window || !windowManager.has('tool-cookie')) {
            // Open cookie cutter settings if not open
            openToolWindow('cookie');
        }

        // Get cookie cutter settings
        const settings = {
            blade_thick: parseFloat(document.getElementById('bladeThick')?.value || 2.0),
            blade_height: parseFloat(document.getElementById('bladeHeight')?.value || 20.0),
            base_thick: parseFloat(document.getElementById('baseThick')?.value || 3.0),
            base_extra: parseFloat(document.getElementById('baseExtra')?.value || 10.0),
            max_dim: parseFloat(document.getElementById('maxDim')?.value || 90.0),
            no_base: document.getElementById('noBase')?.checked || false
        };

        showNotification('Generating cookie cutter from edited outline...', 'processing');

        try {
            const response = await fetch('/modeling/api/generate_from_outline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    outline_data: {
                        outline: this.points,
                        width: this.width,
                        height: this.height,
                        type: this.outlineType
                    },
                    params: settings
                })
            });

            const data = await response.json();

            if (data.success) {
                showNotification('Cookie cutter generated!', 'success');
                loadSTL(data.download_url);

                if (typeof addObjectToScene === 'function') {
                    addObjectToScene('Cookie Cutter (Edited)', data.download_url);
                }
            } else {
                showNotification('Error: ' + data.error, 'error');
            }
        } catch (error) {
            showNotification('Generation failed: ' + error.message, 'error');
        }
    }

    async generateStamp() {
    async generateStamp() {
        if (this.points.length < 3) {
            showNotification('Need at least 3 points for stamp', 'error');
            return;
        }

        // Open stamp tool if not open
        if (!windowManager.has('tool-stamp')) {
            openToolWindow('stamp');
        }

        try {
            // Send outline data to stamp generation endpoint
            const response = await fetch('/modeling/api/generate_stamp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    outline_data: this.getOutlineData(),
                    params: {
                        stamp_type: 'positive',  // Default positive stamp
                        detail_level: 0.5,
                        edge_profile: 'sharp',
                        base_thickness: 5.0,
                        detail_height: 2.0,
                        max_dimension: 80.0
                    }
                })
            });

            const result = await response.json();

            if (result.error) {
                showNotification('Stamp generation failed: ' + result.error, 'error');
            } else {
                showNotification('Stamp generated successfully!', 'success');
                // Load generated stamp into scene
                if (result.download_url && window.sceneManager) {
                    window.sceneManager.loadSTL(result.download_url);
                }
            }
        } catch (error) {
            showNotification('Stamp generation failed: ' + error.message, 'error');
        }
    }
    // Get current outline data
    getOutlineData() {
        return {
            outline: this.points,
            width: this.width,
            height: this.height,
            type: this.outlineType,
            point_count: this.points.length
        };
    }
}

// Global instance
const outlineEditorV2 = new OutlineEditorV2();

// Hook into old extract outline function
const originalExtractOutline = window.extractOutlineFromImage;
window.extractOutlineFromImage = async function() {
    if (!currentFile) {
        showNotification('Please upload an image first', 'error');
        return;
    }

    showNotification('Extracting outline...', 'processing');

    const formData = new FormData();
    formData.append('image', currentFile);

    try {
        const response = await fetch('/modeling/api/extract_outline', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Outline extracted (${data.outline.point_count} points)`, 'success');

            // Open persistent editor
            outlineEditorV2.open(data.outline);
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Extraction failed: ' + error.message, 'error');
    }
};
