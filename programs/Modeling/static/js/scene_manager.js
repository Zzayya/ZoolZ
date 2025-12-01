// ============================================================================
// SCENE MANAGER - Multi-object scene hierarchy and management
// ============================================================================

// Scene objects storage
let sceneObjects = [];
let selectedObjectId = null;
let objectIdCounter = 0;

// Initialize scene manager
function initSceneManager() {
    console.log('Scene Manager initialized');
    updateSceneList();
}

// Add object to scene
function addObjectToScene(name, url, meshData = null) {
    const objectId = `obj_${objectIdCounter++}`;

    const sceneObject = {
        id: objectId,
        name: name || `Object ${objectIdCounter}`,
        url: url,
        mesh: meshData || null,
        visible: true,
        locked: false,
        position: { x: 0, y: 0, z: 0 },
        rotation: { x: 0, y: 0, z: 0 },
        scale: { x: 1, y: 1, z: 1 }
    };

    sceneObjects.push(sceneObject);

    // If mesh data provided, add to Three.js scene
    if (meshData) {
        meshData.userData.objectId = objectId;
        scene.add(meshData);
    } else if (url) {
        // Load mesh from URL
        loadSTLForObject(url, objectId);
    }

    updateSceneList();
    selectObject(objectId);

    showNotification(`Added "${sceneObject.name}" to scene`, 'success');

    return objectId;
}

// Load STL for specific object
function loadSTLForObject(url, objectId) {
    const loader = new THREE.STLLoader();

    loader.load(url, (geometry) => {
        const material = new THREE.MeshPhongMaterial({
            color: 0x00aaff,
            specular: 0x111111,
            shininess: 200,
            flatShading: false
        });

        const objectMesh = new THREE.Mesh(geometry, material);
        objectMesh.userData.objectId = objectId;

        // Center geometry
        geometry.center();

        // Find object in array and update
        const obj = sceneObjects.find(o => o.id === objectId);
        if (obj) {
            obj.mesh = objectMesh;
            scene.add(objectMesh);
        }

        updateSceneList();
    });
}

// Remove object from scene
function removeObjectFromScene(objectId) {
    const index = sceneObjects.findIndex(o => o.id === objectId);
    if (index === -1) return;

    const obj = sceneObjects[index];

    // Remove mesh from Three.js scene
    if (obj.mesh) {
        scene.remove(obj.mesh);
        obj.mesh.geometry.dispose();
        obj.mesh.material.dispose();
    }

    // Remove from array
    sceneObjects.splice(index, 1);

    // Deselect if this was selected
    if (selectedObjectId === objectId) {
        selectedObjectId = null;
    }

    updateSceneList();
    showNotification(`Removed "${obj.name}"`, 'success');
}

// Select object
function selectObject(objectId) {
    // Deselect previous
    if (selectedObjectId) {
        const prevObj = sceneObjects.find(o => o.id === selectedObjectId);
        if (prevObj && prevObj.mesh) {
            prevObj.mesh.material.color.setHex(0x00aaff);
            prevObj.mesh.material.emissive.setHex(0x000000);
        }
    }

    selectedObjectId = objectId;

    // Highlight new selection
    const obj = sceneObjects.find(o => o.id === objectId);
    if (obj && obj.mesh) {
        obj.mesh.material.color.setHex(0xffaa00);
        obj.mesh.material.emissive.setHex(0x331100);

        // Show transform controls if available
        if (typeof attachTransformControls === 'function') {
            attachTransformControls(obj.mesh);
        }
    }

    updateSceneList();
    updateObjectProperties(objectId);
}

// Toggle object visibility
function toggleObjectVisibility(objectId) {
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj) return;

    obj.visible = !obj.visible;

    if (obj.mesh) {
        obj.mesh.visible = obj.visible;
    }

    updateSceneList();
}

// Toggle object lock
function toggleObjectLock(objectId) {
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj) return;

    obj.locked = !obj.locked;

    // Lock prevents selection and transform
    updateSceneList();
}

// Rename object
function renameObject(objectId, newName) {
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj) return;

    obj.name = newName || `Object ${objectIdCounter}`;
    updateSceneList();
}

// Duplicate object
function duplicateObject(objectId) {
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj) return;

    const newObjectId = `obj_${objectIdCounter++}`;

    // Clone object
    const clonedObj = {
        id: newObjectId,
        name: `${obj.name} Copy`,
        url: obj.url,
        mesh: null,
        visible: true,
        locked: false,
        position: { x: obj.position.x + 20, y: obj.position.y, z: obj.position.z },
        rotation: { ...obj.rotation },
        scale: { ...obj.scale }
    };

    sceneObjects.push(clonedObj);

    // Clone mesh if exists
    if (obj.mesh) {
        const clonedMesh = obj.mesh.clone();
        clonedMesh.material = obj.mesh.material.clone();
        clonedMesh.userData.objectId = newObjectId;
        clonedMesh.position.set(clonedObj.position.x, clonedObj.position.y, clonedObj.position.z);

        clonedObj.mesh = clonedMesh;
        scene.add(clonedMesh);
    }

    updateSceneList();
    selectObject(newObjectId);

    showNotification(`Duplicated "${obj.name}"`, 'success');
}

// Update scene list UI
function updateSceneList() {
    const listContainer = document.getElementById('sceneObjectsList');
    if (!listContainer) return;

    if (sceneObjects.length === 0) {
        listContainer.innerHTML = '<div class="scene-empty">No objects in scene</div>';
        return;
    }

    listContainer.innerHTML = '';

    sceneObjects.forEach(obj => {
        const item = document.createElement('div');
        item.className = 'scene-object-item';
        if (obj.id === selectedObjectId) {
            item.classList.add('selected');
        }
        if (!obj.visible) {
            item.classList.add('hidden');
        }

        item.innerHTML = `
            <div class="scene-object-info" onclick="selectObject('${obj.id}')">
                <span class="scene-object-icon">${obj.locked ? '🔒' : '📦'}</span>
                <span class="scene-object-name" ondblclick="startRename('${obj.id}')" title="${obj.name}">
                    ${obj.name}
                </span>
            </div>
            <div class="scene-object-actions">
                <button class="scene-action-btn" onclick="toggleObjectVisibility('${obj.id}')" title="Toggle visibility">
                    ${obj.visible ? '👁️' : '👁️‍🗨️'}
                </button>
                <button class="scene-action-btn" onclick="toggleObjectLock('${obj.id}')" title="Lock/Unlock">
                    ${obj.locked ? '🔒' : '🔓'}
                </button>
                <button class="scene-action-btn" onclick="duplicateObject('${obj.id}')" title="Duplicate">
                    📋
                </button>
                <button class="scene-action-btn scene-delete-btn" onclick="removeObjectFromScene('${obj.id}')" title="Delete">
                    🗑️
                </button>
            </div>
        `;

        listContainer.appendChild(item);
    });

    // Update count
    const countEl = document.getElementById('sceneObjectCount');
    if (countEl) {
        countEl.textContent = sceneObjects.length;
    }
}

// Start rename mode
function startRename(objectId) {
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj || obj.locked) return;

    const newName = prompt('Rename object:', obj.name);
    if (newName && newName.trim() !== '') {
        renameObject(objectId, newName.trim());
    }
}

// Update object properties panel
function updateObjectProperties(objectId) {
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj) return;

    // Update transform inputs if they exist
    const posX = document.getElementById('objPosX');
    const posY = document.getElementById('objPosY');
    const posZ = document.getElementById('objPosZ');

    if (posX && obj.mesh) {
        posX.value = obj.mesh.position.x.toFixed(2);
        posY.value = obj.mesh.position.y.toFixed(2);
        posZ.value = obj.mesh.position.z.toFixed(2);
    }

    const scaleUniform = document.getElementById('objScaleUniform');
    if (scaleUniform && obj.mesh) {
        scaleUniform.value = obj.mesh.scale.x.toFixed(2);
    }
}

// Apply position from inputs
function applyObjectPosition() {
    if (!selectedObjectId) return;

    const obj = sceneObjects.find(o => o.id === selectedObjectId);
    if (!obj || !obj.mesh) return;

    const x = parseFloat(document.getElementById('objPosX').value) || 0;
    const y = parseFloat(document.getElementById('objPosY').value) || 0;
    const z = parseFloat(document.getElementById('objPosZ').value) || 0;

    obj.mesh.position.set(x, y, z);
    obj.position = { x, y, z };

    showNotification('Position updated', 'success');
}

// Apply rotation from inputs
function applyObjectRotation() {
    if (!selectedObjectId) return;

    const obj = sceneObjects.find(o => o.id === selectedObjectId);
    if (!obj || !obj.mesh) return;

    const x = (parseFloat(document.getElementById('objRotX').value) || 0) * Math.PI / 180;
    const y = (parseFloat(document.getElementById('objRotY').value) || 0) * Math.PI / 180;
    const z = (parseFloat(document.getElementById('objRotZ').value) || 0) * Math.PI / 180;

    obj.mesh.rotation.set(x, y, z);
    obj.rotation = { x, y, z };

    showNotification('Rotation updated', 'success');
}

// Apply scale from inputs
function applyObjectScale() {
    if (!selectedObjectId) return;

    const obj = sceneObjects.find(o => o.id === selectedObjectId);
    if (!obj || !obj.mesh) return;

    const uniform = parseFloat(document.getElementById('objScaleUniform').value) || 1;

    obj.mesh.scale.set(uniform, uniform, uniform);
    obj.scale = { x: uniform, y: uniform, z: uniform };

    showNotification('Scale updated', 'success');
}

// Fuse all visible objects
async function fuseAllObjects() {
    const visibleObjects = sceneObjects.filter(o => o.visible && o.mesh);

    if (visibleObjects.length < 2) {
        showNotification('Need at least 2 visible objects to fuse', 'error');
        return;
    }

    showNotification('Fusing objects...', 'processing');

    // For now, use Boolean union on first two objects
    // In future, can chain multiple boolean operations

    try {
        // This would need backend support for multi-mesh boolean
        // For now, show placeholder
        showNotification('Multi-object fusion coming soon!', 'info');

        // TODO: Implement backend route for multi-object boolean operations
    } catch (error) {
        showNotification('Fusion error: ' + error.message, 'error');
    }
}

// Clear all objects
function clearScene() {
    if (sceneObjects.length === 0) return;

    if (!confirm(`Clear all ${sceneObjects.length} objects from scene?`)) {
        return;
    }

    // Remove all meshes
    sceneObjects.forEach(obj => {
        if (obj.mesh) {
            scene.remove(obj.mesh);
            obj.mesh.geometry.dispose();
            obj.mesh.material.dispose();
        }
    });

    sceneObjects = [];
    selectedObjectId = null;

    updateSceneList();
    showNotification('Scene cleared', 'success');
}

// Export all objects as single STL
async function exportSceneAsSTL() {
    if (sceneObjects.length === 0) {
        showNotification('No objects to export', 'error');
        return;
    }

    // Combine all visible meshes and export
    // This needs backend support
    showNotification('Scene export coming soon!', 'info');
}

// Toggle scene panel
function toggleScenePanel() {
    const panel = document.getElementById('scenePanel');
    if (!panel) return;

    if (panel.style.display === 'none') {
        panel.style.display = 'flex';
    } else {
        panel.style.display = 'none';
    }
}

// Initialize on load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        initSceneManager();
    });
}
