/**
 * Background Tasks Module
 * Handles async task execution with progress tracking and UI updates
 */

class BackgroundTaskManager {
    constructor() {
        this.activeTasks = new Map();
        this.pollInterval = 500; // Poll every 500ms
    }

    /**
     * Start an async task and track its progress
     * @param {string} url - API endpoint for starting the task
     * @param {FormData} formData - Form data to send
     * @param {Object} options - {onProgress, onComplete, onError, operationName}
     */
    async startTask(url, formData, options = {}) {
        const {
            onProgress = (percent, status) => {},
            onComplete = (result) => {},
            onError = (error) => {},
            operationName = 'Operation'
        } = options;

        try {
            // Show loading indicator
            showProgress(`Starting ${operationName.toLowerCase()}...`);

            // Start the background task
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to start task');
            }

            const taskId = data.task_id;
            console.log(`✅ ${operationName} task started: ${taskId}`);

            // Store task info
            this.activeTasks.set(taskId, {
                operationName,
                startTime: Date.now()
            });

            // Start polling for progress
            this.pollTaskStatus(taskId, onProgress, onComplete, onError);

            return taskId;

        } catch (error) {
            console.error(`❌ Error starting ${operationName}:`, error);
            hideProgress();
            onError(error.message);
            throw error;
        }
    }

    /**
     * Poll task status until completion
     */
    async pollTaskStatus(taskId, onProgress, onComplete, onError) {
        const poll = async () => {
            try {
                const response = await fetch(`/modeling/api/task_status/${taskId}`);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to get task status');
                }

                const { state, current, total, status, result, error } = data;
                const percent = total > 0 ? Math.round((current / total) * 100) : 0;

                // Update progress
                onProgress(percent, status || state);

                // Check state
                if (state === 'SUCCESS') {
                    console.log(`✅ Task ${taskId} completed successfully`);
                    this.activeTasks.delete(taskId);
                    hideProgress();
                    onComplete(result);
                    return; // Stop polling

                } else if (state === 'FAILURE') {
                    console.error(`❌ Task ${taskId} failed:`, error);
                    this.activeTasks.delete(taskId);
                    hideProgress();
                    onError(error || 'Task failed');
                    return; // Stop polling

                } else {
                    // Task still running - continue polling
                    setTimeout(poll, this.pollInterval);
                }

            } catch (error) {
                console.error(`❌ Error polling task ${taskId}:`, error);
                this.activeTasks.delete(taskId);
                hideProgress();
                onError(error.message);
            }
        };

        // Start polling
        poll();
    }

    /**
     * Cancel all active tasks
     */
    cancelAll() {
        this.activeTasks.clear();
        hideProgress();
    }

    /**
     * Get active task count
     */
    getActiveCount() {
        return this.activeTasks.size;
    }
}

// Global instance
window.backgroundTaskManager = new BackgroundTaskManager();


/**
 * Helper: Generate cookie cutter with progress tracking
 */
async function generateCookieCutterAsync() {
    const fileInput = document.getElementById('cookieInput');
    if (!fileInput || !fileInput.files[0]) {
        alert('⚠️ Please upload an image first');
        return;
    }

    // Get parameters from UI
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('blade_thick', document.getElementById('bladeThick')?.value || 2.0);
    formData.append('blade_height', document.getElementById('bladeHeight')?.value || 20.0);
    formData.append('base_thick', document.getElementById('baseThick')?.value || 3.0);
    formData.append('base_extra', document.getElementById('baseExtra')?.value || 10.0);
    formData.append('max_dim', document.getElementById('maxDim')?.value || 90.0);
    formData.append('detail_level', document.getElementById('detailLevel')?.value || 0.5);
    formData.append('no_base', document.getElementById('noBase')?.checked || false);

    await window.backgroundTaskManager.startTask(
        '/modeling/api/generate_async',
        formData,
        {
            operationName: 'Cookie Cutter Generation',
            onProgress: (percent, status) => {
                showProgress(`${status} (${percent}%)`);
            },
            onComplete: (result) => {
                console.log('✅ Cookie cutter generated!', result);
                if (result.download_url) {
                    loadModelFromServer(result.download_url);
                    showSuccess('Cookie cutter generated successfully!');
                }
            },
            onError: (error) => {
                showError(`Generation failed: ${error}`);
            }
        }
    );
}


/**
 * Helper: Thicken mesh with progress tracking
 */
async function thickenMeshAsync() {
    if (!currentMesh) {
        alert('⚠️ Please load a model first');
        return;
    }

    // Export current mesh to file
    const stlBlob = await exportCurrentMeshAsBlob();

    // Get parameters
    const formData = new FormData();
    formData.append('stl', stlBlob, 'current_mesh.stl');
    formData.append('offset', document.getElementById('thickenOffset')?.value || 2.0);
    formData.append('smooth', document.getElementById('thickenSmooth')?.checked || true);

    await window.backgroundTaskManager.startTask(
        '/modeling/api/stl/thicken_async',
        formData,
        {
            operationName: 'Mesh Thickening',
            onProgress: (percent, status) => {
                showProgress(`${status} (${percent}%)`);
            },
            onComplete: (result) => {
                console.log('✅ Mesh thickened!', result);
                if (result.download_url) {
                    loadModelFromServer(result.download_url);
                    showSuccess('Mesh thickened successfully!');
                }
            },
            onError: (error) => {
                showError(`Thickening failed: ${error}`);
            }
        }
    );
}


/**
 * Helper: Hollow mesh with progress tracking
 */
async function hollowMeshAsync() {
    if (!currentMesh) {
        alert('⚠️ Please load a model first');
        return;
    }

    // Export current mesh to file
    const stlBlob = await exportCurrentMeshAsBlob();

    // Get parameters
    const formData = new FormData();
    formData.append('stl', stlBlob, 'current_mesh.stl');
    formData.append('wall_thickness', document.getElementById('wallThickness')?.value || 2.0);
    formData.append('add_drainage', document.getElementById('addDrainage')?.checked || true);
    formData.append('drain_diameter', document.getElementById('drainDiameter')?.value || 5.0);

    await window.backgroundTaskManager.startTask(
        '/modeling/api/stl/hollow_async',
        formData,
        {
            operationName: 'Mesh Hollowing',
            onProgress: (percent, status) => {
                showProgress(`${status} (${percent}%)`);
            },
            onComplete: (result) => {
                console.log('✅ Mesh hollowed!', result);
                if (result.download_url) {
                    loadModelFromServer(result.download_url);
                    showSuccess('Mesh hollowed successfully!');
                }
            },
            onError: (error) => {
                showError(`Hollowing failed: ${error}`);
            }
        }
    );
}


/**
 * Helper: Export current mesh as Blob for upload
 */
async function exportCurrentMeshAsBlob() {
    // This function should export the current Three.js mesh as STL blob
    // You'll need to implement this based on your Three.js setup
    // For now, just a placeholder
    throw new Error('exportCurrentMeshAsBlob not implemented yet');
}


/**
 * UI Helper: Show progress message
 */
function showProgress(message) {
    // Check if progress indicator exists, otherwise create it
    let progressDiv = document.getElementById('progressIndicator');

    if (!progressDiv) {
        progressDiv = document.createElement('div');
        progressDiv.id = 'progressIndicator';
        progressDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.9);
            color: #00ff00;
            padding: 15px 25px;
            border-radius: 8px;
            border: 2px solid #00ff00;
            font-family: monospace;
            font-size: 14px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0, 255, 0, 0.3);
        `;
        document.body.appendChild(progressDiv);
    }

    progressDiv.textContent = message;
    progressDiv.style.display = 'block';
}


/**
 * UI Helper: Hide progress message
 */
function hideProgress() {
    const progressDiv = document.getElementById('progressIndicator');
    if (progressDiv) {
        progressDiv.style.display = 'none';
    }
}


/**
 * UI Helper: Show success message
 */
function showSuccess(message) {
    console.log('✅', message);
    // You can integrate with your existing notification system here
    if (typeof showNotification === 'function') {
        showNotification(message, 'success');
    } else {
        alert(message);
    }
}


/**
 * UI Helper: Show error message
 */
function showError(message) {
    console.error('❌', message);
    // You can integrate with your existing notification system here
    if (typeof showNotification === 'function') {
        showNotification(message, 'error');
    } else {
        alert(`Error: ${message}`);
    }
}
