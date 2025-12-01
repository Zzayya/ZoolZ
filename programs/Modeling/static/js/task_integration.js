/**
 * Background Task Integration
 * Connects existing functions to background task system
 */

// ============================================================================
// BACKGROUND TASK HELPERS
// ============================================================================

async function generateCookieCutterSync(formData, generateBtn, generateText, downloadBtn) {
    // Fallback to synchronous generation if Celery not available
    try {
        const response = await fetch('/modeling/api/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            downloadUrl = data.download_url;
            showStatus('Cookie cutter generated successfully!', 'success');
            if (typeof showStats === 'function') {
                showStats(data.stats);
            }

            if (downloadBtn) {
                downloadBtn.style.display = 'inline-flex';
            }

            if (typeof loadSTL === 'function') {
                loadSTL(downloadUrl);
            }

            if (typeof saveToHistory === 'function') {
                saveToHistory('Cookie Cutter Generated');
            }

            // Update measurements
            if (window.measurementOverlay && window.currentMesh) {
                window.measurementOverlay.update(window.currentMesh);
            }
        } else {
            showStatus('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateText.textContent = 'Generate';
    }
}

async function pollTaskProgress(taskId, generateBtn, generateText, downloadBtn) {
    const pollInterval = 500; // Poll every 500ms

    const poll = async () => {
        try {
            const response = await fetch('/modeling/api/task_status/' + taskId);
            const data = await response.json();

            const state = data.state;
            const current = data.current || 0;
            const total = data.total || 100;
            const status = data.status;
            const result = data.result;
            const error = data.error;

            const percent = total > 0 ? Math.round((current / total) * 100) : 0;

            // Update UI with progress
            generateText.innerHTML = '<span class="spinner"></span> ' + (status || state) + ' (' + percent + '%)';
            if (typeof showStatus === 'function') {
                showStatus((status || state) + ' (' + percent + '%)', 'processing');
            }

            if (state === 'SUCCESS') {
                // Task complete!
                window.downloadUrl = result.download_url;
                if (typeof showStatus === 'function') {
                    showStatus('Cookie cutter generated successfully!', 'success');
                }
                if (typeof showStats === 'function') {
                    showStats(result.stats);
                }

                if (downloadBtn) {
                    downloadBtn.style.display = 'inline-flex';
                }

                if (typeof loadSTL === 'function') {
                    loadSTL(result.download_url);
                }

                if (typeof saveToHistory === 'function') {
                    saveToHistory('Cookie Cutter Generated');
                }

                // Update measurements
                setTimeout(() => {
                    if (window.measurementOverlay && window.currentMesh) {
                        window.measurementOverlay.update(window.currentMesh);
                    }
                }, 1000); // Wait for model to load

                generateBtn.disabled = false;
                generateText.textContent = 'Generate';
                return; // Stop polling

            } else if (state === 'FAILURE') {
                if (typeof showStatus === 'function') {
                    showStatus('Error: ' + (error || 'Task failed'), 'error');
                }
                generateBtn.disabled = false;
                generateText.textContent = 'Generate';
                return; // Stop polling

            } else {
                // Task still running - continue polling
                setTimeout(poll, pollInterval);
            }

        } catch (error) {
            console.error('Error polling task:', error);
            if (typeof showStatus === 'function') {
                showStatus('Error: ' + error.message, 'error');
            }
            generateBtn.disabled = false;
            generateText.textContent = 'Generate';
        }
    };

    // Start polling
    poll();
}

// ============================================================================
// AUTO-UPDATE MEASUREMENTS
// ============================================================================

// Hook into mesh loading to auto-update measurements
document.addEventListener('DOMContentLoaded', () => {
    // Watch for mesh changes
    setInterval(() => {
        if (window.measurementOverlay && window.currentMesh) {
            const lastMesh = window._lastMeasuredMesh;
            if (lastMesh !== window.currentMesh) {
                window.measurementOverlay.update(window.currentMesh);
                window._lastMeasuredMesh = window.currentMesh;
            }
        }
    }, 1000); // Check every second

    console.log('✅ Background task integration loaded');
});
