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

    // Grid - positioned at y=0 (horizontal plane, build plate level)
    const gridHelper = new THREE.GridHelper(200, 20, 0x0095ff, 0x003366);
    gridHelper.position.y = 0; // Ensure it's at ground level
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
