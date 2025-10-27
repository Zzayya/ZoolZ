// Parametric CAD 3D Viewer and Controller

let scene, camera, renderer, controls, mesh;
let currentShapeId = null;
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

function loadSTL(url) {
    const loader = new THREE.STLLoader();

    loader.load(url, function(geometry) {
        // Remove old mesh
        if (mesh) {
            scene.remove(mesh);
        }

        // Create material
        const material = new THREE.MeshPhongMaterial({
            color: 0x00c8ff,
            specular: 0x111111,
            shininess: 200,
            flatShading: false
        });

        // Create mesh
        mesh = new THREE.Mesh(geometry, material);

        // Center and scale
        geometry.computeBoundingBox();
        const center = geometry.boundingBox.getCenter(new THREE.Vector3());
        mesh.position.sub(center);

        // Add to scene
        scene.add(mesh);

        // Adjust camera
        const size = geometry.boundingBox.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const dist = maxDim * 2;
        camera.position.set(dist, dist, dist);
        controls.target.set(0, 0, 0);
        controls.update();
    }, undefined, function(error) {
        console.error('Error loading STL:', error);
        showStatus('Error loading 3D model', 'error');
    });
}

// Shape type selector
const shapeTypeSelect = document.getElementById('shapeType');
const paramsContainer = document.getElementById('params-container');
const generateBtn = document.getElementById('generateBtn');
const generateText = document.getElementById('generateText');
const downloadBtn = document.getElementById('downloadBtn');
const openscadCode = document.getElementById('openscadCode');
const shapeInfo = document.getElementById('shapeInfo');
const copyCodeBtn = document.getElementById('copyCodeBtn');

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
    generateText.textContent = 'Generate Shape';
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
    generateText.innerHTML = '<span class="spinner"></span> Generating...';
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
            currentShapeId = data.shape_id;
            showStatus('Shape generated successfully!', 'success');

            // Display OpenSCAD code
            openscadCode.textContent = data.openscad_code;

            // Display shape info
            displayShapeInfo(shapeType, params, data.preview);

            // Load preview (if available)
            // For now, export and load STL
            await renderAndLoadSTL(data.shape_id);

            downloadBtn.style.display = 'block';
            openScadBtn.style.display = 'block';
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
        generateText.textContent = 'Generate Shape';
    }
}

async function renderAndLoadSTL(shapeId) {
    try {
        const response = await fetch('/parametric/api/render', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shape_id: shapeId,
                filename: `shape_${shapeId}.stl`
            })
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            loadSTL(downloadUrl);
        } else {
            showStatus(`Error rendering: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Render error:', error);
    }
}

function displayShapeInfo(shapeType, params, preview) {
    let html = `<p><strong>Shape:</strong> ${shapeType.charAt(0).toUpperCase() + shapeType.slice(1)}</p>`;
    html += `<p><strong>Parameters:</strong></p><ul style="padding-left: 20px;">`;

    for (const [key, value] of Object.entries(params)) {
        html += `<li>${key}: ${value}</li>`;
    }

    html += '</ul>';

    if (preview) {
        const vertexCount = preview.vertices ? preview.vertices.length / 3 : 0;
        const faceCount = preview.faces ? preview.faces.length / 3 : 0;
        html += `<p style="margin-top: 10px;"><strong>Mesh Info:</strong></p>`;
        html += `<p>Vertices: ${vertexCount.toLocaleString()}</p>`;
        html += `<p>Faces: ${faceCount.toLocaleString()}</p>`;
    }

    shapeInfo.innerHTML = html;
}

// Download button
downloadBtn.addEventListener('click', () => {
    if (downloadUrl) {
        window.location.href = downloadUrl;
    }
});

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

// Open in OpenSCAD button
const openScadBtn = document.getElementById('openScadBtn');
openScadBtn.addEventListener('click', () => {
    const code = openscadCode.textContent;
    const shapeType = shapeTypeSelect.value || 'design';

    // Create a blob with the OpenSCAD code
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    // Create a temporary link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = `${shapeType}_${Date.now()}.scad`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showStatus('OpenSCAD file downloaded! Open it with OpenSCAD application.', 'success');
});

function showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.style.display = 'block';
}

// Initialize on load
window.addEventListener('load', initViewer);
