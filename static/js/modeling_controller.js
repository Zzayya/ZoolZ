// ZoolZ 3D Studio - Professional Modeling Controller

let scene, camera, renderer, controls, mesh, gridHelper;
let currentFile = null;
let downloadUrl = null;
let currentTool = 'cookie'; // Current active tool
let selectedFaces = []; // For face selection in Thiccer tool
let faceHighlights = []; // Visual highlights for selected faces
let raycaster, mouse; // For 3D picking
let isSTLMode = false; // Track if we're in STL editing mode
let gridVisible = true; // Track grid visibility
let statsVisible = false; // Track stats overlay visibility

// Initialize Three.js scene
function initViewer() {
    const container = document.getElementById('viewer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050810);

    // Camera
    camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
    camera.position.set(0, 50, 100);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 50);
    scene.add(directionalLight);

    const directionalLight2 = new THREE.DirectionalLight(0x0095ff, 0.3);
    directionalLight2.position.set(-50, -50, -50);
    scene.add(directionalLight2);

    // Grid - positioned at y=0 (horizontal plane, build plate level)
    gridHelper = new THREE.GridHelper(200, 20, 0x0095ff, 0x003366);
    gridHelper.position.y = 0; // Ensure it's at ground level
    gridHelper.name = 'buildPlateGrid'; // Name it for toggling
    scene.add(gridHelper);

    // Axes
    const axesHelper = new THREE.AxesHelper(50);
    scene.add(axesHelper);

    // Initialize raycaster for 3D picking
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    // Add click listener for face selection (when in Thiccer mode)
    renderer.domElement.addEventListener('click', onViewerClick, false);

    // Add right-click context menu
    renderer.domElement.addEventListener('contextmenu', onContextMenu, false);

    // Handle window resize
    window.addEventListener('resize', onWindowResize);

    // Close context menu on any click
    document.addEventListener('click', () => {
        document.getElementById('contextMenu').classList.remove('active');
    });

    // File overlay drag and drop
    setupFileHandling();

    // Start animation loop
    animate();
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

function loadSTL(url) {
    const loader = new THREE.STLLoader();

    loader.load(url, function(geometry) {
        // Remove old mesh
        if (mesh) {
            scene.remove(mesh);
        }

        // Create material
        const material = new THREE.MeshPhongMaterial({
            color: 0x0095ff,
            specular: 0x111111,
            shininess: 200,
            flatShading: false
        });

        // Center geometry at origin FIRST (for proper rotation axis)
        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        const center = bbox.getCenter(new THREE.Vector3());

        // Translate geometry so its center is at (0,0,0)
        geometry.translate(-center.x, -center.y, -center.z);

        // Create mesh (now centered at origin)
        mesh = new THREE.Mesh(geometry, material);

        // NOW position the mesh so base sits on build plate
        // In Three.js: Y is up, XZ is the ground plane
        // Recompute bbox after centering
        geometry.computeBoundingBox();
        const newBbox = geometry.boundingBox;
        const minY = newBbox.min.y;

        // Lift mesh so bottom is at y=0 (base flush on build plate)
        mesh.position.set(0, -minY, 0);

        // Add to scene
        scene.add(mesh);

        // Adjust camera to look at model center
        const size = newBbox.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const modelHeight = size.y; // Y is up in Three.js
        camera.position.set(maxDim, maxDim, maxDim);
        controls.target.set(0, modelHeight / 2, 0);  // Look at center of model (Y-up)
        controls.update();
    }, undefined, function(error) {
        console.error('Error loading STL:', error);
        showStatus('Error loading 3D model', 'error');
    });
}

// File Handling for New Professional UI
function handleFile(file) {
    const isImage = file.type.startsWith('image/');
    const isSTL = file.name.toLowerCase().endsWith('.stl');

    if (!isImage && !isSTL) {
        showStatus('Please upload an image or STL file', 'error');
        return;
    }

    currentFile = file;

    // Update status bar
    document.getElementById('statusFile').textContent = file.name;

    if (isImage) {
        // Handle image upload for cookie cutter
        isSTLMode = false;

        // Enable generate button for cookie cutter
        const generateBtn = document.getElementById('generateBtn');
        const generateText = document.getElementById('generateText');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateText.textContent = 'Generate Cookie Cutter';
        }

        // Enable outline extraction buttons
        const extractOutlineBtn = document.getElementById('extractOutlineBtn');
        const extractDetailsBtn = document.getElementById('extractDetailsBtn');
        if (extractOutlineBtn) {
            extractOutlineBtn.disabled = false;
        }
        if (extractDetailsBtn) {
            extractDetailsBtn.disabled = false;
        }

        showNotification(`Image loaded: ${file.name}`, 'success');

        // Switch to cookie tool if not already active
        if (currentTool !== 'cookie') {
            switchTool('cookie');
        }

    } else if (isSTL) {
        // Handle STL upload - load directly into viewer
        isSTLMode = true;

        // Create URL for STL file and load it
        const url = URL.createObjectURL(file);
        loadSTL(url);

        showNotification(`STL loaded: ${file.name}`, 'success');

        // Show download button in toolbar
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.style.display = 'inline-flex';
            downloadUrl = url; // Set initial download URL to the uploaded file
        }
    }
}

async function generateCookieCutter() {
    if (!currentFile) {
        showStatus('Please upload an image first', 'error');
        return;
    }

    const generateBtn = document.getElementById('generateBtn');
    const generateText = document.getElementById('generateText');
    const downloadBtn = document.getElementById('downloadBtn');

    const formData = new FormData();
    formData.append('image', currentFile);
    formData.append('detail_level', document.getElementById('detailLevel').value / 100);
    formData.append('blade_thick', document.getElementById('bladeThick').value);
    formData.append('blade_height', document.getElementById('bladeHeight').value);
    formData.append('base_thick', document.getElementById('baseThick').value);
    formData.append('base_extra', document.getElementById('baseExtra').value);
    formData.append('max_dim', document.getElementById('maxDim').value);
    formData.append('no_base', document.getElementById('noBase').checked);

    generateBtn.disabled = true;
    generateText.innerHTML = '<span class="spinner"></span> Generating...';
    showStatus('Processing image and generating 3D model...', 'processing');

    try {
        const response = await fetch('/modeling/api/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus('Cookie cutter generated successfully!', 'success');
            showStats(data.stats);

            // Show download button in toolbar
            if (downloadBtn) {
                downloadBtn.style.display = 'inline-flex';
            }

            // Load STL into viewer
            loadSTL(downloadUrl);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
        generateText.textContent = 'Regenerate';
    }
}

// Model control buttons and sliders
const rotationXSlider = document.getElementById('rotationX');
const rotationYSlider = document.getElementById('rotationY');
const rotationZSlider = document.getElementById('rotationZ');
const rotationXValue = document.getElementById('rotationXValue');
const rotationYValue = document.getElementById('rotationYValue');
const rotationZValue = document.getElementById('rotationZValue');
const snapBtn = document.getElementById('snapBtn');
const curaBtn = document.getElementById('curaBtn');

// Rotation sliders - Cura style
rotationXSlider.addEventListener('input', (e) => {
    if (mesh) {
        const degrees = parseFloat(e.target.value);
        const radians = (degrees * Math.PI) / 180;
        mesh.rotation.x = radians;
        rotationXValue.textContent = `${degrees}°`;
    }
});

rotationYSlider.addEventListener('input', (e) => {
    if (mesh) {
        const degrees = parseFloat(e.target.value);
        const radians = (degrees * Math.PI) / 180;
        mesh.rotation.y = radians;
        rotationYValue.textContent = `${degrees}°`;
    }
});

rotationZSlider.addEventListener('input', (e) => {
    if (mesh) {
        const degrees = parseFloat(e.target.value);
        const radians = (degrees * Math.PI) / 180;
        mesh.rotation.z = radians;
        rotationZValue.textContent = `${degrees}°`;
    }
});

// Snap to build plate
snapBtn.addEventListener('click', () => {
    if (mesh) {
        // Reset rotation
        mesh.rotation.set(0, 0, 0);

        // Reset sliders
        rotationXSlider.value = 0;
        rotationYSlider.value = 0;
        rotationZSlider.value = 0;
        rotationXValue.textContent = '0°';
        rotationYValue.textContent = '0°';
        rotationZValue.textContent = '0°';

        // Position base flush on build plate
        // Geometry is already centered at origin, just need to lift to y=0
        mesh.geometry.computeBoundingBox();
        const bbox = mesh.geometry.boundingBox;
        const minY = bbox.min.y; // Y is up in Three.js
        mesh.position.set(0, -minY, 0);

        // Reset camera to optimal view
        const size = bbox.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const modelHeight = size.y; // Y is height
        camera.position.set(maxDim, maxDim, maxDim);
        controls.target.set(0, modelHeight / 2, 0); // Y-up coordinate system
        controls.update();

        showStatus('Model snapped to build plate', 'success');
    }
});

// Export to Cura (download with instructions)
curaBtn.addEventListener('click', () => {
    if (downloadUrl) {
        window.location.href = downloadUrl;
        showStatus('Download STL and drag it into Cura to slice!', 'success');
    }
});

// Initialize on load
window.addEventListener('load', initViewer);

// ============================================================================
// STL TOOL FUNCTIONS - Complete Implementation
// ============================================================================

// Tool switching function (called from HTML buttons)
function switchTool(tool) {
    currentTool = tool;

    // Update status bar
    const toolNames = {
        'cookie': 'Cookie Cutter',
        'outline': 'Outline',
        'thiccer': 'Thicken Walls',
        'hollow': 'Hollow Out',
        'repair': 'Repair Mesh',
        'simplify': 'Simplify',
        'mirror': 'Mirror',
        'scale': 'Scale',
        'boolean': 'Boolean Ops',
        'measure': 'Measure',
        'split': 'Split/Cut',
        'array': 'Array Pattern'
    };
    document.getElementById('statusTool').textContent = toolNames[tool] || tool;

    // Clear face selection when switching tools
    if (mesh && faceHighlights && faceHighlights.length > 0) {
        clearFaceSelection();
    }

    // Update button states (works with both old and new classes)
    document.querySelectorAll('.tool-btn, .tool-icon-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const toolBtn = document.getElementById(tool + 'Btn');
    if (toolBtn) {
        toolBtn.classList.add('active');
    }

    // Hide all parameter sections
    document.querySelectorAll('.tool-params').forEach(section => {
        section.style.display = 'none';
    });

    // Show appropriate parameter section
    const paramSection = document.getElementById(tool + 'Params');
    if (paramSection) {
        paramSection.style.display = 'block';
    }

    console.log(`Switched to tool: ${tool}`);
}

// 3D Face Selection for Thiccer Tool
function onViewerClick(event) {
    // Only allow face selection in Thiccer mode with STL loaded
    if (currentTool !== 'thiccer' || !isSTLMode || !mesh) {
        return;
    }

    // Calculate mouse position in normalized device coordinates
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Update the raycaster
    raycaster.setFromCamera(mouse, camera);

    // Check for intersections
    const intersects = raycaster.intersectObject(mesh);

    if (intersects.length > 0) {
        const faceIndex = intersects[0].faceIndex;

        // Shift-click for multi-selection, regular click for single
        if (event.shiftKey) {
            toggleFaceSelection(faceIndex);
        } else {
            // Clear previous selection and select only this face
            clearFaceSelection();
            toggleFaceSelection(faceIndex);
        }

        updateSelectionInfo();
    }
}

function toggleFaceSelection(faceIndex) {
    const index = selectedFaces.indexOf(faceIndex);

    if (index > -1) {
        // Deselect
        selectedFaces.splice(index, 1);
        removeFaceHighlight(faceIndex);
    } else {
        // Select
        selectedFaces.push(faceIndex);
        addFaceHighlight(faceIndex);
    }
}

function addFaceHighlight(faceIndex) {
    const geometry = mesh.geometry;
    const positions = geometry.attributes.position.array;

    // Get the three vertices of the face
    const a = faceIndex * 3;
    const b = a + 1;
    const c = a + 2;

    const v1 = new THREE.Vector3(positions[a * 3], positions[a * 3 + 1], positions[a * 3 + 2]);
    const v2 = new THREE.Vector3(positions[b * 3], positions[b * 3 + 1], positions[b * 3 + 2]);
    const v3 = new THREE.Vector3(positions[c * 3], positions[c * 3 + 1], positions[c * 3 + 2]);

    // Create highlight geometry
    const highlightGeometry = new THREE.BufferGeometry();
    const vertices = new Float32Array([
        v1.x, v1.y, v1.z,
        v2.x, v2.y, v2.z,
        v3.x, v3.y, v3.z
    ]);

    highlightGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

    const highlightMaterial = new THREE.MeshBasicMaterial({
        color: 0xff6600,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.6
    });

    const highlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
    highlight.userData.faceIndex = faceIndex;

    // Add to mesh (so it moves with the mesh)
    mesh.add(highlight);
    faceHighlights.push(highlight);
}

function removeFaceHighlight(faceIndex) {
    const index = faceHighlights.findIndex(h => h.userData.faceIndex === faceIndex);
    if (index > -1) {
        mesh.remove(faceHighlights[index]);
        faceHighlights.splice(index, 1);
    }
}

function clearFaceSelection() {
    selectedFaces = [];
    if (mesh && faceHighlights) {
        faceHighlights.forEach(h => mesh.remove(h));
    }
    faceHighlights = [];
    updateSelectionInfo();
}

function selectAllWalls() {
    if (!isSTLMode || !mesh) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    // Clear current selection
    clearFaceSelection();

    showStatus('Analyzing walls... this may take a moment', 'processing');

    // Analyze the STL to find all walls
    const formData = new FormData();
    formData.append('stl', currentFile);
    formData.append('max_wall_thickness', 2.0);

    fetch('/modeling/api/stl/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.walls && data.walls.wall_face_indices) {
            const wallFaces = data.walls.wall_face_indices;

            if (wallFaces.length === 0) {
                showStatus('No thin walls detected. Select faces manually or use "Select All Faces"', 'info');
            } else {
                // Select all wall faces
                wallFaces.forEach(faceIndex => {
                    selectedFaces.push(faceIndex);
                    addFaceHighlight(faceIndex);
                });

                updateSelectionInfo();
                showStatus(`Selected ${wallFaces.length} wall faces`, 'success');
            }
        } else {
            showStatus('Could not detect walls automatically', 'error');
        }
    })
    .catch(error => {
        showStatus(`Error: ${error.message}`, 'error');
    });
}

function selectAllFaces() {
    if (!isSTLMode || !mesh) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    clearFaceSelection();

    const faceCount = mesh.geometry.attributes.position.count / 3;

    for (let i = 0; i < faceCount; i++) {
        selectedFaces.push(i);
        addFaceHighlight(i);
    }

    updateSelectionInfo();
    showStatus(`Selected all ${faceCount} faces`, 'success');
}

function updateSelectionInfo() {
    const selectionInfo = document.getElementById('selectionInfo');
    const selectedCount = document.getElementById('selectedCount');
    const applyBtn = document.getElementById('applyThickenBtn');

    if (selectedFaces.length > 0) {
        selectionInfo.style.display = 'block';
        selectedCount.textContent = selectedFaces.length;
        if (applyBtn) applyBtn.disabled = false;
    } else {
        selectionInfo.style.display = 'none';
        if (applyBtn) applyBtn.disabled = true;
    }
}

// STL Tool Operations - All Complete & Working

async function applyThickening() {
    if (!isSTLMode || !currentFile) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    const thickness = parseFloat(document.getElementById('wallThickness').value);

    if (isNaN(thickness) || thickness <= 0) {
        showStatus('Please enter a valid thickness', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('stl', currentFile);
    formData.append('thickness_mm', thickness);
    formData.append('auto_detect', selectedFaces.length === 0);

    if (selectedFaces.length > 0) {
        formData.append('selected_faces', JSON.stringify(selectedFaces));
    }

    showStatus('Thickening walls... this may take a moment', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/thicken', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus('Wall thickening complete!', 'success');
            showStats(data.stats);
            downloadBtn.style.display = 'block';

            // Load thickened model
            loadSTL(downloadUrl);
            clearFaceSelection();
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

async function applyHollow() {
    if (!isSTLMode || !currentFile) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    const wallThickness = parseFloat(document.getElementById('hollowWallThickness').value);
    const addDrainage = document.getElementById('hollowDrainage').checked;
    const drainageDiameter = parseFloat(document.getElementById('drainageDiameter').value);

    const formData = new FormData();
    formData.append('stl', currentFile);
    formData.append('wall_thickness', wallThickness);
    formData.append('add_drainage', addDrainage);
    formData.append('drainage_diameter', drainageDiameter);

    showStatus('Hollowing model... this may take a moment', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/hollow', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus('Hollowing complete!', 'success');
            showStats(data.stats);
            downloadBtn.style.display = 'block';
            loadSTL(downloadUrl);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

async function applyRepair() {
    if (!isSTLMode || !currentFile) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    const aggressive = document.getElementById('aggressiveRepair').checked;

    const formData = new FormData();
    formData.append('stl', currentFile);
    formData.append('aggressive', aggressive);

    showStatus('Repairing mesh... this may take a moment', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/repair', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;

            let message = 'Mesh repaired!';
            if (data.repair_log && data.repair_log.length > 0) {
                message += ` (${data.repair_log.join(', ')})`;
            }

            showStatus(message, 'success');
            showStats(data.after);
            downloadBtn.style.display = 'block';
            loadSTL(downloadUrl);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

async function applySimplify() {
    if (!isSTLMode || !currentFile) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    const reductionPercent = parseFloat(document.getElementById('reductionPercent').value) / 100;

    const formData = new FormData();
    formData.append('stl', currentFile);
    formData.append('reduction_percent', reductionPercent);
    formData.append('preserve_boundaries', true);

    showStatus('Simplifying mesh... this may take a moment', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/simplify', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus(`Simplified! Reduced by ${data.stats.reduction_ratio * 100}%`, 'success');
            showStats(data.stats);
            downloadBtn.style.display = 'block';
            loadSTL(downloadUrl);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

async function applyMirror() {
    if (!isSTLMode || !currentFile) {
        showStatus('Please load an STL file first', 'error');
        return;
    }

    const axis = document.querySelector('input[name="mirrorAxis"]:checked').value;
    const merge = document.getElementById('mirrorMerge').checked;

    const formData = new FormData();
    formData.append('stl', currentFile);
    formData.append('axis', axis);
    formData.append('merge', merge);

    showStatus(`Mirroring across ${axis.toUpperCase()}-axis...`, 'processing');

    try {
        const response = await fetch('/modeling/api/stl/mirror', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus('Mirroring complete!', 'success');
            showStats(data.stats);
            downloadBtn.style.display = 'block';
            loadSTL(downloadUrl);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Additional STL Tools

function applyScale() {
    if (!mesh) {
        showStatus('Please load a model first', 'error');
        return;
    }

    const scalePercent = parseFloat(document.getElementById('scalePercent').value) / 100;
    mesh.scale.set(scalePercent, scalePercent, scalePercent);

    // Reposition to keep base on build plate
    mesh.geometry.computeBoundingBox();
    const bbox = mesh.geometry.boundingBox;
    const minY = bbox.min.y * scalePercent;
    mesh.position.y = -minY;

    showStatus(`Scaled to ${scalePercent * 100}%`, 'success');
}

function autoOrient() {
    if (!mesh) {
        showStatus('Please load a model first', 'error');
        return;
    }

    // Find largest face and orient it downward
    const geometry = mesh.geometry;
    geometry.computeBoundingBox();

    // Simple heuristic: lay flat the dimension that would give best print stability
    const bbox = geometry.boundingBox;
    const size = bbox.getSize(new THREE.Vector3());

    // Orient largest surface down
    if (size.x >= size.y && size.x >= size.z) {
        mesh.rotation.set(0, 0, Math.PI / 2);
    } else if (size.y >= size.x && size.y >= size.z) {
        // Already optimal (Y up)
        mesh.rotation.set(0, 0, 0);
    } else {
        mesh.rotation.set(Math.PI / 2, 0, 0);
    }

    // Snap to build plate
    geometry.computeBoundingBox();
    const newBbox = geometry.boundingBox;
    mesh.position.y = -newBbox.min.y;

    showStatus('Auto-oriented for best printing', 'success');
}

// ============================================================================
// UI CONTROL FUNCTIONS - Professional Interface
// ============================================================================

// Panel Management
function togglePanel(panelType) {
    const panels = {
        'tool': document.getElementById('toolPanel'),
        'props': document.getElementById('propsPanel')
    };

    const buttons = {
        'tool': document.getElementById('toggleToolPanel'),
        'props': document.getElementById('togglePropsPanel')
    };

    const panel = panels[panelType];
    const button = buttons[panelType];

    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        button.classList.add('active');
    } else {
        panel.style.display = 'none';
        button.classList.remove('active');
    }
}

function togglePanelExpand(panelType) {
    if (panelType === 'tool') {
        const panel = document.getElementById('toolPanel');
        panel.classList.toggle('expanded');
    }
}

// File Handling
function setupFileHandling() {
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const fileOverlay = document.getElementById('fileOverlay');

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
            closeFileOverlay();
        }
    });

    // Drag and drop on drop zone
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
            closeFileOverlay();
        }
    });

    // Click to browse
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON') {
            fileInput.click();
        }
    });

    // Global drag and drop (anywhere on viewport)
    document.body.addEventListener('dragover', (e) => {
        e.preventDefault();
        openFileOverlay();
    });
}

function openFileOverlay() {
    document.getElementById('fileOverlay').classList.add('active');
}

function closeFileOverlay() {
    document.getElementById('fileOverlay').classList.remove('active');
}

function downloadModel() {
    if (downloadUrl) {
        window.location.href = downloadUrl;
        showNotification('Downloading STL file...', 'success');
    } else {
        showNotification('No model to download', 'error');
    }
}

// Enhanced Notification System
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} active`;

    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('active');
    }, 3000);
}

// Viewport Controls
function toggleGrid() {
    if (gridHelper) {
        gridVisible = !gridVisible;
        gridHelper.visible = gridVisible;

        const gridBtn = document.getElementById('gridToggle');
        if (gridVisible) {
            gridBtn.classList.add('active');
        } else {
            gridBtn.classList.remove('active');
        }

        showNotification(`Grid ${gridVisible ? 'shown' : 'hidden'}`, 'success');
    }
}

function toggleStats() {
    statsVisible = !statsVisible;
    const statsOverlay = document.getElementById('statsOverlay');

    if (statsVisible) {
        statsOverlay.classList.add('active');
    } else {
        statsOverlay.classList.remove('active');
    }
}

function resetCamera() {
    if (mesh) {
        mesh.geometry.computeBoundingBox();
        const bbox = mesh.geometry.boundingBox;
        const size = bbox.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const modelHeight = size.y;

        camera.position.set(maxDim, maxDim, maxDim);
        controls.target.set(0, modelHeight / 2, 0);
        controls.update();

        showNotification('Camera reset', 'success');
    } else {
        camera.position.set(0, 50, 100);
        controls.target.set(0, 0, 0);
        controls.update();
        showNotification('Camera reset', 'success');
    }
}

function snapToPlate() {
    if (mesh) {
        // Reset rotation
        mesh.rotation.set(0, 0, 0);

        // Position base flush on build plate
        mesh.geometry.computeBoundingBox();
        const bbox = mesh.geometry.boundingBox;
        const minY = bbox.min.y;
        mesh.position.set(0, -minY, 0);

        showNotification('Snapped to build plate', 'success');
    } else {
        showNotification('No model loaded', 'error');
    }
}

// Context Menu
function onContextMenu(event) {
    event.preventDefault();

    const contextMenu = document.getElementById('contextMenu');
    contextMenu.style.left = `${event.clientX}px`;
    contextMenu.style.top = `${event.clientY}px`;
    contextMenu.classList.add('active');
}

// Enhanced Status Display
function showStatus(message, type) {
    showNotification(message, type);

    // Also update status bar if needed
    const statusFile = document.getElementById('statusFile');
    if (currentFile) {
        statusFile.textContent = currentFile.name;
    }
}

function showStats(stats) {
    if (stats) {
        document.getElementById('statVertices').textContent = stats.vertices?.toLocaleString() || stats.mirrored_vertices?.toLocaleString() || '-';
        document.getElementById('statFaces').textContent = stats.faces?.toLocaleString() || stats.mirrored_faces?.toLocaleString() || '-';
        document.getElementById('statWatertight').textContent = stats.is_watertight ? '✓' : '✗';

        // Auto-show stats when model is loaded
        if (!statsVisible) {
            toggleStats();
            setTimeout(() => {
                if (statsVisible) toggleStats();
            }, 5000);
        }
    }
}

// Parameter Value Updates - Wire up all sliders
document.addEventListener('DOMContentLoaded', () => {
    // Detail Level
    const detailLevel = document.getElementById('detailLevel');
    if (detailLevel) {
        detailLevel.addEventListener('input', (e) => {
            document.getElementById('detailValue').textContent = (e.target.value / 100).toFixed(2);
        });
    }

    // Blade Thickness
    const bladeThick = document.getElementById('bladeThick');
    if (bladeThick) {
        bladeThick.addEventListener('input', (e) => {
            document.getElementById('bladeThickValue').textContent = parseFloat(e.target.value).toFixed(1);
        });
    }

    // Blade Height
    const bladeHeight = document.getElementById('bladeHeight');
    if (bladeHeight) {
        bladeHeight.addEventListener('input', (e) => {
            document.getElementById('bladeHeightValue').textContent = parseFloat(e.target.value).toFixed(1);
        });
    }

    // Base Thickness
    const baseThick = document.getElementById('baseThick');
    if (baseThick) {
        baseThick.addEventListener('input', (e) => {
            document.getElementById('baseThickValue').textContent = parseFloat(e.target.value).toFixed(1);
        });
    }

    // Base Extension
    const baseExtra = document.getElementById('baseExtra');
    if (baseExtra) {
        baseExtra.addEventListener('input', (e) => {
            document.getElementById('baseExtraValue').textContent = parseFloat(e.target.value).toFixed(1);
        });
    }

    // Max Dimension
    const maxDim = document.getElementById('maxDim');
    if (maxDim) {
        maxDim.addEventListener('input', (e) => {
            document.getElementById('maxDimValue').textContent = e.target.value;
        });
    }

    // Hollow Wall Thickness
    const hollowWallThickness = document.getElementById('hollowWallThickness');
    if (hollowWallThickness) {
        hollowWallThickness.addEventListener('input', (e) => {
            document.getElementById('hollowWallThicknessValue').textContent = parseFloat(e.target.value).toFixed(1);
        });
    }

    // Drainage Diameter
    const drainageDiameter = document.getElementById('drainageDiameter');
    if (drainageDiameter) {
        drainageDiameter.addEventListener('input', (e) => {
            document.getElementById('drainageDiameterValue').textContent = parseFloat(e.target.value).toFixed(1);
        });
    }

    // Reduction Percent
    const reductionPercent = document.getElementById('reductionPercent');
    if (reductionPercent) {
        reductionPercent.addEventListener('input', (e) => {
            document.getElementById('reductionPercentValue').textContent = e.target.value;
        });
    }

    // Scale Percent
    const scalePercent = document.getElementById('scalePercent');
    if (scalePercent) {
        scalePercent.addEventListener('input', (e) => {
            document.getElementById('scalePercentValue').textContent = e.target.value;
        });
    }

    // Detail Precision slider
    const detailPrecision = document.getElementById('detailPrecision');
    if (detailPrecision) {
        detailPrecision.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value) / 100;
            document.getElementById('detailPrecisionValue').textContent = value.toFixed(2);
        });
    }
});

// Extract outline from uploaded image
function extractOutlineFromImage() {
    if (!currentFile) {
        showNotification('Please upload an image first', 'error');
        return;
    }

    const detailLevel = parseFloat(document.getElementById('detailLevel').value) / 100;

    // Call the outline extraction function from outline_editor.js
    extractOutline(currentFile, detailLevel);
}

// Extract inner details from uploaded image
function extractDetailsFromImage() {
    if (!currentFile) {
        showNotification('Please upload an image first', 'error');
        return;
    }

    const precision = parseFloat(document.getElementById('detailPrecision').value) / 100;

    // Call the detail extraction function from outline_editor.js
    extractDetails(currentFile, precision).then(detailData => {
        if (detailData && detailData.detail_count > 0) {
            // Show the stamp generation button
            const stampBtn = document.getElementById('generateStampBtn');
            if (stampBtn) {
                stampBtn.style.display = 'block';
            }
        }
    });
}

// Initialize on load
window.addEventListener('load', initViewer);
