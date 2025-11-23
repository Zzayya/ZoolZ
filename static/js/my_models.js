// ============================================================================
// MY MODELS - User's saved models library
// ============================================================================

let myModelsList = [];

// Open My Models panel
function openMyModels() {
    const panel = document.getElementById('myModelsPanel');
    if (!panel) return;

    // Show panel
    panel.classList.add('visible');

    // Load models list
    loadMyModelsList();
}

// Close My Models panel
function closeMyModels() {
    const panel = document.getElementById('myModelsPanel');
    if (!panel) return;

    panel.classList.remove('visible');
}

// Load list of saved models
async function loadMyModelsList() {
    try {
        const response = await fetch('/modeling/api/my_models/list');
        const data = await response.json();

        if (data.success) {
            myModelsList = data.models || [];
            renderMyModelsList();
        } else {
            showNotification('Error loading My Models', 'error');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        myModelsList = [];
        renderMyModelsList();
    }
}

// Render models list in UI
function renderMyModelsList() {
    const container = document.getElementById('myModelsListContainer');
    if (!container) return;

    if (myModelsList.length === 0) {
        container.innerHTML = `
            <div class="my-models-empty">
                <p>No saved models yet</p>
                <p style="font-size: 0.85em; color: #888; margin-top: 10px;">
                    Models you create or save will appear here
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    myModelsList.forEach(model => {
        const card = document.createElement('div');
        card.className = 'my-model-card';

        const fileSize = model.size ? (model.size / 1024).toFixed(1) + ' KB' : 'Unknown';
        const modifiedDate = model.modified ? new Date(model.modified).toLocaleDateString() : 'Unknown';

        card.innerHTML = `
            <div class="my-model-preview">
                📦
            </div>
            <div class="my-model-info">
                <div class="my-model-name">${model.name}</div>
                <div class="my-model-details">
                    ${fileSize} • ${modifiedDate}
                </div>
            </div>
            <div class="my-model-actions">
                <button class="my-model-action-btn" onclick="loadMyModel('${model.filename}')" title="Load model">
                    📂 Load
                </button>
                <button class="my-model-action-btn delete" onclick="deleteMyModel('${model.filename}')" title="Delete model">
                    🗑️
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}

// Load a model from My Models
async function loadMyModel(filename) {
    try {
        const response = await fetch(`/modeling/my_models/${filename}`);

        if (!response.ok) {
            throw new Error('Failed to load model');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // Load STL
        loadSTL(url);

        // Store file reference
        currentFile = new File([blob], filename, { type: 'model/stl' });

        closeMyModels();
        showNotification(`Loaded: ${filename}`, 'success');

        // Push undo state
        if (typeof pushUndoState === 'function') {
            pushUndoState(`Load ${filename}`);
        }
    } catch (error) {
        showNotification('Error loading model: ' + error.message, 'error');
    }
}

// Delete a model from My Models
async function deleteMyModel(filename) {
    if (!confirm(`Delete "${filename}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/modeling/api/my_models/delete/${filename}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Deleted: ${filename}`, 'success');
            loadMyModelsList();
        } else {
            showNotification('Error deleting model', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// Save current model to My Models
async function saveToMyModels() {
    if (!currentFile && !downloadUrl) {
        showNotification('No model to save', 'error');
        return;
    }

    const filename = prompt('Save as:', currentFile ? currentFile.name : 'model.stl');
    if (!filename) return;

    // Ensure .stl extension
    const finalFilename = filename.endsWith('.stl') ? filename : filename + '.stl';

    try {
        let fileToSave;

        if (currentFile) {
            fileToSave = currentFile;
        } else if (downloadUrl) {
            // Fetch from download URL
            const response = await fetch(downloadUrl);
            const blob = await response.blob();
            fileToSave = new File([blob], finalFilename, { type: 'model/stl' });
        }

        const formData = new FormData();
        formData.append('file', fileToSave);
        formData.append('filename', finalFilename);

        const response = await fetch('/modeling/api/my_models/save', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Saved to My Models: ${finalFilename}`, 'success');
        } else {
            showNotification('Error saving: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error saving: ' + error.message, 'error');
    }
}
