// ============================================================================
// UNDO/REDO SYSTEM - Track and reverse operations
// ============================================================================

let undoStack = [];
let redoStack = [];
const MAX_UNDO_STACK = 50;

// State snapshot structure
function captureState() {
    return {
        mesh: mesh ? {
            geometry: mesh.geometry.clone(),
            position: mesh.position.clone(),
            rotation: mesh.rotation.clone(),
            scale: mesh.scale.clone()
        } : null,
        sceneObjects: sceneObjects.map(obj => ({
            id: obj.id,
            name: obj.name,
            visible: obj.visible,
            locked: obj.locked,
            position: obj.mesh ? obj.mesh.position.clone() : null,
            rotation: obj.mesh ? obj.mesh.rotation.clone() : null,
            scale: obj.mesh ? obj.mesh.scale.clone() : null
        })),
        currentFile: currentFile,
        downloadUrl: downloadUrl,
        timestamp: Date.now()
    };
}

// Push state to undo stack
function pushUndoState(operation = 'operation') {
    const state = captureState();
    state.operation = operation;

    undoStack.push(state);

    // Limit stack size
    if (undoStack.length > MAX_UNDO_STACK) {
        undoStack.shift();
    }

    // Clear redo stack when new action is performed
    redoStack = [];

    updateUndoRedoButtons();
    console.log(`Undo state pushed: ${operation}`);
}

// Undo last operation
function undo() {
    if (undoStack.length === 0) {
        showNotification('Nothing to undo', 'info');
        return;
    }

    // Save current state to redo stack
    const currentState = captureState();
    redoStack.push(currentState);

    // Get previous state
    const previousState = undoStack.pop();

    // Restore state
    restoreState(previousState);

    updateUndoRedoButtons();
    showNotification(`Undid: ${previousState.operation}`, 'success');
}

// Redo last undone operation
function redo() {
    if (redoStack.length === 0) {
        showNotification('Nothing to redo', 'info');
        return;
    }

    // Save current state to undo stack
    const currentState = captureState();
    undoStack.push(currentState);

    // Get next state
    const nextState = redoStack.pop();

    // Restore state
    restoreState(nextState);

    updateUndoRedoButtons();
    showNotification(`Redid: ${nextState.operation}`, 'success');
}

// Restore a captured state
function restoreState(state) {
    // Restore main mesh
    if (state.mesh && mesh) {
        mesh.geometry.dispose();
        mesh.geometry = state.mesh.geometry.clone();
        mesh.position.copy(state.mesh.position);
        mesh.rotation.copy(state.mesh.rotation);
        mesh.scale.copy(state.mesh.scale);
    }

    // Restore scene objects
    // This is simplified - full implementation would need more complex scene management
    state.sceneObjects.forEach(savedObj => {
        const obj = sceneObjects.find(o => o.id === savedObj.id);
        if (obj && obj.mesh) {
            obj.visible = savedObj.visible;
            obj.locked = savedObj.locked;
            obj.mesh.visible = savedObj.visible;
            if (savedObj.position) obj.mesh.position.copy(savedObj.position);
            if (savedObj.rotation) obj.mesh.rotation.copy(savedObj.rotation);
            if (savedObj.scale) obj.mesh.scale.copy(savedObj.scale);
        }
    });

    updateSceneList();
}

// Update undo/redo button states
function updateUndoRedoButtons() {
    const undoBtn = document.getElementById('undoBtn');
    const redoBtn = document.getElementById('redoBtn');

    if (undoBtn) {
        undoBtn.disabled = undoStack.length === 0;
        undoBtn.title = undoStack.length > 0
            ? `Undo: ${undoStack[undoStack.length - 1].operation}`
            : 'Nothing to undo';
    }

    if (redoBtn) {
        redoBtn.disabled = redoStack.length === 0;
        redoBtn.title = redoStack.length > 0
            ? `Redo: ${redoStack[redoStack.length - 1].operation}`
            : 'Nothing to redo';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+Z or Cmd+Z for undo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
    }

    // Ctrl+Y or Cmd+Y or Ctrl+Shift+Z for redo
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        redo();
    }
});

// Clear undo/redo stacks
function clearUndoRedo() {
    undoStack = [];
    redoStack = [];
    updateUndoRedoButtons();
}

// Initialize
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        updateUndoRedoButtons();
    });
}
