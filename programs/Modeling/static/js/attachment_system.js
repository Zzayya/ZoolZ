// ============================================================================
// ATTACHMENT SYSTEM - Click object, add features (clips, threads, holes, etc.)
// ============================================================================

// Attachment mode state
let attachmentMode = {
    active: false,
    type: null,  // 'snap_clip', 'thread', 'mounting_holes', etc.
    selectedObject: null,
    selectedEdge: null,
    measurements: {}
};

// ============================================================================
// ATTACHMENT MODE ACTIVATION
// ============================================================================

function enterAttachmentMode(attachmentType) {
    /**
     * Enter attachment mode - user will select object, then feature location
     *
     * @param {string} attachmentType - Type of attachment ('snap_clip', 'thread', etc.)
     */
    attachmentMode.active = true;
    attachmentMode.type = attachmentType;
    attachmentMode.selectedObject = null;
    attachmentMode.selectedEdge = null;

    // Update UI
    showNotification(`Attachment Mode: ${getAttachmentLabel(attachmentType)}`, 'info');
    showAttachmentInstructions(attachmentType);

    // Change cursor
    document.body.style.cursor = 'crosshair';

    // Enable click detection on scene objects
    enableAttachmentSelection();
}

function exitAttachmentMode() {
    /**
     * Exit attachment mode and return to normal
     */
    attachmentMode.active = false;
    attachmentMode.type = null;
    attachmentMode.selectedObject = null;
    attachmentMode.selectedEdge = null;

    document.body.style.cursor = 'default';
    hideAttachmentInstructions();
    disableAttachmentSelection();

    showNotification('Attachment mode cancelled', 'info');
}

function getAttachmentLabel(type) {
    const labels = {
        'snap_clip': 'Add Snap Clip',
        'thread_510': 'Add 510 Thread',
        'mounting_holes': 'Add Mounting Holes',
        'drainage_holes': 'Add Drainage Holes',
        'handle': 'Add Handle',
        'feet': 'Add Feet',
        'text_label': 'Add Text Label'
    };
    return labels[type] || 'Add Attachment';
}

// ============================================================================
// UI HELPERS
// ============================================================================

function showAttachmentInstructions(type) {
    const instructions = getInstructionsForType(type);

    const instructionDiv = document.createElement('div');
    instructionDiv.id = 'attachment-instructions';
    instructionDiv.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 149, 255, 0.95);
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        box-shadow: 0 4px 20px rgba(0, 149, 255, 0.5);
        animation: slideDown 0.3s ease;
    `;
    instructionDiv.innerHTML = `
        <div style="margin-bottom: 8px;">${instructions.step1}</div>
        <div style="font-size: 11px; opacity: 0.9;">Press ESC to cancel</div>
    `;

    document.body.appendChild(instructionDiv);

    // Add CSS animation
    if (!document.getElementById('attachment-animation-style')) {
        const style = document.createElement('style');
        style.id = 'attachment-animation-style';
        style.textContent = `
            @keyframes slideDown {
                from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
}

function hideAttachmentInstructions() {
    const instructionDiv = document.getElementById('attachment-instructions');
    if (instructionDiv) {
        instructionDiv.remove();
    }
}

function updateAttachmentInstructions(newText) {
    const instructionDiv = document.getElementById('attachment-instructions');
    if (instructionDiv) {
        instructionDiv.querySelector('div').textContent = newText;
    }
}

function getInstructionsForType(type) {
    const instructions = {
        'snap_clip': {
            step1: '1. Click on an EDGE of your object',
            step2: '2. Adjust clip size if needed'
        },
        'thread_510': {
            step1: '1. Click on a CYLINDER surface',
            step2: '2. Choose male or female thread'
        },
        'mounting_holes': {
            step1: '1. Click on a FLAT SURFACE',
            step2: '2. Configure hole pattern'
        },
        'drainage_holes': {
            step1: '1. Click on the BOTTOM SURFACE',
            step2: '2. Configure hole size and spacing'
        },
        'handle': {
            step1: '1. Click on the SIDE of your object',
            step2: '2. Adjust handle size'
        }
    };

    return instructions[type] || {
        step1: '1. Click on your object',
        step2: '2. Configure attachment'
    };
}

// ============================================================================
// EDGE DETECTION SYSTEM
// ============================================================================

function enableAttachmentSelection() {
    /**
     * Enable raycasting to detect clicks on scene objects
     */
    if (typeof renderer === 'undefined' || typeof camera === 'undefined') {
        console.error('Three.js renderer/camera not available');
        return;
    }

    // Add click event listener to viewer
    const viewer = document.getElementById('viewer');
    if (viewer) {
        viewer.addEventListener('click', onAttachmentClick);
        viewer.addEventListener('mousemove', onAttachmentHover);
    }

    // ESC to cancel
    document.addEventListener('keydown', onAttachmentKeydown);
}

function disableAttachmentSelection() {
    const viewer = document.getElementById('viewer');
    if (viewer) {
        viewer.removeEventListener('click', onAttachmentClick);
        viewer.removeEventListener('mousemove', onAttachmentHover);
    }
    document.removeEventListener('keydown', onAttachmentKeydown);
}

function onAttachmentKeydown(event) {
    if (event.key === 'Escape' && attachmentMode.active) {
        exitAttachmentMode();
    }
}

function onAttachmentClick(event) {
    if (!attachmentMode.active) return;

    // Get click position in normalized device coordinates
    const rect = event.target.getBoundingClientRect();
    const mouse = new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
    );

    // Raycast to find intersected object
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);

    // Get all scene meshes
    const meshes = [];
    scene.traverse((child) => {
        if (child.isMesh && child.visible && child.name !== 'buildPlate' && child.name !== 'grid') {
            meshes.push(child);
        }
    });

    const intersects = raycaster.intersect(meshes);

    if (intersects.length > 0) {
        const intersection = intersects[0];

        if (!attachmentMode.selectedObject) {
            // First click - select the object
            handleObjectSelection(intersection);
        } else {
            // Second click - select the attachment point
            handleAttachmentPoint(intersection);
        }
    }
}

function onAttachmentHover(event) {
    if (!attachmentMode.active) return;

    // Show hover highlight on valid surfaces
    const rect = event.target.getBoundingClientRect();
    const mouse = new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);

    const meshes = [];
    scene.traverse((child) => {
        if (child.isMesh && child.visible && child.name !== 'buildPlate' && child.name !== 'grid') {
            meshes.push(child);
        }
    });

    const intersects = raycaster.intersect(meshes);

    // Update hover effect (you can add visual feedback here)
    if (intersects.length > 0) {
        document.body.style.cursor = 'pointer';
    } else {
        document.body.style.cursor = 'crosshair';
    }
}

function handleObjectSelection(intersection) {
    /**
     * User clicked on an object - select it for attachment
     */
    attachmentMode.selectedObject = intersection.object;

    // Highlight the selected object
    highlightObject(intersection.object, true);

    // Update instructions
    const instructions = getInstructionsForType(attachmentMode.type);
    updateAttachmentInstructions(instructions.step1 + ' ← Click edge/surface now');

    showNotification(`Object selected. Now ${instructions.step1.toLowerCase()}`, 'success');
}

function handleAttachmentPoint(intersection) {
    /**
     * User clicked on a point/edge/surface - detect geometry and show attachment options
     */
    const point = intersection.point;
    const face = intersection.face;
    const object = intersection.object;

    // Detect what was clicked based on attachment type
    if (attachmentMode.type === 'snap_clip') {
        detectAndMeasureEdge(point, face, object);
    } else if (attachmentMode.type === 'thread_510') {
        detectCylinderSurface(point, face, object);
    } else if (attachmentMode.type === 'mounting_holes') {
        detectFlatSurface(point, face, object);
    }
}

// ============================================================================
// GEOMETRY DETECTION
// ============================================================================

function detectAndMeasureEdge(point, face, object) {
    /**
     * Find the nearest edge to the clicked point and measure its length
     */
    const geometry = object.geometry;

    // Get vertices of the clicked face
    const vertices = [
        geometry.attributes.position.getX(face.a),
        geometry.attributes.position.getY(face.a),
        geometry.attributes.position.getZ(face.a),
        geometry.attributes.position.getX(face.b),
        geometry.attributes.position.getY(face.b),
        geometry.attributes.position.getZ(face.b),
        geometry.attributes.position.getX(face.c),
        geometry.attributes.position.getY(face.c),
        geometry.attributes.position.getZ(face.c)
    ];

    // Find closest edge to click point
    const v1 = new THREE.Vector3(vertices[0], vertices[1], vertices[2]);
    const v2 = new THREE.Vector3(vertices[3], vertices[4], vertices[5]);
    const v3 = new THREE.Vector3(vertices[6], vertices[7], vertices[8]);

    // Calculate edge lengths
    const edge1Length = v1.distanceTo(v2);
    const edge2Length = v2.distanceTo(v3);
    const edge3Length = v3.distanceTo(v1);

    // Find which edge is closest to click point
    const distances = [
        distanceToLineSegment(point, v1, v2),
        distanceToLineSegment(point, v2, v3),
        distanceToLineSegment(point, v3, v1)
    ];

    const closestEdgeIndex = distances.indexOf(Math.min(...distances));
    const edgeLengths = [edge1Length, edge2Length, edge3Length];
    const selectedEdgeLength = edgeLengths[closestEdgeIndex];

    // Store measurements
    attachmentMode.measurements = {
        edgeLength: selectedEdgeLength,
        edgeStart: closestEdgeIndex === 0 ? v1 : (closestEdgeIndex === 1 ? v2 : v3),
        edgeEnd: closestEdgeIndex === 0 ? v2 : (closestEdgeIndex === 1 ? v3 : v1),
        surfaceNormal: face.normal.clone()
    };

    // Show attachment popup with measurements
    showSnapClipAttachmentPopup(selectedEdgeLength);
}

function distanceToLineSegment(point, lineStart, lineEnd) {
    /**
     * Calculate distance from point to line segment
     */
    const line = new THREE.Line3(lineStart, lineEnd);
    const closestPoint = new THREE.Vector3();
    line.closestPointToPoint(point, true, closestPoint);
    return point.distanceTo(closestPoint);
}

function detectCylinderSurface(point, face, object) {
    /**
     * Detect if clicked surface is cylindrical and measure diameter
     */
    // For now, use bounding box to estimate diameter
    const bbox = new THREE.Box3().setFromObject(object);
    const size = bbox.getSize(new THREE.Vector3());

    // Assume cylinder - use smallest dimension as diameter
    const diameter = Math.min(size.x, size.z);

    attachmentMode.measurements = {
        diameter: diameter,
        height: size.y,
        position: point.clone(),
        normal: face.normal.clone()
    };

    showThreadAttachmentPopup(diameter);
}

function detectFlatSurface(point, face, object) {
    /**
     * Detect flat surface and measure area
     */
    const bbox = new THREE.Box3().setFromObject(object);
    const size = bbox.getSize(new THREE.Vector3());

    attachmentMode.measurements = {
        width: size.x,
        length: size.z,
        position: point.clone(),
        normal: face.normal.clone()
    };

    showMountingHolesAttachmentPopup(size.x, size.z);
}

// ============================================================================
// ATTACHMENT POPUPS
// ============================================================================

function showSnapClipAttachmentPopup(edgeLength) {
    /**
     * Show popup to configure snap clip for measured edge
     */
    const content = `
        <div class="tool-section">
            <h3>Snap Clip for ${edgeLength.toFixed(1)}mm Edge</h3>
            <p style="color: #8ab4f8; font-size: 0.9rem; margin-bottom: 15px;">
                Auto-sized to fit this edge. Adjust if needed:
            </p>

            <label>
                Clip Length (mm):
                <input type="number" id="attach_clip_length" value="${edgeLength.toFixed(1)}" step="1" min="10">
            </label>

            <label>
                Clip Width (mm):
                <input type="number" id="attach_clip_width" value="10.0" step="0.5" min="3">
            </label>

            <label>
                Thickness (mm):
                <input type="number" id="attach_clip_thickness" value="2.0" step="0.1" min="0.5">
            </label>

            <label>
                Clip Gap (mm):
                <input type="number" id="attach_clip_gap" value="3.0" step="0.5" min="1">
            </label>
        </div>

        <div class="tool-actions">
            <button class="btn" onclick="generateAndAttachClip()">Attach Clip</button>
            <button class="btn btn-secondary" onclick="cancelAttachment()">Cancel</button>
        </div>
    `;

    windowManager.create('attachment-config', 'Configure Snap Clip', content, {
        width: 400,
        persistent: true
    });
}

function showThreadAttachmentPopup(diameter) {
    const content = `
        <div class="tool-section">
            <h3>510 Thread for ${diameter.toFixed(1)}mm Cylinder</h3>

            <label>
                Thread Type:
                <select id="attach_thread_type" class="param-select">
                    <option value="male">Male (Pin)</option>
                    <option value="female">Female (Socket)</option>
                </select>
            </label>

            <label>
                Outer Diameter (mm):
                <input type="number" id="attach_thread_diameter" value="${diameter.toFixed(1)}" step="0.5">
            </label>

            <label>
                Thread Height (mm):
                <input type="number" id="attach_thread_height" value="15.0" step="1">
            </label>
        </div>

        <div class="tool-actions">
            <button class="btn" onclick="generateAndAttachThread()">Attach Thread</button>
            <button class="btn btn-secondary" onclick="cancelAttachment()">Cancel</button>
        </div>
    `;

    windowManager.create('attachment-config', 'Configure Thread', content, {
        width: 400,
        persistent: true
    });
}

function showMountingHolesAttachmentPopup(width, length) {
    const content = `
        <div class="tool-section">
            <h3>Mounting Holes for ${width.toFixed(1)}×${length.toFixed(1)}mm Surface</h3>

            <label>
                Hole Diameter (mm):
                <input type="number" id="attach_hole_diameter" value="3.0" step="0.5">
            </label>

            <label>
                Hole Spacing (mm):
                <input type="number" id="attach_hole_spacing" value="20.0" step="1">
            </label>

            <label>
                Pattern:
                <select id="attach_hole_pattern" class="param-select">
                    <option value="grid">Grid</option>
                    <option value="corners">4 Corners</option>
                    <option value="line">Line</option>
                </select>
            </label>
        </div>

        <div class="tool-actions">
            <button class="btn" onclick="generateAndAttachHoles()">Add Holes</button>
            <button class="btn btn-secondary" onclick="cancelAttachment()">Cancel</button>
        </div>
    `;

    windowManager.create('attachment-config', 'Configure Mounting Holes', content, {
        width: 400,
        persistent: true
    });
}

// ============================================================================
// ATTACHMENT GENERATION
// ============================================================================

async function generateAndAttachClip() {
    /**
     * Generate snap clip and boolean-union it to the selected object
     */
    const params = {
        length: parseFloat(document.getElementById('attach_clip_length').value),
        width: parseFloat(document.getElementById('attach_clip_width').value),
        thickness: parseFloat(document.getElementById('attach_clip_thickness').value),
        clip_gap: parseFloat(document.getElementById('attach_clip_gap').value),
        flex_length: 15.0
    };

    showNotification('Generating snap clip...', 'processing');

    try {
        // Step 1: Generate the clip
        const formData = new FormData();
        formData.append('shape_type', 'snap_clip');
        Object.keys(params).forEach(key => formData.append(key, params[key]));

        const clipResponse = await fetch('/modeling/api/generate/shape', {
            method: 'POST',
            body: formData
        });

        const clipData = await clipResponse.json();

        if (!clipData.success) {
            showNotification('Error generating clip: ' + clipData.error, 'error');
            return;
        }

        showNotification('Clip generated! Now merging with object...', 'processing');

        // Step 2: Get the current object's STL
        // Check if we have a currentFile URL
        if (!currentFile) {
            showNotification('No object loaded to attach clip to', 'error');
            return;
        }

        // Step 3: Boolean union the clip with the object
        const booleanFormData = new FormData();

        // Fetch both STL files and append as blobs
        const objectBlob = await fetch(currentFile).then(r => r.blob());
        const clipBlob = await fetch(clipData.download_url).then(r => r.blob());

        booleanFormData.append('mesh1', objectBlob, 'object.stl');
        booleanFormData.append('mesh2', clipBlob, 'clip.stl');
        booleanFormData.append('operation', 'union');

        const booleanResponse = await fetch('/modeling/api/stl/boolean', {
            method: 'POST',
            body: booleanFormData
        });

        const booleanData = await booleanResponse.json();

        if (booleanData.success) {
            // Load the merged result
            loadSTL(booleanData.download_url);

            showNotification('✅ Snap clip attached successfully!', 'success');
            windowManager.close('attachment-config');
            exitAttachmentMode();
        } else {
            showNotification('Error merging clip: ' + booleanData.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        console.error('Attachment error:', error);
    }
}

async function generateAndAttachThread() {
    // Similar to clip but for threads
    showNotification('Thread attachment not yet implemented', 'info');
    cancelAttachment();
}

async function generateAndAttachHoles() {
    // Similar but for mounting holes
    showNotification('Mounting holes not yet implemented', 'info');
    cancelAttachment();
}

function cancelAttachment() {
    windowManager.close('attachment-config');
    exitAttachmentMode();
}

// ============================================================================
// OBJECT HIGHLIGHTING
// ============================================================================

let highlightedObject = null;
let originalMaterial = null;

function highlightObject(object, highlight) {
    if (highlight) {
        if (highlightedObject) {
            // Unhighlight previous
            highlightObject(highlightedObject, false);
        }

        originalMaterial = object.material;
        object.material = new THREE.MeshPhongMaterial({
            color: 0x0095ff,
            transparent: true,
            opacity: 0.7,
            emissive: 0x0095ff,
            emissiveIntensity: 0.5
        });
        highlightedObject = object;
    } else {
        if (highlightedObject && originalMaterial) {
            highlightedObject.material = originalMaterial;
            highlightedObject = null;
            originalMaterial = null;
        }
    }
}
