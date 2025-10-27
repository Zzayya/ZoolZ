// Cookie Cutter 3D Viewer and Controller

let scene, camera, renderer, controls, mesh;
let currentFile = null;
let downloadUrl = null;

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

    // Grid
    const gridHelper = new THREE.GridHelper(200, 20, 0x0095ff, 0x003366);
    scene.add(gridHelper);

    // Axes
    const axesHelper = new THREE.AxesHelper(50);
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
            color: 0x0095ff,
            specular: 0x111111,
            shininess: 200,
            flatShading: false
        });

        // Create mesh
        mesh = new THREE.Mesh(geometry, material);

        // Position on build plate (bottom at z=0, centered in XY)
        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        const centerX = (bbox.min.x + bbox.max.x) / 2;
        const centerY = (bbox.min.y + bbox.max.y) / 2;
        const minZ = bbox.min.z;

        // Move so bottom sits on z=0 and centered in XY
        mesh.position.set(-centerX, -centerY, -minZ);

        // Add to scene
        scene.add(mesh);

        // Adjust camera
        const size = geometry.boundingBox.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const modelHeight = size.z;
        camera.position.set(maxDim, maxDim, maxDim);
        controls.target.set(0, 0, modelHeight / 2);  // Look at center of model
        controls.update();
    }, undefined, function(error) {
        console.error('Error loading STL:', error);
        showStatus('Error loading 3D model', 'error');
    });
}

// File upload handling
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const generateBtn = document.getElementById('generateBtn');
const generateText = document.getElementById('generateText');
const downloadBtn = document.getElementById('downloadBtn');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showStatus('Please upload an image file', 'error');
        return;
    }

    currentFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    // Enable generate button
    generateBtn.disabled = false;
    generateText.textContent = 'Generate Cookie Cutter';
}

// Parameter updates
const params = {
    detailLevel: document.getElementById('detailLevel'),
    bladeThick: document.getElementById('bladeThick'),
    bladeHeight: document.getElementById('bladeHeight'),
    baseThick: document.getElementById('baseThick'),
    baseExtra: document.getElementById('baseExtra'),
    maxDim: document.getElementById('maxDim'),
    noBase: document.getElementById('noBase')
};

// Update value displays
params.detailLevel.addEventListener('input', (e) => {
    document.getElementById('detailValue').textContent = (e.target.value / 100).toFixed(2);
});

params.bladeThick.addEventListener('input', (e) => {
    document.getElementById('bladeThickValue').textContent = parseFloat(e.target.value).toFixed(1);
});

params.bladeHeight.addEventListener('input', (e) => {
    document.getElementById('bladeHeightValue').textContent = parseFloat(e.target.value).toFixed(1);
});

params.baseThick.addEventListener('input', (e) => {
    document.getElementById('baseThickValue').textContent = parseFloat(e.target.value).toFixed(1);
});

params.baseExtra.addEventListener('input', (e) => {
    document.getElementById('baseExtraValue').textContent = parseFloat(e.target.value).toFixed(1);
});

params.maxDim.addEventListener('input', (e) => {
    document.getElementById('maxDimValue').textContent = e.target.value;
});

// Generate button
generateBtn.addEventListener('click', generateCookieCutter);

async function generateCookieCutter() {
    if (!currentFile) {
        showStatus('Please upload an image first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('image', currentFile);
    formData.append('detail_level', params.detailLevel.value / 100);
    formData.append('blade_thick', params.bladeThick.value);
    formData.append('blade_height', params.bladeHeight.value);
    formData.append('base_thick', params.baseThick.value);
    formData.append('base_extra', params.baseExtra.value);
    formData.append('max_dim', params.maxDim.value);
    formData.append('no_base', params.noBase.checked);

    generateBtn.disabled = true;
    generateText.innerHTML = '<span class="spinner"></span> Generating...';
    showStatus('Processing image and generating 3D model...', 'processing');

    try {
        const response = await fetch('/cookie/api/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus('Cookie cutter generated successfully!', 'success');
            showStats(data.stats);
            downloadBtn.style.display = 'block';
            snapBtn.style.display = 'block';
            curaBtn.style.display = 'block';

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

// Download button
downloadBtn.addEventListener('click', () => {
    if (downloadUrl) {
        window.location.href = downloadUrl;
    }
});

function showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.style.display = 'block';
}

function showStats(stats) {
    const statsEl = document.getElementById('stats');
    statsEl.innerHTML = `
        <div class="stat-box">
            <div class="stat-label">Vertices</div>
            <div class="stat-value">${stats.vertices.toLocaleString()}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Faces</div>
            <div class="stat-value">${stats.faces.toLocaleString()}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Watertight</div>
            <div class="stat-value">${stats.is_watertight ? '✓' : '✗'}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Ready</div>
            <div class="stat-value">Print</div>
        </div>
    `;
    statsEl.style.display = 'grid';
}

// Model control buttons
const rotateLeftBtn = document.getElementById('rotateLeft');
const rotateRightBtn = document.getElementById('rotateRight');
const rotationDegreesInput = document.getElementById('rotationDegrees');
const snapBtn = document.getElementById('snapBtn');
const curaBtn = document.getElementById('curaBtn');

// Rotation controls
rotateLeftBtn.addEventListener('click', () => {
    if (mesh) {
        const degrees = parseFloat(rotationDegreesInput.value) || 90;
        const radians = (degrees * Math.PI) / 180;
        mesh.rotation.z += radians;
    }
});

rotateRightBtn.addEventListener('click', () => {
    if (mesh) {
        const degrees = parseFloat(rotationDegreesInput.value) || 90;
        const radians = (degrees * Math.PI) / 180;
        mesh.rotation.z -= radians;
    }
});

// Snap to build plate
snapBtn.addEventListener('click', () => {
    if (mesh) {
        // Reset rotation and position
        mesh.rotation.set(0, 0, 0);

        // Recalculate position to sit on build plate
        mesh.geometry.computeBoundingBox();
        const bbox = mesh.geometry.boundingBox;
        const centerX = (bbox.min.x + bbox.max.x) / 2;
        const centerY = (bbox.min.y + bbox.max.y) / 2;
        const minZ = bbox.min.z;
        mesh.position.set(-centerX, -centerY, -minZ);

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
