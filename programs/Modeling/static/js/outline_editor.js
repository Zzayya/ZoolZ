// ============================================================================
// OUTLINE EDITOR - Interactive canvas for editing outlines
// ============================================================================

let outlineEditorVisible = false;
let currentOutlineData = null;
let currentDetailData = null;
let canvas = null;
let ctx = null;
let selectedPointIndex = -1;
let isDragging = false;
let canvasScale = 1.0;
let canvasOffset = { x: 0, y: 0 };
let isEnlargedView = false;

// Initialize outline editor
function initOutlineEditor() {
    canvas = document.getElementById('outlineCanvas');
    if (!canvas) {
        console.error('Outline canvas not found');
        return;
    }

    ctx = canvas.getContext('2d');

    // Mouse events for dragging points
    canvas.addEventListener('mousedown', handleCanvasMouseDown);
    canvas.addEventListener('mousemove', handleCanvasMouseMove);
    canvas.addEventListener('mouseup', handleCanvasMouseUp);
    canvas.addEventListener('mouseleave', handleCanvasMouseUp);

    console.log('Outline editor initialized');
}

// Show outline editor with data
function showOutlineEditor(outlineData) {
    currentOutlineData = outlineData;
    outlineEditorVisible = true;

    const panel = document.getElementById('outlineEditorPanel');
    if (panel) {
        panel.classList.add('visible');
        resizeCanvas();
        drawOutline();
    }
}

// Close outline editor
function closeOutlineEditor() {
    outlineEditorVisible = false;
    const panel = document.getElementById('outlineEditorPanel');
    if (panel) {
        panel.classList.remove('visible');
    }
    currentOutlineData = null;
    selectedPointIndex = -1;
}

// Toggle enlarged view
function toggleEnlargedView() {
    isEnlargedView = !isEnlargedView;
    const panel = document.getElementById('outlineEditorPanel');

    if (isEnlargedView) {
        panel.classList.add('enlarged');
    } else {
        panel.classList.remove('enlarged');
    }

    resizeCanvas();
    drawOutline();
}

// Resize canvas to fit container
function resizeCanvas() {
    if (!canvas || !currentOutlineData) return;

    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    // Calculate scale to fit outline in canvas
    const outline = currentOutlineData.outline;
    if (!outline || outline.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    outline.forEach(([x, y]) => {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
    });

    const outlineWidth = maxX - minX;
    const outlineHeight = maxY - minY;

    const padding = 40;
    const scaleX = (canvas.width - padding * 2) / outlineWidth;
    const scaleY = (canvas.height - padding * 2) / outlineHeight;
    canvasScale = Math.min(scaleX, scaleY);

    canvasOffset.x = (canvas.width - outlineWidth * canvasScale) / 2 - minX * canvasScale;
    canvasOffset.y = (canvas.height - outlineHeight * canvasScale) / 2 - minY * canvasScale;
}

// Draw outline on canvas
function drawOutline() {
    if (!ctx || !currentOutlineData) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    drawGrid();

    const outline = currentOutlineData.outline;
    if (!outline || outline.length === 0) return;

    // Draw outline shape
    ctx.strokeStyle = 'rgba(0, 149, 255, 0.8)';
    ctx.fillStyle = 'rgba(0, 149, 255, 0.15)';
    ctx.lineWidth = 2;

    ctx.beginPath();
    outline.forEach(([x, y], i) => {
        const canvasX = x * canvasScale + canvasOffset.x;
        const canvasY = y * canvasScale + canvasOffset.y;

        if (i === 0) {
            ctx.moveTo(canvasX, canvasY);
        } else {
            ctx.lineTo(canvasX, canvasY);
        }
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw control points
    outline.forEach(([x, y], i) => {
        const canvasX = x * canvasScale + canvasOffset.x;
        const canvasY = y * canvasScale + canvasOffset.y;

        const isSelected = i === selectedPointIndex;
        const radius = isSelected ? 6 : 4;

        ctx.fillStyle = isSelected ? 'rgba(255, 100, 0, 0.9)' : 'rgba(0, 149, 255, 0.9)';
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, radius, 0, Math.PI * 2);
        ctx.fill();

        // Draw border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 1;
        ctx.stroke();
    });

    // Draw point count
    ctx.fillStyle = 'rgba(0, 149, 255, 0.8)';
    ctx.font = '12px monospace';
    ctx.fillText(`Points: ${outline.length}`, 10, 20);
}

// Draw grid
function drawGrid() {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;

    const gridSize = 50 * canvasScale;

    // Vertical lines
    for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
}

// Handle mouse down on canvas
function handleCanvasMouseDown(e) {
    if (!currentOutlineData) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Find nearest point
    const outline = currentOutlineData.outline;
    let nearestIndex = -1;
    let nearestDist = Infinity;

    outline.forEach(([x, y], i) => {
        const canvasX = x * canvasScale + canvasOffset.x;
        const canvasY = y * canvasScale + canvasOffset.y;

        const dist = Math.sqrt((mouseX - canvasX) ** 2 + (mouseY - canvasY) ** 2);
        if (dist < nearestDist && dist < 10) {  // 10px threshold
            nearestDist = dist;
            nearestIndex = i;
        }
    });

    if (nearestIndex !== -1) {
        selectedPointIndex = nearestIndex;
        isDragging = true;
        canvas.style.cursor = 'grabbing';
        drawOutline();
    }
}

// Handle mouse move on canvas
function handleCanvasMouseMove(e) {
    if (!currentOutlineData) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (isDragging && selectedPointIndex !== -1) {
        // Update point position
        const outlineX = (mouseX - canvasOffset.x) / canvasScale;
        const outlineY = (mouseY - canvasOffset.y) / canvasScale;

        currentOutlineData.outline[selectedPointIndex] = [outlineX, outlineY];
        drawOutline();
    } else {
        // Update cursor based on proximity to points
        const outline = currentOutlineData.outline;
        let nearPoint = false;

        for (let i = 0; i < outline.length; i++) {
            const [x, y] = outline[i];
            const canvasX = x * canvasScale + canvasOffset.x;
            const canvasY = y * canvasScale + canvasOffset.y;

            const dist = Math.sqrt((mouseX - canvasX) ** 2 + (mouseY - canvasY) ** 2);
            if (dist < 10) {
                nearPoint = true;
                break;
            }
        }

        canvas.style.cursor = nearPoint ? 'grab' : 'default';
    }
}

// Handle mouse up on canvas
function handleCanvasMouseUp() {
    isDragging = false;
    selectedPointIndex = -1;
    canvas.style.cursor = 'default';
    drawOutline();
}

// Extract outline from uploaded image
async function extractOutline(file, detailLevel = 0.5) {
    try {
        showNotification('Extracting outline...', 'processing');

        const formData = new FormData();
        formData.append('image', file);
        formData.append('detail_level', detailLevel);

        const response = await fetch('/modeling/api/extract_outline', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Outline extracted: ${data.outline.point_count} points`, 'success');
            showOutlineEditor(data.outline);
            return data.outline;
        } else {
            showNotification(`Error: ${data.error}`, 'error');
            return null;
        }
    } catch (error) {
        showNotification(`Extraction failed: ${error.message}`, 'error');
        return null;
    }
}

// Extract inner details from uploaded image
async function extractDetails(file, precision = 0.5) {
    try {
        showNotification('Extracting inner details...', 'processing');

        const formData = new FormData();
        formData.append('image', file);
        formData.append('precision', precision);

        const response = await fetch('/modeling/api/extract_details', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentDetailData = data.details;
            showNotification(`Found ${data.details.detail_count} inner details`, 'success');
            // TODO: Show details in a separate view
            return data.details;
        } else {
            showNotification(`Error: ${data.error}`, 'error');
            return null;
        }
    } catch (error) {
        showNotification(`Detail extraction failed: ${error.message}`, 'error');
        return null;
    }
}

// Generate cookie cutter from edited outline
async function generateFromOutline() {
    if (!currentOutlineData) {
        showNotification('No outline data available', 'error');
        return;
    }

    try {
        showNotification('Generating cookie cutter...', 'processing');

        // Get parameters from UI
        const params = {
            blade_thick: parseFloat(document.getElementById('bladeThick')?.value || 2.0),
            blade_height: parseFloat(document.getElementById('bladeHeight')?.value || 20.0),
            base_thick: parseFloat(document.getElementById('baseThick')?.value || 3.0),
            base_extra: parseFloat(document.getElementById('baseExtra')?.value || 10.0),
            max_dim: parseFloat(document.getElementById('maxDim')?.value || 90.0),
            no_base: document.getElementById('noBase')?.checked || false
        };

        const response = await fetch('/modeling/api/generate_from_outline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                outline_data: currentOutlineData,
                params: params
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Cookie cutter generated!', 'success');

            // Load the generated STL into the scene
            const stlUrl = data.download_url;
            loadSTL(stlUrl);

            // Add to scene manager
            if (typeof addObjectToScene === 'function') {
                addObjectToScene('Cookie Cutter', stlUrl);
            }
        } else {
            showNotification(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Generation failed: ${error.message}`, 'error');
    }
}

// Generate detail stamp
async function generateDetailStamp() {
    if (!currentDetailData) {
        showNotification('No detail data available', 'error');
        return;
    }

    try {
        showNotification('Generating detail stamp...', 'processing');

        const params = {
            stamp_depth: 2.0,
            stamp_height: 3.0,
            max_dim: parseFloat(document.getElementById('maxDim')?.value || 90.0)
        };

        const response = await fetch('/modeling/api/generate_detail_stamp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                detail_data: currentDetailData,
                params: params
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Detail stamp generated!', 'success');

            // Load the generated STL into the scene
            const stlUrl = data.download_url;
            loadSTL(stlUrl);

            // Add to scene manager
            if (typeof addObjectToScene === 'function') {
                addObjectToScene('Detail Stamp', stlUrl);
            }
        } else {
            showNotification(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Stamp generation failed: ${error.message}`, 'error');
    }
}

// Initialize on load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        initOutlineEditor();
    });
}
