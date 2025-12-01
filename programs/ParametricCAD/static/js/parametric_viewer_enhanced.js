// Parametric CAD 3D Viewer - ENHANCED VERSION with Transform Controls
// Major features: Click selection, Move/Rotate/Scale gizmos, Properties panel, Shape naming

let scene, camera, renderer, controls;
let shapes = {}; // Store all meshes by shape_id with metadata
let selectedShapes = new Set(); // Track selected shape IDs
let transformControls; // Transform gizmo (move/rotate/scale)
let transformMode = 'translate'; // Current transform mode
let raycaster, mouse; // For click selection
let downloadUrl = null;
let history = []; // Undo/redo history
let historyIndex = -1;

// Enhanced shape metadata
class ShapeData {
    constructor(shapeId, mesh, type, params) {
        this.id = shapeId;
        this.mesh = mesh;
        this.type = type;
        this.params = params;
        this.name = `${type}_${shapeId.split('_')[1]}`; // Default name
        this.visible = true;
        this.locked = false;
        this.transforms = {
            position: { x: 0, y: 0, z: 0 },
            rotation: { x: 0, y: 0, z: 0 },
            scale: { x: 1, y: 1, z: 1 }
        };
    }
}

// Shape parameter definitions
const shapeParams = {
    box: [
        { name: 'width', label: 'Width (mm)', type: 'number', default: 20, min: 1, max: 200 },
        { name: 'height', label: 'Height (mm)', type: 'number', default: 20, min: 1, max: 200 },
        { name: 'depth', label: 'Depth (mm)', type: 'number', default: 20, min: 1, max: 200 },
        { name: 'center', label: 'Center at Origin', type: 'checkbox', default: true }
    ],
    cylinder: [
        { name: 'radius', label: 'Radius (mm)', type: 'number', default: 10, min: 1, max: 100 },
        { name: 'height', label: 'Height (mm)', type: 'number', default: 20, min: 1, max: 200 },
        { name: 'segments', label: 'Segments', type: 'number', default: 32, min: 3, max: 128 },
        { name: 'center', label: 'Center at Origin', type: 'checkbox', default: true }
    ],
    sphere: [
        { name: 'radius', label: 'Radius (mm)', type: 'number', default: 10, min: 1, max: 100 },
        { name: 'subdivisions', label: 'Subdivisions', type: 'number', default: 3, min: 1, max: 5 }
    ],
    cone: [
        { name: 'radius', label: 'Radius (mm)', type: 'number', default: 10, min: 1, max: 100 },
        { name: 'height', label: 'Height (mm)', type: 'number', default: 20, min: 1, max: 200 },
        { name: 'segments', label: 'Segments', type: 'number', default: 32, min: 3, max: 128 },
        { name: 'center', label: 'Center at Origin', type: 'checkbox', default: true }
    ],
    torus: [
        { name: 'major_radius', label: 'Ring Radius (mm)', type: 'number', default: 15, min: 5, max: 100 },
        { name: 'minor_radius', label: 'Tube Radius (mm)', type: 'number', default: 5, min: 1, max: 50 },
        { name: 'major_sections', label: 'Ring Sections', type: 'number', default: 32, min: 3, max: 128 },
        { name: 'minor_sections', label: 'Tube Sections', type: 'number', default: 16, min: 3, max: 64 }
    ],
    prism: [
        { name: 'sides', label: 'Number of Sides', type: 'number', default: 6, min: 3, max: 12 },
        { name: 'radius', label: 'Radius (mm)', type: 'number', default: 10, min: 1, max: 100 },
        { name: 'height', label: 'Height (mm)', type: 'number', default: 20, min: 1, max: 200 }
    ]
};

// Initialize Three.js scene with enhanced features
function initViewer() {
    const container = document.getElementById('viewer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050810);

    // Camera
    camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
    camera.position.set(40, 40, 60);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Orbit Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Transform Controls (Move/Rotate/Scale gizmo)
    transformControls = new THREE.TransformControls(camera, renderer.domElement);
    transformControls.addEventListener('change', () => {
        renderer.render(scene, camera);
        updatePropertiesPanel(); // Update numeric inputs when dragging gizmo
    });
    transformControls.addEventListener('dragging-changed', (event) => {
        controls.enabled = !event.value; // Disable orbit when dragging gizmo
    });
    scene.add(transformControls);

    // Raycaster for click selection
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(50, 50, 50);
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0x0095ff, 0.3);
    directionalLight2.position.set(-50, -50, -50);
    scene.add(directionalLight2);

    // Grid (build plate)
    const gridHelper = new THREE.GridHelper(100, 20, 0x0095ff, 0x003366);
    scene.add(gridHelper);

    // Axes
    const axesHelper = new THREE.AxesHelper(30);
    scene.add(axesHelper);

    // Event listeners
    window.addEventListener('resize', onWindowResize);
    renderer.domElement.addEventListener('click', onMouseClick);
    document.addEventListener('keydown', onKeyDown);

    // Start animation loop
    animate();

    console.log('✓ Enhanced Parametric CAD Viewer initialized');
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

function onWindowResize() {
    const container = document.getElementById('viewer');
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

// ============================================================================
// SELECTION SYSTEM - Click to select shapes in 3D
// ============================================================================

function onMouseClick(event) {
    // Calculate mouse position in normalized device coordinates
    const container = document.getElementById('viewer');
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Raycast from camera through mouse position
    raycaster.setFromCamera(mouse, camera);

    // Get all mesh objects (filter out grid, axes, etc.)
    const meshObjects = Object.values(shapes).map(sd => sd.mesh);
    const intersects = raycaster.intersectObjects(meshObjects);

    if (intersects.length > 0) {
        // Clicked on a shape
        const clickedMesh = intersects[0].object;
        const shapeId = clickedMesh.userData.shapeId;

        if (event.ctrlKey || event.metaKey) {
            // Ctrl+Click = toggle selection (multi-select)
            toggleShapeSelection(shapeId);
        } else {
            // Regular click = select only this shape
            clearSelection();
            selectShape(shapeId);
        }
    } else {
        // Clicked on empty space = deselect all
        if (!event.ctrlKey && !event.metaKey) {
            clearSelection();
        }
    }
}

function selectShape(shapeId) {
    if (!shapes[shapeId]) return;

    selectedShapes.add(shapeId);
    const shapeData = shapes[shapeId];

    // Visual feedback - highlight
    shapeData.mesh.material.color.setHex(0x00ffff);
    shapeData.mesh.material.emissive.setHex(0x00ffff);
    shapeData.mesh.material.opacity = 1.0;

    // Attach transform gizmo to last selected shape
    transformControls.attach(shapeData.mesh);

    updateUI();
}

function toggleShapeSelection(shapeId) {
    if (selectedShapes.has(shapeId)) {
        deselectShape(shapeId);
    } else {
        selectShape(shapeId);
    }
}

function deselectShape(shapeId) {
    if (!shapes[shapeId]) return;

    selectedShapes.delete(shapeId);
    const shapeData = shapes[shapeId];

    // Restore original color
    shapeData.mesh.material.color.copy(shapeData.mesh.userData.originalColor);
    shapeData.mesh.material.emissive.setHex(0x000000);
    shapeData.mesh.material.opacity = 0.9;

    updateUI();
}

function clearSelection() {
    selectedShapes.forEach(shapeId => {
        if (shapes[shapeId]) {
            const shapeData = shapes[shapeId];
            shapeData.mesh.material.color.copy(shapeData.mesh.userData.originalColor);
            shapeData.mesh.material.emissive.setHex(0x000000);
            shapeData.mesh.material.opacity = 0.9;
        }
    });
    selectedShapes.clear();
    transformControls.detach();
    updateUI();
}

// ============================================================================
// TRANSFORM CONTROLS - Move/Rotate/Scale
// ============================================================================

function onKeyDown(event) {
    // Hotkeys for transform modes (like Blender)
    if (event.key === 'g' || event.key === 'G') {
        setTransformMode('translate');
    } else if (event.key === 'r' || event.key === 'R') {
        setTransformMode('rotate');
    } else if (event.key === 's' || event.key === 'S') {
        setTransformMode('scale');
    } else if (event.key === 'Escape') {
        clearSelection();
    } else if (event.key === 'Delete' || event.key === 'Backspace') {
        deleteSelectedShapes();
    }
    // Undo/Redo
    else if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
        undo();
    } else if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
        redo();
    }
}

function setTransformMode(mode) {
    transformMode = mode;
    transformControls.setMode(mode);

    // Update button states
    document.getElementById('moveBtn').classList.toggle('active', mode === 'translate');
    document.getElementById('rotateBtn').classList.toggle('active', mode === 'rotate');
    document.getElementById('scaleBtn').classList.toggle('active', mode === 'scale');
}

function deleteSelectedShapes() {
    if (selectedShapes.size === 0) {
        showStatus('No shapes selected', 'warning');
        return;
    }

    const shapesToDelete = Array.from(selectedShapes);
    shapesToDelete.forEach(shapeId => {
        removeShapeFromScene(shapeId);
    });

    showStatus(`Deleted ${shapesToDelete.length} shape(s)`, 'success');
    updateOpenSCADCode();
}

// ============================================================================
// SHAPE MANAGEMENT
// ============================================================================

function addShapeToScene(shapeId, stlUrl, type, params) {
    const loader = new THREE.STLLoader();

    loader.load(stlUrl, function(geometry) {
        // Create material - different colors for different shapes
        const hue = (Object.keys(shapes).length * 0.15) % 1.0;
        const color = new THREE.Color();
        color.setHSL(hue, 0.8, 0.5);

        const material = new THREE.MeshPhongMaterial({
            color: color,
            specular: 0x111111,
            shininess: 200,
            flatShading: false,
            transparent: true,
            opacity: 0.9
        });

        // Create mesh
        const mesh = new THREE.Mesh(geometry, material);

        // Position on build plate (bottom at z=0, centered in XY)
        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        const centerX = (bbox.min.x + bbox.max.x) / 2;
        const centerY = (bbox.min.y + bbox.max.y) / 2;
        const minZ = bbox.min.z;

        // Move so bottom sits on z=0 and centered in XY
        mesh.position.set(-centerX, -centerY, -minZ);

        // Store mesh with metadata
        mesh.userData.shapeId = shapeId;
        mesh.userData.originalColor = color.clone();

        // Create enhanced shape data
        const shapeData = new ShapeData(shapeId, mesh, type, params);
        shapes[shapeId] = shapeData;

        // Add to scene
        scene.add(mesh);

        // Adjust camera to fit all shapes
        adjustCameraToFitAll();

        // Update UI
        updateUI();

        // Save to history
        saveHistory();

    }, undefined, function(error) {
        console.error('Error loading STL:', error);
        showStatus('Error loading 3D model', 'error');
    });
}

function removeShapeFromScene(shapeId) {
    const shapeData = shapes[shapeId];
    if (shapeData) {
        scene.remove(shapeData.mesh);
        shapeData.mesh.geometry.dispose();
        shapeData.mesh.material.dispose();
        delete shapes[shapeId];
        selectedShapes.delete(shapeId);

        if (selectedShapes.size === 0) {
            transformControls.detach();
        }

        updateUI();
        saveHistory();
    }
}

function adjustCameraToFitAll() {
    if (Object.keys(shapes).length === 0) return;

    // Calculate combined bounding box
    const box = new THREE.Box3();
    Object.values(shapes).forEach(shapeData => {
        const meshBox = new THREE.Box3().setFromObject(shapeData.mesh);
        box.union(meshBox);
    });

    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const dist = maxDim * 2;

    camera.position.set(dist, dist, dist);
    controls.target.set(center.x, center.y, center.z);
    controls.update();
}

// ============================================================================
// PROPERTIES PANEL - Edit selected shape
// ============================================================================

function updatePropertiesPanel() {
    const propsPanel = document.getElementById('propertiesPanel');

    if (selectedShapes.size === 0) {
        propsPanel.innerHTML = '<p style="color: #8ab4f8;">Select a shape to edit properties</p>';
        return;
    }

    if (selectedShapes.size > 1) {
        propsPanel.innerHTML = '<p style="color: #8ab4f8;">Multiple shapes selected</p>';
        // TODO: Show common properties
        return;
    }

    // Single shape selected - show full properties
    const shapeId = Array.from(selectedShapes)[0];
    const shapeData = shapes[shapeId];

    let html = `
        <div class="property-section">
            <h3>Shape Properties</h3>

            <!-- Shape Name -->
            <div class="form-group">
                <label for="shapeName">Name</label>
                <input type="text" id="shapeName" value="${shapeData.name}"
                       onchange="renameShape('${shapeId}', this.value)">
            </div>

            <!-- Visibility & Lock -->
            <div class="form-group">
                <label>
                    <input type="checkbox" id="shapeVisible" ${shapeData.visible ? 'checked' : ''}
                           onchange="toggleShapeVisibility('${shapeId}')">
                    Visible
                </label>
                <label style="margin-left: 20px;">
                    <input type="checkbox" id="shapeLocked" ${shapeData.locked ? 'checked' : ''}
                           onchange="toggleShapeLock('${shapeId}')">
                    Locked
                </label>
            </div>
        </div>

        <div class="property-section">
            <h3>Transform</h3>

            <!-- Position -->
            <div class="form-group">
                <label>Position X (mm)</label>
                <input type="number" id="posX" value="${shapeData.mesh.position.x.toFixed(2)}"
                       onchange="setShapePosition('${shapeId}', 'x', parseFloat(this.value))">
            </div>
            <div class="form-group">
                <label>Position Y (mm)</label>
                <input type="number" id="posY" value="${shapeData.mesh.position.y.toFixed(2)}"
                       onchange="setShapePosition('${shapeId}', 'y', parseFloat(this.value))">
            </div>
            <div class="form-group">
                <label>Position Z (mm)</label>
                <input type="number" id="posZ" value="${shapeData.mesh.position.z.toFixed(2)}"
                       onchange="setShapePosition('${shapeId}', 'z', parseFloat(this.value))">
            </div>

            <!-- Rotation -->
            <div class="form-group">
                <label>Rotation X (degrees)</label>
                <input type="number" id="rotX" value="${(shapeData.mesh.rotation.x * 180 / Math.PI).toFixed(2)}"
                       onchange="setShapeRotation('${shapeId}', 'x', parseFloat(this.value))">
            </div>
            <div class="form-group">
                <label>Rotation Y (degrees)</label>
                <input type="number" id="rotY" value="${(shapeData.mesh.rotation.y * 180 / Math.PI).toFixed(2)}"
                       onchange="setShapeRotation('${shapeId}', 'y', parseFloat(this.value))">
            </div>
            <div class="form-group">
                <label>Rotation Z (degrees)</label>
                <input type="number" id="rotZ" value="${(shapeData.mesh.rotation.z * 180 / Math.PI).toFixed(2)}"
                       onchange="setShapeRotation('${shapeId}', 'z', parseFloat(this.value))">
            </div>

            <!-- Scale -->
            <div class="form-group">
                <label>Scale X</label>
                <input type="number" id="scaleX" value="${shapeData.mesh.scale.x.toFixed(2)}" step="0.1"
                       onchange="setShapeScale('${shapeId}', 'x', parseFloat(this.value))">
            </div>
            <div class="form-group">
                <label>Scale Y</label>
                <input type="number" id="scaleY" value="${shapeData.mesh.scale.y.toFixed(2)}" step="0.1"
                       onchange="setShapeScale('${shapeId}', 'y', parseFloat(this.value))">
            </div>
            <div class="form-group">
                <label>Scale Z</label>
                <input type="number" id="scaleZ" value="${shapeData.mesh.scale.z.toFixed(2)}" step="0.1"
                       onchange="setShapeScale('${shapeId}', 'z', parseFloat(this.value))">
            </div>

            <button onclick="resetTransforms('${shapeId}')" class="btn-secondary">
                Reset Transforms
            </button>
        </div>

        <div class="property-section">
            <h3>Shape Parameters</h3>
            <p style="color: #8ab4f8; font-size: 0.9em;">
                Type: ${shapeData.type}<br>
                ${getParamsDisplay(shapeData.params)}
            </p>
            <p style="color: #666; font-size: 0.85em;">
                Note: To change shape parameters, create a new shape.
            </p>
        </div>
    `;

    propsPanel.innerHTML = html;
}

function getParamsDisplay(params) {
    let html = '';
    for (const [key, value] of Object.entries(params)) {
        html += `${key}: ${value}<br>`;
    }
    return html;
}

// Transform setters
function setShapePosition(shapeId, axis, value) {
    if (!shapes[shapeId]) return;
    shapes[shapeId].mesh.position[axis] = value;
    saveHistory();
}

function setShapeRotation(shapeId, axis, degrees) {
    if (!shapes[shapeId]) return;
    shapes[shapeId].mesh.rotation[axis] = degrees * Math.PI / 180;
    saveHistory();
}

function setShapeScale(shapeId, axis, value) {
    if (!shapes[shapeId]) return;
    if (value <= 0) value = 0.01; // Prevent negative/zero scale
    shapes[shapeId].mesh.scale[axis] = value;
    saveHistory();
}

function resetTransforms(shapeId) {
    if (!shapes[shapeId]) return;
    const shapeData = shapes[shapeId];
    shapeData.mesh.position.set(0, 0, 0);
    shapeData.mesh.rotation.set(0, 0, 0);
    shapeData.mesh.scale.set(1, 1, 1);
    updatePropertiesPanel();
    saveHistory();
}

function renameShape(shapeId, newName) {
    if (!shapes[shapeId]) return;
    shapes[shapeId].name = newName.trim() || shapes[shapeId].name;
    updateShapesList();
    updateOpenSCADCode();
}

function toggleShapeVisibility(shapeId) {
    if (!shapes[shapeId]) return;
    const shapeData = shapes[shapeId];
    shapeData.visible = !shapeData.visible;
    shapeData.mesh.visible = shapeData.visible;
}

function toggleShapeLock(shapeId) {
    if (!shapes[shapeId]) return;
    shapes[shapeId].locked = !shapes[shapeId].locked;
    // TODO: Implement lock behavior (disable transforms)
}

// ============================================================================
// HISTORY SYSTEM - Undo/Redo
// ============================================================================

function saveHistory() {
    // Simple history: save current scene state
    const state = {
        shapes: Object.keys(shapes).map(id => ({
            id,
            position: { ...shapes[id].mesh.position },
            rotation: { ...shapes[id].mesh.rotation },
            scale: { ...shapes[id].mesh.scale },
            name: shapes[id].name
        }))
    };

    // Remove future history if we're not at the end
    if (historyIndex < history.length - 1) {
        history = history.slice(0, historyIndex + 1);
    }

    history.push(state);
    historyIndex++;

    // Limit history size
    if (history.length > 50) {
        history.shift();
        historyIndex--;
    }
}

function undo() {
    if (historyIndex <= 0) {
        showStatus('Nothing to undo', 'info');
        return;
    }

    historyIndex--;
    restoreHistory();
    showStatus('Undo', 'info');
}

function redo() {
    if (historyIndex >= history.length - 1) {
        showStatus('Nothing to redo', 'info');
        return;
    }

    historyIndex++;
    restoreHistory();
    showStatus('Redo', 'info');
}

function restoreHistory() {
    const state = history[historyIndex];

    state.shapes.forEach(shapeState => {
        const shapeData = shapes[shapeState.id];
        if (shapeData) {
            shapeData.mesh.position.copy(shapeState.position);
            shapeData.mesh.rotation.copy(shapeState.rotation);
            shapeData.mesh.scale.copy(shapeState.scale);
            shapeData.name = shapeState.name;
        }
    });

    updateUI();
}

// ============================================================================
// UI UPDATE
// ============================================================================

function updateUI() {
    updateShapesList();
    updatePropertiesPanel();
    updateBooleanButtons();
    updateOpenSCADCode();
}

function updateShapesList() {
    const shapesListContainer = document.getElementById('shapesList');

    if (Object.keys(shapes).length === 0) {
        shapesListContainer.innerHTML = '<p style="color: #666;">No shapes created yet</p>';
        return;
    }

    let html = '';
    Object.values(shapes).forEach(shapeData => {
        const isSelected = selectedShapes.has(shapeData.id);
        html += `
            <div class="shape-item ${isSelected ? 'selected' : ''}"
                 onclick="toggleShapeSelection('${shapeData.id}')"
                 style="cursor: pointer;">
                <div>
                    <strong>${shapeData.name}</strong><br>
                    <small>${shapeData.type}</small>
                </div>
                <button onclick="event.stopPropagation(); removeShapeFromScene('${shapeData.id}')"
                        style="padding: 5px 10px;">
                    Delete
                </button>
            </div>
        `;
    });

    shapesListContainer.innerHTML = html;
}

function updateBooleanButtons() {
    const count = selectedShapes.size;
    const unionBtn = document.getElementById('unionBtn');
    const differenceBtn = document.getElementById('differenceBtn');
    const intersectionBtn = document.getElementById('intersectionBtn');

    if (unionBtn) unionBtn.disabled = count < 2;
    if (differenceBtn) differenceBtn.disabled = count < 2;
    if (intersectionBtn) intersectionBtn.disabled = count < 2;
}

function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('shapeInfo') || document.createElement('div');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    console.log(`[${type}] ${message}`);
}

// This file continues... Let me know if you want the rest (generate shape, boolean ops, OpenSCAD export)
// Next sections: generateShape(), booleanOperations(), updateOpenSCADCode(), etc.

// ============================================================================
// SHAPE GENERATION - Create shapes via backend
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI after DOM loaded
    initUIElements();
    initEventListeners();
});

function initUIElements() {
    // Get references to UI elements
    window.shapeTypeSelect = document.getElementById('shapeType');
    window.paramsContainer = document.getElementById('params-container');
    window.generateBtn = document.getElementById('generateBtn');
    window.generateText = document.getElementById('generateText');
    window.downloadBtn = document.getElementById('downloadBtn');
    window.exportAllBtn = document.getElementById('exportAllBtn');
    window.openscadCode = document.getElementById('openscadCode');
    window.copyCodeBtn = document.getElementById('copyCodeBtn');
    window.shapesListContainer = document.getElementById('shapesList');
    window.shapeInfo = document.getElementById('shapeInfo');
}

function initEventListeners() {
    // Shape type selector
    shapeTypeSelect.addEventListener('change', function() {
        const shapeType = this.value;

        if (!shapeType) {
            paramsContainer.innerHTML = '<p style="color: #8ab4f8;">Select a shape to see parameters</p>';
            generateBtn.disabled = true;
            generateText.textContent = 'Select Shape First';
            return;
        }

        buildParameterForm(shapeType);
        generateBtn.disabled = false;
        generateText.textContent = 'Add Shape to Scene';
    });

    // Generate button
    generateBtn.addEventListener('click', generateShape);

    // Transform mode buttons
    if (document.getElementById('moveBtn')) {
        document.getElementById('moveBtn').addEventListener('click', () => setTransformMode('translate'));
    }
    if (document.getElementById('rotateBtn')) {
        document.getElementById('rotateBtn').addEventListener('click', () => setTransformMode('rotate'));
    }
    if (document.getElementById('scaleBtn')) {
        document.getElementById('scaleBtn').addEventListener('click', () => setTransformMode('scale'));
    }

    // Boolean operation buttons
    if (document.getElementById('unionBtn')) {
        document.getElementById('unionBtn').addEventListener('click', () => performBoolean('union'));
    }
    if (document.getElementById('differenceBtn')) {
        document.getElementById('differenceBtn').addEventListener('click', () => performBoolean('difference'));
    }
    if (document.getElementById('intersectionBtn')) {
        document.getElementById('intersectionBtn').addEventListener('click', () => performBoolean('intersection'));
    }

    // Clear all button
    if (document.getElementById('clearAllBtn')) {
        document.getElementById('clearAllBtn').addEventListener('click', clearScene);
    }

    // Copy code button
    if (copyCodeBtn) {
        copyCodeBtn.addEventListener('click', copyOpenSCADCode);
    }

    // Export button
    if (exportAllBtn) {
        exportAllBtn.addEventListener('click', exportAllShapes);
    }
}

function buildParameterForm(shapeType) {
    const params = shapeParams[shapeType];
    if (!params) {
        paramsContainer.innerHTML = '<p style="color: #ff6b6b;">Unknown shape type</p>';
        return;
    }

    let html = '';
    params.forEach(param => {
        html += '<div class="form-group">';
        html += '<label for="' + param.name + '">' + param.label + '</label>';

        if (param.type === 'checkbox') {
            html += '<input type="checkbox" id="' + param.name + '"' + (param.default ? ' checked' : '') + '>';
        } else {
            html += '<input type="' + param.type + '" id="' + param.name + '" value="' + param.default + '"';
            if (param.min !== undefined) html += ' min="' + param.min + '"';
            if (param.max !== undefined) html += ' max="' + param.max + '"';
            html += '>';
        }

        html += '</div>';
    });

    paramsContainer.innerHTML = html;
}

function getParameterValues(shapeType) {
    const params = shapeParams[shapeType];
    const values = {};

    params.forEach(param => {
        const input = document.getElementById(param.name);
        if (input) {
            if (param.type === 'checkbox') {
                values[param.name] = input.checked;
            } else {
                values[param.name] = parseFloat(input.value);
            }
        }
    });

    return values;
}

async function generateShape() {
    const shapeType = shapeTypeSelect.value;
    if (!shapeType) return;

    const params = getParameterValues(shapeType);

    generateBtn.disabled = true;
    generateText.textContent = 'Adding...';
    showStatus('Creating shape...', 'info');

    try {
        const response = await fetch('/parametric/api/shape/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                shape_type: shapeType,
                params: params,
                operations: []
            })
        });

        const data = await response.json();

        if (data.success) {
            showStatus('Shape added!', 'success');
            await renderAndLoadSTL(data.shape_id, shapeType, params);
            await updateOpenSCADCode();
            exportAllBtn.style.display = 'block';
        } else {
            showStatus('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateText.textContent = 'Add Shape to Scene';
    }
}

async function renderAndLoadSTL(shapeId, shapeType, params) {
    try {
        const response = await fetch('/parametric/api/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                shape_id: shapeId,
                filename: shapeId + '.stl'
            })
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            addShapeToScene(shapeId, downloadUrl, shapeType, params);
        } else {
            showStatus('Error rendering: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Render error:', error);
    }
}

// ============================================================================
// BOOLEAN OPERATIONS
// ============================================================================

async function performBoolean(operation) {
    if (selectedShapes.size < 2) {
        showStatus('Select at least 2 shapes', 'warning');
        return;
    }

    const shapeIds = Array.from(selectedShapes);
    showStatus('Performing ' + operation + '...', 'info');

    try {
        const response = await fetch('/parametric/api/combine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                shapes: shapeIds,
                operation: operation
            })
        });

        const data = await response.json();

        if (data.success) {
            shapeIds.forEach(id => removeShapeFromScene(id));
            await renderAndLoadSTL(data.result_id, 'combined', {});
            await updateOpenSCADCode();
            showStatus(operation + ' completed!', 'success');
        } else {
            showStatus('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// OPENSCAD CODE GENERATION
// ============================================================================

async function updateOpenSCADCode() {
    if (Object.keys(shapes).length === 0) {
        openscadCode.textContent = '// No shapes in scene';
        return;
    }

    try {
        const response = await fetch('/parametric/api/openscad/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            let code = '// ZoolZ Parametric CAD - Generated OpenSCAD Code\n\n';
            code += data.code;

            // Add transform comments for each shape
            Object.values(shapes).forEach(shapeData => {
                const pos = shapeData.mesh.position;
                const rot = shapeData.mesh.rotation;
                const scale = shapeData.mesh.scale;

                const hasTransforms = pos.x !== 0 || pos.y !== 0 || pos.z !== 0 ||
                                    rot.x !== 0 || rot.y !== 0 || rot.z !== 0 ||
                                    scale.x !== 1 || scale.y !== 1 || scale.z !== 1;

                if (hasTransforms) {
                    code += '\n// ' + shapeData.name + ' - Transforms:\n';
                    if (pos.x !== 0 || pos.y !== 0 || pos.z !== 0) {
                        code += '// translate([' + pos.x.toFixed(2) + ', ' + pos.y.toFixed(2) + ', ' + pos.z.toFixed(2) + '])\n';
                    }
                    if (rot.x !== 0 || rot.y !== 0 || rot.z !== 0) {
                        code += '// rotate([' + (rot.x * 180 / Math.PI).toFixed(2) + ', ' + (rot.y * 180 / Math.PI).toFixed(2) + ', ' + (rot.z * 180 / Math.PI).toFixed(2) + '])\n';
                    }
                    if (scale.x !== 1 || scale.y !== 1 || scale.z !== 1) {
                        code += '// scale([' + scale.x.toFixed(2) + ', ' + scale.y.toFixed(2) + ', ' + scale.z.toFixed(2) + '])\n';
                    }
                }
            });

            openscadCode.textContent = code;
        } else {
            openscadCode.textContent = '// Error generating code';
        }
    } catch (error) {
        console.error('Error:', error);
        openscadCode.textContent = '// Error generating code';
    }
}

function copyOpenSCADCode() {
    const code = openscadCode.textContent;
    navigator.clipboard.writeText(code).then(() => {
        showStatus('Code copied!', 'success');
        copyCodeBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyCodeBtn.textContent = 'Copy Code';
        }, 2000);
    }).catch(() => {
        showStatus('Failed to copy', 'error');
    });
}

// ============================================================================
// EXPORT
// ============================================================================

async function exportAllShapes() {
    showStatus('Exporting...', 'info');

    const code = openscadCode.textContent;
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'zoolz_scene_' + Date.now() + '.scad';
    a.click();

    URL.revokeObjectURL(url);
    showStatus('Export complete!', 'success');
}

// ============================================================================
// SCENE MANAGEMENT
// ============================================================================

async function clearScene() {
    if (Object.keys(shapes).length === 0) {
        showStatus('Scene already empty', 'info');
        return;
    }

    if (!confirm('Clear all shapes?')) return;

    try {
        const response = await fetch('/parametric/api/shapes/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            Object.keys(shapes).forEach(shapeId => {
                const shapeData = shapes[shapeId];
                scene.remove(shapeData.mesh);
                shapeData.mesh.geometry.dispose();
                shapeData.mesh.material.dispose();
            });

            shapes = {};
            selectedShapes.clear();
            transformControls.detach();
            history = [];
            historyIndex = -1;

            updateUI();
            openscadCode.textContent = '// No shapes in scene';
            exportAllBtn.style.display = 'none';
            
            showStatus('Scene cleared', 'success');
        }
    } catch (error) {
        showStatus('Error clearing scene', 'error');
    }
}

console.log('Enhanced Parametric CAD Viewer - Ready!');
