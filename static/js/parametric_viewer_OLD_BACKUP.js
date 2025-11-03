// Parametric CAD 3D Viewer and Controller - MULTI-SHAPE VERSION

let scene, camera, renderer, controls;
let shapes = {}; // Store all meshes by shape_id
let selectedShapes = new Set(); // Track selected shape IDs
let downloadUrl = null;

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
    camera.position.set(40, 40, 60);

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

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(50, 50, 50);
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0x0095ff, 0.3);
    directionalLight2.position.set(-50, -50, -50);
    scene.add(directionalLight2);

    // Grid
    const gridHelper = new THREE.GridHelper(100, 20, 0x0095ff, 0x003366);
    scene.add(gridHelper);

    // Axes
    const axesHelper = new THREE.AxesHelper(30);
    scene.add(axesHelper);

    // Handle window resize
    window.addEventListener('resize', onWindowResize);

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

function addShapeToScene(shapeId, stlUrl) {
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

        // Add to scene and registry
        scene.add(mesh);
        shapes[shapeId] = mesh;

        // Adjust camera to fit all shapes
        adjustCameraToFitAll();

    }, undefined, function(error) {
        console.error('Error loading STL:', error);
        showStatus('Error loading 3D model', 'error');
    });
}

function adjustCameraToFitAll() {
    if (Object.keys(shapes).length === 0) return;

    // Calculate combined bounding box
    const box = new THREE.Box3();
    Object.values(shapes).forEach(mesh => {
        const meshBox = new THREE.Box3().setFromObject(mesh);
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

function removeShapeFromScene(shapeId) {
    const mesh = shapes[shapeId];
    if (mesh) {
        scene.remove(mesh);
        mesh.geometry.dispose();
        mesh.material.dispose();
        delete shapes[shapeId];
        selectedShapes.delete(shapeId);
        updateBooleanButtons();
    }
}

function toggleShapeSelection(shapeId) {
    if (selectedShapes.has(shapeId)) {
        selectedShapes.delete(shapeId);
        // Restore original color
        const mesh = shapes[shapeId];
        if (mesh) {
            mesh.material.color.copy(mesh.userData.originalColor);
            mesh.material.emissive.setHex(0x000000);
            mesh.material.opacity = 0.9;
        }
    } else {
        selectedShapes.add(shapeId);
        // Highlight selected shape
        const mesh = shapes[shapeId];
        if (mesh) {
            mesh.material.color.setHex(0x00ffff);
            mesh.material.emissive.setHex(0x00ffff);
            mesh.material.opacity = 1.0;
        }
    }
    updateBooleanButtons();
    updateShapesList();
}

function updateBooleanButtons() {
    const count = selectedShapes.size;
    const unionBtn = document.getElementById('unionBtn');
    const differenceBtn = document.getElementById('differenceBtn');
    const intersectionBtn = document.getElementById('intersectionBtn');

    unionBtn.disabled = count < 2;
    differenceBtn.disabled = count < 2;
    intersectionBtn.disabled = count < 2;
}

// Shape type selector
const shapeTypeSelect = document.getElementById('shapeType');
const paramsContainer = document.getElementById('params-container');
const generateBtn = document.getElementById('generateBtn');
const generateText = document.getElementById('generateText');
const downloadBtn = document.getElementById('downloadBtn');
const exportAllBtn = document.getElementById('exportAllBtn');
const openscadCode = document.getElementById('openscadCode');
const shapeInfo = document.getElementById('shapeInfo');
const copyCodeBtn = document.getElementById('copyCodeBtn');
const shapesListContainer = document.getElementById('shapesList');

shapeTypeSelect.addEventListener('change', function() {
    const shapeType = this.value;

    if (!shapeType) {
        paramsContainer.innerHTML = '<p style="color: #8ab4f8;">Select a shape to see parameters</p>';
        generateBtn.disabled = true;
        generateText.textContent = 'Select Shape First';
        return;
    }

    // Build parameter form
    buildParameterForm(shapeType);
    generateBtn.disabled = false;
    generateText.textContent = 'Add Shape to Scene';
});

function buildParameterForm(shapeType) {
    const params = shapeParams[shapeType];
    if (!params) {
        paramsContainer.innerHTML = '<p style="color: #ff6b6b;">Unknown shape type</p>';
        return;
    }

    let html = '';
    params.forEach(param => {
        html += '<div class="form-group">';
        html += `<label for="${param.name}">${param.label}</label>`;

        if (param.type === 'checkbox') {
            html += `<input type="checkbox" id="${param.name}" ${param.default ? 'checked' : ''}>`;
        } else {
            html += `<input type="${param.type}" id="${param.name}" value="${param.default}"`;
            if (param.min !== undefined) html += ` min="${param.min}"`;
            if (param.max !== undefined) html += ` max="${param.max}"`;
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

// Generate button
generateBtn.addEventListener('click', generateShape);

async function generateShape() {
    const shapeType = shapeTypeSelect.value;
    if (!shapeType) return;

    const params = getParameterValues(shapeType);

    generateBtn.disabled = true;
    generateText.innerHTML = '<span class="spinner"></span> Adding...';
    showStatus('Creating shape...', 'info');

    try {
        const response = await fetch('/parametric/api/shape/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shape_type: shapeType,
                params: params,
                operations: []
            })
        });

        const data = await response.json();

        if (data.success) {
            showStatus('Shape added to scene!', 'success');

            // Render and load STL
            await renderAndLoadSTL(data.shape_id, shapeType, params);

            // Update shapes list
            await updateShapesList();

            // Update OpenSCAD code to show all shapes
            await updateAllOpenSCADCode();

            exportAllBtn.style.display = 'block';
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
        generateText.textContent = 'Add Shape to Scene';
    }
}

async function renderAndLoadSTL(shapeId, shapeType, params) {
    try {
        const response = await fetch('/parametric/api/render', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shape_id: shapeId,
                filename: `${shapeId}.stl`
            })
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            addShapeToScene(shapeId, downloadUrl);
        } else {
            showStatus(`Error rendering: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Render error:', error);
    }
}

async function updateShapesList() {
    try {
        const response = await fetch('/parametric/api/shapes/list');
        const data = await response.json();

        if (data.success && data.shapes.length > 0) {
            let html = '';
            data.shapes.forEach(shape => {
                const isSelected = selectedShapes.has(shape.id);
                html += `
                    <div class="shape-item ${isSelected ? 'selected' : ''}" data-shape-id="${shape.id}">
                        <div class="shape-item-header">
                            <div style="display: flex; align-items: center;">
                                <div class="checkbox-container">
                                    <input type="checkbox" ${isSelected ? 'checked' : ''}
                                           onclick="toggleShapeSelection('${shape.id}')" />
                                </div>
                                <span class="shape-item-title">${shape.type}</span>
                            </div>
                            <button class="shape-item-delete" onclick="deleteShape('${shape.id}')">×</button>
                        </div>
                        <div class="shape-item-info">ID: ${shape.id}</div>
                    </div>
                `;
            });
            shapesListContainer.innerHTML = html;
        } else {
            shapesListContainer.innerHTML = '<div class="empty-state">No shapes yet.<br>Add shapes to begin!</div>';
        }
    } catch (error) {
        console.error('Error updating shapes list:', error);
    }
}

async function deleteShape(shapeId) {
    removeShapeFromScene(shapeId);
    await updateShapesList();
    await updateAllOpenSCADCode();

    if (Object.keys(shapes).length === 0) {
        exportAllBtn.style.display = 'none';
        openscadCode.textContent = '// No shapes in scene';
    }
}

// Clear all button
document.getElementById('clearAllBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/parametric/api/shapes/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Remove all meshes from scene
            Object.keys(shapes).forEach(shapeId => {
                removeShapeFromScene(shapeId);
            });

            shapes = {};
            selectedShapes.clear();
            await updateShapesList();
            openscadCode.textContent = '// No shapes in scene';
            exportAllBtn.style.display = 'none';
            showStatus('Scene cleared', 'success');
        }
    } catch (error) {
        showStatus('Error clearing scene', 'error');
    }
});

// Boolean operations
document.getElementById('unionBtn').addEventListener('click', () => performBooleanOp('union'));
document.getElementById('differenceBtn').addEventListener('click', () => performBooleanOp('difference'));
document.getElementById('intersectionBtn').addEventListener('click', () => performBooleanOp('intersection'));

async function performBooleanOp(operation) {
    if (selectedShapes.size < 2) return;

    const shapeIds = Array.from(selectedShapes);
    showStatus(`Performing ${operation}...`, 'info');

    try {
        const response = await fetch('/parametric/api/combine', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shapes: shapeIds,
                operation: operation
            })
        });

        const data = await response.json();

        if (data.success) {
            // Remove old shapes
            shapeIds.forEach(id => removeShapeFromScene(id));

            // Add combined shape
            await renderAndLoadSTL(data.result_id, 'combined', {});
            await updateShapesList();
            await updateAllOpenSCADCode();

            selectedShapes.clear();
            updateBooleanButtons();

            showStatus(`${operation} completed!`, 'success');
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

async function updateAllOpenSCADCode() {
    try {
        const response = await fetch('/parametric/api/shapes/list');
        const data = await response.json();

        if (data.success && data.shapes.length > 0) {
            let code = "// Generated by ZoolZ - Multi-Shape Scene\n\n";

            for (const shape of data.shapes) {
                const codeResponse = await fetch('/parametric/api/openscad/export', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ shape_id: shape.id })
                });

                const codeData = await codeResponse.json();
                if (codeData.success) {
                    code += codeData.code + '\n';
                }
            }

            openscadCode.textContent = code;
        } else {
            openscadCode.textContent = '// No shapes in scene';
        }
    } catch (error) {
        console.error('Error updating OpenSCAD code:', error);
    }
}

// Copy code button
copyCodeBtn.addEventListener('click', () => {
    const code = openscadCode.textContent;
    navigator.clipboard.writeText(code).then(() => {
        copyCodeBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyCodeBtn.textContent = 'Copy Code';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
});

// Export all button
exportAllBtn.addEventListener('click', async () => {
    const code = openscadCode.textContent;
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `zoolz_scene_${Date.now()}.scad`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showStatus('OpenSCAD file downloaded!', 'success');
});

function showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.style.display = 'block';

    if (type === 'success') {
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    }
}

// Initialize on load
window.addEventListener('load', initViewer);
