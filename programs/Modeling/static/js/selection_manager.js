// ============================================================================
// SELECTION MANAGER - Smart object selection and highlight system
// ============================================================================

class SelectionManager {
    constructor() {
        this.selectedObjects = new Set(); // Can multi-select
        this.activeObject = null; // Primary selection (for settings)
        this.selectionColor = 0xffaa00; // Orange highlight
        this.normalColor = 0x00aaff; // Normal blue
        this.emissiveColor = 0x331100; // Glow for selected
        this.listeners = []; // Callbacks for selection change
    }

    // Select single object (clears previous selection)
    select(objectId) {
        this.clearSelection();
        this.addToSelection(objectId);
        this.activeObject = objectId;
        this.notifyListeners('select', objectId);
    }

    // Add to selection (multi-select with Ctrl/Cmd)
    addToSelection(objectId) {
        if (!objectId) return;

        const obj = sceneObjects.find(o => o.id === objectId);
        if (!obj || obj.locked) return;

        // Remove previous highlight
        if (this.activeObject && this.activeObject !== objectId) {
            this.unhighlightObject(this.activeObject);
        }

        this.selectedObjects.add(objectId);
        this.activeObject = objectId;
        this.highlightObject(objectId);

        this.notifyListeners('add', objectId);
    }

    // Remove from selection
    removeFromSelection(objectId) {
        this.selectedObjects.delete(objectId);
        this.unhighlightObject(objectId);

        // If this was active, set new active
        if (this.activeObject === objectId) {
            const remaining = Array.from(this.selectedObjects);
            this.activeObject = remaining.length > 0 ? remaining[0] : null;
            if (this.activeObject) {
                this.highlightObject(this.activeObject);
            }
        }

        this.notifyListeners('remove', objectId);
    }

    // Clear all selections
    clearSelection() {
        this.selectedObjects.forEach(id => {
            this.unhighlightObject(id);
        });
        this.selectedObjects.clear();
        this.activeObject = null;
        this.notifyListeners('clear');
    }

    // Toggle selection (for multi-select)
    toggleSelection(objectId) {
        if (this.selectedObjects.has(objectId)) {
            this.removeFromSelection(objectId);
        } else {
            this.addToSelection(objectId);
        }
    }

    // Check if object is selected
    isSelected(objectId) {
        return this.selectedObjects.has(objectId);
    }

    // Get active object (primary selection)
    getActiveObject() {
        return this.activeObject;
    }

    // Get all selected objects
    getSelectedObjects() {
        return Array.from(this.selectedObjects);
    }

    // Highlight object visually
    highlightObject(objectId) {
        const obj = sceneObjects.find(o => o.id === objectId);
        if (!obj || !obj.mesh) return;

        obj.mesh.material.color.setHex(this.selectionColor);
        obj.mesh.material.emissive.setHex(this.emissiveColor);

        // Add glow effect
        if (!obj.mesh.userData.outline) {
            const outlineGeometry = obj.mesh.geometry.clone();
            const outlineMaterial = new THREE.MeshBasicMaterial({
                color: 0xffaa00,
                side: THREE.BackSide,
                transparent: true,
                opacity: 0.3
            });
            const outline = new THREE.Mesh(outlineGeometry, outlineMaterial);
            outline.scale.multiplyScalar(1.02);
            obj.mesh.add(outline);
            obj.mesh.userData.outline = outline;
        }
    }

    // Remove highlight from object
    unhighlightObject(objectId) {
        const obj = sceneObjects.find(o => o.id === objectId);
        if (!obj || !obj.mesh) return;

        obj.mesh.material.color.setHex(this.normalColor);
        obj.mesh.material.emissive.setHex(0x000000);

        // Remove glow effect
        if (obj.mesh.userData.outline) {
            obj.mesh.remove(obj.mesh.userData.outline);
            obj.mesh.userData.outline.geometry.dispose();
            obj.mesh.userData.outline.material.dispose();
            delete obj.mesh.userData.outline;
        }
    }

    // Register listener for selection changes
    onSelectionChange(callback) {
        this.listeners.push(callback);
    }

    // Notify all listeners
    notifyListeners(action, objectId = null) {
        this.listeners.forEach(callback => {
            callback({
                action: action,
                objectId: objectId,
                selectedObjects: this.getSelectedObjects(),
                activeObject: this.activeObject
            });
        });
    }

    // Box select (select multiple objects in area)
    // Box select (select multiple objects in area)
    boxSelect(startX, startY, endX, endY) {
        if (!window.camera || !window.renderer) return;

        // Convert screen coordinates to normalized device coordinates
        const canvas = window.renderer.domElement;
        const rect = canvas.getBoundingClientRect();

        // Normalize coordinates (-1 to 1)
        const x1 = ((Math.min(startX, endX) - rect.left) / rect.width) * 2 - 1;
        const y1 = -((Math.min(startY, endY) - rect.top) / rect.height) * 2 + 1;
        const x2 = ((Math.max(startX, endX) - rect.left) / rect.width) * 2 - 1;
        const y2 = -((Math.max(startY, endY) - rect.top) / rect.height) * 2 + 1;

        // Check each object's screen position
        const vector = new THREE.Vector3();
        sceneObjects.forEach(obj => {
            if (obj.locked) return;

            // Project object center to screen space
            vector.setFromMatrixPosition(obj.mesh.matrixWorld);
            vector.project(window.camera);

            // Check if within selection box
            if (vector.x >= x1 && vector.x <= x2 && 
                vector.y >= y2 && vector.y <= y1) {
                this.selectedObjects.add(obj.id);
                this.highlightObject(obj.id);
            }
        });

        this.updateUI();
    }

    // Select all
    selectAll() {
        this.clearSelection();
        sceneObjects.forEach(obj => {
            if (!obj.locked) {
                this.selectedObjects.add(obj.id);
                this.highlightObject(obj.id);
            }
        });
        this.activeObject = sceneObjects.length > 0 ? sceneObjects[0].id : null;
        this.notifyListeners('selectAll');
    }

    // Invert selection
    invertSelection() {
        const currentSelection = new Set(this.selectedObjects);
        this.clearSelection();

        sceneObjects.forEach(obj => {
            if (!obj.locked && !currentSelection.has(obj.id)) {
                this.selectedObjects.add(obj.id);
                this.highlightObject(obj.id);
            }
        });

        this.activeObject = this.selectedObjects.size > 0
            ? Array.from(this.selectedObjects)[0]
            : null;

        this.notifyListeners('invertSelection');
    }

    // Get selection info for UI
    getSelectionInfo() {
        if (this.selectedObjects.size === 0) {
            return { count: 0, text: 'Nothing selected' };
        } else if (this.selectedObjects.size === 1) {
            const obj = sceneObjects.find(o => o.id === this.activeObject);
            return {
                count: 1,
                text: `Selected: ${obj ? obj.name : 'Unknown'}`,
                object: obj
            };
        } else {
            return {
                count: this.selectedObjects.size,
                text: `Selected: ${this.selectedObjects.size} objects`
            };
        }
    }
}

// Tool Settings Manager - Knows which object settings apply to
class ToolSettingsManager {
    constructor() {
        this.currentTool = null;
        this.settings = new Map(); // Tool-specific settings
        this.targetMode = 'new'; // 'new' or 'selected'
    }

    // Set current tool
    setTool(toolName) {
        this.currentTool = toolName;
        console.log(`Tool changed to: ${toolName}`);
    }

    // Get current tool
    getTool() {
        return this.currentTool;
    }

    // Set setting for current tool
    setSetting(key, value) {
        if (!this.currentTool) return;

        if (!this.settings.has(this.currentTool)) {
            this.settings.set(this.currentTool, {});
        }

        this.settings.get(this.currentTool)[key] = value;
    }

    // Get setting for current tool
    getSetting(key, defaultValue = null) {
        if (!this.currentTool) return defaultValue;

        const toolSettings = this.settings.get(this.currentTool);
        return toolSettings && toolSettings[key] !== undefined
            ? toolSettings[key]
            : defaultValue;
    }

    // Get all settings for current tool
    getAllSettings() {
        if (!this.currentTool) return {};
        return this.settings.get(this.currentTool) || {};
    }

    // Determine if settings apply to selected object or new generation
    getTargetMode() {
        const activeObject = selectionManager.getActiveObject();
        if (activeObject) {
            return 'selected'; // Modify selected object
        } else {
            return 'new'; // Generate new object
        }
    }

    // Get target object for tool operation
    getTargetObject() {
        const mode = this.getTargetMode();
        if (mode === 'selected') {
            const objectId = selectionManager.getActiveObject();
            return sceneObjects.find(o => o.id === objectId);
        }
        return null;
    }
}

// Global instances
const selectionManager = new SelectionManager();
const toolSettingsManager = new ToolSettingsManager();

// Hook into scene manager's selectObject function
const originalSelectObject = selectObject;
selectObject = function(objectId) {
    originalSelectObject(objectId);
    selectionManager.select(objectId);
};

// Keyboard shortcuts for selection
document.addEventListener('keydown', (e) => {
    // Don't trigger if typing in input
    if (document.activeElement.tagName === 'INPUT' ||
        document.activeElement.tagName === 'TEXTAREA') {
        return;
    }

    // Ctrl/Cmd + A: Select all
    if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault();
        selectionManager.selectAll();
    }

    // Ctrl/Cmd + Shift + I: Invert selection
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'i') {
        e.preventDefault();
        selectionManager.invertSelection();
    }

    // Escape: Clear selection
    if (e.key === 'Escape') {
        selectionManager.clearSelection();
    }
});

// Update UI based on selection changes
selectionManager.onSelectionChange((event) => {
    console.log('Selection changed:', event);

    // Update status bar
    const statusEl = document.getElementById('selectionStatus');
    if (statusEl) {
        const info = selectionManager.getSelectionInfo();
        statusEl.textContent = info.text;
    }

    // Update tool settings windows (if open)
    updateToolSettingsUI();
});

// Update tool settings UI based on selection
function updateToolSettingsUI() {
    const mode = toolSettingsManager.getTargetMode();
    const targetObject = toolSettingsManager.getTargetObject();

    // Update all open tool windows with mode indicator
    windowManager.windows.forEach((window, id) => {
        if (id.startsWith('tool-')) {
            // Add mode indicator to window
            let modeIndicator = window.element.querySelector('.tool-mode-indicator');
            if (!modeIndicator) {
                modeIndicator = document.createElement('div');
                modeIndicator.className = 'tool-mode-indicator';
                modeIndicator.style.cssText = `
                    padding: 8px 12px;
                    background: rgba(0, 149, 255, 0.1);
                    border-bottom: 1px solid rgba(0, 149, 255, 0.2);
                    font-size: 12px;
                    color: #00c8ff;
                    text-align: center;
                `;
                window.bodyElement.insertBefore(modeIndicator, window.bodyElement.firstChild);
            }

            if (mode === 'selected' && targetObject) {
                modeIndicator.textContent = `🎯 Modifying: ${targetObject.name}`;
                modeIndicator.style.background = 'rgba(255, 170, 0, 0.1)';
                modeIndicator.style.borderColor = 'rgba(255, 170, 0, 0.3)';
                modeIndicator.style.color = '#ffaa00';
            } else {
                modeIndicator.textContent = '✨ Creating New Object';
                modeIndicator.style.background = 'rgba(0, 149, 255, 0.1)';
                modeIndicator.style.borderColor = 'rgba(0, 149, 255, 0.2)';
                modeIndicator.style.color = '#00c8ff';
            }
        }
    });
}
