// ============================================================================
// ADVANCED TOOL FUNCTIONS - Boolean, Split, Measure, Array
// ============================================================================

// Boolean Operations
let secondMeshFile = null;

document.addEventListener('DOMContentLoaded', () => {
    const booleanMesh2Input = document.getElementById('booleanMesh2');
    if (booleanMesh2Input) {
        booleanMesh2Input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                secondMeshFile = e.target.files[0];
                const mesh2Info = document.getElementById('mesh2Info');
                const applyBtn = document.getElementById('applyBooleanBtn');

                mesh2Info.textContent = `Second mesh loaded: ${secondMeshFile.name}`;
                mesh2Info.style.display = 'block';
                applyBtn.disabled = false;
            }
        });
    }
});

async function applyBoolean() {
    if (!currentFile) {
        showNotification('Please load first mesh', 'error');
        return;
    }

    if (!secondMeshFile) {
        showNotification('Please load second mesh', 'error');
        return;
    }

    const operation = document.getElementById('booleanOp').value;

    const formData = new FormData();
    formData.append('mesh1', currentFile);
    formData.append('mesh2', secondMeshFile);
    formData.append('operation', operation);

    showNotification('Performing boolean operation...', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/boolean', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showNotification('Boolean ' + operation + ' complete!', 'success');
            showStats(data.stats);
            loadSTL(downloadUrl);

            document.getElementById('downloadBtn').style.display = 'inline-flex';
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// Split/Cut Tool
async function applySplit() {
    if (!mesh) {
        showNotification('Please load a model first', 'error');
        return;
    }

    const splitAxis = document.querySelector('input[name="splitAxis"]:checked').value;
    const splitPosition = parseFloat(document.getElementById('splitPosition').value);
    const keepPart = document.getElementById('splitKeepPart').value;

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('plane_axis', splitAxis);
    formData.append('plane_position', splitPosition);
    formData.append('keep_part', keepPart);

    showNotification('Splitting model...', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/split', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            if (data.download_urls.length > 0) {
                downloadUrl = data.download_urls[0];  // Load first part
                loadSTL(downloadUrl);

                showNotification('Split complete! ' + data.parts_created + ' part(s) created', 'success');
                document.getElementById('downloadBtn').style.display = 'inline-flex';

                // If both parts, show info
                if (data.parts_created === 2) {
                    console.log('Second part:', data.download_urls[1]);
                }
            }
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// Measurement Tool
let measurementPoints = [];
let measurementMarkers = [];

function onViewerClickForMeasurement(event) {
    if (currentTool !== 'measure' || !mesh) return;

    const rect = renderer.domElement.getBoundingClientRect();
    const mx = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    const my = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    const tempMouse = new THREE.Vector2(mx, my);
    raycaster.setFromCamera(tempMouse, camera);
    const intersects = raycaster.intersectObject(mesh);

    if (intersects.length > 0) {
        const point = intersects[0].point;
        measurementPoints.push(point);

        // Add visual marker
        const marker = new THREE.Mesh(
            new THREE.SphereGeometry(1, 16, 16),
            new THREE.MeshBasicMaterial({ color: 0x00ff00 })
        );
        marker.position.copy(point);
        scene.add(marker);
        measurementMarkers.push(marker);

        // If we have two points, calculate distance
        if (measurementPoints.length === 2) {
            const distance = measurementPoints[0].distanceTo(measurementPoints[1]);
            document.getElementById('measureDistance').textContent = distance.toFixed(2);

            // Draw line between points
            const lineGeometry = new THREE.BufferGeometry().setFromPoints(measurementPoints);
            const lineMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 2 });
            const line = new THREE.Line(lineGeometry, lineMaterial);
            scene.add(line);
            measurementMarkers.push(line);

            showNotification('Distance: ' + distance.toFixed(2) + ' mm', 'success');
        }
    }
}

function clearMeasurement() {
    measurementPoints = [];
    measurementMarkers.forEach(marker => scene.remove(marker));
    measurementMarkers = [];
    document.getElementById('measureDistance').textContent = '--';
    showNotification('Measurement cleared', 'success');
}

// Array/Pattern Tool
function updateArrayParams() {
    const arrayType = document.getElementById('arrayType').value;
    const linearParams = document.getElementById('linearArrayParams');
    const circularParams = document.getElementById('circularArrayParams');

    if (arrayType === 'linear') {
        linearParams.style.display = 'block';
        circularParams.style.display = 'none';
    } else {
        linearParams.style.display = 'none';
        circularParams.style.display = 'block';
    }
}

async function applyArray() {
    if (!mesh) {
        showNotification('Please load a model first', 'error');
        return;
    }

    const arrayType = document.getElementById('arrayType').value;
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('array_type', arrayType);

    if (arrayType === 'linear') {
        formData.append('count_x', document.getElementById('arrayCountX').value);
        formData.append('count_y', document.getElementById('arrayCountY').value);
        formData.append('spacing_x', document.getElementById('arraySpacingX').value);
        formData.append('spacing_y', document.getElementById('arraySpacingY').value);
    } else {
        formData.append('count', document.getElementById('arrayCircularCount').value);
        formData.append('radius', document.getElementById('arrayRadius').value);
        formData.append('rotate_to_center', document.getElementById('arrayRotateToCenter').checked);
    }

    showNotification('Creating array pattern...', 'processing');

    try {
        const response = await fetch('/modeling/api/stl/array', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showNotification('Array created with ' + data.stats.copies_created + ' copies!', 'success');
            showStats(data.stats);
            loadSTL(downloadUrl);

            document.getElementById('downloadBtn').style.display = 'inline-flex';
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}
