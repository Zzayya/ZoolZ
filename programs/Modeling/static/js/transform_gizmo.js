// ============================================================================
// TRANSFORM GIZMO - Visual manipulation handles for objects
// ============================================================================

let transformControls = null;
let transformMode = 'translate'; // translate, rotate, scale

// Initialize transform controls
function initTransformControls() {
    if (!scene || !camera || !renderer) {
        console.error('Cannot init transform controls: missing scene/camera/renderer');
        return;
    }

    // Load TransformControls from Three.js examples
    if (typeof THREE.TransformControls === 'undefined') {
        console.warn('TransformControls not loaded, using precision inputs only');
        return;
    }

    transformControls = new THREE.TransformControls(camera, renderer.domElement);

    // Set initial mode
    transformControls.setMode(transformMode);
    transformControls.setSize(0.8); // Smaller handles

    // Add to scene
    scene.add(transformControls);

    // Disable orbit controls while transforming
    transformControls.addEventListener('dragging-changed', (event) => {
        if (controls) {
            controls.enabled = !event.value;
        }
    });

    // Update object position when transform changes
    transformControls.addEventListener('objectChange', () => {
        if (transformControls.object && selectedObjectId) {
            const obj = sceneObjects.find(o => o.id === selectedObjectId);
            if (obj) {
                obj.position = {
                    x: transformControls.object.position.x,
                    y: transformControls.object.position.y,
                    z: transformControls.object.position.z
                };
                obj.rotation = {
                    x: transformControls.object.rotation.x,
                    y: transformControls.object.rotation.y,
                    z: transformControls.object.rotation.z
                };
                obj.scale = {
                    x: transformControls.object.scale.x,
                    y: transformControls.object.scale.y,
                    z: transformControls.object.scale.z
                };

                // Update precision inputs
                updateObjectProperties(selectedObjectId);
            }
        }
    });

    console.log('Transform controls initialized');
}

// Attach transform controls to object
function attachTransformControls(mesh) {
    if (!transformControls) {
        console.warn('Transform controls not available');
        return;
    }

    transformControls.attach(mesh);

    // Show transform controls UI
    const transformUI = document.getElementById('transformControls');
    if (transformUI) {
        transformUI.style.display = 'block';
    }

    // Update mode buttons
    updateTransformModeButtons();
}

// Detach transform controls
function detachTransformControls() {
    if (!transformControls) return;

    transformControls.detach();

    // Hide transform controls UI
    const transformUI = document.getElementById('transformControls');
    if (transformUI) {
        transformUI.style.display = 'none';
    }
}

// Set transform mode
function setTransformMode(mode) {
    transformMode = mode;

    if (transformControls) {
        transformControls.setMode(mode);
    }

    updateTransformModeButtons();
    showNotification(`Transform mode: ${mode}`, 'info');
}

// Update mode button states
function updateTransformModeButtons() {
    const modes = ['translate', 'rotate', 'scale'];
    modes.forEach(mode => {
        const btn = document.getElementById(`transformMode_${mode}`);
        if (btn) {
            if (mode === transformMode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    });
}

// Toggle transform space (local vs world)
function toggleTransformSpace() {
    if (!transformControls) return;

    const currentSpace = transformControls.space;
    const newSpace = currentSpace === 'world' ? 'local' : 'world';

    transformControls.setSpace(newSpace);
    showNotification(`Transform space: ${newSpace}`, 'info');
}

// Snap to grid toggle
let snapToGrid = false;
let gridSize = 5; // mm

function toggleSnapToGrid() {
    snapToGrid = !snapToGrid;

    if (transformControls) {
        if (snapToGrid) {
            transformControls.setTranslationSnap(gridSize);
            transformControls.setRotationSnap(THREE.MathUtils.degToRad(15));
            transformControls.setScaleSnap(0.1);
            showNotification(`Snap to grid: ${gridSize}mm`, 'success');
        } else {
            transformControls.setTranslationSnap(null);
            transformControls.setRotationSnap(null);
            transformControls.setScaleSnap(null);
            showNotification('Snap to grid: OFF', 'info');
        }
    }
}

// Keyboard shortcuts for transform
document.addEventListener('keydown', (event) => {
    // Only handle if no input is focused
    if (document.activeElement.tagName === 'INPUT' ||
        document.activeElement.tagName === 'TEXTAREA') {
        return;
    }

    switch(event.key.toLowerCase()) {
        case 'g': // Move (like Blender)
            setTransformMode('translate');
            break;
        case 'r': // Rotate
            setTransformMode('rotate');
            break;
        case 's': // Scale
            setTransformMode('scale');
            break;
        case 'delete':
        case 'backspace':
            if (selectedObjectId && event.shiftKey) {
                event.preventDefault();
                removeObjectFromScene(selectedObjectId);
            }
            break;
        case 'd':
            if (selectedObjectId && event.shiftKey) {
                event.preventDefault();
                duplicateObject(selectedObjectId);
            }
            break;
        case 'h':
            if (selectedObjectId) {
                event.preventDefault();
                toggleObjectVisibility(selectedObjectId);
            }
            break;
    }
});

// Align objects
function alignObjects(axis, direction) {
    if (!selectedObjectId) return;

    const obj = sceneObjects.find(o => o.id === selectedObjectId);
    if (!obj || !obj.mesh) return;

    const bounds = new THREE.Box3().setFromObject(obj.mesh);
    const size = bounds.getSize(new THREE.Vector3());

    if (axis === 'y' && direction === 'bottom') {
        // Snap to plate (Y = 0)
        const offset = bounds.min.y;
        obj.mesh.position.y -= offset;
    } else if (axis === 'center') {
        // Center on build plate
        const center = bounds.getCenter(new THREE.Vector3());
        obj.mesh.position.x -= center.x;
        obj.mesh.position.z -= center.z;
    }

    updateObjectProperties(selectedObjectId);
    showNotification(`Aligned to ${direction}`, 'success');
}

// Focus camera on selected object
function focusOnSelected() {
    if (!selectedObjectId) return;

    const obj = sceneObjects.find(o => o.id === selectedObjectId);
    if (!obj || !obj.mesh) return;

    const bounds = new THREE.Box3().setFromObject(obj.mesh);
    const center = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);

    // Move camera to look at object
    const distance = maxDim * 2;
    camera.position.set(
        center.x + distance,
        center.y + distance,
        center.z + distance
    );

    if (controls) {
        controls.target.copy(center);
        controls.update();
    }

    showNotification('Focused on object', 'success');
}

// Toggle transform controls body visibility
function toggleTransformBody() {
    const body = document.getElementById('transformControlsBody');
    if (!body) return;

    if (body.style.display === 'none') {
        body.style.display = 'block';
    } else {
        body.style.display = 'none';
    }
}

// Initialize on load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // Wait for scene to be created
        setTimeout(() => {
            initTransformControls();
        }, 1000);
    });
}
